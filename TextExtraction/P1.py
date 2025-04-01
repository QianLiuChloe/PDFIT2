import fitz  
from PIL import Image, ImageDraw
import os

def visualize_text_boxes(pdf_path, output_folder="P1"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = fitz.open(pdf_path)
    
    for page_number in range(len(doc)):
        page = doc[page_number]
        
        # 渲染页面为图像
        pix = page.get_pixmap()
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        draw = ImageDraw.Draw(img)
        
        # 提取页面中所有单词，每个单词的元组格式为 (x0, y0, x1, y1, text, ...)
        words = page.get_text("words")
        for word in words:
            x0, y0, x1, y1 = word[:4]
            text = word[4] if len(word) >= 5 else ""
            # 仅标记文本为 "P1" 的区域，忽略大小写
            if text.lower() == "p1":
                draw.rectangle((x0, y0, x1, y1), outline="red", width=2)
        
        output_path = os.path.join(output_folder, f"page_{page_number+1}.png")
        img.save(output_path)
        print(f"Saved: {output_path}")

if __name__ == "__main__":
    pdf_file = "output.pdf"  
    visualize_text_boxes(pdf_file)
