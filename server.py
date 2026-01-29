import os
import base64
import json
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

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

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 构建 Agent 消息（模仿 Plato 格式）
        message = {
            "chat_id": "web-user",
            "text": request.text,
            "image": None,
            "db_config": request.db_config,
            "file_config": request.file_config.dict() if request.file_config else None
        }
        
        result = agent.process_message(message, session_id=request.session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vision")
async def vision_endpoint(text: str = Form(...), session_id: Optional[str] = Form(None), db_config: Optional[str] = Form(None), file_config: Optional[str] = Form(None), file: UploadFile = File(...)):
    try:
        # 读取并编码图像
        contents = await file.read()
        encoded = base64.b64encode(contents).decode('utf-8')
        data_uri = f"data:{file.content_type};base64,{encoded}"
        
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

        # 构建消息
        message = {
            "chat_id": "web-user",
            "text": text,
            "image": data_uri,
            "db_config": parsed_db_config,
            "file_config": parsed_file_config
        }
        
        result = agent.process_message(message, session_id=session_id)
        return result
    except Exception as e:
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
