#!/usr/bin/env python3
"""Create a camera-like photograph of a printed marker chessboard."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from generate_chess_position import render_position


def add_print_texture(board: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    height, width = board.shape[:2]
    fine_noise = rng.normal(0, 1.8, (height, width, 1)).astype(np.float32)
    paper_shading = cv2.GaussianBlur(
        rng.normal(0, 1, (height, width)).astype(np.float32), (0, 0), 55
    )[..., None] * 7.0
    textured = board.astype(np.float32) + fine_noise + paper_shading
    return np.clip(textured, 0, 255).astype(np.uint8)


def make_test_image(
    fen: str,
    output_size: tuple[int, int] = (1400, 1050),
    seed: int = 2026,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    board = render_position(fen, board_size=960, marker_fraction=0.58)
    board = add_print_texture(board, seed)

    width, height = output_size
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    desk = np.zeros_like(canvas, dtype=np.float32)
    desk[:] = (116, 91, 67)
    desk += rng.normal(0, 5, desk.shape[:2] + (1,))
    canvas[:] = np.clip(desk, 0, 255).astype(np.uint8)

    source = np.array([[0, 0], [959, 0], [959, 959], [0, 959]], dtype=np.float32)
    destination = np.array(
        [[175, 105], [1190, 72], [1280, 890], [92, 940]], dtype=np.float32
    )
    transform = cv2.getPerspectiveTransform(source, destination)

    paper_mask = np.full((960, 960), 255, dtype=np.uint8)
    warped_mask = cv2.warpPerspective(paper_mask, transform, (width, height))
    shadow = cv2.GaussianBlur(warped_mask, (0, 0), 22)
    shadow_layer = np.zeros_like(canvas)
    shadow_layer[:] = (25, 18, 12)
    shadow_alpha = (shadow.astype(np.float32) / 255.0 * 0.42)[..., None]
    canvas = (canvas.astype(np.float32) * (1 - shadow_alpha)
              + shadow_layer.astype(np.float32) * shadow_alpha).astype(np.uint8)

    warped_board = cv2.warpPerspective(board, transform, (width, height))
    alpha = (warped_mask.astype(np.float32) / 255.0)[..., None]
    canvas = (canvas.astype(np.float32) * (1 - alpha)
              + warped_board.astype(np.float32) * alpha).astype(np.uint8)

    # A small amount of camera softness and chroma noise makes the print less synthetic.
    canvas = cv2.GaussianBlur(canvas, (3, 3), 0.45)
    canvas = np.clip(
        canvas.astype(np.int16) + rng.normal(0, 1.5, canvas.shape).astype(np.int16),
        0,
        255,
    ).astype(np.uint8)
    return canvas, destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--fen",
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        help="piece placement to print on the board",
    )
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    image, _ = make_test_image(args.fen, seed=args.seed)
    if not cv2.imwrite(str(args.output), image):
        raise OSError(f"could not write {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())