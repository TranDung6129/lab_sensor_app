import numpy as np
from typing import Optional, Tuple
from scipy import signal
from ..core.interfaces import Preprocessor

class BandPassFilter(Preprocessor):
    """Band-pass filter using Butterworth design."""
    
    def __init__(self, low_freq: float, high_freq: float, 
                 fs: float = 200.0, order: int = 4):
        """Initialize the band-pass filter.
        
        Args:
            low_freq (float): Lower cutoff frequency in Hz
            high_freq (float): Upper cutoff frequency in Hz
            fs (float): Sampling frequency in Hz
            order (int): Filter order
        """
        if low_freq >= high_freq:
            raise ValueError("low_freq must be less than high_freq")
        if low_freq <= 0 or high_freq >= fs/2:
            raise ValueError("Frequencies must be within Nyquist range")
            
        self.low_freq = low_freq
        self.high_freq = high_freq
        self.fs = fs
        self.order = order
        
        # Design filter
        nyq = fs / 2
        low = low_freq / nyq
        high = high_freq / nyq
        self.b, self.a = signal.butter(order, [low, high], btype='band')
        
        # State variables
        self.n_channels = None
        self.zi = None
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.n_channels = n_channels
        self.zi = np.zeros((max(len(self.a), len(self.b)) - 1, n_channels))
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply band-pass filter to input data.
        
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

class NotchFilter(Preprocessor):
    """Notch (band-stop) filter for removing specific frequencies."""
    
    def __init__(self, freq: float, quality_factor: float = 30.0, 
                 fs: float = 200.0):
        """Initialize the notch filter.
        
        Args:
            freq (float): Frequency to remove in Hz
            quality_factor (float): Quality factor (higher = narrower notch)
            fs (float): Sampling frequency in Hz
        """
        if freq <= 0 or freq >= fs/2:
            raise ValueError("Frequency must be within Nyquist range")
        if quality_factor <= 0:
            raise ValueError("Quality factor must be positive")
            
        self.freq = freq
        self.quality_factor = quality_factor
        self.fs = fs
        
        # Design filter
        self.b, self.a = signal.iirnotch(freq, quality_factor, fs)
        
        # State variables
        self.n_channels = None
        self.zi = None
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.n_channels = n_channels
        self.zi = np.zeros((max(len(self.a), len(self.b)) - 1, n_channels))
        
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Apply notch filter to input data.
        
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