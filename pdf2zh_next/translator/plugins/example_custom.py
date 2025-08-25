"""
Example custom translator plugin
Demonstrates how to create custom translators
"""
import logging
from typing import Literal
from pydantic import BaseModel, Field
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.translator.base_rate_limiter import BaseRateLimiter
from pdf2zh_next.translator.base_translator import BaseTranslator
from pdf2zh_next.translator.registry import TranslatorRegistry

logger = logging.getLogger(__name__)


class LLMEnabledExampleSettings(BaseModel):
    """Settings for LLM-enabled example translator"""
    
    translate_engine_type: Literal["LLMEnabledExample"] = Field(default="LLMEnabledExample")
    support_llm: Literal["yes", "no"] = Field(
        default="yes", description="Whether the translator supports LLM"
    )
    
    api_key: str | None = Field(
        default=None, description="API key for LLM-enabled example service"
    )
    base_url: str = Field(
        default="https://api.example.com", 
        description="Base URL for LLM-enabled example service"
    )
    model_name: str = Field(
        default="example-model", 
        description="Model name to use"
    )
    temperature: float = Field(
        default=0.7, 
        description="Temperature for text generation"
    )

    def validate_settings(self) -> None:
        """Validate settings"""
        if not self.api_key:
            raise ValueError("LLM Enabled Example API key is required")


class LLMEnabledExampleTranslator(BaseTranslator):
    """Example translator with LLM support"""
    
    name = "llm_enabled_example"
    support_llm = True
    lang_map = {"zh": "zh-CN", "en": "en-US"} 
    
    def __init__(
        self,
        settings: SettingsModel,
        rate_limiter: BaseRateLimiter,
    ):
        super().__init__(settings, rate_limiter)
        
        # Get custom configuration
        config = settings.translate_engine_settings
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        self.temperature = config.temperature
        
        # Add cache-affecting parameters
        self.add_cache_impact_parameters("model_name", self.model_name)
        self.add_cache_impact_parameters("temperature", self.temperature)
        
        logger.info(f"Initialized LLMEnabledExampleTranslator with model: {self.model_name}")
    
    def do_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """
        Execute translation
        This is example implementation, should call real API in actual use
        """
        # Example: simple text processing
        translated = f"[{self.name}] Translated from {self.lang_in} to {self.lang_out}: {text}"
        
        logger.debug(f"Translated text: {text[:50]}...")
        return translated
    
    def do_llm_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """
        Execute LLM translation (if supported)
        """
        if text is None:
            return None
        
        # Example: LLM-style translation
        translated = f"[{self.name}-LLM] {text} -> (translated with model {self.model_name})"
        
        logger.debug(f"LLM translated text: {text[:50]}...")
        return translated


class NoLLMExampleSettings(BaseModel):
    """Settings for No-LLM example translator"""
    
    translate_engine_type: Literal["NoLLMExample"] = Field(default="NoLLMExample")
    support_llm: Literal["yes", "no"] = Field(
        default="no", description="Whether the translator supports LLM"
    )
    
    service_url: str = Field(
        default="https://translate.no-llm-example.com",
        description="Service URL for No-LLM translator"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )

    def validate_settings(self) -> None:
        """Validate settings"""
        pass


class NoLLMExampleTranslator(BaseTranslator):
    """Example translator without LLM support"""
    
    name = "no_llm_example"
    support_llm = False
    
    def __init__(
        self,
        settings: SettingsModel,
        rate_limiter: BaseRateLimiter,
    ):
        super().__init__(settings, rate_limiter)
        config = settings.translate_engine_settings
        self.service_url = config.service_url
        self.timeout = config.timeout
        
        logger.info(f"Initialized NoLLMExampleTranslator with URL: {self.service_url}")
    
    def do_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """Execute translation"""
        translated = f"[{self.name}] Simple translation: {text}"
        return translated


def register_translator():
    """
    Function to register translators
    Plugin loader will automatically call this function
    """
    # Register first translator (with LLM support)
    TranslatorRegistry.register(
        "LLMEnabledExample",
        LLMEnabledExampleTranslator,
        LLMEnabledExampleSettings,
        support_llm=True
    )
    
    # Register second translator (without LLM support)
    TranslatorRegistry.register(
        "NoLLMExample",
        NoLLMExampleTranslator,
        NoLLMExampleSettings,
        support_llm=False
    )
    
    logger.info("Registered example custom translators: LLMEnabledExample, NoLLMExample")