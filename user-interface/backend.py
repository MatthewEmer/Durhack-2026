def GetWords():
    print("Enter the phrase")
    phrase = input(": ").lower()
    words = phrase.split(' ')

    for i in range(len(words)):
        words[i] = f'"{words[i]}"'
    return words
