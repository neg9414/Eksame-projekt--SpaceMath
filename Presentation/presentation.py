"""Presentation lag for SpaceMath.
her er alt det visuelle i spillet (UI).
det er også her Pygame bliver brugt, så resten af projektet ikke er afhængigt af det.
"""

#import af de nødvendige ting fra Pygame og andre moduler
from __future__ import annotations

import pygame
import os
import sys
from typing import Optional

#GameSession styrer selve spillets regler og logik og generate_problem laver nye matematikopgaver
from Logik.logik import GameSession, generate_problem

#database bruges til at gemme elever og deres scores i en SQLite database, så det kan vises i spillet og i læreroversigten
from Data.data import Database

#denne klasse styrer hele spillet som, tegne på skærmen, input og game loop. Selve logikken bag det hele ligger i GameSession, så jeg holder det adskilt.
class SpaceMathGame:

    WIDTH = 940
    HEIGHT = 780

#her sætter jeg spillet op, indlæser billeder og fonts, opretter forbindelse til database osv. 
    def __init__(self, student_name: str = "Elev"):
        pygame.init()

#opretter vindue og sætter titel
        pygame.display.set_caption("SpaceMath")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.score_font = pygame.font.SysFont("Consolas", 36)

        base_path = os.path.dirname(__file__)
        assets_path = os.path.join(base_path, "Stastik")
        
        try:
            digital_font_path = os.path.join(assets_path, "digital-7.ttf")
            self.digital_font = pygame.font.Font(digital_font_path, 48)
        except Exception:
            self.digital_font = pygame.font.SysFont("monospace", 48, bold=True)

#database bruges til at gemme spilleners data
        self.db = Database()
        self.db.connect()

#opretter elve i databse og gemmer id
        self.student_id = self.db.add_student(student_name)

#hele spilrunde logic
        self.game_session = GameSession()
        
        self.answer_text: str = ""
        self.feedback: str = ""
        self.feedback_timer = 0
        self.running = True
        self.preview_active = False

        self.x_offset = 0

        path = os.path.join(assets_path, "spil.png")
        self.background = pygame.image.load(path)
        self.background = pygame.transform.scale(self.background, (self.WIDTH, self.HEIGHT))

        menu_path = os.path.join(assets_path, "menu.png")
        self.menu_background = pygame.image.load(menu_path)
        self.menu_background = pygame.transform.scale(self.menu_background, (self.WIDTH, self.HEIGHT))

        completion_path = os.path.join(assets_path, "slut.png")
        try:
            self.completion_background = pygame.image.load(completion_path)
            self.completion_background = pygame.transform.scale(self.completion_background, (self.WIDTH, self.HEIGHT))
        except:
            self.completion_background = None

        score_path = os.path.join(assets_path, "score.png")
        try:
            self.score_background = pygame.image.load(score_path)
            self.score_background = pygame.transform.scale(self.score_background, (self.WIDTH, self.HEIGHT))
        except Exception:
            self.score_background = None

        start_path = os.path.join(assets_path, "start.png")
        try:
            self.start_background = pygame.image.load(start_path)
            self.start_background = pygame.transform.scale(self.start_background, (self.WIDTH, self.HEIGHT))
        except:
            self.start_background = None

