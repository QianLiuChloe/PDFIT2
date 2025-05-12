# mark_region_auto.py   ── 2025-05-12  覆盖版
import fitz           # PyMuPDF
from PIL import Image
from pathlib import Path


def mark_region_auto(
        pdf_path: str,
        jpg_path: str,
        coords_px: tuple[float, float, float, float],
        output_path: str | None = None,
        line_color=(0, 1, 1),         # 青色外框
        line_width=2,
        mask_color=(1, 1, 1)          # ### NEW：遮罩颜色（白色）
):
    """
    给出 PDF 与整页 JPG，自动推算缩放并：
      1) 用白色填充 ROI 以外区域
      2) 在 ROI 边缘画空心矩形框

    Parameters
    ----------
    pdf_path   : str  单页 PDF
    jpg_path   : str  同页整图 JPG
    coords_px  : (x1, y1, x2, y2)  ROI 在 JPG 上的像素坐标（左上原点）
    output_path: str  若为空，默认 <pdf_stem>_marked.pdf
    """
    pdf_path   = Path(pdf_path)
    jpg_path   = Path(jpg_path)
    output_pdf = Path(output_path or pdf_path.with_stem(pdf_path.stem + "_marked"))

    # -------- 1. 读取尺寸信息 --------
    doc  = fitz.open(pdf_path)
    page = doc[0]
    pw_pt, ph_pt = page.rect.width, page.rect.height        # 页面 pt
    img_w, img_h = Image.open(jpg_path).size                # JPG 像素

    # -------- 2. 推算缩放因子 --------
    zoom_x = img_w / pw_pt
    zoom_y = img_h / ph_pt
    if abs(zoom_x - zoom_y) > 1e-3:
        print("[警告] x / y 缩放不一致，使用平均值处理。")
    zoom = (zoom_x + zoom_y) / 2.0

    # -------- 3. 像素 → pt，无需翻转 --------
    x1_px, y1_px, x2_px, y2_px = coords_px
    x1_pt, y1_pt = x1_px / zoom, y1_px / zoom
    x2_pt, y2_pt = x2_px / zoom, y2_px / zoom

    # 归一化 (x1,y1) 为左上，(x2,y2) 为右下
    x0, y0 = min(x1_pt, x2_pt), min(y1_pt, y2_pt)
    x3, y3 = max(x1_pt, x2_pt), max(y1_pt, y2_pt)
    roi = fitz.Rect(x0, y0, x3, y3)

    # -------- 4. 绘制遮罩（四块白色矩形） -------- ### NEW
    page.draw_rect(fitz.Rect(0,        0, pw_pt, y0), fill=mask_color, overlay=True)  # 上
    page.draw_rect(fitz.Rect(0,        y3, pw_pt, ph_pt), fill=mask_color, overlay=True)  # 下
    page.draw_rect(fitz.Rect(0,        y0, x0,   y3), fill=mask_color, overlay=True)  # 左
    page.draw_rect(fitz.Rect(x3,       y0, pw_pt, y3), fill=mask_color, overlay=True)  # 右

    # -------- 5. 画 ROI 外框 --------
    page.draw_rect(roi, color=line_color, width=line_width, overlay=True)

    # -------- 6. 保存 --------
    doc.save(output_pdf, deflate=True)
    doc.close()
    print(f"✔ 已保存标记文件 → {output_pdf}")


# ---------------------- DEMO ----------------------
if __name__ == "__main__":
    coords = (653.38464, 320.80148, 3519.4097, 2315.2349)   # ROI 像素坐标
    mark_region_auto(
        pdf_path="1.pdf",
        jpg_path="1.jpg",
        coords_px=coords,
        line_color=(0, 1, 0)   # 绿色轮廓
    )
