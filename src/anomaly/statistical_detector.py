import numpy as np
from typing import Dict, Optional
from ..core.interfaces import Detector

class StatisticalDetector(Detector):
    """Detector that identifies anomalies based on statistical measures."""
    
    def __init__(self, 
                 window_size: int = 100,
                 threshold_std: float = 3.0,
                 min_samples: int = 10):
        """Initialize the statistical detector.
        
        Args:
            window_size: Size of sliding window for computing statistics
            threshold_std: Number of standard deviations for anomaly threshold
            min_samples: Minimum number of samples required before detection
        """
        self.window_size = window_size
        self.threshold_std = threshold_std
        self.min_samples = min_samples
        
        # State variables
        self.n_channels = None
        self.buffer = None
        self.buffer_index = 0
        self.buffer_filled = False
        
    def _initialize(self, n_channels: int):
        """Initialize detector state."""
        self.n_channels = n_channels
        self.buffer = np.zeros((self.window_size, n_channels))
        self.buffer_index = 0
        self.buffer_filled = False
        
    def _update_buffer(self, data: np.ndarray):
        """Update circular buffer with new data.
        
        Args:
            data (np.ndarray): New data of shape (n_samples, n_channels)
        """
        n_samples = data.shape[0]
        
        for i in range(n_samples):
            self.buffer[self.buffer_index] = data[i]
            self.buffer_index = (self.buffer_index + 1) % self.window_size
            
            if self.buffer_index == 0:
                self.buffer_filled = True
                
    def _compute_statistics(self) -> tuple:
        """Compute statistics from buffer data.
        
        Returns:
            tuple: (mean, std) of buffer data
        """
        if not self.buffer_filled:
            return None, None
            
        mean = np.mean(self.buffer, axis=0)
        std = np.std(self.buffer, axis=0)
        
        return mean, std
        
    def detect(self, data: np.ndarray, dt: float) -> Dict[str, np.ndarray]:
        """Detect anomalies in input data based on statistical measures.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            dt (float): Time step in seconds (not used, kept for interface compatibility)
            
        Returns:
            Dict[str, np.ndarray]: Dictionary containing:
                - 'anomalies': Boolean array indicating anomalies (True) vs normal (False)
                - 'scores': Anomaly scores (higher values indicate more anomalous)
        """
        if len(data.shape) != 2:
            raise ValueError("Input data must be 2D array (n_samples, n_channels)")
            
        n_samples, n_channels = data.shape
        
        # Initialize if first time
        if self.n_channels is None:
            self._initialize(n_channels)
        elif self.n_channels != n_channels:
            raise ValueError(f"Number of channels changed from {self.n_channels} to {n_channels}")
            
        # Initialize output arrays
        anomalies = np.zeros((n_samples, n_channels), dtype=bool)
        scores = np.zeros((n_samples, n_channels))
        
        # Process each sample
        for i in range(n_samples):
            # Update buffer with new sample
            self._update_buffer(data[i:i+1])
            
            # Compute statistics if buffer is filled
            mean, std = self._compute_statistics()
            
            if mean is not None and std is not None:
                # Compute z-scores
                z_scores = np.abs((data[i] - mean) / (std + 1e-10))
                
                # Compute anomaly scores (normalized z-scores)
                scores[i] = z_scores / self.threshold_std
                
                # Mark as anomaly if z-score exceeds threshold
                anomalies[i] = z_scores > self.threshold_std
                
        return {
            'anomalies': anomalies,
            'scores': scores
        } 