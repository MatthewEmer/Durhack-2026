#!/usr/bin/env python3
"""Render a chess position from FEN using the custom piece marker bitmaps."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from chess_fen import load_markers


PIECE_MARKER_INDEX = {symbol: index for index, symbol in enumerate("kqrbnpKQRBNP")}


def parse_fen_board(fen: str) -> list[list[str | None]]:
    placement = fen.split()[0]
    ranks = placement.split("/")
    if len(ranks) != 8:
        raise ValueError("FEN must contain exactly 8 ranks")

    board: list[list[str | None]] = []
    for rank in ranks:
        squares: list[str | None] = []
        for character in rank:
            if character.isdigit() and character in "12345678":
                squares.extend([None] * int(character))
            elif character in PIECE_MARKER_INDEX:
                squares.append(character)
            else:
                raise ValueError(f"invalid FEN piece or empty-square count: {character!r}")
        if len(squares) != 8:
            raise ValueError(f"FEN rank {rank!r} contains {len(squares)} squares, expected 8")
        board.append(squares)
    return board


def render_position(
    fen: str,
    marker_file: Path = Path("custom_markers.csv"),
    board_size: int = 960,
    marker_fraction: float = 0.5,
    rotation: int = 0,
) -> np.ndarray:
    if board_size < 8:
        raise ValueError("board size must be at least 8 pixels")
    if not 0.1 <= marker_fraction <= 1.0:
        raise ValueError("marker fraction must be between 0.1 and 1.0")
    if rotation not in range(4):
        raise ValueError("rotation must be one of 0, 1, 2, or 3")

    board = parse_fen_board(fen)
    patterns = load_markers(marker_file)
    image = np.full((board_size, board_size, 3), 255, dtype=np.uint8)

    for row in range(8):
        top = row * board_size // 8
        bottom = (row + 1) * board_size // 8
        for column in range(8):
            left = column * board_size // 8
            right = (column + 1) * board_size // 8
            colour = 232 if (row + column) % 2 == 0 else 96
            image[top:bottom, left:right] = colour

            piece = board[row][column]
            if piece is None:
                continue
            pattern = np.asarray(patterns[PIECE_MARKER_INDEX[piece]], dtype=np.uint8)
            pattern = np.rot90(pattern, rotation)
            marker = np.where(pattern == 1, 0, 255).astype(np.uint8)
            marker_size = max(1, int(min(right - left, bottom - top) * marker_fraction))
            marker = cv2.resize(marker, (marker_size, marker_size), interpolation=cv2.INTER_NEAREST)
            marker_left = left + (right - left - marker_size) // 2
            marker_top = top + (bottom - top - marker_size) // 2
            image[marker_top:marker_top + marker_size, marker_left:marker_left + marker_size] = cv2.cvtColor(
                marker, cv2.COLOR_GRAY2BGR
            )
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fen", help="FEN string; only the piece-placement field is rendered")
    parser.add_argument("output", type=Path, help="output PNG path")
    parser.add_argument("-m", "--markers", type=Path, default=Path("custom_markers.csv"))
    parser.add_argument("--size", type=int, default=960, help="board width and height in pixels")
    parser.add_argument("--marker-fraction", type=float, default=0.5,
                        help="marker width as a fraction of a board square")
    parser.add_argument("--rotation", type=int, choices=range(4), default=0,
                        help="rotate every marker by 90-degree turns")
    args = parser.parse_args()

    try:
        image = render_position(args.fen, args.markers, args.size,
                                args.marker_fraction, args.rotation)
        if not cv2.imwrite(str(args.output), image):
            raise OSError(f"could not write image: {args.output}")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())