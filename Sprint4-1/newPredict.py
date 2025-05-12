
import math, os, sys
import fitz, cv2
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from yolo import YOLO
from typing import Tuple

# PDF to JPG
def pdf_to_jpg(pdf_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(exist_ok=True)
    with fitz.open(pdf_path) as doc:
        page = doc[0]
        pix  = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # ≈300 dpi
        jpg_path = output_dir / f"{pdf_path.stem}_page_1.jpg"
        Image.frombytes("RGB", [pix.width, pix.height], pix.samples)\
             .save(jpg_path, quality=95, subsampling=0)
    print(f"✔ Image saved: {jpg_path}")
    return jpg_path

DEDUP_THRESHOLD = 5.0
LINE_COLOR      = (0, 1, 1)
LINE_WIDTH      = 2
PREVIEW_ZOOM    = 2.0

def center(coord): return ((coord[0]+coord[2])/2, (coord[1]+coord[3])/2)

def is_close(new, existing, thr=DEDUP_THRESHOLD):
    nc = center(new)
    return any(math.hypot(nc[0]-center(c)[0], nc[1]-center(c)[1]) < thr for c in existing)

def subtract_rect(base, sub):
    if not base.intersects(sub): return [base]
    inter = base & sub; r=[]
    if inter.y0>base.y0: r.append(fitz.Rect(base.x0,base.y0,base.x1,inter.y0))
    if inter.y1<base.y1: r.append(fitz.Rect(base.x0,inter.y1,base.x1,base.y1))
    if inter.x0>base.x0: r.append(fitz.Rect(base.x0,inter.y0,inter.x0,inter.y1))
    if inter.x1<base.x1: r.append(fitz.Rect(inter.x1,inter.y0,base.x1,inter.y1))
    return r

def subtract_rects(full_rect, subs):
    covers=[full_rect]
    for s in subs:
        tmp=[]
        for r in covers: tmp.extend(subtract_rect(r,s))
        covers=tmp
    return covers

def pdf_postprocess(pdf_path: Path, img_path: Path,
                    coords_px: Tuple[float, float, float, float],
                    out_dir: Path):

    doc  = fitz.open(pdf_path)
    page = doc[0]

    # ---------- ① 计算缩放，把像素坐标转换为 PDF pt ----------
    pw, ph = page.rect.width, page.rect.height
    img_w, img_h = Image.open(img_path).size
    zx, zy = img_w / pw, img_h / ph
    if abs(zx - zy) > 1e-3:
        print("x/y scaling is inconsistent, take average")
    zoom = (zx + zy) / 2

    x1_px, y1_px, x2_px, y2_px = coords_px
    x1_pt, y1_pt = x1_px / zoom, y1_px / zoom
    x2_pt, y2_pt = x2_px / zoom, y2_px / zoom
    region_rect  = fitz.Rect(min(x1_pt, x2_pt), min(y1_pt, y2_pt),
                             max(x1_pt, x2_pt), max(y1_pt, y2_pt))


    page.draw_rect(region_rect, color=LINE_COLOR, width=LINE_WIDTH)


    words = page.get_text("words")
    dedup = {}
    for w in words:
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        if region_rect.contains(fitz.Point(cx, cy)):
            lbl = w[4].strip()
            if not lbl:
                continue
            dedup.setdefault(lbl, [])
            if not is_close(w[:4], dedup[lbl]):
                dedup[lbl].append(w[:4])
    counts = {k: len(v) for k, v in dedup.items()}


    pix = page.get_pixmap(matrix=fitz.Matrix(PREVIEW_ZOOM, PREVIEW_ZOOM))
    np_img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        np_img = np_img[..., :3]
    pil_img = Image.fromarray(np_img)
    draw = ImageDraw.Draw(pil_img)
    cmap = plt.get_cmap("tab10")
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()
    for i, (lbl, boxes) in enumerate(dedup.items()):
        rgb = tuple(int(255 * c) for c in cmap(i % 10)[:3])
        for b in boxes:
            x0, y0, x1, y1 = [v * PREVIEW_ZOOM for v in b]
            draw.rectangle([x0, y0, x1, y1], outline=rgb, width=2)
            draw.text((x0, y0), lbl, fill=rgb, font=font)
    preview_path = out_dir / f"{pdf_path.stem}_preview.png"
    pil_img.save(preview_path)


    cover_rects = subtract_rects(page.rect, [region_rect])
    for cr in cover_rects:
        annot = page.add_redact_annot(cr)
        annot.set_colors(stroke=None, fill=(1, 1, 1))
        annot.update()
    page.apply_redactions()


    marked_pdf = out_dir / f"{pdf_path.stem}_marked.pdf"
    doc.save(marked_pdf, deflate=True)
    doc.close()

    df = pd.DataFrame(counts.items(), columns=["Element", "Count"])
    excel_path = out_dir / f"{pdf_path.stem}_label_counts.xlsx"
    df.to_excel(excel_path, index=False)

    print("\n=== PDF post-processing completed ===")
    print("preview image  →", preview_path)
    print("mark PDF →", marked_pdf)
    print("counting table  →", excel_path)



if __name__ == "__main__":
    pdf_path = Path(input("PDF Path: ").strip().strip('"'))
    if not pdf_path.exists():
        sys.exit("PDF not found.")

    out_dir = pdf_path.parent / pdf_path.stem
    jpg_path = pdf_to_jpg(pdf_path, out_dir)


    yolo = YOLO(); crop=True; count=False
    r_img, coord_raw = yolo.detect_image(Image.open(jpg_path), crop=crop, count=count)
    if coord_raw is None or len(coord_raw)!=4:
        sys.exit("No detection.")
    coord_px = (coord_raw[1], coord_raw[0], coord_raw[3], coord_raw[2])  # yx→xy


    annotated_path = out_dir / f"{pdf_path.stem}_annotated.png"
    r_img.save(annotated_path, quality=95, subsampling=0)
    print("Coordinate", coord_px)


    try:
        pdf_postprocess(pdf_path, annotated_path, coord_px, out_dir)
    except Exception as e:
        print("Post-processing failed:", e)
