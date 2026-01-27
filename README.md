# Way: Dual-Brain Intelligence

> **Next-Generation Personal Agent Architecture.**
> Integrating high-fidelity vision processing with deep logical reasoning.

**Way** is not just a chatbot. It is an autonomous agent built on a **Dual-Brain Architecture**, designed to perceive, reason, and execute. By fusing **Gemini 3 Pro** (Vision) and **Gemini Flash Thinking** (Logic), Way achieves a new level of multimodal interaction.

---

## // Core Capabilities

### 👁️ Vision Core (V-Brain)
*   **Engine**: Gemini 3 Pro (Preview)
*   **Function**: Pixel-level image analysis and semantic understanding.
*   **Capability**: Instantly decodes visual data, converting images into structured context for the logic core.

### 🧠 Logic Core (L-Brain)
*   **Engine**: Gemini Flash Thinking
*   **Function**: Complex reasoning, planning, and code generation.
*   **Capability**: Handles multi-step tasks, maintains deep context, and executes logical operations with precision.

### ⚡ System Features
*   **Dual-Theme UI**: Cyberpunk-inspired Dark/Light modes.
*   **Persistent Memory**: File-based session storage with full history management.
*   **Agent Tools**:
    *   `fs_read`: Access local file systems.
    *   `db_query`: Execute SQLite operations.
    *   `sys_scan`: Analyze directory structures.

---

## // Tech Stack

*   **Runtime**: Python 3.12+
*   **API Interface**: FastAPI / Uvicorn
*   **Frontend**: Vanilla JS / CSS3 (No framework overhead)
*   **Intelligence**: OpenAI SDK (Gemini Adapter)
*   **Storage**: JSON / SQLite

---

## // Quick Start

### 1. Prerequisite
System requires **Python 3.8+**.

### 2. Installation
Initialize the environment and dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configuration
Configure the neural link in `.env`:

```env
# Vision Core Configuration
VISION_API_KEY=sk-xxxx
VISION_BASE_URL=https://api.bltcy.ai/v1
VISION_MODEL=gemini-2.0-pro-exp-02-05

# Logic Core Configuration
LOGIC_API_KEY=sk-xxxx
LOGIC_BASE_URL=https://api.bltcy.ai/v1
LOGIC_MODEL=gemini-2.0-flash-thinking-exp-01-21
```

### 4. Initialization
Launch the neural interface:

```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### 5. Access
Terminal active at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## // Project Structure

```text
personal-agent/
├── core/               # Kernel Modules
│   ├── agent.py        # Main Event Loop (ReAct)
│   ├── llm_client.py   # Logic Interface
│   ├── vision_client.py# Vision Interface
│   └── tools.py        # System Tools
├── data/               # Persistent Storage
├── web/                # User Interface
├── server.py           # API Gateway
└── config.py           # System Config
```

---

## // Security Protocol

*   **API Security**: Keep `.env` strictly confidential.
*   **Filesystem Access**: Agent operates with read/write permissions. Run in a controlled environment.

---

### Credits
**Dev**: 油豆腐 & Feng ZhanWei
*Est. 2026*
