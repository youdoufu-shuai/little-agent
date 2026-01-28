import json
import os
import uuid
from typing import List, Dict, Optional

class PersonaManager:
    def __init__(self, storage_file: str = "data/personas.json"):
        self.storage_file = storage_file
        self.storage_dir = os.path.dirname(storage_file)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize default if not exists
        if not os.path.exists(self.storage_file):
            self._save_personas([
                {
                    "id": "default",
                    "name": "默认助手",
                    "description": "标准智能助手",
                    "system_prompt": "你是一个智能个人助手。请始终使用中文回答用户的问题。利用你的视觉和逻辑能力为用户提供帮助。你可以读取本地文件、查询SQLite和MySQL数据库，以及生成图像。",
                    "is_active": True
                }
            ])

    def list_personas(self) -> List[Dict]:
        return self._load_personas()

    def get_persona(self, persona_id: str) -> Optional[Dict]:
        personas = self._load_personas()
        for p in personas:
            if p["id"] == persona_id:
                return p
        return None

    def get_active_persona(self) -> Optional[Dict]:
        personas = self._load_personas()
        for p in personas:
            if p.get("is_active"):
                return p
        return personas[0] if personas else None

    def add_persona(self, name: str, description: str, system_prompt: str) -> Dict:
        personas = self._load_personas()
        if len(personas) >= 5:
            raise ValueError("最多只能保存5个配置")
            
        new_persona = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "is_active": False
        }
        personas.append(new_persona)
        self._save_personas(personas)
        return new_persona

    def update_persona(self, persona_id: str, **kwargs) -> Optional[Dict]:
        personas = self._load_personas()
        for p in personas:
            if p["id"] == persona_id:
                if p["id"] == "default": # Prevent critical edits to default if needed, but allowing for now
                    pass
                p.update(kwargs)
                self._save_personas(personas)
                return p
        return None

    def delete_persona(self, persona_id: str) -> bool:
        if persona_id == "default":
            raise ValueError("不能删除默认配置")
            
        personas = self._load_personas()
        initial_len = len(personas)
        personas = [p for p in personas if p["id"] != persona_id]
        
        if len(personas) < initial_len:
            self._save_personas(personas)
            return True
        return False

    def set_active_persona(self, persona_id: str):
        personas = self._load_personas()
        found = False
        for p in personas:
            if p["id"] == persona_id:
                p["is_active"] = True
                found = True
            else:
                p["is_active"] = False
        
        if found:
            self._save_personas(personas)
        else:
            raise ValueError("Persona not found")

    def _load_personas(self) -> List[Dict]:
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_personas(self, personas: List[Dict]):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(personas, f, ensure_ascii=False, indent=2)