#jeg bruger et state system til at styre spillets flow, så jeg kan have forsekllige skærme
        self.state = "start"

        button_width = 220
        button_height = 70
        button_x = self.WIDTH // 2 - button_width // 2
        self.elev_button = pygame.Rect(button_x, 340, button_width, button_height)
        self.teacher_button = pygame.Rect(button_x, 440, button_width, button_height)

        self.play_button = pygame.Rect(self.WIDTH//2 - 100, self.HEIGHT//2, 200, 10)
        
        self.score_button = pygame.Rect(self.WIDTH//2 - 120, self.HEIGHT//2 + 40, 240, 50)
        
        self.back_button = pygame.Rect(self.WIDTH//2 - 75, 450, 150, 50)
        
        self.scores_back_button = pygame.Rect(50, 50, 150, 50)

        self.teacher_back_button = pygame.Rect(50, 50, 150, 50)

        self.button_rects: dict[str, pygame.Rect] = {}
        self._create_buttons()

        self.preview_operator = ""
        self.typing_timer = 0
        self.displayed_problem = ""
        self.displayed_answer = ""
        self.show_problem = False
        self.blink_timer = 0
        self.preview_circle_pos = (self.WIDTH // 2, self.HEIGHT // 2)

    def _draw_text(self, text: str, x: int, y: int, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        surface = self.font.render(text, True, color)
        rect = surface.get_rect(topleft=(x + self.x_offset, y))
        self.screen.blit(surface, rect)

#her bliver spillet tegnet hver frame af game loppet
    def _render_menu(self):
        self.screen.blit(self.menu_background, (0, 0))

        mouse = pygame.mouse.get_pos()

        color = (255, 255, 255)
        if self.play_button.collidepoint(mouse):
            color = (200, 200, 200)
        text = self.font.render("SPIL HER", True, (255, 255, 0))
        text_rect = text.get_rect(center=self.play_button.center)
        self.screen.blit(text, text_rect)
        
        score_text = self.font.render("Se din score her", True, (255, 140, 0))
        score_text_rect = score_text.get_rect(center=(self.WIDTH // 2, self.score_button.centery))

        mouse_over_score = score_text_rect.collidepoint(mouse)
        score_link_color = (255, 165, 0) if mouse_over_score else (255, 140, 0)
        score_text = self.font.render("Se din score her", True, score_link_color)
        score_text_rect = score_text.get_rect(center=(self.WIDTH // 2, self.score_button.centery))
        self.screen.blit(score_text, score_text_rect)
        underline_y = score_text_rect.bottom + 2
        pygame.draw.line(self.screen, score_link_color, (score_text_rect.left, underline_y), (score_text_rect.right, underline_y), 2)

        pygame.display.flip()


    def _render_start(self):
        if self.start_background:
            self.screen.blit(self.start_background, (0, 0))
        else:
            self.screen.fill((10, 10, 40))

        mouse = pygame.mouse.get_pos()
        for rect, label in [(self.teacher_button, "Lærer"), (self.elev_button, "Elev")]:
            btn_color = (200, 100, 100) if rect.collidepoint(mouse) else (150, 50, 50)
            pygame.draw.rect(self.screen, btn_color, rect, border_radius=12)
            pygame.draw.rect(self.screen, (255, 200, 200), rect, 2, border_radius=12)
            text = self.font.render(label, True, (255, 255, 255))
            self.screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()

    def _render_teacher_overview(self):
        if self.score_background:
            self.screen.blit(self.score_background, (0, 0))
        else:
            self.screen.fill((20, 20, 40))

        mouse = pygame.mouse.get_pos()
        title = self.score_font.render("Læreroversigt", True, (255, 255, 0))
        title_rect = title.get_rect(center=(self.WIDTH // 2, 70))
        self.screen.blit(title, title_rect)

        pygame.draw.rect(self.screen, (200, 100, 100) if self.teacher_back_button.collidepoint(mouse) else (150, 50, 50), self.teacher_back_button, border_radius=8)
        pygame.draw.rect(self.screen, (255, 200, 200), self.teacher_back_button, 2, border_radius=8)
        back_text = self.font.render("Tilbage", True, (255, 255, 255))
        self.screen.blit(back_text, back_text.get_rect(center=self.teacher_back_button.center))

        students = self.db.get_all_students()
        y_offset = 160
        header = self.score_font.render("Navn                Runder    Point", True, (30, 30, 30))
        self.screen.blit(header, (80, y_offset))
        y_offset += 40

        if students:
            for student in students:
                text = f"{student['name']:<15} {student['games_played']:>6}    {student['total_score']:>6}"
                line = self.score_font.render(text, True, (30, 30, 30))
                self.screen.blit(line, line.get_rect(topleft=(80, y_offset)))
                y_offset += 35
                if y_offset > self.HEIGHT - 80:
                    break
        else:
            line = self.score_font.render("Ingen elever fundet endnu.", True, (30, 30, 30))
            self.screen.blit(line, line.get_rect(topleft=(80, y_offset)))

        pygame.display.flip()

    def _render_scores(self):
        if self.score_background:
            self.screen.blit(self.score_background, (0, 0))
        else:
            self.screen.fill((20, 20, 50))
        
        mouse = pygame.mouse.get_pos()
        back_btn_color = (200, 100, 100) if self.scores_back_button.collidepoint(mouse) else (150, 50, 50)
        pygame.draw.rect(self.screen, back_btn_color, self.scores_back_button, border_radius=8)
        pygame.draw.rect(self.screen, (255, 200, 200), self.scores_back_button, 2, border_radius=8)
        back_text = self.font.render("Tilbage", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=self.scores_back_button.center)
        self.screen.blit(back_text, back_text_rect)
        
        scores = self.db.get_all_games(self.student_id)  # Hent alle scores
        title_text = self.score_font.render("Dine scores:", True, (20, 20, 20))
        self.screen.blit(title_text, title_text.get_rect(topleft=(100, 120)))
        y_offset = 180
        for i, game in enumerate(scores):
            score_info = f"Spil {i+1}: {game['problems_solved']}/10 korrekt - Score: {game['score']}"
            score_line = self.score_font.render(score_info, True, (30, 30, 30))
            self.screen.blit(score_line, score_line.get_rect(topleft=(100, y_offset)))
            y_offset += 40
        
        pygame.display.flip()

    def _render_completed(self):

        if self.completion_background:
            self.screen.blit(self.completion_background, (0, 0))
        else:
            self.screen.fill((30, 30, 60))
        
        large_font = pygame.font.Font(None, 120)
        tillykke_text = large_font.render("Tillykke!", True, (255, 255, 0))
        tillykke_rect = tillykke_text.get_rect(center=(self.WIDTH // 2, 200))
        self.screen.blit(tillykke_text, tillykke_rect)

        score_font = pygame.font.Font(None, 80)
        score_text = score_font.render(f"Score: {self.game_session.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.WIDTH // 2, 350))
        self.screen.blit(score_text, score_rect)

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
                elif label == "Slet":
                    self.answer_text = self.answer_text[:-1]
                else:
                    self.answer_text += label
                return

    def _render(self) -> None:
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.background, (0, 0))

        current_problem = min(self.game_session.problems_solved + 1, self.game_session.PROBLEMS_PER_ROUND)
        progress = f"{current_problem}/{self.game_session.PROBLEMS_PER_ROUND}"
        self._draw_text("SpaceMath", 80, 30, (255, 255, 0))
        self._draw_text(progress, 400, 30, (255, 255, 255))
        
        self._draw_text(f"Score: {self.game_session.score}", 720, 700, (0, 0, 0))
        
        if self.preview_active:
            self._draw_preview_button()
# viser ploblemmet efter 2 blinks
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
            self._draw_digital_text(self.feedback, 80, 530, (255, 255, 255))
        else:
            self._update_typing_effect()
            self._draw_digital_text(self.displayed_problem, 80, 530, (255, 255, 255))
            self._draw_digital_text(self.displayed_answer, 320, 530, (255, 255, 255))

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0:
                self.feedback = ""
#starter preview for næste problem
                if self.game_session.problems_solved < self.game_session.PROBLEMS_PER_ROUND:
                    self._start_preview()
                else:
                    self.state = "completed"

        self._draw_buttons()
        self._draw_text("Click buttons to answer, Esc to quit", 200, 440, (180, 180, 180))
        pygame.display.flip()

    def _draw_preview_button(self) -> None:
        if (self.blink_timer // 10) % 2 == 0:
            color = (170, 50, 50) if self.preview_operator == "-" else (50, 170, 50)
            x, y = self.preview_circle_pos
            pygame.draw.circle(self.screen, color, (770, 610), 40)

    def _start_preview(self) -> None:
        next_problem = generate_problem()
        self.preview_operator = next_problem.operator
        self.preview_active = True
        self.blink_timer = 0
        self.typing_timer = 0  #reset typing effect
        self.game_session.current_problem = next_problem
        self.displayed_problem = ""
        self.displayed_answer = ""
        self.show_problem = False

    def _update_typing_effect(self) -> None:
        problem = self.game_session.current_problem
        full_problem = f"{problem.left} {problem.operator} {problem.right} ="
        
        if self.typing_timer % 5 == 0:
            if len(self.displayed_problem) < len(full_problem):
                self.displayed_problem = full_problem[:len(self.displayed_problem) + 1]
        
        self.displayed_answer = self.answer_text
        self.typing_timer += 1

    def _draw_digital_text(self, text: str, x: int, y: int, color: tuple[int, int, int]) -> None:
        surface = self.digital_font.render(text, True, color)
        rect = surface.get_rect(topleft=(x + self.x_offset, y))
        self.screen.blit(surface, rect)

#denne funktion håndterer når spilleren svarer. Jeg validerer først input (skal være tal), derefter sender jeg svaret til GameSession som så afgør om det er rigtigt eller forkert
    def _handle_submit(self) -> None:
        if not self.answer_text.strip():
            return       
        try:
            guess = int(self.answer_text.strip())
        except ValueError:
            self.feedback = "Skriv kun tal"
            self.answer_text = ""
            return

        result = self.game_session.submit_answer(guess)

        self.feedback = result["feedback"]
        self.feedback_timer = 90
        self.answer_text = ""
        self.preview_active = False  #stop preview
        self.show_problem = False
        self.blink_timer = 0
        
        if result["is_complete"]:
#gemmer hele runden til database
            self.db.save_game(self.student_id, result["score"], result["problems_solved"])
            self.state = "game"
        
#hjerte af mit spil, det er her alt sker og spillet kører. Jeg bruger start systemmet til at skifte mellem forskellige skærme. der sker også en håndtering af input, rendering for hver state og lukkelsen af databaseforbindelsen og pygame ordentligt når spillet sluttes
    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "start":
                        if self.elev_button.collidepoint(event.pos):
                            self.state = "menu"
                        elif self.teacher_button.collidepoint(event.pos):
                            self.state = "teacher"
                    elif self.state == "menu":
                        score_text = self.font.render("Se din score her", True, (255, 140, 0))
                        score_text_rect = score_text.get_rect(center=(self.WIDTH // 2, self.score_button.centery))
                        if self.play_button.collidepoint(event.pos):
                            self.state = "game"
                            #reset for ny runde
                            self.game_session.reset()
                            self.answer_text = ""
                            self.feedback = ""
                            self.preview_active = False
                            self.typing_timer = 0
                            self.displayed_problem = ""
                            self.displayed_answer = ""
                            #starter preview for første problem
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
                    elif self.state == "teacher":
                        if self.teacher_back_button.collidepoint(event.pos):
                            self.state = "start"

            if self.state == "start":
                self._render_start()
            elif self.state == "menu":
                self._render_menu()
            elif self.state == "scores":
                self._render_scores()
            elif self.state == "completed":
                self._render_completed()
            elif self.state == "teacher":
                self._render_teacher_overview()
            else:  # game
                self._render()
                if self.preview_active:
                    self.blink_timer += 1

            self.clock.tick(30)

        self.db.close()
        pygame.quit()
        sys.exit()
#når spillet lukker, slutter dadabaseforbindelsen og pygame ordentligt, så der ikke er noget tilbage der kører i baggrunden eller åbne forbindelser