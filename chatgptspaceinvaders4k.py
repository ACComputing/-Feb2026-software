# ============================================================
# CAT'S SPACE INVADERS 0.1 — Famicom Beeps n Boops Edition
# Single File • No Assets • 60 FPS
# ============================================================

import pygame
import sys
import math
import random
import array

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 600, 400
FPS = 60

BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
GREEN  = (120, 255, 120)
RED    = (255, 80, 80)
YELLOW = (255, 255, 120)

# ---------------- INIT ----------------
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cat's Space Invaders 0.1")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier", 16)

# ---------------- CHIP SOUND ----------------
def beep(freq=800, dur=0.08, vol=0.5):
    sr = 22050
    samples = int(sr * dur)
    buf = array.array("h")

    for i in range(samples):
        t = i / sr
        val = int(vol * 32767 * math.sin(2 * math.pi * freq * t))
        buf.append(val)

    snd = pygame.mixer.Sound(buffer=buf)
    snd.play()

# ---------------- TEXT DRAW ----------------
def draw_text(text, x, y, color=WHITE, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

# ---------------- PLAYER ----------------
class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - 15, HEIGHT - 30, 30, 10)
        self.speed = 4

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)

# ---------------- BULLET ----------------
class Bullet:
    def __init__(self, x, y, dy, color):
        self.rect = pygame.Rect(x, y, 4, 8)
        self.dy = dy
        self.color = color

    def update(self):
        self.rect.y += self.dy

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)

# ---------------- ENEMY ----------------
class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 12)

    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)

# ---------------- GAME ----------------
def play_game():
    player = Player()
    bullets = []
    enemies = []
    score = 0

    for row in range(4):
        for col in range(8):
            enemies.append(Enemy(60 + col * 50, 50 + row * 30))

    enemy_dir = 1
    enemy_timer = 0

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_SPACE:
                    bullets.append(Bullet(player.rect.centerx - 2, player.rect.top, -6, WHITE))
                    beep(1200)

        keys = pygame.key.get_pressed()
        player.update(keys)

        # Enemies movement
        enemy_timer += 1
        if enemy_timer > 30:
            enemy_timer = 0
            move_down = False
            for e in enemies:
                e.rect.x += enemy_dir * 10
                if e.rect.right > WIDTH - 10 or e.rect.left < 10:
                    move_down = True
            if move_down:
                enemy_dir *= -1
                for e in enemies:
                    e.rect.y += 10
                beep(300)

        # Update bullets
        for b in bullets[:]:
            b.update()
            if b.rect.bottom < 0:
                bullets.remove(b)

        # Collision
        for b in bullets[:]:
            for e in enemies[:]:
                if b.rect.colliderect(e.rect):
                    bullets.remove(b)
                    enemies.remove(e)
                    score += 10
                    beep(600)
                    break

        # Draw
        player.draw()
        for b in bullets:
            b.draw()
        for e in enemies:
            e.draw()

        draw_text(f"SCORE: {score}", 10, 10, YELLOW)

        if not enemies:
            draw_text("YOU WIN!", WIDTH//2, HEIGHT//2, GREEN, center=True)
            pygame.display.flip()
            pygame.time.delay(1500)
            return

        pygame.display.flip()

# ---------------- INFO SCREENS ----------------
def info_screen(title, lines):
    while True:
        clock.tick(FPS)
        screen.fill(BLACK)

        draw_text(title, WIDTH//2, 60, YELLOW, center=True)
        for i, line in enumerate(lines):
            draw_text(line, WIDTH//2, 120 + i * 24, WHITE, center=True)

        draw_text("Press ESC to return", WIDTH//2, HEIGHT - 40, GREEN, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        pygame.display.flip()

# ---------------- MAIN MENU ----------------
def main_menu():
    options = ["Play Game", "How to Play", "About", "Credits", "Exit"]
    index = 0

    while True:
        clock.tick(FPS)
        screen.fill(BLACK)

        draw_text("CAT'S SPACE INVADERS 0.1", WIDTH//2, 80, YELLOW, center=True)

        for i, opt in enumerate(options):
            color = GREEN if i == index else WHITE
            draw_text(opt, WIDTH//2, 150 + i * 30, color, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    index = (index - 1) % len(options)
                    beep(400)
                if event.key == pygame.K_DOWN:
                    index = (index + 1) % len(options)
                    beep(400)
                if event.key == pygame.K_RETURN:
                    beep(900)
                    if options[index] == "Play Game":
                        play_game()
                    elif options[index] == "How to Play":
                        info_screen("HOW TO PLAY", [
                            "LEFT / RIGHT - Move",
                            "SPACE - Shoot",
                            "ESC - Back / Quit"
                        ])
                    elif options[index] == "About":
                        info_screen("ABOUT", [
                            "A tiny retro Space Invaders clone",
                            "Written in pure Python + pygame",
                            "Famicom vibes only 😼"
                        ])
                    elif options[index] == "Credits":
                        info_screen("CREDITS", [
                            "Code: Cat-san",
                            "Engine: pygame",
                            "Beep Tech: math.sin()"
                        ])
                    elif options[index] == "Exit":
                        pygame.quit()
                        sys.exit()

        pygame.display.flip()

# ---------------- RUN ----------------
main_menu()
