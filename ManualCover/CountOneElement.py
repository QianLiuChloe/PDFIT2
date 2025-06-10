import fitz  
from PIL import Image, ImageDraw, ImageFont
import os
import math

def center(coord):

    x0, y0, x1, y1 = coord
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def is_close(new_coord, existing_coords, threshold=5.0):

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
    total_p1_count = 0  
    

    try:
        font = ImageFont.truetype("arial.ttf", size=20)
    except IOError:
        font = ImageFont.load_default()

    for page_number in range(len(doc)):
        page = doc[page_number]
        

        pix = page.get_pixmap()
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        draw = ImageDraw.Draw(img)
        
        seen_coords = [] 
        page_p1_count = 0   
   
        words = page.get_text("words")
        for word in words:
            x0, y0, x1, y1 = word[:4]
            text = word[4] if len(word) >= 5 else ""
  
            if text.lower() == "bp1":
                coord = (x0, y0, x1, y1)
         
                print(f"Page {page_number+1} - Found P1 at raw coordinates: {coord}, center: {center(coord)}")
           
                if not is_close(coord, seen_coords, threshold):
                    seen_coords.append(coord)
                    draw.rectangle((x0, y0, x1, y1), outline="red", width=2)
                    page_p1_count += 1
        
        total_p1_count += page_p1_count

        draw.text((10, 10), f"P1 count: {page_p1_count}", fill="red", font=font)
        
        output_path = os.path.join(output_folder, f"page_{page_number+1}.png")
        img.save(output_path)
        print(f"Saved: {output_path} (Unique P1 count: {page_p1_count})")
    
    print(f"\nTotal unique P1 count in PDF: {total_p1_count}")

if __name__ == "__main__":
    pdf_file = "output_2.pdf"  
    visualize_text_boxes(pdf_file)
