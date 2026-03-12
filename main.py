from __future__ import annotations

import argparse

from Presentation.presentation import SpaceMathGame


def main() -> None:
    parser = argparse.ArgumentParser(description="SpaceMath - math game for HTX Programmering B")
    parser.add_argument("--name", default="Elev", help="Name of the player (used for saving scores)")
    args = parser.parse_args()

    game = SpaceMathGame(student_name=args.name)
    game.run()


if __name__ == "__main__":
    main()
