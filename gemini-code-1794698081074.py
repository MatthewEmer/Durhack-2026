#!/usr/bin/env python3
"""Detect custom 9x9 chess-piece markers in a photograph and print FEN.

The marker file contains one 9x9 bitmap per line, encoded row-by-row as hex.
The first six markers are black pieces (k, q, r, b, n, p); the last six are
the corresponding white pieces (K, Q, R, B, N, P).
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

MARKER_SIZE = 9
CELL_COUNT = MARKER_SIZE * MARKER_SIZE
PIECE_SYMBOLS = "kqrbnpKQRBNP"
DEFAULT_MARKER_FILE = Path(__file__).with_name("data-files") / "custom_markers.csv"

_TEMPLATE_CACHE: dict[bytes, tuple[np.ndarray, np.ndarray]] = {}


@dataclass(frozen=True)
class Detection:
    symbol: str
    center: tuple[float, float]
    corners: np.ndarray
    score: int


def load_markers(path: Path) -> np.ndarray:
    """Load 12 9x9 binary marker templates as a (12, 9, 9) uint8 array."""
    patterns: list[list[list[int]]] = []
    with path.open(newline="", encoding="utf-8") as marker_file:
        for line_num, row in enumerate(csv.reader(marker_file), start=1):
            if not row or not row[0].strip() or row[0].strip().startswith("#"):
                continue
            raw = row[0].strip()
            value = raw.lower().removeprefix("0x")
            try:
                number = int(value, 16)
            except ValueError as exc:
                raise ValueError(f"{path}:{line_num}: invalid hex {raw!r}") from exc

            if number < 0 or number.bit_length() > CELL_COUNT:
                raise ValueError(f"{path}:{line_num}: marker {raw!r} exceeds 9x9 bits")

            bits = format(number, f"0{CELL_COUNT}b")
            patterns.append([
                [int(ch) for ch in bits[r * MARKER_SIZE : (r + 1) * MARKER_SIZE]]
                for r in range(MARKER_SIZE)
            ])

    if len(patterns) != len(PIECE_SYMBOLS):
        raise ValueError(f"expected {len(PIECE_SYMBOLS)} markers in {path}, found {len(patterns)}")

    return np.asarray(patterns, dtype=np.uint8)


def order_corners(points: np.ndarray | list) -> np.ndarray:
    """Order 4 quadrilateral vertices clockwise starting from top-left."""
    pts = np.asarray(points, dtype=np.float32).reshape(4, 2)
    centroid = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
    pts = pts[np.argsort(angles)]
    # Rotate so top-left (smallest x + y) is index 0
    tl_idx = int(np.argmin(pts.sum(axis=1)))
    return np.roll(pts, -tl_idx, axis=0)


def _get_rotated_templates(patterns: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (48, 81) flattened templates and corresponding marker IDs."""
    key = patterns.tobytes()
    cached = _TEMPLATE_CACHE.get(key)
    if cached is not None:
        return cached

    templates = []
    marker_ids = []
    for marker_id, pattern in enumerate(patterns):
        for turns in range(4):
            templates.append(np.rot90(pattern, turns).reshape(-1))
            marker_ids.append(marker_id)

    result = (np.asarray(templates, dtype=np.uint8), np.asarray(marker_ids, dtype=np.int32))
    _TEMPLATE_CACHE[key] = result
    return result


def identify_marker(
    cell_bits: np.ndarray, patterns: np.ndarray, max_errors: int
) -> tuple[str, int] | None:
    """Match a 9x9 binary grid against all 4 rotations of the 12 piece markers."""
    templates, marker_ids = _get_rotated_templates(patterns)
    observed = np.asarray(cell_bits, dtype=np.uint8).reshape(1, CELL_COUNT)

    # Vectorized Hamming distance across all 48 orientations at once
    distances = np.count_nonzero(templates != observed, axis=1)
    best_idx = int(np.argmin(distances))
    best_score = int(distances[best_idx])

    if best_score > max_errors:
        return None
    return PIECE_SYMBOLS[int(marker_ids[best_idx])], best_score


