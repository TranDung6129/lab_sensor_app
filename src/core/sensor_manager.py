# src/core/sensor_manager.py (trích đoạn cập nhật)
import logging
from typing import Dict, List, Type, Optional, Callable, Any
# Giả sử các lớp cảm biến đã được import
from .sensors.base_sensor import BaseSensor, SensorConnectionError
from .sensors.witmotion_uart_sensor import WitMotionUARTSensor
# from .sensors.your_other_sensor import YourOtherSensor
# from .sensors.mock_sensor import MockSensor # Thêm MockSensor

logger = logging.getLogger(__name__)

class SensorManager:
    def __init__(self, sensor_processor): # Truyền sensor_processor vào
        self.sensors: Dict[str, BaseSensor] = {} # sensor_id -> SensorInstance
        self.sensor_processor = sensor_processor
        self.sensor_types: Dict[str, Type[BaseSensor]] = {
            "WitMotion_UART": WitMotionUARTSensor,
            # "Your_Other_Sensor_Type": YourOtherSensor,
            # "Mock": MockSensor, # Thêm Mock sensor vào đây
        }
        self.on_sensor_list_changed_callback: Optional[Callable] = None # Callback khi danh sách sensor thay đổi
        self.on_sensor_status_updated_callback: Optional[Callable[[str], None]] = None # Callback khi trạng thái sensor thay đổi


    def set_callbacks(self, on_list_changed: Callable, on_status_updated: Callable[[str], None]):
        self.on_sensor_list_changed_callback = on_list_changed
        self.on_sensor_status_updated_callback = on_status_updated

    def add_sensor(self, sensor_id: str, name: str, sensor_type_str: str, config: Dict[str, Any]) -> bool:
        if sensor_id in self.sensors:
            logger.warning(f"Sensor with ID {sensor_id} already exists.")
            # Có thể cập nhật config và thử reconnect nếu muốn
            existing_sensor = self.sensors[sensor_id]
            if existing_sensor.get_sensor_type() == sensor_type_str:
                logger.info(f"Updating config for existing sensor {sensor_id} and attempting to reconnect.")
                existing_sensor.disconnect() # Ngắt kết nối cũ
                existing_sensor.config = config # Cập nhật config
                existing_sensor.name = name
                # Không cần gọi lại set_on_data_callback và set_on_status_change_callback nếu đã gọi 1 lần
                return existing_sensor.connect()
            else:
                logger.error(f"Cannot change sensor type for existing ID {sensor_id}.")
                return False

        if sensor_type_str not in self.sensor_types:
            logger.error(f"Unknown sensor type: {sensor_type_str}")
            return False

        SensorClass = self.sensor_types[sensor_type_str]
        try:
            sensor_instance = SensorClass(sensor_id, name, config)
            sensor_instance.set_on_data_callback(self._handle_sensor_data)
            sensor_instance.set_on_status_change_callback(self._handle_sensor_status_change)

            if sensor_instance.connect(): # connect() giờ sẽ start thread đọc dữ liệu
                self.sensors[sensor_id] = sensor_instance
                # sensor_processor được thông báo qua _handle_sensor_data
                logger.info(f"Sensor {name} (ID: {sensor_id}, Type: {sensor_type_str}) added and connected.")
                if self.on_sensor_list_changed_callback:
                    self.on_sensor_list_changed_callback()
                return True
            else:
                logger.error(f"Failed to connect sensor {name} (ID: {sensor_id}). Error: {sensor_instance.error_message}")
                # Không thêm vào self.sensors nếu kết nối thất bại
                return False
        except Exception as e:
            logger.error(f"Error instantiating or connecting sensor {name} (ID: {sensor_id}): {e}", exc_info=True)
            return False

    def _handle_sensor_data(self, sensor_id: str, data: Dict[str, Any]):
        if sensor_id in self.sensors and self.sensor_processor:
            # logger.debug(f"Data from {sensor_id}: {data}") # Log này có thể rất nhiều
            self.sensor_processor.update_sensor_data(sensor_id, data, self.sensors[sensor_id].data_timestamp)
        # else:
        #     logger.warning(f"Received data for unknown or inactive sensor_id: {sensor_id}")

    def _handle_sensor_status_change(self, sensor_id: str, connected: bool, error_message: Optional[str]):
        logger.info(f"Status change for sensor {sensor_id}: Connected={connected}, Error='{error_message}'")
        if sensor_id in self.sensors:
            self.sensors[sensor_id].connected = connected # Đảm bảo trạng thái trong manager được cập nhật
            self.sensors[sensor_id].error_message = error_message
        if self.on_sensor_status_updated_callback:
            self.on_sensor_status_updated_callback(sensor_id) # Báo cho UI cập nhật trạng thái của sensor này
        if self.on_sensor_list_changed_callback: # Cũng có thể cần cập nhật lại list nếu trạng thái thay đổi quan trọng
            self.on_sensor_list_changed_callback()


    def remove_sensor(self, sensor_id: str) -> bool:
        if sensor_id in self.sensors:
            sensor_instance = self.sensors[sensor_id]
            logger.info(f"Attempting to remove sensor {sensor_instance.name} (ID: {sensor_id}).")
            sensor_instance.disconnect() # Điều này sẽ dừng thread đọc dữ liệu
            del self.sensors[sensor_id]
            if self.sensor_processor:
                self.sensor_processor.remove_sensor(sensor_id)
            logger.info(f"Sensor {sensor_id} removed.")
            if self.on_sensor_list_changed_callback:
                self.on_sensor_list_changed_callback()
            return True
        logger.warning(f"Sensor {sensor_id} not found for removal.")
        return False

    def get_sensor_instance(self, sensor_id: str) -> Optional[BaseSensor]:
        return self.sensors.get(sensor_id)

    def get_all_sensor_info(self) -> List[Dict[str, Any]]:
        return [s.get_sensor_info() for s in self.sensors.values()]

    def get_sensor_info(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        sensor = self.get_sensor_instance(sensor_id)
        return sensor.get_sensor_info() if sensor else None

    def get_available_sensor_types(self) -> List[str]:
        return list(self.sensor_types.keys())

    def send_command_to_sensor(self, sensor_id: str, command_type: str, params: Dict[str, Any]) -> bool:
        sensor = self.get_sensor_instance(sensor_id)
        if sensor:
            logger.info(f"Sending command '{command_type}' with params {params} to sensor {sensor.name} (ID: {sensor_id})")
            try:
                return sensor.send_config_command(command_type, params)
            except Exception as e:
                logger.error(f"Error sending command to sensor {sensor_id}: {e}", exc_info=True)
                return False
        logger.warning(f"Sensor {sensor_id} not found to send command.")
        return False

    def stop_all_sensors(self):
        logger.info("Stopping all sensors...")
        for sensor_id in list(self.sensors.keys()): # list() để tránh lỗi thay đổi dict khi lặp
            self.remove_sensor(sensor_id)
        logger.info("All sensors stopped.")