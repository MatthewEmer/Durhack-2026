## Importing libraries.
 
import csv
import copy

##


## Word to FEN converter class.

class WordstoFensConverter:
    _wordList:list
    _fens:list


    def __init__(self, wordListFile, fensFile):
        with open(wordListFile, mode="r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            self._wordList = [row[0].strip() for row in reader if row]
        with open(fensFile, mode="r", encoding="utf-8") as file:
            self._fens = [line.strip() for line in file if line.strip()]


    def WordToFen(self, word):
        try:
            wordIndex = self._wordList.index(word)
            return self._fens[wordIndex]
        except:
            print("Error", word)
            return ""


    def FenToWord(self, fen):
        try:
            fenIndex = self._fens.index(fen)
            return self._wordList[fenIndex]
        except:
            print("Error", fen)
            return ""


    def GetFens(self): return copy.deepcopy(self._fens)
    def GetWords(self): return copy.deepcopy(self._wordList)

##