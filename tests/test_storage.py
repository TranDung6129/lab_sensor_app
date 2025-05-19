import pytest
import numpy as np
import os
import tempfile
from lab_sensor_app.storage.timeseries_db import TimeSeriesDB

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.h5")
    
    # Create database
    db = TimeSeriesDB(db_path)
    
    yield db
    
    # Cleanup
    os.remove(db_path)
    os.rmdir(temp_dir)

def test_save_load(temp_db):
    """Test saving and loading data."""
    # Create test data
    data = np.random.randn(100, 3)
    
    # Save data
    temp_db.save("test_data", data)
    
    # Load data
    loaded_data = temp_db.load("test_data")
    
    # Check data
    assert loaded_data is not None
    assert np.array_equal(data, loaded_data)
    
def test_save_overwrite(temp_db):
    """Test overwriting existing data."""
    # Create test data
    data1 = np.random.randn(100, 3)
    data2 = np.random.randn(200, 3)
    
    # Save first dataset
    temp_db.save("test_data", data1)
    
    # Save second dataset
    temp_db.save("test_data", data2)
    
    # Load data
    loaded_data = temp_db.load("test_data")
    
    # Check data
    assert loaded_data is not None
    assert np.array_equal(data2, loaded_data)
    
def test_load_nonexistent(temp_db):
    """Test loading nonexistent data."""
    # Try to load nonexistent data
    loaded_data = temp_db.load("nonexistent")
    
    # Check result
    assert loaded_data is None
    
def test_list_keys(temp_db):
    """Test listing dataset keys."""
    # Create test data
    data1 = np.random.randn(100, 3)
    data2 = np.random.randn(200, 3)
    
    # Save datasets
    temp_db.save("data1", data1)
    temp_db.save("data2", data2)
    
    # List keys
    keys = temp_db.list_keys()
    
    # Check keys
    assert len(keys) == 2
    assert "data1" in keys
    assert "data2" in keys
    
def test_metadata(temp_db):
    """Test metadata storage and retrieval."""
    # Create test data
    data = np.random.randn(100, 3)
    
    # Save data
    temp_db.save("test_data", data)
    
    # Get metadata
    metadata = temp_db.get_metadata("test_data")
    
    # Check metadata
    assert metadata is not None
    assert metadata['shape'] == data.shape
    assert metadata['dtype'] == str(data.dtype)
    assert 'timestamp' in metadata 