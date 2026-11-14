import unittest
from pathlib import Path

import cv2
import numpy as np

from chess_fen import find_grid_detections, load_markers, make_fen
from generate_chess_position import render_position


MARKER_FILE = Path(__file__).with_name("custom_markers.csv")
BOARD_SIZE = 960
SQUARE_SIZE = BOARD_SIZE // 8


class ChessFenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patterns = load_markers(MARKER_FILE)

    def render_board(self, placements, rotations=None):
        image = np.full((BOARD_SIZE, BOARD_SIZE, 3), 255, dtype=np.uint8)
        for row in range(8):
            for column in range(8):
                colour = 232 if (row + column) % 2 == 0 else 96
                image[
                    row * SQUARE_SIZE : (row + 1) * SQUARE_SIZE,
                    column * SQUARE_SIZE : (column + 1) * SQUARE_SIZE,
                ] = colour

        rotations = rotations or {}
        for (row, column), marker_id in placements.items():
            pattern = np.asarray(self.patterns[marker_id], dtype=np.uint8)
            pattern = np.rot90(pattern, rotations.get((row, column), 0))
            marker = np.where(pattern == 1, 0, 255).astype(np.uint8)
            marker = cv2.resize(marker, (80, 80), interpolation=cv2.INTER_NEAREST)
            left = column * SQUARE_SIZE + 20
            top = row * SQUARE_SIZE + 20
            image[top : top + 80, left : left + 80] = cv2.cvtColor(
                marker, cv2.COLOR_GRAY2BGR
            )
        return image

    def decode(self, image, board_corners=None):
        if board_corners is None:
            board_corners = np.array(
                [[0, 0], [BOARD_SIZE, 0], [BOARD_SIZE, BOARD_SIZE], [0, BOARD_SIZE]],
                dtype=np.float32,
            )
        detections = find_grid_detections(image, self.patterns, board_corners, 12)
        return make_fen(image, detections, board_corners)

    @staticmethod
    def expected_fen(rows):
        ranks = []
        for row in rows:
            empty = 0
            rank = ""
            for symbol in row:
                if symbol == ".":
                    empty += 1
                else:
                    if empty:
                        rank += str(empty)
                        empty = 0
                    rank += symbol
            if empty:
                rank += str(empty)
            ranks.append(rank)
        return "/".join(ranks) + " w - - 0 1"

    def test_empty_board(self):
        image = self.render_board({})
        self.assertEqual(self.decode(image), "8/8/8/8/8/8/8/8 w - - 0 1")

    def test_standard_starting_position(self):
        placements = {}
        for column, marker_id in enumerate((8, 10, 9, 7, 6, 9, 10, 8)):
            placements[(0, column)] = marker_id
            placements[(1, column)] = 11
        for column, marker_id in enumerate((2, 4, 3, 1, 0, 3, 4, 2)):
            placements[(6, column)] = 5
            placements[(7, column)] = marker_id
        expected = self.expected_fen([
            "RNBQKBNR", "PPPPPPPP", "........", "........",
            "........", "........", "pppppppp", "rnbqkbnr",
        ])
        self.assertEqual(self.decode(self.render_board(placements)), expected)

    def test_all_marker_types_and_rotations(self):
        placements = {
            (row, column): offset + column
            for row, offset in ((0, 0), (7, 6))
            for column in range(6)
        }
        rotations = {(row, column): (row + column) % 4 for row, column in placements}
        expected_rows = ["kqrbnp2"] + ["........"] * 6 + ["KQRBNP2"]
        self.assertEqual(
            self.decode(self.render_board(placements, rotations)),
            self.expected_fen(expected_rows),
        )

    def test_sparse_mixed_position(self):
        placements = {
            (0, 4): 6,
            (2, 3): 3,
            (3, 5): 11,
            (4, 2): 0,
            (5, 6): 8,
            (7, 7): 5,
        }
        expected_rows = [
            "4K3", "8", "3b4", "5P2", "2k5", "6R1", "8", "7p",
        ]
        self.assertEqual(self.decode(self.render_board(placements)), self.expected_fen(expected_rows))

    def test_perspective_board(self):
        placements = {
            (0, 0): 0, (1, 1): 7, (2, 2): 1, (3, 3): 8,
            (4, 4): 2, (5, 5): 9, (6, 6): 3, (7, 7): 10,
        }
        source = np.array([[0, 0], [BOARD_SIZE, 0], [BOARD_SIZE, BOARD_SIZE], [0, BOARD_SIZE]], dtype=np.float32)
        destination = np.array([[70, 40], [1060, 20], [1100, 1010], [30, 1040]], dtype=np.float32)
        transform = cv2.getPerspectiveTransform(source, destination)
        image = cv2.warpPerspective(self.render_board(placements), transform, (1130, 1080), borderValue=(255, 255, 255))
        expected_rows = ["k7", "1Q6", "2q5", "3R4", "4r3", "5B2", "6b1", "7N"]
        self.assertEqual(self.decode(image, destination), self.expected_fen(expected_rows))

    def test_fen_generator_round_trip(self):
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        image = render_position(fen, MARKER_FILE)
        self.assertEqual(
            self.decode(image),
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w - - 0 1",
        )


if __name__ == "__main__":
    unittest.main()