def sample_marker_patch(
    gray: np.ndarray, corners: np.ndarray, patterns: np.ndarray, max_errors: int
) -> tuple[str, int] | None:
    """Warp a quadrilateral to 36x36, binarize, and identify the 9x9 marker."""
    warp_size = MARKER_SIZE * 4  # Oversample 4x to prevent single-pixel aliasing
    dst = np.array(
        [[0, 0], [warp_size, 0], [warp_size, warp_size], [0, warp_size]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(corners, dst)
    warped = cv2.warpPerspective(gray, matrix, (warp_size, warp_size), flags=cv2.INTER_AREA)
    _, thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Downsample each 4x4 cell block by majority vote (> 127)
    cells = (thresh.reshape(MARKER_SIZE, 4, MARKER_SIZE, 4).mean(axis=(1, 3)) > 127).astype(np.uint8)
    return identify_marker(cells, patterns, max_errors)


def find_quad_markers(
    gray: np.ndarray,
    patterns: np.ndarray,
    max_errors: int,
    min_area: float,
    max_area: float | None = None,
) -> list[Detection]:
    """Detect square marker contours directly in a grayscale image."""
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    binary_images = [
        cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5
        ),
    ]

    detections: list[Detection] = []
    for binary in binary_images:
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or (max_area is not None and area > max_area):
                continue

            perimeter = cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                continue

            corners = order_corners(polygon)
            match = sample_marker_patch(gray, corners, patterns, max_errors)
            if match is None:
                continue

            symbol, score = match
            center = tuple(corners.mean(axis=0).tolist())

            # Deduplicate detections near the same center, keeping the lowest error
            replaced = False
            for idx, existing in enumerate(detections):
                if np.hypot(center[0] - existing.center[0], center[1] - existing.center[1]) < 15.0:
                    if score < existing.score:
                        detections[idx] = Detection(symbol, center, corners, score)
                    replaced = True
                    break
            if not replaced:
                detections.append(Detection(symbol, center, corners, score))

    return detections


def find_grid_detections(
    image: np.ndarray,
    patterns: np.ndarray,
    board_corners: np.ndarray,
    max_errors: int,
) -> list[Detection]:
    """Detect markers on an 8x8 board via contour detection + sliding-window fallback."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    board_size = 960  # 120 px per square
    sq_size = board_size // 8

    board_space = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    rectified_space = np.array(
        [[0, 0], [board_size, 0], [board_size, board_size], [0, board_size]],
        dtype=np.float32,
    )
    image_to_rect = cv2.getPerspectiveTransform(board_corners, rectified_space)
    rect_to_image = cv2.getPerspectiveTransform(rectified_space, board_corners)
    board_to_image = cv2.getPerspectiveTransform(board_space, board_corners)

    rectified = cv2.warpPerspective(gray, image_to_rect, (board_size, board_size))

    # Pass 1: Fast contour-based marker detection in rectified board space
    grid: list[list[Detection | None]] = [[None] * 8 for _ in range(8)]
    quad_hits = find_quad_markers(
        rectified,
        patterns,
        max_errors=max_errors,
        min_area=(sq_size * 0.25) ** 2,
        max_area=(sq_size * 0.95) ** 2,
    )
    for hit in quad_hits:
        col = int(hit.center[0] // sq_size)
        row = int(hit.center[1] // sq_size)
        if 0 <= row < 8 and 0 <= col < 8:
            img_corners = cv2.perspectiveTransform(hit.corners[None, :, :], rect_to_image)[0]
            img_center = tuple(img_corners.mean(axis=0).tolist())
            det = Detection(hit.symbol, img_center, img_corners, hit.score)
            if grid[row][col] is None or det.score < grid[row][col].score:
                grid[row][col] = det

    # Pass 2: Sliding-window fallback only for empty squares (e.g., white markers on white squares)
    fractions = np.arange(0.45, 0.86, 0.08)
    offsets = (-0.06, 0.0, 0.06)

    for row in range(8):
        for col in range(8):
            if grid[row][col] is not None and grid[row][col].score <= 2:
                continue

            best: tuple[int, str, np.ndarray] | None = None
            for fraction in fractions:
                inset = (1.0 - fraction) / 2.0
                for off_x in offsets:
                    for off_y in offsets:
                        left = max(0.0, (col + inset + off_x) / 8.0)
                        top = max(0.0, (row + inset + off_y) / 8.0)
                        right = min(1.0, (col + 1.0 - inset + off_x) / 8.0)
                        bottom = min(1.0, (row + 1.0 - inset + off_y) / 8.0)

                        x0, y0 = round(left * board_size), round(top * board_size)
                        x1, y1 = round(right * board_size), round(bottom * board_size)
                        if x1 - x0 < MARKER_SIZE or y1 - y0 < MARKER_SIZE:
                            continue

                        patch = cv2.resize(
                            rectified[y0:y1, x0:x1],
                            (MARKER_SIZE, MARKER_SIZE),
                            interpolation=cv2.INTER_AREA,
                        )
                        _, bits = cv2.threshold(patch, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        match = identify_marker(bits, patterns, max_errors)
                        if match is not None and (best is None or match[1] < best[0]):
                            square = np.array(
                                [[left, top], [right, top], [right, bottom], [left, bottom]],
                                dtype=np.float32,
                            )
                            best = (match[1], match[0], square)

            if best is not None and (grid[row][col] is None or best[0] < grid[row][col].score):
                img_corners = cv2.perspectiveTransform(best[2][None, :, :], board_to_image)[0]
                img_center = tuple(img_corners.mean(axis=0).tolist())
                grid[row][col] = Detection(best[1], img_center, img_corners, best[0])

    return [det for row in grid for det in row if det is not None]


def board_corners_from_image(image: np.ndarray) -> np.ndarray:
    """Locate the outer 4 corners of the chessboard."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    for finder in (
        lambda: cv2.findChessboardCornersSB(gray, (7, 7), cv2.CALIB_CB_EXHAUSTIVE),
        lambda: cv2.findChessboardCorners(gray, (7, 7)),
    ):
        found, corners = finder()
        if found:
            pts = corners.reshape(7, 7, 2)
            # Ensure top-left is at [0, 0] before extrapolating outer border
            tl, tr, br, bl = pts[0, 0], pts[0, 6], pts[6, 6], pts[6, 0]
            horiz = (tr - tl) / 6.0
            vert = (bl - tl) / 6.0
            return order_corners([
                tl - horiz - vert,
                tr + horiz - vert,
                br + horiz + vert,
                bl - horiz + vert,
            ])

    def largest_quadrilateral(mask: np.ndarray) -> np.ndarray | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        image_area = image.shape[0] * image.shape[1]
        for contour in contours:
            area = cv2.contourArea(contour)
            if not (image_area * 0.1 < area < image_area * 0.98):
                continue
            polygon = cv2.approxPolyDP(contour, 0.03 * cv2.arcLength(contour, True), True)
            if len(polygon) == 4 and cv2.isContourConvex(polygon):
                candidates.append((area, polygon))
        if candidates:
            return order_corners(max(candidates, key=lambda c: c[0])[1])
        return None

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    neutral = (hsv[:, :, 1] < 70).astype(np.uint8) * 255
    neutral = cv2.morphologyEx(neutral, cv2.MORPH_CLOSE, np.ones((21, 21), dtype=np.uint8))
    corners = largest_quadrilateral(neutral)
    if corners is not None:
        return corners

    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    corners = largest_quadrilateral(thresholded)
    if corners is not None:
        return corners

    raise ValueError("could not find the chessboard; pass --board-corners TL TR BR BL")


