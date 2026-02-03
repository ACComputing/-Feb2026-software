#!/usr/bin/env python3
"""
ULTRA!SNAKE  —  files = off  —  program.py
60 FPS · Famicom speed · Famicom graphics · Famicom beeps & boops
No external files. All assets procedural.
"""

import pygame
import math
import array
import random

# === INIT ===
pygame.init()
pygame.mixer.init(44100, -16, 2, 512)

# === CONSTANTS (Famicom-style) ===
FPS = 60
SCALE = 3
NES_W, NES_H = 256, 240
W, H = NES_W * SCALE, NES_H * SCALE
TILE = 16
GRID_W = NES_W // TILE   # 16
GRID_H = NES_H // TILE   # 15
# Famicom speed: move one tile every 8 frames (~7.5 moves/sec at 60fps)
MOVE_EVERY_FRAMES = 8

# NES-like palette
class Pal:
    BLACK = (0, 0, 0)
    WHITE = (252, 252, 252)
    DARK_GRAY = (84, 84, 84)
    LIGHT_GRAY = (168, 168, 168)
    GREEN_DARK = (0, 168, 0)
    GREEN = (0, 200, 0)
    GREEN_LIGHT = (128, 248, 128)
    RED = (216, 40, 0)
    YELLOW = (252, 216, 0)
    BLUE = (0, 120, 248)
    BG = (0, 56, 0)          # Dark green playfield
    BORDER = (0, 88, 0)
    SNAKE_HEAD = (0, 248, 0)
    SNAKE_BODY = (0, 200, 0)
    APPLE = (248, 0, 0)
    TEXT = (252, 252, 252)
    # OG Snake / terminal
    CRT_BG = (0, 12, 0)
    CRT_GREEN = (0, 255, 0)
    CRT_DIM = (0, 180, 0)
    CRT_BORDER = (0, 80, 0)

# === AUDIO: Famicom beeps & boops (no external files) ===
SFX = {}

def famicom_wave(freq, duration, volume=0.2, wave="sq"):
    sample_rate = 44100
    n = int(sample_rate * duration)
    buf = array.array("h")
    for i in range(n):
        t = i / sample_rate
        if wave == "sq":
            v = 1.0 if (int(t * freq * 2) % 2 == 0) else -1.0
        else:
            v = 2.0 * abs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
        env = max(0, 1.0 - (i / n) * 1.2)
        s = int(v * 32767 * volume * env)
        buf.append(s)
        buf.append(s)
    return pygame.mixer.Sound(buffer=buf)

def famicom_slide(start_hz, end_hz, duration, volume=0.2):
    sample_rate = 44100
    n = int(sample_rate * duration)
    buf = array.array("h")
    for i in range(n):
        t = i / sample_rate
        progress = i / n
        freq = start_hz + (end_hz - start_hz) * progress
        v = 1.0 if (int(t * freq * 2) % 2 == 0) else -1.0
        env = max(0, 1.0 - progress * 1.1)
        s = int(v * 32767 * volume * env)
        buf.append(s)
        buf.append(s)
    return pygame.mixer.Sound(buffer=buf)

def init_sfx():
    SFX["eat"] = famicom_wave(440, 0.08, 0.2, "sq")
    SFX["eat"].set_volume(0.5)
    SFX["eat2"] = famicom_wave(880, 0.06, 0.15, "sq")
    SFX["gameover"] = famicom_slide(400, 80, 0.35, 0.22)
    SFX["start"] = famicom_wave(523, 0.12, 0.2, "sq")
    SFX["menu_move"] = famicom_wave(220, 0.06, 0.15, "sq")
    SFX["menu_accept"] = famicom_wave(440, 0.1, 0.2, "sq")

def play_sfx(key):
    if key in SFX and SOUND_ENABLED:
        SFX[key].play()

# Global: can be toggled in Settings
SOUND_ENABLED = True

# Menu state
MENU_MAIN = "menu"
MENU_HOWTO = "howto"
MENU_CREDITS = "credits"
MENU_ABOUT = "about"
MENU_SETTINGS = "settings"
MENU_EXIT_PROMPT = "exit_prompt"
STATE_GAME = "game"

MENU_ITEMS = [
    "GAME",
    "HOW TO PLAY",
    "CREDITS",
    "ABOUT",
    "GAME SOUND",
    "SETTINGS",
    "EXIT",
]

