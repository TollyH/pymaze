"""
Precalculates all possible solutions from every possible position in each maze.
Useful for slower computers or complex mazes where path finding on-the-fly may
not be feasible. This only needs to be run when new levels are added or
existing levels are modified.
"""
import os
import pickle
import sys
from typing import Dict, List, Tuple


def precalculate_solutions():
    if os.path.isdir("precalculated_solutions.pickle"):
        print(
            "A folder named 'precalculated_solutions.pickle' currently exists."
            + " Please rename or delete it before running this script."
        )
        sys.exit(1)
    elif os.path.isfile("precalculated_solutions.pickle"):
        os.remove("precalculated_solutions.pickle")
    # Import must be done here so that the outdated pickle file is deleted
    # before the contents of the file is executed
    from maze_levels import levels
    # A list of each level's possible solutions mapped to each possible
    # position of the player
    level_solutions: List[
        Dict[Tuple[int, int], List[List[Tuple[int, int]]]]
    ] = []
    for index, maze_level in enumerate(levels):
        new_solutions: Dict[Tuple[int, int], List[List[Tuple[int, int]]]] = {}
        for y, row in enumerate(maze_level.wall_map):
            for x, point in enumerate(row):
                print(
                    f"\rCalculating point ({x:3d}, {y:3d}) "
                    + f"for level {index + 1:3d}",
                    end="", flush=True
                )
                if not point:
                    new_solutions[x, y] = sorted(
                        maze_level._path_search(
                            [(x, y)],
                            maze_level.exit_keys + [maze_level.end_point]
                        ), key=len
                    )
        level_solutions.append(new_solutions)
    with open("precalculated_solutions.pickle", 'wb') as file:
        pickle.dump(level_solutions, file)


if __name__ == "__main__":
    precalculate_solutions()
