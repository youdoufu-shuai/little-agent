import os
import json
import fnmatch

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
