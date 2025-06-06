import tkinter as tk
from tkinter import messagebox, simpledialog
import chess
import chess.engine
from PIL import Image, ImageTk
import os
import random

STOCKFISH_PATH = os.path.join(os.path.dirname(__file__), "stockfish-windows-x86-64-avx2", "stockfish", "stockfish-windows-x86-64-avx2.exe")
if not os.path.exists(STOCKFISH_PATH):
    print(f"Erreur: Stockfish introuvable à l'emplacement : {STOCKFISH_PATH}")

PIECE_IMAGE_DIR = "images"
SQUARE_SIZE = 64

class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Échecs Graphiques - vs Stockfish ou 1v1")

        self.board = chess.Board()
        self.canvas = tk.Canvas(root, width=8*SQUARE_SIZE, height=8*SQUARE_SIZE, borderwidth=0, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.canvas.bind("<Button-1>", self.on_click_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_piece)
        self.canvas.bind("<ButtonRelease-1>", self.on_click_drag_end)

        self.images = {}
        self.selected_square = None
        self.dragged_piece_id = None
        self.dragged_piece_original_pos = None
        self.flipped = False
        self.engine = None
        self.vs_ai = True

        self.player_color = "white"

        self.load_images()
        self.draw_board()
        self.add_controls()

        if self.vs_ai and self.board.turn == chess.BLACK and self.player_color == "white":
            self.root.after(300, self.play_ai_move)

    def choose_white(self):
        self.player_color = "white"
        self.flipped = False
        self.reset_game()

    def choose_black(self):
        self.player_color = "black"
        self.flipped = True
        self.reset_game()

    def choose_random(self):
        self.player_color = random.choice(["white", "black"])
        self.flipped = (self.player_color == "black")
        self.reset_game()

    def load_images(self):
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K']
        colors = ['w', 'b']
        for color in colors:
            for piece in pieces:
                filename = f"{color}{piece}.png"
                path = os.path.join(PIECE_IMAGE_DIR, filename)
                try:
                    image = Image.open(path).resize((SQUARE_SIZE, SQUARE_SIZE), Image.Resampling.LANCZOS)
                    self.images[color + piece] = ImageTk.PhotoImage(image)
                except FileNotFoundError:
                    messagebox.showerror("Erreur de fichier", f"Image manquante: {path}.")
                    self.root.destroy()

    def draw_board(self):
        self.canvas.delete("all")
        color_light = "#F0D9B5"
        color_dark = "#B58863"

        for rank in range(8):
            for file in range(8):
                x1 = file * SQUARE_SIZE
                y1 = rank * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                color = color_light if (rank + file) % 2 == 0 else color_dark
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - chess.square_rank(square)
                col = chess.square_file(square)
                if self.flipped:
                    row, col = 7 - row, 7 - col
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE
                key = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.images[key], tags=f"piece_{square}")

        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = 7 - chess.square_rank(self.selected_square)
            if self.flipped:
                row, col = 7 - row, 7 - col
            x1 = col * SQUARE_SIZE
            y1 = row * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3, tags="highlight")
            self.canvas.tag_lower("highlight")

    def on_click_drag_start(self, event):
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        if self.flipped:
            col = 7 - col
            row = 7 - row
        square = chess.square(col, 7 - row)

        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn:
            self.selected_square = square
            self.canvas.delete("highlight")
            self.draw_board()

            self.dragged_piece_id = self.canvas.find_withtag(f"piece_{square}")
            if self.dragged_piece_id:
                self.canvas.tag_raise(self.dragged_piece_id)
                self.dragged_piece_original_pos = (event.x, event.y)

    def on_drag_piece(self, event):
        if self.dragged_piece_id and self.dragged_piece_original_pos:
            dx = event.x - self.dragged_piece_original_pos[0]
            dy = event.y - self.dragged_piece_original_pos[1]
            self.canvas.move(self.dragged_piece_id, dx, dy)
            self.dragged_piece_original_pos = (event.x, event.y)

    def on_click_drag_end(self, event):
        if self.selected_square is not None:
            col = event.x // SQUARE_SIZE
            row = event.y // SQUARE_SIZE
            if self.flipped:
                col = 7 - col
                row = 7 - row
            target_square = chess.square(col, 7 - row)

            move = chess.Move(self.selected_square, target_square)

            if self.board.piece_at(self.selected_square).piece_type == chess.PAWN and \
               (chess.square_rank(target_square) == 7 or chess.square_rank(target_square) == 0):
                promotion_choice = simpledialog.askstring("Promotion", "Promouvoir en (q, r, b, n) ?").lower()
                if promotion_choice in ['q', 'r', 'b', 'n']:
                    move = chess.Move(self.selected_square, target_square, promotion=chess.Piece.from_symbol(promotion_choice).piece_type)
                else:
                    messagebox.showerror("Erreur", "Choix de promotion invalide.")
                    self.reset_drag_state()
                    self.draw_board()
                    return

            self.make_move(move)
            self.reset_drag_state()
        else:
            self.reset_drag_state()

    def reset_drag_state(self):
        self.selected_square = None
        self.dragged_piece_id = None
        self.dragged_piece_original_pos = None
        self.canvas.delete("highlight")

    def make_move(self, move):
        if move in self.board.legal_moves:
            self.board.push(move)
            self.flipped = not self.flipped if not self.vs_ai else self.flipped
            self.draw_board()

            if self.board.is_game_over():
                self.end_game()
                return

            if self.vs_ai and self.board.turn == (chess.BLACK if self.player_color == "white" else chess.WHITE):
                self.root.after(300, self.play_ai_move)
        else:
            messagebox.showerror("Mouvement invalide", "Ce mouvement n'est pas légal.")
            self.draw_board()

    def play_ai_move(self):
        if not self.engine:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            except Exception as e:
                messagebox.showerror("Erreur Stockfish", str(e))
                return

        try:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.3))
            self.board.push(result.move)
            self.draw_board()

            if self.board.is_game_over():
                self.end_game()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            self.end_game()

    def end_game(self):
        result = self.board.result()
        if self.engine:
            self.engine.quit()
            self.engine = None
        messagebox.showinfo("Fin de partie", f"Partie terminée ! Résultat : {result}")

    def reset_game(self):
        if self.engine:
            self.engine.quit()
            self.engine = None
        self.board.reset()
        self.flipped = (self.player_color == "black")
        self.reset_drag_state()
        self.draw_board()
        if self.vs_ai and self.board.turn == (chess.BLACK if self.player_color == "white" else chess.WHITE):
            self.root.after(300, self.play_ai_move)

    def add_controls(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Blancs", command=self.choose_white).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Noirs", command=self.choose_black).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Aléatoire", command=self.choose_random).pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="Reset", command=self.reset_game).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="1v1", command=self.set_pvp).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Stockfish", command=self.set_vs_ai).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Retourner", command=self.toggle_flip).pack(side=tk.LEFT, padx=5)

        move_input_frame = tk.Frame(self.root)
        move_input_frame.pack(pady=5)

        tk.Label(move_input_frame, text="Entrez le mouvement (ex: e2e4):").pack(side=tk.LEFT, padx=5)
        self.move_entry = tk.Entry(move_input_frame, width=10)
        self.move_entry.pack(side=tk.LEFT, padx=5)
        self.move_entry.bind("<Return>", self.process_text_move_event)

        tk.Button(move_input_frame, text="Jouer", command=self.process_text_move).pack(side=tk.LEFT, padx=5)

    def toggle_flip(self):
        self.flipped = not self.flipped
        self.draw_board()

    def process_text_move_event(self, event=None):
        self.process_text_move()

    def process_text_move(self):
        move_uci = self.move_entry.get().strip()
        self.move_entry.delete(0, tk.END)

        if not move_uci:
            messagebox.showwarning("Saisie vide", "Veuillez entrer un mouvement.")
            return

        try:
            move = chess.Move.from_uci(move_uci)
            self.make_move(move)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def set_pvp(self):
        self.vs_ai = False
        self.reset_game()
        messagebox.showinfo("Mode", "1v1 activé.")

    def set_vs_ai(self):
        self.vs_ai = True
        self.reset_game()
        messagebox.showinfo("Mode", "Contre Stockfish activé.")
        if self.board.turn == (chess.BLACK if self.player_color == "white" else chess.WHITE):
            self.root.after(300, self.play_ai_move)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
