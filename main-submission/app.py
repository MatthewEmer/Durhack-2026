import os
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

from mapping import WordstoFensConverter
from chess_fen import decode_image


# --------------------------------------------------
# Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="ChessEncoding",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
WORD_FILE = BASE_DIR / "data-files" / "durhack_word_list.csv"
FEN_FILE = BASE_DIR / "data-files" / "fen_list.txt"
MARKER_FILE = BASE_DIR / "data-files" / "custom_markers.csv"

PIECES = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1120px;
        padding-top: 2.4rem;
        padding-bottom: 3rem;
    }
    .hero {
        padding: 1.5rem 1.6rem;
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 18px;
        margin-bottom: 1.3rem;
        background: linear-gradient(120deg,
            rgba(185,145,95,.13), rgba(100,120,100,.07));
    }
    .hero h1 {
        font-size: 2.5rem;
        letter-spacing: -1.5px;
        margin: 0;
    }
    .hero p {
        color: #888;
        margin: .35rem 0 0 0;
    }
    div[data-testid="stForm"] {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 14px;
        padding: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Backend setup
# --------------------------------------------------

@st.cache_resource
def load_converter():
    if not WORD_FILE.exists():
        raise FileNotFoundError(f"Word list not found: {WORD_FILE}")
    if not FEN_FILE.exists():
        raise FileNotFoundError(f"FEN list not found: {FEN_FILE}")
    return WordstoFensConverter(str(WORD_FILE), str(FEN_FILE))


try:
    converter = load_converter()
    word_list = converter.GetWords()
    fen_list = converter.GetFens()
except Exception as exc:
    st.error(f"Could not load the word/FEN data files: {exc}")
    st.stop()

if len(word_list) != len(fen_list):
    st.error(
        "Your word list and FEN list have different lengths "
        f"({len(word_list)} words, {len(fen_list)} FENs). "
        "Please check that the files are aligned."
    )
    st.stop()

word_to_fen = dict(zip(word_list, fen_list))
fen_to_word = dict(zip(fen_list, word_list))


# --------------------------------------------------
# FEN and chessboard helpers
# --------------------------------------------------

def fen_to_boardstate(fen: str):
    """Expand the piece-placement portion of a FEN into an 8x8 board."""
    ranks = fen.split("/")
    if len(ranks) != 8:
        raise ValueError("The FEN must contain exactly eight ranks.")

    board = []
    for rank in ranks:
        row = []
        for char in rank:
            if char.isdigit():
                count = int(char)
                if count < 1 or count > 8:
                    raise ValueError(f"Invalid empty-square count: {char}")
                row.extend(["."] * count)
            elif char in PIECES:
                row.append(char)
            else:
                raise ValueError(f"Unexpected character in FEN: {char}")

        if len(row) != 8:
            raise ValueError("Each FEN rank must describe exactly eight squares.")
        board.append(row)

    return board


def draw_chessboard(fen: str):
    """Create a Matplotlib chessboard figure from a piece-placement FEN."""
    board = fen_to_boardstate(fen)
    fig, ax = plt.subplots(figsize=(4.2, 4.2))

    light = "#F0D9B5"
    dark = "#B58863"

    for row in range(8):
        for col in range(8):
            square_colour = light if (row + col) % 2 == 0 else dark
            ax.add_patch(
                patches.Rectangle(
                    (col, 7 - row), 1, 1,
                    facecolor=square_colour,
                    edgecolor="none",
                )
            )

            piece = board[row][col]
            if piece != ".":
                ax.text(
                    col + 0.5,
                    7 - row + 0.5,
                    PIECES[piece],
                    fontsize=25,
                    ha="center",
                    va="center",
                    color="#FAFAFA" if piece.isupper() else "#202020",
                )

    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_aspect("equal")
    ax.set_xticks([i + 0.5 for i in range(8)])
    ax.set_yticks([i + 0.5 for i in range(8)])
    ax.set_xticklabels(list("abcdefgh"), fontsize=8)
    ax.set_yticklabels(list("87654321"), fontsize=8)
    ax.tick_params(length=0, pad=4)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout(pad=0.6)
    return fig


def show_result_card(title: str, word: str, fen: str, key: str):
    """Display a word, its FEN, and a board preview."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.subheader(word if word else "Word not found")
        st.code(fen, language=None)

        try:
            fig = draw_chessboard(fen)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        except ValueError as exc:
            st.warning(f"Could not draw this board: {exc}")

        st.download_button(
            "Download FEN",
            data=fen,
            file_name=f"{key}_encoding.fen",
            mime="text/plain",
            key=f"download_{key}",
            use_container_width=True,
        )


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>♟ ChessEncoding</h1>
        <p>A random chess game? More like a secret word...</p>
    </div>
    """,
    unsafe_allow_html=True,
)

