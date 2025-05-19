import numpy as np
from typing import Optional
from ..core.interfaces import Preprocessor

class MovingAverage(Preprocessor):
    """Simple moving average filter for smoothing data."""
    
    def __init__(self, window_size: int = 5):
        """Initialize the moving average filter.
        
        Args:
            window_size (int): Size of the moving window
        """
        if window_size < 1:
            raise ValueError("Window size must be at least 1")
        self.window_size = window_size
        self.buffer = None
        self.buffer_idx = 0
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.buffer = np.zeros((self.window_size, n_channels))
        self.buffer_idx = 0
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply moving average filter to input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Smoothed data with same shape as input
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.buffer is None:
            self._initialize(n_channels)
        elif self.buffer.shape[1] != n_channels:
            raise ValueError(f"Number of channels changed from {self.buffer.shape[1]} to {n_channels}")
            
        # Process data
        smoothed = np.zeros_like(data)
        for i in range(n_samples):
            # Update buffer
            self.buffer[self.buffer_idx] = data[i]
            self.buffer_idx = (self.buffer_idx + 1) % self.window_size
            
            # Compute moving average
            smoothed[i] = np.mean(self.buffer, axis=0)
            
        return smoothed

class ExponentialSmoothing(Preprocessor):
    """Exponential smoothing filter for real-time data smoothing."""
    
    def __init__(self, alpha: float = 0.3):
        """Initialize the exponential smoothing filter.
        
        Args:
            alpha (float): Smoothing factor (0 < alpha < 1)
        """
        if not 0 < alpha < 1:
            raise ValueError("Alpha must be between 0 and 1")
        self.alpha = alpha
        self.prev_output = None
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.prev_output = np.zeros(n_channels)
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply exponential smoothing to input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Smoothed data with same shape as input
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.prev_output is None:
            self._initialize(n_channels)
        elif len(self.prev_output) != n_channels:
            raise ValueError(f"Number of channels changed from {len(self.prev_output)} to {n_channels}")
            
        # Process data
        smoothed = np.zeros_like(data)
        for i in range(n_samples):
            smoothed[i] = self.alpha * data[i] + (1 - self.alpha) * self.prev_output
            self.prev_output = smoothed[i]
            
        return smoothed

class KalmanFilter(Preprocessor):
    """Kalman filter for optimal state estimation and noise reduction."""
    
    def __init__(self, process_noise: float = 0.1, measurement_noise: float = 1.0):
        """Initialize the Kalman filter.
        
        Args:
            process_noise (float): Process noise covariance
            measurement_noise (float): Measurement noise covariance
        """
        self.Q = process_noise  # Process noise
        self.R = measurement_noise  # Measurement noise
        self.P = None  # Error covariance
        self.x = None  # State estimate
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.P = np.ones(n_channels)  # Initial error covariance
        self.x = np.zeros(n_channels)  # Initial state estimate
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply Kalman filter to input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Filtered data with same shape as input
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.x is None:
            self._initialize(n_channels)
        elif len(self.x) != n_channels:
            raise ValueError(f"Number of channels changed from {len(self.x)} to {n_channels}")
            
        # Process data
        filtered = np.zeros_like(data)
        for i in range(n_samples):
            # Prediction
            x_pred = self.x
            P_pred = self.P + self.Q
            
            # Update
            K = P_pred / (P_pred + self.R)  # Kalman gain
            self.x = x_pred + K * (data[i] - x_pred)
            self.P = (1 - K) * P_pred
            
            filtered[i] = self.x
            
        return filtered 