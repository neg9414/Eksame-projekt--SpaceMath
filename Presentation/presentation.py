"""Presentation layer for SpaceMath.

This module contains the Pygame user interface and is the only place where Pygame is imported.
"""

from __future__ import annotations

import sys
from typing import Optional

import pygame
import os

from Logik.logik import MathProblem, check_answer, generate_problem, update_score
from Data.data import Database


class SpaceMathGame:
    """A minimal Pygame-based game loop for SpaceMath."""

    WIDTH = 940
    HEIGHT = 780

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
        self.feedback_timer = 0  # frames count until feedback clears
        self.running = True

        # Global horizontal offset: sæt til negativ for venstre, positiv for højre.
        self.x_offset = 0

        base_path = os.path.dirname(__file__)  # mappen hvor presentation.py ligger
        path = os.path.join(base_path, "stastik", "spille_skeam.png")
        self.background = pygame.image.load(path)
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))

        # Layout buttons (digits + backspace + submit) so players use mouse clicks
        self.button_rects: dict[str, pygame.Rect] = {}
        self._create_buttons()

    def _draw_text(self, text: str, x: int, y: int, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        surface = self.font.render(text, True, color)
        rect = surface.get_rect(topleft=(x + self.x_offset, y))
        self.screen.blit(surface, rect)

    def _create_buttons(self) -> None:
        """Create button rectangles for the on-screen keypad."""
        btn_w, btn_h = 57, 37
        gap = 10
        start_x = (self.WIDTH - (btn_w * 3 + gap * 2)) // 12 + self.x_offset
        start_y = 650

        layout = [
            ["1", "2", "3", "4", "5", "", "OK"],
            ["6", "7", "8", "9", "0", "", "Slet"],
        ]

        for row_idx, row in enumerate(layout):
            for col_idx, label in enumerate(row):
                x = start_x + col_idx * (btn_w + gap)
                y = start_y + row_idx * (btn_h + gap)
                if label:  # Only create buttons for non-empty labels
                    self.button_rects[label] = pygame.Rect(x, y, btn_w, btn_h)

    def _draw_buttons(self) -> None:
        """Render on-screen keypad buttons."""
        for label, rect in self.button_rects.items():
            pygame.draw.rect(self.screen, (50, 50, 120), rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 200, 255), rect, 2, border_radius=8)
            text_surf = self.font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def _handle_button_click(self, pos: tuple[int, int]) -> None:
        """Update input based on which on-screen button was clicked."""
        for label, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                if label == "OK":
                    self._handle_submit()
                elif label in ("C", "Slet"):
                    # Remove last character when Slet is pressed, or clear all when C is used.
                    if label == "Slet":
                        self.answer_text = self.answer_text[:-1]
                    else:
                        self.answer_text = ""
                else:
                    # Append digit to the answer text
                    self.answer_text += label
                return

    def _render(self) -> None:
        self.screen.fill((0, 0, 0))  # Ensure full clear before redraw (avoid any ghosting)
        self.screen.blit(self.background, (0, 0))
        self._draw_text("SpaceMath", 80, 30, (255, 255, 0))
        self._draw_text(f"Score: {self.score}", 720, 700, (0, 0, 0))
        self._draw_text(
            f"Problem: {self.problem.left} {self.problem.operator} {self.problem.right}", 80, 540
        )
        self._draw_text(f"Answer: {self.answer_text}", 320, 540)
        self._draw_text(self.feedback, 430, 540, (200, 200, 0))

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0:
                self.feedback = ""

        self._draw_buttons()
        self._draw_text("Click buttons to answer, Esc to quit", 200, 440, (180, 180, 180))
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

        self.feedback = "Rigtigt!" if correct else "Prøv igen."
        self.feedback_timer = 60  # keep feedback for ~2 seconds at 30 FPS
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
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_button_click(event.pos)

            self._render()
            self.clock.tick(30)

        self.db.close()
        pygame.quit()
        sys.exit()
