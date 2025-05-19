import pytest
import numpy as np
from scipy import signal
from lab_sensor_app.preprocessing.bandpass import BandPassFilter
from lab_sensor_app.preprocessing.notch import NotchFilter
from lab_sensor_app.preprocessing.lowpass import LowPassFilter

def test_bandpass_initialization():
    """Test BandPassFilter initialization and parameter validation."""
    # Test valid parameters
    bp = BandPassFilter(low_freq=10, high_freq=50, fs=200)
    assert bp.low_freq == 10
    assert bp.high_freq == 50
    assert bp.fs == 200
    
    # Test invalid frequency range
    with pytest.raises(ValueError):
        BandPassFilter(low_freq=50, high_freq=10)
    with pytest.raises(ValueError):
        BandPassFilter(low_freq=0, high_freq=50)
    with pytest.raises(ValueError):
        BandPassFilter(low_freq=10, high_freq=150, fs=200)

def test_bandpass_filtering():
    """Test BandPassFilter on mixed frequency data."""
    # Generate test data with multiple frequencies
    fs = 200
    t = np.linspace(0, 1, fs)
    low_freq = np.sin(2 * np.pi * 5 * t)  # 5 Hz
    mid_freq = 0.5 * np.sin(2 * np.pi * 20 * t)  # 20 Hz
    high_freq = 0.25 * np.sin(2 * np.pi * 60 * t)  # 60 Hz
    data = low_freq + mid_freq + high_freq
    data = data.reshape(-1, 1)  # Shape (200, 1)
    
    # Apply band-pass filter
    bp = BandPassFilter(low_freq=10, high_freq=30, fs=fs)
    filtered = bp.preprocess(data)
    
    # Check results
    assert filtered.shape == data.shape
    # Low and high frequencies should be attenuated
    assert np.std(filtered) < np.std(data)
    # Mid frequency should be preserved
    assert np.max(np.abs(filtered)) > 0.1

def test_notch_initialization():
    """Test NotchFilter initialization and parameter validation."""
    # Test valid parameters
    notch = NotchFilter(freq=50, quality_factor=30, fs=200)
    assert notch.freq == 50
    assert notch.quality_factor == 30
    assert notch.fs == 200
    
    # Test invalid parameters
    with pytest.raises(ValueError):
        NotchFilter(freq=0, fs=200)
    with pytest.raises(ValueError):
        NotchFilter(freq=150, fs=200)
    with pytest.raises(ValueError):
        NotchFilter(freq=50, quality_factor=0)

def test_notch_filtering():
    """Test NotchFilter on data with specific frequency."""
    # Generate test data with target frequency
    fs = 200
    t = np.linspace(0, 1, fs)
    target_freq = np.sin(2 * np.pi * 50 * t)  # 50 Hz
    other_freq = 0.5 * np.sin(2 * np.pi * 20 * t)  # 20 Hz
    data = target_freq + other_freq
    data = data.reshape(-1, 1)  # Shape (200, 1)
    
    # Apply notch filter
    notch = NotchFilter(freq=50, quality_factor=30, fs=fs)
    filtered = notch.preprocess(data)
    
    # Check results
    assert filtered.shape == data.shape
    # Target frequency should be attenuated
    assert np.std(filtered) < np.std(data)
    # Other frequency should be preserved
    assert np.max(np.abs(filtered)) > 0.1

def test_lowpass_initialization():
    """Test LowPassFilter initialization and parameter validation."""
    # Test valid parameters
    lp = LowPassFilter(cutoff_freq=50, fs=200)
    assert lp.cutoff_freq == 50
    assert lp.fs == 200
    
    # Test invalid parameters
    with pytest.raises(ValueError):
        LowPassFilter(cutoff_freq=0, fs=200)
    with pytest.raises(ValueError):
        LowPassFilter(cutoff_freq=150, fs=200)

def test_lowpass_filtering():
    """Test LowPassFilter on mixed frequency data."""
    # Generate test data with multiple frequencies
    fs = 200
    t = np.linspace(0, 1, fs)
    low_freq = np.sin(2 * np.pi * 5 * t)  # 5 Hz
    high_freq = 0.5 * np.sin(2 * np.pi * 50 * t)  # 50 Hz
    data = low_freq + high_freq
    data = data.reshape(-1, 1)  # Shape (200, 1)
    
    # Apply low-pass filter
    lp = LowPassFilter(cutoff_freq=20, fs=fs)
    filtered = lp.preprocess(data)
    
    # Check results
    assert filtered.shape == data.shape
    # High frequency should be attenuated
    assert np.std(filtered) < np.std(data)
    # Low frequency should be preserved
    assert np.max(np.abs(filtered)) > 0.1

def test_filter_channel_consistency():
    """Test that filters maintain consistent channel count."""
    # Create test data
    data1 = np.random.randn(100, 3)  # 3 channels
    data2 = np.random.randn(100, 2)  # 2 channels
    
    # Test BandPassFilter
    bp = BandPassFilter(low_freq=10, high_freq=50)
    bp.preprocess(data1)
    with pytest.raises(ValueError):
        bp.preprocess(data2)
        
    # Test NotchFilter
    notch = NotchFilter(freq=50)
    notch.preprocess(data1)
    with pytest.raises(ValueError):
        notch.preprocess(data2)
        
    # Test LowPassFilter
    lp = LowPassFilter(cutoff_freq=50)
    lp.preprocess(data1)
    with pytest.raises(ValueError):
        lp.preprocess(data2) 