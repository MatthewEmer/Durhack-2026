import turtle 

screen = turtle.Screen()
pen = turtle.Turtle()


class ChessBoard:
    ## Setting up the class.

    squaresInEachRow:int
    squaresInEachColumn:int

    squareSize:float

    rowOffset:float
    columnOffset:float


    def __init__(self, squareSize=50.0, squaresInEachRow=8, squaresInEachColumn=8):
        self.squareSize = squareSize
        self.squaresInEachRow = squaresInEachRow
        self.squaresInEachColumn = squaresInEachColumn

        self.rowOffset = (float(squaresInEachRow) / 2) * squareSize
        self.columnOffset = (float(squaresInEachColumn) / 2) * squareSize

    ##


    ## Drawing an instance of the board.

    def DrawBoard(self):
        for columnNumber in range(self.squaresInEachColumn):
            pen.up()
            pen.setpos(-self.rowOffset, (self.squareSize * columnNumber) - self.columnOffset)
            pen.down()

            self._DrawCol(columnNumber)

        pen.hideturtle()   


    def _DrawCol(self, columnNumber):
        for rowNumber in range(self.squaresInEachRow):
            if (rowNumber + columnNumber) % 2 == 0:
                pen.fillcolor("black")
            else:
                pen.fillcolor("white")

            pen.begin_fill()
            self._DrawSquare()
            pen.end_fill()


    def _DrawSquare(self):
        for i in range(4):
            pen.forward(self.squareSize)
            pen.left(90)
        pen.forward(self.squareSize)

    ##


screen.setup(600, 600)
pen.speed(0)

chessBoard = ChessBoard()
chessBoard.DrawBoard()