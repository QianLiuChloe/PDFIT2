#!/usr/bin/env python3
"""
pdf_layer_exporter.py — Export PDF page elements into separate logical "layers".

**2025‑05‑15 v4 — De‑duplicated Text Layer**
-------------------------------------------------
* NEW: `_save_text()` rebuilds plain‑text via `page.get_text("blocks")` and
  removes visually overlapping duplicates (common with PDFs where glyphs are
  drawn multiple times or overlayed for clipping/fill effects).
* Uses a positional hash `(rounded_y, rounded_x, stripped_line)` to keep only
  the first occurrence.
* Keeps previous fixes (interactive CLI, graceful deps, XML fallback).

Layers produced for every page (0‑indexed):
  • images/   — raster images (PNG/JPEG) at original resolution
  • text/     — **de‑duplicated** UTF‑8 plain‑text files per page
  • vectors/  — SVGs with vector paths only (images & text stripped) — if
                *beautifulsoup4* missing, outputs full SVG instead.

Quick start
-----------
```bash
pip install pymupdf==1.23.20      # required
pip install beautifulsoup4 lxml   # optional but recommended
pip install tqdm                  # progress bar
```
Run with or without arguments:
```bash
python pdf_layer_exporter.py                # interactive mode
python pdf_layer_exporter.py file.pdf -o out # CLI mode
```
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import List, Tuple, Set

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Optional dependencies with graceful fallback
# ---------------------------------------------------------------------------
_bs4_spec = importlib.util.find_spec("bs4")
if _bs4_spec is not None:
    from bs4 import BeautifulSoup, FeatureNotFound  # type: ignore
    _HAS_BS4 = True
else:
    _HAS_BS4 = False
    print("[!] beautifulsoup4 not found — vector layer will contain ALL elements."  # noqa: E501
          "\n    pip install beautifulsoup4 lxml  # for clean paths‑only SVG", file=sys.stderr)

_tqdm_spec = importlib.util.find_spec("tqdm")
if _tqdm_spec is not None:
    from tqdm import tqdm  # type: ignore
    _progress = tqdm
else:
    _progress = lambda it, **kw: it  # noqa: E731
    print("[!] tqdm not found — progress bar disabled.\n    pip install tqdm", file=sys.stderr)

# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _save_images(page: fitz.Page, page_index: int, root: Path) -> None:
    img_dir = root / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for img_num, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = page.parent.extract_image(xref)
        ext = base_image["ext"]
        img_bytes = base_image["image"]
        (img_dir / f"page{page_index:04d}_img{img_num:03d}.{ext}").write_bytes(img_bytes)


def _save_text(page: fitz.Page, page_index: int, root: Path) -> None:
    """Extract text, remove duplicates drawn at identical visual positions."""
    txt_dir = root / "text"
    txt_dir.mkdir(parents=True, exist_ok=True)

    # Use block mode for positional metadata
    blocks: List[Tuple] = page.get_text("blocks")  # (x0,y0,x1,y1, text, block_no, block_type)
    seen: Set[Tuple[float, float, str]] = set()
    lines: List[Tuple[float, float, str]] = []

    for b in blocks:
        x0, y0, _, _, text, *_ = b
        if not text.strip():
            continue
        for ln in text.splitlines():
            stripped = ln.rstrip()
            if not stripped:
                continue
            # hash by rounded coords (1 decimal pt ~ 0.1pt ≈ 0.035mm)
            h = (round(y0, 1), round(x0, 1), stripped)
            if h in seen:
                continue
            seen.add(h)
            lines.append((y0, x0, stripped))

    # Sort top‑to‑bottom, left‑to‑right
    lines.sort(key=lambda t: (t[0], t[1]))
    plain_text = "\n".join(l[2] for l in lines)
    (txt_dir / f"page{page_index:04d}.txt").write_text(plain_text, encoding="utf-8")


def _save_vectors(page: fitz.Page, page_index: int, root: Path) -> None:
    vec_dir = root / "vectors"
    vec_dir.mkdir(parents=True, exist_ok=True)
    svg_str = page.get_svg_image(text_as_path=False)

    if _HAS_BS4:
        try:
            soup = BeautifulSoup(svg_str, "xml")
        except FeatureNotFound:
            print("[!] lxml not installed, falling back to 'html.parser' — SVG cleaning may be less accurate.", file=sys.stderr)
            soup = BeautifulSoup(svg_str, "html.parser")
        for tag in soup.find_all(["image", "text"]):
            tag.decompose()
        svg_clean = soup.prettify()
    else:
        svg_clean = svg_str  # fallback: keep everything

    (vec_dir / f"page{page_index:04d}.svg").write_text(svg_clean, encoding="utf-8")


def export_layers(pdf_path: Path, output_root: Path) -> None:
    doc = fitz.open(pdf_path)
    total = len(doc)
    for i in _progress(range(total), desc="Processing pages", unit="page"):
        page = doc.load_page(i)
        _save_images(page, i, output_root)
        _save_text(page, i, output_root)
        _save_vectors(page, i, output_root)

# ---------------------------------------------------------------------------
# CLI / Interactive entry
# ---------------------------------------------------------------------------

def cli() -> None:
    parser = argparse.ArgumentParser(
        description="Export PDF elements (images, text, vectors) into separate layer folders."  # noqa: E501
    )
    parser.add_argument("pdf", nargs="?", help="Path to source PDF (leave blank for prompt)")
    parser.add_argument("-o", "--output", help="Output directory (default: export_layers)")
    args = parser.parse_args()

    # PDF path — prompt if missing
    if args.pdf is None:
        pdf_path_str = input("Input PDF file path > ").strip().strip('"')
    else:
        pdf_path_str = args.pdf

    pdf_path = Path(pdf_path_str).expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"[!] PDF not found: {pdf_path}")

    # Output directory
    if args.output is None:
        out_dir_str = input("Output directory [export_layers] > ").strip()
        out_dir_str = out_dir_str or "export_layers"
    else:
        out_dir_str = args.output

    out_root = Path(out_dir_str).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    export_layers(pdf_path, out_root)
    print(f"\n✓ Finished! Layers exported to: {out_root}\n")


if __name__ == "__main__":
    cli()
