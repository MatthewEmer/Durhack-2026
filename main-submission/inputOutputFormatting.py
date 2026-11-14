def GetWords():
    print("Enter the phrase you want to send.")
    phrase = input(": ").lower()
    words = phrase.split(' ')

    return words


def GetFens():
    print("Enter the fens you want to send, separated by spaces.")
    userInput = input(": ")
    fens = userInput.split(' ')

    return fens


def GetMode():
    modes = ["encode", "decode"]
    userInput = ""
    
    while userInput not in modes:
        print("Do you want to encode or decode?")
        userInput = input(": ").lower() 

    return userInput