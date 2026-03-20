"""Logic layer for SpaceMath.

This module contains the game rules and core mechanics. It does not depend on Pygame
or any user interface code.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MathProblem:
    left: int
    right: int
    operator: str
    answer: int


def generate_problem(max_value: int = 10) -> MathProblem:
    """Generate a simple addition or subtraction problem with non-negative answers."""
    left = random.randint(0, max_value)
    right = random.randint(0, max_value)
    operator = random.choice(["+", "-"])

    if operator == "-":
        # Ensure subtraction does not go below zero
        left, right = max(left, right), min(left, right)

    answer = left + right if operator == "+" else left - right
    return MathProblem(left=left, right=right, operator=operator, answer=answer)


def check_answer(problem: MathProblem, guess: int) -> bool:
    """Return True if the guess matches the correct answer."""
    return guess == problem.answer


def update_score(current_score: int, correct: bool) -> int:
    """Update a score based on whether the last answer was correct."""
    return current_score + 1 if correct else max(0, current_score - 1)
