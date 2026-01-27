import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    # Plato API
    PLATO_API_KEY = os.getenv("PLATO_API_KEY")
    PLATO_BASE_URL = os.getenv("PLATO_BASE_URL", "https://api.plato.com/v1")
    
    # Logic Brain (Gemini 3 Flash Thinking)
    LOGIC_API_KEY = os.getenv("LOGIC_API_KEY")
    LOGIC_BASE_URL = os.getenv("LOGIC_BASE_URL", "https://api.bltcy.ai/v1")
    LOGIC_MODEL = os.getenv("LOGIC_MODEL", "gemini-3-flash-preview-thinking-*")
    
    # Vision Brain (Gemini)
    VISION_API_KEY = os.getenv("VISION_API_KEY")
    VISION_BASE_URL = os.getenv("VISION_BASE_URL", "https://api.bltcy.ai/v1")
    VISION_MODEL = os.getenv("VISION_MODEL", "gemini-3-pro-preview")

    # Agent Settings
    AGENT_NAME = "Personal Assistant"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @staticmethod
    def validate():
        missing = []
        if not Config.LOGIC_API_KEY:
            missing.append("LOGIC_API_KEY")
        if not Config.VISION_API_KEY:
            missing.append("VISION_API_KEY")
        # Plato key might be optional for local testing
            
        if missing:
            print(f"Warning: Missing configuration for: {', '.join(missing)}")
