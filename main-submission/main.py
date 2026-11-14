import sys

sys.path.append('../aruco')

## Importing files.

from boardGenerator import ChessBoard
from boardGenerator import defaultBoardState
from mapping import WordstoFensConverter
from inputOutputFormatting import *
from chess_fen import decode_image

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
    imgs = GetImgs()
    words=[]
    fens=[]
    for img in imgs:
        fen = decode_image(img)
        fens.append(fen)
        words.append(converter.FenToWord(fen))
##


## Outputting the result.

board = ChessBoard(words, 8, 8)
    
boardStates = []
for i in range(3):
    if fens[i] in fenList:
        boardStates.append(board.FentoBoardstate(fens[i]))
    else:
        boardStates.append(defaultBoardState)

board.DrawBoards(boardStates)

##