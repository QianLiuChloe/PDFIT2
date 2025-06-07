<<<<<<< HEAD

import re, os, math, fitz, pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector, Button    

DEDUP_THRESHOLD = 5.0     
LINE_COLOR      = (0, 1, 1)   
LINE_WIDTH      = 2
PREVIEW_ZOOM    = 2.0

def parse_coord_line(s: str) -> tuple[float, float, float, float]:
   
    nums = list(map(float, re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?", s)))
    if len(nums) != 4:
        raise ValueError("please check your input(Coordinates from YOLO output)")
    y1, x1, y2, x2 = nums
    return (x1, y1, x2, y2)

def center(coord):
    x0, y0, x1, y1 = coord
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def is_close(new_coord, existing_coords, threshold=DEDUP_THRESHOLD):
    nc = center(new_coord)
    for c in existing_coords:
        if math.hypot(nc[0]-center(c)[0], nc[1]-center(c)[1]) < threshold:
            return True
    return False

def subtract_rect(base, sub):
 
    res = []
    if not base.intersects(sub):
        return [base]
    inter = base & sub
    if inter.y0 > base.y0:
        res.append(fitz.Rect(base.x0, base.y0, base.x1, inter.y0))
    if inter.y1 < base.y1:
        res.append(fitz.Rect(base.x0, inter.y1, base.x1, base.y1))
    if inter.x0 > base.x0:
        res.append(fitz.Rect(base.x0, inter.y0, inter.x0, inter.y1))
    if inter.x1 < base.x1:
        res.append(fitz.Rect(inter.x1, inter.y0, base.x1, inter.y1))
    return res

def subtract_rects(full_rect, sub_rects):
    covers = [full_rect]
    for sub in sub_rects:
        tmp = []
        for r in covers:
            tmp.extend(subtract_rect(r, sub))
        covers = tmp
    return covers


def main():

    pdf_path  = Path(input("PDF Path: ").strip().strip('"'))
    img_path  = Path(input("PNG/JPG path: ").strip().strip('"'))
    coord_str = input("Paste the YOLO output coordinates").strip()
    coords_px = parse_coord_line(coord_str)
    print("after analysing  (x1, y1, x2, y2):", coords_px)

    if not pdf_path.exists() or not img_path.exists():
        print("Flie not exist")
        return


    doc  = fitz.open(pdf_path)
    page = doc[0]
    pw_pt, ph_pt = page.rect.width, page.rect.height


    img_w, img_h = Image.open(img_path).size
    zoom_x = img_w / pw_pt
    zoom_y = img_h / ph_pt
    if abs(zoom_x - zoom_y) > 1e-3:
        print("An x/y scaling inconsistency was detected, the average will be used.")
    zoom = (zoom_x + zoom_y) / 2

 
    x1_px, y1_px, x2_px, y2_px = coords_px
    x1_pt, y1_pt = x1_px/zoom, y1_px/zoom
    x2_pt, y2_pt = x2_px/zoom, y2_px/zoom
    region_rect = fitz.Rect(min(x1_pt,x2_pt), min(y1_pt,y2_pt),
                            max(x1_pt,x2_pt), max(y1_pt,y2_pt))

    page.draw_rect(region_rect, color=LINE_COLOR, width=LINE_WIDTH)

   
    words = page.get_text("words")  # [(x0,y0,x1,y1, text, ...), ...]
    dedup = {}
    for w in words:
        
        cx, cy = (w[0]+w[2])/2, (w[1]+w[3])/2
        if region_rect.contains(fitz.Point(cx, cy)):
            label = w[4].strip()
            if not label:  
                continue
            if label not in dedup:
                dedup[label] = []
            if not is_close(w[:4], dedup[label]):
                dedup[label].append(w[:4])
    counts = {k: len(v) for k, v in dedup.items()}
    print("\n=== Counting results ===")
    for k, v in counts.items():
        print(f"{k}: {v}")


    pix = page.get_pixmap(matrix=fitz.Matrix(PREVIEW_ZOOM, PREVIEW_ZOOM))
    np_img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4: 
        np_img = np_img[..., :3]
    pil_img = Image.fromarray(np_img)
    draw    = ImageDraw.Draw(pil_img)
    cmap    = plt.get_cmap("tab10")
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()

    for i, (lbl, boxes) in enumerate(dedup.items()):
        rgb = tuple(int(255*c) for c in cmap(i%10)[:3])
        for b in boxes:
            x0, y0, x1, y1 = [v*PREVIEW_ZOOM for v in b]
            draw.rectangle([x0,y0,x1,y1], outline=rgb, width=2)
            draw.text((x0, y0), lbl, fill=rgb, font=font)
    preview_path = pdf_path.with_stem(pdf_path.stem + "_preview").with_suffix(".png")
    pil_img.save(preview_path)
    print("Preview save as →", preview_path)

 
    cover_rects = subtract_rects(page.rect, [region_rect])
    for cr in cover_rects:
        page.add_redact_annot(cr, fill=(1,1,1))
    page.apply_redactions()


    marked_pdf = pdf_path.with_stem(pdf_path.stem + "_marked").with_suffix(".pdf")
    doc.save(marked_pdf, deflate=True)
    doc.close()
    print("NEW PDF save as", marked_pdf)

    df = pd.DataFrame(list(counts.items()), columns=["Element", "Count"])
    excel_path = pdf_path.with_stem(pdf_path.stem + "_label_counts").with_suffix(".xlsx")
    df.to_excel(excel_path, index=False)
    print("Counting Table", excel_path)

if __name__ == "__main__":
    main()
=======

import re, os, math, fitz, pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector, Button    

DEDUP_THRESHOLD = 5.0     
LINE_COLOR      = (0, 1, 1)   
LINE_WIDTH      = 2
PREVIEW_ZOOM    = 2.0

def parse_coord_line(s: str) -> tuple[float, float, float, float]:
   
    nums = list(map(float, re.findall(r"[-+]?\d*\.\d+(?:[eE][-+]?\d+)?", s)))
    if len(nums) != 4:
        raise ValueError("please check your input(Coordinates from YOLO output)")
    y1, x1, y2, x2 = nums
    return (x1, y1, x2, y2)

def center(coord):
    x0, y0, x1, y1 = coord
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def is_close(new_coord, existing_coords, threshold=DEDUP_THRESHOLD):
    nc = center(new_coord)
    for c in existing_coords:
        if math.hypot(nc[0]-center(c)[0], nc[1]-center(c)[1]) < threshold:
            return True
    return False

def subtract_rect(base, sub):
 
    res = []
    if not base.intersects(sub):
        return [base]
    inter = base & sub
    if inter.y0 > base.y0:
        res.append(fitz.Rect(base.x0, base.y0, base.x1, inter.y0))
    if inter.y1 < base.y1:
        res.append(fitz.Rect(base.x0, inter.y1, base.x1, base.y1))
    if inter.x0 > base.x0:
        res.append(fitz.Rect(base.x0, inter.y0, inter.x0, inter.y1))
    if inter.x1 < base.x1:
        res.append(fitz.Rect(inter.x1, inter.y0, base.x1, inter.y1))
    return res

def subtract_rects(full_rect, sub_rects):
    covers = [full_rect]
    for sub in sub_rects:
        tmp = []
        for r in covers:
            tmp.extend(subtract_rect(r, sub))
        covers = tmp
    return covers


def main():

    pdf_path  = Path(input("PDF Path: ").strip().strip('"'))
    img_path  = Path(input("PNG/JPG path: ").strip().strip('"'))
    coord_str = input("Paste the YOLO output coordinates").strip()
    coords_px = parse_coord_line(coord_str)
    print("after analysing  (x1, y1, x2, y2):", coords_px)

    if not pdf_path.exists() or not img_path.exists():
        print("Flie not exist")
        return


    doc  = fitz.open(pdf_path)
    page = doc[0]
    pw_pt, ph_pt = page.rect.width, page.rect.height


    img_w, img_h = Image.open(img_path).size
    zoom_x = img_w / pw_pt
    zoom_y = img_h / ph_pt
    if abs(zoom_x - zoom_y) > 1e-3:
        print("An x/y scaling inconsistency was detected, the average will be used.")
    zoom = (zoom_x + zoom_y) / 2

 
    x1_px, y1_px, x2_px, y2_px = coords_px
    x1_pt, y1_pt = x1_px/zoom, y1_px/zoom
    x2_pt, y2_pt = x2_px/zoom, y2_px/zoom
    region_rect = fitz.Rect(min(x1_pt,x2_pt), min(y1_pt,y2_pt),
                            max(x1_pt,x2_pt), max(y1_pt,y2_pt))

    page.draw_rect(region_rect, color=LINE_COLOR, width=LINE_WIDTH)

   
    words = page.get_text("words")  # [(x0,y0,x1,y1, text, ...), ...]
    dedup = {}
    for w in words:
        
        cx, cy = (w[0]+w[2])/2, (w[1]+w[3])/2
        if region_rect.contains(fitz.Point(cx, cy)):
            label = w[4].strip()
            if not label:  
                continue
            if label not in dedup:
                dedup[label] = []
            if not is_close(w[:4], dedup[label]):
                dedup[label].append(w[:4])
    counts = {k: len(v) for k, v in dedup.items()}
    print("\n=== Counting results ===")
    for k, v in counts.items():
        print(f"{k}: {v}")


    pix = page.get_pixmap(matrix=fitz.Matrix(PREVIEW_ZOOM, PREVIEW_ZOOM))
    np_img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4: 
        np_img = np_img[..., :3]
    pil_img = Image.fromarray(np_img)
    draw    = ImageDraw.Draw(pil_img)
    cmap    = plt.get_cmap("tab10")
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()

    for i, (lbl, boxes) in enumerate(dedup.items()):
        rgb = tuple(int(255*c) for c in cmap(i%10)[:3])
        for b in boxes:
            x0, y0, x1, y1 = [v*PREVIEW_ZOOM for v in b]
            draw.rectangle([x0,y0,x1,y1], outline=rgb, width=2)
            draw.text((x0, y0), lbl, fill=rgb, font=font)
    preview_path = pdf_path.with_stem(pdf_path.stem + "_preview").with_suffix(".png")
    pil_img.save(preview_path)
    print("✔ 预览已保存 →", preview_path)

 
    cover_rects = subtract_rects(page.rect, [region_rect])
    for cr in cover_rects:
        page.add_redact_annot(cr, fill=(1,1,1))
    page.apply_redactions()


    marked_pdf = pdf_path.with_stem(pdf_path.stem + "_marked").with_suffix(".pdf")
    doc.save(marked_pdf, deflate=True)
    doc.close()
    print("NEW PDF save as", marked_pdf)

    df = pd.DataFrame(list(counts.items()), columns=["Element", "Count"])
    excel_path = pdf_path.with_stem(pdf_path.stem + "_label_counts").with_suffix(".xlsx")
    df.to_excel(excel_path, index=False)
    print("Counting Table", excel_path)

if __name__ == "__main__":
    main()
>>>>>>> dc417a4d1236f18ca80811912643da3b84695192
