from .file_ops import read_file, write_file, list_directory, search_files
from .db_ops import query_sqlite, query_mysql
from .web_ops import search_web, read_url, get_weather
from .media_ops import generate_image, analyze_image, generate_document, generate_mindmap
from .memory_ops import add_memo, read_memos, delete_memo
from .python_ops import run_python

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
                    },
                    "size": {
                        "type": "string",
                        "description": "图像尺寸，例如 '1024x1024' 或 '16:9'。"
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
