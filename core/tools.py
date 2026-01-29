import os
import sqlite3
import pymysql
import json
import requests
import re
import time
import subprocess
import sys
from datetime import datetime
from openai import OpenAI
from config import Config
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def read_file(file_path: str) -> str:
    """
    读取本地文件的内容。
    
    Args:
        file_path: 文件的绝对路径。
        
    Returns:
        文件的内容字符串。
    """
    try:
        if not os.path.exists(file_path):
            return f"错误: 文件 '{file_path}' 不存在。"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件出错: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    """
    将内容写入本地文件。如果目录不存在，则创建目录。
    
    Args:
        file_path: 文件的绝对路径。
        content: 要写入的内容。
        
    Returns:
        确认信息。
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"成功写入文件: {file_path}"
    except Exception as e:
        return f"写入文件出错: {str(e)}"

def list_directory(dir_path: str) -> str:
    """
    列出给定路径下的文件和目录。
    
    Args:
        dir_path: 目录的绝对路径。
        
    Returns:
        文件/目录名称的列表。
    """
    try:
        if not os.path.exists(dir_path):
            return f"错误: 目录 '{dir_path}' 不存在。"
            
        items = os.listdir(dir_path)
        return json.dumps(items, ensure_ascii=False)
    except Exception as e:
        return f"列出目录出错: {str(e)}"

def search_files(root_dir: str, pattern: str, max_results: int = 20) -> str:
    """
    在指定目录中递归搜索文件。
    
    Args:
        root_dir: 搜索的根目录绝对路径。
        pattern: 文件名搜索模式（不区分大小写，支持部分匹配）。
        max_results: 返回的最大结果数（默认为 20）。
        
    Returns:
        匹配的文件绝对路径列表。
    """
    try:
        import fnmatch
        
        if not os.path.exists(root_dir):
            return f"错误: 目录 '{root_dir}' 不存在。"
            
        results = []
        count = 0
        
        # 遍历目录
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 过滤隐藏目录
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            
            for filename in filenames:
                # 检查文件名是否匹配
                # 支持简单的子字符串匹配或 glob 模式
                if pattern.lower() in filename.lower() or fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    full_path = os.path.join(dirpath, filename)
                    results.append(full_path)
                    count += 1
                    
                    if count >= max_results:
                        break
            
            if count >= max_results:
                break
                
        if not results:
            return f"在 '{root_dir}' 中未找到包含 '{pattern}' 的文件。"
            
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"搜索文件出错: {str(e)}"

def query_sqlite(db_path: str, query: str) -> str:
    """
    在本地 SQLite 数据库上执行 SQL 查询。
    
    Args:
        db_path: SQLite 数据库文件的绝对路径。
        query: 要执行的 SQL 查询。
        
    Returns:
        查询结果的 JSON 字符串。
    """
    try:
        if not os.path.exists(db_path):
            return f"错误: 数据库文件 '{db_path}' 不存在。"
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # 获取列名和行数据
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
            
        conn.close()
        return json.dumps(results, ensure_ascii=False, default=str)
    except Exception as e:
        return f"执行查询出错: {str(e)}"

def query_mysql(query: str, host: str, user: str, password: str, database: Optional[str] = None, port: int = 3306) -> str:
    """
    在 MySQL 数据库上执行 SQL 查询。
    
    Args:
        query: 要执行的 SQL 查询。
        host: 数据库主机。
        user: 数据库用户。
        password: 数据库密码。
        database: 数据库名称。如果查询不需要选定数据库（例如 SHOW DATABASES），则可选。
        port: 数据库端口（默认为 3306）。
        
    Returns:
        查询结果的 JSON 字符串。
    """
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection:
            with connection.cursor() as cursor:
                affected_rows = cursor.execute(query)
                
                # 检查是否为读取查询
                query_stripped = query.strip().upper()
                if query_stripped.startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                    result = cursor.fetchall()
                    return json.dumps(result, ensure_ascii=False, default=str)
                else:
                    connection.commit()
                    return json.dumps({
                        "status": "success", 
                        "rows_affected": affected_rows,
                        "message": "查询执行成功。"
                    }, ensure_ascii=False)
    except Exception as e:
        return f"执行 MySQL 查询出错: {str(e)}"

def generate_image(prompt: str, filename: str) -> str:
    """
    基于提示词生成图像，使用配置的 API，保存到 web/images/ai_generated/。
    如果 API 失败，则回退到本地占位符。
    
    Args:
        prompt: 图像的文本描述或内容。
        filename: 保存的文件名 (例如 "image.png")。
        
    Returns:
        生成的图像的 URL 路径或错误信息。
    """
    # 修改：将 AI 生成图片保存到 ai_generated 子目录
    base_dir = os.path.join(os.getcwd(), "web", "images")
    output_dir = os.path.join(base_dir, "ai_generated")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
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
            response = client.chat.completions.create(
                model="gemini-3-pro-image-preview",
                messages=[
                    {"role": "user", "content": prompt}
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
                        
                    return f"/static/images/ai_generated/{filename}"
                else:
                    raise Exception(f"下载图像失败。状态码: {img_response.status_code}")
            else:
                 raise Exception("响应中未找到图像 URL")
                
    except Exception as e:
        print(f"API 图像生成失败: {e}")
        import traceback
        traceback.print_exc()
        # 继续执行回退方案...

    try:
        # 2. 回退方案: 创建简单的占位符图像 (本地)
        print("正在回退到本地占位符生成...")
        
        width, height = 512, 512
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
        d.text((50, 200), text, fill=(255, 255, 255), font=font)
        
        img.save(filepath)
        return f"/static/images/ai_generated/{filename}"
        
    except Exception as e:
        return f"图像生成完全失败: {str(e)}"

def search_web(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo 搜索网络。
    
    Args:
        query: 搜索查询。
        max_results: 返回的最大结果数（默认为 5）。
        
    Returns:
        搜索结果的 JSON 字符串。
    """
    try:
        results = []
        with DDGS() as ddgs:
            # text() 方法返回一个迭代器
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"搜索网络出错: {str(e)}"

