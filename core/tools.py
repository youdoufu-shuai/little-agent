import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

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
        
        # Simple security check to prevent reading outside of allowed areas if needed
        # For a personal agent, we might allow full access or restrict to home/project
        # defaulting to full access as requested.
        
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
    }
]

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "list_directory": list_directory,
    "query_sqlite": query_sqlite
}
