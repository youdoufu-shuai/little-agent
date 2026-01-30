import os
import json
import sqlite3
import pymysql
from typing import Optional

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
