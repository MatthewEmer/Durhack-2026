import turtle 

screen = turtle.Screen()
pen = turtle.Turtle()


def DrawBoard(squareSize):
    offset = 4 * squareSize

    for col in range(8):
        pen.up()
        pen.setpos(-offset, (squareSize * col) - offset)
        pen.down()

        DrawCol(col, squareSize)

    pen.hideturtle()   


def DrawCol(col, squareSize):
    for row in range(8):
        if (col + row) % 2 == 0:
            pen.fillcolor("black")
        else:
            pen.fillcolor("white")

        pen.begin_fill()
        DrawSquare(squareSize)
        pen.end_fill()


def DrawSquare(size):
    for i in range(4):
        pen.forward(size)
        pen.left(90)
    pen.forward(size)


screen.setup(600, 600)
pen.speed(0)

DrawBoard(50)
input("")