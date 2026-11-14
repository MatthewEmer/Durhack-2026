import csv

with open("durhack_word_list.csv", mode="r", encoding="utf-8", newline="") as file:
    reader = csv.reader(file)
    words = [row[0].strip() for row in reader if row]
with open("fen_list.txt", mode="r", encoding="utf-8") as file:
    # .strip() removes the trailing newline (\n) and extra whitespace
    # 'if line.strip()' skips any completely blank lines
    entries = [line.strip() for line in file if line.strip()]