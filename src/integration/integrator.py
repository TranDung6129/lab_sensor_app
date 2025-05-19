import numpy as np
from typing import List, Optional
from ..core.interfaces import Integrator, Preprocessor

class RealTimeIntegrator(Integrator):
    """Real-time double integrator for converting acceleration to displacement.
    
    This class implements a real-time double integration algorithm with drift compensation
    and optional preprocessing steps. It uses trapezoidal integration with drift correction.
    """
    
    def __init__(self, preprocessors: Optional[List[Preprocessor]] = None, 
                 window: int = 100, dt: float = 0.005):
        """Initialize the integrator.
        
        Args:
            preprocessors (Optional[List[Preprocessor]]): List of preprocessors to apply
            window (int): Window size for drift correction
            dt (float): Time step between samples in seconds
        """
        self.preprocessors = preprocessors or []
        self.window = window
        self.dt = dt
        
        # State variables
        self.n_channels = None
        self.velocity = None
        self.displacement = None
        self.prev_accel = None
        self.buffer = None
        self.buffer_idx = 0
        
    def _initialize(self, n_channels: int):
        """Initialize integrator state."""
        self.n_channels = n_channels
        self.velocity = np.zeros(n_channels)
        self.displacement = np.zeros(n_channels)
        self.prev_accel = np.zeros(n_channels)
        self.buffer = np.zeros((self.window, n_channels))
        self.buffer_idx = 0
        
    def _apply_preprocessors(self, data: np.ndarray) -> np.ndarray:
        """Apply all preprocessors in sequence."""
        processed = data.copy()
        for preprocessor in self.preprocessors:
            processed = preprocessor.preprocess(processed)
        return processed
        
    def _update_buffer(self, data: np.ndarray):
        """Update the circular buffer with new data."""
        self.buffer[self.buffer_idx] = data
        self.buffer_idx = (self.buffer_idx + 1) % self.window
        
    def _correct_drift(self, integrated: np.ndarray) -> np.ndarray:
        """Correct drift in integrated signal using buffer statistics."""
        if self.buffer_idx == 0:  # Buffer is full
            drift = np.mean(self.buffer, axis=0)
            return integrated - drift * np.arange(len(integrated))[:, np.newaxis]
        return integrated
        
    def integrate(self, data: np.ndarray) -> np.ndarray:
        """Perform double integration on acceleration data.
        
        Args:
            data (np.ndarray): Acceleration data of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Displacement data with same shape as input
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.n_channels is None:
            self._initialize(n_channels)
        elif self.n_channels != n_channels:
            raise ValueError(f"Number of channels changed from {self.n_channels} to {n_channels}")
            
        # Apply preprocessors
        processed = self._apply_preprocessors(data)
        
        # Initialize output arrays
        velocity = np.zeros_like(processed)
        displacement = np.zeros_like(processed)
        
        # First integration (acceleration -> velocity)
        for i in range(n_samples):
            # Trapezoidal integration
            if i == 0:
                velocity[i] = self.velocity
            else:
                velocity[i] = velocity[i-1] + 0.5 * self.dt * (processed[i] + processed[i-1])
            
            # Update buffer for drift correction
            self._update_buffer(velocity[i])
            
            # Correct drift in velocity
            velocity[i] = self._correct_drift(velocity[i:i+1])[0]
            
            # Second integration (velocity -> displacement)
            if i == 0:
                displacement[i] = self.displacement
            else:
                displacement[i] = displacement[i-1] + 0.5 * self.dt * (velocity[i] + velocity[i-1])
            
            # Update state
            self.velocity = velocity[i]
            self.displacement = displacement[i]
            self.prev_accel = processed[i]
            
        return displacement
