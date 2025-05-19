from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple, List, Dict

class DataSource(ABC):
    """
    Interface for data acquisition modules.
    """
    @abstractmethod
    def read_frame(self) -> np.ndarray:
        """Read a frame of sensor data.
        
        Returns:
            np.ndarray: Array of shape (n_samples, n_channels) containing sensor readings
        """
        pass

class Preprocessor(ABC):
    """
    Interface for preprocessing modules (detrend, filter).
    """
    @abstractmethod
    def preprocess(self, data: np.ndarray) -> np.ndarray:
        """Preprocess the input data.
        
        Args:
            data (np.ndarray): Input data array
            
        Returns:
            np.ndarray: Preprocessed data with same shape as input
        """
        pass

class Integrator(ABC):
    """
    Interface for integration modules (e.g. acceleration→velocity/displacement).
    """
    @abstractmethod
    def integrate(self, data: np.ndarray) -> np.ndarray:
        """Integrate the input data.
        
        Args:
            data (np.ndarray): Input data array
            
        Returns:
            np.ndarray: Integrated data with same shape as input
        """
        pass

class Estimator(ABC):
    """
    Interface for estimation modules (frequency, amplitude, phase).
    """
    @abstractmethod
    def estimate(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate frequencies and amplitudes from the input data.
        
        Args:
            data (np.ndarray): Input data array
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Tuple of (frequencies, amplitudes)
        """
        pass

class Detector(ABC):
    """
    Interface for anomaly detection modules.
    """
    @abstractmethod
    def detect(self, data: np.ndarray, dt: float) -> Dict[str, np.ndarray]:
        """Detect anomalies in input data.
        
        Args:
            data (np.ndarray): Input data array of shape (n_samples, n_channels)
            dt (float): Time step in seconds
            
        Returns:
            Dict[str, np.ndarray]: Dictionary containing:
                - 'anomalies': Boolean array indicating anomalies (True) vs normal (False)
                - 'scores': Anomaly scores (higher values indicate more anomalous)
        """
        pass

class Storage(ABC):
    """
    Interface for storage modules (DB, file).
    """
    @abstractmethod
    def save(self, key: str, data: np.ndarray) -> None:
        """Save data to storage.
        
        Args:
            key (str): Key to store data under
            data (np.ndarray): Data to store
        """
        pass

    @abstractmethod
    def load(self, key: str) -> np.ndarray:
        """Load data from storage.
        
        Args:
            key (str): Key to load data from
            
        Returns:
            np.ndarray: Loaded data
        """
        pass

class PluginManager(ABC):
    """
    Interface for plugin management (load, unload).
    """
    @abstractmethod
    def register(self, plugin: object) -> None:
        """Register a new plugin.
        
        Args:
            plugin (object): Plugin instance to register
        """
        pass

    @abstractmethod
    def unregister(self, name: str) -> None:
        """Unregister a plugin.
        
        Args:
            name (str): Name of plugin to unregister
        """
        pass

class Visualizer(ABC):
    """
    Interface for visualization modules.
    """
    @abstractmethod
    def plot_time_series(self, data: np.ndarray, title: str) -> None:
        """Plot time series data.
        
        Args:
            data (np.ndarray): Time series data to plot
            title (str): Plot title
        """
        pass

    @abstractmethod
    def plot_spectrum(self, data: np.ndarray, title: str) -> None:
        """Plot frequency spectrum.
        
        Args:
            data (np.ndarray): Data to compute and plot spectrum
            title (str): Plot title
        """
        pass
