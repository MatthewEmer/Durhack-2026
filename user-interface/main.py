import board as Board
import backend as Backend

words = Backend.GetWords()

chessBoard = Board.ChessBoard(words, 8, 8)

boardStates = [Board.defaultBoardState, Board.defaultBoardState, Board.defaultBoardState]
chessBoard.DrawBoards(boardStates)