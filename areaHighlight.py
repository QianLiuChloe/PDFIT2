# mark_region_auto.py  ── 2025-05-12 修正版
import fitz          # PyMuPDF
from PIL import Image
from pathlib import Path

def mark_region_auto(
        pdf_path: str,
        jpg_path: str,
        coords_px: tuple[float, float, float, float],
        output_path: str | None = None,
        line_color=(0, 1, 1),        # 青色
        line_width=2
    ):
    """
    给出同一页的 PDF 与 JPG（整页），自动推算缩放并在 PDF 里画空心矩形框。

    Parameters
    ----------
    pdf_path   : str  PDF 文件路径（单页或至少第一页对应）
    jpg_path   : str  同一页导出的整页 JPG 路径
    coords_px  : tuple(x1, y1, x2, y2)  蓝框在 JPG 上的像素坐标（左上原点）
    output_path: str  输出 PDF 路径；None → 在源文件名后加 _marked.pdf
    """
    pdf_path   = Path(pdf_path)
    jpg_path   = Path(jpg_path)
    output_pdf = Path(output_path or pdf_path.with_stem(pdf_path.stem + "_marked"))

    # 1) 读取 PDF，获取页面尺寸（pt）
    doc  = fitz.open(pdf_path)
    page = doc[0]
    pw_pt, ph_pt = page.rect.width, page.rect.height

    # 2) 读取 JPG，获取像素尺寸
    img_w, img_h = Image.open(jpg_path).size

    # 3) 计算缩放因子
    zoom_x = img_w / pw_pt
    zoom_y = img_h / ph_pt
    if abs(zoom_x - zoom_y) > 1e-3:
        print("[警告] 检测到 x/y 缩放不一致，可能页面被拉伸或裁剪，"
              "以下使用平均值处理。")
    zoom = (zoom_x + zoom_y) / 2.0

    # 4) 像素坐标 → pt（不再翻转 y 轴）
    x1_px, y1_px, x2_px, y2_px = coords_px
    x1_pt = x1_px / zoom
    x2_pt = x2_px / zoom
    y1_pt = y1_px / zoom
    y2_pt = y2_px / zoom

    # 5) 画矩形
    rect = fitz.Rect(min(x1_pt, x2_pt), min(y1_pt, y2_pt),
                     max(x1_pt, x2_pt), max(y1_pt, y2_pt))
    page.draw_rect(rect, color=line_color, width=line_width)

    # 6) 保存
    doc.save(output_pdf, deflate=True)
    doc.close()
    print(f"✔ 已保存标记文件 → {output_pdf}")

# ---------------------- DEMO ----------------------
if __name__ == "__main__":
    # 在 JPG 上量好的像素坐标
    coords = (653.38464, 320.80148, 3519.4097, 2315.2349)
    mark_region_auto(
        pdf_path="1.pdf",
        jpg_path="1.jpg",
        coords_px=coords,
        line_color=(0, 1, 0)   # 绿色
    )
