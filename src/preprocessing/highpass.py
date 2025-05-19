import numpy as np
from typing import Optional
from ..core.interfaces import Preprocessor

class HighPassFilter(Preprocessor):
    """Recursive high-pass filter for removing low-frequency components.
    
    This class implements a first-order high-pass filter using the difference equation:
    y[n] = q * (y[n-1] + x[n] - x[n-1])
    where q is the filter coefficient that determines the cutoff frequency.
    """
    
    def __init__(self, q: float = 0.99, dt: float = 0.005):
        """Initialize the high-pass filter.
        
        Args:
            q (float): Filter coefficient (0 < q < 1). Higher values give lower cutoff frequency.
            dt (float): Time step between samples in seconds.
        """
        if not 0 < q < 1:
            raise ValueError("Filter coefficient q must be between 0 and 1")
            
        self.q = q
        self.dt = dt
        self.n_channels = None
        self.prev_input = None
        self.prev_output = None
        
    def _initialize(self, n_channels: int):
        """Initialize filter state for a new data stream."""
        self.n_channels = n_channels
        self.prev_input = np.zeros(n_channels)
        self.prev_output = np.zeros(n_channels)
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply high-pass filter to input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Filtered data with same shape as input
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.n_channels is None:
            self._initialize(n_channels)
        elif self.n_channels != n_channels:
            raise ValueError(f"Number of channels changed from {self.n_channels} to {n_channels}")
            
        # Process data
        filtered = np.zeros_like(data)
        for i in range(n_samples):
            # Apply filter to each channel
            for ch in range(n_channels):
                # First-order high-pass filter
                filtered[i, ch] = self.q * (self.prev_output[ch] + 
                                          data[i, ch] - self.prev_input[ch])
                
                # Update state
                self.prev_input[ch] = data[i, ch]
                self.prev_output[ch] = filtered[i, ch]
                
        return filtered
