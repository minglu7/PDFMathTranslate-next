import importlib
import logging

from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.config.translate_engine_model import (
    NOT_SUPPORTED_TRANSLATION_ENGINE_SETTING_TYPE,
)
from pdf2zh_next.config.translate_engine_model import TRANSLATION_ENGINE_METADATA
from pdf2zh_next.config.translate_engine_model import TranslateEngineSettingError
from pdf2zh_next.translator.base_rate_limiter import BaseRateLimiter
from pdf2zh_next.translator.base_translator import BaseTranslator
from pdf2zh_next.translator.rate_limiter.qps_rate_limiter import QPSRateLimiter
from pdf2zh_next.translator.registry import TranslatorRegistry
from pdf2zh_next.translator.plugin_loader import load_plugins

logger = logging.getLogger(__name__)


def get_rate_limiter(settings: SettingsModel) -> BaseRateLimiter:
    if settings.translation.qps:
        return QPSRateLimiter(settings.translation.qps)
    else:
        return None


def get_translator(settings: SettingsModel) -> BaseTranslator:
    # Load all plugins first
    load_plugins()
    
    rate_limiter = get_rate_limiter(settings=settings)
    translator_config = settings.translate_engine_settings

    if isinstance(translator_config, NOT_SUPPORTED_TRANSLATION_ENGINE_SETTING_TYPE):
        raise TranslateEngineSettingError(
            f"{translator_config.translate_engine_type} is not supported, Please use other translator!"
        )

    # Check if it's a custom translator
    translate_engine_type = translator_config.translate_engine_type
    translator_info = TranslatorRegistry.get_translator_info(translate_engine_type)
    
    if translator_info:
        # Use custom translator
        logger.info(f"Using custom translator: {translate_engine_type}")
        
        # Check glossary support
        if settings.translation.glossaries and not translator_info.support_llm:
            raise TranslateEngineSettingError(
                f"{translate_engine_type} does not support glossary. Please choose a different translator or remove the glossary."
            )
        
        return translator_info.translator_class(settings, rate_limiter)

    # Use built-in translator (original logic)
    for metadata in TRANSLATION_ENGINE_METADATA:
        if isinstance(translator_config, metadata.setting_model_type):
            translate_engine_type = metadata.translate_engine_type
            logger.info(f"Using built-in translator: {translate_engine_type}")
            model_name = f"pdf2zh_next.translator.translator_impl.{translate_engine_type.lower()}"
            module = importlib.import_module(model_name)
            if settings.translation.glossaries and not metadata.support_llm:
                raise TranslateEngineSettingError(
                    f"{translate_engine_type} does not support glossary. Please choose a different translator or remove the glossary."
                )
            return getattr(module, f"{translate_engine_type}Translator")(
                settings, rate_limiter
            )

    raise ValueError(f"No translator found for type: {translate_engine_type}")
