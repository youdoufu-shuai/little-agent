# Personal AI Agent (Way)

这是一个基于双脑架构（Dual-Brain Architecture）的智能个人助手，结合了强大的视觉处理能力和逻辑推理能力。它提供了一个现代化的 Web 界面，支持多轮对话历史、主题切换，并具备读取本地文件和查询数据库的能力。

## ✨ 主要特性

   双层架构:
    使用 Gemini 3 Pro 预览版，支持强大的图像理解和分析。
    使用 Gemini Flash Thinking，提供深度推理和复杂的逻辑处理。
   Web 交互界面:

       支持 深色/浅色 主题切换。
       完全本地化的中文界面。
       支持图片上传与预览。
   会话管理:
       基于文件的持久化会话存储。
       支持创建新对话、查看历史记录、删除对话。
       自动生成对话标题。
   工具调用能力 (Agent Tools):
       📂 文件读取: Agent 可以读取本地文件内容。
       🗄️ 数据库查询: Agent 可以执行 SQLite SQL 查询。
       🔎 目录浏览: Agent 可以查看文件系统结构。

## 🛠️ 技术栈

   后端: Python, FastAPI, Uvicorn, OpenAI SDK (兼容 Gemini 调用)
   前端: 原生 HTML5, CSS3 (Flexbox/Grid), JavaScript (ES6+), FontAwesome
   存储: JSON (会话存储), SQLite (可选数据源)

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装 Python 3.8 或更高版本。

### 2. 安装依赖

在项目根目录下运行：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

项目根目录已经包含一个 `.env` 文件模板。您需要确保其中配置了正确的 API Key：

```env
# 视觉模型配置 (Vision Brain)
VISION_API_KEY=your_api_key_here
VISION_BASE_URL=https://api.bltcy.ai/v1
VISION_MODEL=gemini-2.0-pro-exp-02-05

# 逻辑模型配置 (Logic Brain)
LOGIC_API_KEY=your_api_key_here
LOGIC_BASE_URL=https://api.bltcy.ai/v1
LOGIC_MODEL=gemini-2.0-flash-thinking-exp-01-21
```

### 4. 启动服务

使用 Uvicorn 启动后端服务器：

```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### 5. 使用

打开浏览器访问：[http://127.0.0.1:8000](http://127.0.0.1:8000)

   对话: 在输入框输入文字，按回车或点击发送。
   视觉分析: 点击输入框左侧的图片图标上传图片，Agent 会自动分析图片内容。
   管理历史: 左侧边栏显示历史记录，支持点击切换和删除。
   切换主题: 右上角按钮可切换日间/夜间模式。
   工具使用: 您可以直接告诉 Agent "请读取 xxx 文件" 或 "查询 xxx 数据库"，它会自动调用工具执行。

## 📁 目录结构

```
personal-agent/
├── core/               # 核心逻辑模块
│   ├── agent.py        # Agent 主体逻辑 (ReAct 循环)
│   ├── llm_client.py   # LLM 客户端封装
│   ├── vision_client.py# 视觉模型客户端封装
│   ├── session_manager.py # 会话管理 (CRUD)
│   └── tools.py        # 工具函数定义 (文件/DB操作)
├── data/               # 数据存储
│   └── sessions/       # 会话 JSON 文件
├── web/                # 前端静态资源
│   ├── index.html      # 主页面
│   ├── style.css       # 样式表
│   └── app.js          # 前端交互逻辑
├── server.py           # FastAPI 服务入口
├── config.py           # 配置加载
├── requirements.txt    # 项目依赖
└── .env                # 环境变量配置
```

## 📝 注意事项

   请妥善保管您的 API Key。
   Agent 具有读取本地文件的权限，请在安全的环境下运行。

## 制作人：油豆腐，Feng ZhanWei
