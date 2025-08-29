# 自定义翻译器插件开发指南（基于包安装与入口点）

本指南介绍如何以“独立 Python 包”的形式为 PDF2ZH-next 开发并发布自定义翻译器插件，插件通过 Python entry points 自动被主程序发现与加载。

## 🌟 关键特性

- ✅ 独立包发布：支持本地、Git、PyPI 安装
- ✅ 自动发现：通过 entry points 加载，无需文件复制
- ✅ 类型安全：每个翻译器有独立的 Pydantic 配置模型
- ✅ 热插拔：不修改主项目代码即可扩展

## 🚀 快速开始

示例参考：`examples/pdf2zh-plugin-sungrow/`

检查插件依赖
- 安装插件后，可运行 `pdf2zh-plugin-doctor` 检查插件与当前环境/依赖是否兼容。

### 1) 编写插件代码（示例）

```python
# my_plugin/translators/my_translator.py
from typing import Literal
from pydantic import BaseModel, Field
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.translator.base_rate_limiter import BaseRateLimiter
from pdf2zh_next.translator.base_translator import BaseTranslator
from pdf2zh_next.translator.registry import TranslatorRegistry


class MyTranslatorSettings(BaseModel):
    translate_engine_type: Literal["MyTranslator"] = Field(default="MyTranslator")
    support_llm: Literal["yes", "no"] = Field(default="yes")
    api_key: str | None = Field(default=None, description="API 密钥")
    base_url: str = Field(default="https://api.example.com", description="API 地址")

    def validate_settings(self) -> None:
        if not self.api_key:
            raise ValueError("API key is required")


class MyTranslator(BaseTranslator):
    name = "my_translator"
    support_llm = True

    def __init__(self, settings: SettingsModel, rate_limiter: BaseRateLimiter):
        super().__init__(settings, rate_limiter)
        cfg: MyTranslatorSettings = settings.translate_engine_settings
        self.api_key = cfg.api_key
        self.base_url = cfg.base_url
        self.add_cache_impact_parameters("base_url", self.base_url)

    def do_translate(self, text: str, rate_limit_params: dict | None = None) -> str:
        return f"Translated by MyTranslator: {text}"

    def do_llm_translate(self, text: str, rate_limit_params: dict | None = None) -> str:
        return f"LLM translated: {text}" if text else text


def register_translator() -> None:
    # 调用注册中心完成注册
    TranslatorRegistry.register("MyTranslator", MyTranslator, MyTranslatorSettings)
```

### 2) 在 `pyproject.toml` 声明入口点

插件必须在 `pyproject.toml` 中添加 entry point，供主程序发现：

```toml
[project]
name = "my-pdf2zh-plugin"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
  "pdf2zh-next>=0.0.0",  # 建议声明与主程序的兼容范围
  # 你的插件依赖...
]

[project.entry-points."pdf2zh_next.translators"]
my-translator = "my_plugin.translators.my_translator:register_translator"
```

说明：
- 入口点分组固定为 `pdf2zh_next.translators`
- 入口点值指向一个可调用对象（推荐注册函数），调用后需通过 `TranslatorRegistry.register(...)` 完成注册

### 3) 安装与使用

- 本地路径安装：`pip install -e ./my-pdf2zh-plugin`
- Git 安装：`pip install git+https://github.com/you/my-pdf2zh-plugin.git`
- PyPI 安装：`pip install my-pdf2zh-plugin`

安装后，主程序会在运行时自动发现插件（无需复制到任何目录）。

```python
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.translator.utils import get_translator
from my_plugin.translators.my_translator import MyTranslatorSettings

settings = SettingsModel()
settings.translate_engine_settings = MyTranslatorSettings(api_key="xxx")
translator = get_translator(settings)
print(translator.translate("Hello World"))
```

## 📝 开发规范

- 配置类：继承 `BaseModel`，包含 `translate_engine_type`（Literal），可选 `support_llm`
- 翻译器类：继承 `BaseTranslator`，实现 `do_translate()`，可选 `do_llm_translate()`
- 注册函数：提供入口点指向的可调用（如 `register_translator()`），内部调用 `TranslatorRegistry.register(...)`

## 🔧 进阶：模块自动发现（可选）

若入口点直接指向模块而非可调用对象，加载器将尝试在模块内自动匹配 `*Translator` 与 `*Settings` 并注册。但推荐显式提供注册函数以获得更可控的行为与错误提示。

## 🤝 最佳实践

- 依赖：在 `pyproject.toml` 中声明插件依赖，使用语义化版本范围
- 兼容：建议声明对主程序的依赖范围（如 `pdf2zh-next>=X,<Y`）
- 错误处理：对外部 API 做好重试与异常处理
- 日志：使用标准日志接口，避免过量输出

---

现在你可以用标准 Python 包的方式，发布与分发你的翻译器插件，并被 PDF2ZH-next 自动发现与加载！
