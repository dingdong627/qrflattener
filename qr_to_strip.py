#!/usr/bin/env python3
"""
qr_to_strip.py

Converts a QR-code SVG (made of 4x4 unit black squares on a white
background, as produced by typical QR SVG generators) into a single
long horizontal "strip" SVG: one box per QR module, laid out left to
right, row by row (row-major order), colored black or white.

This is the "long line of just black and white pixels" representation.

Usage:
    python3 qr_to_strip.py input_qr.svg output_strip.svg [--box-size 10]
"""

import re
import sys
import argparse


def parse_qr_svg(svg_text):
    """
    Parse a QR SVG of the form produced by common QR libraries:
      - a white background rect
      - a single <path> containing one
        "M{x},{y}l4,0 0,4 -4,0 0,-4z" subpath per BLACK module

    Returns:
        grid: 2D list of 0/1 (1 = black) sized [rows][cols]
        module_size: the size of one module in original SVG units (e.g. 4)
        quiet_zone: number of quiet-zone modules surrounding the code (e.g. 1)
    """
    # Get the overall SVG pixel size (assumes square, e.g. width="156px")
    width_match = re.search(r'width="(\d+)', svg_text)
    if not width_match:
        raise ValueError("Could not find SVG width")
    svg_size = int(width_match.group(1))

    # Find all black-module top-left coordinates from the path data.
    # Each module subpath looks like: M4,4l4,0 0,4 -4,0 0,-4z
    coords = re.findall(r'M(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)l(-?\d+(?:\.\d+)?),0', svg_text)
    if not coords:
        raise ValueError("Could not find any module path data in the SVG")

    xs = [float(x) for x, y, _ in coords]
    ys = [float(y) for x, y, _ in coords]
    module_size = abs(float(coords[0][2]))  # the 'l4,0' step length

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Quiet zone = how many modules of white border surround the code.
    # The code's own modules start at min_x; modules are module_size apart.
    quiet_zone = round(min_x / module_size)

    # Total modules across (including quiet zone on both sides)
    total_modules = round(svg_size / module_size)

    # Build grid of all white, then mark black modules
    grid = [[0] * total_modules for _ in range(total_modules)]
    for x, y, _ in coords:
        col = round(float(x) / module_size)
        row = round(float(y) / module_size)
        grid[row][col] = 1

    return grid, module_size, quiet_zone, total_modules


def flatten_grid(grid):
    """Flatten a 2D grid into a single row-major list of 0/1 values."""
    flat = []
    for row in grid:
        flat.extend(row)
    return flat


def build_strip_svg(flat_pixels, box_size=10):
    """
    Build an SVG showing the flattened pixel sequence as a single long
    horizontal strip of black/white boxes, one box per pixel.
    """
    n = len(flat_pixels)
    width = n * box_size
    height = box_size

    parts = []
    parts.append(
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}px" height="{height}px" '
        f'viewBox="0 0 {width} {height}" preserveAspectRatio="xMinYMin meet">'
    )
    # White background
    parts.append(f'<rect width="100%" height="100%" fill="#fff"/>')

    # Black boxes only (white is just background, so we only draw black cells)
    path_cmds = []
    for i, val in enumerate(flat_pixels):
        if val:
            x = i * box_size
            path_cmds.append(
                f'M{x},0l{box_size},0 0,{box_size} -{box_size},0 0,-{box_size}z'
            )
    if path_cmds:
        parts.append(f'<path d="{" ".join(path_cmds)}" stroke="transparent" fill="#000"/>')

    parts.append('</svg>')
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_svg", help="Path to the input QR code SVG")
    parser.add_argument("output_svg", help="Path to write the output strip SVG")
    parser.add_argument(
        "--box-size", type=int, default=10,
        help="Size (in px/units) of each box in the output strip (default: 10)"
    )
    args = parser.parse_args()

    with open(args.input_svg, "r") as f:
        svg_text = f.read()

    grid, module_size, quiet_zone, total_modules = parse_qr_svg(svg_text)
    flat = flatten_grid(grid)

    strip_svg = build_strip_svg(flat, box_size=args.box_size)

    with open(args.output_svg, "w") as f:
        f.write(strip_svg)

    print(f"Parsed grid: {total_modules}x{total_modules} modules "
          f"(quiet zone: {quiet_zone} modules, module size: {module_size}px)")
    print(f"Flattened to {len(flat)} pixels ({sum(flat)} black, {len(flat) - sum(flat)} white)")
    print(f"Wrote strip SVG to: {args.output_svg}")

    # Also print metadata needed to reconstruct the grid later, in case
    # the user wants to hardcode it instead of re-detecting it.
    print(f"Metadata for reconstruction -> total_modules={total_modules}, "
          f"module_size={module_size}, quiet_zone={quiet_zone}")


if __name__ == "__main__":
    main()
