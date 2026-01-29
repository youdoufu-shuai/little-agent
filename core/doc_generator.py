import os
from typing import List, Dict, Any, Optional
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class DocumentGenerator:
    """
    处理混合内容的 .docx 和 .pdf 文档生成。
    """

    @staticmethod
    def generate(filename: str, file_type: str, content: List[Dict[str, Any]], style_config: Optional[Dict[str, Any]] = None) -> str:
        """
        生成文档。
        
        Args:
            filename: 输出文件名（基本名称）。
            file_type: 'docx' 或 'pdf'。
            content: 内容块列表。
            style_config: 全局样式设置。
            
        Returns:
            生成文件的绝对路径。
        """
        # 确保输出目录存在
        output_dir = os.path.join(os.getcwd(), "web", "files")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 确保扩展名匹配
        if not filename.lower().endswith(f".{file_type}"):
            filename += f".{file_type}"
            
        file_path = os.path.join(output_dir, filename)
        
        if file_type.lower() == 'docx':
            return DocumentGenerator._generate_docx(file_path, content, style_config)
        elif file_type.lower() == 'pdf':
            return DocumentGenerator._generate_pdf(file_path, content, style_config)
        else:
            raise ValueError("Unsupported file type. Use 'docx' or 'pdf'.")

    @staticmethod
    def _generate_docx(file_path: str, content: List[Dict[str, Any]], style_config: Optional[Dict[str, Any]]) -> str:
        doc = Document()
        
        # 如果可能，应用全局样式（python-docx 在没有模板的情况下全局默认设置有限）
        # 目前我们将逐个元素应用。
        
        for block in content:
            b_type = block.get("type", "paragraph")
            text = block.get("text", "")
            
            if b_type == "heading":
                level = block.get("level", 1)
                doc.add_heading(text, level=level)
                
            elif b_type == "paragraph":
                p = doc.add_paragraph()
                run = p.add_run(text)
                
                # 样式覆盖
                style = block.get("style", {})
                if "font_size" in style:
                    run.font.size = Pt(style["font_size"])
                if "bold" in style:
                    run.bold = style["bold"]
                if "italic" in style:
                    run.italic = style["italic"]
                if "alignment" in style:
                    align = style["alignment"].lower()
                    if align == "center":
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    elif align == "right":
                        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    elif align == "justify":
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        
            elif b_type == "image":
                path = block.get("path")
                width = block.get("width", 6.0) # 默认 6 英寸
                
                # 解析相对路径
                if path and not os.path.isabs(path):
                    # 尝试在 web/images 或当前目录中查找
                    potential_paths = [
                        os.path.join(os.getcwd(), path),
                        os.path.join(os.getcwd(), "web", path),
                        os.path.join(os.getcwd(), "web", "images", os.path.basename(path))
                    ]
                    for p_path in potential_paths:
                        if os.path.exists(p_path):
                            path = p_path
                            break
                            
                if path and os.path.exists(path):
                    try:
                        doc.add_picture(path, width=Inches(min(width, 6.0))) # 限制最大宽度
                    except Exception as e:
                        doc.add_paragraph(f"[Image load failed: {str(e)}]")
                else:
                    doc.add_paragraph(f"[Image not found: {block.get('path')}]")
                    
            elif b_type == "page_break":
                doc.add_page_break()
                
        doc.save(file_path)
        return f"/static/files/{os.path.basename(file_path)}"

    @staticmethod
    def _generate_pdf(file_path: str, content: List[Dict[str, Any]], style_config: Optional[Dict[str, Any]]) -> str:
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 可以根据 style_config 在此处添加自定义样式
        
        for block in content:
            b_type = block.get("type", "paragraph")
            text = block.get("text", "")
            
            if b_type == "heading":
                level = block.get("level", 1)
                # 将级别映射到 h1, h2, h3...
                style_name = f'Heading{min(level, 6)}'
                if style_name not in styles:
                    style_name = 'Heading1'
                story.append(Paragraph(text, styles[style_name]))
                
            elif b_type == "paragraph":
                # 如果需要特定样式，为此段落创建自定义样式
                # 为简单起见，使用 'BodyText' 或创建临时样式
                style = styles['BodyText']
                
                # ReportLab 通常通过文本中的类似 XML 的标签处理样式，
                # 或者我们可以定义一个新的 ParagraphStyle。
                # 对于基本文本，我们只使用 BodyText。
                # 如果需要对齐：
                block_style = block.get("style", {})
                if "alignment" in block_style:
                    # 克隆并修改
                    align_map = {"left": 0, "center": 1, "right": 2, "justify": 4}
                    align = block_style["alignment"].lower()
                    if align in align_map:
                        style = ParagraphStyle(
                            f'Custom_{len(story)}',
                            parent=styles['BodyText'],
                            alignment=align_map[align]
                        )
                
                story.append(Paragraph(text, style))
                story.append(Spacer(1, 12))
                
            elif b_type == "image":
                path = block.get("path")
                width = block.get("width", 400) # 大致像素
                height = block.get("height", 300)
                
                # 解析相对路径
                if path and not os.path.isabs(path):
                    potential_paths = [
                        os.path.join(os.getcwd(), path),
                        os.path.join(os.getcwd(), "web", path),
                        os.path.join(os.getcwd(), "web", "images", os.path.basename(path))
                    ]
                    for p_path in potential_paths:
                        if os.path.exists(p_path):
                            path = p_path
                            break
                
                if path and os.path.exists(path):
                    try:
                        # ReportLab 图像
                        # 转换宽度概念（英寸/像素）？
                        # ReportLab 使用点（1/72 英寸）。
                        # 如果用户为 docx 传递 6（英寸），我们可能需要转换。
                        # 让我们假设输入是通用的 'width' 比例。
                        # 如果 < 10，假设为英寸 -> * 72。
                        img_width = width
                        if img_width < 20: 
                            img_width = img_width * 72
                            
                        # 保持纵横比的逻辑可以在这里实现
                        img = RLImage(path, width=img_width, height=img_width*0.75) # 纵横比猜测
                        # 更好：如果我们只设置宽度，让 reportlab 处理纵横比？
                        # RLImage(path, width=w, height=h) 需要两者或计算逻辑。
                        # 让我们尝试使用 PIL 获取图像大小以保持纵横比
                        try:
                            from PIL import Image as PILImage
                            with PILImage.open(path) as pi:
                                iw, ih = pi.size
                                aspect = ih / iw
                                img_height = img_width * aspect
                                img = RLImage(path, width=img_width, height=img_height)
                        except:
                            pass # 回退到近似方形
                            
                        story.append(img)
                        story.append(Spacer(1, 12))
                    except Exception as e:
                        story.append(Paragraph(f"[Image load failed: {str(e)}]", styles['BodyText']))
                else:
                    story.append(Paragraph(f"[Image not found: {block.get('path')}]", styles['BodyText']))
                    
            elif b_type == "page_break":
                from reportlab.platypus import PageBreak
                story.append(PageBreak())
                
        doc.build(story)
        return f"/static/files/{os.path.basename(file_path)}"
