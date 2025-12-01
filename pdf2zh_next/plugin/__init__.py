"""Plugin system for pdf2zh-next."""

from pdf2zh_next.plugin.loader import PluginLoader, get_plugin_loader, load_plugins
from pdf2zh_next.plugin.registry import TranslatorRegistry, TranslatorInfo

__all__ = ["PluginLoader", "get_plugin_loader", "load_plugins", "TranslatorRegistry", "TranslatorInfo"]