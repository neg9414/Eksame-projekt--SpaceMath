"""Presentation layer for SpaceMath.

This module contains the Pygame user interface and is the only place where Pygame is imported.
"""

from __future__ import annotations

import sys
from typing import Optional

import pygame
import os

from Logik.logik import GameSession, generate_problem
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

        base_path = os.path.dirname(__file__)
        
        # Digital font for problems and answers
        try:
            digital_font_path = os.path.join(base_path, "Stastik", "digital-7.ttf")
            self.digital_font = pygame.font.Font(digital_font_path, 48)
        except:
            # Fallback to monospace if font not found
            self.digital_font = pygame.font.SysFont("monospace", 48, bold=True)

        self.db = Database()
        self.db.connect()
        self.student_id = self.db.add_student(student_name)

        # 🎮 GAME SESSION - Håndterer hele spilrunde logic
        self.game_session = GameSession()
        
        self.answer_text: str = ""
        self.feedback: str = ""
        self.feedback_timer = 0
        self.running = True
        
        # ⏱️ TIMER TIL AFSLUTTEDE SKÆRM
        self.completion_timer = 0

        self.x_offset = 0

        # 🎮 SPIL BAGGRUND
        path = os.path.join(base_path, "stastik", "spille_skeam.png")
        self.background = pygame.image.load(path)
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))

        # 🏠 MENU BAGGRUND (DIN NYE)
        menu_path = os.path.join(base_path, "stastik", "projekt_pro_start.png")
        self.menu_background = pygame.image.load(menu_path)
        self.menu_background = pygame.transform.scale(self.menu_background, (self.WIDTH, self.HEIGHT))

        # 🏁 COMPLETION BAGGRUND
        completion_path = os.path.join(base_path, "stastik", "slutside.png")
        try:
            self.completion_background = pygame.image.load(completion_path)
            self.completion_background = pygame.transform.scale(self.completion_background, (self.WIDTH, self.HEIGHT))
        except:
            # Fallback hvis billede ikke findes
            self.completion_background = None

        # 🏆 SCORE BAGGRUND
        score_path = os.path.join(base_path, "stastik", "score.png")
        try:
            self.score_background = pygame.image.load(score_path)
            self.score_background = pygame.transform.scale(self.score_background, (self.WIDTH, self.HEIGHT))
        except:
            # Fallback hvis billede ikke findes
            self.score_background = None

        # 🔄 STATE (menu eller game)
        self.state = "menu"

        # 🔘 SPIL KNAP
        self.play_button = pygame.Rect(self.WIDTH//2 - 100, self.HEIGHT//2, 200, 10)
        
        # 🏆 SE DIN SCORE KNAP (menu)
        self.score_button = pygame.Rect(self.WIDTH//2 - 120, self.HEIGHT//2 + 40, 240, 50)
        
        # 🔙 TILBAGE-KNAP (completion screen)
        self.back_button = pygame.Rect(self.WIDTH//2 - 75, 450, 150, 50)
        
        # 🔙 TILBAGE-KNAP (scores screen)
        self.scores_back_button = pygame.Rect(50, 50, 150, 50)

        # Buttons til spil
        self.button_rects: dict[str, pygame.Rect] = {}
        self._create_buttons()

        # New variables for preview and typing effect
        self.preview_timer = 0
        self.preview_operator = ""
        self.typing_timer = 0
        self.displayed_problem = ""
        self.displayed_answer = ""
        self.show_problem = False
        self.blink_timer = 0
        self.preview_circle_pos = (self.WIDTH // 2, self.HEIGHT // 2)

    def set_preview_circle_position(self, x: int, y: int) -> None:
        """Set the preview circle position anywhere on screen."""
        self.preview_circle_pos = (770, 610)

    def _draw_text(self, text: str, x: int, y: int, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        surface = self.font.render(text, True, color)
        rect = surface.get_rect(topleft=(x + self.x_offset, y))
        self.screen.blit(surface, rect)

    # 🏠 MENU RENDER
    def _render_menu(self):
        self.screen.blit(self.menu_background, (0, 0))

        mouse = pygame.mouse.get_pos()

        # SPIL HER knap
        color = (255, 255, 255)
        if self.play_button.collidepoint(mouse):
            color = (200, 200, 200)
        text = self.font.render("SPIL HER", True, (255, 255, 0))
        text_rect = text.get_rect(center=self.play_button.center)
        self.screen.blit(text, text_rect)
        
        # SE DIN SCORE link
        score_text = self.font.render("Se din score her", True, (255, 140, 0))
        score_text_rect = score_text.get_rect(center=(self.WIDTH // 2, self.score_button.centery))
        
        # Tjek om musen er over teksten
        mouse_over_score = score_text_rect.collidepoint(mouse)
        score_link_color = (255, 165, 0) if mouse_over_score else (255, 140, 0)
        score_text = self.font.render("Se din score her", True, score_link_color)
        score_text_rect = score_text.get_rect(center=(self.WIDTH // 2, self.score_button.centery))
        self.screen.blit(score_text, score_text_rect)
        # Tegn understreg
        underline_y = score_text_rect.bottom + 2
        pygame.draw.line(self.screen, score_link_color, (score_text_rect.left, underline_y), (score_text_rect.right, underline_y), 2)

        pygame.display.flip()

    # 🏆 SCORE SCREEN
    def _render_scores(self):
        """Tegn score-skærm med scores fra database."""
        # Tegn baggrund
        if self.score_background:
            self.screen.blit(self.score_background, (0, 0))
        else:
            # Fallback farve hvis billede ikke findes
            self.screen.fill((20, 20, 50))
        
        # Tilbage-knap
        mouse = pygame.mouse.get_pos()
        back_btn_color = (200, 100, 100) if self.scores_back_button.collidepoint(mouse) else (150, 50, 50)
        pygame.draw.rect(self.screen, back_btn_color, self.scores_back_button, border_radius=8)
        pygame.draw.rect(self.screen, (255, 200, 200), self.scores_back_button, 2, border_radius=8)
        back_text = self.font.render("Tilbage", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=self.scores_back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        # Vis scores fra database
        scores = self.db.get_all_games(self.student_id)  # Hent alle scores
        self._draw_text("Dine scores:", 100, 120, (255, 255, 0))
        y_offset = 180
        for i, game in enumerate(scores):
            score_info = f"Spil {i+1}: {game[3]}/10 korrekt - Score: {game[4]}"
            self._draw_text(score_info, 100, y_offset, (255, 255, 255))
            y_offset += 40
        
        pygame.display.flip()

    # ✅ COMPLETION SCREEN
    def _render_completed(self):
        """Tegn afsluttede skærm med score."""
        # Tegn baggrund
        if self.completion_background:
            self.screen.blit(self.completion_background, (0, 0))
        else:
            # Fallback farve hvis billede ikke findes
            self.screen.fill((30, 30, 60))
        
        # Stor font til Tillykke
        large_font = pygame.font.Font(None, 120)
        tillykke_text = large_font.render("Tillykke!", True, (255, 255, 0))
        tillykke_rect = tillykke_text.get_rect(center=(self.WIDTH // 2, 200))
        self.screen.blit(tillykke_text, tillykke_rect)
        
        # Stor font til Score
        score_font = pygame.font.Font(None, 80)
        score_text = score_font.render(f"Score: {self.game_session.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.WIDTH // 2, 350))
        self.screen.blit(score_text, score_rect)
        
        # Tilbage-knap
        mouse = pygame.mouse.get_pos()
        button_color = (200, 100, 100) if self.back_button.collidepoint(mouse) else (150, 50, 50)
        pygame.draw.rect(self.screen, button_color, self.back_button, border_radius=8)
        pygame.draw.rect(self.screen, (255, 200, 200), self.back_button, 2, border_radius=8)
        button_text = self.font.render("Tilbage", True, (255, 255, 255))
        button_rect = button_text.get_rect(center=self.back_button.center)
        self.screen.blit(button_text, button_rect)
        
        pygame.display.flip()

    def _create_buttons(self) -> None:
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
                if label:
                    self.button_rects[label] = pygame.Rect(x, y, btn_w, btn_h)

    def _draw_buttons(self) -> None:
        for label, rect in self.button_rects.items():
            pygame.draw.rect(self.screen, (50, 50, 120), rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 200, 255), rect, 2, border_radius=8)
            text_surf = self.font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def _handle_button_click(self, pos: tuple[int, int]) -> None:
        for label, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                if label == "OK":
                    self._handle_submit()
                elif label in ("C", "Slet"):
                    if label == "Slet":
                        self.answer_text = self.answer_text[:-1]
                    else:
                        self.answer_text = ""
                else:
                    self.answer_text += label
                return

    # 🎮 SPIL RENDER
    def _render(self) -> None:
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, 0))
        
        # Show progress next to SpaceMath
        current_problem = min(self.game_session.problems_solved + 1, self.game_session.PROBLEMS_PER_ROUND)
        progress = f"{current_problem}/{self.game_session.PROBLEMS_PER_ROUND}"
        self._draw_text("SpaceMath", 80, 30, (255, 255, 0))
        self._draw_text(progress, 400, 30, (255, 255, 255))
        
        self._draw_text(f"Score: {self.game_session.score}", 720, 700, (0, 0, 0))
        
        if self.preview_timer > 0:
            # Show preview button
            self._draw_preview_button()
            # Start showing problem after 2 blinks (about 40 frames)
            if self.blink_timer >= 40 and not self.show_problem:
                self.show_problem = True
                self.typing_timer = 0
                self.displayed_problem = ""
                self.displayed_answer = ""
            if self.show_problem:
                self._update_typing_effect()
                self._draw_digital_text(self.displayed_problem, 80, 530, (255, 255, 255))
                self._draw_digital_text(self.displayed_answer, 320, 530, (255, 255, 255))
        elif self.feedback_timer > 0:
            # Vis kun feedback når der er feedback
            self._draw_digital_text(self.feedback, 80, 530, (255, 255, 255))
        else:
            # Vis problem og input når der ikke er feedback
            self._update_typing_effect()
            self._draw_digital_text(self.displayed_problem, 80, 530, (255, 255, 255))
            self._draw_digital_text(self.displayed_answer, 320, 530, (255, 255, 255))

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0:
                self.feedback = ""
                # Start preview for next problem
                if self.game_session.problems_solved < self.game_session.PROBLEMS_PER_ROUND:
                    self._start_preview()
                else:
                    # Runde er færdig, gå til completion screen
                    self.state = "completed"

        self._draw_buttons()
        self._draw_text("Click buttons to answer, Esc to quit", 200, 440, (180, 180, 180))
        pygame.display.flip()

    def _draw_preview_button(self) -> None:
        """Draw the blinking preview button for next operator."""
        # Blink with longer on-time: 10 frames on, 10 frames off
        if (self.blink_timer // 10) % 2 == 0:
            color = (170, 50, 50) if self.preview_operator == "-" else (50, 170, 50)
            x, y = self.preview_circle_pos
            pygame.draw.circle(self.screen, color, (770, 610), 40)

    def _start_preview(self) -> None:
        """Start the preview phase for the next problem."""
        next_problem = generate_problem()
        self.preview_operator = next_problem.operator
        self.preview_timer = 9999  # Keep preview active until answer
        self.blink_timer = 0
        self.typing_timer = 0  # Reset typing effect
        self.game_session.current_problem = next_problem
        self.displayed_problem = ""
        self.displayed_answer = ""
        self.show_problem = False

    def _update_typing_effect(self) -> None:
        """Update the typing effect for problem and answer."""
        problem = self.game_session.current_problem
        full_problem = f"{problem.left} {problem.operator} {problem.right} ="
        
        if self.typing_timer % 5 == 0:  # Every 5 frames, add a character (faster)
            if len(self.displayed_problem) < len(full_problem):
                self.displayed_problem = full_problem[:len(self.displayed_problem) + 1]
        
        # Always show full answer as user types
        self.displayed_answer = self.answer_text
        self.typing_timer += 1

    def _draw_digital_text(self, text: str, x: int, y: int, color: tuple[int, int, int]) -> None:
        """Draw text with digital font."""
        surface = self.digital_font.render(text, True, color)
        rect = surface.get_rect(topleft=(x + self.x_offset, y))
        self.screen.blit(surface, rect)

    def _handle_submit(self) -> None:
        """Håndterer indsendt svar."""
        if not self.answer_text.strip():
            return
        
        # Valider input
        try:
            guess = int(self.answer_text.strip())
        except ValueError:
            self.feedback = "Skriv kun tal"
            self.answer_text = ""
            return

        # Lad game_session håndtere svaret
        result = self.game_session.submit_answer(guess)
        
        # Opdater UI baseret på resultat
        self.feedback = result["feedback"]
        self.feedback_timer = 90
        self.answer_text = ""
        self.preview_timer = 0  # Stop preview
        self.show_problem = False
        self.blink_timer = 0
        
        # ✅ TJEK OM RUNDE ER FÆRDIG
        if result["is_complete"]:
            # Gem hele runden til database
            self.db.save_game(self.student_id, result["score"], result["problems_solved"])
            # Gå til afsluttede skærm efter feedback vises
            # (feedback_timer håndterer overgangen i _render())
            self.state = "game"  # Bliv i game state mens feedback vises
        
        # Preview startes når feedback_timer når 0 (se _render)

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "menu":
                        score_text = self.font.render("Se din score her", True, (255, 140, 0))
                        score_text_rect = score_text.get_rect(center=(self.WIDTH // 2, self.score_button.centery))
                        if self.play_button.collidepoint(event.pos):
                            self.state = "game"
                            # Reset for ny runde
                            self.game_session.reset()
                            self.answer_text = ""
                            self.feedback = ""
                            self.preview_timer = 0
                            self.typing_timer = 0
                            self.displayed_problem = ""
                            self.displayed_answer = ""
                            # Start preview for first problem
                            self._start_preview()
                        elif score_text_rect.collidepoint(event.pos):
                            self.state = "scores"
                    elif self.state == "game":
                        self._handle_button_click(event.pos)
                    elif self.state == "completed":
                        if self.back_button.collidepoint(event.pos):
                            self.state = "menu"
                    elif self.state == "scores":
                        if self.scores_back_button.collidepoint(event.pos):
                            self.state = "menu"

            # 🔄 SKIFT MELLEM MENU, SPIL OG AFSLUTTET
            if self.state == "menu":
                self._render_menu()
            elif self.state == "scores":
                self._render_scores()
            elif self.state == "completed":
                # Viser completion screen med Tilbage-knap
                self._render_completed()
            else:  # game
                self._render()
                # Preview timer counts down only if not showing problem yet
                if self.preview_timer > 0:
                    self.blink_timer += 1

            self.clock.tick(30)

        self.db.close()
        pygame.quit()
        sys.exit()