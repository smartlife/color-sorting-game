"""Level generation utilities for the color sorting game.

Levels are produced by starting from a solved configuration and then
applying a number of *reverse* moves.  Each reverse move removes a
uniform group of objects from one base and places it onto another base
without checking colour compatibility.  Because the operation is exactly
reversible, the generated puzzles are guaranteed to be solvable.  The
amount of scrambling per level is controlled through ``DIFFICULTY_STEPS``.
Running the module will create ``levels.json`` inside the generation folder.
"""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

# Folder containing object_*.png files
IMG_DIR = Path(__file__).resolve().parents[1] / "img"
# Output file path
OUTPUT_FILE = Path(__file__).resolve().parent / "levels.json"

# The number of levels to generate
NUM_LEVELS = 6

# Difficulty parameters. Keys are level numbers starting from 0.
# When a key is reached the settings are updated for all following levels.
# ``steps`` controls how many reverse moves are applied when scrambling.
DIFFICULTY_STEPS = {
    0: {"bases_count": 3, "base_height": 5, "steps": 5},
    2: {"bases_count": 4, "steps": 10},
    4: {"bases_count": 5, "steps": 15},
}


def load_colors(img_dir: Path) -> list[str]:
    """Return a list of object names based on image files.

    The game uses files named ``object_<color>.png``. This function
    extracts all ``<color>`` names so level generation automatically
    adapts when new images are added.
    """
    colors = []
    for path in sorted(img_dir.glob("object_*.png")):
        name = path.stem.replace("object_", "")
        colors.append(name)
    return colors


def is_solved(bases: list[list[str]], base_height: int) -> bool:
    """Check whether all bases are complete and contain a single color."""
    for b in bases:
        if not b:
            continue
        if len(b) != base_height:
            return False
        if any(obj != b[0] for obj in b):
            return False
    return True


def back_propagate(bases: list[list[str]], base_height: int, steps: int) -> None:
    """Scramble using moves that are the reverse of allowed game moves.

    The game only allows moving a uniform group from one base to another if the
    destination is empty or has the same color on top.  When running in reverse
    we ignore this color restriction and simply move random groups between bases
    as long as there is space.  Each reverse step can be undone with a single
    legal move in the forward direction, therefore the final configuration
    remains solvable.
    """
    rng = random.Random()
    for _ in range(steps):
        # pick a source with objects
        src_indices = [i for i, b in enumerate(bases) if b]
        if not src_indices:
            break
        src = rng.choice(src_indices)
        src_base = bases[src]

        # contiguous group of same color from the top
        color = src_base[-1]
        group = 1
        for j in range(len(src_base) - 2, -1, -1):
            if src_base[j] == color:
                group += 1
            else:
                break

        # pick a target with free space
        tgt_indices = [i for i, b in enumerate(bases) if i != src and len(b) < base_height]
        if not tgt_indices:
            break
        tgt = rng.choice(tgt_indices)
        tgt_base = bases[tgt]
        free = base_height - len(tgt_base)
        move_cnt = rng.randint(1, min(group, free))
        for _ in range(move_cnt):
            tgt_base.append(src_base.pop())


def create_level(base_count: int, base_height: int, colors: list[str], steps: int) -> dict:
    """Return a single level configuration.

    Starting from a solved state (one empty base and the rest filled with a
    single color), the configuration is scrambled by applying the
    ``back_propagate`` routine for ``steps`` iterations.
    """
    color_count = min(len(colors), base_count - 1)
    chosen_colors = colors[:color_count]
    bases = [[c] * base_height for c in chosen_colors]
    while len(bases) < base_count:
        bases.append([])
    back_propagate(bases, base_height, steps)
    if is_solved(bases, base_height):
        back_propagate(bases, base_height, steps)
    per_row = 3
    rows = []
    for i in range(0, len(bases), per_row):
        row = []
        for b in bases[i:i + per_row]:
            row.append({"baseHeight": base_height, "objects": b})
        rows.append(row)
    return {"rows": rows}


def generate_levels() -> list[dict]:
    """Create all levels using ``DIFFICULTY_STEPS`` as rules."""
    colors = load_colors(IMG_DIR)
    levels = []
    settings = {}
    for level_num in range(NUM_LEVELS):
        if level_num in DIFFICULTY_STEPS:
            settings.update(DIFFICULTY_STEPS[level_num])
        base_count = settings.get("bases_count", 3)
        base_height = settings.get("base_height", 5)
        steps = settings.get("steps", 5)
        level = create_level(base_count, base_height, colors, steps)
        levels.append(level)
    return levels


def _parse_level(level: dict) -> tuple[list[list[str]], list[int]]:
    """Return mutable bases list and matching height list from a level."""
    bases = []
    heights = []
    for row in level["rows"]:
        for cell in row:
            bases.append(list(cell["objects"]))
            heights.append(cell["baseHeight"])
    return bases, heights


def _solved(bases: list[list[str]], heights: list[int]) -> bool:
    """True if each base is either empty or filled with one colour."""
    for b, h in zip(bases, heights):
        if not b:
            continue
        if len(b) != h:
            return False
        if any(o != b[0] for o in b):
            return False
    return True


def _next_states(bases: list[list[str]], heights: list[int]) -> list[list[list[str]]]:
    """Yield new board states by applying all legal moves."""
    count = len(bases)
    states = []
    for i in range(count):
        src = bases[i]
        if not src:
            continue
        color = src[-1]
        group = 1
        for j in range(len(src) - 2, -1, -1):
            if src[j] == color:
                group += 1
            else:
                break
        for j in range(count):
            if i == j:
                continue
            tgt = bases[j]
            if len(tgt) == heights[j]:
                continue
            if tgt and tgt[-1] != color:
                continue
            free = heights[j] - len(tgt)
            max_move = min(group, free)
            for mv in range(1, max_move + 1):
                new_b = [list(b) for b in bases]
                moved = new_b[i][-mv:]
                new_b[i] = new_b[i][:-mv]
                new_b[j].extend(moved)
                states.append(new_b)
    return states


def solve_level(level: dict) -> tuple[bool, int]:
    """Attempt to solve ``level`` using breadth-first search.

    Returns a tuple ``(solved, explored)`` where ``solved`` indicates
    whether a solution exists and ``explored`` counts how many next states
    were generated during the search.  The algorithm keeps a set of visited
    configurations to avoid infinite loops.  If the queue is exhausted
    without reaching a solved state the level is deemed unsolvable.
    """

    bases, heights = _parse_level(level)
    start = tuple(tuple(b) for b in bases)
    queue = deque([bases])
    visited = {start}
    explored = 0
    while queue:
        cur = queue.popleft()
        if _solved(cur, heights):
            return True, explored
        for nxt in _next_states(cur, heights):
            explored += 1
            key = tuple(tuple(b) for b in nxt)
            if key not in visited:
                visited.add(key)
                queue.append(nxt)
    return False, explored


def main() -> None:
    """Generate ``levels.json`` and validate each level with the solver."""
    levels = generate_levels()
    OUTPUT_FILE.write_text(json.dumps(levels, indent=2))
    print(f"Wrote {len(levels)} level(s) to {OUTPUT_FILE}")

    for idx, lvl in enumerate(levels, start=1):
        solved, explored = solve_level(lvl)
        if not solved:
            raise RuntimeError(f"Level {idx} has no solution after exploring {explored} options")
        print(f"Level {idx} solved after exploring {explored} options")


if __name__ == "__main__":
    main()
