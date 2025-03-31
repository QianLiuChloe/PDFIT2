import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import os

def visualize_pdf_elements(pdf_path, output_folder):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 打开 PDF 文件
    doc = fitz.open(pdf_path)
    
    for page_number in range(len(doc)):
        page = doc[page_number]
        # 将页面渲染为图像
        pix = page.get_pixmap()
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        draw = ImageDraw.Draw(img)
        
        # 1. 标记文本元素（红色框）
        words = page.get_text("words")
        for word in words:
            x0, y0, x1, y1 = word[:4]
            draw.rectangle((x0, y0, x1, y1), outline="red", width=2)
        
        # 2. 标记向量图形（蓝色框）
        drawings = page.get_drawings()
        for drawing in drawings:
            rect = drawing.get("rect")
            if rect:
                draw.rectangle((rect.x0, rect.y0, rect.x1, rect.y1), outline="blue", width=2)
        
        # 3. 标记注释（绿色框）
        if page.annots():
            for annot in page.annots():
                rect = annot.rect
                draw.rectangle((rect.x0, rect.y0, rect.x1, rect.y1), outline="green", width=2)
        
        # 4. 标记链接（紫色框）
        links = page.get_links()
        for link in links:
            if "from" in link:
                rect = fitz.Rect(link["from"])
                draw.rectangle((rect.x0, rect.y0, rect.x1, rect.y1), outline="purple", width=2)
        
        # 保存标记后的页面图像
        output_path = os.path.join(output_folder, f"page_{page_number+1}.png")
        img.save(output_path)
        print(f"已保存：{output_path}")

if __name__ == "__main__":
    pdf_file = "1.pdf"  # 请替换为你的 PDF 文件路径
    output_folder = r"D:\Qian\PDFIT2\ElementExtraction\Output"
    visualize_pdf_elements(pdf_file, output_folder)
