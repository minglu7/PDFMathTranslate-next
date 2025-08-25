# 自定义翻译器部署指南

## 📁 部署目录选择

插件系统会按以下优先级搜索自定义翻译器：

### 1. 用户全局目录（推荐个人用户）
```bash
~/.pdf2zh/plugins/your_translator.py
```
**适用场景:**
- 个人开发者
- 跨多个项目使用同一翻译器
- 不想修改项目代码结构

**使用方法:**
```bash
mkdir -p ~/.pdf2zh/plugins
cp your_translator.py ~/.pdf2zh/plugins/
pdf2zh document.pdf --your-translator
```

### 2. 项目本地目录（推荐团队项目）
```bash
your-project-root/pdf2zh_plugins/your_translator.py
```
**适用场景:**
- 团队协作项目
- 需要版本控制的翻译器
- 项目特定的翻译需求

**使用方法:**
```bash
cd your-project
mkdir -p pdf2zh_plugins
cp your_translator.py pdf2zh_plugins/
git add pdf2zh_plugins/your_translator.py
pdf2zh document.pdf --your-translator
```

### 3. 环境变量目录（推荐服务器部署）
```bash
export PDF2ZH_PLUGIN_DIR=/opt/pdf2zh/plugins
```
**适用场景:**
- 服务器环境
- Docker 容器部署
- 需要集中管理多个翻译器

**使用方法:**
```bash
# 方法1: 临时设置
export PDF2ZH_PLUGIN_DIR=/path/to/plugins
pdf2zh document.pdf --your-translator

# 方法2: 永久设置（添加到 .bashrc 或 .profile）
echo 'export PDF2ZH_PLUGIN_DIR=/opt/pdf2zh/plugins' >> ~/.bashrc
source ~/.bashrc
```

### 4. 源码目录（不推荐）
```bash
pdf2zh_next/translator/plugins/your_translator.py
```
**注意:** 升级软件时会丢失，仅用于开发测试。

## 🛠️ 部署步骤详解

### 步骤1: 准备翻译器代码
使用提供的模板创建您的翻译器：
```bash
cp pdf2zh_next/translator/plugins/template.py.disabled your_translator.py
# 根据模板中的注释修改代码
```

### 步骤2: 选择部署目录
根据您的使用场景选择合适的目录（见上文）。

### 步骤3: 部署文件
将翻译器文件复制到选定目录。

### 步骤4: 验证部署
```bash
pdf2zh --help | grep your-translator
# 如果能看到您的翻译器参数，说明部署成功
```

### 步骤5: 使用翻译器
```bash
# 命令行方式
pdf2zh document.pdf --your-translator --your-api-key "key"

# 配置文件方式  
pdf2zh document.pdf --config-file your_config.toml
```

## 🐳 Docker 部署

### Dockerfile 示例
```dockerfile
FROM your-base-image

# 创建插件目录
RUN mkdir -p /opt/pdf2zh/plugins

# 复制翻译器文件
COPY your_translator.py /opt/pdf2zh/plugins/

# 设置环境变量
ENV PDF2ZH_PLUGIN_DIR=/opt/pdf2zh/plugins

# 其他配置...
```

### Docker Compose 示例
```yaml
version: '3.8'
services:
  pdf2zh:
    image: your-pdf2zh-image
    environment:
      - PDF2ZH_PLUGIN_DIR=/opt/pdf2zh/plugins
    volumes:
      - ./plugins:/opt/pdf2zh/plugins
    # 其他配置...
```

## ⚡ 性能优化建议

1. **避免重复加载**: 插件系统有缓存机制，但建议在生产环境中固定插件位置。

2. **错误处理**: 确保您的翻译器有完善的错误处理，避免影响主程序。

3. **依赖管理**: 如果翻译器需要额外依赖，建议在部署说明中明确列出。

## 🔍 故障排除

### 插件未被识别
1. 检查文件名（不能以 `_` 开头）
2. 确保有 `register_translator()` 函数
3. 检查目录权限

### 命令行参数未出现
1. 重新启动终端
2. 检查插件是否有语法错误
3. 查看调试日志

### 配置文件不生效
1. 检查 TOML 语法
2. 确保 `translate_engine_type` 与注册名称匹配
3. 验证配置文件路径

## 📞 技术支持

如遇问题，请提供：
1. 插件文件内容
2. 部署目录路径  
3. 错误信息
4. 使用的命令

---
*本指南适用于 pdf2zh-next 自定义翻译器插件系统*