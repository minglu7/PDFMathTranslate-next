"""
Plugin loader
Supports loading custom translator plugins from multiple directories
"""
import os
import sys
import logging
import importlib.util
from pathlib import Path
from typing import List, Optional
from pdf2zh_next.translator.registry import TranslatorRegistry

logger = logging.getLogger(__name__)


class PluginLoader:
    """Plugin loader"""
    
    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """
        Initialize plugin loader
        
        Args:
            plugin_dirs: Plugin directory list, use default directories if None
        """
        if plugin_dirs is None:
            self.plugin_dirs = self._get_default_plugin_dirs()
        else:
            self.plugin_dirs = plugin_dirs
        
        self._loaded_plugins = set()
    
    def _get_default_plugin_dirs(self) -> List[Path]:
        """Get default plugin directories"""
        dirs = []
        
        # 1. Built-in plugin directory
        builtin_dir = Path(__file__).parent / "plugins"
        dirs.append(builtin_dir)
        
        # 2. User global plugin directory
        user_dir = Path.home() / ".pdf2zh" / "plugins"
        dirs.append(user_dir)
        
        # 3. Project local plugin directory
        project_dir = Path.cwd() / "pdf2zh_plugins"
        dirs.append(project_dir)
        
        # 4. Environment variable specified plugin directory
        env_plugin_dir = os.environ.get('PDF2ZH_PLUGIN_DIR')
        if env_plugin_dir:
            dirs.append(Path(env_plugin_dir))
        
        return dirs
    
    def load_all_plugins(self) -> int:
        """
        Load plugins from all plugin directories
        
        Returns:
            Number of successfully loaded plugins
        """
        if TranslatorRegistry.is_initialized():
            logger.debug("Plugins already loaded, skipping")
            return len(TranslatorRegistry.list_custom_translators())
        
        loaded_count = 0
        for plugin_dir in self.plugin_dirs:
            if plugin_dir.exists() and plugin_dir.is_dir():
                count = self._load_plugins_from_dir(plugin_dir)
                loaded_count += count
                logger.info(f"Loaded {count} plugins from {plugin_dir}")
            else:
                logger.debug(f"Plugin directory not found: {plugin_dir}")
        
        TranslatorRegistry.set_initialized(True)
        
        # Also set dynamic type manager status
        try:
            from pdf2zh_next.config.dynamic_types import DynamicTypeManager
            DynamicTypeManager.set_initialized(True)
        except ImportError:
            pass
        
        logger.info(f"Total loaded plugins: {loaded_count}")
        return loaded_count
    
    def _load_plugins_from_dir(self, plugin_dir: Path) -> int:
        """
        Load plugins from specified directory
        
        Args:
            plugin_dir: Plugin directory path
            
        Returns:
            Number of successfully loaded plugins
        """
        loaded_count = 0
        
        for py_file in plugin_dir.glob("*.py"):
            # Skip private files and __init__.py
            if py_file.name.startswith("_"):
                continue
            
            if self._load_plugin_file(py_file):
                loaded_count += 1
        
        return loaded_count
    
    def _load_plugin_file(self, plugin_file: Path) -> bool:
        """
        Load single plugin file
        
        Args:
            plugin_file: Plugin file path
            
        Returns:
            Whether loading was successful
        """
        # Avoid duplicate loading
        if str(plugin_file) in self._loaded_plugins:
            return False
        
        try:
            # Dynamically import module
            module_name = f"pdf2zh_plugin_{plugin_file.stem}_{id(plugin_file)}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create spec for plugin: {plugin_file}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to support relative imports
            sys.modules[module_name] = module
            
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                # Clean up sys.modules
                if module_name in sys.modules:
                    del sys.modules[module_name]
                raise e
            
            # Try to call registration function
            success = self._register_plugin_translators(module, plugin_file)
            
            if success:
                self._loaded_plugins.add(str(plugin_file))
                logger.debug(f"Successfully loaded plugin: {plugin_file}")
                return True
            else:
                # Clean up sys.modules
                if module_name in sys.modules:
                    del sys.modules[module_name]
                return False
                
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_file}: {e}")
            return False
    
    def _register_plugin_translators(self, module, plugin_file: Path) -> bool:
        """
        Register translators from plugin
        
        Args:
            module: Plugin module
            plugin_file: Plugin file path
            
        Returns:
            Whether registration was successful
        """
        success = False
        
        # Method 1: Call register_translator function
        if hasattr(module, 'register_translator'):
            try:
                module.register_translator()
                success = True
                logger.debug(f"Registered translators via register_translator() from {plugin_file}")
            except Exception as e:
                logger.error(f"Error calling register_translator() from {plugin_file}: {e}")
        
        # Method 2: Call register_translators function (supports plural form)
        if hasattr(module, 'register_translators'):
            try:
                module.register_translators()
                success = True
                logger.debug(f"Registered translators via register_translators() from {plugin_file}")
            except Exception as e:
                logger.error(f"Error calling register_translators() from {plugin_file}: {e}")
        
        # Method 3: Auto-discover and register (search for translator classes in module)
        auto_registered = self._auto_register_translators(module, plugin_file)
        if auto_registered:
            success = True
        
        if not success:
            logger.warning(f"No translators registered from plugin: {plugin_file}")
        
        return success
    
    def _auto_register_translators(self, module, plugin_file: Path) -> bool:
        """
        Auto-discover and register translators
        
        Args:
            module: Plugin module
            plugin_file: Plugin file path
            
        Returns:
            Whether any translators were registered
        """
        from pdf2zh_next.translator.base_translator import BaseTranslator
        from pydantic import BaseModel
        
        registered = False
        
        # Find classes that inherit from BaseTranslator
        translator_classes = []
        settings_classes = []
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            if (isinstance(attr, type) and 
                issubclass(attr, BaseTranslator) and 
                attr != BaseTranslator):
                translator_classes.append(attr)
            
            elif (isinstance(attr, type) and 
                  issubclass(attr, BaseModel) and 
                  attr != BaseModel and
                  attr_name.endswith('Settings')):
                settings_classes.append(attr)
        
        # Try to match translator classes with settings classes
        for translator_class in translator_classes:
            # Find corresponding settings class
            translator_name = translator_class.__name__.replace('Translator', '')
            settings_class = None
            
            for settings_cls in settings_classes:
                settings_name = settings_cls.__name__.replace('Settings', '')
                if translator_name == settings_name:
                    settings_class = settings_cls
                    break
            
            if settings_class:
                try:
                    # Get translator type from settings class
                    translator_type = translator_name
                    if hasattr(settings_class, 'model_fields') and 'translate_engine_type' in settings_class.model_fields:
                        field = settings_class.model_fields['translate_engine_type']
                        if hasattr(field, 'default'):
                            translator_type = field.default
                    
                    TranslatorRegistry.register(translator_type, translator_class, settings_class)
                    registered = True
                    logger.debug(f"Auto-registered translator {translator_type} from {plugin_file}")
                    
                except Exception as e:
                    logger.error(f"Error auto-registering translator {translator_class.__name__}: {e}")
        
        return registered
    
    def reload_plugin(self, plugin_file: Path) -> bool:
        """
        Reload specified plugin
        
        Args:
            plugin_file: Plugin file path
            
        Returns:
            Whether reload was successful
        """
        # Remove from loaded list
        plugin_path_str = str(plugin_file)
        if plugin_path_str in self._loaded_plugins:
            self._loaded_plugins.remove(plugin_path_str)
        
        return self._load_plugin_file(plugin_file)
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugins"""
        return list(self._loaded_plugins)


# Global plugin loader instance
_global_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get global plugin loader instance"""
    global _global_plugin_loader
    if _global_plugin_loader is None:
        _global_plugin_loader = PluginLoader()
    return _global_plugin_loader


def load_plugins() -> int:
    """Convenient function to load all plugins"""
    loader = get_plugin_loader()
    return loader.load_all_plugins()