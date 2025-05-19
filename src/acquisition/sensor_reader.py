import numpy as np
from typing import Optional
import serial
from ..core.interfaces import DataSource

class SensorReader(DataSource):
    """A class for reading sensor data from various sources."""
    
    def __init__(self, source: str = 'MOCK', frame_size: int = 50, 
                 port: Optional[str] = None, baudrate: int = 115200):
        """Initialize the sensor reader.
        
        Args:
            source (str): Data source type ('MOCK', 'UART', etc.)
            frame_size (int): Number of samples per frame
            port (Optional[str]): Serial port for UART communication
            baudrate (int): Baud rate for UART communication
        """
        self.source = source
        self.frame_size = frame_size
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        
        if source == 'UART':
            if port is None:
                raise ValueError("Port must be specified for UART source")
            self.serial = serial.Serial(port, baudrate)
    
    def read_frame(self) -> np.ndarray:
        """Read a frame of sensor data.
        
        Returns:
            np.ndarray: Array of shape (frame_size, 3) containing sensor readings
        """
        if self.source == 'MOCK':
            # Generate mock accelerometer data (x, y, z)
            return np.random.randn(self.frame_size, 3)
        
        elif self.source == 'UART':
            if self.serial is None:
                raise RuntimeError("Serial connection not initialized")
            
            # Read raw data from serial port
            data = []
            for _ in range(self.frame_size):
                if self.serial.in_waiting >= 6:  # 2 bytes per axis * 3 axes
                    x = int.from_bytes(self.serial.read(2), 'little')
                    y = int.from_bytes(self.serial.read(2), 'little')
                    z = int.from_bytes(self.serial.read(2), 'little')
                    data.append([x, y, z])
            
            return np.array(data)
        
        else:
            raise ValueError(f"Unsupported source type: {self.source}")
    
    def __del__(self):
        """Clean up resources."""
        if self.serial is not None:
            self.serial.close()
