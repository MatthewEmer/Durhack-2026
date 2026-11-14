## Importing files.

from boardGenerator import ChessBoard
from boardGenerator import defaultBoardState
from mapping import WordstoFensConverter
from inputOutputFormatting import *

##


## Setup.

converter = WordstoFensConverter("durhack_word_list.csv", "fen_list.txt")
fenList = converter.GetFens()
wordList = converter.GetWords()

mode = GetMode()

##


## Encoding mode.

if mode == "encode":
    words = GetWords()
    fens = []
    for i in range(3):
        fens.append(converter.WordToFen(words[i]))

    print(fens)

##


## Decoding mode.

if mode == "decode":
    fens = GetFens()
    words = []
    for i in range(3):
        words.append(converter.FenToWord(fens[i]))

    print(words)

##


## Outputting the result.

board = ChessBoard(words, 8, 8)
    
boardStates = []
for i in range(3):
    if fens[i] in fenList:
        boardStates.append(board.FenToBoardstate(fens[i]))
    else:
        boardStates.append(defaultBoardState)

board.DrawBoards(boardStates)

##