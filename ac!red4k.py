import pygame
import sys

# --- CONFIGURATION ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 576  # 4x GameBoy Resolution (160x144)
TILE_SIZE = 64        # 4x 16px tiles
FPS = 60
MOVE_SPEED = 4        # Speed of movement (pixels per frame)

# Colors (GameBoy Palette)
COLOR_DARKEST = (15, 56, 15)
COLOR_DARK = (48, 98, 48)
COLOR_LIGHT = (139, 172, 15)
COLOR_LIGHTEST = (155, 188, 15)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --- MAP DATA ---
# 0: Grass, 1: Wall/Bush, 2: Water, 3: Path, 4: Warp/Door
PALLET_TOWN = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 3, 3, 3, 3, 3, 3, 3, 3, 1],
    [1, 3, 0, 0, 0, 0, 0, 0, 3, 1],
    [1, 3, 0, 1, 1, 1, 1, 0, 3, 1],
    [1, 3, 0, 1, 4, 1, 1, 0, 3, 1], # House
    [1, 3, 0, 0, 0, 0, 0, 0, 3, 1],
    [1, 3, 3, 3, 4, 3, 3, 3, 3, 1], # Lab
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# --- CLASSES ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.color = COLOR_DARKEST
        self.target_x = self.rect.x
        self.target_y = self.rect.y
        self.moving = False

    def move(self, dx, dy, current_map):
        if self.moving:
            return

        new_x = (self.rect.x // TILE_SIZE) + dx
        new_y = (self.rect.y // TILE_SIZE) + dy

        # Collision Check
        if 0 <= new_y < len(current_map) and 0 <= new_x < len(current_map[0]):
            if current_map[new_y][new_x] != 1:  # Not a wall
                self.target_x = new_x * TILE_SIZE
                self.target_y = new_y * TILE_SIZE
                self.moving = True

    def update(self):
        if self.moving:
            if self.rect.x < self.target_x: self.rect.x += MOVE_SPEED
            elif self.rect.x > self.target_x: self.rect.x -= MOVE_SPEED
            
            if self.rect.y < self.target_y: self.rect.y += MOVE_SPEED
            elif self.rect.y > self.target_y: self.rect.y -= MOVE_SPEED

            if self.rect.x == self.target_x and self.rect.y == self.target_y:
                self.moving = False

    def draw(self, surface):
        # Draw a simple "Red" character sprite
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, WHITE, (self.rect.x + 10, self.rect.y + 10, 10, 10)) # Left Eye
        pygame.draw.rect(surface, WHITE, (self.rect.x + 40, self.rect.y + 10, 10, 10)) # Right Eye

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cat's ! Pokemon Red [MR.AC]")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 20, bold=True)
        
        self.player = Player(4, 5)
        self.current_map = PALLET_TOWN
        self.dialogue = "Welcome to Pallet Town!"
        self.running = True

    def draw_map(self):
        for row_index, row in enumerate(self.current_map):
            for col_index, tile in enumerate(row):
                rect = pygame.Rect(col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile == 0: color = COLOR_LIGHT      # Grass
                elif tile == 1: color = COLOR_DARK     # Bush/Wall
                elif tile == 3: color = COLOR_LIGHTEST # Path
                elif tile == 4: color = (100, 100, 255) # Door
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1) # Tile borders

    def draw_ui(self):
        # Dialogue Box
        ui_rect = pygame.Rect(10, SCREEN_HEIGHT - 100, SCREEN_WIDTH - 20, 90)
        pygame.draw.rect(self.screen, WHITE, ui_rect)
        pygame.draw.rect(self.screen, BLACK, ui_rect, 4)
        
        text_surf = self.font.render(self.dialogue, True, BLACK)
        self.screen.blit(text_surf, (25, SCREEN_HEIGHT - 80))
        
        # Header Info
        header_text = self.font.render("CAT'S ! RED [MR.AC] - 60 FPS", True, WHITE)
        self.screen.blit(header_text, (10, 10))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:    self.player.move(0, -1, self.current_map)
        if keys[pygame.K_DOWN]:  self.player.move(0, 1, self.current_map)
        if keys[pygame.K_LEFT]:  self.player.move(-1, 0, self.current_map)
        if keys[pygame.K_RIGHT]: self.player.move(1, 0, self.current_map)

    def run(self):
        while self.running:
            self.handle_input()
            self.player.update()
            
            # Rendering
            self.screen.fill(COLOR_DARK)
            self.draw_map()
            self.player.draw(self.screen)
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
