
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Chessboard represented as an 8x8 array
# Uppercase = White pieces
# Lowercase = Black pieces
# "." = Empty square

boardState = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

class ChessBoard:
    _pieces = {'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙', 'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'}
    _board:list

    _figure:plt.Figure
    _axes:plt.axes.Axes

    _boardWidth:int
    _boardHeight:int


    def __init__(self, boardWidth, boardHeight):
        self._figure, self._axes = plt.subplots(figsize=(4, 4))
        self._boardWidth = boardWidth
        self._boardHeight = boardHeight


    def DrawBoard(self, boardState):
        for rowNumber in range(self._boardHeight):
            for columnNumber in range(self._boardWidth):
                colour = '#F0D9B5' if (rowNumber + columnNumber) % 2 == 0 else "#C9A07F"

                square = patches.Rectangle((columnNumber, 7 - rowNumber), 1, 1, facecolor=colour)
                self._axes.add_patch(square)

                self._DrawPiece(boardState[rowNumber][columnNumber], rowNumber, columnNumber)

        self._axes.set_xlim(0, 8)
        self._axes.set_ylim(0, 8)
        self._axes.set_xticks([i + 0.5 for i in range(8)])
        self._axes.set_yticks([i + 0.5 for i in range(8)])
        self._axes.set_xticklabels(list('abcdefgh'))
        self._axes.set_yticklabels(list('87654321'))
    
        self._axes.set_aspect('equal')
        self._axes.tick_params(length=0)
        self._axes.set_title("Chess Board", fontsize=18, pad=15)

        plt.show()


    def _DrawPiece(self, piece, rowNumber, columnNumber):
        if piece != ".":
            self._axes.text(columnNumber + 0.5, 7 - rowNumber + 0.5, self._pieces[piece], fontsize=20, ha="center", va="center", color="white" if piece.isupper() else "black")



board = ChessBoard(8, 8)
board.DrawBoard(boardState)