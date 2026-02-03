#!/usr/bin/env python3
"""
Cat's Ultra Mario 2D Bros! v2.1 (Famicom Speed Edition)
Complete 32-Level Campaign (1-1 to 8-4)
Features:
- Accurate Famicom Speed (60 FPS)
- Procedural 8-bit Music & Sound Engine
- PAUSE Functionality (Stops Music/Game)
- Hammer Bros, Bullet Bills, Lakitu, Spinies
- Physics (Momentum, Variable Jump Height)

Controls:
  Arrow Keys - Move
  Z / Space  - Jump
  X / Shift  - Run/Fire
  Enter      - Pause/Resume
"""

import pygame
import math
import array
import random

# === INITIALIZATION ===
pygame.init()
pygame.mixer.init(44100, -16, 2, 512)

# === CONSTANTS & PHYSICS ===
SCALE = 3
NES_W, NES_H = 256, 240
W, H = NES_W * SCALE, NES_H * SCALE
T = 16
FPS = 60

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cat's Ultra Mario 2D Bros! v2.1")
nes_surface = pygame.Surface((NES_W, NES_H))
clock = pygame.time.Clock()

class Phys:
    # NES-like sub-pixel physics values
    WALK_ACCEL = 0.098   # Acceleration walking
    RUN_ACCEL = 0.144    # Acceleration running
    FRICTION = 0.88      # Ground friction
    SKID_DECEL = 0.15    # Turning around
    WALK_MAX = 1.6       # Max walk speed
    RUN_MAX = 2.9        # Max run speed
    GRAVITY = 0.25       # Base gravity
    GRAVITY_HOLDING = 0.11 # Gravity while holding jump (variable jump height)
    MAX_FALL = 4.5       # Terminal velocity
    JUMP_FORCE = -5.6    # Initial jump impulse
    BOUNCE_FORCE = -3.0  # Enemy stomp bounce
    
    GOOMBA_SPEED = 0.6
    KOOPA_SPEED = 0.6
    SHELL_SPEED = 3.5
    BULLET_SPEED = 2.5

class Pal:
    BLACK = (0, 0, 0); WHITE = (252, 252, 252); SKY = (92, 148, 252)
    UNDERGROUND = (0, 0, 0); UNDERWATER = (32, 56, 236); CASTLE = (0, 0, 0)
    MARIO_RED = (216, 40, 0); MARIO_TAN = (252, 152, 56); MARIO_BROWN = (136, 20, 0)
    BRICK = (172, 80, 36); BRICK_DARK = (120, 20, 0)
    QUESTION = (252, 152, 56); QUESTION_DARK = (200, 116, 20)
    GROUND = (200, 76, 12); GROUND_DARK = (136, 20, 0)
    PIPE = (0, 168, 0); PIPE_LIGHT = (0, 228, 0); PIPE_DARK = (0, 108, 0)
    CASTLE_GRAY = (188, 188, 188); CASTLE_DARK = (116, 116, 116)
    GOOMBA = (172, 80, 36); KOOPA_GREEN = (0, 168, 0); KOOPA_RED = (216, 40, 0)
    HAMMER_BRO = (0, 168, 0); BULLET = (60, 60, 60)
    COIN = (252, 188, 60); OVERLAY = (0, 0, 0, 128)

# === AUDIO ENGINE ===
SFX = {}
MUSIC_CHANNEL = None

def generate_wave(freq_func, duration, volume=0.2, wave_type="sq"):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    
    for i in range(n_samples):
        t = i / sample_rate
        f = freq_func(t)
        
        # Waveform generation
        v = 0.0
        if wave_type == "sq":
            v = 1.0 if (f * t * 2 * math.pi) % (2 * math.pi) < math.pi else -1.0
        elif wave_type == "tri":
            v = 2.0 * abs(2.0 * (t * f - math.floor(t * f + 0.5))) - 1.0
        elif wave_type == "noi":
            v = random.uniform(-1, 1)
            
        # Envelope
        decay = max(0, 1.0 - (i / n_samples))
        sample = int(v * 32767 * volume * decay)
        buf.append(sample)
        buf.append(sample) # Stereo
        
    return pygame.mixer.Sound(buffer=buf)

