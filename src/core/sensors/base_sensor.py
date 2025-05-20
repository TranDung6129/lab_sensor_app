from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
import logging
import time
import threading

logger = logging.getLogger(__name__)

class SensorConnectionError(Exception):
    """Custom exception for sensor connection errors."""
    pass

class SensorConfigurationError(Exception):
    """Custom exception for sensor configuration errors."""
    pass

class BaseSensor(ABC):
    def __init__(self, sensor_id: str, name: str, config: Dict[str, Any]):
        self.sensor_id = sensor_id # ID duy nhất, có thể là địa chỉ MAC, UUID, hoặc do người dùng đặt
        self.name = name # Tên thân thiện do người dùng đặt
        self.config = config # Bao gồm protocol, port_address, baudrate, và các config đặc thù
        self.connected = False
        self.last_data: Optional[Dict[str, Any]] = None # Dữ liệu thô gần nhất
        self.processed_data: Optional[Dict[str, Any]] = None # Dữ liệu đã qua xử lý cơ bản (nếu có)
        self.error_message: Optional[str] = None
        self.data_timestamp: Optional[float] = None

        self._stop_event = threading.Event()
        self._data_thread: Optional[threading.Thread] = None
        self.on_data_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None # Callback khi có dữ liệu mới
        self.on_status_change_callback: Optional[Callable[[str, bool, Optional[str]], None]] = None # Callback khi trạng thái thay đổi

    @abstractmethod
    def _connect_to_sensor(self) -> None:
        """
        Triển khai logic kết nối cụ thể cho từng loại cảm biến.
        Ném SensorConnectionError nếu thất bại.
        Cập nhật self.connected = True nếu thành công.
        """
        pass

    @abstractmethod
    def _disconnect_from_sensor(self) -> None:
        """
        Triển khai logic ngắt kết nối cụ thể.
        Cập nhật self.connected = False.
        """
        pass

    @abstractmethod
    def _read_data_loop(self) -> None:
        """
        Vòng lặp đọc dữ liệu từ cảm biến.
        Gọi self._process_raw_data và self.on_data_callback.
        Nên kiểm tra self._stop_event.is_set() để dừng.
        """
        pass

    @abstractmethod
    def _process_raw_data(self, raw_data: Any) -> Optional[Dict[str, Any]]:
        """
        Xử lý dữ liệu thô từ cảm biến thành dictionary chuẩn hóa.
        Trả về None nếu dữ liệu không hợp lệ.
        """
        pass

    def send_config_command(self, command_type: str, params: Dict[str, Any]) -> bool:
        """
        Gửi lệnh cấu hình đến cảm biến.
        Đây là một phương thức tùy chọn, không phải tất cả cảm biến đều hỗ trợ.
        Args:
            command_type: Loại lệnh (ví dụ: "SET_DATA_RATE", "CALIBRATE")
            params: Dictionary chứa các tham số cho lệnh
        Returns:
            True nếu gửi lệnh thành công (không nhất thiết cảm biến đã áp dụng), False nếu lỗi.
        """
        logger.warning(f"Sensor {self.name} (Type: {self.get_sensor_type()}) does not implement send_config_command for '{command_type}'.")
        return False

    def connect(self) -> bool:
        if self.connected:
            logger.info(f"Sensor {self.name} ({self.sensor_id}) is already connected.")
            return True
        try:
            self._connect_to_sensor() # Gọi triển khai cụ thể
            self.connected = True
            self.error_message = None
            logger.info(f"Sensor {self.name} ({self.sensor_id}) connected successfully.")
            if self.on_status_change_callback:
                self.on_status_change_callback(self.sensor_id, True, None)

            # Khởi động luồng đọc dữ liệu
            self._stop_event.clear()
            self._data_thread = threading.Thread(target=self._read_data_loop, daemon=True)
            self._data_thread.start()
            return True
        except SensorConnectionError as e:
            self.connected = False
            self.error_message = str(e)
            logger.error(f"Failed to connect to sensor {self.name} ({self.sensor_id}): {self.error_message}")
            if self.on_status_change_callback:
                self.on_status_change_callback(self.sensor_id, False, self.error_message)
            return False
        except Exception as e:
            self.connected = False
            self.error_message = f"Unexpected error during connection: {str(e)}"
            logger.error(f"Unexpected error connecting to sensor {self.name} ({self.sensor_id}): {self.error_message}", exc_info=True)
            if self.on_status_change_callback:
                self.on_status_change_callback(self.sensor_id, False, self.error_message)
            return False

    def disconnect(self) -> bool:
        if not self.connected and not (self._data_thread and self._data_thread.is_alive()):
            logger.info(f"Sensor {self.name} ({self.sensor_id}) is already disconnected.")
            return True

        logger.info(f"Requesting disconnect for sensor {self.name} ({self.sensor_id})...")
        self._stop_event.set() # Báo cho luồng đọc dừng lại

        if self._data_thread and self._data_thread.is_alive():
            logger.debug(f"Waiting for data thread of {self.name} to join...")
            self._data_thread.join(timeout=2.0) # Chờ luồng dừng, timeout 2 giây
            if self._data_thread.is_alive():
                logger.warning(f"Data thread for {self.name} did not stop in time.")
        self._data_thread = None

        try:
            self._disconnect_from_sensor() # Gọi triển khai cụ thể
        except Exception as e:
            logger.error(f"Error during physical disconnect for sensor {self.name}: {str(e)}", exc_info=True)
            # Vẫn tiếp tục coi như đã ngắt kết nối logic

        self.connected = False
        old_error_message = self.error_message
        self.error_message = "User disconnected" if not old_error_message or "connected" in old_error_message.lower() else old_error_message
        logger.info(f"Sensor {self.name} ({self.sensor_id}) disconnected.")
        if self.on_status_change_callback:
            self.on_status_change_callback(self.sensor_id, False, self.error_message)
        return True

    def get_sensor_info(self) -> Dict[str, Any]:
        return {
            "id": self.sensor_id,
            "name": self.name,
            "type": self.get_sensor_type(),
            "connected": self.connected,
            "config": self.config,
            "error_message": self.error_message,
            "last_data_timestamp": self.data_timestamp
        }

    def get_available_data_keys(self) -> List[str]:
        """Trả về danh sách các key dữ liệu mà cảm biến này có thể cung cấp."""
        # Mặc định, nếu có last_data, trả về các key của nó
        if self.last_data:
            return list(self.last_data.keys())
        return [] # Hoặc một danh sách cố định dựa trên loại cảm biến

    @abstractmethod
    def get_sensor_type(self) -> str:
        pass

    def set_on_data_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Gán callback để được gọi khi có dữ liệu mới."""
        self.on_data_callback = callback

    def set_on_status_change_callback(self, callback: Callable[[str, bool, Optional[str]], None]):
        """Gán callback để được gọi khi trạng thái kết nối thay đổi."""
        self.on_status_change_callback = callback

    def is_alive(self) -> bool:
        """Kiểm tra xem luồng đọc dữ liệu có đang chạy không."""
        return self._data_thread is not None and self._data_thread.is_alive()