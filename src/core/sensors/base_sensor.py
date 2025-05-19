from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseSensor(ABC):
    """Abstract base class for all sensor types."""
    
    def __init__(self, sensor_id: str, config: Dict[str, Any]):
        self.sensor_id = sensor_id
        self.config = config
        self.connected = False
        self.last_data: Optional[Dict[str, Any]] = None
        
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the sensor."""
        pass
        
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the sensor."""
        pass
        
    @abstractmethod
    def read_data(self) -> Dict[str, Any]:
        """Read data from the sensor."""
        pass
        
    @abstractmethod
    def get_sensor_type(self) -> str:
        """Get the type of sensor."""
        pass
        
    def get_sensor_info(self) -> Dict[str, Any]:
        """Get sensor information."""
        return {
            "id": self.sensor_id,
            "type": self.get_sensor_type(),
            "connected": self.connected,
            "config": self.config
        } 