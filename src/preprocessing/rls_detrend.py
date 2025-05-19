import numpy as np
from typing import Optional
from ..core.interfaces import Preprocessor

class RLSDetrend(Preprocessor):
    """Recursive Least Squares (RLS) detrending filter.
    
    This class implements an RLS-based detrending algorithm that can adaptively
    remove linear and higher-order trends from sensor data in real-time.
    """
    
    def __init__(self, q: float = 0.99, dt: float = 0.005, order: int = 1):
        """Initialize the RLS detrending filter.
        
        Args:
            q (float): Forgetting factor (0 < q < 1). Higher values give more weight to recent data.
            dt (float): Time step between samples in seconds.
            order (int): Polynomial order for trend removal (1=linear, 2=quadratic, etc.)
        """
        if not 0 < q < 1:
            raise ValueError("Forgetting factor q must be between 0 and 1")
        if order < 1:
            raise ValueError("Order must be at least 1")
            
        self.q = q
        self.dt = dt
        self.order = order
        self.n_channels = None
        self.P = None  # Covariance matrix
        self.theta = None  # Parameter vector
        self.t = 0  # Time counter
        
    def _initialize(self, n_channels: int):
        """Initialize filter parameters for a new data stream."""
        self.n_channels = n_channels
        self.P = np.eye(self.order + 1) * 1000  # Large initial covariance
        self.theta = np.zeros((self.order + 1, n_channels))
        self.t = 0
        
    def _get_basis(self) -> np.ndarray:
        """Generate polynomial basis functions for current time step."""
        t = self.t * self.dt
        return np.array([t**i for i in range(self.order + 1)])
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Remove trend from input data using RLS algorithm.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Detrended data with same shape as input
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.n_channels is None:
            self._initialize(n_channels)
        elif self.n_channels != n_channels:
            raise ValueError(f"Number of channels changed from {self.n_channels} to {n_channels}")
            
        # Process each sample
        detrended = np.zeros_like(data)
        for i in range(n_samples):
            # Get basis functions for current time
            phi = self._get_basis()
            
            # Update for each channel
            for ch in range(n_channels):
                # Prediction
                y_pred = np.dot(phi, self.theta[:, ch])
                
                # Innovation
                innovation = data[i, ch] - y_pred
                
                # Kalman gain
                k = np.dot(self.P, phi) / (self.q + np.dot(phi, np.dot(self.P, phi)))
                
                # Update parameters
                self.theta[:, ch] += k * innovation
                
                # Update covariance
                self.P = (self.P - np.outer(k, np.dot(phi, self.P))) / self.q
                
                # Store detrended value
                detrended[i, ch] = innovation
                
            self.t += 1
            
        return detrended
