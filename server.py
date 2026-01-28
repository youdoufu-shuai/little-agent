import os
import base64
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the Agent
from core.agent import PersonalAgent

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
agent = PersonalAgent()

# Serve static files
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

class ChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    db_config: Optional[Dict[str, Any]] = None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Construct message for Agent (mimicking Plato format)
        message = {
            "chat_id": "web-user",
            "text": request.text,
            "image": None,
            "db_config": request.db_config
        }
        
        result = agent.process_message(message, session_id=request.session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vision")
async def vision_endpoint(text: str = Form(...), session_id: Optional[str] = Form(None), db_config: Optional[str] = Form(None), file: UploadFile = File(...)):
    try:
        # Read and encode image
        contents = await file.read()
        encoded = base64.b64encode(contents).decode('utf-8')
        data_uri = f"data:{file.content_type};base64,{encoded}"
        
        # Parse db_config if present
        parsed_config = None
        if db_config:
            try:
                parsed_config = json.loads(db_config)
            except:
                pass

        # Construct message
        message = {
            "chat_id": "web-user",
            "text": text,
            "image": data_uri,
            "db_config": parsed_config
        }
        
        result = agent.process_message(message, session_id=session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# History / Session Management API

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

# Personas Management API

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

# Database Viewer API

class DBConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None # Make database optional

@app.post("/api/db/databases")
async def list_databases(config: DBConfig):
    from core.tools import query_mysql
    try:
        sql = "SHOW DATABASES"
        # Connect without specific DB to list databases
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
        
        # Query to list tables
        sql = "SHOW TABLES"
        res = query_mysql(sql, config.host, config.user, config.password, config.database, config.port)
        if res.startswith("Error"):
             raise HTTPException(status_code=400, detail=res)
        return json.loads(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/query")
async def query_db(config: DBConfig, query: str = Form(...)):
    # Note: reusing query_mysql tool logic but exposed for UI
    # Wait, FastAPI form param with Pydantic model body is tricky.
    # Let's use a single Pydantic model for request body
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
