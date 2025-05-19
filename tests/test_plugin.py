import pytest
import os
import tempfile
import importlib
from lab_sensor_app.plugin.manager import PluginLoader

class TestPlugin:
    """Test plugin class."""
    
    def __init__(self):
        self.name = "test_plugin"
        
    def register(self):
        """Register plugin."""
        pass

@pytest.fixture
def temp_plugin_dir():
    """Create a temporary plugin directory for testing."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create plugin file
    plugin_file = os.path.join(temp_dir, "test_plugin.py")
    with open(plugin_file, 'w') as f:
        f.write("""
class TestPlugin:
    def __init__(self):
        self.name = "test_plugin"
        
    def register(self):
        pass
""")
        
    # Create __init__.py
    init_file = os.path.join(temp_dir, "__init__.py")
    with open(init_file, 'w') as f:
        f.write("# Plugin package\n")
        
    yield temp_dir
    
    # Cleanup
    os.remove(plugin_file)
    os.remove(init_file)
    os.rmdir(temp_dir)

def test_register_unregister():
    """Test registering and unregistering plugins."""
    # Create plugin manager
    manager = PluginLoader()
    
    # Create test plugin
    plugin = TestPlugin()
    
    # Register plugin
    manager.register(plugin)
    
    # Check plugin is registered
    assert "test_plugin" in manager.plugins
    assert manager.plugins["test_plugin"] == plugin
    
    # Unregister plugin
    manager.unregister("test_plugin")
    
    # Check plugin is unregistered
    assert "test_plugin" not in manager.plugins
    
def test_register_duplicate():
    """Test registering duplicate plugins."""
    # Create plugin manager
    manager = PluginLoader()
    
    # Create test plugin
    plugin = TestPlugin()
    
    # Register plugin
    manager.register(plugin)
    
    # Try to register again
    with pytest.raises(ValueError):
        manager.register(plugin)
        
def test_unregister_nonexistent():
    """Test unregistering nonexistent plugin."""
    # Create plugin manager
    manager = PluginLoader()
    
    # Try to unregister nonexistent plugin
    with pytest.raises(ValueError):
        manager.unregister("nonexistent")
        
def test_get_plugin():
    """Test getting registered plugin."""
    # Create plugin manager
    manager = PluginLoader()
    
    # Create test plugin
    plugin = TestPlugin()
    
    # Register plugin
    manager.register(plugin)
    
    # Get plugin
    loaded_plugin = manager.get_plugin("test_plugin")
    
    # Check plugin
    assert loaded_plugin == plugin
    
    # Get nonexistent plugin
    loaded_plugin = manager.get_plugin("nonexistent")
    
    # Check result
    assert loaded_plugin is None
    
def test_list_plugins():
    """Test listing registered plugins."""
    # Create plugin manager
    manager = PluginLoader()
    
    # Create test plugins
    plugin1 = TestPlugin()
    plugin2 = TestPlugin()
    plugin2.name = "test_plugin2"
    
    # Register plugins
    manager.register(plugin1)
    manager.register(plugin2)
    
    # List plugins
    plugins = manager.list_plugins()
    
    # Check plugins
    assert len(plugins) == 2
    assert "test_plugin" in plugins
    assert "test_plugin2" in plugins
    
def test_load_plugins(temp_plugin_dir):
    """Test loading plugins from directory."""
    # Create plugin manager
    manager = PluginLoader(temp_plugin_dir)
    
    # Load plugins
    manager.load_plugins()
    
    # Check plugins
    assert "test_plugin" in manager.plugins
    
def test_reload_plugins(temp_plugin_dir):
    """Test reloading plugins."""
    # Create plugin manager
    manager = PluginLoader(temp_plugin_dir)
    
    # Load plugins
    manager.load_plugins()
    
    # Check initial plugins
    assert "test_plugin" in manager.plugins
    
    # Reload plugins
    manager.reload_plugins()
    
    # Check plugins after reload
    assert "test_plugin" in manager.plugins 