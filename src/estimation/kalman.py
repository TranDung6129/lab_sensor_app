import numpy as np
from typing import Dict, Optional, Tuple
from ..core.interfaces import Estimator

class KalmanFilter(Estimator):
    """Kalman filter for state estimation."""
    
    def __init__(self, n_states: int, n_measurements: int,
                 process_noise: float = 0.1,
                 measurement_noise: float = 1.0):
        """Initialize the Kalman filter.
        
        Args:
            n_states (int): Number of states to estimate
            n_measurements (int): Number of measurements
            process_noise (float): Process noise covariance
            measurement_noise (float): Measurement noise covariance
        """
        self.n_states = n_states
        self.n_measurements = n_measurements
        
        # State transition matrix (constant velocity model)
        self.F = np.eye(n_states)
        for i in range(n_states // 2):
            self.F[i, i + n_states // 2] = 1.0
            
        # Measurement matrix
        self.H = np.zeros((n_measurements, n_states))
        for i in range(n_measurements):
            self.H[i, i] = 1.0
            
        # Process noise covariance
        self.Q = np.eye(n_states) * process_noise
        
        # Measurement noise covariance
        self.R = np.eye(n_measurements) * measurement_noise
        
        # State variables
        self.n_channels = None
        self.x = None  # State estimate
        self.P = None  # Error covariance
        
    def _initialize(self, n_channels: int):
        """Initialize filter state."""
        self.n_channels = n_channels
        self.x = np.zeros((self.n_states, n_channels))
        self.P = np.zeros((self.n_states, self.n_states, n_channels))
        for ch in range(n_channels):
            self.P[:, :, ch] = np.eye(self.n_states)
            
    def _predict(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Predict next state.
        
        Args:
            dt (float): Time step in seconds
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Predicted state and covariance
        """
        # Update state transition matrix for current dt
        F = self.F.copy()
        for i in range(self.n_states // 2):
            F[i, i + self.n_states // 2] = dt
            
        # Predict state
        x_pred = np.zeros_like(self.x)
        P_pred = np.zeros_like(self.P)
        
        for ch in range(self.n_channels):
            x_pred[:, ch] = F @ self.x[:, ch]
            P_pred[:, :, ch] = F @ self.P[:, :, ch] @ F.T + self.Q
            
        return x_pred, P_pred
        
    def _update(self, z: np.ndarray, x_pred: np.ndarray, 
                P_pred: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Update state estimate with measurement.
        
        Args:
            z (np.ndarray): Measurement vector
            x_pred (np.ndarray): Predicted state
            P_pred (np.ndarray): Predicted covariance
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Updated state and covariance
        """
        x_update = np.zeros_like(x_pred)
        P_update = np.zeros_like(P_pred)
        
        for ch in range(self.n_channels):
            # Innovation
            y = z[:, ch] - self.H @ x_pred[:, ch]
            
            # Innovation covariance
            S = self.H @ P_pred[:, :, ch] @ self.H.T + self.R
            
            # Kalman gain
            K = P_pred[:, :, ch] @ self.H.T @ np.linalg.inv(S)
            
            # Update state
            x_update[:, ch] = x_pred[:, ch] + K @ y
            
            # Update covariance
            P_update[:, :, ch] = (np.eye(self.n_states) - K @ self.H) @ P_pred[:, :, ch]
            
        return x_update, P_update
        
    def estimate(self, data: np.ndarray, dt: float) -> Dict[str, np.ndarray]:
        """Estimate state from input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            dt (float): Time step in seconds
            
        Returns:
            Dict[str, np.ndarray]: Dictionary containing:
                - 'position': Position estimates
                - 'velocity': Velocity estimates
                - 'acceleration': Acceleration estimates
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
        n_states_per_dim = self.n_states // 3  # Position, velocity, acceleration
        position = np.zeros((n_samples, n_channels))
        velocity = np.zeros((n_samples, n_channels))
        acceleration = np.zeros((n_samples, n_channels))
        
        # Process each sample
        for i in range(n_samples):
            # Predict
            x_pred, P_pred = self._predict(dt)
            
            # Update
            self.x, self.P = self._update(data[i:i+1].T, x_pred, P_pred)
            
            # Extract states
            for ch in range(n_channels):
                position[i, ch] = self.x[0, ch]
                velocity[i, ch] = self.x[n_states_per_dim, ch]
                acceleration[i, ch] = self.x[2*n_states_per_dim, ch]
                
        return {
            'position': position,
            'velocity': velocity,
            'acceleration': acceleration
        } 