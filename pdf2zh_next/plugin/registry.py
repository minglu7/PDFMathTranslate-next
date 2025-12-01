"""
Translator registry center
Supports dynamic registration and management of custom translators
"""
import logging
from typing import Dict, Type, Any, List
from pdf2zh_next.translator.base_translator import BaseTranslator
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TranslatorInfo:
    """Translator information class"""
    
    def __init__(
        self, 
        translator_class: Type[BaseTranslator], 
        settings_class: Type[BaseModel],
        support_llm: bool = False
    ):
        self.translator_class = translator_class
        self.settings_class = settings_class
        self.support_llm = support_llm
        self.translator_type = self._get_translator_type(settings_class)
    
    def _get_translator_type(self, settings_class: Type[BaseModel]) -> str:
        """Extract translator type from settings class"""
        if hasattr(settings_class, 'model_fields') and 'translate_engine_type' in settings_class.model_fields:
            field = settings_class.model_fields['translate_engine_type']
            if hasattr(field, 'default'):
                return field.default
        
        # If not found, use class name
        return settings_class.__name__.replace('Settings', '')


class TranslatorRegistry:
    """Translator registry center"""
    
    _custom_translators: Dict[str, TranslatorInfo] = {}
    _initialized = False
    
    @classmethod
    def register(
        cls, 
        translator_type: str, 
        translator_class: Type[BaseTranslator], 
        settings_class: Type[BaseModel],
        support_llm: bool = None
    ) -> None:
        """
        Register custom translator
        
        Args:
            translator_type: Translator type identifier
            translator_class: Translator implementation class
            settings_class: Settings class
            support_llm: Whether supports LLM, auto-detect if None
        """
        # Auto-detect LLM support
        if support_llm is None:
            support_llm = (
                hasattr(settings_class, 'model_fields') and
                'support_llm' in settings_class.model_fields and
                settings_class.model_fields['support_llm'].default == "yes"
            )
        
        translator_info = TranslatorInfo(translator_class, settings_class, support_llm)
        cls._custom_translators[translator_type] = translator_info
        
        # Also register dynamic type
        try:
            from pdf2zh_next.config.dynamic_types import DynamicTypeManager
            DynamicTypeManager.register_setting_type(settings_class)
        except ImportError:
            logger.warning("Dynamic type manager not available, skipping type registration")
        
        logger.info(f"Registered custom translator: {translator_type}")
    
    @classmethod
    def get_translator_info(cls, translator_type: str) -> TranslatorInfo:
        """Get translator information"""
        return cls._custom_translators.get(translator_type)
    
    @classmethod
    def is_custom_translator(cls, translator_type: str) -> bool:
        """Check if it's a custom translator"""
        return translator_type in cls._custom_translators
    
    @classmethod
    def list_custom_translators(cls) -> List[str]:
        """List all custom translator types"""
        return list(cls._custom_translators.keys())
    
    @classmethod
    def get_all_translator_info(cls) -> Dict[str, TranslatorInfo]:
        """Get all translator information"""
        return cls._custom_translators.copy()
    
    @classmethod
    def unregister(cls, translator_type: str) -> bool:
        """Unregister translator"""
        if translator_type in cls._custom_translators:
            del cls._custom_translators[translator_type]
            logger.info(f"Unregistered custom translator: {translator_type}")
            return True
        return False
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered translators"""
        cls._custom_translators.clear()
        logger.info("Cleared all custom translators")
    
    @classmethod
    def get_settings_classes(cls) -> List[Type[BaseModel]]:
        """Get all custom translator settings classes"""
        return [info.settings_class for info in cls._custom_translators.values()]
    
    @classmethod
    def set_initialized(cls, value: bool = True) -> None:
        """Set initialization status"""
        cls._initialized = value
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if initialized"""
        return cls._initialized