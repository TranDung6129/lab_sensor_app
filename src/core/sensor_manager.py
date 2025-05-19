from typing import Dict, List, Type
import logging
from .sensors.base_sensor import BaseSensor
from .sensors.accelerometer import AccelerometerSensor
from .sensors.temperature import TemperatureSensor

logger = logging.getLogger(__name__)

class SensorManager:
    """Manages sensor connections and configurations."""
    
    def __init__(self):
        self.sensors: Dict[str, BaseSensor] = {}
        self.sensor_types: Dict[str, Type[BaseSensor]] = {
            "accelerometer": AccelerometerSensor,
            "temperature": TemperatureSensor,
            # Add more sensor types here
        }
        
    def add_sensor(self, sensor_id: str, sensor_type: str, config: dict) -> bool:
        """Add a new sensor with specified type."""
        try:
            if sensor_type not in self.sensor_types:
                logger.error(f"Unknown sensor type: {sensor_type}")
                return False
                
            sensor_class = self.sensor_types[sensor_type]
            sensor = sensor_class(sensor_id, config)
            
            if sensor.connect():
                self.sensors[sensor_id] = sensor
                logger.info(f"Added sensor {sensor_id} of type {sensor_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding sensor {sensor_id}: {e}")
            return False
            
    def remove_sensor(self, sensor_id: str) -> bool:
        """Remove a sensor."""
        try:
            if sensor_id in self.sensors:
                self.sensors[sensor_id].disconnect()
                del self.sensors[sensor_id]
                logger.info(f"Removed sensor {sensor_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing sensor {sensor_id}: {e}")
            return False
            
    def read_sensor_data(self, sensor_id: str) -> dict:
        """Read data from a specific sensor."""
        try:
            if sensor_id in self.sensors:
                return self.sensors[sensor_id].read_data()
            return {}
        except Exception as e:
            logger.error(f"Error reading sensor {sensor_id}: {e}")
            return {}
            
    def get_available_sensor_types(self) -> List[str]:
        """Get list of available sensor types."""
        return list(self.sensor_types.keys())
        
    def get_sensor_info(self, sensor_id: str) -> dict:
        """Get information about a specific sensor."""
        try:
            if sensor_id in self.sensors:
                return self.sensors[sensor_id].get_sensor_info()
            return {}
        except Exception as e:
            logger.error(f"Error getting sensor info for {sensor_id}: {e}")
            return {} 