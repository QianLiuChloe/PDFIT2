import fitz
import io
from PIL import Image

def extract_images(pdf_path, output_folder="PDFIT2\ImageExtraction\ExtractedImages"):
    import os
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    doc = fitz.open(pdf_path)
    image_count = 0

    for page_number in range(len(doc)):
        page = doc[page_number]
        image_list = page.get_images(full=True)
        for image_index, img in enumerate(image_list):
            xref = img[0]
   
            pix = fitz.Pixmap(doc, xref)

            if pix.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            image_filename = os.path.join(output_folder, f"image_page{page_number+1}_{image_index+1}.png")
            pix.save(image_filename)
            pix = None
            image_count += 1
    print(f"Number of Images: {image_count} 。")

if __name__ == "__main__":
    pdf_file = "3.pdf"  
    extract_images(pdf_file)
