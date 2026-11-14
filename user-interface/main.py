import board as Board
import backend as Backend
import mapping as Mapping

words = Backend.GetWords()

fens = []
for word in words:
    fen = Mapping.fen_from_word(word[1:-1])
    if fen == -1:
        raise ValueError("Word not in list!")
    fens.append(fen)

chessBoard = Board.ChessBoard(words, 8, 8)

boardStates = [Board.defaultBoardState, Board.defaultBoardState, Board.defaultBoardState]
chessBoard.DrawBoards(boardStates)