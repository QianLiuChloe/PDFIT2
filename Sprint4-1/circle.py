#!/usr/bin/env python3
"""
svg_circle_remover.py — Delete all <circle> elements from an SVG file.

**2025-05-15 v4 — Flexible Output**
----------------------------------
* New `-o/--output` to specify output file explicitly.
* New `-p/--print` to stream cleaned SVG to stdout (no file written).
* Improved file-type guard & binary read remain.

Usage Examples
--------------
    # Interactive, default writes my.svg -> my_nocircle.svg
    python svg_circle_remover.py

    # CLI, choose output name
    python svg_circle_remover.py drawing.svg -o drawing_clean.svg

    # In-place overwrite (destructive)
    python svg_circle_remover.py drawing.svg -i

    # Print to console / pipe elsewhere
    python svg_circle_remover.py drawing.svg -p > tmp.svg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Optional dependency: BeautifulSoup
# ---------------------------------------------------------------------------
try:
    from bs4 import BeautifulSoup, FeatureNotFound  # type: ignore
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False
    print("[!] beautifulsoup4 not found — falling back to xml.etree (slower)", file=sys.stderr)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _remove_circles_bs4(svg_bytes: bytes) -> str:
    try:
        soup = BeautifulSoup(svg_bytes, "xml")
    except (FeatureNotFound, Exception):
        soup = BeautifulSoup(svg_bytes, "html.parser")
    for c in soup.find_all("circle"):
        c.decompose()
    return soup.prettify()


def _remove_circles_etree(svg_bytes: bytes) -> str:
    root = ET.fromstring(svg_bytes)
    ns = "{http://www.w3.org/2000/svg}"
    def traverse(parent):
        for child in list(parent):
            if child.tag == f"{ns}circle":
                parent.remove(child)
            else:
                traverse(child)
    traverse(root)
    return ET.tostring(root, encoding="unicode")


def clean_svg(svg_path: Path) -> str:
    svg_bytes = svg_path.read_bytes()
    return (_remove_circles_bs4(svg_bytes) if _HAS_BS4 else _remove_circles_etree(svg_bytes))

# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def cli() -> None:
    parser = argparse.ArgumentParser(description="Remove all <circle> elements from an SVG.")
    parser.add_argument("svg", nargs="?", help="Path to SVG (leave blank for prompt)")
    parser.add_argument("-i", "--inplace", action="store_true", help="Edit the SVG in-place (overwrite)")
    parser.add_argument("-o", "--output", help="Write cleaned SVG to this file (ignored with -i)")
    parser.add_argument("-p", "--print", action="store_true", help="Print cleaned SVG to stdout instead of writing file")
    args = parser.parse_args()

    svg_path = Path((args.svg or input("Input SVG file path > ").strip().strip('"'))).expanduser().resolve()
    if not svg_path.is_file():
        raise SystemExit(f"[!] File not found: {svg_path}")
    if svg_path.suffix.lower() != ".svg":
        print("[!] Warning: provided file does not appear to be an SVG.", file=sys.stderr)

    cleaned_svg = clean_svg(svg_path)

    # Handle output destinations
    if args.print:
        print(cleaned_svg)
        return

    if args.inplace:
        out_path = svg_path
    else:
        out_path = Path(args.output) if args.output else svg_path.with_stem(svg_path.stem + "_nocircle")
    out_path.write_text(cleaned_svg, encoding="utf-8")
    print(f"✓ Circles removed → {out_path}")

if __name__ == "__main__":
    cli()
