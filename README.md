# 🔑 API Key Manager CLI

一个基于 Python 的现代化命令行工具，用于安全、快捷地管理您的 API Keys。

它不仅能存储和查询 Key，还集成了类似 `thefuck` 的**模糊匹配纠错**功能和**语义化搜索**能力，防止因手误或记不清名称而找不到 Key。

本项目的设计初衷是本人对于众多网站需要自己保存 APIKEY 到本地感到厌烦，因此写了这样一个简单的管理 API Keys 的项目。项目起名灵感来源于`thefuck`项目，当你在终端输错命令时，输入 fuck（或者你设置的其他别名），它会自动纠正你上一个错误的命令。

## ✨ 核心特性

- **💾 本地存储**: 基于 SQLite 轻量级存储，数据保存在本地，安全可控。
- **🔍 模糊查询**: 输错了 Key 名称？(如 `gihub` -> `github`)，工具会自动猜测并修正您的意图。
- **🧠 语义搜索**: 记不住 Key 的名字？直接搜索描述（如“生产环境 OpenAI”），即可找到对应的 Key。
- **🛡️ 智能防重**: 添加 Key 时会自动检测是否存在类似名称，防止重复创建或意外覆盖，并提供“修正更新”选项。
- **🎨 现代化 UI**: 使用 Rich 库构建，支持彩色输出、表格展示和交互式确认。
- **⚡ UV 驱动**: 采用 `uv` 进行极速依赖管理和打包。

## 🛠️ 安装与开发 (使用 uv)

本项目完全使用 [uv](https://github.com/astral-sh/uv) 进行管理。

### 方式一：作为全局工具安装 (推荐)

如果您想在系统的任何地方直接使用 `apikey` 命令，这是最推荐的方式。

1. 确保已安装 `uv`。
2. 在项目根目录下运行：

   ```bash
   uv tool install .
   ```

3. 现在您可以直接在终端输入命令：
   ```bash
   fuckapi list
   ```

### 方式二：开发模式

如果您需要修改代码或进行调试：

1. **同步环境**:
   ```bash
   uv sync
   ```

2. **运行脚本**:
   使用 `uv run` 在虚拟环境中执行命令：
   ```bash
   uv run fuckapi list
   ```

## 📖 使用指南

### 1. 添加/更新 Key (`add`)

交互式地添加一个新的 API Key。系统会自动检测您是否正在重复创建或覆盖已有的 Key。

```bash
fuckapi add
```

或者使用单行命令：

```bash
fuckapi add -n "openai_gpt4" -v "sk-xxxxxx" -d "GPT-4 生产环境 Key"
```

> **智能防重**: 如果您输入了 `openai_gtp4` (拼写错误)，而库中已有 `openai_gpt4`，工具会提示您：
> *"检测到相似的 Key... 是否要更新原有的 'openai_gpt4' (修正输入)？"*

### 2. 查询 Key (`get`)

这是最强大的功能。您可以输入名称、模糊名称或描述。

**精确/模糊查询:**
```bash
# 假设库里有 'github_token'
fuckapi get github_toke  
# -> 系统提示: ➜ 您是不是要找: 'github_token' ?
```

**语义搜索:**
```bash
# 假设您记不住名字，只记得是用于 "测试环境"
fuckapi get "测试环境"
# -> 系统列出所有描述中包含 "测试环境" 的 Keys
```

### 3. 列出所有 (`list`)

查看当前存储的所有 Key。默认情况下，Key 的值会被隐藏（脱敏）。

```bash
fuckapi list
```

如果需要查看完整的值：

```bash
fuckapi list --show-values
```

## ⚙️ 项目配置 (pyproject.toml)

本项目使用 `pyproject.toml` 管理依赖和元数据。核心依赖如下：

```toml
[project]
name = "apikey-manager"
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "rapidfuzz>=3.0.0",
]

[project.scripts]
fuckapi = "fuckapikey.main:cli"
```

## 📂 数据存储

所有数据默认存储在用户 Home 目录下的 `.fuckapi` 路径下的 `apikeys.db` 文件中。您可以随时备份此文件以保存您的数据。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request！

1. Fork 本项目
2. 使用 `uv sync` 安装依赖
3. 提交您的修改
4. 发起 Pull Request

---
License: MIT