"""
Contains the definitions of each instance of Level. Also provides the constants
T and F as shorthands for True and False respectively, T corresponding to where
a wall is and F corresponding to a occupyable space. If a pre-calculated
solutions file exists, it will be loaded here.
"""
import os
import pickle
from typing import Dict, List, Tuple

from level import Level

F = False
T = True

levels = [
    Level(
        (10, 10),
        [
            [T, T, T, T, T, F, T, T, T, T],
            [T, T, F, F, F, F, T, T, T, T],
            [T, T, F, T, T, F, T, T, T, T],
            [T, F, F, T, T, F, T, T, T, T],
            [T, F, F, T, T, F, F, F, F, T],
            [T, F, T, T, F, F, T, T, F, T],
            [T, F, T, F, F, T, T, T, F, T],
            [T, F, T, F, T, T, T, T, F, F],
            [T, F, T, F, T, T, T, T, T, F],
            [T, F, F, F, T, T, T, T, T, F]
        ],
        (5, 0), (1, 9), [(2, 1), (9, 9), (1, 3)], None, None
    ),
    Level(
        (10, 10),
        [
            [F, F, F, F, F, F, T, F, T, T],
            [T, F, T, T, T, F, T, F, F, F],
            [T, F, T, F, T, F, T, T, T, F],
            [T, F, T, F, F, F, T, T, T, F],
            [T, F, T, T, T, T, T, F, T, F],
            [T, F, F, F, F, F, F, F, F, F],
            [T, F, T, T, F, T, F, T, T, T],
            [T, F, T, F, F, T, F, T, T, T],
            [F, F, F, F, T, T, F, F, T, T],
            [T, T, T, F, T, T, T, F, F, F]
        ],
        (0, 0), (9, 5), [(0, 8), (3, 2), (3, 9), (9, 9), (7, 4), (7, 0)],
        (7, 0), 20
    ),
    Level(
        (15, 15),
        [
            [F, F, T, T, F, F, F, T, T, F, F, F, T, F, F],
            [T, F, F, F, F, T, F, T, F, F, T, F, F, F, T],
            [T, F, T, T, T, T, F, T, T, F, T, T, T, F, T],
            [T, F, F, F, F, T, F, F, F, F, F, F, F, F, F],
            [F, F, T, F, T, T, T, T, F, T, T, T, F, T, F],
            [T, T, T, F, F, F, T, T, F, T, F, T, T, T, F],
            [F, F, F, F, T, F, F, F, F, T, F, T, F, T, F],
            [F, T, F, T, T, F, T, T, F, T, F, F, F, F, F],
            [T, T, F, T, T, F, T, T, T, T, T, T, T, F, T],
            [T, F, F, F, F, F, F, F, F, T, F, F, T, F, T],
            [T, T, F, T, T, T, T, T, F, T, T, F, T, F, F],
            [F, T, F, F, F, F, F, T, F, F, F, F, T, F, T],
            [F, T, F, T, T, T, T, T, F, T, F, T, T, F, F],
            [F, T, F, T, T, F, F, T, F, T, F, T, T, F, T],
            [F, F, F, F, T, T, F, F, F, F, F, F, F, F, T]
        ],
        (0, 0), (0, 11),
        [
            (0, 4), (8, 1), (8, 7), (0, 7), (12, 4), (12, 6), (10, 5),
            (10, 9), (14, 0), (14, 12), (14, 10), (5, 13), (4, 3), (3, 14)
        ],
        (7, 6), 35
    ),
    Level(
        (17, 17),
        [
            [F, F, F, F, T, T, F, T, F, T, T, T, F, F, F, T, T],
            [F, T, T, F, F, F, F, T, F, T, F, T, F, T, F, F, T],
            [F, F, T, T, T, T, F, T, F, F, F, T, F, T, T, F, F],
            [T, F, F, F, T, F, F, F, F, T, T, T, F, F, F, F, T],
            [T, F, T, F, T, T, T, F, T, T, F, F, F, T, T, F, T],
            [F, F, F, F, F, F, F, F, T, F, F, T, T, T, F, F, F],
            [F, T, T, F, T, T, T, F, T, F, T, T, F, F, F, T, F],
            [F, F, T, F, F, F, F, F, F, F, F, F, F, T, T, T, T],
            [T, F, T, T, T, T, T, F, F, F, T, T, F, F, F, F, T],
            [T, F, F, F, F, F, F, F, F, F, F, F, F, T, F, T, T],
            [F, F, T, T, F, T, T, F, T, F, T, F, T, T, F, F, F],
            [T, F, F, F, F, T, T, F, T, F, T, T, T, F, F, T, T],
            [T, T, T, T, T, T, F, F, T, F, F, F, F, F, T, T, F],
            [T, F, F, T, F, T, F, T, T, T, T, F, T, F, F, F, F],
            [T, F, T, T, F, F, F, F, F, F, T, F, T, T, F, T, T],
            [F, F, F, F, F, T, T, T, T, F, F, F, T, F, F, F, T],
            [T, T, F, T, F, F, T, F, F, F, T, F, T, T, F, T, T]
        ],
        (8, 7), (8, 9),
        [
            (0, 10), (0, 15), (2, 13), (10, 1), (16, 2), (16, 6), (14, 16),
            (5, 16), (7, 16), (14, 16), (16, 10), (16, 12), (14, 16), (15, 8),
            (2, 16), (11, 16), (6, 0),
        ],
        (8, 8), 40
    ),
    Level(
        (19, 19),
        [
            [F, F, F, F, F, T, F, F, F, T, F, F, F, T, F, F, F, F, F],
            [T, T, F, T, F, T, T, T, F, T, F, T, F, T, T, T, T, T, F],
            [F, T, F, T, F, F, F, T, F, F, F, T, F, F, F, F, F, F, F],
            [F, T, F, T, T, T, F, T, F, T, T, T, T, T, T, T, F, T, T],
            [F, T, F, F, F, T, F, F, F, T, F, F, F, T, F, F, F, T, F],
            [F, T, T, T, F, T, T, T, T, T, F, T, T, T, T, T, T, T, F],
            [F, F, F, T, F, F, F, F, F, T, F, T, F, F, F, T, F, F, F],
            [F, T, T, T, T, T, F, T, T, T, F, T, F, T, F, T, T, T, F],
            [F, T, F, F, F, F, F, T, F, F, F, T, F, T, F, F, F, F, F],
            [F, T, F, T, T, T, T, T, F, T, T, T, F, T, F, T, F, T, T],
            [F, T, F, F, F, T, F, T, F, F, F, F, F, T, F, T, F, T, F],
            [F, T, T, T, F, T, F, T, T, T, F, T, T, T, F, T, F, T, F],
            [F, F, F, F, F, F, F, F, F, F, F, F, F, F, F, T, F, T, F],
            [T, T, T, T, F, T, F, T, T, T, F, T, T, T, T, T, F, T, F],
            [F, F, F, F, F, T, F, T, F, T, F, T, F, F, F, F, F, F, F],
            [F, T, T, T, F, T, F, T, F, T, F, T, T, T, F, T, T, T, T],
            [F, T, F, F, F, F, F, T, F, F, F, F, F, T, F, T, F, F, F],
            [F, T, T, T, T, T, F, T, F, T, T, T, F, T, T, T, F, T, F],
            [F, F, F, F, F, F, F, F, F, F, F, T, F, F, F, F, F, T, F]
        ],
        (0, 18), (18, 0),
        [
            (0, 2), (2, 6), (18, 18), (6, 0), (12, 4), (18, 4), (14, 4),
            (14, 16), (18, 10), (2, 16), (10, 18), (8, 14), (0, 0), (6, 10),
            (8, 6), (14, 0), (16, 6), (12, 14)
        ],
        (14, 0), 60
    ),
    Level(
        (20, 20),
        [
            [T, F, T, T, T, F, F, T, T, F, F, T, T, T, F, F, F, T, T, T],
            [F, F, F, F, T, T, F, F, F, F, T, T, F, T, T, T, F, F, F, F],
            [T, F, T, F, F, F, F, T, T, F, F, F, F, F, F, T, F, T, T, F],
            [T, F, T, T, T, T, T, T, T, T, F, T, F, T, F, T, F, T, F, F],
            [T, F, F, F, F, F, T, T, F, T, T, T, T, T, F, T, F, F, F, T],
            [T, T, T, F, T, F, T, F, F, F, F, F, F, T, F, T, T, T, F, F],
            [T, F, T, T, T, F, T, T, F, T, T, T, F, F, F, T, T, F, F, T],
            [T, F, T, F, F, F, T, T, F, F, T, F, F, T, T, T, F, F, F, F],
            [F, F, T, F, T, T, T, T, T, F, T, T, F, T, F, F, F, T, F, T],
            [F, T, T, F, T, F, F, F, T, F, F, T, T, T, F, T, T, T, F, T],
            [F, T, F, F, T, F, T, T, T, F, F, F, F, F, F, F, F, T, T, T],
            [F, F, F, T, T, F, F, F, F, F, T, T, T, T, T, T, F, F, F, T],
            [T, T, F, T, T, T, T, T, F, F, F, T, F, F, F, T, T, T, F, F],
            [T, F, F, F, F, F, F, T, T, F, T, T, F, T, F, F, F, T, F, T],
            [F, F, T, F, T, T, F, F, T, T, T, T, F, T, T, T, F, T, T, T],
            [F, T, T, F, T, T, T, F, F, T, F, F, F, T, F, T, F, F, F, T],
            [T, T, F, F, T, F, T, T, F, F, F, T, F, T, F, T, T, T, F, F],
            [T, F, F, T, T, F, F, T, T, F, T, T, F, T, F, F, T, F, F, T],
            [T, F, T, T, T, T, F, T, F, F, F, T, F, F, F, T, T, F, T, T],
            [T, F, F, F, F, F, F, T, T, F, T, T, T, T, T, T, F, F, F, F]
        ],
        (9, 9), (19, 19),
        [
            (1, 0), (5, 0), (10, 0), (14, 0), (0, 1), (12, 1), (10, 3),
            (12, 3), (8, 4), (3, 5), (7, 5), (19, 5), (1, 6), (11, 7), (19, 7),
            (12, 8), (7, 9), (18, 9), (10, 12), (19, 12), (9, 13), (18, 13),
            (0, 15), (14, 15), (5, 16), (19, 16), (15, 17), (8, 18), (10, 18),
            (9, 19), (16, 19)
        ],
        (9, 19), 75
    ),
    Level(
        (40, 40),
        [
            [F, F, F, F, F, F, F, F, F, F, F, F, T, F, F, F, F, T, F, F, F, T, F, F, F, F, T, T, T, F, F, F, F, T, T, T, T, T, F, T],
            [F, T, T, T, F, T, T, T, T, T, T, F, T, F, T, T, T, T, F, T, F, T, F, T, T, F, T, F, F, F, T, T, F, T, F, F, F, F, F, F],
            [F, F, F, T, F, F, F, F, T, F, T, F, T, F, T, T, F, F, F, T, T, T, F, T, T, F, T, F, T, T, T, T, F, T, F, T, T, F, T, F],
            [F, T, F, T, T, F, T, T, T, F, T, F, F, F, F, F, F, T, F, T, F, F, F, T, F, F, F, F, T, F, F, T, F, T, F, T, T, T, T, F],
            [F, T, F, F, T, F, F, F, F, F, T, T, T, T, T, T, F, T, T, T, F, T, F, T, T, F, T, T, T, F, T, T, F, F, F, F, T, F, T, F],
            [F, T, F, T, T, T, F, T, T, F, T, F, T, T, F, T, F, F, F, F, F, T, F, F, T, F, F, F, F, F, T, F, F, T, T, F, T, F, F, F],
            [F, T, T, T, F, T, F, T, T, F, F, F, F, F, F, T, F, T, F, T, T, T, T, F, T, T, T, F, T, T, T, T, F, F, F, F, T, T, F, T],
            [F, F, F, F, F, T, F, F, F, F, T, F, T, F, T, T, F, T, F, T, F, F, T, F, F, T, T, F, F, F, F, T, T, T, T, F, F, T, F, T],
            [F, T, F, T, T, T, F, T, T, T, T, T, T, F, T, T, F, T, F, T, F, T, T, T, F, T, F, F, T, F, T, T, T, F, T, T, T, T, F, F],
            [F, T, F, F, T, F, F, T, F, F, F, F, F, F, F, F, F, T, F, T, F, T, F, T, F, T, T, F, T, T, T, F, F, F, T, T, T, F, F, T],
            [F, T, T, F, F, F, T, T, F, T, T, T, F, T, T, T, F, T, F, F, F, F, F, T, F, F, F, F, T, F, F, F, T, F, F, F, F, F, T, T],
            [F, F, T, F, T, F, T, F, F, T, F, T, F, T, F, T, F, T, T, T, T, T, T, T, T, T, T, F, T, T, T, F, T, T, T, T, T, F, F, T],
            [T, F, T, F, T, F, T, T, T, T, F, F, F, T, F, F, F, F, F, F, F, F, F, T, F, F, F, F, T, F, T, F, T, F, F, F, T, T, F, T],
            [T, F, T, F, T, F, F, F, T, T, T, T, F, T, T, T, F, T, F, T, T, F, T, T, T, T, T, F, T, F, T, T, T, F, T, T, T, F, F, T],
            [F, F, T, T, T, F, T, F, F, F, T, T, F, T, T, T, F, T, F, F, T, F, F, T, F, F, F, F, F, F, T, F, F, F, T, F, T, F, T, T],
            [T, F, T, F, T, F, T, T, T, F, F, F, F, F, F, T, F, T, T, T, T, F, T, T, F, T, F, T, T, F, T, T, F, T, T, F, T, F, F, T],
            [T, F, F, F, T, F, F, F, T, T, T, F, T, T, F, T, T, T, F, F, F, F, T, T, F, T, T, T, T, F, F, F, F, T, F, F, T, T, F, T],
            [F, F, T, F, T, F, T, F, F, F, T, F, F, T, F, F, F, T, T, F, T, T, T, F, F, F, F, F, T, T, F, T, T, T, F, T, T, T, F, T],
            [F, T, T, F, T, F, T, T, F, T, T, F, T, T, F, T, T, T, T, F, T, F, F, F, T, F, T, F, F, T, F, T, F, F, F, T, F, F, F, T],
            [F, T, T, T, T, F, T, T, T, T, T, F, T, F, F, F, F, F, T, F, F, F, T, T, T, F, T, T, F, T, F, T, F, T, T, T, F, T, T, T],
            [F, F, T, T, F, F, F, F, F, F, T, F, T, T, F, T, F, T, T, T, T, T, T, F, T, T, T, T, F, F, F, F, F, F, F, F, F, F, F, T],
            [T, F, F, T, F, T, T, F, T, T, T, F, T, T, T, T, F, T, F, F, F, F, F, F, F, F, F, F, F, T, T, T, F, T, T, T, F, T, F, T],
            [F, F, T, T, F, F, T, F, F, F, T, F, F, F, T, T, T, T, F, T, T, T, T, T, T, T, T, T, T, T, F, T, F, T, F, T, T, T, F, T],
            [F, T, T, F, F, T, T, F, T, T, T, T, T, T, T, F, F, F, F, T, F, F, F, T, F, F, F, F, F, F, F, T, F, T, F, T, F, T, F, F],
            [F, F, T, F, T, T, T, F, F, F, F, F, F, F, F, F, T, T, F, F, F, T, F, T, F, T, T, T, T, T, T, T, F, T, F, F, F, F, F, T],
            [F, T, T, F, F, F, T, T, T, F, T, T, T, T, F, T, T, T, T, F, T, T, F, F, F, F, F, T, F, F, F, F, F, T, F, T, T, T, F, T],
            [T, T, T, F, T, T, T, F, T, F, T, T, F, T, F, F, F, T, F, F, F, T, T, T, T, T, F, T, T, T, T, F, T, T, F, T, T, F, F, F],
            [F, F, F, F, F, F, T, F, F, F, F, F, F, T, F, T, F, T, T, T, F, F, F, F, F, T, F, T, F, F, F, F, T, F, F, T, F, F, T, F],
            [T, T, F, T, T, F, T, T, T, F, T, T, T, T, T, T, F, T, F, T, T, T, T, T, T, T, F, F, F, T, T, T, T, T, T, T, F, T, T, F],
            [T, F, F, F, T, F, T, F, F, F, F, F, F, F, F, F, F, F, F, F, F, T, F, F, F, F, F, T, F, F, T, F, F, F, F, T, F, T, F, F],
            [T, T, F, T, T, F, T, T, F, T, F, T, F, T, T, T, T, F, T, T, F, T, F, T, T, T, T, T, F, T, T, T, T, T, F, T, F, T, F, T],
            [F, F, F, F, T, F, F, T, T, T, T, T, F, F, F, F, T, F, T, T, F, T, F, F, F, T, F, F, F, F, F, F, F, T, F, F, F, T, F, F],
            [T, F, T, F, T, T, T, T, F, T, F, T, F, T, T, T, T, F, F, F, F, T, F, T, F, F, F, T, T, T, T, T, T, T, T, F, T, T, T, F],
            [T, F, T, F, F, F, F, T, F, T, F, T, T, T, F, F, F, F, T, T, F, T, F, T, T, T, T, T, F, T, T, F, F, F, T, F, T, F, F, F],
            [T, T, T, T, F, T, T, T, F, F, F, F, T, T, T, T, T, F, F, F, F, T, F, F, F, F, T, T, F, F, F, F, T, F, T, T, T, F, T, T],
            [F, T, F, F, F, F, F, T, T, F, T, T, T, F, F, F, F, F, T, T, F, T, F, T, T, F, F, T, T, F, T, F, T, F, T, F, F, F, F, T],
            [F, F, F, T, F, T, F, F, T, F, F, F, F, F, T, F, T, F, F, F, F, T, F, F, T, F, T, T, T, F, T, F, T, F, T, F, T, T, F, F],
            [T, F, T, T, F, T, T, T, T, T, F, T, T, T, T, F, T, T, T, F, T, T, F, T, T, F, T, F, F, F, T, F, T, F, T, F, T, F, F, T],
            [T, F, T, T, F, F, F, T, T, F, F, F, T, F, F, F, F, T, F, F, F, F, F, T, F, F, F, F, T, T, T, F, T, F, F, F, T, F, T, T],
            [T, F, F, T, T, T, F, F, F, F, T, T, T, F, T, T, F, T, T, F, T, F, T, T, F, T, T, F, T, T, F, F, T, T, F, T, T, F, F, F]
        ],
        (0, 0), (39, 39),
        [
            (3, 4), (7, 2), (9, 2), (7, 11), (10, 11), (14, 11), (3, 15),
            (18, 16), (17, 19), (23, 20), (30, 22), (33, 27), (35, 33),
            (39, 36), (9, 20), (13, 22), (20, 1), (22, 9), (29, 12),
            (35, 14), (29, 10), (36, 7), (39, 8), (35, 14), (30, 3),
            (39, 23), (14, 11), (24, 12), (7, 26), (6, 31), (18, 28),
            (10, 30), (15, 31), (14, 33), (28, 33), (24, 39), (2, 39),
            (27, 39)
        ],
        (39, 39), 120
    )
]

if os.path.isfile("precalculated_solutions.pickle"):
    with open("precalculated_solutions.pickle", 'rb') as file:
        level_solutions: List[
            Dict[Tuple[int, int], List[List[Tuple[int, int]]]]
        ] = pickle.load(file)
    for index, solution_map in enumerate(level_solutions):
        try:
            levels[index]._solution_cache = solution_map
        except IndexError:
            break
