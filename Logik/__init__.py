"""Logic layer package for SpaceMath.

This package contains core game rules and mechanics.
"""

from .logik import MathProblem, check_answer, generate_problem, update_score

__all__ = ["MathProblem", "check_answer", "generate_problem", "update_score"]
