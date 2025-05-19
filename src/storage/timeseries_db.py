import h5py
import numpy as np
from typing import Optional
from ..core.interfaces import Storage
import os

class TimeSeriesDB(Storage):
    """HDF5-based storage for time series data."""
    
    def __init__(self, db_path: str = "data/timeseries.h5"):
        """Initialize the time series database.
        
        Args:
            db_path: Path to HDF5 database file
        """
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
    def _init_db(self):
        """Initialize HDF5 database file."""
        with h5py.File(self.db_path, 'a') as f:
            # Create metadata group if it doesn't exist
            if 'metadata' not in f:
                f.create_group('metadata')
                
    def _get_dataset_path(self, key: str) -> str:
        """Get full dataset path from key.
        
        Args:
            key: Dataset key
            
        Returns:
            str: Full dataset path
        """
        return f"data/{key}"
        
    def save(self, key: str, data: np.ndarray) -> None:
        """Save time series data to database.
        
        Args:
            key: Key to store data under
            data: Data array to store
        """
        if not isinstance(data, np.ndarray):
            raise TypeError("Data must be numpy array")
            
        dataset_path = self._get_dataset_path(key)
        
        with h5py.File(self.db_path, 'a') as f:
            # Delete existing dataset if it exists
            if dataset_path in f:
                del f[dataset_path]
                
            # Create new dataset
            f.create_dataset(dataset_path, data=data, compression='gzip')
            
            # Store metadata
            metadata = {
                'shape': data.shape,
                'dtype': str(data.dtype),
                'timestamp': np.datetime64('now').astype(str)
            }
            
            # Update metadata
            if key in f['metadata']:
                del f['metadata'][key]
            f['metadata'].create_dataset(key, data=str(metadata))
            
    def load(self, key: str) -> Optional[np.ndarray]:
        """Load time series data from database.
        
        Args:
            key: Key to load data from
            
        Returns:
            Optional[np.ndarray]: Loaded data array or None if not found
        """
        dataset_path = self._get_dataset_path(key)
        
        try:
            with h5py.File(self.db_path, 'r') as f:
                if dataset_path not in f:
                    return None
                    
                # Load data
                data = f[dataset_path][:]
                
                return data
                
        except Exception as e:
            print(f"Error loading data for key {key}: {str(e)}")
            return None
            
    def list_keys(self) -> list:
        """List all available dataset keys.
        
        Returns:
            list: List of dataset keys
        """
        keys = []
        
        try:
            with h5py.File(self.db_path, 'r') as f:
                if 'data' in f:
                    keys = list(f['data'].keys())
        except Exception as e:
            print(f"Error listing keys: {str(e)}")
            
        return keys
        
    def get_metadata(self, key: str) -> Optional[dict]:
        """Get metadata for a dataset.
        
        Args:
            key: Dataset key
            
        Returns:
            Optional[dict]: Dataset metadata or None if not found
        """
        try:
            with h5py.File(self.db_path, 'r') as f:
                if key not in f['metadata']:
                    return None
                    
                # Load metadata
                metadata_str = f['metadata'][key][()]
                return eval(metadata_str)
                
        except Exception as e:
            print(f"Error loading metadata for key {key}: {str(e)}")
            return None
