# src/core/sensors/witmotion_uart_sensor.py
import serial
import time
import threading
import logging
from typing import Dict, Any, Optional, List

from .base_sensor import BaseSensor, SensorConnectionError, SensorConfigurationError
from .parsers.witmotion_parser import WitmotionParser # Import parser mới

logger = logging.getLogger(__name__)

class WitMotionUARTSensor(BaseSensor):
    """
    Lớp cảm biến WitMotion kết nối qua UART.
    Chịu trách nhiệm giao tiếp, gửi lệnh cấu hình và sử dụng WitmotionParser để phân tích dữ liệu.
    """
    # Các mã lệnh cấu hình WitMotion (ví dụ)
    CMD_PREFIX = b'\xFF\xAA'
    CMD_SET_DATA_RATE = 0x03
    CMD_CALIBRATE_ACC = 0x01 # Mã lệnh cho CAL (01 = ACC, 02 = GYRO, 03 = MAG, 04 = INSTALL_DIR)
    CMD_SAVE_SETTINGS = 0x00 # Mã lệnh cho REG_SAVE (00 = SAVE)
    # ... thêm các mã lệnh khác

    # Ánh xạ rate_code sang giá trị Hz (tham khảo)
    DATA_RATE_MAP_HZ = {
        0x01: 1, 0x02: 2, 0x03: 5, 0x04: 10, 0x05: 20,
        0x06: 50, 0x07: 100, 0x08: 125, 0x09: 200, 0x0a: 250,
        0x0b: 500 # Lưu ý: tài liệu gốc WitMotion có thể khác, đây là ví dụ
        # Một số cảm biến WitMotion dùng mã khác cho tốc độ cao hơn (ví dụ WT901C-232)
        # 0x09: 100Hz, 0x0a: 200Hz, 0x0b: không xác định rõ ràng trong nhiều tài liệu, có thể là 500Hz hoặc fast mode
        # Cần kiểm tra datasheet của model cụ thể. Ví dụ BWT901CL dùng 0x09 là 200Hz.
    }
    DEFAULT_DATA_RATE_CODE = 0x09 # Mặc định 200Hz cho nhiều model phổ biến

    def __init__(self, sensor_id: str, name: str, config: Dict[str, Any]):
        super().__init__(sensor_id, name, config)
        self.serial_connection: Optional[serial.Serial] = None
        self.parser = WitmotionParser()

        # Lấy thông tin cấu hình từ dict `config`
        self.port_name: Optional[str] = config.get("port_address")
        self.baudrate: int = config.get("baudrate", 115200)
        
        # Cấu hình dải đo cho parser, nếu có trong config
        acc_range_g = config.get("acc_range_g", WitmotionParser.DEFAULT_ACC_RANGE)
        gyro_range_dps = config.get("gyro_range_dps", WitmotionParser.DEFAULT_GYRO_RANGE)
        self.parser.set_measurement_ranges(acc_range=acc_range_g, gyro_range=gyro_range_dps)

        # Cấu hình tốc độ dữ liệu mặc định (có thể ghi đè bằng lệnh)
        # Giá trị này là mã byte, ví dụ 0x09 cho 200Hz tùy model
        self.target_data_rate_code: int = config.get("data_rate_code", self.DEFAULT_DATA_RATE_CODE)
        
        # Thời gian chờ giữa các lần đọc (để không làm quá tải CPU)
        self._read_interval = 0.001 # 1ms, luồng đọc sẽ chủ yếu bị block bởi serial.read()

        # Cơ chế tích lũy gói tin:
        # WitMotion thường gửi cụm ACC, GYRO, ANGLE liên tiếp.
        # Chúng ta có thể đợi đến khi nhận được gói ANGLE (0x53) cuối cùng trong cụm
        # rồi mới coi là một "bản tin" hoàn chỉnh để gửi đi.
        self._current_data_packet: Dict[str, Any] = {}
        self._expected_packets_in_cycle = {
            WitmotionParser.PACKET_TYPE_ACCELERATION,
            WitmotionParser.PACKET_TYPE_ANGULAR_VELOCITY,
            WitmotionParser.PACKET_TYPE_ANGLE
        }
        self._received_packets_in_current_cycle = set()


    def _connect_to_sensor(self) -> None:
        if not self.port_name:
            raise SensorConnectionError(f"[{self.name}] Serial port not specified in configuration.")
        try:
            self.serial_connection = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=0.1 # Timeout cho read operation
            )
            if not self.serial_connection.is_open: # Kiểm tra lại sau khi khởi tạo
                raise SensorConnectionError(f"[{self.name}] Failed to open serial port {self.port_name}.")

            logger.info(f"[{self.name}] Successfully connected to serial port {self.port_name} at {self.baudrate} baud.")
            
            # Gửi lệnh cấu hình tốc độ dữ liệu ngay sau khi kết nối nếu được định nghĩa
            # Lưu ý: một số cảm biến cần thời gian khởi động trước khi nhận lệnh
            time.sleep(0.2) # Chờ một chút cho cảm biến ổn định
            if self.target_data_rate_code is not None:
                self.send_config_command("SET_DATA_RATE", {"rate_code_int": self.target_data_rate_code})
            # Có thể thêm các lệnh cấu hình khởi tạo khác ở đây

        except serial.SerialException as e:
            raise SensorConnectionError(f"[{self.name}] Serial connection error on {self.port_name}: {e}")
        except Exception as e:
            raise SensorConnectionError(f"[{self.name}] Unexpected error connecting: {e}")

    def _disconnect_from_sensor(self) -> None:
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                logger.info(f"[{self.name}] Serial port {self.port_name} disconnected.")
            except Exception as e:
                logger.error(f"[{self.name}] Error closing serial port: {e}")
        self.serial_connection = None

    def _read_data_loop(self) -> None:
        logger.info(f"[{self.name}] Data reading loop started.")
        
        while not self._stop_event.is_set():
            if not self.connected or not self.serial_connection:
                logger.warning(f"[{self.name}] Sensor not connected or serial connection lost.")
                time.sleep(0.1)
                continue

            try:
                if self.serial_connection.in_waiting > 0:
                    bytes_to_read = self.serial_connection.in_waiting
                    raw_bytes = self.serial_connection.read(bytes_to_read)
                    if raw_bytes:
                        # Chỉ log raw bytes ở mức debug
                        logger.debug(f"[{self.name}] Raw bytes received: {raw_bytes.hex(' ')}")
                        for byte_val in raw_bytes:
                            self.parser.process_byte(byte_val)

                        newly_parsed = self.parser.get_parsed_data()
                        if newly_parsed:
                            # Chỉ log dữ liệu mới ở mức debug
                            logger.debug(f"[{self.name}] Newly parsed data: {newly_parsed}")
                            self._current_data_packet.update(newly_parsed)
                            
                            if hasattr(self.parser, '_last_packet_type_processed') and \
                               self.parser._last_packet_type_processed is not None:
                                self._received_packets_in_current_cycle.add(self.parser._last_packet_type_processed)
                                # Chỉ log trạng thái gói tin ở mức debug
                                logger.debug(f"[{self.name}] Current received packets in cycle: {self._received_packets_in_current_cycle}")

                            if self._received_packets_in_current_cycle.issuperset(self._expected_packets_in_cycle):
                                if self.on_data_callback and self._current_data_packet:
                                    self.last_data = self._current_data_packet.copy()
                                    self.data_timestamp = time.time()
                                    # Chỉ log khi hoàn thành một chu kỳ dữ liệu
                                    logger.info(f"[{self.name}] Completed data cycle with packets: {self._received_packets_in_current_cycle}")
                                    self.on_data_callback(self.sensor_id, self.last_data)
                                self._current_data_packet.clear()
                                self._received_packets_in_current_cycle.clear()
                                self.parser.clear_cached_data()
                else:
                    time.sleep(0.001)
            except Exception as e:
                logger.error(f"[{self.name}] Error in data reading loop: {e}", exc_info=True)
                time.sleep(0.1)

        logger.debug(f"[{self.name}] Data reading loop stopped.")
        self._disconnect_from_sensor()


    def _process_raw_data(self, raw_data: Any) -> Optional[Dict[str, Any]]:
        """
        Phương thức này không còn cần thiết nữa vì WitmotionParser đã xử lý việc này.
        Dữ liệu nhận được từ on_data_callback đã là dictionary chuẩn.
        """
        if isinstance(raw_data, dict):
            return raw_data
        logger.warning(f"[{self.name}] _process_raw_data received non-dict data: {type(raw_data)}")
        return None


    def _construct_command(self, register_address: int, value_bytes: bytes) -> bytes:
        """Xây dựng một gói lệnh WitMotion chuẩn."""
        if not (0 <= register_address <= 0xFF):
            raise ValueError("Register address must be a byte (0-255).")
        
        payload = bytes([register_address]) + value_bytes
        command_frame = self.CMD_PREFIX + payload
        checksum = sum(command_frame) & 0xFF
        return command_frame + bytes([checksum])

    def send_config_command(self, command_type: str, params: Dict[str, Any]) -> bool:
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error(f"[{self.name}] Cannot send command: Serial port not open.")
            return False

        final_command: Optional[bytes] = None
        log_message = ""

        if command_type == "SET_DATA_RATE":
            # params = {"rate_code_int": 0x09} (0x09 là 200Hz cho nhiều model)
            rate_code_int = params.get("rate_code_int")
            if rate_code_int is None or not (0x00 <= rate_code_int <= 0x0B): # Kiểm tra dải mã hợp lệ (ví dụ)
                logger.error(f"[{self.name}] Invalid or missing 'rate_code_int' for SET_DATA_RATE: {rate_code_int}")
                return False
            
            value_byte = bytes([rate_code_int])
            # Lệnh đầy đủ: FF AA 03 <rate_byte> <checksum>
            # Ở đây self.CMD_SET_DATA_RATE (0x03) chính là register_address
            command_payload = self.CMD_PREFIX + bytes([self.CMD_SET_DATA_RATE]) + value_byte
            checksum = sum(command_payload) & 0xFF
            final_command = command_payload + bytes([checksum])
            
            # Cập nhật target rate của instance
            self.target_data_rate_code = rate_code_int
            self.config["data_rate_code"] = rate_code_int # Lưu vào config của instance

            rate_hz_str = f"{self.DATA_RATE_MAP_HZ.get(rate_code_int, 'Unknown')} Hz"
            log_message = f"SET_DATA_RATE to code 0x{rate_code_int:02X} ({rate_hz_str})"

        elif command_type == "CALIBRATE_ACC":
            # Lệnh: FF AA 01 01 CS (Bắt đầu hiệu chỉnh ACC)
            # Sau đó cần gửi FF AA 00 01 CS (Lưu cấu hình)
            command_payload = self.CMD_PREFIX + bytes([self.CMD_CALIBRATE_ACC, 0x01])
            checksum = sum(command_payload) & 0xFF
            final_command = command_payload + bytes([checksum])
            log_message = "CALIBRATE_ACC (Start)"
            # Lưu ý: Cần thêm logic để gửi lệnh SAVE sau đó.
            # Hoặc tạo command_type="SAVE_SETTINGS" riêng.

        elif command_type == "SAVE_SETTINGS":
            # Lệnh: FF AA 00 01 CS
            command_payload = self.CMD_PREFIX + bytes([self.CMD_SAVE_SETTINGS, 0x01])
            checksum = sum(command_payload) & 0xFF
            final_command = command_payload + bytes([checksum])
            log_message = "SAVE_SETTINGS"
            
        # Thêm các command_type khác ở đây:
        # ELIF command_type == "SET_GYRO_RANGE":
        #     params = {"range_code": 0x00} # 0x00 = 250dps, 0x01=500, 0x02=1000, 0x03=2000
        #     REG_GYRO_RANGE = 0xXX # Địa chỉ thanh ghi dải đo Gyro
        #     ... construct final_command ...

        else:
            logger.warning(f"[{self.name}] Unsupported command_type '{command_type}'.")
            return False

        if final_command:
            try:
                self.serial_connection.write(final_command)
                time.sleep(0.1) # Chờ cảm biến xử lý, WitMotion thường không có ACK rõ ràng cho nhiều lệnh config
                logger.info(f"[{self.name}] Sent command: {log_message}. Bytes: {final_command.hex().upper()}")
                # Một số lệnh có thể cần đọc phản hồi từ cảm biến để xác nhận
                return True
            except Exception as e:
                logger.error(f"[{self.name}] Error sending command '{log_message}': {e}")
                raise SensorConfigurationError(f"Failed to send {command_type}: {e}")
        return False

    def get_sensor_type(self) -> str:
        return "WitMotion_UART"

    def get_available_data_keys(self) -> List[str]:
        """Trả về danh sách các key dữ liệu mà cảm biến này có thể cung cấp."""
        return WitmotionParser.get_known_data_keys() # Lấy từ parser

    @staticmethod
    def get_supported_config_commands() -> Dict[str, Dict[str, Any]]:
        """
        Trả về một dictionary mô tả các lệnh cấu hình được hỗ trợ và các tham số của chúng.
        UI có thể sử dụng thông tin này để tạo giao diện cấu hình động.
        """
        return {
            "SET_DATA_RATE": {
                "description": "Đặt tốc độ dữ liệu đầu ra của cảm biến.",
                "params": {
                    "rate_code_int": {
                        "type": "choice", # Hoặc "int" nếu người dùng nhập mã trực tiếp
                        "label": "Mã Tốc độ (0x00-0x0B)",
                        "choices": {f"0x{code:02X} ({hz} Hz)": code for code, hz in WitMotionUARTSensor.DATA_RATE_MAP_HZ.items()},
                        "default": WitMotionUARTSensor.DEFAULT_DATA_RATE_CODE
                    }
                }
            },
            "CALIBRATE_ACC": {
                "description": "Bắt đầu quá trình hiệu chỉnh gia tốc kế (cần đặt cảm biến trên mặt phẳng tĩnh).",
                "params": {} # Lệnh này không cần tham số từ người dùng
            },
            "SAVE_SETTINGS": {
                "description": "Lưu các cài đặt hiện tại vào bộ nhớ flash của cảm biến.",
                "params": {}
            }
            # Thêm các lệnh khác...
        }