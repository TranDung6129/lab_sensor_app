import pytest
import numpy as np
from lab_sensor_app.preprocessing.smoothing import MovingAverage, ExponentialSmoothing, KalmanFilter

def test_moving_average_initialization():
    """Test MovingAverage initialization and parameter validation."""
    # Test valid parameters
    ma = MovingAverage(window_size=5)
    assert ma.window_size == 5
    
    # Test invalid window size
    with pytest.raises(ValueError):
        MovingAverage(window_size=0)

def test_moving_average_smoothing():
    """Test MovingAverage on noisy data."""
    # Generate test data with noise
    t = np.linspace(0, 1, 100)
    signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
    noise = 0.2 * np.random.randn(100)
    data = signal + noise
    data = data.reshape(-1, 1)  # Shape (100, 1)
    
    # Apply moving average
    ma = MovingAverage(window_size=5)
    smoothed = ma.preprocess(data)
    
    # Check results
    assert smoothed.shape == data.shape
    assert np.std(smoothed) < np.std(data)  # Should reduce noise
    assert np.all(np.abs(smoothed) < 1.5)  # Should preserve signal amplitude

def test_exponential_smoothing_initialization():
    """Test ExponentialSmoothing initialization and parameter validation."""
    # Test valid parameters
    es = ExponentialSmoothing(alpha=0.3)
    assert es.alpha == 0.3
    
    # Test invalid alpha
    with pytest.raises(ValueError):
        ExponentialSmoothing(alpha=1.1)
    with pytest.raises(ValueError):
        ExponentialSmoothing(alpha=0)

def test_exponential_smoothing():
    """Test ExponentialSmoothing on step response."""
    # Generate step response data
    data = np.zeros((100, 1))
    data[50:] = 1  # Step at t=50
    
    # Apply exponential smoothing
    es = ExponentialSmoothing(alpha=0.3)
    smoothed = es.preprocess(data)
    
    # Check results
    assert smoothed.shape == data.shape
    assert smoothed[0] == 0  # Initial value
    assert smoothed[-1] > 0.9  # Should approach final value
    assert np.all(np.diff(smoothed[50:]) >= 0)  # Should be monotonic

def test_kalman_filter_initialization():
    """Test KalmanFilter initialization."""
    kf = KalmanFilter(process_noise=0.1, measurement_noise=1.0)
    assert kf.Q == 0.1
    assert kf.R == 1.0

def test_kalman_filter():
    """Test KalmanFilter on noisy constant signal."""
    # Generate constant signal with noise
    signal = np.ones((100, 1))
    noise = 0.5 * np.random.randn(100, 1)
    data = signal + noise
    
    # Apply Kalman filter
    kf = KalmanFilter(process_noise=0.1, measurement_noise=1.0)
    filtered = kf.preprocess(data)
    
    # Check results
    assert filtered.shape == data.shape
    assert np.std(filtered) < np.std(data)  # Should reduce noise
    assert np.all(np.abs(filtered - 1) < 0.5)  # Should track true value

def test_smoothing_channel_consistency():
    """Test that smoothing filters maintain consistent channel count."""
    # Create test data
    data1 = np.random.randn(100, 3)  # 3 channels
    data2 = np.random.randn(100, 2)  # 2 channels
    
    # Test MovingAverage
    ma = MovingAverage()
    ma.preprocess(data1)
    with pytest.raises(ValueError):
        ma.preprocess(data2)
        
    # Test ExponentialSmoothing
    es = ExponentialSmoothing()
    es.preprocess(data1)
    with pytest.raises(ValueError):
        es.preprocess(data2)
        
    # Test KalmanFilter
    kf = KalmanFilter()
    kf.preprocess(data1)
    with pytest.raises(ValueError):
        kf.preprocess(data2) 