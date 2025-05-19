import pytest
import numpy as np
from lab_sensor_app.estimation.fft_estimator import FFTEstimator
from lab_sensor_app.estimation.goertzel_estimator import GoertzelEstimator

def test_fft_initialization():
    """Test FFTEstimator initialization and parameter validation."""
    # Test valid parameters
    fft = FFTEstimator(fs=200.0, window='hann')
    assert fft.fs == 200.0
    assert fft.window == 'hann'
    
    # Test invalid window
    with pytest.raises(AttributeError):
        FFTEstimator(fs=200.0, window='invalid_window')

def test_fft_estimation():
    """Test FFTEstimator on mixed frequency data."""
    # Generate test data with multiple frequencies
    fs = 200.0
    n_samples = 1000
    t = np.linspace(0, n_samples/fs, n_samples)
    
    # Create signal with two frequencies
    f1, f2 = 10.0, 30.0  # Hz
    a1, a2 = 1.0, 0.5    # amplitudes
    signal = a1 * np.sin(2 * np.pi * f1 * t) + a2 * np.sin(2 * np.pi * f2 * t)
    data = signal.reshape(-1, 1)  # Shape (1000, 1)
    
    # Apply FFT estimator
    fft = FFTEstimator(fs=fs)
    result = fft.estimate(data, 1/fs)
    
    # Check results
    assert 'frequencies' in result
    assert 'amplitudes' in result
    
    # Find peaks
    freqs = result['frequencies']
    amps = result['amplitudes'][:, 0]  # First channel
    
    # Find indices of peaks
    peak_indices = np.argsort(amps)[-2:]  # Two highest peaks
    peak_freqs = freqs[peak_indices]
    peak_amps = amps[peak_indices]
    
    # Check if peaks are at correct frequencies
    assert np.min(np.abs(peak_freqs - f1)) < 1.0  # Within 1 Hz
    assert np.min(np.abs(peak_freqs - f2)) < 1.0  # Within 1 Hz
    
    # Check if amplitudes are correct (within 20%)
    assert np.min(np.abs(peak_amps - a1)) < 0.2 * a1
    assert np.min(np.abs(peak_amps - a2)) < 0.2 * a2

def test_goertzel_initialization():
    """Test GoertzelEstimator initialization and parameter validation."""
    # Test valid parameters
    goertzel = GoertzelEstimator(target_freq=50.0, fs=200.0)
    assert goertzel.target_freq == 50.0
    assert goertzel.fs == 200.0
    
    # Test invalid frequency
    with pytest.raises(ValueError):
        GoertzelEstimator(target_freq=0, fs=200.0)
    with pytest.raises(ValueError):
        GoertzelEstimator(target_freq=150, fs=200.0)

def test_goertzel_estimation():
    """Test GoertzelEstimator on single frequency data."""
    # Generate test data
    fs = 200.0
    n_samples = 1000
    t = np.linspace(0, n_samples/fs, n_samples)
    
    # Create signal with target frequency
    target_freq = 50.0  # Hz
    amplitude = 1.0
    signal = amplitude * np.sin(2 * np.pi * target_freq * t)
    data = signal.reshape(-1, 1)  # Shape (1000, 1)
    
    # Apply Goertzel estimator
    goertzel = GoertzelEstimator(target_freq=target_freq, fs=fs)
    result = goertzel.estimate(data, 1/fs)
    
    # Check results
    assert 'frequency' in result
    assert 'amplitude' in result
    
    # Check frequency
    assert np.all(result['frequency'] == target_freq)
    
    # Check amplitude (within 20%)
    assert np.abs(result['amplitude'][0, 0] - amplitude) < 0.2 * amplitude

def test_estimator_channel_consistency():
    """Test that estimators maintain consistent channel count."""
    # Create test data
    data1 = np.random.randn(1000, 3)  # 3 channels
    data2 = np.random.randn(1000, 2)  # 2 channels
    
    # Test FFTEstimator
    fft = FFTEstimator(fs=200.0)
    fft.estimate(data1, 0.01)
    with pytest.raises(ValueError):
        fft.estimate(data2, 0.01)
        
    # Test GoertzelEstimator
    goertzel = GoertzelEstimator(target_freq=50.0, fs=200.0)
    goertzel.estimate(data1, 0.01)
    with pytest.raises(ValueError):
        goertzel.estimate(data2, 0.01) 