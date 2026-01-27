import requests
from config import Config

class PlatoClient:
    def __init__(self):
        self.api_key = Config.PLATO_API_KEY
        self.base_url = Config.PLATO_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_updates(self):
        """
        Poll for new messages from Plato.
        This is a placeholder implementation.
        """
        # try:
        #     response = requests.get(f"{self.base_url}/updates", headers=self.headers)
        #     if response.status_code == 200:
        #         return response.json().get("messages", [])
        # except Exception as e:
        #     print(f"Error getting updates from Plato: {e}")
        return []

    def send_message(self, chat_id, text):
        """
        Send a message back to Plato.
        """
        # try:
        #     payload = {"chat_id": chat_id, "text": text}
        #     requests.post(f"{self.base_url}/messages", json=payload, headers=self.headers)
        # except Exception as e:
        #     print(f"Error sending message to Plato: {e}")
        if Config.DEBUG:
            print(f"[Plato Mock] Sending to {chat_id}: {text}")
