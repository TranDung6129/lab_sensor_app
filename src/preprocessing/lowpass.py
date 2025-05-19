import numpy as np
from typing import Optional, Tuple
from scipy import signal
from ..core.interfaces import Preprocessor

class LowPassFilter(Preprocessor):
    """Low-pass filter using Butterworth design."""
    
    def __init__(self, cutoff_freq: float, fs: float = 200.0, order: int = 4):
        """Initialize the low-pass filter.
        
        Args:
            cutoff_freq (float): Cutoff frequency in Hz
            fs (float): Sampling frequency in Hz
            order (int): Filter order
        """
        if cutoff_freq <= 0 or cutoff_freq >= fs/2:
            raise ValueError("Cutoff frequency must be within Nyquist range")
            
        self.cutoff_freq = cutoff_freq
        self.fs = fs
        self.order = order
        
        # Design filter
        nyq = fs / 2
        cutoff = cutoff_freq / nyq
        self.b, self.a = signal.butter(order, cutoff, btype='low')
        
        # State variables
        self.n_channels = None
        self.zi = None
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.n_channels = n_channels
        self.zi = np.zeros((max(len(self.a), len(self.b)) - 1, n_channels))
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply low-pass filter to input data.
        
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
            
        # Process each channel
        filtered = np.zeros_like(data)
        for ch in range(n_channels):
            filtered[:, ch], self.zi[:, ch] = signal.filtfilt(
                self.b, self.a, data[:, ch], zi=self.zi[:, ch]
            )
            
        return filtered 