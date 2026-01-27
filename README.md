# Way: 双脑智能架构

> **次世代个人 Agent 架构。**
> 融合高保真视觉处理与深度逻辑推理。

**Way** 不仅仅是一个聊天机器人。它是一个构建在 **双脑架构 (Dual-Brain Architecture)** 之上的自主 Agent，旨在感知、推理和执行。通过融合 **Gemini 3 Pro** (视觉) 和 **Gemini Flash Thinking** (逻辑)，Way 实现了多模态交互的新高度。

---

## // 核心能力

### 👁️ 视觉核心 (V-Brain)
*   **引擎**: Gemini 3 Pro (Preview)
*   **职能**: 像素级图像分析与语义理解。
*   **能力**: 瞬时解码视觉数据，将图像转化为逻辑核心可理解的结构化上下文。

### 🧠 逻辑核心 (L-Brain)
*   **引擎**: Gemini Flash Thinking
*   **职能**: 复杂推理、任务规划与代码生成。
*   **能力**: 处理多步骤任务，保持深度上下文，并精确执行逻辑操作。

### ⚡ 系统特性
*   **双主题 UI**: 赛博朋克风格的深色/浅色模式。
*   **持久化记忆**: 基于文件的会话存储，支持全生命周期历史管理。
*   **Agent 工具箱**:
    *   `fs_read`: 访问本地文件系统。
    *   `db_query`: 执行 SQLite 数据库操作。
    *   `sys_scan`: 深度分析目录结构。

---

## // 技术栈

*   **运行环境**: Python 3.12+
*   **API 接口**: FastAPI / Uvicorn
*   **前端架构**: Vanilla JS / CSS3 (无框架开销，极致轻量)
*   **智能核心**: OpenAI SDK (Gemini Adapter)
*   **数据存储**: JSON / SQLite

---

## // 快速开始

### 1. 前置要求
系统需安装 **Python 3.8+** 环境。

### 2. 安装部署
初始化运行环境与依赖库：

```bash
pip install -r requirements.txt
```

### 3. 神经连接配置
在 `.env` 文件中配置核心参数：

```env
# 视觉核心配置 (Vision Core)
VISION_API_KEY=sk-xxxx
VISION_BASE_URL=https://api.bltcy.ai/v1
VISION_MODEL=gemini-2.0-pro-exp-02-05

# 逻辑核心配置 (Logic Core)
LOGIC_API_KEY=sk-xxxx
LOGIC_BASE_URL=https://api.bltcy.ai/v1
LOGIC_MODEL=gemini-2.0-flash-thinking-exp-01-21
```

### 4. 启动核心
激活神经接口网关：

```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### 5. 接入终端
终端访问地址：[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## // 工程结构

```text
personal-agent/
├── core/               # 内核模块 (Kernel Modules)
│   ├── agent.py        # 主事件循环 (ReAct Loop)
│   ├── llm_client.py   # 逻辑接口
│   ├── vision_client.py# 视觉接口
│   └── tools.py        # 系统工具集
├── data/               # 持久化存储
├── web/                # 用户界面
├── server.py           # API 网关
└── config.py           # 系统配置
```

---

## // 安全协议

*   **API 安全**: 严守 `.env` 配置文件机密性。
*   **文件系统权限**: Agent 拥有文件读写权限。请务必在受控环境中运行。

---

### 开发人员
**Dev**: 油豆腐 & Feng ZhanWei
*Est. 2026*
