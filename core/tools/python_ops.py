import os
import sys
import subprocess
import ast

def run_python(code: str) -> str:
    """
    在单独的进程中执行 Python 代码。
    包含基本的安全检查（禁止 subprocess 和部分 os 操作）。
    
    Args:
        code: 要执行的 Python 代码。
        
    Returns:
        执行的输出 (stdout + stderr)。
    """
    # 1. 静态安全检查
    try:
        tree = ast.parse(code)
        
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.violations = []

            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name == 'subprocess':
                        self.violations.append(f"Line {node.lineno}: 禁止导入 subprocess 模块 (请使用 RunCommand 工具执行系统命令)")
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module == 'subprocess':
                    self.violations.append(f"Line {node.lineno}: 禁止从 subprocess 导入 (请使用 RunCommand 工具执行系统命令)")
                self.generic_visit(node)

            def visit_Call(self, node):
                # 检查 os.system, os.popen 等
                if isinstance(node.func, ast.Attribute):
                    # 检查形式: os.xxx()
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                        dangerous = ['system', 'popen', 'spawn', 'execl', 'execle', 'execlp', 
                                   'execv', 'execve', 'execvp', 'execvpe', 'kill', 'fork']
                        if node.func.attr in dangerous:
                            self.violations.append(f"Line {node.lineno}: 禁止调用 os.{node.func.attr}")
                self.generic_visit(node)

        visitor = SecurityVisitor()
        visitor.visit(tree)
        
        if visitor.violations:
            return "代码安全检查未通过:\n" + "\n".join(visitor.violations)
            
    except SyntaxError as e:
        return f"代码语法错误: {e}"
    except Exception as e:
        return f"安全检查时发生错误: {e}"

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
