import logging
from typing import Literal

import requests
from pydantic import BaseModel, Field
from tenacity import before_sleep_log
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.config.translate_engine_model import GUI_PASSWORD_FIELDS, GUI_SENSITIVE_FIELDS
from pdf2zh_next.translator.base_rate_limiter import BaseRateLimiter
from pdf2zh_next.translator.base_translator import BaseTranslator
from pdf2zh_next.translator.registry import TranslatorRegistry

logger = logging.getLogger(__name__)


class SungrowSettings(BaseModel):
    """Sungrow Translation API settings"""

    translate_engine_type: Literal["Sungrow"] = Field(default="Sungrow")

    sungrow_api_url: str | None = Field(
        default=None, description="Sungrow translation API server URL"
    )
    sungrow_username: str | None = Field(
        default=None, description="Sungrow API basic auth username"
    )
    sungrow_password: str | None = Field(
        default=None, description="Sungrow API basic auth password"
    )
    sungrow_tenant_id: str | None = Field(
        default=None, description="Sungrow API tenant ID"
    )
    sungrow_scene: str = Field(
        default="UNIVERSAL", description="Translation scene for Sungrow service"
    )

    def validate_settings(self) -> None:
        if not self.sungrow_api_url:
            raise ValueError("Sungrow API URL is required")
        if not self.sungrow_username:
            raise ValueError("Sungrow username is required")
        if not self.sungrow_password:
            raise ValueError("Sungrow password is required")
        if not self.sungrow_tenant_id:
            raise ValueError("Sungrow tenant ID is required")


GUI_PASSWORD_FIELDS.extend(["sungrow_username", "sungrow_password"])
GUI_SENSITIVE_FIELDS.extend(["sungrow_api_url", "sungrow_tenant_id"])


class SungrowTranslator(BaseTranslator):
    """Sungrow translation API implementation"""

    name = "sungrow"
    lang_map = {}

    def __init__(
        self,
        settings: SettingsModel,
        rate_limiter: BaseRateLimiter,
    ):
        super().__init__(settings, rate_limiter)

        cfg: SungrowSettings = settings.translate_engine_settings
        self.api_url = cfg.sungrow_api_url
        self.username = cfg.sungrow_username
        self.password = cfg.sungrow_password
        self.tenant_id = cfg.sungrow_tenant_id
        self.scene = cfg.sungrow_scene
        self.timeout = 60
        self.basic_auth = (self.username, self.password)

        cfg.validate_settings()

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def do_translate(self, text: str, rate_limit_params: dict | None = None):
        if not text or not text.strip():
            return text

        payload = {
            "content": [text],
            "scene": self.scene,
            "inputLang": self.lang_in,
            "outputLang": self.lang_out,
        }
        headers = {"Content-Type": "application/json", "Tenant-Id": self.tenant_id}

        resp = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            auth=self.basic_auth,
            timeout=self.timeout,
        )
        resp.raise_for_status()

        data = resp.json()
        if data.get("code") == 0 and "data" in data:
            translate_res = data["data"].get("translateRes", [])
            return translate_res[0] if translate_res else text

        logger.warning(f"Sungrow API business returned error: {data}")
        return text


def register_translator() -> None:
    """Register translator via entry point callable."""
    TranslatorRegistry.register(
        "Sungrow",
        SungrowTranslator,
        SungrowSettings,
    )

