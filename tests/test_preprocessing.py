import pytest
import numpy as np
from lab_sensor_app.preprocessing.rls_detrend import RLSDetrend
from lab_sensor_app.preprocessing.highpass import HighPassFilter

def test_rls_detrend_initialization():
    """Test RLSDetrend initialization and parameter validation."""
    # Test valid parameters
    detrend = RLSDetrend(q=0.99, dt=0.005, order=1)
    assert detrend.q == 0.99
    assert detrend.dt == 0.005
    assert detrend.order == 1
    
    # Test invalid q
    with pytest.raises(ValueError):
        RLSDetrend(q=1.1)
    with pytest.raises(ValueError):
        RLSDetrend(q=0)
        
    # Test invalid order
    with pytest.raises(ValueError):
        RLSDetrend(order=0)

def test_rls_detrend_linear_trend():
    """Test RLSDetrend on data with linear trend."""
    # Generate test data with linear trend
    t = np.linspace(0, 1, 100)
    trend = 2 * t  # Linear trend
    signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
    data = trend + signal
    data = data.reshape(-1, 1)  # Shape (100, 1)
    
    # Apply detrending
    detrend = RLSDetrend(q=0.99, dt=0.01)
    detrended = detrend.preprocess(data)
    
    # Check results
    assert detrended.shape == data.shape
    assert np.all(np.abs(np.mean(detrended)) < 0.1)  # Mean should be close to 0
    assert np.all(np.abs(detrended) < 2)  # Amplitude should be preserved

def test_highpass_initialization():
    """Test HighPassFilter initialization and parameter validation."""
    # Test valid parameters
    filter = HighPassFilter(q=0.99, dt=0.005)
    assert filter.q == 0.99
    assert filter.dt == 0.005
    
    # Test invalid q
    with pytest.raises(ValueError):
        HighPassFilter(q=1.1)
    with pytest.raises(ValueError):
        HighPassFilter(q=0)

def test_highpass_filtering():
    """Test HighPassFilter on mixed frequency data."""
    # Generate test data with low and high frequency components
    t = np.linspace(0, 1, 100)
    low_freq = np.sin(2 * np.pi * 1 * t)  # 1 Hz
    high_freq = 0.5 * np.sin(2 * np.pi * 10 * t)  # 10 Hz
    data = low_freq + high_freq
    data = data.reshape(-1, 1)  # Shape (100, 1)
    
    # Apply filter
    filter = HighPassFilter(q=0.99, dt=0.01)
    filtered = filter.preprocess(data)
    
    # Check results
    assert filtered.shape == data.shape
    # Low frequency component should be attenuated
    assert np.std(filtered) < np.std(data)
    # High frequency component should be preserved
    assert np.max(np.abs(filtered)) > 0.1

def test_preprocessor_channel_consistency():
    """Test that preprocessors maintain consistent channel count."""
    # Create test data
    data1 = np.random.randn(100, 3)  # 3 channels
    data2 = np.random.randn(100, 2)  # 2 channels
    
    # Test RLSDetrend
    detrend = RLSDetrend()
    detrend.preprocess(data1)
    with pytest.raises(ValueError):
        detrend.preprocess(data2)
        
    # Test HighPassFilter
    filter = HighPassFilter()
    filter.preprocess(data1)
    with pytest.raises(ValueError):
        filter.preprocess(data2) 