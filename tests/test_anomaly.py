import pytest
import numpy as np
from lab_sensor_app.anomaly.threshold_detector import ThresholdDetector
from lab_sensor_app.anomaly.statistical_detector import StatisticalDetector

def test_threshold_detector_initialization():
    """Test ThresholdDetector initialization and parameter validation."""
    # Test valid parameters
    detector = ThresholdDetector(lower_threshold=-1.0, upper_threshold=1.0, window_size=3)
    assert detector.lower_threshold == -1.0
    assert detector.upper_threshold == 1.0
    assert detector.window_size == 3
    
    # Test with array thresholds
    detector = ThresholdDetector(
        lower_threshold=np.array([-1.0, -2.0]),
        upper_threshold=np.array([1.0, 2.0])
    )
    assert np.array_equal(detector.lower_threshold, np.array([-1.0, -2.0]))
    assert np.array_equal(detector.upper_threshold, np.array([1.0, 2.0]))

def test_threshold_detection():
    """Test ThresholdDetector on data with known anomalies."""
    # Create test data
    n_samples = 1000
    n_channels = 2
    data = np.zeros((n_samples, n_channels))
    
    # Add anomalies
    data[100:110, 0] = 2.0  # Upper threshold exceedance
    data[200:210, 1] = -2.0  # Lower threshold exceedance
    
    # Initialize detector
    detector = ThresholdDetector(
        lower_threshold=-1.0,
        upper_threshold=1.0,
        window_size=3
    )
    
    # Detect anomalies
    result = detector.detect(data, 0.01)
    
    # Check results
    assert 'anomalies' in result
    assert 'scores' in result
    
    # Check anomaly detection
    assert np.any(result['anomalies'][100:110, 0])  # Upper threshold
    assert np.any(result['anomalies'][200:210, 1])  # Lower threshold
    
    # Check scores
    assert np.all(result['scores'][100:110, 0] > 0)  # Positive scores for upper exceedance
    assert np.all(result['scores'][200:210, 1] > 0)  # Positive scores for lower exceedance

def test_statistical_detector_initialization():
    """Test StatisticalDetector initialization and parameter validation."""
    # Test valid parameters
    detector = StatisticalDetector(window_size=100, threshold_std=3.0, min_samples=10)
    assert detector.window_size == 100
    assert detector.threshold_std == 3.0
    assert detector.min_samples == 10

def test_statistical_detection():
    """Test StatisticalDetector on data with known anomalies."""
    # Create test data
    n_samples = 1000
    n_channels = 2
    data = np.random.normal(0, 1, (n_samples, n_channels))
    
    # Add anomalies
    data[100:110, 0] = 5.0  # Large positive anomaly
    data[200:210, 1] = -5.0  # Large negative anomaly
    
    # Initialize detector
    detector = StatisticalDetector(window_size=50, threshold_std=3.0)
    
    # Detect anomalies
    result = detector.detect(data, 0.01)
    
    # Check results
    assert 'anomalies' in result
    assert 'scores' in result
    
    # Check anomaly detection
    assert np.any(result['anomalies'][100:110, 0])  # Positive anomaly
    assert np.any(result['anomalies'][200:210, 1])  # Negative anomaly
    
    # Check scores
    assert np.all(result['scores'][100:110, 0] > 1.0)  # High scores for anomalies
    assert np.all(result['scores'][200:210, 1] > 1.0)  # High scores for anomalies

def test_detector_channel_consistency():
    """Test that detectors maintain consistent channel count."""
    # Create test data
    data1 = np.random.randn(1000, 3)  # 3 channels
    data2 = np.random.randn(1000, 2)  # 2 channels
    
    # Test ThresholdDetector
    threshold_detector = ThresholdDetector(lower_threshold=-1.0, upper_threshold=1.0)
    threshold_detector.detect(data1, 0.01)
    with pytest.raises(ValueError):
        threshold_detector.detect(data2, 0.01)
        
    # Test StatisticalDetector
    statistical_detector = StatisticalDetector(window_size=50)
    statistical_detector.detect(data1, 0.01)
    with pytest.raises(ValueError):
        statistical_detector.detect(data2, 0.01) 