import fitz  
from PIL import Image, ImageDraw, ImageFont
import os
import math

def center(coord):
    """计算矩形的中心点坐标"""
    x0, y0, x1, y1 = coord
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def is_close(new_coord, existing_coords, threshold=5.0):
    """
    判断新坐标new_coord的中心点与已有坐标列表existing_coords中任一中心点的距离是否小于阈值。
    如果小于阈值，则认为它们代表同一处P1，返回True。
    """
    new_center = center(new_coord)
    for coord in existing_coords:
        existing_center = center(coord)
        dist = math.hypot(new_center[0] - existing_center[0], new_center[1] - existing_center[1])
        if dist < threshold:
            return True
    return False

def visualize_text_boxes(pdf_path, output_folder="Example2_bp1", threshold=5.0):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = fitz.open(pdf_path)
    total_p1_count = 0  # 统计整个 PDF 中唯一 P1 出现次数
    
    # 尝试加载字体，否则使用默认字体
    try:
        font = ImageFont.truetype("arial.ttf", size=20)
    except IOError:
        font = ImageFont.load_default()

    for page_number in range(len(doc)):
        page = doc[page_number]
        
        # 渲染页面为图像
        pix = page.get_pixmap()
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        draw = ImageDraw.Draw(img)
        
        seen_coords = []  # 用于存储已识别的P1的坐标（列表形式，便于存储浮点数）
        page_p1_count = 0   # 当前页唯一 P1 出现次数
        
        # 提取页面中所有单词，格式为 (x0, y0, x1, y1, text, ...)
        words = page.get_text("words")
        for word in words:
            x0, y0, x1, y1 = word[:4]
            text = word[4] if len(word) >= 5 else ""
            # 仅处理文本为 "P1" 的区域，忽略大小写
            if text.lower() == "bp1":
                coord = (x0, y0, x1, y1)
                # 打印原始坐标及计算得到的中心点
                print(f"Page {page_number+1} - Found P1 at raw coordinates: {coord}, center: {center(coord)}")
                # 如果新坐标的中心点与已记录的任一中心点距离大于阈值，则认为是一个新的P1
                if not is_close(coord, seen_coords, threshold):
                    seen_coords.append(coord)
                    draw.rectangle((x0, y0, x1, y1), outline="red", width=2)
                    page_p1_count += 1
        
        total_p1_count += page_p1_count

        # 在图像上写入当前页的P1数量统计（位于页面左上角）
        draw.text((10, 10), f"P1 count: {page_p1_count}", fill="red", font=font)
        
        output_path = os.path.join(output_folder, f"page_{page_number+1}.png")
        img.save(output_path)
        print(f"Saved: {output_path} (Unique P1 count: {page_p1_count})")
    
    print(f"\nTotal unique P1 count in PDF: {total_p1_count}")

if __name__ == "__main__":
    pdf_file = "output_2.pdf"  
    visualize_text_boxes(pdf_file)
