import os
import re
import requests
import json
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from config import Config

def generate_image(prompt: str, filename: str, size: str = "1024x1024") -> str:
    """
    基于提示词生成图像，使用配置的 API，保存到 web/images/ai_generated/。
    如果 API 失败，则回退到本地占位符。
    
    Args:
        prompt: 图像的文本描述或内容。
        filename: 保存的文件名 (例如 "image.png")。
        size: 图像尺寸，例如 "1024x1024" 或 "16:9"。
        
    Returns:
        生成的图像的 URL 路径及 Markdown 预览。
    """
    # 修改：将 AI 生成图片保存到 ai_generated 子目录
    base_dir = os.path.join(os.getcwd(), "web", "images")
    output_dir = os.path.join(base_dir, "ai_generated")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    web_path = f"/static/images/ai_generated/{filename}"
    
    # 解析尺寸
    width, height = 1024, 1024
    if size == "16:9":
        width, height = 1280, 720
    elif "x" in size:
        try:
            parts = size.split("x")
            width = int(parts[0])
            height = int(parts[1])
        except:
            pass
    
    # 1. 尝试使用 API 生成 (真实图像生成)
    try:
        # 使用 LOGIC_API_KEY 作为生成功能的默认值
        api_key = Config.LOGIC_API_KEY or Config.VISION_API_KEY
        base_url = Config.LOGIC_BASE_URL
        
        if api_key:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # 使用 chat completion 调用 gemini-3-pro-image-preview
            # 注意：如果模型支持尺寸参数，应在此处传递。
            # 目前只能通过 prompt 暗示。
            enhanced_prompt = f"{prompt} --aspect {width}:{height}"
            
            response = client.chat.completions.create(
                model="gemini-3-pro-image-preview",
                messages=[
                    {"role": "user", "content": enhanced_prompt}
                ]
            )
            
            content = response.choices[0].message.content
            # 提取 markdown 图像链接: ![alt](url)
            match = re.search(r'!\[.*?\]\((.*?)\)', content)
            
            if match:
                image_url = match.group(1)
                
                # 下载图像
                print(f"正在从以下地址下载图像: {image_url}")
                img_response = requests.get(image_url, timeout=30)
                
                if img_response.status_code == 200:
                    img_data = img_response.content
                    with open(filepath, 'wb') as f:
                        f.write(img_data)
                        
                    return f"图像生成成功。预览：\n![{prompt}]({web_path})"
                else:
                    raise Exception(f"下载图像失败。状态码: {img_response.status_code}")
            else:
                 # 如果没有 Markdown 链接，但有内容，可能生成失败或格式不同
                 pass
                 # raise Exception("响应中未找到图像 URL")
                
    except Exception as e:
        print(f"API 图像生成失败: {e}")
        # import traceback
        # traceback.print_exc()
        # 继续执行回退方案...

    try:
        # 2. 回退方案: 创建简单的占位符图像 (本地)
        print("正在回退到本地占位符生成...")
        
        # 根据提示词长度生成背景颜色 (伪随机)
        r = (len(prompt) * 15) % 255
        g = (len(prompt) * 35) % 255
        b = (len(prompt) * 55) % 255
        color = (r, g, b)
        
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        
        # 文本换行和绘制
        # 尝试加载字体
        try:
             # 尝试 macOS 上的常用字体位置
             font_path = "/System/Library/Fonts/Helvetica.ttc"
             if not os.path.exists(font_path):
                 font = ImageFont.load_default()
             else:
                 font = ImageFont.truetype(font_path, 40)
        except:
             font = ImageFont.load_default()
             
        # 简单的文本绘制 (大致居中)
        text = "AI IMAGE\n" + prompt[:20] + "..."
        d.text((50, height // 2), text, fill=(255, 255, 255), font=font)
        
        img.save(filepath)
        return f"本地图像生成成功（回退模式）。预览：\n![{prompt}]({web_path})"
        
    except Exception as e:
        return f"图像生成完全失败: {str(e)}"

def analyze_image(image_url: str) -> str:
    """
    Analyzes the content of an image from a URL using a vision model.
    
    Args:
        image_url: The URL of the image to analyze.
        
    Returns:
        A description of the image content.
    """
    try:
        # Import locally to avoid circular dependencies
        from core.vision_client import VisionClient
        client = VisionClient()
        return client.analyze_image(image_input=image_url)
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def generate_document(filename: str, file_type: str, content: str, style_config: Optional[str] = None) -> str:
    """
    Generates a Word (.docx) or PDF (.pdf) document with mixed text and images.
    
    Args:
        filename: Name of the file to save (e.g., 'report'). Extension will be added if missing.
        file_type: 'docx' or 'pdf'.
        content: JSON string representing a list of content blocks.
                 Each block: {"type": "heading|paragraph|image|page_break", "text": "...", "level": 1, "path": "...", "style": {...}}
        style_config: Optional JSON string for global style settings.
        
    Returns:
        The URL path to the generated file.
    """
    try:
        from core.doc_generator import DocumentGenerator
        
        # Parse JSON content
        content_list = json.loads(content)
        style_dict = json.loads(style_config) if style_config else None
        
        path = DocumentGenerator.generate(filename, file_type, content_list, style_dict)
        
        # Convert absolute path to relative URL for frontend access
        # DocumentGenerator saves to web/files/documents
        basename = os.path.basename(path)
        url_path = f"/static/files/documents/{basename}"
        
        return f"Document generated. Download link: [{basename}]({url_path})"
    except Exception as e:
        return f"Error generating document: {str(e)}"

def generate_mindmap(filename: str, content: str) -> str:
    """
    Generates an HTML mindmap file using Mermaid.js.
    
    Args:
        filename: The filename (e.g., 'idea_map').
        content: The Mermaid syntax content.
        
    Returns:
        The URL path to the generated file.
    """
    try:
        from core.mindmap_generator import MindmapGenerator
        path = MindmapGenerator.generate(filename, content)
        return f"思维导图已生成。请点击链接查看: [查看思维导图]({path})"
    except Exception as e:
        return f"Error generating mindmap: {str(e)}"
