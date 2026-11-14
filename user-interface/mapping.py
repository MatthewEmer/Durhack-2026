import csv

def load_data():
    with open("durhack_word_list.csv", mode="r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        words = [row[0].strip() for row in reader if row]
    with open("fen_list.txt", mode="r", encoding="utf-8") as file:
        # .strip() removes the trailing newline (\n) and extra whitespace
        # 'if line.strip()' skips any completely blank lines
        fens = [line.strip() for line in file if line.strip()]

    return (words, fens)

def fen_from_word(word):
    words, fens = load_data()
    try:
        idx = words.index(word)
    except ValueError:
        return -1
    return fens[idx]


def word_from_fen(fen):
    words, fens = load_data()
    try:   
        idx = fens.index(fen)
    except ValueError:
        return -1
    return words[idx]