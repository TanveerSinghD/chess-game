from __future__ import annotations

import random
from typing import Dict, List, Sequence, Tuple, Optional

BOOK_RESPONSES: Dict[Tuple[str, ...], List[Tuple[str, str]]] = {
    # Queen's Gambit (1.d4 d5 2.c4)
    ("d2d4", "d7d5", "c2c4"): [
        ("e7e6", "QGD"),   # Queen's Gambit Declined
        ("c7c6", "Slav"),  # Slav Defense
    ],
    # Queen's Gambit Accepted continue (1.d4 d5 2.c4 dxc4 3.Nf3)
    ("d2d4", "d7d5", "c2c4", "d5c4", "g1f3"): [
        ("e7e6", "QGA ...e6"),
        ("g8f6", "QGA ...Nf6"),
    ],
    # King's Pawn: default to Sicilian / classical e5
    ("e2e4",): [
        ("c7c5", "Sicilian Defense"),
        ("e7e5", "Open Game"),
    ],
    ("e2e4", "e7e5", "g1f3"): [
        ("b8c6", "Ruy Lopez/Italian"),
    ],
    ("e2e4", "c7c5", "g1f3"): [
        ("d7d6", "Najdorf setup"),
        ("e7e6", "Kan/Flex"),
    ],
    ("e2e4", "e7e6"): [
        ("d2d4", "French advance/classical"),
    ],
    ("e2e4", "c7c6"): [
        ("d2d4", "Caro-Kann mainline"),
    ],
    ("e2e4", "d7d5"): [
        ("e4d5", "Scandinavian capture"),
    ],
    ("e2e4", "g7g6"): [
        ("d2d4", "Modern/Pirc setup"),
    ],
    ("e2e4", "d7d6"): [
        ("d2d4", "Pirc/Philidor setup"),
    ],
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5"): [
        ("a7a6", "Ruy Lopez ...a6"),
    ],
    ("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4"): [
        ("g8f6", "Sicilian Najdorf/Classic"),
    ],
    ("e2e4", "c7c5", "g1f3", "e7e6"): [
        ("d2d4", "Sicilian Kan/Taimanov"),
    ],
    # English opening
    ("c2c4",): [
        ("e7e5", "Reverse Sicilian"),
        ("c7c5", "Symmetrical English"),
    ],
    ("c2c4", "e7e5", "g1f3"): [
        ("b8c6", "English Four Knights"),
    ],
    # Reti
    ("g1f3",): [
        ("d7d5", "Reti ...d5"),
        ("g8f6", "Reti ...Nf6"),
    ],
    ("d2d4",): [
        ("d7d5", "Classical d4d5"),
        ("g8f6", "Indian setups"),
        ("f7f5", "Dutch Defense"),
    ],
    ("d2d4", "g8f6", "c2c4"): [
        ("e7e6", "Nimzo/QID"),
        ("g7g6", "King's Indian"),
        ("c7c6", "Slav/Semi-Slav"),
    ],
    ("d2d4", "g8f6", "c2c4", "e7e6", "b1c3"): [
        ("f8b4", "Nimzo-Indian"),
    ],
    ("d2d4", "g8f6", "c2c4", "g7g6"): [
        ("b1c3", "KID/Grunfeld waiting"),
    ],
    ("d2d4", "g8f6", "c2c4", "g7g6", "b1c3"): [
        ("d7d5", "Grunfeld"),
        ("f8g7", "KID fianchetto"),
    ],
    ("d2d4", "f7f5"): [
        ("c2c4", "Dutch mainline"),
    ],
    ("d2d4", "d7d5", "c2c4", "e7e6", "g1f3"): [
        ("g8f6", "QGD Orthodox"),
    ],
    ("d2d4", "d7d5", "c2c4", "c7c6"): [
        ("g1f3", "Slav/Semi-Slav"),
    ],
    ("d2d4", "d7d5", "c2c4", "c7c6", "g1f3"): [
        ("g8f6", "Slav ...Nf6"),
    ],
    ("g1f3", "d7d5", "c2c4"): [
        ("c7c6", "Semi-Slav vs Reti/English"),
    ],
    ("c2c4", "c7c5"): [
        ("g1f3", "Symmetrical English"),
    ],
    ("c2c4", "e7e5", "g1f3", "b8c6"): [
        ("b1c3", "English Four Knights"),
    ],
}

