# src/core/sensors/parsers/witmotion_parser.py
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class ParsedSensorData:
    """Lớp đơn giản để lưu trữ dữ liệu đã được phân tích từ cảm biến."""
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.timestamp: Optional[float] = None # Sẽ được gán bởi BaseSensor khi nhận được

    def set_value(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_value(self, key: str) -> Any:
        return self.data.get(key)

    def get_all_data(self) -> Dict[str, Any]:
        return self.data.copy()

    def clear(self):
        self.data.clear()

class WitmotionParser:
    """
    Xử lý và phân tích cú pháp dữ liệu thô từ cảm biến WitMotion.
    Lớp này không quản lý kết nối serial.
    """
    PACKET_HEADER = 0x55
    PACKET_SIZE = 11 # Kích thước gói tin chuẩn của WitMotion

    # Định nghĩa các mã loại gói tin
    PACKET_TYPE_TIME = 0x50
    PACKET_TYPE_ACCELERATION = 0x51
    PACKET_TYPE_ANGULAR_VELOCITY = 0x52
    PACKET_TYPE_ANGLE = 0x53
    PACKET_TYPE_MAGNETIC = 0x54
    PACKET_TYPE_PORT_STATUS = 0x55 # Trùng header, cẩn thận khi xử lý
    PACKET_TYPE_ATMOSPHERIC_PRESSURE = 0x56
    PACKET_TYPE_LONGITUDE_LATITUDE = 0x57
    PACKET_TYPE_GPS_VELOCITY = 0x58
    PACKET_TYPE_QUATERNION = 0x59
    PACKET_TYPE_GPS_ACCURACY = 0x5A


    # Các dải đo mặc định (có thể được ghi đè bởi cấu hình cảm biến nếu cần)
    DEFAULT_ACC_RANGE = 16.0  # g
    DEFAULT_GYRO_RANGE = 2000.0  # °/s
    DEFAULT_ANGLE_RANGE = 180.0  # °

    # Các key dữ liệu chuẩn mà parser này sẽ cố gắng trích xuất
    KNOWN_DATA_KEYS = [
        "accX", "accY", "accZ",
        "gyroX", "gyroY", "gyroZ",
        "angleX", "angleY", "angleZ",
        "magX", "magY", "magZ",
        "pressure", "altitude",
        "longitude", "latitude",
        "gpsHeight", "gpsYaw", "gpsGroundSpeed",
        "q0", "q1", "q2", "q3", # Quaternion
        "gpsAccuracy", "gpsHorizontalAccuracy", "gpsVerticalAccuracy",
        "year", "month", "day", "hour", "minute", "second", "millisecond" # Time packet
    ]


    def __init__(self, on_complete_packet: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Khởi tạo WitmotionParser.
        Args:
            on_complete_packet: Callback sẽ được gọi khi một gói dữ liệu hoàn chỉnh được xử lý,
                                 mang theo dictionary dữ liệu đã phân tích.
        """
        self._buffer: bytearray = bytearray()
        self.parsed_data_cache = ParsedSensorData() # Cache để tích lũy dữ liệu từ các gói khác nhau
                                                   # trước khi gọi on_complete_packet
        self.on_complete_packet = on_complete_packet
        self._last_packet_type_processed: Optional[int] = None

        # Các dải đo hiện tại, có thể được cập nhật từ bên ngoài nếu cảm biến được cấu hình khác
        self.acc_range = self.DEFAULT_ACC_RANGE
        self.gyro_range = self.DEFAULT_GYRO_RANGE
        self.angle_range = self.DEFAULT_ANGLE_RANGE


    def set_measurement_ranges(self, acc_range: Optional[float] = None,
                               gyro_range: Optional[float] = None,
                               angle_range: Optional[float] = None):
        if acc_range is not None: self.acc_range = acc_range
        if gyro_range is not None: self.gyro_range = gyro_range
        if angle_range is not None: self.angle_range = angle_range
        logger.info(f"WitmotionParser ranges updated: Acc={self.acc_range}g, Gyro={self.gyro_range}°/s, Angle={self.angle_range}°")


    def process_byte(self, byte_val: int) -> None:
        """
        Xử lý từng byte dữ liệu nhận được.
        Khi một gói tin hoàn chỉnh và hợp lệ được xử lý, self.on_complete_packet sẽ được gọi.
        """
        self._buffer.append(byte_val)

        while len(self._buffer) >= self.PACKET_SIZE:
            # Tìm header 0x55
            try:
                header_index = self._buffer.index(self.PACKET_HEADER)
                if header_index > 0:
                    # Loại bỏ các byte rác trước header
                    logger.debug(f"Discarding {header_index} garbage bytes: {self._buffer[:header_index].hex()}")
                    self._buffer = self._buffer[header_index:]
            except ValueError:
                # Không tìm thấy header, có thể buffer chứa toàn byte rác
                logger.debug(f"No header found in buffer of size {len(self._buffer)}. Discarding entire buffer: {self._buffer.hex()}")
                self._buffer.clear()
                return

            if len(self._buffer) < self.PACKET_SIZE:
                # Chưa đủ dữ liệu cho một gói tin hoàn chỉnh
                break

            # Lấy một gói tin tiềm năng
            potential_packet = self._buffer[:self.PACKET_SIZE]

            # Kiểm tra checksum
            calculated_checksum = sum(potential_packet[:-1]) & 0xFF
            packet_checksum = potential_packet[-1]

            if calculated_checksum == packet_checksum:
                # Checksum hợp lệ, xử lý gói tin
                self._decode_packet_and_notify(potential_packet)
                # Xóa gói tin đã xử lý khỏi buffer
                self._buffer = self._buffer[self.PACKET_SIZE:]
            else:
                # Checksum không hợp lệ. Đây có thể là header giả.
                # Bỏ qua byte header này và tìm header tiếp theo.
                logger.warning(f"Checksum error. Packet: {potential_packet.hex()}. Calculated: {calculated_checksum:02X}, Got: {packet_checksum:02X}. Discarding header byte.")
                self._buffer = self._buffer[1:]
        
        # Giới hạn kích thước buffer để tránh tràn bộ nhớ nếu liên tục nhận dữ liệu lỗi
        max_buffer_size = self.PACKET_SIZE * 5 
        if len(self._buffer) > max_buffer_size:
            logger.warning(f"Parser buffer exceeded max size ({max_buffer_size}), truncating.")
            self._buffer = self._buffer[-max_buffer_size:]


    def _decode_packet_and_notify(self, packet: bytes) -> None:
        """Giải mã gói tin và gọi callback nếu có dữ liệu mới."""
        packet_type = packet[1]
        data_payload = packet[2:-1] # 8 byte data
        new_data_decoded = False

        # Xóa cache trước khi giải mã gói mới để tránh nhầm lẫn dữ liệu cũ
        # self.parsed_data_cache.clear() # Không clear ở đây, mà tích lũy

        if packet_type == self.PACKET_TYPE_ACCELERATION: # 0x51
            ax = self._to_short(data_payload[0:2]) / 32768.0 * self.acc_range
            ay = self._to_short(data_payload[2:4]) / 32768.0 * self.acc_range
            az = self._to_short(data_payload[4:6]) / 32768.0 * self.acc_range
            # temp = self._to_short(data_payload[6:8]) / 100.0 # Nhiệt độ từ gói gia tốc
            self.parsed_data_cache.set_value("accX", round(ax, 4))
            self.parsed_data_cache.set_value("accY", round(ay, 4))
            self.parsed_data_cache.set_value("accZ", round(az, 4))
            # self.parsed_data_cache.set_value("chipTempAcc", temp)
            new_data_decoded = True
            # logger.debug(f"Decoded ACC: X={ax:.2f}, Y={ay:.2f}, Z={az:.2f}")

        elif packet_type == self.PACKET_TYPE_ANGULAR_VELOCITY: # 0x52
            wx = self._to_short(data_payload[0:2]) / 32768.0 * self.gyro_range
            wy = self._to_short(data_payload[2:4]) / 32768.0 * self.gyro_range
            wz = self._to_short(data_payload[4:6]) / 32768.0 * self.gyro_range
            self.parsed_data_cache.set_value("gyroX", round(wx, 4))
            self.parsed_data_cache.set_value("gyroY", round(wy, 4))
            self.parsed_data_cache.set_value("gyroZ", round(wz, 4))
            new_data_decoded = True
            # logger.debug(f"Decoded GYRO: X={wx:.2f}, Y={wy:.2f}, Z={wz:.2f}")

        elif packet_type == self.PACKET_TYPE_ANGLE: # 0x53
            roll = self._to_short(data_payload[0:2]) / 32768.0 * self.angle_range
            pitch = self._to_short(data_payload[2:4]) / 32768.0 * self.angle_range
            yaw = self._to_short(data_payload[4:6]) / 32768.0 * self.angle_range
            self.parsed_data_cache.set_value("angleX", round(roll, 4)) # Roll
            self.parsed_data_cache.set_value("angleY", round(pitch, 4)) # Pitch
            self.parsed_data_cache.set_value("angleZ", round(yaw, 4))   # Yaw
            new_data_decoded = True
            # logger.debug(f"Decoded ANGLE: Roll={roll:.2f}, Pitch={pitch:.2f}, Yaw={yaw:.2f}")
        
        elif packet_type == self.PACKET_TYPE_MAGNETIC: # 0x54
            mx = self._to_short(data_payload[0:2]) # Đơn vị của từ kế thường là mGs hoặc uT, không có dải đo chuẩn
            my = self._to_short(data_payload[2:4])
            mz = self._to_short(data_payload[4:6])
            self.parsed_data_cache.set_value("magX", mx)
            self.parsed_data_cache.set_value("magY", my)
            self.parsed_data_cache.set_value("magZ", mz)
            new_data_decoded = True

        elif packet_type == self.PACKET_TYPE_QUATERNION: #0x59
            q0 = self._to_short(data_payload[0:2]) / 32768.0
            q1 = self._to_short(data_payload[2:4]) / 32768.0
            q2 = self._to_short(data_payload[4:6]) / 32768.0
            q3 = self._to_short(data_payload[6:8]) / 32768.0
            self.parsed_data_cache.set_value("q0", round(q0, 6))
            self.parsed_data_cache.set_value("q1", round(q1, 6))
            self.parsed_data_cache.set_value("q2", round(q2, 6))
            self.parsed_data_cache.set_value("q3", round(q3, 6))
            new_data_decoded = True
        
        # Thêm các loại gói tin khác nếu cần (0x50, 0x56, 0x57, 0x58, 0x5A)

        else:
            logger.debug(f"Unhandled WitMotion packet type: {packet_type:02X}")

        # Gọi callback khi một gói tin được giải mã thành công VÀ đó là gói tin cuối cùng trong một "chu kỳ"
        # Hoặc đơn giản là gọi callback mỗi khi có dữ liệu mới từ một gói.
        # Để tránh gửi dữ liệu không đầy đủ, ta có thể đợi đến khi nhận được gói Angle (0x53)
        # vì đó thường là gói cuối trong bộ ba Acc-Gyro-Angle.
        # Hoặc, nếu on_complete_packet được thiết kế để nhận các cập nhật từng phần,
        # thì gọi nó mỗi khi new_data_decoded = True.
        # Hiện tại, sẽ gọi khi có dữ liệu mới và cache sẽ được gửi đi.
        # Việc BaseSensor quyết định khi nào gửi đi (ví dụ, sau khi tích đủ 1 cụm dữ liệu) là hợp lý hơn.
        # Parser chỉ nên báo hiệu là có data mới trong cache.
        if new_data_decoded and self.on_complete_packet:
            # Quyết định: Gửi toàn bộ cache đi mỗi khi có một gói mới được giải mã.
            # Lớp Sensor (ví dụ WitMotionUARTSensor) sẽ quyết định khi nào emit dữ liệu cuối cùng cho SensorProcessor
            # dựa trên việc nó đã nhận đủ các loại gói tin mong muốn hay chưa.
            # Hoặc đơn giản hơn, WitMotionUARTSensor sẽ lấy self.parser.parsed_data_cache.get_all_data() theo một tần suất nhất định.
            # Trong thiết kế hiện tại của BaseSensor, _read_data_loop sẽ gọi _process_raw_data,
            # và _process_raw_data sẽ trả về dict.
            # Vậy, WitmotionParser không cần callback on_complete_packet nữa.
            # Thay vào đó, WitmotionUARTSensor sẽ lấy dữ liệu từ parsed_data_cache.
            pass # Không cần callback ở đây nữa nếu UARTSensor chủ động lấy
        
        self._last_packet_type_processed = packet_type


    def get_parsed_data(self) -> Dict[str, Any]:
        """Trả về bản sao của dữ liệu đã được phân tích và xóa cache."""
        data_to_return = self.parsed_data_cache.get_all_data()
        # Quyết định xóa cache hay không tùy thuộc vào logic của cảm biến gọi nó.
        # Nếu cảm biến muốn tích lũy nhiều gói trước khi lấy, thì không nên xóa ở đây.
        # self.parsed_data_cache.clear() # Tạm thời không xóa, để cảm biến quyết định
        return data_to_return

    def clear_cached_data(self):
        self.parsed_data_cache.clear()
        logger.debug("WitmotionParser cache cleared.")

    def _to_short(self, two_bytes: bytes) -> int:
        """Chuyển đổi 2 byte (little-endian) thành số nguyên có dấu 16-bit."""
        if len(two_bytes) < 2: return 0 # Phòng trường hợp dữ liệu không đủ
        val = int.from_bytes(two_bytes, byteorder='little', signed=True)
        return val

    @staticmethod
    def get_known_data_keys() -> List[str]:
        return WitmotionParser.KNOWN_DATA_KEYS