"""Logic lag for SpaceMath.
indholder spillet regler og logik, såsom at generere opgaver, tjekke svar og holde styr på score osv. uafhængigt af UI, pygame og data lag
"""

from __future__ import annotations

#jeg bruger random til at lave opgaver og dataclass til at strukturere data
import random
from dataclasses import dataclass
from typing import Tuple

#jeg bruger dataclass for at gøre det nemt at oprette og arbejde med data og frozen=True betyder at objektet ikke kan ændres efter det er lavet
@dataclass(frozen=True)
class MathProblem:
    left: int
    right: int
    operator: str
    answer: int

#laver en ny matematik problem og søger for at det ikke bliver i minus og til sidst returnere det som en MathProblem dataclass
def generate_problem(max_value: int = 10) -> MathProblem:
    left = random.randint(0, max_value)
    right = random.randint(0, max_value)
    operator = random.choice(["+", "-"])

    if operator == "-":
        left, right = max(left, right), min(left, right)

    answer = left + right if operator == "+" else left - right
    return MathProblem(left=left, right=right, operator=operator, answer=answer)

#rigtigt eller forkert
def check_answer(problem: MathProblem, guess: int) -> bool:
    return guess == problem.answer

#plusser 1 til score hvis det er rigtigt, ellers forbliver det det samme
def update_score(current_score: int, correct: bool) -> int:
    return current_score + 1 if correct else current_score

#styrrer spillet, score, antal opgaver løst og nuværdende opgaver
class GameSession:
    PROBLEMS_PER_ROUND = 10  # antal opgaver per runde

#starter ny spille runde
    def __init__(self):
        self.problems_solved = 0
        self.score = 0

#med en generate tilfældig problem
        self.current_problem: MathProblem = generate_problem()

#kernen i spillet, tjekker svar, opdaterer scorer, tæller løste opgaver, gernerer ny opgaver og returnere en en dictionary med info  
    def submit_answer(self, guess: int) -> dict:

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
        self.problems_solved = 0
        self.score = 0
        self.current_problem = generate_problem()
    
    def get_current_problem(self) -> MathProblem:
#returnerer den nuværende opgave
        return self.current_problem
