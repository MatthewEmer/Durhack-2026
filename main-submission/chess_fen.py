#!/usr/bin/env python3
"""Detect the custom 9x9 chess-piece markers in a photograph and print FEN.

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


MARKER_SIZE = 9
PIECE_SYMBOLS = "kqrbnpKQRBNP"


@dataclass
class Detection:
    symbol: str
    center: tuple[float, float]
    corners: object
    score: int


def load_markers(path: Path) -> list[list[list[int]]]:
    patterns: list[list[list[int]]] = []
    with path.open(newline="", encoding="utf-8") as marker_file:
        for row in csv.reader(marker_file):
            if not row or not row[0].strip():
                continue
            value = row[0].strip().lower().removeprefix("0x")
            number = int(value, 16)
            bits = format(number, f"0{MARKER_SIZE * MARKER_SIZE}b")
            if len(bits) != MARKER_SIZE * MARKER_SIZE:
                raise ValueError(f"{path}: marker {row[0]!r} is not a 9x9 bitmap")
            patterns.append(
                [list(map(int, bits[row * MARKER_SIZE : (row + 1) * MARKER_SIZE]))
                 for row in range(MARKER_SIZE)]
            )

    if len(patterns) != len(PIECE_SYMBOLS):
        raise ValueError(f"expected 12 markers in {path}, found {len(patterns)}")
    return patterns


def order_corners(points):
    import numpy as np

    points = np.asarray(points, dtype="float32").reshape(4, 2)
    sums = points.sum(axis=1)
    differences = points[:, 0] - points[:, 1]
    return np.array(
        [points[sums.argmin()], points[differences.argmax()],
         points[sums.argmax()], points[differences.argmin()]],
        dtype="float32",
    )


def rotated(pattern, turns: int):
    import numpy as np

    return np.rot90(np.asarray(pattern, dtype="uint8"), turns)


def identify_marker(cell_bits, patterns: list[list[list[int]]], max_errors: int):
    import numpy as np

    observed = np.asarray(cell_bits, dtype="uint8")
    candidates = []
    for marker_id, pattern in enumerate(patterns):
        for turns in range(4):
            rotated_pattern = rotated(pattern, turns)
            for inverted in (False, True):
                expected = 1 - rotated_pattern if inverted else rotated_pattern
                score = int(np.count_nonzero(observed != expected))
                candidates.append((score, marker_id))
    score, marker_id = min(candidates)
    if score > max_errors:
        return None
    return PIECE_SYMBOLS[marker_id], score


def sample_marker(gray, corners, patterns, max_errors):
    import cv2
    import numpy as np
    import numpy as np

    destination = np.array(
        [[0, 0], [MARKER_SIZE, 0], [MARKER_SIZE, MARKER_SIZE], [0, MARKER_SIZE]],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(corners, destination)
    warped = cv2.warpPerspective(gray, matrix, (MARKER_SIZE, MARKER_SIZE))
    _, thresholded = cv2.threshold(warped, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    result = identify_marker(thresholded, patterns, max_errors)
    if result is None:
        # A marker may be printed with the opposite foreground convention.
        thresholded = 1 - thresholded
        result = identify_marker(thresholded, patterns, max_errors)
    return result


def find_marker_detections(image, patterns, max_errors, min_area):
    import cv2
    import numpy as np

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    binary_images = [
        cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 31, 5),
    ]
    detections: list[Detection] = []
    for binary in binary_images:
        contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            perimeter = cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, 0.05 * perimeter, True)
            if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                continue
            corners = order_corners(polygon.reshape(4, 2))
            marker = sample_marker(gray, corners, patterns, max_errors)
            if marker is None:
                continue
            center = tuple(np.mean(corners, axis=0).tolist())
            if any(np.linalg.norm(np.asarray(center) - np.asarray(old.center)) < 12
                   for old in detections):
                continue
            detections.append(Detection(marker[0], center, corners, marker[1]))
    return detections


def find_grid_detections(image, patterns, board_corners, max_errors):
    import cv2
    import numpy as np

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    board_space = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype="float32")
    board_to_image = cv2.getPerspectiveTransform(board_space, board_corners)
    detections: list[Detection] = []
    for row in range(8):
        for column in range(8):
            best = None
            for fraction in (0.5, 0.55, 2.0 / 3.0, 0.75, 0.85, 0.95):
                inset = (1.0 - fraction) / 2.0
                left = (column + inset) / 8.0
                top = (row + inset) / 8.0
                right = (column + 1.0 - inset) / 8.0
                bottom = (row + 1.0 - inset) / 8.0
                square = np.array(
                    [[left, top], [right, top], [right, bottom], [left, bottom]],
                    dtype="float32",
                )
                corners = cv2.perspectiveTransform(square[None, :, :], board_to_image)[0]
                marker_matrix = cv2.getPerspectiveTransform(
                    corners,
                    np.array([[0, 0], [90, 0], [90, 90], [0, 90]], dtype="float32"),
                )
                warped = cv2.warpPerspective(gray, marker_matrix, (90, 90))
                warped = cv2.resize(warped, (9, 9), interpolation=cv2.INTER_AREA)
                _, bits = cv2.threshold(warped, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                match = identify_marker(bits, patterns, max_errors)
                if match is not None and (best is None or match[1] < best[0]):
                    best = (match[1], match[0], corners)
            if best is not None:
                center = tuple(np.mean(best[2], axis=0).tolist())
                detections.append(Detection(best[1], center, best[2], best[0]))
    return detections


def board_corners_from_image(image):
    import cv2
    import numpy as np

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    for finder in (
        lambda: cv2.findChessboardCornersSB(gray, (7, 7), cv2.CALIB_CB_EXHAUSTIVE),
        lambda: cv2.findChessboardCorners(gray, (7, 7)),
    ):
        found, corners = finder()
        if found:
            points = corners.reshape(-1, 2)
            inner = [points[0], points[6], points[-1], points[-7]]
            horizontal = (inner[1] - inner[0]) / 6
            vertical = (inner[3] - inner[0]) / 6
            return order_corners([
                inner[0] - horizontal - vertical,
                inner[1] + horizontal - vertical,
                inner[2] + horizontal + vertical,
                inner[3] - horizontal + vertical,
            ])

    def largest_quadrilateral(mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        image_area = image.shape[0] * image.shape[1]
        for contour in contours:
            area = cv2.contourArea(contour)
            polygon = cv2.approxPolyDP(contour, 0.03 * cv2.arcLength(contour, True), True)
            if (len(polygon) == 4 and cv2.isContourConvex(polygon)
                    and image_area * 0.1 < area < image_area * 0.98):
                candidates.append((area, polygon.reshape(4, 2)))
        if candidates:
            return order_corners(max(candidates, key=lambda candidate: candidate[0])[1])
        return None

    # Printed boards are usually neutral gray/white, while their surroundings
    # have more colour. Closing this mask bridges the alternating board squares.
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    neutral = (hsv[:, :, 1] < 70).astype("uint8") * 255
    neutral = cv2.morphologyEx(neutral, cv2.MORPH_CLOSE, np.ones((21, 21), dtype="uint8"))
    corners = largest_quadrilateral(neutral)
    if corners is not None:
        return corners

    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    corners = largest_quadrilateral(thresholded)
    if corners is not None:
        return corners
    raise ValueError("could not find the chessboard; pass --board-corners TL TR BR BL")


def parse_corners(values):
    import numpy as np

    try:
        return order_corners([[float(value) for value in point.split(",")] for point in values])
    except (ValueError, IndexError):
        raise argparse.ArgumentTypeError("corners must be four points written as x,y")


def make_fen(image, detections, board_corners):
    import cv2
    import numpy as np

    source = np.asarray(board_corners, dtype="float32")
    target = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype="float32")
    inverse = cv2.getPerspectiveTransform(source, target)
    board = [[None for _ in range(8)] for _ in range(8)]
    for detection in detections:
        point = cv2.perspectiveTransform(
            np.asarray([[detection.center]], dtype="float32"), inverse
        )[0, 0]
        column, row = int(point[0] * 8), int(point[1] * 8)
        if 0 <= row < 8 and 0 <= column < 8:
            current = board[row][column]
            if current is None or detection.score < current.score:
                board[row][column] = detection

    ranks = []
    for row in board:
        empty = 0
        rank = ""
        for square in row:
            if square is None:
                empty += 1
            else:
                if empty:
                    rank += str(empty)
                    empty = 0
                rank += square.symbol
        if empty:
            rank += str(empty)
        ranks.append(rank)
    return "/".join(ranks)


def decode_image(
    image_path: str | Path,
    marker_file: str | Path | None = None,
    board_corners=None,
    min_area: float = 100.0,
    max_errors: int = 12,
    annotated: str | Path | None = None,
) -> str:
    """Decode a chess position from an image path and return its FEN string.

    ``board_corners`` may contain four points in TL, TR, BR, BL order. If it is
    omitted, the board boundary is detected automatically.
    """
    import cv2
    import numpy as np

    image_path = Path(image_path)
    marker_path = "./main-submission/data-files/custom_markers.csv"
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"could not read image: {image_path}")
    patterns = load_markers(marker_path)
    corners = board_corners if board_corners is not None else board_corners_from_image(image)
    corners = np.asarray(corners, dtype="float32")
    detections = find_grid_detections(image, patterns, corners, max_errors)
    if not detections:
        detections = find_marker_detections(image, patterns, max_errors, min_area)

    if annotated is not None:
        annotated_path = Path(annotated)
        for detection in detections:
            cv2.polylines(image, [detection.corners.astype("int32")], True, (0, 180, 0), 2)
            cv2.putText(image, detection.symbol, tuple(map(int, detection.center)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.polylines(image, [corners.astype("int32")], True, (255, 0, 0), 3)
        annotated_path.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(annotated_path), image):
            raise OSError(f"could not write annotated image: {annotated_path}")

    return make_fen(image, detections, corners)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="photograph containing the chessboard")
    parser.add_argument("-m", "--markers", type=Path,
                        default=Path(__file__).with_name("custom_markers.csv"))
    parser.add_argument("--board-corners", nargs=4, metavar="X,Y",
                        help="board corners in FEN order: TL TR BR BL")
    parser.add_argument("--min-area", type=float, default=100.0)
    parser.add_argument("--max-errors", type=int, default=12,
                        help="maximum differing cells allowed when matching a marker")
    parser.add_argument("--annotated", type=Path,
                        help="write a diagnostic image with detections and board corners")
    args = parser.parse_args()

    try:
        import cv2
    except ImportError:
        print("OpenCV is required: python -m pip install opencv-python", file=sys.stderr)
        return 2

    try:
        corners = parse_corners(args.board_corners) if args.board_corners else None
        print(decode_image(args.image, args.markers, corners, args.min_area,
                           args.max_errors, args.annotated))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())