import pytest
import numpy as np
from lab_sensor_app.acquisition.sensor_reader import SensorReader

def test_sensor_reader_mock():
    """Test the mock data source."""
    reader = SensorReader(source='MOCK', frame_size=50)
    data = reader.read_frame()
    
    # Check shape
    assert data.shape == (50, 3)
    
    # Check data type
    assert data.dtype == np.float64
    
    # Check value range (mock data is standard normal)
    assert np.all(np.abs(data) < 5)  # 99.9% of values should be within ±5

def test_sensor_reader_uart_no_port():
    """Test that UART source requires a port."""
    with pytest.raises(ValueError):
        SensorReader(source='UART')

def test_sensor_reader_invalid_source():
    """Test that invalid source raises ValueError."""
    with pytest.raises(ValueError):
        reader = SensorReader(source='INVALID')
        reader.read_frame()

def test_sensor_reader_frame_size():
    """Test different frame sizes."""
    for frame_size in [10, 50, 100]:
        reader = SensorReader(source='MOCK', frame_size=frame_size)
        data = reader.read_frame()
        assert data.shape == (frame_size, 3) 