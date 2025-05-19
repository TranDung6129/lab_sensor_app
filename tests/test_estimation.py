import pytest
import numpy as np
from lab_sensor_app.estimation.kalman import KalmanFilter
from lab_sensor_app.estimation.ekf import ExtendedKalmanFilter

def test_kalman_initialization():
    """Test KalmanFilter initialization and parameter validation."""
    # Test valid parameters
    kf = KalmanFilter(n_states=6, n_measurements=3)
    assert kf.n_states == 6
    assert kf.n_measurements == 3
    
    # Test invalid parameters
    with pytest.raises(ValueError):
        KalmanFilter(n_states=0, n_measurements=3)
    with pytest.raises(ValueError):
        KalmanFilter(n_states=6, n_measurements=0)

def test_kalman_filtering():
    """Test KalmanFilter on simulated data."""
    # Generate test data (constant acceleration)
    n_samples = 100
    dt = 0.01
    t = np.linspace(0, dt * n_samples, n_samples)
    acceleration = 1.0  # m/s^2
    velocity = acceleration * t
    position = 0.5 * acceleration * t**2
    
    # Add noise
    noise = np.random.normal(0, 0.1, n_samples)
    measurements = position + noise
    measurements = measurements.reshape(-1, 1)  # Shape (100, 1)
    
    # Apply Kalman filter
    kf = KalmanFilter(n_states=6, n_measurements=3)
    estimates = kf.estimate(measurements, dt)
    
    # Check results
    assert 'position' in estimates
    assert 'velocity' in estimates
    assert 'acceleration' in estimates
    
    # Position should track true position
    assert np.mean(np.abs(estimates['position'] - position.reshape(-1, 1))) < 0.5
    
    # Velocity should track true velocity
    assert np.mean(np.abs(estimates['velocity'] - velocity.reshape(-1, 1))) < 0.5
    
    # Acceleration should be close to true acceleration
    assert np.mean(np.abs(estimates['acceleration'] - acceleration)) < 0.5

def test_ekf_initialization():
    """Test ExtendedKalmanFilter initialization and parameter validation."""
    # Define test functions
    def state_transition(x, dt):
        # Constant acceleration model
        x_next = x.copy()
        x_next[0] += x[2] * dt + 0.5 * x[4] * dt**2  # position
        x_next[1] += x[3] * dt + 0.5 * x[5] * dt**2  # position
        x_next[2] += x[4] * dt  # velocity
        x_next[3] += x[5] * dt  # velocity
        return x_next
        
    def measurement_function(x):
        # Direct position measurement
        return np.array([x[0], x[1]])
    
    # Test valid parameters
    ekf = ExtendedKalmanFilter(n_states=6, n_measurements=2,
                              state_transition=state_transition,
                              measurement_function=measurement_function)
    assert ekf.n_states == 6
    assert ekf.n_measurements == 2
    
    # Test invalid parameters
    with pytest.raises(ValueError):
        ExtendedKalmanFilter(n_states=0, n_measurements=2,
                            state_transition=state_transition,
                            measurement_function=measurement_function)
    with pytest.raises(ValueError):
        ExtendedKalmanFilter(n_states=6, n_measurements=0,
                            state_transition=state_transition,
                            measurement_function=measurement_function)

def test_ekf_filtering():
    """Test ExtendedKalmanFilter on simulated data."""
    # Define test functions
    def state_transition(x, dt):
        # Constant acceleration model
        x_next = x.copy()
        x_next[0] += x[2] * dt + 0.5 * x[4] * dt**2  # position
        x_next[1] += x[3] * dt + 0.5 * x[5] * dt**2  # position
        x_next[2] += x[4] * dt  # velocity
        x_next[3] += x[5] * dt  # velocity
        return x_next
        
    def measurement_function(x):
        # Direct position measurement
        return np.array([x[0], x[1]])
    
    # Generate test data (constant acceleration)
    n_samples = 100
    dt = 0.01
    t = np.linspace(0, dt * n_samples, n_samples)
    acceleration = 1.0  # m/s^2
    velocity = acceleration * t
    position = 0.5 * acceleration * t**2
    
    # Add noise
    noise = np.random.normal(0, 0.1, n_samples)
    measurements = np.column_stack((position + noise, position + noise))  # Shape (100, 2)
    
    # Apply Extended Kalman filter
    ekf = ExtendedKalmanFilter(n_states=6, n_measurements=2,
                              state_transition=state_transition,
                              measurement_function=measurement_function)
    estimates = ekf.estimate(measurements, dt)
    
    # Check results
    assert 'position' in estimates
    assert 'velocity' in estimates
    assert 'acceleration' in estimates
    
    # Position should track true position
    assert np.mean(np.abs(estimates['position'] - position.reshape(-1, 1))) < 0.5
    
    # Velocity should track true velocity
    assert np.mean(np.abs(estimates['velocity'] - velocity.reshape(-1, 1))) < 0.5
    
    # Acceleration should be close to true acceleration
    assert np.mean(np.abs(estimates['acceleration'] - acceleration)) < 0.5

def test_estimator_channel_consistency():
    """Test that estimators maintain consistent channel count."""
    # Create test data
    data1 = np.random.randn(100, 3)  # 3 channels
    data2 = np.random.randn(100, 2)  # 2 channels
    
    # Test KalmanFilter
    kf = KalmanFilter(n_states=6, n_measurements=3)
    kf.estimate(data1, 0.01)
    with pytest.raises(ValueError):
        kf.estimate(data2, 0.01)
        
    # Test ExtendedKalmanFilter
    def state_transition(x, dt):
        return x
    def measurement_function(x):
        return x[:2]
        
    ekf = ExtendedKalmanFilter(n_states=6, n_measurements=2,
                              state_transition=state_transition,
                              measurement_function=measurement_function)
    ekf.estimate(data1, 0.01)
    with pytest.raises(ValueError):
        ekf.estimate(data2, 0.01) 