import fitz  
from PIL import Image, ImageDraw
import os

def visualize_text_boxes(pdf_path, output_folder="Output"):

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = fitz.open(pdf_path)
    
    for page_number in range(len(doc)):
        page = doc[page_number]
        
        pix = page.get_pixmap()
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        draw = ImageDraw.Draw(img)
        

        words = page.get_text("words")
        for word in words:
            x0, y0, x1, y1 = word[:4]

            draw.rectangle((x0, y0, x1, y1), outline="red", width=2)
        
        output_path = os.path.join(output_folder, f"page_{page_number+1}.png")
        img.save(output_path)
        print(f"Saved：{output_path}")

if __name__ == "__main__":
    pdf_file = "2.pdf"  
    visualize_text_boxes(pdf_file)
