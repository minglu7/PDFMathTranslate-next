"""
Plugin loader (entry-point based)
Loads custom translator plugins from installed Python packages via entry points.
Performs runtime precheck of plugin package requirements and Python version.
"""
import logging
import sys
from typing import Optional, Set, List, Tuple

try:
    # Python 3.10+
    from importlib.metadata import (
        entry_points,
        EntryPoint,
        distributions,
        Distribution,
        version as get_version,
        PackageNotFoundError,
    )
except Exception:  # pragma: no cover - fallback for very old Pythons
    from importlib_metadata import (  # type: ignore
        entry_points,
        EntryPoint,
        distributions,
        Distribution,
        version as get_version,
        PackageNotFoundError,
    )

from pdf2zh_next.translator.registry import TranslatorRegistry

logger = logging.getLogger(__name__)


ENTRYPOINT_GROUP = "pdf2zh_next.translators"


class PluginLoader:
    """Plugin loader using Python entry points."""

    def __init__(self):
        self._loaded_entrypoint_names: Set[str] = set()

    def load_all_plugins(self) -> int:
        """Load plugins from installed packages via entry points.

        Returns:
            int: Number of successfully loaded plugins
        """
        if TranslatorRegistry.is_initialized():
            logger.debug("Plugins already loaded, skipping")
            return len(TranslatorRegistry.list_custom_translators())

        loaded_count = 0
        ep_items = self._discover_entry_points()
        for ep, dist in ep_items:
            try:
                if ep.name in self._loaded_entrypoint_names:
                    continue
                # Precheck requirements of the providing distribution
                ok, warnings = self._precheck_distribution(dist)
                if not ok:
                    for msg in warnings:
                        logger.warning(msg)
                    logger.warning(
                        f"Skipped loading plugin '{ep.name}' due to unmet requirements"
                    )
                    continue
                self._load_from_entry_point(ep)
                self._loaded_entrypoint_names.add(ep.name)
                loaded_count += 1
                logger.info(f"Loaded plugin entry point: {ep.name} -> {ep.value}")
            except Exception as e:
                logger.error(f"Failed to load plugin from entry point {ep.name}: {e}")

        TranslatorRegistry.set_initialized(True)

        # Also set dynamic type manager status
        try:
            from pdf2zh_next.config.dynamic_types import DynamicTypeManager
            DynamicTypeManager.set_initialized(True)
        except ImportError:
            pass

        logger.info(f"Total loaded plugins: {loaded_count}")
        return loaded_count

    def _discover_entry_points(self) -> List[Tuple[EntryPoint, "Distribution"]]:
        """Discover entry points for this application and their distributions."""
        items: List[Tuple[EntryPoint, "Distribution"]] = []
        try:
            for dist in distributions():
                try:
                    for ep in getattr(dist, "entry_points", []):
                        if getattr(ep, "group", None) == ENTRYPOINT_GROUP:
                            items.append((ep, dist))
                except Exception:
                    continue
            logger.debug(
                f"Discovered {len(items)} entry points in group '{ENTRYPOINT_GROUP}'"
            )
        except Exception as e:
            logger.error(f"Error discovering entry points: {e}")
        return items

    def _precheck_distribution(self, dist: "Distribution") -> Tuple[bool, List[str]]:
        """Precheck plugin distribution requirements.

        - Validates Requires-Python
        - Validates Requires-Dist (installed and version-satisfied)
        - Highlights pdf2zh-next compatibility explicitly

        Returns: (ok, messages)
        """
        messages: List[str] = []

        name = dist.metadata.get("Name", "<unknown-plugin>")
        requires_python = (dist.metadata or {}).get("Requires-Python")

        # Attempt to use packaging for robust spec parsing if available
        try:
            from packaging.requirements import Requirement  # type: ignore
            from packaging.specifiers import SpecifierSet  # type: ignore
            from packaging.version import Version  # type: ignore
            from packaging.markers import default_environment  # type: ignore
            from packaging.utils import canonicalize_name  # type: ignore

            # Python version check
            if requires_python:
                try:
                    spec = SpecifierSet(requires_python)
                    py_version = Version(
                        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                    )
                    if py_version not in spec:
                        messages.append(
                            f"Plugin '{name}' requires Python {requires_python}, "
                            f"but current Python is {py_version}. Consider using a compatible Python version or a plugin version supporting your Python."
                        )
                        return False, messages
                except Exception:
                    # If parsing fails, ignore this check
                    pass

            # Dependency checks
            env = default_environment()
            requires = dist.requires or []
            for req_line in requires:
                try:
                    req = Requirement(req_line)
                except Exception:
                    continue

                # Skip if environment marker doesn't match
                if req.marker and not req.marker.evaluate(env):
                    continue

                pkg_name = canonicalize_name(req.name)
                # Emphasize our own package requirement
                if pkg_name in {canonicalize_name("pdf2zh-next"), canonicalize_name("pdf2zh_next")}:
                    try:
                        cur_ver = get_version("pdf2zh-next")
                    except PackageNotFoundError:
                        try:
                            cur_ver = get_version("pdf2zh_next")
                        except PackageNotFoundError:
                            cur_ver = None
                    if cur_ver is None:
                        messages.append(
                            f"Plugin '{name}' requires '{req}', but pdf2zh-next is not installed. Try: pip install 'pdf2zh-next{req.specifier}'"
                        )
                        return False, messages
                    if req.specifier and Version(cur_ver) not in req.specifier:
                        messages.append(
                            f"Plugin '{name}' requires '{req}', but installed pdf2zh-next=={cur_ver} does not satisfy. "
                            f"Try aligning versions, e.g.: pip install 'pdf2zh-next{req.specifier}'"
                        )
                        return False, messages
                    continue

                # General dependency check
                try:
                    installed_ver = get_version(req.name)
                except PackageNotFoundError:
                    messages.append(
                        f"Plugin '{name}' requires '{req}', but '{req.name}' is not installed. Try: pip install '{req.name}{req.specifier}'"
                    )
                    return False, messages

                if req.specifier and Version(installed_ver) not in req.specifier:
                    messages.append(
                        f"Plugin '{name}' requires '{req}', but installed {req.name}=={installed_ver} does not satisfy. "
                        f"Try: pip install '{req.name}{req.specifier}'"
                    )
                    return False, messages

            return True, []

        except Exception:
            # packaging not available or unexpected error; skip strict checks
            logger.debug(
                f"Dependency precheck limited for plugin '{name}' (packaging not available)"
            )
            return True, []

    def _load_from_entry_point(self, ep: "EntryPoint") -> None:
        """Load and execute a plugin registration entry point.

        The entry point should resolve to a callable that performs
        registration by calling TranslatorRegistry.register(...).
        """
        target = ep.load()

        # If the object is a callable, call it (preferred)
        if callable(target):
            target()
            return

        # If it's a module-like object, attempt auto-registration
        try:
            self._auto_register_from_module(target)
        except Exception as e:
            raise RuntimeError(
                f"Entry point '{ep.name}' resolved to non-callable and auto-discovery failed: {e}"
            )

    def _auto_register_from_module(self, module) -> None:
        """Auto-discover translator and settings classes inside a module and register them."""
        from pdf2zh_next.translator.base_translator import BaseTranslator
        from pydantic import BaseModel

        translator_classes = []
        settings_classes = []

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseTranslator) and attr is not BaseTranslator:
                translator_classes.append(attr)
            elif (
                isinstance(attr, type)
                and issubclass(attr, BaseModel)
                and attr is not BaseModel
                and attr_name.endswith("Settings")
            ):
                settings_classes.append(attr)

        any_registered = False
        for t_cls in translator_classes:
            t_name = t_cls.__name__.removesuffix("Translator")
            matched_settings = None
            for s_cls in settings_classes:
                s_name = s_cls.__name__.removesuffix("Settings")
                if s_name == t_name:
                    matched_settings = s_cls
                    break

            if matched_settings is None:
                continue

            translator_type = t_name
            if hasattr(matched_settings, "model_fields") and "translate_engine_type" in matched_settings.model_fields:
                field = matched_settings.model_fields["translate_engine_type"]
                if hasattr(field, "default"):
                    translator_type = field.default

            TranslatorRegistry.register(translator_type, t_cls, matched_settings)
            any_registered = True

        if not any_registered:
            raise RuntimeError("No translator classes discovered for auto-registration")


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