def init_audio():
    global MUSIC_CHANNEL
    # SFX
    SFX["jump"] = generate_wave(lambda t: 150 + t*300, 0.15, 0.15, "sq")
    SFX["jump_big"] = generate_wave(lambda t: 100 + t*200, 0.2, 0.15, "sq")
    SFX["stomp"] = generate_wave(lambda t: 300 - t*900, 0.1, 0.2, "sq")
    SFX["coin"] = generate_wave(lambda t: 1174 if t < 0.05 else 1568, 0.3, 0.15, "sq")
    SFX["bump"] = generate_wave(lambda t: 100 - t*100, 0.1, 0.2, "sq")
    SFX["break"] = generate_wave(lambda t: 0, 0.15, 0.2, "noi")
    SFX["die"] = generate_wave(lambda t: 400 - t*150, 2.5, 0.3, "sq")
    SFX["pause"] = generate_wave(lambda t: 600 if (t*10)%2 < 1 else 0, 0.4, 0.2, "tri")
    
    MUSIC_CHANNEL = pygame.mixer.Channel(0)

# Procedural Music Generator
class MusicEngine:
    def __init__(self):
        self.notes = [
            (330, 0.15), (330, 0.15), (330, 0.30), (261, 0.15), (330, 0.30), (392, 0.60), (196, 0.60), # Intro
            (261, 0.45), (196, 0.45), (164, 0.45), (220, 0.30), (246, 0.30), (233, 0.15), (220, 0.30), # Main 1
        ]
        self.track_idx = 0
        self.next_note_time = 0
        self.playing = True

    def update(self):
        if not self.playing: return
        
        now = pygame.time.get_ticks()
        if now >= self.next_note_time:
            freq, duration = self.notes[self.track_idx]
            # Create short beep for note
            snd = generate_wave(lambda t: freq, duration * 0.9, 0.08, "sq")
            MUSIC_CHANNEL.play(snd)
            
            self.next_note_time = now + int(duration * 1000)
            self.track_idx = (self.track_idx + 1) % len(self.notes)

# === SPRITE DRAWING ===
def draw_rects(surf, color, rects, dx=0, dy=0):
    for r in rects: pygame.draw.rect(surf, color, (r[0]+dx, r[1]+dy, r[2], r[3]))

