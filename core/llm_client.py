from openai import OpenAI
from config import Config

class LLMClient:
    def __init__(self):
        # Updated to use LOGIC_ config variables
        if Config.LOGIC_API_KEY:
            self.client = OpenAI(
                api_key=Config.LOGIC_API_KEY,
                base_url=Config.LOGIC_BASE_URL
            )
            self.model = Config.LOGIC_MODEL
        else:
            self.client = None
            self.model = None

    def chat(self, messages, tools=None):
        """
        Send a chat completion request to the Logic Model (Gemini Flash Thinking).
        
        :param messages: List of message dicts (role, content)
        :param tools: Optional list of tool definitions
        :return: Response object or content string
        """
        if not self.client:
            print("Error: Logic client not initialized.")
            return None

        try:
            params = {
                "model": self.model,
                "messages": messages,
            }
            # Note: Gemini models via OpenAI compat layer might have different tool support
            # For now we keep it, but be aware 'thinking' models might not support tools in all versions
            if tools:
                params["tools"] = tools
                
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message
        except Exception as e:
            print(f"Error calling Logic API: {e}")
            return None
