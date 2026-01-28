import os
import sqlite3
import pymysql
import json
import requests
from openai import OpenAI
from config import Config
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

def read_file(file_path: str) -> str:
    """
    Reads the content of a local file.
    
    Args:
        file_path: Absolute path to the file.
        
    Returns:
        The content of the file as a string.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_directory(dir_path: str) -> str:
    """
    Lists files and directories in a given path.
    
    Args:
        dir_path: Absolute path to the directory.
        
    Returns:
        A list of file names/directories.
    """
    try:
        if not os.path.exists(dir_path):
            return f"Error: Directory '{dir_path}' does not exist."
            
        items = os.listdir(dir_path)
        return json.dumps(items, ensure_ascii=False)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def query_sqlite(db_path: str, query: str) -> str:
    """
    Executes a SQL query on a local SQLite database.
    
    Args:
        db_path: Absolute path to the SQLite database file.
        query: The SQL query to execute.
        
    Returns:
        Query results as a JSON string.
    """
    try:
        if not os.path.exists(db_path):
            return f"Error: Database file '{db_path}' does not exist."
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch columns and rows
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
            
        conn.close()
        return json.dumps(results, ensure_ascii=False, default=str)
    except Exception as e:
        return f"Error executing query: {str(e)}"

def query_mysql(query: str, host: str, user: str, password: str, database: Optional[str] = None, port: int = 3306) -> str:
    """
    Executes a SQL query on a MySQL database.
    
    Args:
        query: The SQL query to execute.
        host: Database host.
        user: Database user.
        password: Database password.
        database: Database name. Optional if query doesn't require selected DB (e.g. SHOW DATABASES).
        port: Database port (default 3306).
        
    Returns:
        Query results as a JSON string.
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
                
                # Check if it's a read query
                query_stripped = query.strip().upper()
                if query_stripped.startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                    result = cursor.fetchall()
                    return json.dumps(result, ensure_ascii=False, default=str)
                else:
                    connection.commit()
                    return json.dumps({
                        "status": "success", 
                        "rows_affected": affected_rows,
                        "message": "Query executed successfully."
                    }, ensure_ascii=False)
    except Exception as e:
        return f"Error executing MySQL query: {str(e)}"

def generate_image(prompt: str, filename: str) -> str:
    """
    Generates an image based on a prompt using the configured API, 
    saving it to web/images/. Falls back to local placeholder if API fails.
    
    Args:
        prompt: The text description or content for the image.
        filename: The filename to save (e.g., "image.png").
        
    Returns:
        The URL path to the generated image or error message.
    """
    output_dir = os.path.join(os.getcwd(), "web", "images")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    
    # 1. Try to generate using the API (Real Image Generation)
    try:
        # Use LOGIC_API_KEY as default for generation capabilities
        api_key = Config.LOGIC_API_KEY or Config.VISION_API_KEY
        base_url = Config.LOGIC_BASE_URL
        
        if api_key:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # Use dall-e-3 if available, or fall back to dall-e-2 or model specific logic
            # For bltcy.ai (Gemini wrapper), we might need to be specific, but standard OpenAI client usually works
            # with standard model names if mapped correctly by provider.
            response = client.images.generate(
                model="gemini-3-pro-image-preview", # Use user specified model
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            if response.data and response.data[0].url:
                image_url = response.data[0].url
                
                # Download the image
                img_data = requests.get(image_url).content
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                    
                return f"/static/images/{filename}"
                
    except Exception as e:
        print(f"API Image Generation failed: {e}")
        # Proceed to fallback...

    try:
        # 2. Fallback: Create a simple placeholder image (Local)
        print("Falling back to local placeholder generation...")
        
        width, height = 512, 512
        # Generate a background color based on prompt length (pseudo-random)
        r = (len(prompt) * 15) % 255
        g = (len(prompt) * 35) % 255
        b = (len(prompt) * 55) % 255
        color = (r, g, b)
        
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        
        # Text wrapping and drawing
        # Try to load a font
        try:
             # Try common font locations on macOS
             font_path = "/System/Library/Fonts/Helvetica.ttc"
             if not os.path.exists(font_path):
                 font = ImageFont.load_default()
             else:
                 font = ImageFont.truetype(font_path, 40)
        except:
             font = ImageFont.load_default()
             
        # Simple text drawing (centered-ish)
        text = prompt
        # If text is too long, truncate for the demo
        if len(text) > 50:
            text = text[:47] + "..."
            
        d.text((50, 200), text, fill=(255, 255, 255), font=font)
        d.text((50, 250), "(AI Generated - Placeholder)", fill=(200, 200, 200), font=font)
        d.text((50, 300), "(API Failed)", fill=(200, 200, 200), font=font)
        
        # Save file
        img.save(filepath)
        
        # Return the relative path for web access
        return f"/static/images/{filename}"
        
    except Exception as e:
        return f"Error generating image: {str(e)}"

# Tool Definitions for LLM
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a local file. Use this when you need to access information stored in a text-based file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The absolute path to the file to read."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories in a given path. Use this to explore the file system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "The absolute path to the directory."
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
            "description": "Execute a SQL query on a local SQLite database. Use this to retrieve data from a database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {
                        "type": "string",
                        "description": "The absolute path to the SQLite database file."
                    },
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute."
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
            "description": "Execute a SQL query on a MySQL database. Requires connection details provided in the context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute."
                    },
                    "host": {
                        "type": "string",
                        "description": "Database host."
                    },
                    "user": {
                        "type": "string",
                        "description": "Database user."
                    },
                    "password": {
                        "type": "string",
                        "description": "Database password."
                    },
                    "database": {
                        "type": "string",
                        "description": "Database name."
                    },
                    "port": {
                        "type": "integer",
                        "description": "Database port (default 3306)."
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
            "description": "Generate an image based on a text prompt. Use this when the user asks to draw or generate an image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The description of the image to generate."
                    },
                    "filename": {
                        "type": "string",
                        "description": "The filename to save the image as (e.g., 'creation.png')."
                    }
                },
                "required": ["prompt", "filename"]
            }
        }
    }
]

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "list_directory": list_directory,
    "query_sqlite": query_sqlite,
    "query_mysql": query_mysql,
    "generate_image": generate_image
}
