#!/usr/bin/env python3
"""
strip_to_qr.py

Converts a flattened black/white "strip" SVG (as produced by
qr_to_strip.py) back into a normal-looking square QR code SVG.

Since a strip is just a 1D row-major flattening of the QR module grid,
this script reshapes it back into a square grid (size = sqrt(N)) and
redraws it in the same style as a typical QR SVG: a white background
rect plus a single black <path> made of one 4x4-unit square per black
module.

Usage:
    python3 strip_to_qr.py input_strip.svg output_qr.svg [--module-size 4]
"""

import re
import math
import argparse


def parse_strip_svg(svg_text):
    """
    Parse the strip SVG produced by qr_to_strip.py.

    Returns:
        flat_pixels: list of 0/1 values, in the order boxes were drawn
        box_size: size of each box in the strip (in SVG units)
        total_boxes: total number of boxes in the strip (black + white)
    """
    # Get strip width/height to determine box size and box count
    width_match = re.search(r'width="(\d+)', svg_text)
    height_match = re.search(r'height="(\d+)', svg_text)
    if not width_match or not height_match:
        raise ValueError("Could not find strip SVG dimensions")

    strip_width = int(width_match.group(1))
    box_size = int(height_match.group(1))  # height == box_size for a 1-row strip

    total_boxes = round(strip_width / box_size)

    # Find black box x-positions: "M{x},0l{box_size},0 ..."
    coords = re.findall(r'M(-?\d+(?:\.\d+)?),0l(-?\d+(?:\.\d+)?),0', svg_text)
    black_indices = set()
    for x, step in coords:
        idx = round(float(x) / box_size)
        black_indices.add(idx)

    flat_pixels = [1 if i in black_indices else 0 for i in range(total_boxes)]
    return flat_pixels, box_size, total_boxes


def reshape_to_grid(flat_pixels):
    """Reshape a flat row-major list of 0/1 values back into a square 2D grid."""
    n = len(flat_pixels)
    side = round(math.sqrt(n))
    if side * side != n:
        raise ValueError(
            f"Pixel count {n} is not a perfect square; cannot reshape into a square grid."
        )
    grid = []
    for r in range(side):
        grid.append(flat_pixels[r * side:(r + 1) * side])
    return grid


def build_qr_svg(grid, module_size=4):
    """
    Build a normal QR-style SVG from a 2D grid of 0/1 values, matching
    the original format: white background rect + single black <path>
    made of 4x4-unit squares (one per black module).
    """
    side = len(grid)
    svg_size = side * module_size

    path_cmds = []
    for row_idx, row in enumerate(grid):
        y = row_idx * module_size
        for col_idx, val in enumerate(row):
            if val:
                x = col_idx * module_size
                path_cmds.append(
                    f'M{x},{y}l{module_size},0 0,{module_size} '
                    f'-{module_size},0 0,-{module_size}z'
                )

    svg = (
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_size}px" height="{svg_size}px" '
        f'viewBox="0 0 {svg_size} {svg_size}" preserveAspectRatio="xMinYMin meet">'
        f'<rect width="100%" height="100%" fill="#fff" cx="0" cy="0"/>'
        f'<path d="{" ".join(path_cmds)}" stroke="transparent" fill="#000"/>'
        f'</svg>'
    )
    return svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_strip_svg", help="Path to the input strip SVG")
    parser.add_argument("output_qr_svg", help="Path to write the reconstructed QR SVG")
    parser.add_argument(
        "--module-size", type=int, default=4,
        help="Size (in SVG units) of each QR module in the output (default: 4, "
             "matching typical QR SVG generators)"
    )
    args = parser.parse_args()

    with open(args.input_strip_svg, "r") as f:
        svg_text = f.read()

    flat_pixels, box_size, total_boxes = parse_strip_svg(svg_text)
    grid = reshape_to_grid(flat_pixels)

    qr_svg = build_qr_svg(grid, module_size=args.module_size)

    with open(args.output_qr_svg, "w") as f:
        f.write(qr_svg)

    side = len(grid)
    print(f"Parsed strip: {total_boxes} pixels ({sum(flat_pixels)} black)")
    print(f"Reshaped into {side}x{side} grid")
    print(f"Wrote reconstructed QR SVG to: {args.output_qr_svg}")


if __name__ == "__main__":
    main()
