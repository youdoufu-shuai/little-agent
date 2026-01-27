from openai import OpenAI
from config import Config

class VisionClient:
    def __init__(self):
        # Updated to use VISION_ config variables
        if Config.VISION_API_KEY:
            # Use OpenAI client for Gemini via the compatible API endpoint
            self.client = OpenAI(
                api_key=Config.VISION_API_KEY,
                base_url=Config.VISION_BASE_URL
            )
            self.model = Config.VISION_MODEL
        else:
            self.client = None
            self.model = None

    def analyze_image(self, image_input, prompt="请详细描述这张图片的内容"):
        """
        Analyze an image using Gemini Pro Vision (via OpenAI compatible API).
        
        :param image_input: URL of the image or base64 string
        :param prompt: Prompt for analysis
        :return: Text description
        """
        if not self.client:
            return "视觉功能未配置 (缺少 VISION_API_KEY)。"
            
        try:
            # Construct message with image for OpenAI Vision API format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_input
                            }
                        }
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"Error analyzing image: {e}"
