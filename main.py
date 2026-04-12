#stanpunkt for programmet
#her starter jeg programmet, hvor jeg bruger argparse så man kan give et navn til spilleren uden at skulle ændre direkte i koden.
from __future__ import annotations

import argparse

from Presentation.presentation import SpaceMathGame


def main() -> None:
    parser = argparse.ArgumentParser(description="SpaceMath - math game for HTX Programmering B")
    parser.add_argument("--name", default="Elev", help="Name of the player (used for saving scores)")
    args = parser.parse_args()

#her opretter jeg selve spillet og sender spillerens navn med ind ,så det kan bruges til fx. scoreing i spillet
    game = SpaceMathGame(student_name=args.name)

#spillets hovdeloop
    game.run()


if __name__ == "__main__":
    main()