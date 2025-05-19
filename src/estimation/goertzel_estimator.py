import numpy as np
from typing import Dict, Optional
from ..core.interfaces import Estimator

class GoertzelEstimator(Estimator):
    """Goertzel algorithm for single-tone frequency estimation."""
    
    def __init__(self, target_freq: float, fs: float = 200.0):
        """Initialize the Goertzel estimator.
        
        Args:
            target_freq (float): Target frequency to detect in Hz
            fs (float): Sampling frequency in Hz
        """
        if target_freq <= 0 or target_freq >= fs/2:
            raise ValueError("Target frequency must be within Nyquist range")
            
        self.target_freq = target_freq
        self.fs = fs
        
        # State variables
        self.n_channels = None
        self.coeff = None
        
    def _initialize(self, n_channels: int):
        """Initialize estimator state."""
        self.n_channels = n_channels
        
    def _compute_coefficient(self, n_samples: int) -> float:
        """Compute Goertzel coefficient for given number of samples.
        
        Args:
            n_samples (int): Number of samples
            
        Returns:
            float: Goertzel coefficient
        """
        k = n_samples * self.target_freq / self.fs
        w = 2 * np.pi * k / n_samples
        return 2 * np.cos(w)
        
    def _compute_goertzel(self, data: np.ndarray) -> np.ndarray:
        """Compute Goertzel algorithm on input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Amplitudes for target frequency
        """
        n_samples = data.shape[0]
        
        # Compute coefficient if not already done
        if self.coeff is None:
            self.coeff = self._compute_coefficient(n_samples)
            
        # Initialize arrays
        s0 = np.zeros((n_samples + 1, self.n_channels))
        s1 = np.zeros((n_samples + 1, self.n_channels))
        s2 = np.zeros((n_samples + 1, self.n_channels))
        
        # Run Goertzel algorithm
        for i in range(n_samples):
            s0[i+1] = data[i] + self.coeff * s1[i] - s2[i]
            s2[i+1] = s1[i]
            s1[i+1] = s0[i+1]
            
        # Compute amplitude
        amps = np.sqrt(s1[-1]**2 + s2[-1]**2 - self.coeff * s1[-1] * s2[-1])
        amps = amps * 2 / n_samples
        
        return amps
        
    def estimate(self, data: np.ndarray, dt: float) -> Dict[str, np.ndarray]:
        """Estimate amplitude of target frequency from input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            dt (float): Time step in seconds (not used, kept for interface compatibility)
            
        Returns:
            Dict[str, np.ndarray]: Dictionary containing:
                - 'frequency': Target frequency in Hz
                - 'amplitude': Amplitude of target frequency
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.n_channels is None:
            self._initialize(n_channels)
        elif self.n_channels != n_channels:
            raise ValueError(f"Number of channels changed from {self.n_channels} to {n_channels}")
            
        # Compute Goertzel
        amps = self._compute_goertzel(data)
        
        return {
            'frequency': np.full((1, n_channels), self.target_freq),
            'amplitude': amps.reshape(1, -1)
        }
