#!/usr/bin/env python3
"""
pdf2svg.py
----------
将 PDF 每一页转换为单独的 SVG 文件（page-1.svg、page-2.svg …）。
运行脚本时会提示输入 PDF 文件路径，输出默认保存在同一目录下。

依赖:
    pip install pymupdf
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # 给出友好提示
    print("缺少 PyMuPDF，请先执行:  pip install pymupdf")
    sys.exit(1)


def pdf_to_svg(pdf_path: Path) -> None:
    if not pdf_path.is_file():
        print(f"[错误] 找不到文件: {pdf_path}")
        return

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[错误] 无法打开 PDF: {e}")
        return

    out_dir = pdf_path.parent
    for page in doc:
        # PyMuPDF ≥1.22 推荐 get_svg_image( )；低版本可用 get_svg_text( )
        try:
            svg_text = page.get_svg_image(text_as_path=False)
        except AttributeError:
            svg_text = page.get_svg_text()

        svg_name = out_dir / f"page-{page.number + 1}.svg"
        svg_name.write_text(svg_text, encoding="utf-8")
        print(f"✓ 已保存: {svg_name}")

    print(f"\n完成！共导出 {len(doc)} 页 SVG。")


if __name__ == "__main__":
    # 如果想通过命令行参数传递路径，也支持 
    pdf_input = (
        Path(sys.argv[1]).expanduser()
        if len(sys.argv) > 1
        else Path(input("path: ").strip()).expanduser()
    )
    pdf_to_svg(pdf_input)
