import csv
import io

import chess
import chess.pgn
import chess.svg


default_board = chess.Board()
piece_counts = {pt: len(default_board.pieces(pt, chess.WHITE)) for pt in chess.PIECE_TYPES}
capture_counts = {pt: .0 for pt in chess.PIECE_TYPES}
captured_counts = {pt: .0 for pt in chess.PIECE_TYPES}


with open("data/games_metadata_profile.csv", "rb") as f:
    NUM_LINES = sum(1 for _ in f)


with open("data/games_metadata_profile.csv", encoding="utf-8") as game_file:
    reader = csv.DictReader(game_file)
    i = 0
    for data in reader:
        moves = data["Moves"]
        game = chess.pgn.read_game(io.StringIO(moves))
        if game is None:
            continue
        board = game.board()
        for move in game.mainline_moves():
            if board.is_capture(move):
                pt_capture = board.piece_at(move.from_square).piece_type
                if board.is_en_passant(move):
                    pt_captured = chess.PAWN
                else:
                    pt_captured = board.piece_at(move.to_square).piece_type
                capture_counts[pt_capture] += 1/piece_counts[pt_capture]
                captured_counts[pt_captured] += 1/piece_counts[pt_captured]
            board.push(move)
        if i % 1000 == 0:
            print(f"\r{i/NUM_LINES*100:.0f}%", end="")
        i += 1

print("\r100%")
capture_count_total = sum(capture_counts.values())
captured_count_total = sum(captured_counts.values())
with open("data/capture_counts.csv", "w+", encoding="utf-8") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = ['Piece Type', 'Capture Count', 'Captured Count'])
    writer.writeheader()
    for pt in capture_counts:
        writer.writerow({
            'Piece Type': chess.piece_symbol(pt),
            'Capture Count': round(capture_counts[pt]/capture_count_total*100, 2),
            'Captured Count': round(captured_counts[pt]/captured_count_total*100, 2),
        })
print("Wrote output to 'data/capture_counts.csv'")
