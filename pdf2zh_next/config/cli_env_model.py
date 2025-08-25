from __future__ import annotations

import logging

from pydantic import Field
from pydantic import create_model

from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.config.translate_engine_model import _DEFAULT_TRANSLATION_ENGINE
from pdf2zh_next.config.translate_engine_model import TRANSLATION_ENGINE_METADATA

logger = logging.getLogger(__name__)

# The following is magic code,
# if you need to modify it,
# please contact the maintainer!

__translation_flag_fields = {
    x.cli_flag_name: (
        bool,
        Field(
            default=False, description=f"Use {x.translate_engine_type} for translation"
        ),
    )
    for x in TRANSLATION_ENGINE_METADATA
}

__translation_flag_fields.update(
    {
        x.cli_detail_field_name: (
            x.setting_model_type,
            Field(default_factory=x.setting_model_type),
        )
        for x in TRANSLATION_ENGINE_METADATA
        if x.cli_detail_field_name
    }
)

__exclude_fields = list(__translation_flag_fields.keys())

# If you want to use more field parameters in `pdf2zh_next/config/model.py`
# please add the corresponding forwarding here!

__cli_env_settings_model_fields = {
    k: (
        v.annotation,
        Field(
            default=v.default,
            description=v.description,
            default_factory=v.default_factory,
            alias=v.alias,
            discriminator=v.discriminator,
        ),
    )
    for k, v in SettingsModel.model_fields.items()
    if k != "translate_engine_settings"
}
__cli_env_settings_model_fields.update(__translation_flag_fields)

CLIEnvSettingsModel = create_model(
    "CLIEnvSettingsModel",
    **__cli_env_settings_model_fields,
)


def to_settings_model(self) -> SettingsModel:
    # Get model data excluding translation engine flags
    model_data = self.model_dump(exclude=__exclude_fields)
    
    # Check if translate_engine_settings is provided directly (from config file)
    if hasattr(self, 'translate_engine_settings') and self.translate_engine_settings is not None:
        translate_engine_settings = self.translate_engine_settings
    # Also check _extra_args for translate_engine_settings (from config file processing)
    elif hasattr(self, '_extra_args') and 'translate_engine_settings' in getattr(self, '_extra_args', {}):
        translate_engine_settings = self._extra_args['translate_engine_settings']
    else:
        # Check for custom translators first
        translate_engine_settings = None
        try:
            from pdf2zh_next.translator import load_plugins
            from pdf2zh_next.translator.registry import TranslatorRegistry
            
            load_plugins()
            custom_translators = TranslatorRegistry.get_all_translator_info()
            
            for translator_type, translator_info in custom_translators.items():
                flag_name = translator_type.lower()
                # Check if this custom translator was selected
                extra_args = getattr(self, '_extra_args', {})
                if extra_args.get(flag_name, False):
                    # Build settings from CLI args
                    settings_data = {'translate_engine_type': translator_type}
                    settings_class = translator_info.settings_class
                    
                    for field_name, field_info in settings_class.model_fields.items():
                        if field_name == 'translate_engine_type':
                            continue
                        
                        cli_field_name = field_name.lower()
                        if cli_field_name in extra_args:
                            value = extra_args[cli_field_name]
                            if value is not None:
                                settings_data[field_name] = value
                    
                    translate_engine_settings = settings_class(**settings_data)
                    break
        except Exception as e:
            logger.debug(f"Error checking custom translators: {e}")
        
        # If no custom translator found, check predefined ones
        if translate_engine_settings is None:
            for metadata in TRANSLATION_ENGINE_METADATA:
                if getattr(self, metadata.cli_flag_name):
                    if metadata.cli_detail_field_name:
                        translate_engine_settings = metadata.setting_model_type(
                            **getattr(self, metadata.cli_detail_field_name).model_dump()
                        )
                    else:
                        translate_engine_settings = metadata.setting_model_type()
                    break
            else:
                logger.warning("No translation engine selected, using SiliconFlow Free")
                translate_engine_settings = _DEFAULT_TRANSLATION_ENGINE()

    return SettingsModel(
        **model_data,
        translate_engine_settings=translate_engine_settings,
    )


def validate_settings(self) -> None:
    self.to_settings_model().validate_settings()


def clone(self):
    return self.model_copy(deep=True)


CLIEnvSettingsModel.to_settings_model = to_settings_model
CLIEnvSettingsModel.validate_settings = validate_settings
CLIEnvSettingsModel.clone = clone
