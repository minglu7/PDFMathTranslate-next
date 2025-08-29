# 自定义翻译器部署指南（包安装）

自定义翻译器现以“独立 Python 包 + entry points”的方式部署与使用。主程序在运行时自动发现并加载已安装的插件包。

## 🛠️ 部署步骤

### 步骤 1：在插件包中声明入口点

`pyproject.toml` 示例：

```toml
[project]
name = "my-pdf2zh-plugin"
version = "0.1.0"
dependencies = [
  "pdf2zh-next>=0.0.0",
]

[project.entry-points."pdf2zh_next.translators"]
my-translator = "my_plugin.translators.my_translator:register_translator"
```

> 入口点分组固定为 `pdf2zh_next.translators`，值需指向一个可调用对象（如 `register_translator`）。

### 步骤 2：安装插件

- 本地目录：`pip install -e ./my-pdf2zh-plugin`
- Git 仓库：`pip install git+https://github.com/you/my-pdf2zh-plugin.git`
- PyPI：`pip install my-pdf2zh-plugin`

安装完成后，无需复制任何 `.py` 文件到特定目录。

### 步骤 3：验证加载

运行 `pdf2zh --help` 时会动态注入已安装插件的参数；或在代码中触发加载：

```python
from pdf2zh_next.translator import load_plugins, TranslatorRegistry
load_plugins()
print(TranslatorRegistry.list_custom_translators())
```

### 步骤 4：体检插件

安装后可用以下命令检查插件与依赖是否满足：

```bash
pdf2zh-plugin-doctor
```

若有不满足的依赖，命令会给出可执行的 `pip install` 建议。

### 步骤 5：使用插件

```bash
pdf2zh document.pdf --mytranslator  # 具体名称以插件注册为准
```

或在代码中：

```python
from pdf2zh_next.config.model import SettingsModel
from my_plugin.translators.my_translator import MyTranslatorSettings
from pdf2zh_next.translator.utils import get_translator

settings = SettingsModel()
settings.translate_engine_settings = MyTranslatorSettings(api_key="xxx")
translator = get_translator(settings)
```

## 🐳 Docker / 服务器部署

- 在容器构建阶段通过 `pip install <包名或git地址>` 安装插件
- 不再需要设置 `PDF2ZH_PLUGIN_DIR` 或挂载特定目录

## ⚡ 常见问题

- 未被识别：确认插件已安装且入口点分组与名称正确
- 运行报错：确保入口点指向的对象可调用，并在内部调用 `TranslatorRegistry.register(...)`
- 依赖冲突：建议插件使用合适的版本范围；必要时将插件隔离为独立服务或子进程

## ✅ 迁移提示（从旧目录式到包式）

- 旧有的 `~/.pdf2zh/plugins/`、`./pdf2zh_plugins/`、`PDF2ZH_PLUGIN_DIR` 等目录部署方式已弃用
- 将原有单文件插件封装为独立包，并添加 entry point 即可

---
本指南适用于新版（entry point）插件系统。
