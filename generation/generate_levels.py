"""Level generation utilities for the color sorting game.

Levels are produced by starting from a solved configuration and then
applying a number of *legal* moves at random.  Because each move obeys the
game rules, simply reversing the sequence leads back to the solution.  The
amount of scrambling per level is controlled through ``DIFFICULTY_STEPS``.
Running the module will create ``levels.json`` inside the generation folder.
"""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path

# Use a fixed seed so generated puzzles are reproducible. This also makes
# debugging easier because the exact same boards can be re-created across
# runs of the script.
random.seed(0)

# Folder containing object_*.png files
# The images live under the "www" directory of the project so adjust the
# path accordingly.  A previous version pointed one directory too high which
# meant no colours were loaded and empty levels were produced.
IMG_DIR = Path(__file__).resolve().parents[1] / "www" / "img"
# Output file path
OUTPUT_FILE = Path(__file__).resolve().parent / "levels.json"

# The number of levels to generate
# We now create a larger set so the game has more content to play through.
NUM_LEVELS = 40

# Difficulty parameters. Keys are level numbers starting from 0.
# When a key is reached the settings are updated for all following levels.
# ``steps`` controls how many random moves are applied when scrambling.
DIFFICULTY_STEPS = {
    # Start with three bases and a small amount of scrambling.
    0: {"bases_count": 3, "base_height": 5, "steps": 5},
    # Increase scrambling after the first few levels to slowly ramp up
    # difficulty while keeping the same number of bases.
    5: {"steps": 10},
    # Add another base and more scrambling once the player has warmed up.
    10: {"bases_count": 4, "steps": 15},
    # Continue to raise complexity.
    20: {"bases_count": 5, "steps": 20},
    # Final stretch uses six bases and heavy scrambling.
    30: {"bases_count": 6, "steps": 25},
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


def scramble(bases: list[list[str]], base_height: int, steps: int) -> None:
    """Randomly mix ``bases`` by moving blocks without colour restrictions.

    Traditional color sort puzzles are created by starting from a solved
    configuration and executing arbitrary moves while never exceeding the
    capacity of any base.  The sequence is then discarded, leaving a scrambled
    board for the player.  Because we only move blocks between bases that have
    room, reversing the exact sequence would restore the solved state, so a
    solution is guaranteed to exist.  Unlike the previous implementation, moves
    are *not* limited to empty or matching-colour targets which prevents all
    bases from remaining single-coloured during generation.
    """

    rng = random
    for _ in range(steps):
        moves = []
        count = len(bases)
        for i in range(count):
            src = bases[i]
            if not src:
                continue
            for j in range(count):
                if i == j:
                    continue
                tgt = bases[j]
                if len(tgt) == base_height:
                    continue
                max_move = min(len(src), base_height - len(tgt))
                for mv in range(1, max_move + 1):
                    moves.append((i, j, mv))
        if not moves:
            break
        i, j, mv = rng.choice(moves)
        block = bases[i][-mv:]
        bases[i] = bases[i][:-mv]
        bases[j].extend(block)


def create_level(base_count: int, base_height: int, colors: list[str], steps: int) -> dict:
    """Return a single level configuration.

    A fresh board is created in a solved state (all bases contain one colour
    except for a spare empty base).  ``scramble`` then executes random moves to
    mix the objects.  If the resulting puzzle is either already solved or the
    breadth‑first solver fails to find a solution we repeat the process until a
    valid board is produced.  This guards against unlucky sequences that would
    otherwise yield an unsolvable arrangement.
    """
    color_count = min(len(colors), base_count - 1)
    chosen_colors = colors[:color_count]

    while True:
        bases = [[c] * base_height for c in chosen_colors]
        while len(bases) < base_count:
            bases.append([])

        scramble(bases, base_height, steps)
        if is_solved(bases, base_height):
            continue
        level = {"rows": []}
        per_row = 3
        for i in range(0, len(bases), per_row):
            row = []
            for b in bases[i:i + per_row]:
                row.append({"baseHeight": base_height, "objects": b})
            level["rows"].append(row)
        solved, _ = solve_level(level)
        if solved:
            return level


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


def back_propagate(bases: list[list[str]], heights: list[int]) -> list[list[list[str]]]:
    """Return every board that can reach ``bases`` in one legal move.

    ``bases`` must describe a solved configuration according to ``_solved``.
    For each possible forward move from an unknown board ``U`` to ``bases`` we
    reconstruct ``U`` by reversing that move and verify that the original forward
    operation would be legal.  This allows generation of puzzles by repeatedly
    applying backwards steps from a solved state while keeping the guarantee of
    solvability.
    """

    if not _solved(bases, heights):
        raise ValueError("back_propagate expects a solved configuration")

    result: list[list[list[str]]] = []
    count = len(bases)
    for tgt in range(count):
        source_base = bases[tgt]
        if not source_base:
            continue
        # determine the contiguous run of identical colours on top of tgt
        colour = source_base[-1]
        run = 1
        for idx in range(len(source_base) - 2, -1, -1):
            if source_base[idx] == colour:
                run += 1
            else:
                break
        for r in range(1, run + 1):
            group = source_base[-r:]
            for src in range(count):
                if src == tgt:
                    continue
                if len(bases[src]) + r > heights[src]:
                    continue
                new_src = bases[src] + group
                new_tgt = source_base[:-r]
                if new_tgt and new_tgt[-1] != colour:
                    continue
                candidate = [list(b) for b in bases]
                candidate[src] = new_src
                candidate[tgt] = new_tgt
                if not _solved(candidate, heights):
                    result.append(candidate)
    return result


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
