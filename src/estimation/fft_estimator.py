import numpy as np
from typing import Dict, Tuple
from ..core.interfaces import Estimator

class FFTEstimator(Estimator):
    """FFT-based frequency estimator."""
    
    def __init__(self, fs: float = 200.0, window: str = 'hann'):
        """Initialize the FFT estimator.
        
        Args:
            fs (float): Sampling frequency in Hz
            window (str): Window function to apply ('hann', 'hamming', 'blackman', etc.)
        """
        self.fs = fs
        self.window = window
        
        # State variables
        self.n_channels = None
        self.window_func = None
        
    def _initialize(self, n_channels: int):
        """Initialize estimator state."""
        self.n_channels = n_channels
        
    def _apply_window(self, data: np.ndarray) -> np.ndarray:
        """Apply window function to input data.
        
        Args:
            data (np.ndarray): Input data array
            
        Returns:
            np.ndarray: Windowed data
        """
        if self.window_func is None:
            self.window_func = getattr(np, self.window)(data.shape[0])
        return data * self.window_func[:, np.newaxis]
        
    def _compute_fft(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute FFT of input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Frequencies and amplitudes
        """
        # Apply window
        windowed_data = self._apply_window(data)
        
        # Compute FFT
        n_samples = data.shape[0]
        freqs = np.fft.rfftfreq(n_samples, 1/self.fs)
        fft = np.fft.rfft(windowed_data, axis=0)
        
        # Compute amplitudes
        amps = np.abs(fft) * 2 / n_samples
        
        return freqs, amps
        
    def estimate(self, data: np.ndarray, dt: float) -> Dict[str, np.ndarray]:
        """Estimate frequencies and amplitudes from input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            dt (float): Time step in seconds (not used, kept for interface compatibility)
            
        Returns:
            Dict[str, np.ndarray]: Dictionary containing:
                - 'frequencies': Array of frequencies in Hz
                - 'amplitudes': Array of amplitudes for each frequency
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.n_channels is None:
            self._initialize(n_channels)
        elif self.n_channels != n_channels:
            raise ValueError(f"Number of channels changed from {self.n_channels} to {n_channels}")
            
        # Compute FFT
        freqs, amps = self._compute_fft(data)
        
        return {
            'frequencies': freqs,
            'amplitudes': amps
        }
