import os
import re
from typing import Optional

class MindmapGenerator:
    @staticmethod
    def _sanitize_content(content: str) -> str:
        """
        Sanitizes Mermaid content to avoid syntax errors.
        1. Strips markdown code blocks.
        2. Wraps text in quotes if it contains special characters but isn't a shape definition.
        """
        # 1. Strip Markdown code blocks
        content = re.sub(r'```mermaid\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        lines = content.split('\n')
        sanitized_lines = []
        
        # Regex to capture ID and Opener only
        # We will determine Closer based on Opener and strip it from the end
        start_regex = re.compile(r'^([^\[\(\{\)\s]+)([\[\(\{\)]+)')
        
        # Counter for auto-generated IDs to ensure unique nodes
        node_counter = 0
        
        for line in lines:
            if not line.strip():
                continue
                
            # Preserve indentation
            indent_match = re.match(r'^(\s*)', line)
            indent = indent_match.group(1) if indent_match else ""
            text = line.strip()
            
            # Replace '::' with ':' to avoid Mermaid class syntax conflict
            text = text.replace('::', ':')
            
            if text == 'mindmap':
                sanitized_lines.append(line)
                continue
                
            # Try to match shape definition start
            match = start_regex.match(text)
            is_valid_shape = False
            
            if match:
                node_id = match.group(1)
                opener = match.group(2)
                
                # Determine expected closer
                if opener == '((':
                    closer = '))'
                elif opener == '(':
                    closer = ')'
                elif opener == '[':
                    closer = ']'
                elif opener == '{':
                    closer = '}'
                elif opener == '{{':
                    closer = '}}'
                elif opener == ')':
                    closer = '('
                elif opener == '))':
                    closer = '(('
                else:
                    if opener.startswith('('): closer = ')' * len(opener)
                    elif opener.startswith('['): closer = ']' * len(opener)
                    elif opener.startswith('{'): closer = '}' * len(opener)
                    else: closer = ''

                # Check if text ends with expected closer
                if closer and text.endswith(closer):
                    # Extract content
                    start_idx = len(node_id) + len(opener)
                    end_idx = -len(closer)
                    inner_text = text[start_idx:end_idx]
                    
                    # Check if inner_text is already quoted
                    if inner_text.startswith('"') and inner_text.endswith('"'):
                        safe_text = inner_text
                    else:
                        # Replace double quotes with single quotes to avoid Mermaid syntax errors
                        safe_text = f'"{inner_text.replace("\"", "\'")}"'
                        
                    sanitized_lines.append(f'{indent}{node_id}{opener}{safe_text}{closer}')
                    is_valid_shape = True
            
            if not is_valid_shape:
                # Not a valid shape definition, treat as plain text node with auto-ID
                node_counter += 1
                auto_id = f"n{node_counter}"
                
                # Check if text is already quoted
                if text.startswith('"') and text.endswith('"'):
                    inner_text = text[1:-1]
                else:
                    inner_text = text
                    
                # Replace double quotes with single quotes to avoid Mermaid syntax errors
                safe_text = inner_text.replace('"', "'")
                sanitized_lines.append(f'{indent}{auto_id}["{safe_text}"]')
                    
        return '\n'.join(sanitized_lines)

    @staticmethod
    def generate(filename: str, content: str) -> str:
        """
        Generates an HTML file containing a Mermaid mindmap.
        
        Args:
            filename: The base filename (without extension).
            content: The Mermaid syntax content (e.g., "mindmap\\n  root((Root))\\n    Child").
            
        Returns:
            The URL path to the generated HTML file.
        """
        # Ensure web/files/mindmaps directory exists (mapped to /static/files/mindmaps via server.py)
        output_dir = os.path.join(os.getcwd(), "web", "files", "mindmaps")
        os.makedirs(output_dir, exist_ok=True)
        
        # Add .html extension if missing
        if not filename.endswith('.html'):
            filename += '.html'
            
        file_path = os.path.join(output_dir, filename)
        
        # Sanitize content
        sanitized_content = MindmapGenerator._sanitize_content(content)
        
        # HTML Template with Mermaid CDN
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mindmap: {filename}</title>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true }});
    </script>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 20px; background: #f4f4f9; display: flex; flex-direction: column; align-items: center; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .mermaid {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); min-width: 600px; display: flex; justify-content: center; }}
    </style>
</head>
<body>
    <h1>Mindmap: {filename}</h1>
    <div class="mermaid">
{sanitized_content}
    </div>
</body>
</html>"""

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return f"/static/files/mindmaps/{filename}"
        except Exception as e:
            raise Exception(f"Failed to write mindmap file: {str(e)}")
