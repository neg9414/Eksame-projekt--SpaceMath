"""Data layer package for SpaceMath.

This package contains code that reads/writes persistent game data.
It is intentionally independent of any user interface code.
"""

from .data import Database

__all__ = ["Database"]
