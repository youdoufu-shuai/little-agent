import os
import base64
import json
import io
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

# 导入 Agent
from core.agent import PersonalAgent

# 加载环境变量
load_dotenv()

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Agent
agent = PersonalAgent()

# 提供静态文件服务
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("web/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/style.css")
async def get_css():
    with open("web/style.css", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="text/css")

@app.get("/app.js")
async def get_js():
    with open("web/app.js", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="application/javascript")

@app.get("/marked.min.js")
async def get_marked():
    with open("web/marked.min.js", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), media_type="application/javascript")

class DBConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None

class FileConfig(BaseModel):
    allow_read: bool = True
    allowed_paths: List[str] = []

class ChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    db_config: Optional[Dict[str, Any]] = None
    file_config: Optional[FileConfig] = None
    max_steps: Optional[int] = 10

class APIConfig(BaseModel):
    logic_base_url: Optional[str] = None
    logic_api_key: Optional[str] = None
    logic_model: Optional[str] = None
    vision_base_url: Optional[str] = None
    vision_api_key: Optional[str] = None
    vision_model: Optional[str] = None

class PersonaActivateRequest(BaseModel):
    persona_id: str

class PersonaCreateRequest(BaseModel):
    name: str
    description: str
    system_prompt: str

@app.get("/api/personas")
async def list_personas():
    return agent.persona_manager.list_personas()

