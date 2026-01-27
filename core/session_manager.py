import os
import json
import time
import uuid
from typing import List, Dict, Optional

class SessionManager:
    def __init__(self, storage_dir: str = "data/sessions"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_file_path(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def create_session(self, title: str = "New Chat") -> Dict:
        session_id = str(uuid.uuid4())
        now = time.time()
        session = {
            "id": session_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": []
        }
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        file_path = self._get_file_path(session_id)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def list_sessions(self) -> List[Dict]:
        sessions = []
        if not os.path.exists(self.storage_dir):
            return []
            
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                session = self.get_session(session_id)
                if session:
                    # Return only metadata for listing
                    sessions.append({
                        "id": session["id"],
                        "title": session.get("title", "New Chat"),
                        "created_at": session.get("created_at", 0),
                        "updated_at": session.get("updated_at", 0)
                    })
        # Sort by updated_at desc
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

    def add_message(self, session_id: str, role: str, content: str, **kwargs) -> Optional[Dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        # Add any additional fields (e.g. tool_calls, tool_call_id)
        message.update(kwargs)
        
        session["messages"].append(message)
        session["updated_at"] = time.time()
        
        # Auto-update title if it's the first user message and title is default
        if len(session["messages"]) == 1 and role == "user":
            # Simple title generation: first 20 chars
            session["title"] = content[:20] + "..." if len(content) > 20 else content
            
        self._save_session(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def _save_session(self, session: Dict):
        file_path = self._get_file_path(session["id"])
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
