# src/core/sensor_processor.py (trích đoạn cập nhật)
import time
import logging
from collections import deque # Sử dụng deque để lưu trữ dữ liệu hiệu quả hơn
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Giới hạn số điểm dữ liệu mỗi kênh trong bộ đệm của SensorProcessor
# Điều này giúp kiểm soát bộ nhớ và hiệu năng khi vẽ đồ thị
# Nên nhỏ hơn hoặc bằng MAX_DATA_POINTS trong các màn hình hiển thị
PROCESSOR_DATA_BUFFER_SIZE = 2000 # Ví dụ: giữ lại 2000 điểm dữ liệu gần nhất cho mỗi kênh

class SensorProcessor:
    def __init__(self):
        self.active_sensors_config: Dict[str, Dict[str, Any]] = {} # sensor_id -> sensor_info (bao gồm config)
        # self.latest_sensor_data: Dict[str, Dict[str, Any]] = {} # sensor_id -> {data_key: value}
        # Thay thế latest_sensor_data bằng cấu trúc lưu trữ chuỗi thời gian ngắn hạn
        self.sensor_data_buffers: Dict[str, Dict[str, deque]] = {} # sensor_id -> {data_key: deque([(timestamp, value), ...])}
        self.data_keys_by_sensor: Dict[str, List[str]] = {} # sensor_id -> [key1, key2]

        self.alerts: List[Dict[str, Any]] = []
        self.fps_counter = 0
        self.last_fps_update_time = time.perf_counter()
        self.current_fps = 0.0
        self.global_data_timestamp = 0.0 # Timestamp của gói dữ liệu gần nhất được xử lý

    def add_sensor(self, sensor_id: str, sensor_info: Dict[str, Any]):
        if sensor_id not in self.active_sensors_config:
            self.active_sensors_config[sensor_id] = sensor_info
            self.sensor_data_buffers[sensor_id] = {} # Khởi tạo buffer cho sensor mới
            # Lấy data_keys từ sensor_info (cần BaseSensor cung cấp qua get_sensor_info hoặc một phương thức riêng)
            # Hoặc để nó tự động được điền khi dữ liệu đầu tiên đến.
            # Giả sử sensor_info["available_data_keys"] chứa list các key
            self.data_keys_by_sensor[sensor_id] = sensor_info.get("available_data_keys", [])
            for key in self.data_keys_by_sensor[sensor_id]:
                self.sensor_data_buffers[sensor_id][key] = deque(maxlen=PROCESSOR_DATA_BUFFER_SIZE)

            logger.info(f"Sensor {sensor_info.get('name', sensor_id)} added to processor. Known keys: {self.data_keys_by_sensor[sensor_id]}")
        else:
            logger.warning(f"Sensor {sensor_id} already in processor, updating config.")
            self.active_sensors_config[sensor_id].update(sensor_info) # Cập nhật nếu thông tin thay đổi

    def remove_sensor(self, sensor_id: str):
        if sensor_id in self.active_sensors_config:
            del self.active_sensors_config[sensor_id]
            if sensor_id in self.sensor_data_buffers:
                del self.sensor_data_buffers[sensor_id]
            if sensor_id in self.data_keys_by_sensor:
                del self.data_keys_by_sensor[sensor_id]
            logger.info(f"Sensor {sensor_id} removed from processor.")
        else:
            logger.warning(f"Attempted to remove non-existent sensor {sensor_id} from processor.")

    def update_sensor_data(self, sensor_id: str, data: Dict[str, Any], timestamp: Optional[float] = None):
        if sensor_id not in self.active_sensors_config:
            # logger.warning(f"Data received for unknown/inactive sensor: {sensor_id}")
            return

        if timestamp is None:
            timestamp = time.time() # Sử dụng thời gian hệ thống nếu không có timestamp từ cảm biến
        self.global_data_timestamp = timestamp # Cập nhật timestamp toàn cục

        if sensor_id not in self.sensor_data_buffers:
            self.sensor_data_buffers[sensor_id] = {} # Khởi tạo nếu chưa có (có thể xảy ra nếu add_sensor chưa kịp chạy)

        for key, value in data.items():
            if key not in self.sensor_data_buffers[sensor_id]:
                self.sensor_data_buffers[sensor_id][key] = deque(maxlen=PROCESSOR_DATA_BUFFER_SIZE)
                if sensor_id in self.data_keys_by_sensor and key not in self.data_keys_by_sensor[sensor_id]:
                    self.data_keys_by_sensor[sensor_id].append(key)
                    logger.info(f"Discovered new data key '{key}' for sensor {sensor_id}")

            self.sensor_data_buffers[sensor_id][key].append((timestamp, value))

        self.fps_counter += 1
        current_time = time.perf_counter()
        if current_time - self.last_fps_update_time >= 1.0: # Cập nhật FPS mỗi giây
            self.current_fps = self.fps_counter / (current_time - self.last_fps_update_time)
            self.fps_counter = 0
            self.last_fps_update_time = current_time
            # logger.debug(f"Processor FPS: {self.current_fps:.2f}")

    def get_data_for_display(self, sensor_id: str, data_key: str, num_points: Optional[int] = None) -> Tuple[Optional[List[float]], Optional[List[Any]]]:
        """
        Lấy dữ liệu (timestamps, values) cho một kênh cụ thể của một cảm biến.
        Args:
            sensor_id: ID của cảm biến.
            data_key: Key của dữ liệu (ví dụ: "accX", "temperature").
            num_points: Số lượng điểm dữ liệu gần nhất muốn lấy. Nếu None, lấy tất cả trong buffer.
        Returns:
            Tuple (timestamps, values) hoặc (None, None) nếu không có dữ liệu.
        """
        if sensor_id in self.sensor_data_buffers and data_key in self.sensor_data_buffers[sensor_id]:
            buffer = self.sensor_data_buffers[sensor_id][data_key]
            if not buffer:
                return None, None

            if num_points is None or num_points >= len(buffer):
                timestamps, values = zip(*list(buffer))
            else:
                # Lấy num_points cuối cùng
                selected_data = list(buffer)[-num_points:]
                if not selected_data: return None, None
                timestamps, values = zip(*selected_data)
            return list(timestamps), list(values)
        return None, None

    def get_latest_value(self, sensor_id: str, data_key: str) -> Optional[Any]:
        if sensor_id in self.sensor_data_buffers and \
           data_key in self.sensor_data_buffers[sensor_id] and \
           self.sensor_data_buffers[sensor_id][data_key]:
            return self.sensor_data_buffers[sensor_id][data_key][-1][1] # Trả về value của (timestamp, value) cuối cùng
        return None


    def get_all_available_data_streams(self) -> Dict[str, List[str]]:
        """
        Trả về một dictionary: {sensor_id: [data_key1, data_key2,...]}
        """
        streams = {}
        for sensor_id, keys in self.data_keys_by_sensor.items():
            sensor_name = self.active_sensors_config.get(sensor_id, {}).get('name', sensor_id)
            streams[f"{sensor_name} ({sensor_id})"] = keys # Hiển thị cả tên và ID cho dễ chọn
        return streams


    def get_active_sensors_info(self) -> List[Dict[str, Any]]:
        return list(self.active_sensors_config.values())

    def get_fps(self) -> float:
        return self.current_fps

    def get_latest_alerts(self) -> List[Dict[str, Any]]:
        # Cần có logic tạo alerts nếu ứng dụng có chức năng này
        return self.alerts # Hiện tại là rỗng