HOWTO_TEXT = [
    "Move: Arrow keys (UP/DOWN/LEFT/RIGHT)",
    "Eat the red apples to grow and score.",
    "Do not hit the walls or your own tail.",
    "Each apple = 10 points.",
]

CREDITS_TEXT = [
    "ULTRA!SNAKE by MR.AC",
    "",
    "Original Snake: Gremlin (1976)",
    "Blockade / Snake concept:",
    "  early arcade & Nibbler devs.",
    "Thanks to the OG snake",
    "programmers who started it all.",
    "",
    "This version: Famicom-style,",
    "procedural sound, files=off.",
]

ABOUT_TEXT = [
    "A classic Snake game with Famicom",
    "aesthetics. Single file, no external",
    "resources. Made for fun.",
]

# === GAME STATE ===
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("ULTRA!SNAKE  —  files=off")
        self.surf = pygame.Surface((NES_W, NES_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 40)
        init_sfx()
        self.reset()

    def reset(self):
        cx, cy = GRID_W // 2, GRID_H // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.dx, self.dy = 1, 0
        self.apple = self.spawn_apple()
        self.score = 0
        self.frame_count = 0
        self.game_over = False
        self.started = False
        self.move_counter = 0

    def spawn_apple(self):
        while True:
            ax = random.randint(1, GRID_W - 2)
            ay = random.randint(1, GRID_H - 2)
            if (ax, ay) not in self.snake:
                return (ax, ay)

    def update(self, keys):
        if self.game_over:
            return
        if not self.started:
            if keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                self.started = True
                play_sfx("start")
            return

        self.frame_count += 1
        self.move_counter += 1
        if self.move_counter < MOVE_EVERY_FRAMES:
            return
        self.move_counter = 0

        head = self.snake[0]
        nx = head[0] + self.dx
        ny = head[1] + self.dy
        if nx <= 0 or nx >= GRID_W - 1 or ny <= 0 or ny >= GRID_H - 1:
            self.game_over = True
            play_sfx("gameover")
            return
        if (nx, ny) in self.snake:
            self.game_over = True
            play_sfx("gameover")
            return

        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.apple:
            self.score += 10
            play_sfx("eat")
            play_sfx("eat2")
            self.apple = self.spawn_apple()
        else:
            self.snake.pop()

    def handle_input(self, keys):
        if self.game_over:
            return
        if keys[pygame.K_UP] and self.dy != 1:
            self.dx, self.dy = 0, -1
        elif keys[pygame.K_DOWN] and self.dy != -1:
            self.dx, self.dy = 0, 1
        elif keys[pygame.K_LEFT] and self.dx != 1:
            self.dx, self.dy = -1, 0
        elif keys[pygame.K_RIGHT] and self.dx != -1:
            self.dx, self.dy = 1, 0

    def draw(self):
        self.surf.fill(Pal.BG)
        # Border (play area 1..GRID_W-2 x 1..GRID_H-2)
        pygame.draw.rect(self.surf, Pal.BORDER, (0, 0, NES_W, NES_H), 4)
        inner = pygame.Rect(TILE, TILE, NES_W - 2 * TILE, NES_H - 2 * TILE)
        pygame.draw.rect(self.surf, Pal.BLACK, inner)

        for i, (gx, gy) in enumerate(self.snake):
            x, y = gx * TILE, gy * TILE
            c = Pal.SNAKE_HEAD if i == 0 else Pal.SNAKE_BODY
            pygame.draw.rect(self.surf, c, (x + 1, y + 1, TILE - 2, TILE - 2))
            if i == 0:
                pygame.draw.rect(self.surf, Pal.GREEN_LIGHT, (x + 3, y + 3, TILE - 6, TILE - 6))

        ax, ay = self.apple
        pygame.draw.rect(self.surf, Pal.APPLE, (ax * TILE + 2, ay * TILE + 2, TILE - 4, TILE - 4))
        pygame.draw.rect(self.surf, Pal.RED, (ax * TILE + 4, ay * TILE + 4, TILE - 8, TILE - 8), 1)

        # HUD
        txt = self.font.render(f"SCORE {self.score}", True, Pal.TEXT)
        self.surf.blit(txt, (8, 4))
        if not self.started:
            msg = self.big_font.render("ULTRA!SNAKE", True, Pal.YELLOW)
            r = msg.get_rect(center=(NES_W // 2, NES_H // 2 - 20))
            self.surf.blit(msg, r)
            msg2 = self.font.render("ARROWS TO START", True, Pal.LIGHT_GRAY)
            r2 = msg2.get_rect(center=(NES_W // 2, NES_H // 2 + 20))
            self.surf.blit(msg2, r2)
        if self.game_over:
            over = self.big_font.render("GAME OVER", True, Pal.RED)
            r = over.get_rect(center=(NES_W // 2, NES_H // 2 - 10))
            self.surf.blit(over, r)
            msg2 = self.font.render(f"SCORE: {self.score}  [R]ESTART", True, Pal.TEXT)
            r2 = msg2.get_rect(center=(NES_W // 2, NES_H // 2 + 25))
            self.surf.blit(msg2, r2)

        pygame.transform.scale(self.surf, (W, H), self.screen)
        pygame.display.flip()

# === MENU DRAWING (OG Snake style: green on black, terminal/arcade) ===
def draw_menu_screen(surf, screen, font, big_font, menu_index, state):
    # Black/green CRT look
    surf.fill(Pal.CRT_BG)
    # Simple frame (OG arcade double-line feel)
    pygame.draw.rect(surf, Pal.CRT_BORDER, (8, 8, NES_W - 16, NES_H - 16), 2)
    pygame.draw.rect(surf, Pal.CRT_BORDER, (14, 14, NES_W - 28, NES_H - 28), 1)
    # Title block - chunky green like old Snake titles
    title = big_font.render("* S N A K E *", True, Pal.CRT_GREEN)
    surf.blit(title, title.get_rect(center=(NES_W // 2, 32)))
    sub = font.render("ULTRA!SNAKE BY MR.AC", True, Pal.CRT_DIM)
    surf.blit(sub, sub.get_rect(center=(NES_W // 2, 56)))
    # Score line (OG style "HIGH SCORE" placeholder)
    hi = font.render("HIGH SCORE  00000", True, Pal.CRT_DIM)
    surf.blit(hi, (NES_W // 2 - hi.get_width() // 2, 78))
    # Menu options - asterisk or number for selection (old-school)
    y = 108
    for i, label in enumerate(MENU_ITEMS):
        if i == 4:
            label_show = "GAME SOUND ...... " + ("ON" if SOUND_ENABLED else "OFF")
        else:
            label_show = label
        if i == menu_index:
            c = Pal.CRT_GREEN
            prefix = "> "
        else:
            c = Pal.CRT_DIM
            prefix = "  "
        txt = font.render(prefix + label_show, True, c)
        surf.blit(txt, (NES_W // 2 - txt.get_width() // 2, y + i * 18))
    # Bottom line: PRESS ENTER (OG "insert coin" style)
    press = font.render("PRESS ENTER TO START", True, Pal.CRT_DIM)
    surf.blit(press, press.get_rect(center=(NES_W // 2, NES_H - 28)))
    pygame.transform.scale(surf, (W, H), screen)
    pygame.display.flip()

def draw_text_screen(surf, screen, font, big_font, lines, title_str):
    surf.fill(Pal.BG)
    pygame.draw.rect(surf, Pal.BORDER, (0, 0, NES_W, NES_H), 4)
    t = big_font.render(title_str, True, Pal.YELLOW)
    surf.blit(t, t.get_rect(center=(NES_W // 2, 32)))
    y = 64
    for line in lines:
        txt = font.render(line, True, Pal.TEXT)
        surf.blit(txt, (max(0, NES_W // 2 - txt.get_width() // 2), y))
        y += 20
    back = font.render("Press ESC or B to go back", True, Pal.LIGHT_GRAY)
    surf.blit(back, back.get_rect(center=(NES_W // 2, NES_H - 28)))
    pygame.transform.scale(surf, (W, H), screen)
    pygame.display.flip()

def draw_settings_screen(surf, screen, font, big_font):
    surf.fill(Pal.BG)
    pygame.draw.rect(surf, Pal.BORDER, (0, 0, NES_W, NES_H), 4)
    t = big_font.render("SETTINGS", True, Pal.YELLOW)
    surf.blit(t, t.get_rect(center=(NES_W // 2, 40)))
    snd = "ON" if SOUND_ENABLED else "OFF"
    txt = font.render("Game Sound: " + snd + "  (press S to toggle)", True, Pal.TEXT)
    surf.blit(txt, txt.get_rect(center=(NES_W // 2, NES_H // 2 - 10)))
    back = font.render("Press ESC or B to go back", True, Pal.LIGHT_GRAY)
    surf.blit(back, back.get_rect(center=(NES_W // 2, NES_H - 24)))
    pygame.transform.scale(surf, (W, H), screen)
    pygame.display.flip()

def draw_exit_prompt(surf, screen, font, big_font):
    surf.fill(Pal.BG)
    pygame.draw.rect(surf, Pal.BORDER, (0, 0, NES_W, NES_H), 4)
    t = big_font.render("EXIT GAME?", True, Pal.RED)
    surf.blit(t, t.get_rect(center=(NES_W // 2, NES_H // 2 - 30)))
    txt = font.render("(Y)es  /  (N)o", True, Pal.TEXT)
    surf.blit(txt, txt.get_rect(center=(NES_W // 2, NES_H // 2 + 10)))
    pygame.transform.scale(surf, (W, H), screen)
    pygame.display.flip()

# === MAIN ===
def main():
    global SOUND_ENABLED
    game = Game()
    screen = game.screen
    surf = game.surf
    font = game.font
    big_font = game.big_font
    clock = game.clock

    state = MENU_MAIN
    menu_index = 0
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                continue
            if e.type == pygame.KEYDOWN:
                if state == MENU_MAIN:
                    if e.key == pygame.K_UP:
                        menu_index = (menu_index - 1) % len(MENU_ITEMS)
                        play_sfx("menu_move")
                    elif e.key == pygame.K_DOWN:
                        menu_index = (menu_index + 1) % len(MENU_ITEMS)
                        play_sfx("menu_move")
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        play_sfx("menu_accept")
                        if menu_index == 0:
                            state = STATE_GAME
                            game.reset()
                            game.started = True  # Start playing immediately when you press Enter
                            play_sfx("start")
                        elif menu_index == 1:
                            state = MENU_HOWTO
                        elif menu_index == 2:
                            state = MENU_CREDITS
                        elif menu_index == 3:
                            state = MENU_ABOUT
                        elif menu_index == 4:
                            SOUND_ENABLED = not SOUND_ENABLED
                        elif menu_index == 5:
                            state = MENU_SETTINGS
                        elif menu_index == 6:
                            state = MENU_EXIT_PROMPT
                elif state == MENU_HOWTO or state == MENU_CREDITS or state == MENU_ABOUT:
                    if e.key in (pygame.K_ESCAPE, pygame.K_b):
                        state = MENU_MAIN
                elif state == MENU_SETTINGS:
                    if e.key == pygame.K_s:
                        SOUND_ENABLED = not SOUND_ENABLED
                    elif e.key in (pygame.K_ESCAPE, pygame.K_b):
                        state = MENU_MAIN
                elif state == MENU_EXIT_PROMPT:
                    if e.key == pygame.K_y:
                        running = False
                    elif e.key == pygame.K_n:
                        state = MENU_MAIN
                elif state == STATE_GAME:
                    if e.key == pygame.K_ESCAPE:
                        state = MENU_MAIN
                    elif e.key == pygame.K_r and game.game_over:
                        game.reset()

        if not running:
            break

        keys = pygame.key.get_pressed()

        if state == MENU_MAIN:
            draw_menu_screen(surf, screen, font, big_font, menu_index, state)
        elif state == MENU_HOWTO:
            draw_text_screen(surf, screen, font, big_font, HOWTO_TEXT, "HOW TO PLAY")
        elif state == MENU_CREDITS:
            draw_text_screen(surf, screen, font, big_font, CREDITS_TEXT, "CREDITS")
        elif state == MENU_ABOUT:
            draw_text_screen(surf, screen, font, big_font, ABOUT_TEXT, "ABOUT")
        elif state == MENU_SETTINGS:
            draw_settings_screen(surf, screen, font, big_font)
        elif state == MENU_EXIT_PROMPT:
            draw_exit_prompt(surf, screen, font, big_font)
        else:
            game.handle_input(keys)
            game.update(keys)
            game.draw()

        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
