import os
import base64
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the Agent
from core.agent import PersonalAgent

# Load environment variables
load_dotenv()

app = FastAPI()

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

class ChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Construct message for Agent (mimicking Plato format)
        message = {
            "chat_id": "web-user",
            "text": request.text,
            "image": None
        }
        
        result = agent.process_message(message, session_id=request.session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vision")
async def vision_endpoint(text: str = Form(...), session_id: Optional[str] = Form(None), file: UploadFile = File(...)):
    try:
        # Read and encode image
        contents = await file.read()
        encoded = base64.b64encode(contents).decode('utf-8')
        data_uri = f"data:{file.content_type};base64,{encoded}"
        
        # Construct message
        message = {
            "chat_id": "web-user",
            "text": text,
            "image": data_uri
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

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    success = agent.session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
