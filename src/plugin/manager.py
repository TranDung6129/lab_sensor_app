import os
import importlib
import inspect
from typing import Dict, Optional, Type
from ..core.interfaces import PluginManager

class PluginLoader(PluginManager):
    """Plugin manager that loads and manages plugins from a directory."""
    
    def __init__(self, plugin_dir: str = "plugins"):
        """Initialize the plugin manager.
        
        Args:
            plugin_dir: Directory containing plugin modules
        """
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, object] = {}
        
        # Create plugin directory if it doesn't exist
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(plugin_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Plugin package\n")
                
    def _is_valid_plugin(self, obj: object) -> bool:
        """Check if an object is a valid plugin.
        
        Args:
            obj: Object to check
            
        Returns:
            bool: True if object is a valid plugin
        """
        # Check if object has register method
        if not hasattr(obj, 'register'):
            return False
            
        # Check if register is callable
        if not callable(getattr(obj, 'register')):
            return False
            
        return True
        
    def _get_plugin_name(self, obj: object) -> str:
        """Get plugin name from object.
        
        Args:
            obj: Plugin object
            
        Returns:
            str: Plugin name
        """
        # Try to get name from object
        if hasattr(obj, 'name'):
            return obj.name
            
        # Fall back to class/module name
        if inspect.isclass(obj):
            return obj.__name__
        else:
            return obj.__class__.__name__
            
    def register(self, plugin: object) -> None:
        """Register a new plugin.
        
        Args:
            plugin: Plugin instance to register
        """
        if not self._is_valid_plugin(plugin):
            raise ValueError("Invalid plugin: must have register() method")
            
        name = self._get_plugin_name(plugin)
        
        if name in self.plugins:
            raise ValueError(f"Plugin {name} already registered")
            
        self.plugins[name] = plugin
        
    def unregister(self, name: str) -> None:
        """Unregister a plugin.
        
        Args:
            name: Name of plugin to unregister
        """
        if name not in self.plugins:
            raise ValueError(f"Plugin {name} not found")
            
        del self.plugins[name]
        
    def get_plugin(self, name: str) -> Optional[object]:
        """Get a registered plugin.
        
        Args:
            name: Name of plugin to get
            
        Returns:
            Optional[object]: Plugin instance or None if not found
        """
        return self.plugins.get(name)
        
    def list_plugins(self) -> list:
        """List all registered plugins.
        
        Returns:
            list: List of plugin names
        """
        return list(self.plugins.keys())
        
    def load_plugins(self) -> None:
        """Load all plugins from plugin directory."""
        # Get list of Python files in plugin directory
        plugin_files = [f for f in os.listdir(self.plugin_dir) 
                       if f.endswith('.py') and not f.startswith('__')]
                       
        # Import each plugin module
        for plugin_file in plugin_files:
            try:
                # Get module name
                module_name = os.path.splitext(plugin_file)[0]
                
                # Import module
                module = importlib.import_module(f"{self.plugin_dir}.{module_name}")
                
                # Find plugin classes
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and self._is_valid_plugin(obj):
                        # Create instance and register
                        plugin = obj()
                        self.register(plugin)
                        
            except Exception as e:
                print(f"Error loading plugin {plugin_file}: {str(e)}")
                
    def reload_plugins(self) -> None:
        """Reload all plugins from plugin directory."""
        # Clear existing plugins
        self.plugins.clear()
        
        # Load plugins
        self.load_plugins()
