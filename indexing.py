import csv

with open("durhack_word_list.csv", mode="r", encoding="utf-8", newline="") as file:
    reader = csv.reader(file)
    words = [row[0].strip() for row in reader if row]
