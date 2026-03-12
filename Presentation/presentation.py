"""Presentation layer for SpaceMath.

This module contains the Pygame user interface and is the only place where Pygame is imported.
"""

from __future__ import annotations

import sys
from typing import Optional

import pygame

from Logik.logik import MathProblem, check_answer, generate_problem, update_score
from Data.data import Database


class SpaceMathGame:
    """A minimal Pygame-based game loop for SpaceMath."""

    WIDTH = 640
    HEIGHT = 480

    def __init__(self, student_name: str = "Elev"):
        pygame.init()
        pygame.display.set_caption("SpaceMath")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        self.db = Database()
        self.db.connect()
        self.student_id = self.db.add_student(student_name)

        self.score = self.db.get_latest_score(self.student_id)
        self.problem: MathProblem = generate_problem()
        self.answer_text: str = ""
        self.feedback: str = ""
        self.running = True

    def _draw_text(self, text: str, y: int, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        surface = self.font.render(text, True, color)
        rect = surface.get_rect(center=(self.WIDTH // 2, y))
        self.screen.blit(surface, rect)

    def _render(self) -> None:
        self.screen.fill((0, 0, 20))
        self._draw_text("SpaceMath", 40)
        self._draw_text(f"Score: {self.score}", 90)
        self._draw_text(
            f"Problem: {self.problem.left} {self.problem.operator} {self.problem.right}", 150
        )
        self._draw_text(f"Answer: {self.answer_text}", 200)
        self._draw_text(self.feedback, 260, (200, 200, 0))

        self._draw_text("Type numbers, Enter to submit, Esc to quit", 420, (180, 180, 180))
        pygame.display.flip()

    def _handle_submit(self) -> None:
        if not self.answer_text.strip():
            return
        try:
            guess = int(self.answer_text.strip())
        except ValueError:
            self.feedback = "Skriv kun tal (f.eks. 5)"
            self.answer_text = ""
            return

        correct = check_answer(self.problem, guess)
        self.score = update_score(self.score, correct)
        self.db.save_score(self.student_id, self.score)

        self.feedback = "Rigtigt!" if correct else "Forkert - prøv igen."
        self.problem = generate_problem()
        self.answer_text = ""

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN:
                        self._handle_submit()
                    elif event.key == pygame.K_BACKSPACE:
                        self.answer_text = self.answer_text[:-1]
                    elif event.unicode.isdigit() or (event.unicode == "-" and not self.answer_text):
                        self.answer_text += event.unicode

            self._render()
            self.clock.tick(30)

        self.db.close()
        pygame.quit()
        sys.exit()