@app.post("/api/personas")
async def create_persona(request: PersonaCreateRequest):
    try:
        new_persona = agent.persona_manager.add_persona(
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt
        )
        return new_persona
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/personas/activate")
async def activate_persona(request: PersonaActivateRequest):
    try:
        agent.persona_manager.set_active_persona(request.persona_id)
        return {"status": "success", "active_persona_id": request.persona_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str):
    try:
        success = agent.persona_manager.delete_persona(persona_id)
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Persona not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/config")
async def update_config(config: APIConfig):
    """
    更新 API 配置（URL, Key, Model）。
    这将更新运行时的环境变量，并尝试写入 .env 文件以持久化。
    """
    try:
        from config import Config
        import re

        # 更新运行时配置 (Logic)
        if config.logic_base_url:
            os.environ["LOGIC_BASE_URL"] = config.logic_base_url
            Config.LOGIC_BASE_URL = config.logic_base_url
        if config.logic_api_key:
            os.environ["LOGIC_API_KEY"] = config.logic_api_key
            Config.LOGIC_API_KEY = config.logic_api_key
        if config.logic_model:
            os.environ["LOGIC_MODEL"] = config.logic_model
            Config.LOGIC_MODEL = config.logic_model

        # 更新运行时配置 (Vision)
        if config.vision_base_url:
            os.environ["VISION_BASE_URL"] = config.vision_base_url
            Config.VISION_BASE_URL = config.vision_base_url
        if config.vision_api_key:
            os.environ["VISION_API_KEY"] = config.vision_api_key
            Config.VISION_API_KEY = config.vision_api_key
        if config.vision_model:
            os.environ["VISION_MODEL"] = config.vision_model
            Config.VISION_MODEL = config.vision_model

        # 尝试更新 .env 文件
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_content = f.read()
            
            # 辅助函数：更新或追加
            def update_env_var(content, key, value):
                if not value:
                    return content
                pattern = f"^{key}=.*$"
                replacement = f"{key}={value}"
                if re.search(pattern, content, re.MULTILINE):
                    return re.sub(pattern, replacement, content, flags=re.MULTILINE)
                else:
                    return content + f"\n{replacement}"

            env_content = update_env_var(env_content, "LOGIC_BASE_URL", config.logic_base_url)
            env_content = update_env_var(env_content, "LOGIC_API_KEY", config.logic_api_key)
            env_content = update_env_var(env_content, "LOGIC_MODEL", config.logic_model)
            
            env_content = update_env_var(env_content, "VISION_BASE_URL", config.vision_base_url)
            env_content = update_env_var(env_content, "VISION_API_KEY", config.vision_api_key)
            env_content = update_env_var(env_content, "VISION_MODEL", config.vision_model)
            
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_content)
        
        # 重新初始化 Agent 以应用更改 (如果 Agent 内部缓存了这些值)
        # 注意：Agent 实例是全局的，如果它在 __init__ 中读取了配置，需要重新实例化
        global agent
        agent = PersonalAgent()

        return {"status": "success", "message": "配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 构建 Agent 消息（模仿 Plato 格式）
        message = {
            "chat_id": "web-user",
            "text": request.text,
            "image": None,
            "db_config": request.db_config,
            "file_config": request.file_config.dict() if request.file_config else None,
            "max_steps": request.max_steps
        }
        
        result = agent.process_message(message, session_id=request.session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    try:
        message = {
            "chat_id": "web-user",
            "text": request.text,
            "image": None,
            "db_config": request.db_config,
            "file_config": request.file_config.dict() if request.file_config else None,
            "max_steps": request.max_steps
        }
        
        def event_generator():
            try:
                for event in agent.process_message_stream(message, session_id=request.session_id):
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except Exception as e:
                err_event = {"type": "error", "content": str(e)}
                yield f"data: {json.dumps(err_event, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vision")
async def vision_endpoint(text: str = Form(...), session_id: Optional[str] = Form(None), db_config: Optional[str] = Form(None), file_config: Optional[str] = Form(None), file: UploadFile = File(...)):
    try:
        content_type = file.content_type
        filename = file.filename
        
        message_image = None
        extracted_text = ""
        
        # Check if it's an image
        if content_type.startswith("image/"):
            # 读取并编码图像
            contents = await file.read()
            encoded = base64.b64encode(contents).decode('utf-8')
            data_uri = f"data:{file.content_type};base64,{encoded}"
            message_image = data_uri
        else:
             # Document processing
             contents = await file.read()
             file_like = io.BytesIO(contents)
             
             if filename.lower().endswith(".pdf"):
                 try:
                     reader = PdfReader(file_like)
                     for page in reader.pages:
                         extracted_text += page.extract_text() + "\n"
                 except Exception as e:
                     extracted_text = f"[Error reading PDF: {str(e)}]"
             elif filename.lower().endswith(".docx"):
                 try:
                     doc = Document(file_like)
                     for para in doc.paragraphs:
                         extracted_text += para.text + "\n"
                 except Exception as e:
                     extracted_text = f"[Error reading DOCX: {str(e)}]"
             else:
                 # Assume text/code
                 try:
                     extracted_text = contents.decode("utf-8")
                 except UnicodeDecodeError:
                      try:
                         extracted_text = contents.decode("gbk")
                      except:
                         extracted_text = "[Error: Unable to decode file content as text]"
        
        # 如果存在，解析 db_config
        parsed_db_config = None
        if db_config:
            try:
                parsed_db_config = json.loads(db_config)
            except:
                pass

        # 如果存在，解析 file_config
        parsed_file_config = None
        if file_config:
            try:
                parsed_file_config = json.loads(file_config)
            except:
                pass

        # Append extracted text to user message
        final_text = text
        if extracted_text:
            final_text += f"\n\n[Attached File Content: {filename}]\n{extracted_text}\n[End of File Content]"

        # 构建消息
        message = {
            "chat_id": "web-user",
            "text": final_text,
            "image": message_image,
            "db_config": parsed_db_config,
            "file_config": parsed_file_config
        }
        
        result = agent.process_message(message, session_id=session_id)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 历史记录 / 会话管理 API

@app.get("/api/sessions")
async def list_sessions():
    return agent.session_manager.list_sessions()

@app.post("/api/sessions")
async def create_session():
    return agent.session_manager.create_session()

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = agent.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# 人格管理 API

class PersonaCreate(BaseModel):
    name: str
    description: str
    system_prompt: str

@app.get("/api/personas")
async def list_personas():
    return agent.persona_manager.list_personas()

@app.post("/api/personas")
async def create_persona(p: PersonaCreate):
    try:
        return agent.persona_manager.add_persona(p.name, p.description, p.system_prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/personas/{persona_id}/activate")
async def activate_persona(persona_id: str):
    try:
        agent.persona_manager.set_active_persona(persona_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str):
    try:
        agent.persona_manager.delete_persona(persona_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 数据库查看器 API

class DBConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None # 数据库名称可选

@app.post("/api/db/test-connection")
async def test_db_connection(config: DBConfig):
    from core.tools import query_mysql
    try:
        # 使用简单查询测试连接
        sql = "SELECT 1"
        res = query_mysql(sql, config.host, config.user, config.password, None, config.port)
        if res.startswith("Error"):
            raise HTTPException(status_code=400, detail=res)
        return {"status": "success", "message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/databases")
async def list_databases(config: DBConfig):
    from core.tools import query_mysql
    try:
        sql = "SHOW DATABASES"
        # 连接时不指定数据库以列出所有数据库
        res = query_mysql(sql, config.host, config.user, config.password, None, config.port)
        if res.startswith("Error"):
             raise HTTPException(status_code=400, detail=res)
        return json.loads(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/tables")
async def list_db_tables(config: DBConfig):
    from core.tools import query_mysql
    try:
        if not config.database:
             raise HTTPException(status_code=400, detail="Database name required to list tables")
        
        # 查询以列出表
        sql = "SHOW TABLES"
        res = query_mysql(sql, config.host, config.user, config.password, config.database, config.port)
        if res.startswith("Error"):
             raise HTTPException(status_code=400, detail=res)
        return json.loads(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/query")
async def query_db(config: DBConfig, query: str = Form(...)):
    # 注意：复用 query_mysql 工具逻辑，但暴露给 UI 使用
    # 等等，FastAPI 表单参数配合 Pydantic 模型体比较棘手。
    # 让我们使用单个 Pydantic 模型作为请求体
    pass

class DBQueryRequest(BaseModel):
    config: DBConfig
    query: str

@app.post("/api/db/execute")
async def execute_db_query(req: DBQueryRequest):
    from core.tools import query_mysql
    try:
        res = query_mysql(req.query, req.config.host, req.config.user, req.config.password, req.config.database, req.config.port)
        if res.startswith("Error"):
             raise HTTPException(status_code=400, detail=res)
        return json.loads(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    success = agent.session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
