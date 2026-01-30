import os
import json
from datetime import datetime
from typing import List, Dict

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