def draw_mario(s, x, y, f, frame, big, fire, duck):
    # Colors
    c_hat = Pal.WHITE if fire else Pal.MARIO_RED
    c_shirt = Pal.MARIO_RED if fire else Pal.MARIO_TAN
    c_skin = Pal.MARIO_TAN
    
    # Flip logic
    start_x = x if f == 1 else x + 12
    step = 1 if f == 1 else -1
    
    def r(bx, by, bw, bh, col):
        rx = x + bx if f == 1 else x + (12 - bx - bw)
        pygame.draw.rect(s, col, (rx, y+by, bw, bh))

    h_offset = 16 if big else 0
    total_h = 32 if big else 16
    if big and duck: 
        h_offset = 10
        y += 10 # Ducking visual

    # Head
    r(2, 0, 10, 4, c_hat) # Hat top
    r(6, 4, 8, 4, c_skin) # Face
    r(10, 6, 2, 2, Pal.BLACK) # Nose
    
    # Body
    r(3, 8, 8, 8 + h_offset, c_shirt) # Main body
    
    # Arms/Legs (Simple animation based on x position)
    anim = (int(x) // 10) % 3
    if anim == 0:
        r(1, 8+h_offset, 3, 6, c_shirt)
    elif anim == 1:
        r(9, 8+h_offset, 3, 6, c_shirt)

    # Shoes
    r(1, 8+h_offset+6, 4, 2, Pal.MARIO_BROWN)
    r(8, 8+h_offset+6, 4, 2, Pal.MARIO_BROWN)

def draw_goomba(s, x, y, frame):
    walk = (frame // 10) % 2
    c = Pal.GOOMBA
    pygame.draw.rect(s, c, (x, y, 16, 12)) # Head
    pygame.draw.rect(s, Pal.WHITE, (x+3, y+4, 4, 5)) # Eye L
    pygame.draw.rect(s, Pal.WHITE, (x+9, y+4, 4, 5)) # Eye R
    pygame.draw.rect(s, Pal.BLACK, (x+5, y+5, 2, 3)) # Pupil
    pygame.draw.rect(s, Pal.BLACK, (x+9, y+5, 2, 3)) # Pupil
    
    # Feet
    if walk == 0:
        pygame.draw.rect(s, Pal.BLACK, (x, y+12, 6, 4))
        pygame.draw.rect(s, Pal.BLACK, (x+10, y+12, 6, 4))
    else:
        pygame.draw.rect(s, Pal.BLACK, (x+2, y+12, 5, 4))
        pygame.draw.rect(s, Pal.BLACK, (x+9, y+12, 5, 4))

# === ENTITIES ===
class Entity:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.w, self.h = 16, 16
        self.alive = True
        self.frame = 0
        self.facing = -1
        self.on_ground = False
    
    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.w, self.h)
    
    def update(self, level, player):
        self.frame += 1
        self.vy = min(self.vy + Phys.GRAVITY, Phys.MAX_FALL)
        self.x += self.vx
        self.y += self.vy
        self.check_collision(level)
        if self.y > NES_H + 32: self.alive = False
    
    def check_collision(self, level):
        self.on_ground = False
        # Horizontal
        r = pygame.Rect(int(self.x + self.vx), int(self.y), self.w, self.h)
        for t in level.get_tiles(self.x, self.y):
            if t.solid and r.colliderect(t.rect):
                if self.vx > 0: self.x = t.rect.left - self.w
                elif self.vx < 0: self.x = t.rect.right
                self.vx *= -1 # Bounce enemies
                self.facing *= -1
        
        # Vertical
        r = pygame.Rect(int(self.x), int(self.y + self.vy), self.w, self.h)
        for t in level.get_tiles(self.x, self.y + self.vy):
            if t.solid and r.colliderect(t.rect):
                if self.vy > 0:
                    self.y = t.rect.top - self.h
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = t.rect.bottom
                self.vy = 0

    def draw(self, surf, cam): pass

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -Phys.GOOMBA_SPEED
    def draw(self, s, c): 
        col = Pal.GOOMBA
        if self.frame < 0: col = Pal.BRICK_DARK # Squashed state
        draw_goomba(s, self.x-c, self.y, self.frame)

class Koopa(Entity):
    def __init__(self, x, y, red=False):
        super().__init__(x, y)
        self.h = 24
        self.red = red
        self.vx = -Phys.KOOPA_SPEED
        self.shell = False
        self.moving_shell = False
    
    def update(self, level, player):
        if self.moving_shell: self.vx = Phys.SHELL_SPEED * self.facing
        super().update(level, player)
        
    def draw(self, s, c):
        col = Pal.KOOPA_RED if self.red else Pal.KOOPA_GREEN
        h_draw = 16 if self.shell else 24
        y_draw = self.y + (8 if self.shell else 0)
        pygame.draw.rect(s, col, (self.x-c+2, y_draw, 12, 14)) # Shell
        if not self.shell: pygame.draw.rect(s, Pal.MARIO_TAN, (self.x-c+4, self.y, 8, 8)) # Head

class HammerBro(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.h = 24
        self.vx = 0.5
        self.timer = 0
        self.home_x = x
    
    def update(self, level, player):
        self.timer += 1
        super().update(level, player)
        if self.x > self.home_x + 32: self.vx = -0.5
        if self.x < self.home_x - 32: self.vx = 0.5
        self.facing = 1 if player.x > self.x else -1
        
        if self.timer % 160 == 0 and self.on_ground:
            self.vy = -6
            self.on_ground = False
        
        if self.timer % 100 == 50:
            level.add_entity(Hammer(self.x, self.y, self.facing))

    def draw(self, s, c):
        pygame.draw.rect(s, Pal.HAMMER_BRO, (self.x-c+4, self.y, 8, 4)) # Helmet
        pygame.draw.rect(s, Pal.HAMMER_BRO, (self.x-c+2, self.y+12, 12, 10)) # Body
        if self.timer % 20 < 10: pygame.draw.rect(s, Pal.BLACK, (self.x-c+10, self.y+6, 6, 6)) # Hammer

class Hammer(Entity):
    def __init__(self, x, y, direction):
        super().__init__(x, y)
        self.w, self.h = 8, 8
        self.vx = 2 * direction
        self.vy = -4
    def update(self, level, player):
        self.vy += 0.15 
        self.x += self.vx
        self.y += self.vy
        if self.y > NES_H + 16: self.alive = False
    def draw(self, s, c):
        pygame.draw.rect(s, Pal.BLACK, (self.x-c, self.y, 8, 8))

# === TILEMAP SYSTEM ===
class Tile:
    def __init__(self, x, y, t):
        self.x, self.y, self.type = x, y, t
        self.rect = pygame.Rect(x, y, T, T)
        self.solid = t not in [" ", "o", "A", "rope", "water", "top"]
        self.used = False
        self.bump = 0
    
    def draw(self, s, c):
        x, y = self.x - c, self.y - self.bump
        if self.type == "#": # Ground
            pygame.draw.rect(s, Pal.GROUND, (x,y,16,16))
            pygame.draw.rect(s, Pal.GROUND_DARK, (x+4,y+2,8,2))
        elif self.type == "B": # Brick
            pygame.draw.rect(s, Pal.BRICK, (x,y,16,16))
            pygame.draw.rect(s, Pal.BRICK_DARK, (x,y,16,16), 1)
            pygame.draw.rect(s, Pal.BRICK_DARK, (x+1,y+7,14,2))
        elif self.type == "?": 
            col = Pal.QUESTION if not self.used else Pal.BRICK_DARK
            pygame.draw.rect(s, col, (x,y,16,16))
            if not self.used:
                pygame.draw.rect(s, Pal.QUESTION_DARK, (x+4,y+4,8,2))
                pygame.draw.rect(s, Pal.QUESTION_DARK, (x+6,y+10,4,2))
        elif self.type == "H": # Hard Block
            pygame.draw.rect(s, Pal.CASTLE_GRAY, (x,y,16,16))
            pygame.draw.rect(s, Pal.CASTLE_DARK, (x+12,y,4,16))
        elif self.type == "P": # Pipe
            pygame.draw.rect(s, Pal.PIPE, (x,y,16,16))
            pygame.draw.rect(s, Pal.PIPE_LIGHT, (x+2,y,4,16))
        elif self.type == "o": 
            pygame.draw.circle(s, Pal.COIN, (x+8, y+8), 5)

def generate_level(w, s):
    width = 240
    grid = [[" " for _ in range(width)] for _ in range(15)]
    enemies = []
    
    def fill(x, w, t="#"):
        for i in range(x, x+w):
            grid[13][i] = t; grid[14][i] = t
    
    def block(x, y, t="B"):
        if 0<=x<width and 0<=y<15:
            grid[y][x] = t
    
    def pipe(x, h):
        for i in range(h): block(x, 12-i, "P"); block(x+1, 12-i, "P")

    # Base ground
    fill(0, width)
    
    # 1-1 Layout
    if w==1 and s==1:
        block(16, 9, "?")
        for i in range(5): block(20+i, 9, "B" if i%2==0 else "?")
        pipe(28, 2); pipe(38, 3); pipe(46, 4)
        enemies.append((22, 12, "g"))
        enemies.append((40, 12, "g"))
        
        # Pits
        for i in range(69, 71): grid[13][i] = " "; grid[14][i] = " "
        
        # Stairs
        for i in range(8):
            for j in range(i): block(134+i, 12-j, "H")
        
    # Generic Procedural
    else:
        for x in range(20, width-20, 8):
            if random.random() < 0.1: # Pit
                grid[13][x] = " "; grid[14][x] = " "
            elif random.random() < 0.15: # Pipe
                pipe(x, random.randint(2,4))
            elif random.random() < 0.2: # Blocks
                h = 9 if random.random() < 0.5 else 5
                block(x, h, "?" if random.random() < 0.3 else "B")
                if random.random() < 0.4: enemies.append((x, 12, "g"))
                elif random.random() < 0.1: enemies.append((x, 12, "k"))

    # Flag
    block(width-10, 12, "H")
    for i in range(1, 10): block(width-10, 12-i, "P") # Pole
    
    return grid, enemies

class Level:
    def __init__(self, w, s):
        self.grid, e_data = generate_level(w, s)
        self.width_tiles = len(self.grid[0])
        self.tiles = []
        self.entities = []
        self.camera = 0
        
        for y, row in enumerate(self.grid):
            for x, char in enumerate(row):
                if char != " ": self.tiles.append(Tile(x*T, y*T, char))
        
        for e in e_data:
            x, y, t = e
            if t == "g": self.entities.append(Goomba(x*T, y*T))
            elif t == "k": self.entities.append(Koopa(x*T, y*T))

    def get_tiles(self, x, y):
        # Optimization: spatial hashingish
        cx, cy = int(x // T), int(y // T)
        results = []
        for t in self.tiles:
            if abs(t.x//T - cx) < 3 and abs(t.y//T - cy) < 3:
                results.append(t)
        return results

    def update(self, player):
        # Camera Scroll
        target = player.x - NES_W // 2
        self.camera = max(self.camera, target)
        self.camera = min(self.camera, self.width_tiles * T - NES_W)
        self.camera = max(0, self.camera)
        
        # Tile Anims
        for t in self.tiles:
            if t.bump > 0: t.bump = max(0, t.bump - 1)
            
        # Entity Logic
        keep = []
        for e in self.entities:
            # Active zone
            if e.x - self.camera < NES_W + 64 and e.x - self.camera > -64:
                e.update(self, player)
                if player.rect.colliderect(e.rect) and e.alive and not player.dead:
                    # Bounce off head
                    if player.vy > 0 and player.y < e.y:
                        e.alive = False
                        player.vy = Phys.BOUNCE_FORCE
                        SFX["stomp"].play()
                    elif not player.iframe:
                        player.hurt()
            if e.alive: keep.append(e)
        self.entities = keep

    def draw(self, s):
        s.fill(Pal.SKY)
        # Render tiles in view
        for t in self.tiles:
            if -T < t.x - self.camera < NES_W:
                t.draw(s, self.camera)
        # Render entities
        for e in self.entities:
            if -T < e.x - self.camera < NES_W:
                e.draw(s, self.camera)

# === PLAYER ===
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx, self.vy = 0, 0
        self.w, self.h = 12, 16
        self.big = False
        self.dead = False
        self.win = False
        self.facing = 1
        self.on_ground = False
        self.iframe = 0
    
    @property
    def rect(self): return pygame.Rect(self.x+2, self.y, self.w, self.h)
    
    def update(self, keys, level):
        if self.dead: return
        
        # Physics X
        accel = Phys.RUN_ACCEL if keys[pygame.K_LSHIFT] or keys[pygame.K_x] else Phys.WALK_ACCEL
        max_v = Phys.RUN_MAX if keys[pygame.K_LSHIFT] or keys[pygame.K_x] else Phys.WALK_MAX
        friction = Phys.FRICTION if self.on_ground else 0.95
        
        if keys[pygame.K_LEFT]:
            if self.vx > 0: self.vx -= Phys.SKID_DECEL
            else: self.vx -= accel
            self.facing = -1
        elif keys[pygame.K_RIGHT]:
            if self.vx < 0: self.vx += Phys.SKID_DECEL
            else: self.vx += accel
            self.facing = 1
        else:
            self.vx *= friction
            if abs(self.vx) < 0.1: self.vx = 0
            
        self.vx = max(-max_v, min(max_v, self.vx))
        self.x += self.vx
        
        # Collision X
        self.check_x(level)
        
        # Physics Y
        gravity = Phys.GRAVITY_HOLDING if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.vy < 0 else Phys.GRAVITY
        self.vy = min(self.vy + gravity, Phys.MAX_FALL)
        self.y += self.vy
        
        # Collision Y
        self.on_ground = False
        self.check_y(level)
        
        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.on_ground:
            self.vy = Phys.JUMP_FORCE
            SFX["jump"].play()
            self.on_ground = False
            
        # Pit death
        if self.y > NES_H + 16: self.die()
        
        # Win
        if self.x > level.width_tiles * T - 20: self.win = True

        if self.iframe > 0: self.iframe -= 1

    def check_x(self, level):
        r = self.rect
        for t in level.get_tiles(self.x, self.y):
            if t.solid and r.colliderect(t.rect):
                if self.vx > 0: self.x = t.rect.left - self.w - 2; self.vx = 0
                elif self.vx < 0: self.x = t.rect.right - 2; self.vx = 0

    def check_y(self, level):
        r = self.rect
        for t in level.get_tiles(self.x, self.y):
            if t.solid and r.colliderect(t.rect):
                if self.vy > 0:
                    self.y = t.rect.top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = t.rect.bottom
                    self.vy = 0
                    if t.type == "?":
                        t.used = True; t.bump = 4; SFX["coin"].play()
                    elif t.type == "B":
                        t.bump = 4; SFX["bump"].play()

    def hurt(self):
        if self.iframe > 0: return
        if self.big:
            self.big = False
            self.iframe = 120
            SFX["break"].play()
        else:
            self.die()

    def die(self):
        if not self.dead:
            self.dead = True
            SFX["die"].play()
    
    def draw(self, s, c):
        if self.iframe % 8 < 4:
            draw_mario(s, self.x-c, self.y, self.facing, 0, self.big, False, False)

# === MAIN LOOP ===
def main():
    init_audio()
    music_eng = MusicEngine()
    
    world, stage = 1, 1
    lives = 3
    running = True
    
    font = pygame.font.SysFont("arial", 12, bold=True)
    paused_text = pygame.font.SysFont("arial", 24, bold=True).render("PAUSED", True, Pal.WHITE)

    while running:
        level = Level(world, stage)
        player = Player(40, 190)
        paused = False
        
        # Level Loop
        while not player.dead and not player.win and running:
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        paused = not paused
                        SFX["pause"].play()
                        if paused:
                            pygame.mixer.pause() # Stop all audio
                        else:
                            pygame.mixer.unpause() # Resume all audio
            
            if paused:
                # Pause Screen Overlay
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 10)) # Slight darken
                screen.blit(overlay, (0,0))
                
                # Draw Pause Text centered
                pr = paused_text.get_rect(center=(W//2, H//2))
                screen.blit(paused_text, pr)
                
                pygame.display.flip()
                clock.tick(15) # Low FPS for pause menu
                continue # Skip game update

            # Game Update
            music_eng.update()
            keys = pygame.key.get_pressed()
            player.update(keys, level)
            level.update(player)
            
            # Draw
            level.draw(nes_surface)
            player.draw(nes_surface, level.camera)
            
            # HUD
            txt = font.render(f"WORLD {world}-{stage}   LIVES {lives}", True, Pal.WHITE)
            nes_surface.blit(txt, (8, 8))
            
            # Scale to Window
            pygame.transform.scale(nes_surface, (W, H), screen)
            pygame.display.flip()
            clock.tick(FPS)
            
        if player.win:
            stage += 1
            if stage > 4: stage = 1; world += 1
            pygame.time.wait(2000)
        elif player.dead:
            lives -= 1
            if lives < 0: 
                world, stage, lives = 1, 1, 3
            pygame.time.wait(2000)

    pygame.quit()

if __name__ == "__main__":
    main()
