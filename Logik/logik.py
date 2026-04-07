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
    return current_score + 1 if correct else current_score


class GameSession:
    """Håndterer en hel spilrunde (10 opgaver)."""
    
    PROBLEMS_PER_ROUND = 10  # Antal opgaver per runde
    
    def __init__(self):
        self.problems_solved = 0
        self.score = 0
        self.current_problem: MathProblem = generate_problem()
    
    def submit_answer(self, guess: int) -> dict:
        """Håndterer spiller-svar og returnerer feedbackinfo.
        
        Returns:
            dict med keys:
                - 'correct': bool (svar var korrekt)
                - 'feedback': str (feedback til spiller)
                - 'score': int (nuværende score)
                - 'problems_solved': int (antal løste opgaver)
                - 'is_complete': bool (er runde færdig?)
        """
        correct = check_answer(self.current_problem, guess)
        self.score = update_score(self.score, correct)
        self.problems_solved += 1
        
        feedback = "Rigtigt!" if correct else "Prøv igen."
        is_complete = self.problems_solved >= self.PROBLEMS_PER_ROUND
        
        if not is_complete:
            self.current_problem = generate_problem()
        
        return {
            "correct": correct,
            "feedback": feedback,
            "score": self.score,
            "problems_solved": self.problems_solved,
            "is_complete": is_complete
        }
    
    def reset(self) -> None:
        """Reset for ny runde."""
        self.problems_solved = 0
        self.score = 0
        self.current_problem = generate_problem()
    
    def get_current_problem(self) -> MathProblem:
        """Returnerer nuværende opgave."""
        return self.current_problem
