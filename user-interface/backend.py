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

def boardState_to_fen(boardState):
    fen = ""
    for line in boardState:
        subfen = []
        for i in range(len(line)):
            if line[i] != ".":
                subfen.append(line[i])
            else:
                if subfen == []:
                    subfen.append("1")
                elif subfen[-1].isnumeric():
                    subfen[-1] = str(int(subfen[-1])+1)
                else:
                    subfen.append("1")
        fen += "".join(subfen) + "/"
    return fen[:-1]

