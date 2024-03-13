import argparse
import csv
import io
import json
from typing import Iterable, TypedDict
import math

import chess
import chess.pgn


class OpeningTree(TypedDict):
    """Tree of opening moves."""

    openings: set[str]
    next_moves: dict[str, "OpeningTree"]

OpeningCount = TypedDict('OpeningCount', {'moves': str, 'count': int})
OpeningData = dict[str, OpeningCount]


def luminance(c: int) -> float:
    """Compute color luminance."""
    blue = c & 255
    green = (c >> 8) & 255
    red = (c >> 16) & 255
    return (.299 * red) + (.587 * green) + (.114 * blue)

def tree_relevance(tree: OpeningTree, opening_data: OpeningData) -> int:
    """Compute the relevance of a tree by summing up openings that this tree contains."""
    return sum(opening_data[opening]["count"] for opening in tree["openings"])

def scale_color(x: float) -> int:
    """Graduated colour scale from 0 (light blue) to 1 (warm yellow)."""
    assert 0 <= x <= 1, "Invalid colour scale."
    blue  = int(min((max((4*(0.75-x), 0.)), 1.))*255)
    red   = int(min((max((4*(x-0.25), 0.)), 1.))*255)
    green = int(min((max((4*math.fabs(x-0.5)-1., 0.)), 1.))*255)
    return (red<<16) + (green<<8) + blue

def collapse_tree_data(tree: OpeningTree) -> None:
    """Collapse paths that only describe one opening."""
    for subtree in tree["next_moves"].values():
        collapse_tree_data(subtree)
    if len(tree["openings"]) == 1:
        tree["next_moves"].clear()

def generate_nodes(tree: OpeningTree,
                   opening_data: OpeningData,
                   node_id: str = "root",
                   node_label: str = "Start",
                   level: int = 0) -> Iterable[dict]:
    """Generate Vis.js nodes from an opening tree."""
    total_count = sum(v["count"] for v in opening_data.values())
    opening_count = tree_relevance(tree, opening_data) or total_count
    font_size = 30 + math.sqrt(opening_count / total_count) * 150
    bg_color = scale_color((opening_count / total_count)**(1/4))
    fg_color = "#ffffff" if luminance(bg_color) < 128 else "#000000"
    yield {
        "id": node_id,
        "label": node_label,
        "borderWidth": 0,
        "color": f"#{bg_color:06x}",
        "level": level,
        "font": { "size": round(font_size), "color": fg_color }
    }
    for (k, v) in tree["next_moves"].items():
        yield from generate_nodes(
            v, opening_data, f"{node_id}/{k}", node_label=k, level=level+1)
    if len(tree["next_moves"]) == 0:
        opening_name = set(tree["openings"]).pop()
        opening_count = opening_data[opening_name]["count"]
        font_size = 6 + round((opening_count/total_count)**(1/3)*250)
        yield {
            "id": node_id + "-label",
            "label": opening_name,
            "opening_name": opening_name,
            "borderWidth": 0,
            "opacity": 0,
            "level": 10,
            "hidden": opening_data[opening_name]["count"] < 300,
            "font": { "size": font_size }
        }

def generate_edges(tree: OpeningTree,
                   opening_data: dict[str, OpeningCount],
                   parent_id: str = "root") -> Iterable[dict]:
    """Generate Vis.js edges from an opening tree."""
    total_count = sum(i["count"] for i in opening_data.values())
    for (k, v) in tree["next_moves"].items():
        node_id = f"{parent_id}/{k}"
        opening_count = sum(opening_data[opening]["count"] for opening in v["openings"])
        yield {
            "to": node_id,
            "from": parent_id,
            "color": { "inherit": "both" },
            "width": round(1 + math.sqrt(opening_count / total_count) * 100)
        }
        yield from generate_edges(v, opening_data, node_id)
    if len(tree["next_moves"]) == 0:
        yield { "from": parent_id, "to": parent_id + "-label", "width": 3 }

def arrange_fixed_nodes(nodes: list[dict], radius: int) -> None:
    """Arrange nodes so that labels are arranged in a circle."""
    label_count = sum(1 for node in nodes if node["id"].endswith("-label"))
    i = 0
    for node in nodes:
        if node["id"] == "root":
            node.update({"x": 0, "y": 0, "fixed": True })
        if node["id"].endswith("-label"):
            angle = i/label_count*2*math.pi - math.pi/2
            node["x"] = round(math.cos(angle) * radius)
            node["y"] = round(math.sin(angle) * radius)
            node["fixed"] = True
            i += 1

def read_csv(csv_path: str) -> dict[str, OpeningCount]:
    """Read opening moves from CSV."""
    print("\rReading CSV: 0%", end="")
    openings: dict[str, OpeningCount] = {}
    with open(csv_path, "rb") as f:
        NUM_LINES = sum(1 for _ in f)
    with open(csv_path, encoding="utf-8") as game_file:
        reader = csv.DictReader(game_file)
        i = 0
        for data in reader:
            opening = data["Opening"]
            if opening not in openings:
                openings[opening] = {"moves": data["Moves"], "count": 1}
            else:
                openings[opening]["count"] += 1
            if i % 1000 == 0:
                print(f"\rReading CSV: {i/NUM_LINES*100:.0f}%", end="")
            i += 1
    print("\rReading CSV: Done")
    return openings

def parse_openings(openings: dict[str, OpeningCount], threshold: int = 120) -> OpeningTree:
    """Parse opening data into an opening tree."""
    print("\rParsing Openings: 0%", end="")
    tree_data: OpeningTree = {"openings": set(), "next_moves": {}}
    for i, (opening_name, opening_data) in enumerate(openings.items()):
        if opening_data["count"] < threshold:
            continue
        game = chess.pgn.read_game(io.StringIO(opening_data["moves"]))
        if game is None:
            continue
        board = game.board()
        nested_tree_data = tree_data
        for move in game.mainline_moves():
            movestr = board.san(move)
            nested_tree_data = nested_tree_data["next_moves"].setdefault(
                movestr, {"openings": set(), "next_moves": {}})
            nested_tree_data["openings"].add(opening_name)
            board.push(move)
        print(f"\rParsing Openings: {i/len(openings)*100:.0f}%", end="")
    print("\rParsing Openings: Done")
    return tree_data

def write_js(js_path: str,
             tree_data: OpeningTree,
             opening_data: dict[str, OpeningCount]) -> None:
    """Write opening tree to js."""
    print(f"Writing JS to {js_path}:", end=" ")
    node_data = list(generate_nodes(tree_data, opening_data))
    edge_data = list(generate_edges(tree_data, opening_data))
    arrange_fixed_nodes(node_data, 2000)
    node_data_str = json.dumps(node_data, indent=2)
    edge_data_str = json.dumps(edge_data, indent=2)
    with open(js_path, "w+", encoding="utf-8") as js_file:
        js_file.write(f"\
const NODES = {node_data_str};\n\
const EDGES = {edge_data_str};\n")
    print("Done")


def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dataset')
    args = parser.parse_args()

    openings = read_csv(args.input_dataset)
    opening_tree = parse_openings(openings)
    print("Collapsing tree:", end=" ")
    collapse_tree_data(opening_tree)
    print("Done")
    write_js("data/tree_data.js", opening_tree, openings)
    return 1

if __name__ == "__main__":
    main()
