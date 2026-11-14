#!/usr/bin/env python3
"""Generate an A4 print sheet containing three 32-piece marker sets."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from chess_fen import load_markers


A4_WIDTH = 2480
A4_HEIGHT = 3508
STANDARD_SET = "kqrrbbnn" + "p" * 8 + "KQRRBBNN" + "P" * 8
PIECE_SYMBOLS = STANDARD_SET * 3


def put_text(image, text, position, scale=1.0, thickness=2, colour=(25, 25, 25)):
    cv2.putText(image, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, colour, thickness,
                cv2.LINE_AA)


def render_marker(pattern, size: int) -> np.ndarray:
    marker = np.where(np.asarray(pattern, dtype=np.uint8) == 1, 0, 255).astype(np.uint8)
    return cv2.resize(marker, (size, size), interpolation=cv2.INTER_NEAREST)


def marker_sheet(marker_file: Path, width: int = A4_WIDTH, height: int = A4_HEIGHT) -> np.ndarray:
    patterns = load_markers(marker_file)
    marker_indices = {symbol: index for index, symbol in enumerate("kqrbnpKQRBNP")}
    sheet = np.full((height, width, 3), 255, dtype=np.uint8)
    columns = 8
    rows = 12
    board_size = min(width - 260, height - 650)
    marker_size = round(board_size / 12)
    border = 1
    grid_width = columns * marker_size + (columns - 1) * border
    grid_height = rows * marker_size + (rows - 1) * border
    margin_x = 0
    margin_y = 0

    for copy_number, symbol in enumerate(PIECE_SYMBOLS, start=1):
        row, column = divmod(copy_number - 1, columns)
        left = margin_x + column * (marker_size + border)
        top = margin_y + row * (marker_size + border)
        marker = render_marker(patterns[marker_indices[symbol]], marker_size)
        sheet[top:top + marker_size, left:left + marker_size] = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)

    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="output A4 PNG path")
    parser.add_argument("-m", "--markers", type=Path, default=Path("custom_markers.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), marker_sheet(args.markers)):
        raise OSError(f"could not write {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())