def read_url(url: str) -> str:
    """
    获取并读取网页的主要文本内容，包括图像链接。
    
    Args:
        url: 要读取的网页 URL。
        
    Returns:
        提取的网页文本内容和图像链接。
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 清理前提取图像
        image_list = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            # 处理相对 URL
            if src.startswith('//'):
                src = 'https:' + src
            elif not src.startswith(('http://', 'https://')):
                src = urljoin(url, src)
            
            alt = img.get('alt', 'Image')
            img_md = f"![{alt}]({src})"
            if img_md not in image_list:
                image_list.append(img_md)

        # 移除脚本和样式元素
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # 获取文本
        text = soup.get_text()
        
        # 分行并去除每行的首尾空格
        lines = (line.strip() for line in text.splitlines())
        # 将多标题行分解为单行
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # 丢弃空行
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 限制文本长度以避免上下文溢出（约 10k 字符）
        if len(text) > 10000:
            text = text[:10000] + "\n...(内容已截断)..."
            
        # 追加找到的图像
        if image_list:
            text += "\n\n[找到的图像 (前 20 个)]:\n" + "\n".join(image_list[:20])

        return text
    except Exception as e:
        return f"读取 URL 出错: {str(e)}"

# 内存管理 (Memos)
MEMOS_FILE = os.path.join(os.getcwd(), "data", "memos.json")

def _load_memos() -> List[Dict]:
    if not os.path.exists(MEMOS_FILE):
        return []
    try:
        with open(MEMOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def _save_memos(memos: List[Dict]):
    # 确保目录存在
    os.makedirs(os.path.dirname(MEMOS_FILE), exist_ok=True)
    with open(MEMOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)

def add_memo(content: str) -> str:
    """
    向 Agent 的记忆中添加新备忘录。
    
    Args:
        content: 备忘录的内容。
        
    Returns:
        确认信息。
    """
    try:
        memos = _load_memos()
        new_id = 1
        if memos:
            new_id = max(m.get("id", 0) for m in memos) + 1
            
        new_memo = {
            "id": new_id,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        memos.append(new_memo)
        _save_memos(memos)
        return f"已添加备忘录，ID: {new_id}"
    except Exception as e:
        return f"添加备忘录出错: {str(e)}"

def read_memos() -> str:
    """
    读取所有保存的备忘录。
    
    Returns:
        包含所有备忘录的 JSON 字符串。
    """
    try:
        memos = _load_memos()
        if not memos:
            return "未找到备忘录。"
        return json.dumps(memos, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"读取备忘录出错: {str(e)}"

def delete_memo(memo_id: int) -> str:
    """
    根据 ID 删除备忘录。
    
    Args:
        memo_id: 要删除的备忘录的 ID。
        
    Returns:
        确认信息。
    """
    try:
        memos = _load_memos()
        initial_count = len(memos)
        memos = [m for m in memos if m.get("id") != memo_id]
        
        if len(memos) == initial_count:
            return f"未找到 ID 为 {memo_id} 的备忘录。"
            
        _save_memos(memos)
        return f"已删除备忘录 {memo_id}。"
    except Exception as e:
        return f"删除备忘录出错: {str(e)}"

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

def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息。
    
    Args:
        city: 城市名称（例如 "Shanghai" 或 "Beijing"）。
        
    Returns:
        包含天气信息的字符串。
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "错误: 未配置 OPENWEATHER_API_KEY 环境变量。"
        
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "zh_cn"
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            return f"{city} 天气: {weather}, 温度: {temp}°C, 湿度: {humidity}%"
        else:
            return f"获取天气失败: {data.get('message', '未知错误')}"
    except Exception as e:
        return f"请求天气 API 出错: {str(e)}"

def run_python(code: str) -> str:
    """
    在单独的进程中执行 Python 代码。
    
    Args:
        code: 要执行的 Python 代码。
        
    Returns:
        执行的输出 (stdout + stderr)。
    """
    try:
        # 创建临时文件
        temp_file = os.path.join(os.getcwd(), "temp_script.py")
        
        # 将代码写入文件
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        # 带超时运行脚本
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=10  # 10 秒超时
        )
        
        # 清理
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        output = result.stdout
        if result.stderr:
            output += f"\n[标准错误]:\n{result.stderr}"
            
        return output
    except subprocess.TimeoutExpired:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return "错误: 执行超时 (限制: 10秒)。"
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return f"执行 Python 代码出错: {str(e)}"

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

# LLM 的工具定义
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文件的内容。当你需要访问存储在基于文本的文件中的信息时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件的绝对路径。"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_mindmap",
            "description": "生成交互式思维导图 (HTML)。返回文件 URL。生成的 HTML 文件包含 Mermaid 图表。用户可以直接在界面上查看。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "保存的文件名（不带扩展名）。"
                    },
                    "content": {
                        "type": "string",
                        "description": "Mermaid 思维导图语法内容 (例如 'mindmap\\n root((Root))\\n Child')."
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入本地文件。当你需要保存代码、文本或创建新文件时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要写入的文件的绝对路径。"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的内容。"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出给定路径下的文件和目录。使用此工具来探索文件系统。",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "目录的绝对路径。"
                    }
                },
                "required": ["dir_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_sqlite",
            "description": "在本地 SQLite 数据库上执行 SQL 查询。使用此工具从数据库检索数据。",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {
                        "type": "string",
                        "description": "SQLite 数据库文件的绝对路径。"
                    },
                    "query": {
                        "type": "string",
                        "description": "要执行的 SQL 查询。"
                    }
                },
                "required": ["db_path", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_mysql",
            "description": "在 MySQL 数据库上执行 SQL 查询。需要上下文中提供的连接详细信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要执行的 SQL 查询。"
                    },
                    "host": {
                        "type": "string",
                        "description": "数据库主机。"
                    },
                    "user": {
                        "type": "string",
                        "description": "数据库用户。"
                    },
                    "password": {
                        "type": "string",
                        "description": "数据库密码。"
                    },
                    "database": {
                        "type": "string",
                        "description": "数据库名称。"
                    },
                    "port": {
                        "type": "integer",
                        "description": "数据库端口（默认 3306）。"
                    }
                },
                "required": ["query", "host", "user", "password"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "根据文本提示生成图像。当用户要求绘制或生成图像时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "要生成的图像的描述。"
                    },
                    "filename": {
                        "type": "string",
                        "description": "保存图像的文件名（例如 'creation.png'）。"
                    }
                },
                "required": ["prompt", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "使用 DuckDuckGo 搜索网络信息。当你需要查找实时信息、新闻或知识库中没有的事实的时候使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询。"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回的最大结果数（默认为 5）。"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": "读取网页的完整内容，包括文本和图像链接。当你需要阅读文章或分析网页时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要读取的网页 URL。"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_image",
            "description": "分析 URL 中的图像以了解其内容。当你找到图像 URL 并想知道其中包含什么时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "要分析的图像 URL。"
                    }
                },
                "required": ["image_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_document",
            "description": "生成富文本文档 (PDF 或 DOCX)。支持标题、段落和图片。对于图片，可以使用本地路径（绝对路径）或网络 URL。注意：如果需要插入图片，请先使用 generate_image 工具生成或 search_web/read_url 工具获取，然后将路径/URL 传入 content 列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "要保存的文件名（例如 'report'）。"
                    },
                    "file_type": {
                        "type": "string",
                        "enum": ["docx", "pdf"],
                        "description": "要生成的文件类型。"
                    },
                    "content": {
                        "type": "string",
                        "description": "表示内容块列表的 JSON 字符串。示例：'[{\"type\": \"heading\", \"text\": \"Title\", \"level\": 1}, {\"type\": \"paragraph\", \"text\": \"Content...\"}, {\"type\": \"image\", \"path\": \"/abs/path/to/img.png\", \"width\": 400}]'"
                    },
                    "style_config": {
                        "type": "string",
                        "description": "用于全局样式设置的可选 JSON 字符串。"
                    }
                },
                "required": ["filename", "file_type", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_memo",
            "description": "向 Agent 的长期记忆中添加新备忘录。当用户要求你记住某事时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要保存的备忘录内容。"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_memos",
            "description": "读取 Agent 记忆中保存的所有备忘录。当用户询问你记得什么或询问保存的信息时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_memo",
            "description": "按 ID 删除备忘录。当用户要求忘记某事或删除特定笔记时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "memo_id": {
                        "type": "integer",
                        "description": "要删除的备忘录 ID。"
                    }
                },
                "required": ["memo_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息。使用此工具获取当前天气。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称（例如 'Shanghai' 或 'Beijing'）。"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "执行 Python 代码以执行计算、数据处理或简单任务。代码在临时环境中运行。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 Python 代码。"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory,
    "search_files": search_files,
    "query_sqlite": query_sqlite,
    "query_mysql": query_mysql,
    "generate_image": generate_image,
    "search_web": search_web,
    "read_url": read_url,
    "add_memo": add_memo,
    "read_memos": read_memos,
    "delete_memo": delete_memo,
    "get_weather": get_weather,
    "run_python": run_python,
    "analyze_image": analyze_image,
    "generate_document": generate_document,
    "generate_mindmap": generate_mindmap
}
