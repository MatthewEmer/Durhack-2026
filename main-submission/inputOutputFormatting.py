def GetWords():
    wordsFilePath = "./main-submission/data-files/durham_word_list.csv"

    print("Enter the phrase you want to send.")
    phrase = input(": ").lower()
    words = phrase.split(' ')

    return words


def GetFens():
    fensFilePath = "./main-submission/data-files/fen_list.txt"

    print("Enter the fens you want to send, separated by spaces.")
    userInput = input(": ")
    fens = userInput.split(' ')

    return fens


def GetImgs():
    imageFilePath = "./main-submission/images/"

    print("Enter the images you want to decode, separated by spaces. ")
    userInput = input(": ")
    imgs = userInput.split(' ')

    for i in range(len(imgs)):
        imgs[i] = imageFilePath + imgs[i]
    return imgs


def GetMode():
    modes = ["encode", "decode"]
    userInput = ""
    
    while userInput not in modes:
        print("Do you want to encode or decode?")
        userInput = input(": ").lower() 

    return userInput