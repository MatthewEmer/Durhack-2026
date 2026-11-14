
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Chessboard represented as an 8x8 array
# Uppercase = White pieces
# Lowercase = Black pieces
# "." = Empty square

board = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

# Map characters to chess symbols
pieces = {
    'K': '♔', 'Q': '♕', 'R': '♖',
    'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜',
    'b': '♝', 'n': '♞', 'p': '♟'
}

def draw_board(board):
    fig, ax = plt.subplots(figsize=(8, 8))

    # Draw the squares and pieces
    for row in range(8):
        for col in range(8):

            # Alternate square colours
            colour = '#F0D9B5' if (row + col) % 2 == 0 else '#B58863'

            square = patches.Rectangle(
                (col, 7-row), 1, 1,
                facecolor=colour
            )
            ax.add_patch(square)

            # Get piece from array
            piece = board[row][col]

            # Draw piece if square isn't empty
            if piece != '.':
                ax.text(
                    col + 0.5,
                    7 - row + 0.5,
                    pieces[piece],
                    fontsize=40,
                    ha='center',
                    va='center',
                    color='white' if piece.isupper() else 'black'
                )

    # Set up board coordinates
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_xticks([i + 0.5 for i in range(8)])
    ax.set_yticks([i + 0.5 for i in range(8)])
    ax.set_xticklabels(list('abcdefgh'))
    ax.set_yticklabels(list('87654321'))

    ax.set_aspect('equal')
    ax.tick_params(length=0)
    ax.set_title("Chess Board", fontsize=18, pad=15)

    plt.show()


draw_board(board)