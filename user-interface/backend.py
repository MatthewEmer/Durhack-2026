def GetWords():
    print("Enter the phrase")
    phrase = input(": ").lower()
    words = phrase.split(' ')

    for i in range(len(words)):
        words[i] = f'"{words[i]}"'
    return words

def fen_to_boardState(fen):
    boardState = []
    fen_list = fen.split("/")
    for i in range(len(fen_list)):
        spaces = list(fen_list[i])
        line = []
        for j in range(len(spaces)):
            if spaces[j].isnumeric():
                for k in range(int(spaces[j])):
                    line.append(".")
            else:
                line.append(spaces[j])
        boardState.append(line)
    return boardState

fen = "3b3r/1k1p4/pp6/1P3R2/2PP4/1P1K4/7p/7N"
print(fen)
print()
for line in fen_to_boardState(fen):
    print(line)