def parse_corners(values: list[str]) -> np.ndarray:
    try:
        return order_corners([[float(v) for v in pt.split(",")] for pt in values])
    except (ValueError, IndexError) as exc:
        raise argparse.ArgumentTypeError("corners must be four points written as x,y") from exc


def make_fen(detections: list[Detection], board_corners: np.ndarray) -> str:
    """Project detected piece centers onto an 8x8 grid and format the FEN placement."""
    target = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    inverse = cv2.getPerspectiveTransform(board_corners, target)

    board: list[list[Detection | None]] = [[None] * 8 for _ in range(8)]
    if detections:
        centers = np.array([[d.center] for d in detections], dtype=np.float32)
        projected = cv2.perspectiveTransform(centers, inverse)[:, 0, :]
        for detection, (x, y) in zip(detections, projected):
            col, row = int(x * 8), int(y * 8)
            if 0 <= row < 8 and 0 <= col < 8:
                current = board[row][col]
                if current is None or detection.score < current.score:
                    board[row][col] = detection

    ranks = []
    for row in board:
        empty = 0
        rank_chars: list[str] = []
        for square in row:
            if square is None:
                empty += 1
            else:
                if empty:
                    rank_chars.append(str(empty))
                    empty = 0
                rank_chars.append(square.symbol)
        if empty:
            rank_chars.append(str(empty))
        ranks.append("".join(rank_chars))

    return "/".join(ranks)


def decode_image(
    image_path: str | Path,
    marker_file: str | Path | None = None,
    board_corners: np.ndarray | None = None,
    min_area: float = 100.0,
    max_errors: int = 10,
    annotated: str | Path | None = None,
) -> str:
    """Decode a chess position from an image path and return its FEN piece placement."""
    image_path = Path(image_path)
    marker_path = Path(marker_file) if marker_file else DEFAULT_MARKER_FILE

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"could not read image: {image_path}")

    patterns = load_markers(marker_path)
    corners = (
        order_corners(board_corners)
        if board_corners is not None
        else board_corners_from_image(image)
    )

    detections = find_grid_detections(image, patterns, corners, max_errors)
    if not detections:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detections = find_quad_markers(gray, patterns, max_errors, min_area)

    if annotated is not None:
        annotated_path = Path(annotated)
        vis = image.copy()
        for det in detections:
            cv2.polylines(vis, [det.corners.astype(np.int32)], True, (0, 200, 0), 2)
            cv2.putText(
                vis,
                f"{det.symbol}({det.score})",
                tuple(map(int, det.center)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
        cv2.polylines(vis, [corners.astype(np.int32)], True, (255, 0, 0), 3)
        annotated_path.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(annotated_path), vis):
            raise OSError(f"could not write annotated image: {annotated_path}")

    return make_fen(detections, corners)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="photograph containing the chessboard")
    parser.add_argument("-m", "--markers", type=Path, default=DEFAULT_MARKER_FILE)
    parser.add_argument(
        "--board-corners",
        nargs=4,
        metavar="X,Y",
        help="board corners in FEN order: TL TR BR BL",
    )
    parser.add_argument("--min-area", type=float, default=100.0)
    parser.add_argument(
        "--max-errors",
        type=int,
        default=10,
        help="maximum differing cells allowed when matching a marker (out of 81)",
    )
    parser.add_argument(
        "--annotated",
        type=Path,
        help="write a diagnostic image with detections and board corners",
    )
    args = parser.parse_args()

    try:
        corners = parse_corners(args.board_corners) if args.board_corners else None
        fen = decode_image(
            args.image,
            args.markers,
            corners,
            args.min_area,
            args.max_errors,
            args.annotated,
        )
        print(fen)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())