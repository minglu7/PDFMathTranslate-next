"""
Custom translator plugin template
Users can copy this file and modify it for their own translator implementation
"""
import logging
from typing import Literal
from pydantic import BaseModel, Field
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.translator.base_rate_limiter import BaseRateLimiter
from pdf2zh_next.translator.base_translator import BaseTranslator
from pdf2zh_next.translator.registry import TranslatorRegistry

logger = logging.getLogger(__name__)


class MyCustomSettings(BaseModel):
    """
    自定义翻译器配置类
    
    重要提示：
    1. translate_engine_type 必须是唯一的，不能与其他翻译器重复
    2. support_llm 表示是否支持LLM功能
    3. 所有字段建议使用字符串类型以兼容GUI界面
    4. 需要实现 validate_settings 方法进行配置验证
    """
    
    translate_engine_type: Literal["MyCustom"] = Field(default="MyCustom")
    support_llm: Literal["yes", "no"] = Field(
        default="yes", description="Whether the translator supports LLM"
    )
    
    # Add your custom configuration fields here
    api_key: str | None = Field(
        default=None, description="Your API key"
    )
    base_url: str = Field(
        default="https://api.yourservice.com", 
        description="API base URL"
    )
    model_name: str = Field(
        default="your-model", 
        description="Model name to use"
    )
    # Can add more configuration items...

    def validate_settings(self) -> None:
        """
        Validate configuration validity
        Should raise ValueError if configuration is invalid
        """
        if not self.api_key:
            raise ValueError("API key is required")
        # Add more validation logic...


class MyCustomTranslator(BaseTranslator):
    """
    自定义翻译器实现类
    
    重要提示：
    1. 必须继承 BaseTranslator
    2. 需要实现 do_translate 方法
    3. 如果支持LLM，建议也实现 do_llm_translate 方法
    4. name 属性用于日志和调试
    5. lang_map 可选，用于语言代码映射
    """
    
    name = "my_custom"  # 翻译器名称，用于日志
    support_llm = True  # 是否支持LLM
    
    # 可选：语言代码映射
    lang_map = {
        "zh": "zh-CN",
        "en": "en-US"
    }
    
    def __init__(
        self,
        settings: SettingsModel,
        rate_limiter: BaseRateLimiter,
    ):
        """
        初始化翻译器
        
        Args:
            settings: 全局设置对象
            rate_limiter: 速率限制器
        """
        super().__init__(settings, rate_limiter)
        
        # 获取自定义配置
        config = settings.translate_engine_settings
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.model_name = config.model_name
        
        # 添加影响缓存的参数（重要：这些参数变化时会影响翻译结果）
        self.add_cache_impact_parameters("model_name", self.model_name)
        
        # 在这里添加你的初始化逻辑
        # 例如：初始化API客户端、验证连接等
        
        logger.info(f"Initialized MyCustomTranslator with model: {self.model_name}")
    
    def do_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """
        执行翻译（必须实现）
        
        Args:
            text: 待翻译文本
            rate_limit_params: 速率限制参数（可选）
            
        Returns:
            翻译结果文本
        """
        # 在这里实现你的翻译逻辑
        # 例如：调用API、处理响应等
        
        # 示例实现（请替换为真实的翻译逻辑）
        try:
            # 这里应该是真实的API调用
            # response = your_api_client.translate(
            #     text=text,
            #     source_lang=self.lang_in,
            #     target_lang=self.lang_out,
            #     model=self.model_name
            # )
            # translated = response.translated_text
            
            # 示例返回
            translated = f"[MyCustom] Translated: {text}"
            
            logger.debug(f"Translated text: {text[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def do_llm_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """
        执行LLM翻译（如果支持LLM，建议实现此方法）
        
        Args:
            text: 待翻译文本（通常是完整的提示词）
            rate_limit_params: 速率限制参数（可选）
            
        Returns:
            翻译结果文本
        """
        if text is None:
            return None
        
        # 在这里实现你的LLM翻译逻辑
        # 通常text已经包含了完整的提示词
        
        try:
            # 这里应该是真实的LLM API调用
            # response = your_llm_client.chat_completion(
            #     messages=[{"role": "user", "content": text}],
            #     model=self.model_name
            # )
            # translated = response.choices[0].message.content
            
            # 示例返回
            translated = f"[MyCustom-LLM] {text}"
            
            logger.debug(f"LLM translated text: {text[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"LLM translation failed: {e}")
            raise


def register_translator():
    """
    注册翻译器的函数（必须实现）
    
    插件加载器会自动调用此函数来注册你的翻译器
    你可以在这里注册一个或多个翻译器
    """
    TranslatorRegistry.register(
        "MyCustom",  # 翻译器类型（必须与配置类中的 translate_engine_type 一致）
        MyCustomTranslator,  # 翻译器实现类
        MyCustomSettings,  # 配置类
        support_llm=True  # 是否支持LLM（可选，会自动从配置类检测）
    )
    
    logger.info("Registered MyCustom translator")


# 可选：如果你想同时注册多个翻译器，可以这样做：
"""
def register_translators():  # 注意：函数名是复数形式
    # 注册第一个翻译器
    TranslatorRegistry.register("MyCustom1", MyCustomTranslator1, MyCustomSettings1)
    
    # 注册第二个翻译器
    TranslatorRegistry.register("MyCustom2", MyCustomTranslator2, MyCustomSettings2)
    
    logger.info("Registered multiple custom translators")
"""