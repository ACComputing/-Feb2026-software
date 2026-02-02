import pygame
import random
import array
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 600, 400
FPS = 60

# Famicom/NES Inspired Palette
CLR_BG = (0, 0, 0)                  # Pure Black
CLR_PLAYER = (0, 255, 128)          # Neon Mint
CLR_ALIEN_H = (255, 80, 150)       # Bright Pink
CLR_ALIEN_M = (80, 180, 255)       # Sky Blue
CLR_ALIEN_L = (255, 220, 80)       # Sun Yellow (Fixed double underscore)
CLR_ENEMY_BULLET = (255, 255, 255) # White
CLR_UI_TEXT = (255, 255, 255)      # White
CLR_UI_ACCENT = (200, 200, 255)    # Light blue accent

# --- GBA SFX SYNTHESIZER ---
class GbaSfx:
    def __init__(self):
        # pre_init moved to Game.__init__ for better compatibility
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.enabled = True
        except:
            print("Audio initialization failed. Running without sound.")
            self.enabled = False

    def _play_buf(self, buf):
        if not self.enabled: 
            return
        try:
            # Convert to stereo for better compatibility
            stereo_buf = array.array('h')
            for i in range(0, len(buf), 1):
                # Duplicate mono to stereo channels
                stereo_buf.append(buf[i])
                stereo_buf.append(buf[i])
            
            sound = pygame.mixer.Sound(buffer=bytes(stereo_buf))
            sound.set_volume(0.3)
            sound.play()
        except Exception:
            pass

    def play_shoot(self):
        buf = array.array('h')
        duration = 0.05 
        samples = int(44100 * duration)
        
        for i in range(samples):
            freq = 1000 - (i / samples * 600)
            period = 44100 / max(100, freq)
            val = 3000 if (i // (period / 2)) % 2 else -3000
            env = 1.0 - (i / samples)
            buf.append(int(val * env))
        self._play_buf(buf)

    def play_explode(self):
        buf = array.array('h')
        duration = 0.2 
        samples = int(44100 * duration)
        
        for i in range(samples):
            env = 1.0 - (i / samples) ** 2
            noise = random.randint(-8000, 8000)
            rumble_freq = 80
            rumble_period = 44100 / rumble_freq
            rumble = 4000 * math.sin(2 * math.pi * i / rumble_period)
            val = int((noise * 0.7 + rumble * 0.3) * env)
            buf.append(val)
        self._play_buf(buf)

    def play_select(self):
        buf = array.array('h')
        duration = 0.08 
        samples = int(44100 * duration)
        
        for i in range(samples):
            freq = 300 + (i / samples * 300)
            period = 44100 / max(100, freq)
            val = 4000 if (i // (period / 2)) % 2 else -4000
            
            if i < samples * 0.1:
                env = i / (samples * 0.1)
            else:
                env = 1.0 - ((i - samples * 0.1) / (samples * 0.9))
                
            buf.append(int(val * env))
        self._play_buf(buf)

# --- SPRITES ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 24), pygame.SRCALPHA)
        pygame.draw.rect(self.image, CLR_PLAYER, (12, 0, 8, 8))
        pygame.draw.rect(self.image, CLR_PLAYER, (4, 8, 24, 8))
        pygame.draw.rect(self.image, (255, 255, 255), (8, 10, 16, 4))
        pygame.draw.rect(self.image, CLR_PLAYER, (0, 16, 32, 8))
        self.rect = self.image.get_rect(midbottom=(WIDTH//2, HEIGHT-20))
        self.speed = 5
        self.shoot_cooldown = 0

    def update(self, *args, **kwargs):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, row):
        super().__init__()
        self.row = row
        self.points = (3 - (row // 2)) * 10
        self.color = CLR_ALIEN_H if row < 2 else CLR_ALIEN_M if row < 4 else CLR_ALIEN_L
        self.frames = self._create_frames()
        self.frame_idx = 0
        self.image = self.frames[self.frame_idx]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.animation_timer = 0

    def _create_frames(self):
        frames = []
        for frame in range(2):
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.rect(surf, self.color, (4, 4, 16, 12))
            pygame.draw.rect(surf, (0, 0, 0), (6, 8, 4, 4))
            pygame.draw.rect(surf, (0, 0, 0), (14, 8, 4, 4))
            leg_y = 16 if frame == 0 else 18
            pygame.draw.rect(surf, self.color, (4, leg_y, 4, 4))
            pygame.draw.rect(surf, self.color, (16, leg_y, 4, 4))
            frames.append(surf)
        return frames

    def update(self, *args, **kwargs):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_timer = 0
            self.frame_idx = (self.frame_idx + 1) % 2
            self.image = self.frames[self.frame_idx]

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, color):
        super().__init__()
        self.image = pygame.Surface((3, 8))
        self.image.fill(color)
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.speed = speed

    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

# --- ENGINE ---
class Game:
    def __init__(self):
        # Best practice: pre_init before init
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cat's! Space invaders")
        self.clock = pygame.time.Clock()
        self.sfx = GbaSfx()

        try:
            self.font_main = pygame.font.SysFont("monospace", 18, bold=True)
            self.font_title = pygame.font.SysFont("monospace", 36, bold=True)
        except:
            self.font_main = pygame.font.Font(None, 24)
            self.font_title = pygame.font.Font(None, 48)

        self.bg = pygame.Surface((WIDTH, HEIGHT))
        self.bg.fill(CLR_BG)
        for _ in range(100):
            x = random.randint(0, WIDTH - 1)
            y = random.randint(0, HEIGHT - 1)
            size = random.randint(1, 2)
            bright = random.choice([96, 128, 160, 192])
            pygame.draw.circle(self.bg, (bright, bright, bright), (x, y), size)

        self.state = "MENU"
        self.menu_idx = 0
        self.menu_options = ["PLAY GAME", "HOW TO PLAY", "CREDITS", "ABOUT", "EXIT GAME"]
        self.score = 0
        self.lives = 3
        self.running = True
        self.reset_level()

    def reset_level(self):
        self.all_sprites = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        for row in range(5):
            for col in range(10):
                a = Alien(40 + col * 52, 50 + row * 40, row)
                self.aliens.add(a)
                self.all_sprites.add(a)

        self.alien_dir = 1
        self.alien_move_timer = 0
        self.alien_move_delay = 30 
        self.alien_fire_chance = 0.01

    def draw_text(self, text, font, color, x, y, center=True):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def update(self):
        if self.state == "PLAY":
            self.all_sprites.update()

            if self.aliens:
                num_aliens = len(self.aliens)
                self.alien_move_delay = max(6, int(30 - num_aliens * 0.4))
                
                self.alien_move_timer += 1
                if self.alien_move_timer >= self.alien_move_delay:
                    self.alien_move_timer = 0
                    
                    change_dir = False
                    for alien in self.aliens:
                        if (self.alien_dir == 1 and alien.rect.right >= WIDTH - 10) or \
                           (self.alien_dir == -1 and alien.rect.left <= 10):
                            change_dir = True
                            break
                    
                    if change_dir:
                        self.alien_dir *= -1
                        for alien in self.aliens:
                            alien.rect.y += 20
                            if alien.rect.bottom >= self.player.rect.top:
                                self.state = "GAMEOVER"
                                self.player_bullets.empty()
                                self.enemy_bullets.empty()
                                self.sfx.play_explode()
                                break
                    else:
                        step = 8 
                        for alien in self.aliens:
                            alien.rect.x += self.alien_dir * step

            # Fix: Alien shooting (only bottom-most aliens fire)
            if self.aliens and random.random() < self.alien_fire_chance:
                columns = {}
                for alien in self.aliens:
                    col_key = alien.rect.centerx // 50
                    if col_key not in columns or alien.rect.y > columns[col_key].rect.y:
                        columns[col_key] = alien
                
                shooter = random.choice(list(columns.values()))
                bullet = Bullet(shooter.rect.centerx, shooter.rect.bottom, 3, CLR_ENEMY_BULLET)
                self.enemy_bullets.add(bullet)
                self.all_sprites.add(bullet)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] and self.player.shoot_cooldown == 0 and len(self.player_bullets) < 3:
                bullet = Bullet(self.player.rect.centerx, self.player.rect.top, -8, CLR_PLAYER)
                self.player_bullets.add(bullet)
                self.all_sprites.add(bullet)
                self.player.shoot_cooldown = 15
                self.sfx.play_shoot()

            hits = pygame.sprite.groupcollide(self.player_bullets, self.aliens, True, True)
            for hit_list in hits.values():
                for alien in hit_list:
                    self.score += alien.points
                    self.sfx.play_explode()

            if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
                self.sfx.play_explode()
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "GAMEOVER"
                    self.player_bullets.empty()
                    self.enemy_bullets.empty()
                else:
                    self.player.rect.midbottom = (WIDTH//2, HEIGHT-20)
                    self.player_bullets.empty()
                    self.enemy_bullets.empty()

            if not self.aliens:
                self.score += 100
                self.reset_level()
                # Fix: Cap alien fire chance
                self.alien_fire_chance = min(self.alien_fire_chance + 0.002, 0.05)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == "MENU":
                    if event.key == pygame.K_UP:
                        self.menu_idx = (self.menu_idx - 1) % len(self.menu_options)
                        self.sfx.play_select()
                    elif event.key == pygame.K_DOWN:
                        self.menu_idx = (self.menu_idx + 1) % len(self.menu_options)
                        self.sfx.play_select()
                    elif event.key == pygame.K_RETURN:
                        option = self.menu_options[self.menu_idx]
                        self.sfx.play_select()
                        if option == "PLAY GAME":
                            self.score = 0
                            self.lives = 3
                            self.reset_level()
                            self.state = "PLAY"
                            self.player.shoot_cooldown = 15
                        elif option == "EXIT GAME":
                            self.running = False
                        else:
                            self.state = option.replace(" ", "_")
                elif self.state == "PLAY":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                elif self.state in ["HOW_TO_PLAY", "CREDITS", "ABOUT", "GAMEOVER"]:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.state = "MENU"

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        if self.state == "MENU":
            self.draw_text("Cat's! Space invaders", self.font_title, CLR_ALIEN_H, WIDTH//2, 80)
            for i, option in enumerate(self.menu_options):
                color = CLR_PLAYER if i == self.menu_idx else CLR_UI_TEXT
                prefix = "> " if i == self.menu_idx else "  "
                self.draw_text(f"{prefix}{option}", self.font_main, color, WIDTH//2, 180 + i * 40)
            self.draw_text("Use UP/DOWN to navigate, ENTER to select", self.font_main, CLR_UI_ACCENT, WIDTH//2, HEIGHT - 40)

        elif self.state == "PLAY":
            self.all_sprites.draw(self.screen)
            self.draw_text(f"SCORE: {self.score:06d}", self.font_main, CLR_UI_TEXT, 80, 20, center=False)
            self.draw_text(f"LIVES: {self.lives}", self.font_main, CLR_UI_TEXT, WIDTH - 80, 20, center=False)
            for i in range(self.lives):
                x = WIDTH - 100 + i * 15
                pygame.draw.rect(self.screen, CLR_PLAYER, (x, 40, 10, 8))

        elif self.state == "HOW_TO_PLAY":
            self.draw_text("HOW TO PLAY", self.font_title, CLR_ALIEN_M, WIDTH//2, 60)
            instructions = ["LEFT/RIGHT ARROWS - Move ship", "SPACEBAR - Fire laser", "Destroy all alien invaders!", "", "Aliens move faster as there", "are fewer of them.", "", "Avoid enemy fire and prevent", "aliens from reaching the bottom."]
            for i, line in enumerate(instructions):
                self.draw_text(line, self.font_main, CLR_UI_TEXT, WIDTH//2, 120 + i * 25)
            self.draw_text("PRESS ENTER TO RETURN", self.font_main, CLR_UI_ACCENT, WIDTH//2, HEIGHT - 40)

        elif self.state == "CREDITS":
            self.draw_text("CREDITS", self.font_title, CLR_ALIEN_M, WIDTH//2, 60)
            credits = ["Game Design & Programming:", "AC Computing Gaming Division", "", "Sound Design:", "GBA Style SFX Synthesizer", "", "Special Thanks:", "Space Invaders (1978)", "Famicom/NES Developers", "", "[C] 1999-2026"]
            for i, line in enumerate(credits):
                self.draw_text(line, self.font_main, CLR_UI_TEXT, WIDTH//2, 120 + i * 25)
            self.draw_text("PRESS ENTER TO RETURN", self.font_main, CLR_UI_ACCENT, WIDTH//2, HEIGHT - 40)

        elif self.state == "ABOUT":
            self.draw_text("ABOUT", self.font_title, CLR_ALIEN_L, WIDTH//2, 60)
            about_text = ["Cat's! Space invaders", "", "A retro-style space shooter", "inspired by classic arcade", "games from the Famicom/NES era.", "", "Features authentic 8-bit style", "graphics and GBA-inspired", "sound effects.", "", "Created with PyGame"]
            for i, line in enumerate(about_text):
                self.draw_text(line, self.font_main, CLR_UI_TEXT, WIDTH//2, 120 + i * 25)
            self.draw_text("PRESS ENTER TO RETURN", self.font_main, CLR_UI_ACCENT, WIDTH//2, HEIGHT - 40)

        elif self.state == "GAMEOVER":
            self.draw_text("GAME OVER", self.font_title, (255, 50, 50), WIDTH//2, HEIGHT//2 - 40)
            self.draw_text(f"FINAL SCORE: {self.score}", self.font_main, CLR_UI_TEXT, WIDTH//2, HEIGHT//2)
            self.draw_text("PRESS ENTER TO RETURN TO MENU", self.font_main, CLR_UI_ACCENT, WIDTH//2, HEIGHT//2 + 60)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
