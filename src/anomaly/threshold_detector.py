import numpy as np
from typing import Dict, Optional, Union
from ..core.interfaces import Detector

class ThresholdDetector(Detector):
    """Detector that identifies anomalies based on threshold values."""
    
    def __init__(self, 
                 lower_threshold: Optional[Union[float, np.ndarray]] = None,
                 upper_threshold: Optional[Union[float, np.ndarray]] = None,
                 window_size: int = 1):
        """Initialize the threshold detector.
        
        Args:
            lower_threshold: Lower threshold value(s). If None, no lower threshold is applied.
                           Can be a single value or array matching number of channels.
            upper_threshold: Upper threshold value(s). If None, no upper threshold is applied.
                           Can be a single value or array matching number of channels.
            window_size: Number of consecutive samples that must exceed threshold to trigger anomaly
        """
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.window_size = window_size
        
        # State variables
        self.n_channels = None
        self.consecutive_exceedances = None
        
    def _initialize(self, n_channels: int):
        """Initialize detector state."""
        self.n_channels = n_channels
        self.consecutive_exceedances = np.zeros(n_channels)
        
        # Broadcast thresholds to match number of channels
        if self.lower_threshold is not None:
            self.lower_threshold = np.broadcast_to(self.lower_threshold, n_channels)
        if self.upper_threshold is not None:
            self.upper_threshold = np.broadcast_to(self.upper_threshold, n_channels)
            
    def _compute_anomaly_scores(self, data: np.ndarray) -> np.ndarray:
        """Compute anomaly scores based on distance from thresholds.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            
        Returns:
            np.ndarray: Anomaly scores of same shape as input
        """
        scores = np.zeros_like(data)
        
        if self.lower_threshold is not None:
            lower_scores = (self.lower_threshold - data) / np.abs(self.lower_threshold)
            scores = np.maximum(scores, lower_scores)
            
        if self.upper_threshold is not None:
            upper_scores = (data - self.upper_threshold) / np.abs(self.upper_threshold)
            scores = np.maximum(scores, upper_scores)
            
        return scores
        
    def detect(self, data: np.ndarray, dt: float) -> Dict[str, np.ndarray]:
        """Detect anomalies in input data based on thresholds.
        
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
            
        # Compute anomaly scores
        scores = self._compute_anomaly_scores(data)
        
        # Initialize anomalies array
        anomalies = np.zeros((n_samples, n_channels), dtype=bool)
        
        # Check for threshold exceedances
        for i in range(n_samples):
            # Check lower threshold
            if self.lower_threshold is not None:
                lower_exceeded = data[i] < self.lower_threshold
                self.consecutive_exceedances[lower_exceeded] += 1
                self.consecutive_exceedances[~lower_exceeded] = 0
                
            # Check upper threshold
            if self.upper_threshold is not None:
                upper_exceeded = data[i] > self.upper_threshold
                self.consecutive_exceedances[upper_exceeded] += 1
                self.consecutive_exceedances[~upper_exceeded] = 0
                
            # Mark as anomaly if consecutive exceedances reach window size
            anomalies[i] = self.consecutive_exceedances >= self.window_size
            
        return {
            'anomalies': anomalies,
            'scores': scores
        } 