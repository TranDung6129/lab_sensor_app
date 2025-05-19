import numpy as np
from typing import Dict, Optional, Tuple, Callable
from ..core.interfaces import Estimator

class ExtendedKalmanFilter(Estimator):
    """Extended Kalman filter for nonlinear state estimation."""
    
    def __init__(self, n_states: int, n_measurements: int,
                 state_transition: Callable,
                 measurement_function: Callable,
                 process_noise: float = 0.1,
                 measurement_noise: float = 1.0):
        """Initialize the extended Kalman filter.
        
        Args:
            n_states (int): Number of states to estimate
            n_measurements (int): Number of measurements
            state_transition (Callable): Function that computes state transition
                f(x, dt) -> x_next
            measurement_function (Callable): Function that computes measurement
                h(x) -> z
            process_noise (float): Process noise covariance
            measurement_noise (float): Measurement noise covariance
        """
        self.n_states = n_states
        self.n_measurements = n_measurements
        self.f = state_transition
        self.h = measurement_function
        
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
            
    def _compute_jacobian(self, x: np.ndarray, dt: float) -> np.ndarray:
        """Compute Jacobian of state transition function.
        
        Args:
            x (np.ndarray): State vector
            dt (float): Time step
            
        Returns:
            np.ndarray: Jacobian matrix
        """
        # Numerical Jacobian
        eps = 1e-6
        F = np.zeros((self.n_states, self.n_states))
        
        for i in range(self.n_states):
            x_plus = x.copy()
            x_plus[i] += eps
            x_minus = x.copy()
            x_minus[i] -= eps
            
            f_plus = self.f(x_plus, dt)
            f_minus = self.f(x_minus, dt)
            
            F[:, i] = (f_plus - f_minus) / (2 * eps)
            
        return F
        
    def _compute_measurement_jacobian(self, x: np.ndarray) -> np.ndarray:
        """Compute Jacobian of measurement function.
        
        Args:
            x (np.ndarray): State vector
            
        Returns:
            np.ndarray: Jacobian matrix
        """
        # Numerical Jacobian
        eps = 1e-6
        H = np.zeros((self.n_measurements, self.n_states))
        
        for i in range(self.n_states):
            x_plus = x.copy()
            x_plus[i] += eps
            x_minus = x.copy()
            x_minus[i] -= eps
            
            h_plus = self.h(x_plus)
            h_minus = self.h(x_minus)
            
            H[:, i] = (h_plus - h_minus) / (2 * eps)
            
        return H
        
    def _predict(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Predict next state.
        
        Args:
            dt (float): Time step in seconds
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Predicted state and covariance
        """
        x_pred = np.zeros_like(self.x)
        P_pred = np.zeros_like(self.P)
        
        for ch in range(self.n_channels):
            # Predict state
            x_pred[:, ch] = self.f(self.x[:, ch], dt)
            
            # Compute Jacobian
            F = self._compute_jacobian(self.x[:, ch], dt)
            
            # Predict covariance
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
            # Compute measurement Jacobian
            H = self._compute_measurement_jacobian(x_pred[:, ch])
            
            # Innovation
            y = z[:, ch] - self.h(x_pred[:, ch])
            
            # Innovation covariance
            S = H @ P_pred[:, :, ch] @ H.T + self.R
            
            # Kalman gain
            K = P_pred[:, :, ch] @ H.T @ np.linalg.inv(S)
            
            # Update state
            x_update[:, ch] = x_pred[:, ch] + K @ y
            
            # Update covariance
            P_update[:, :, ch] = (np.eye(self.n_states) - K @ H) @ P_pred[:, :, ch]
            
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