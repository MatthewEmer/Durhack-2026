### Importing the libraries.

import matplotlib.pyplot as plt
import matplotlib.patches as patches

###


### Setting default variables as examples.

defaultBoardState = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]
defaultFenString = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
allowedPieceCharacters = "KQRBNPkqrbnp"

###



### Chess board class.

class ChessBoard:
    ## Setup.

    _pieces = {'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙', 'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'}
    _board:list

    _figure:plt.Figure
    _axes:plt.axes.Axes

    _boardWidth:int
    _boardHeight:int
    _titles:list


    def __init__(self, titles, boardWidth, boardHeight):
        self._figure, self._axes = plt.subplots(1, 3, figsize=(12, 4))
        
        self._boardWidth = boardWidth
        self._boardHeight = boardHeight
        
        self._titles = titles

    ##


    ## Drawing the board and pieces.

    def DrawBoards(self, boardStates):
        for boardNumber in range(len(boardStates)):
            boardState = boardStates[boardNumber]
            axis = self._axes[boardNumber]
            title = self._titles[boardNumber]

            for rowNumber in range(self._boardHeight):
                for columnNumber in range(self._boardWidth):
                    colour = '#F0D9B5' if (rowNumber + columnNumber) % 2 == 0 else "#C9A07F"

                    square = patches.Rectangle((columnNumber, 7 - rowNumber), 1, 1, facecolor=colour)
                    axis.add_patch(square)

                    self._DrawPiece(axis, boardState[rowNumber][columnNumber], rowNumber, columnNumber)

            axis.set_xlim(0, 8)
            axis.set_ylim(0, 8)
            axis.set_xticks([i + 0.5 for i in range(8)])
            axis.set_yticks([i + 0.5 for i in range(8)])
            axis.set_xticklabels(list('abcdefgh'))
            axis.set_yticklabels(list('87654321'))

            axis.set_aspect('equal')
            axis.tick_params(length=0)
            axis.set_title(title, fontsize=14, pad=15)

        plt.tight_layout()
        plt.show()


    def _DrawPiece(self, axis, piece, rowNumber, columnNumber):
        if piece != ".":
            axis.text(columnNumber + 0.5, 7 - rowNumber + 0.5, self._pieces[piece], fontsize=20, ha="center", va="center", color="white" if piece.isupper() else "black")

    ##


    ## Converting between FENs and boardstates.

    def FentoBoardstate(self, fen):
        boardState = []
        fenList = fen.split("/")

        for i in range(len(fenList)):
            spaces = list(fenList[i])
            line = []
            for j in range(len(spaces)):
                if spaces[j].isnumeric():
                    for k in range(int(spaces[j])):
                        line.append(".")
                else:
                    line.append(spaces[j])
            boardState.append(line)

        return boardState

    ##
###