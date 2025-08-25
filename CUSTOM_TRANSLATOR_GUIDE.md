# 自定义翻译器插件开发指南

本指南介绍如何为 PDF2ZH-next 项目开发自定义翻译器插件。

## 🌟 功能特性

- ✅ 支持**无限数量**的自定义翻译器
- ✅ **热插拔**：无需修改核心代码
- ✅ **多级插件目录**：支持内置、全局和项目级插件
- ✅ **自动发现**：插件自动加载和注册
- ✅ **类型安全**：每个翻译器都有独立的配置模型
- ✅ **向后兼容**：不影响现有任何代码

## 📁 插件目录结构

```
pdf2zh_next/
├── translator/plugins/           # 内置插件示例
│   ├── example_custom.py        # 示例插件
│   └── template.py              # 插件模板
├── ~/.pdf2zh/plugins/           # 用户全局插件目录
├── ./pdf2zh_plugins/            # 项目本地插件目录
└── $PDF2ZH_PLUGIN_DIR/         # 环境变量指定的插件目录
```

## 🚀 快速开始

### 1. 创建插件文件

复制 `pdf2zh_next/translator/plugins/template.py` 并修改：

```python
from typing import Literal
from pydantic import BaseModel, Field
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.translator.base_rate_limiter import BaseRateLimiter
from pdf2zh_next.translator.base_translator import BaseTranslator
from pdf2zh_next.translator.registry import TranslatorRegistry

class MyTranslatorSettings(BaseModel):
    """翻译器配置类"""
    translate_engine_type: Literal["MyTranslator"] = Field(default="MyTranslator")
    support_llm: Literal["yes", "no"] = Field(default="yes")
    
    api_key: str | None = Field(default=None, description="API密钥")
    base_url: str = Field(default="https://api.example.com", description="API地址")
    
    def validate_settings(self) -> None:
        if not self.api_key:
            raise ValueError("API key is required")

class MyTranslator(BaseTranslator):
    """翻译器实现类"""
    name = "my_translator"
    support_llm = True
    
    def __init__(self, settings: SettingsModel, rate_limiter: BaseRateLimiter):
        super().__init__(settings, rate_limiter)
        config = settings.translate_engine_settings
        self.api_key = config.api_key
        self.base_url = config.base_url
        
        # 添加影响缓存的参数
        self.add_cache_impact_parameters("api_key", self.api_key)
    
    def do_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """实现翻译逻辑"""
        # 这里调用你的翻译API
        translated = f"Translated by MyTranslator: {text}"
        return translated
    
    def do_llm_translate(self, text: str, rate_limit_params: dict = None) -> str:
        """实现LLM翻译逻辑（可选）"""
        if text is None:
            return None
        # 这里调用你的LLM API
        return f"LLM translated: {text}"

def register_translator():
    """注册翻译器"""
    TranslatorRegistry.register(
        "MyTranslator",
        MyTranslator, 
        MyTranslatorSettings
    )
```

### 2. 放置插件文件

将插件文件放到以下任一目录：
- `~/.pdf2zh/plugins/my_translator.py` （推荐用户插件）
- `./pdf2zh_plugins/my_translator.py` （项目级插件）
- `pdf2zh_next/translator/plugins/my_translator.py` （内置插件）

### 3. 使用插件

```python
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.translator.utils import get_translator
from your_plugin import MyTranslatorSettings

# 创建配置
settings = SettingsModel()
settings.translate_engine_settings = MyTranslatorSettings(
    api_key="your-api-key",
    base_url="https://your-api.com"
)

# 创建翻译器
translator = get_translator(settings)

# 使用翻译器
result = translator.translate("Hello World")
print(result)
```

## 📝 开发规范

### 配置类要求

1. **必须继承 `BaseModel`**
2. **必须有 `translate_engine_type` 字段**（Literal类型）
3. **建议有 `support_llm` 字段**
4. **实现 `validate_settings()` 方法**

### 翻译器类要求

1. **必须继承 `BaseTranslator`**
2. **必须实现 `do_translate()` 方法**
3. **如果支持LLM，实现 `do_llm_translate()` 方法**
4. **设置合适的 `name` 属性**

### 注册函数

插件必须提供以下函数之一：
- `register_translator()` - 注册单个翻译器
- `register_translators()` - 注册多个翻译器

## 🔧 高级功能

### 多翻译器插件

```python
def register_translators():
    """注册多个翻译器"""
    TranslatorRegistry.register("TranslatorA", TranslatorA, TranslatorASettings)
    TranslatorRegistry.register("TranslatorB", TranslatorB, TranslatorBSettings)
```

### 语言映射

```python
class MyTranslator(BaseTranslator):
    lang_map = {
        "zh": "zh-CN",
        "en": "en-US"
    }
```

### 缓存参数

```python
def __init__(self, settings, rate_limiter):
    super().__init__(settings, rate_limiter)
    # 添加影响翻译结果的参数到缓存键
    self.add_cache_impact_parameters("model", self.model_name)
    self.add_cache_impact_parameters("temperature", self.temperature)
```

## 🧪 测试插件

使用项目提供的测试脚本：

```bash
python test_plugin_system.py
```

## 📚 示例插件

项目提供了完整的示例插件：

1. **`example_custom.py`** - 完整功能示例
2. **`template.py`** - 开发模板

## 🤝 最佳实践

1. **错误处理**：妥善处理API调用异常
2. **日志记录**：使用适当的日志级别
3. **配置验证**：在 `validate_settings()` 中验证配置
4. **缓存策略**：合理设置缓存影响参数
5. **文档注释**：为配置字段提供清晰的描述

## 🔍 调试提示

1. **查看日志**：设置日志级别为 `DEBUG` 查看详细信息
2. **插件加载**：检查插件是否正确放置在插件目录中
3. **配置验证**：确保 `translate_engine_type` 唯一且匹配
4. **依赖管理**：确保插件所需的依赖包已安装

## 💡 贡献插件

欢迎将优秀的插件贡献给项目！请提交PR到 `pdf2zh_next/translator/plugins/` 目录。

---

现在您已经掌握了创建自定义翻译器插件的完整流程！开始构建属于您自己的翻译器吧！ 🚀