from typing import Dict, List, Optional
import logging
import time

logger = logging.getLogger(__name__)

class SensorProcessor:
    """Handles sensor data processing and management."""
    
    def __init__(self):
        self.active_sensors: Dict[str, dict] = {}
        self.latest_data: Dict[str, dict] = {}
        self.alerts: List[dict] = []
        self.fps = 0
        self.last_update_time = time.time()
        
    def add_sensor(self, sensor_id: str, sensor_config: dict) -> bool:
        """Add a new sensor to the processor."""
        try:
            self.active_sensors[sensor_id] = sensor_config
            logger.info(f"Added sensor {sensor_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding sensor {sensor_id}: {e}")
            return False
            
    def remove_sensor(self, sensor_id: str) -> bool:
        """Remove a sensor from the processor."""
        try:
            if sensor_id in self.active_sensors:
                del self.active_sensors[sensor_id]
                logger.info(f"Removed sensor {sensor_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing sensor {sensor_id}: {e}")
            return False
            
    def update_sensor_data(self, sensor_id: str, data: dict) -> None:
        """Update sensor data."""
        try:
            if sensor_id in self.active_sensors:
                self.latest_data[sensor_id] = data
                self._update_fps()
        except Exception as e:
            logger.error(f"Error updating sensor data for {sensor_id}: {e}")
            
    def get_active_sensors(self) -> List[str]:
        """Get list of active sensor IDs."""
        return list(self.active_sensors.keys())
        
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps
        
    def get_latest_data(self) -> Dict[str, dict]:
        """Get latest data from all sensors."""
        return self.latest_data
        
    def get_latest_alerts(self) -> List[dict]:
        """Get latest alerts."""
        return self.alerts
        
    def _update_fps(self) -> None:
        """Update FPS calculation."""
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        if time_diff > 0:
            self.fps = 1.0 / time_diff
        self.last_update_time = current_time 