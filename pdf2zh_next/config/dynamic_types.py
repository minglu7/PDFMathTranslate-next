"""
Dynamic type manager
Handles dynamic type registration and validation for custom translators
"""
import logging
from typing import Any, Union, Type, get_args
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class DynamicTypeManager:
    """Dynamic type manager"""
    
    _custom_setting_types = set()
    _initialized = False
    
    @classmethod
    def register_setting_type(cls, setting_type: Type[BaseModel]) -> None:
        """Register custom setting type"""
        cls._custom_setting_types.add(setting_type)
        logger.debug(f"Registered dynamic setting type: {setting_type.__name__}")
    
    @classmethod
    def unregister_setting_type(cls, setting_type: Type[BaseModel]) -> None:
        """Unregister setting type"""
        cls._custom_setting_types.discard(setting_type)
        logger.debug(f"Unregistered dynamic setting type: {setting_type.__name__}")
    
    @classmethod
    def get_all_setting_types(cls) -> set:
        """Get all setting types"""
        return cls._custom_setting_types.copy()
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all setting types"""
        cls._custom_setting_types.clear()
        logger.debug("Cleared all dynamic setting types")
    
    @classmethod
    def is_valid_setting_type(cls, value: Any) -> bool:
        """Check if value is a valid setting type instance"""
        if not hasattr(value, '__class__'):
            return False
        
        value_type = type(value)
        return value_type in cls._custom_setting_types
    
    @classmethod
    def validate_setting_instance(cls, value: Any) -> BaseModel:
        """Validate and return setting instance"""
        if cls.is_valid_setting_type(value):
            return value
        
        # Try to match via translate_engine_type attribute
        if hasattr(value, 'translate_engine_type'):
            engine_type = value.translate_engine_type
            for setting_type in cls._custom_setting_types:
                # Check if it's an instance of this type
                if isinstance(value, setting_type):
                    return value
                
                # Try to match by type name
                if hasattr(setting_type, 'model_fields'):
                    field = setting_type.model_fields.get('translate_engine_type')
                    if field and hasattr(field, 'default') and field.default == engine_type:
                        # Try to convert to correct type
                        try:
                            if isinstance(value, dict):
                                return setting_type(**value)
                            elif hasattr(value, 'model_dump'):
                                return setting_type(**value.model_dump())
                            else:
                                return setting_type(**vars(value))
                        except Exception as e:
                            logger.warning(f"Failed to convert to {setting_type.__name__}: {e}")
                            continue
        
        return None
    
    @classmethod
    def get_setting_type_by_engine_type(cls, engine_type: str) -> Type[BaseModel]:
        """Get setting type by engine type"""
        for setting_type in cls._custom_setting_types:
            if hasattr(setting_type, 'model_fields'):
                field = setting_type.model_fields.get('translate_engine_type')
                if field and hasattr(field, 'default') and field.default == engine_type:
                    return setting_type
        return None
    
    @classmethod
    def set_initialized(cls, value: bool = True) -> None:
        """Set initialization status"""
        cls._initialized = value
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if initialized"""
        # Also check translator registry status
        try:
            from pdf2zh_next.translator.registry import TranslatorRegistry
            return cls._initialized and TranslatorRegistry.is_initialized()
        except ImportError:
            return cls._initialized


def create_dynamic_union_type():
    """
    Create union type containing all dynamic types
    This function is called at runtime to get the latest type union
    """
    from pdf2zh_next.config.translate_engine_model import (
        SiliconFlowFreeSettings, OpenAISettings, GoogleSettings, BingSettings,
        DeepLSettings, DeepSeekSettings, OllamaSettings, XinferenceSettings,
        AzureOpenAISettings, ModelScopeSettings, ZhipuSettings, SiliconFlowSettings,
        TencentSettings, GeminiSettings, AzureSettings, AnythingLLMSettings,
        DifySettings, GrokSettings, GroqSettings, QwenMtSettings, OpenAICompatibleSettings
    )
    
    # Base types
    base_types = (
        SiliconFlowFreeSettings,
        OpenAISettings,
        GoogleSettings,
        BingSettings,
        DeepLSettings,
        DeepSeekSettings,
        OllamaSettings,
        XinferenceSettings,
        AzureOpenAISettings,
        ModelScopeSettings,
        ZhipuSettings,
        SiliconFlowSettings,
        TencentSettings,
        GeminiSettings,
        AzureSettings,
        AnythingLLMSettings,
        DifySettings,
        GrokSettings,
        GroqSettings,
        QwenMtSettings,
        OpenAICompatibleSettings,
    )
    
    # Get dynamic types
    dynamic_types = tuple(DynamicTypeManager.get_all_setting_types())
    
    # Combine all types
    all_types = base_types + dynamic_types
    
    if len(all_types) == 1:
        return all_types[0]
    else:
        return Union[all_types]


def validate_translate_engine_setting(value: Any) -> BaseModel:
    """
    Validate translate engine settings
    This is a custom validator that supports dynamic types
    """
    # Ensure plugins are loaded
    if not DynamicTypeManager.is_initialized():
        try:
            from pdf2zh_next.translator import load_plugins
            load_plugins()
        except ImportError:
            logger.warning("Plugin loader not available")
    
    from pdf2zh_next.config.translate_engine_model import (
        TRANSLATION_ENGINE_SETTING_TYPE, NOT_SUPPORTED_TRANSLATION_ENGINE_SETTING_TYPE
    )
    
    if isinstance(value, NOT_SUPPORTED_TRANSLATION_ENGINE_SETTING_TYPE):
        raise ValueError("Unsupported translation engine setting type")
    
    # Check if it's a built-in type
    builtin_types = get_args(TRANSLATION_ENGINE_SETTING_TYPE)
    for builtin_type in builtin_types:
        if isinstance(value, builtin_type):
            return value
    
    # Handle dict type - common case during deserialization
    if isinstance(value, dict) and 'translate_engine_type' in value:
        engine_type = value['translate_engine_type']
        
        # Try built-in types first
        for builtin_type in builtin_types:
            if hasattr(builtin_type, 'model_fields'):
                field = builtin_type.model_fields.get('translate_engine_type')
                if field and hasattr(field, 'default') and field.default == engine_type:
                    try:
                        return builtin_type(**value)
                    except Exception:
                        continue
        
        # Then try dynamic types
        setting_type = DynamicTypeManager.get_setting_type_by_engine_type(engine_type)
        if setting_type:
            try:
                return setting_type(**value)
            except Exception as e:
                logger.warning(f"Failed to create {setting_type.__name__} from dict: {e}")
        
        raise ValueError(f"Unknown translation engine type: {engine_type}")
    
    # Check if it's a dynamic type
    validated = DynamicTypeManager.validate_setting_instance(value)
    if validated is not None:
        return validated
    
    # If none match, raise error
    raise ValueError(f"Invalid translation engine setting type: {type(value).__name__}")


# Export functions for external use
__all__ = [
    'DynamicTypeManager',
    'create_dynamic_union_type',
    'validate_translate_engine_setting'
]