mode = st.radio(
    "What would you like to do?",
    ["Encode words", "Decode images"],
    horizontal=True,
    label_visibility="visible",
)

st.divider()


# --------------------------------------------------
# Encode
# --------------------------------------------------

if mode == "Encode words":
    st.header("Encode words")
    st.write("Enter up to three words from the project word list.")

    with st.form("encode_form"):
        entered_words = [
            st.text_input(
                f"Word {index}",
                placeholder="Type a word from the dictionary",
                key=f"encode_word_{index}",
            ).strip()
            for index in range(1, 4)
        ]
        encode_clicked = st.form_submit_button(
            "Encode words",
            type="primary",
            use_container_width=True,
        )

    if encode_clicked:
        words = [word for word in entered_words if word]

        if not words:
            st.warning("Enter at least one word to encode.")
        else:
            unknown_words = [word for word in words if word not in word_to_fen]

            if unknown_words:
                st.error(
                    "These words were not found in the word list: "
                    + ", ".join(unknown_words)
                )
                st.caption(
                    "The lookup currently uses exact matching, including "
                    "capitalisation and spelling."
                )
            else:
                st.success(f"Successfully encoded {len(words)} word(s).")
                columns = st.columns(len(words))

                for index, (column, word) in enumerate(zip(columns, words), start=1):
                    with column:
                        show_result_card(
                            f"Encoding {index}",
                            word,
                            word_to_fen[word],
                            f"encode_{index}",
                        )


# --------------------------------------------------
# Decode
# --------------------------------------------------

else:
    st.header("Decode chessboard images")
    st.write(
        "Upload photographs containing your custom 9×9 chess-piece markers. "
        "The decoder will detect the board, recover its FEN, and look up the word."
    )

    if not MARKER_FILE.exists():
        st.warning(
            "The marker file was not found at "
            f"`{MARKER_FILE}`. Add `custom_markers.csv` to your data-files "
            "folder before decoding."
        )

    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload up to three chessboard images.",
    )

    if uploaded_files:
        if len(uploaded_files) > 3:
            st.error("Please upload no more than three images.")
        else:
            preview_columns = st.columns(len(uploaded_files))
            for column, uploaded_file in zip(preview_columns, uploaded_files):
                with column:
                    st.image(
                        uploaded_file,
                        caption=uploaded_file.name,
                        use_container_width=True,
                    )

            if st.button(
                "Decode images",
                type="primary",
                use_container_width=True,
                disabled=not MARKER_FILE.exists(),
            ):
                decoded_results = []

                progress = st.progress(0, text="Starting image decoding...")

                for index, uploaded_file in enumerate(uploaded_files, start=1):
                    suffix = Path(uploaded_file.name).suffix or ".png"
                    temp_path = None

                    try:
                        with tempfile.NamedTemporaryFile(
                            suffix=suffix,
                            delete=False,
                        ) as temp_file:
                            temp_file.write(uploaded_file.getvalue())
                            temp_path = temp_file.name

                        # decode_image expects a filesystem path.
                        fen = decode_image(temp_path)
                        word = fen_to_word.get(fen, "")

                        decoded_results.append({
                            "filename": uploaded_file.name,
                            "fen": fen,
                            "word": word,
                        })

                    except Exception as exc:
                        decoded_results.append({
                            "filename": uploaded_file.name,
                            "error": str(exc),
                        })

                    finally:
                        if temp_path and os.path.exists(temp_path):
                            os.unlink(temp_path)

                    progress.progress(
                        index / len(uploaded_files),
                        text=f"Processed {index} of {len(uploaded_files)} image(s)",
                    )

                progress.empty()
                st.subheader("Decoding results")

                for index, result in enumerate(decoded_results, start=1):
                    with st.container(border=True):
                        st.markdown(f"**Image {index}: {result['filename']}**")

                        if "error" in result:
                            st.error(f"Could not decode this image: {result['error']}")
                            continue

                        if result["word"]:
                            st.success(f"Decoded word: {result['word']}")
                        else:
                            st.warning(
                                "A FEN was detected, but it was not found in "
                                "the word dictionary."
                            )

                        st.code(result["fen"], language=None)

                        try:
                            fig = draw_chessboard(result["fen"])
                            st.pyplot(fig, use_container_width=True)
                            plt.close(fig)
                        except ValueError as exc:
                            st.warning(f"Could not draw the detected board: {exc}")

                        st.download_button(
                            "Download decoded FEN",
                            data=result["fen"],
                            file_name=f"decoded_{index}.fen",
                            mime="text/plain",
                            key=f"decoded_download_{index}",
                        )

st.divider()
st.caption("ChessEncoding · Word-to-FEN encoding and image-to-word decoding")
