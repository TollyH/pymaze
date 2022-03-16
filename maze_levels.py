"""
Contains the definitions of each instance of Level. Also provides the constants
T and F as shorthands for True and False respectively, T corresponding to where
a wall is and F corresponding to a occupyable space.
"""
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
        (5, 0), (1, 9), [(2, 1), (9, 9), (1, 3)]
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
        (0, 0), (9, 5), [(0, 8), (3, 2), (3, 9), (9, 9), (7, 4), (7, 0)]
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
        ]
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
        ]
    )
]