# Extended lines and variants (deeper moves)
BOOK_RESPONSES.update({
    # Ruy / Italian / Petrov branches
    ("e2e4", "e7e5", "g1f3"): [
        ("b8c6", "Ruy/Italian"),
        ("g8f6", "Petrov"),
        ("d7d6", "Philidor"),
    ],
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5"): [
        ("a7a6", "Ruy Lopez ...a6"),
        ("g8f6", "Berlin"),
        ("f8c5", "Classical/Italian"),
    ],
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1"): [
        ("f8e7", "Closed Ruy"),
        ("b7b5", "Marshall setup"),
        ("d7d6", "Steinitz"),
    ],
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7", "f1e1", "b7b5", "a4b3", "d7d6", "c2c3"): [
        ("e8g8", "Ruy main castle"),
        ("c8g4", "Chigorin idea"),
    ],
    ("e2e4", "e7e5", "g1f3", "g8f6"): [
        ("f1c4", "Italian Two Knights"),
        ("b1c3", "Four Knights"),
    ],
    ("e2e4", "e7e5", "g1f3", "b8c6", "b1c3", "g8f6"): [
        ("f1b5", "Spanish Four Knights"),
        ("f1c4", "Italian Four Knights"),
    ],

    # Sicilian branches
    ("e2e4", "c7c5", "g1f3"): [
        ("d7d6", "Najdorf setup"),
        ("e7e6", "Kan/Flex"),
        ("b8c6", "Classical Sicilian"),
        ("g7g6", "Accelerated Dragon"),
    ],
    ("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4"): [
        ("g8f6", "Sicilian Najdorf/Classic"),
        ("a7a6", "Najdorf early ...a6"),
    ],
    ("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3"): [
        ("a7a6", "Najdorf"),
        ("g7g6", "Dragon"),
        ("e7e5", "Classical ...e5"),
    ],
    ("e2e4", "c7c5", "g1f3", "e7e6", "d2d4", "c5d4", "f3d4", "b8c6", "b1c3"): [
        ("d7d6", "Scheveningen"),
        ("a7a6", "Kan/Taimanov"),
        ("g8f6", "Flexible ...Nf6"),
    ],
    ("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6", "f1e2"): [
        ("e7e5", "Najdorf ...e5"),
        ("e7e6", "Scheveningen"),
    ],

    # French / Caro / Scandinavian / Pirc
    ("e2e4", "e7e6", "d2d4", "d7d5", "b1c3"): [
        ("f8b4", "French Winawer"),
        ("g8f6", "French Classical"),
        ("c7c5", "French Tarrasch idea"),
    ],
    ("e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "f8b4", "c1d2"): [
        ("g8f6", "Winawer main"),
        ("b4c3", "Winawer capture"),
    ],
    ("e2e4", "c7c6", "d2d4", "d7d5", "b1c3"): [
        ("d5e4", "Caro main"),
        ("g8f6", "Caro ...Nf6"),
    ],
    ("e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4"): [
        ("f8f5", "Caro Classical"),
        ("b8d7", "Caro Karpov"),
    ],
    ("e2e4", "d7d5", "e4d5", "d8d5", "b1c3"): [
        ("d5d6", "Scandinavian ...Qd6"),
        ("d5a5", "Scandinavian ...Qa5"),
    ],
    ("e2e4", "g7g6"): [
        ("d2d4", "Modern/Pirc setup"),
        ("c2c3", "Flexible Modern"),
    ],
    ("e2e4", "d7d6", "d2d4", "g7g6", "b1c3"): [
        ("f8g7", "Pirc mainline"),
        ("c7c6", "Pirc Czech"),
    ],

    # Queen's Gambit / Slav / QGA / Catalan
    ("d2d4", "d7d5", "c2c4"): [
        ("e7e6", "QGD"),
        ("c7c6", "Slav"),
        ("d5c4", "QGA"),
    ],
    ("d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6"): [
        ("f8e7", "QGD Orthodox"),
        ("c7c6", "Semi-Slav"),
    ],
    ("d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5"): [
        ("f8e7", "QGD Lasker prep"),
        ("h7h6", "Anti-pin"),
    ],
    ("d2d4", "d7d5", "c2c4", "c7c6"): [
        ("g1f3", "Slav main"),
        ("b1c3", "Slav 3.Nc3"),
    ],
    ("d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3"): [
        ("e7e6", "Semi-Slav"),
        ("d5c4", "Slav"),
        ("a7a6", "Chebanenko"),
    ],
    ("d2d4", "d7d5", "c2c4", "e7e6", "g1f3"): [
        ("g8f6", "QGD Orthodox"),
        ("c7c5", "Tarrasch"),
    ],
    ("d2d4", "d7d5", "c2c4", "e7e6", "g1f3", "g8f6", "b1c3"): [
        ("c7c5", "Tarrasch"),
        ("f8e7", "Orthodox"),
    ],
    ("d2d4", "d7d5", "c2c4", "e7e6", "g2g3"): [
        ("g8f6", "Catalan ...Nf6"),
        ("c7c6", "Catalan ...c6"),
    ],

    # Indian setups (KID / Grunfeld)
    ("d2d4", "g8f6", "c2c4", "g7g6", "b1c3"): [
        ("d7d5", "Grunfeld"),
        ("f8g7", "KID fianchetto"),
    ],
    ("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5", "g1f3"): [
        ("f8g7", "Grunfeld main"),
        ("c7c6", "Grunfeld ...c6"),
    ],
    ("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d6", "g1f3"): [
        ("f8g7", "KID main"),
        ("e7e5", "KID ...e5"),
    ],

    # English / Reti depth
    ("c2c4", "e7e5", "g1f3"): [
        ("b8c6", "English Four Knights"),
        ("g8f6", "Symmetrical"),
    ],
    ("c2c4", "e7e5", "g1f3", "b8c6", "b1c3"): [
        ("g8f6", "English Four Knights"),
        ("f8b4", "English ...Bb4"),
    ],
    ("c2c4", "c7c5", "g1f3"): [
        ("g8f6", "Symmetrical"),
        ("b8c6", "Symmetrical ...Nc6"),
    ],
    ("g1f3", "d7d5", "c2c4"): [
        ("c7c6", "Semi-Slav vs Reti/English"),
        ("e7e6", "QGD setup vs Reti"),
    ],

    # London / systems
    ("d2d4", "g8f6", "c1f4"): [
        ("d7d5", "London solid"),
        ("c7c5", "London ...c5"),
    ],
    ("d2d4", "d7d5", "g1f3", "g8f6", "c1f4"): [
        ("e7e6", "London ...e6"),
        ("c7c5", "London ...c5"),
    ],
})


def get_book_reply(history: Sequence[str]) -> Optional[str]:
    """
    history: list/tuple of coordinate strings representing moves played so far.
    Returns a preferred reply string (coordinate notation) or None.
    """
    key = tuple(history)
    opts = BOOK_RESPONSES.get(key)
    if not opts:
        return None
    # opts is list of (move, name); pick one at random for variety
    move, _ = random.choice(opts)
    return move
