import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 6
FPS = 60

# Colors
SKY_BLUE = (107, 140, 255)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
GREEN = (0, 128, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros. - PC Edition")
clock = pygame.time.Clock()

# Load fonts
try:
    font_large = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)
except:
    font_large = pygame.font.SysFont('arial', 48)
    font_medium = pygame.font.SysFont('arial', 36)
    font_small = pygame.font.SysFont('arial', 24)

# Create simple sound effects using pygame.mixer.Sound (placeholder)
def create_beep_sound(frequency=440, duration=100):
    sample_rate = 44100
    n_samples = int(round(duration * 0.001 * sample_rate))
    buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
    max_sample = 2**(16 - 1) - 1
    for s in range(n_samples):
        t = float(s) / sample_rate
        buf[s][0] = int(round(max_sample * math.sin(2 * math.pi * frequency * t)))
        buf[s][1] = int(round(max_sample * math.sin(2 * math.pi * frequency * t)))
    return pygame.sndarray.make_sound(buf)

# Try to create sounds, fallback to silent sounds if numpy not available
try:
    import importlib
    import importlib.util
    # Only import numpy if present on the system to avoid unresolved-import warnings
    if importlib.util.find_spec("numpy") is not None:
        numpy = importlib.import_module("numpy")
        jump_sound = create_beep_sound(523, 100)  # C note
        coin_sound = create_beep_sound(659, 150)  # E note
        enemy_sound = create_beep_sound(220, 200)  # A note
        game_over_sound = create_beep_sound(110, 500)  # Low A note
    else:
        raise ImportError("numpy not available")
except Exception:
    # Create silent sounds as fallback
    jump_sound = pygame.mixer.Sound(bytes(0))
    coin_sound = pygame.mixer.Sound(bytes(0))
    enemy_sound = pygame.mixer.Sound(bytes(0))
    game_over_sound = pygame.mixer.Sound(bytes(0))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.jumping = False
        self.direction = 1  # 1 for right, -1 for left
        self.lives = 3
        self.score = 0
        self.coins = 0
        self.invincible = 0
        self.animation_frame = 0
        self.walk_cycle = 0
    
    def move(self, dx):
        self.vel_x = dx
        if dx != 0:
            self.direction = 1 if dx > 0 else -1
            self.walk_cycle = (self.walk_cycle + 1) % 20
    
    def jump(self):
        if not self.jumping:
            self.vel_y = JUMP_STRENGTH
            self.jumping = True
            jump_sound.play()
    
    def update(self, platforms, enemies, coins, flag):
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Update position with collision detection
        self.x += self.vel_x
        
        # Horizontal collision
        for platform in platforms:
            if self.collision(platform):
                if self.vel_x > 0:  # Moving right
                    self.x = platform.x - self.width
                elif self.vel_x < 0:  # Moving left
                    self.x = platform.x + platform.width
                self.vel_x = 0
        
        # Vertical movement and collision
        self.y += self.vel_y
        on_ground = False
        
        for platform in platforms:
            if self.collision(platform):
                if self.vel_y > 0:  # Falling
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.jumping = False
                    on_ground = True
                elif self.vel_y < 0:  # Jumping
                    self.y = platform.y + platform.height
                    self.vel_y = 0
        
        # Screen boundaries
        if self.x < 0:
            self.x = 0
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        
        # Check if fell off the screen
        if self.y > SCREEN_HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                self.respawn()
            return "fall"
        
        # Check enemy collisions
        if self.invincible <= 0:
            for enemy in enemies[:]:
                if self.collision(enemy):
                    # If jumping on enemy
                    if self.vel_y > 0 and self.y < enemy.y:
                        enemies.remove(enemy)
                        self.vel_y = JUMP_STRENGTH * 0.7  # Bounce
                        self.score += 100
                        enemy_sound.play()
                    else:
                        self.lives -= 1
                        self.invincible = 90  # 1.5 seconds of invincibility
                        if self.lives > 0:
                            self.respawn()
                        return "hit"
        
        # Check coin collisions
        for coin in coins[:]:
            if self.collision(coin):
                coins.remove(coin)
                self.coins += 1
                self.score += 200
                coin_sound.play()
        
        # Check flag collision
        if flag and self.collision(flag):
            return "level_complete"
        
        # Decrease invincibility timer
        if self.invincible > 0:
            self.invincible -= 1
        
        return None
    
    def collision(self, obj):
        return (self.x < obj.x + obj.width and
                self.x + self.width > obj.x and
                self.y < obj.y + obj.height and
                self.y + self.height > obj.y)
    
    def respawn(self):
        self.x = 100
        self.y = 300
        self.vel_x = 0
        self.vel_y = 0
        self.jumping = False
    
    def draw(self):
        # Flash when invincible
        if self.invincible > 0 and self.invincible % 10 < 5:
            return
        
        # Draw Mario with simple animation
        color = RED
        hat_color = RED
        overall_color = BLUE
        skin_color = (255, 200, 150)
        
        # Body
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
        # Hat
        pygame.draw.rect(screen, hat_color, (self.x - 5, self.y, self.width + 10, 10))
        pygame.draw.rect(screen, hat_color, (self.x + 5, self.y - 5, self.width - 10, 5))
        
        # Face
        pygame.draw.circle(screen, skin_color, (self.x + self.width//2, self.y + 15), 8)
        
        # Overalls
        pygame.draw.rect(screen, overall_color, (self.x, self.y + 25, self.width, 25))
        pygame.draw.rect(screen, color, (self.x + 5, self.y + 25, self.width - 10, 5))
        
        # Arms and legs with walking animation
        if self.vel_x != 0 and not self.jumping:
            arm_offset = math.sin(self.walk_cycle * 0.3) * 3
            leg_offset = math.sin(self.walk_cycle * 0.3 + math.pi) * 3
        else:
            arm_offset = 0
            leg_offset = 0
        
        # Arms
        pygame.draw.rect(screen, skin_color, (self.x - 5, self.y + 20, 5, 15))
        pygame.draw.rect(screen, skin_color, (self.x + self.width, self.y + 20, 5, 15))
        
        # Legs
        pygame.draw.rect(screen, overall_color, (self.x + 5, self.y + self.height, 7, 10 + leg_offset))
        pygame.draw.rect(screen, overall_color, (self.x + self.width - 12, self.y + self.height, 7, 10 - leg_offset))

class Platform:
    def __init__(self, x, y, width, height, color=BROWN, texture=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.texture = texture
    
    def draw(self):
        # Draw platform base
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

        # Add brick texture
        if self.width > 20 and self.height > 10:
            # Ensure we have an RGB tuple and clamp values to the 0-255 range
            try:
                if isinstance(self.color, pygame.Color):
                    base_rgb = (self.color.r, self.color.g, self.color.b)
                else:
                    # Support tuples/lists of length 3 or 4
                    base_rgb = tuple(self.color[:3])
            except Exception:
                # Fallback to a safe brown if color is unexpected
                base_rgb = (120, 70, 20)

            darker = tuple(max(0, min(255, int(c) - 20)) for c in base_rgb)

            brick_width = 20
            brick_height = 10
            for i in range(0, int(self.width), brick_width):
                for j in range(0, int(self.height), brick_height):
                    pygame.draw.rect(screen, darker,
                                     (self.x + i, self.y + j, brick_width-1, brick_height-1), 1)

class Enemy:
    def __init__(self, x, y, move_range=100):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.start_x = x
        self.move_range = move_range
        self.vel_x = -2
        self.animation_frame = 0
    
    def update(self, platforms):
        # Move enemy
        self.x += self.vel_x
        self.animation_frame = (self.animation_frame + 1) % 30
        
        # Reverse direction at movement boundaries
        if self.x < self.start_x - self.move_range or self.x > self.start_x + self.move_range:
            self.vel_x *= -1
        
        # Check for platform edges
        on_platform = False
        for platform in platforms:
            # Check if enemy is on this platform
            if (self.y + self.height >= platform.y and 
                self.y + self.height <= platform.y + 10 and
                self.x + self.width > platform.x and 
                self.x < platform.x + platform.width):
                on_platform = True
                break
        
        # If not on a platform, turn around
        if not on_platform:
            self.vel_x *= -1
    
    def draw(self):
        # Draw Goomba with simple animation
        body_color = (120, 70, 0)
        underside_color = (100, 50, 0)
        foot_color = (80, 40, 0)
        
        # Body
        pygame.draw.ellipse(screen, body_color, (self.x, self.y, self.width, self.height))
        
        # Underside
        pygame.draw.ellipse(screen, underside_color, (self.x + 5, self.y + 5, self.width - 10, self.height - 10))
        
        # Feet with simple animation
        foot_offset = 0
        if self.animation_frame < 15:
            foot_offset = 2
        
        pygame.draw.ellipse(screen, foot_color, (self.x + 5, self.y + self.height - 5, 8, 5 + foot_offset))
        pygame.draw.ellipse(screen, foot_color, (self.x + self.width - 13, self.y + self.height - 5, 8, 5 + foot_offset))
        
        # Eyes
        eye_offset = 0
        if self.vel_x < 0:  # Looking left
            eye_offset = -2
        else:  # Looking right
            eye_offset = 2
            
        pygame.draw.circle(screen, WHITE, (self.x + 10, self.y + 10), 4)
        pygame.draw.circle(screen, WHITE, (self.x + self.width - 10, self.y + 10), 4)
        pygame.draw.circle(screen, BLACK, (self.x + 10 + eye_offset, self.y + 10), 2)
        pygame.draw.circle(screen, BLACK, (self.x + self.width - 10 + eye_offset, self.y + 10), 2)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.animation_frame = random.random() * 10
        self.collected = False
    
    def update(self):
        self.animation_frame += 0.2
    
    def draw(self):
        if not self.collected:
            # Bobbing and spinning animation
            bob_y = self.y + math.sin(self.animation_frame) * 5
            rotation = self.animation_frame * 20
            
            # Draw coin with simple rotation effect
            coin_radius = 8
            center_x = self.x + self.width/2
            center_y = bob_y + self.height/2
            
            # Outer gold circle
            pygame.draw.circle(screen, YELLOW, (int(center_x), int(center_y)), coin_radius)
            
            # Inner orange circle
            pygame.draw.circle(screen, ORANGE, (int(center_x), int(center_y)), coin_radius - 2)
            
            # Shine effect
            shine_x = center_x + math.cos(rotation * math.pi/180) * 3
            shine_y = center_y + math.sin(rotation * math.pi/180) * 3
            pygame.draw.circle(screen, (255, 255, 200), (int(shine_x), int(shine_y)), 2)

class Flag:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 60
        self.flag_wave = 0
    
    def update(self):
        self.flag_wave += 0.1
    
    def draw(self):
        # Draw flag pole
        pygame.draw.rect(screen, (220, 220, 220), (self.x, self.y, 5, self.height))
        pygame.draw.rect(screen, (180, 180, 180), (self.x - 2, self.y, 9, 5))
        
        # Draw flag with waving animation
        wave_offset = math.sin(self.flag_wave) * 3
        pygame.draw.polygon(screen, RED, [
            (self.x + 5, self.y + 10),
            (self.x + 25 + wave_offset, self.y + 15),
            (self.x + 5, self.y + 30)
        ])

class Game:
    def __init__(self):
        self.player = Player(100, 300)
        self.current_level = 1
        self.platforms = []
        self.enemies = []
        self.coins = []
        self.flag = None
        self.game_state = "menu"  # "menu", "playing", "level_complete", "game_over", "game_complete"
        self.level_complete_timer = 0
        self.camera_x = 0
        self.setup_level()
    
    def setup_level(self):
        # Clear previous level
        self.platforms.clear()
        self.enemies.clear()
        self.coins.clear()
        self.flag = None
        
        # Ground platform (longer for scrolling)
        level_width = 2400 if self.current_level == 3 else 1600
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 50, level_width, 50, BROWN))
        
        if self.current_level == 1:
            # Level 1 - Basic platforming
            self.platforms.append(Platform(200, 450, 100, 20, GREEN))
            self.platforms.append(Platform(400, 400, 100, 20, GREEN))
            self.platforms.append(Platform(600, 350, 100, 20, GREEN))
            self.platforms.append(Platform(300, 300, 100, 20, GREEN))
            self.platforms.append(Platform(500, 250, 100, 20, GREEN))
            
            self.enemies.append(Enemy(300, 420, 80))
            self.enemies.append(Enemy(500, 370, 80))
            
            for i in range(8):
                self.coins.append(Coin(250 + i * 80, 200 + (i % 3) * 50))
            
            self.flag = Flag(900, 200)
        
        elif self.current_level == 2:
            # Level 2 - More challenging
            self.platforms.append(Platform(150, 450, 80, 20, GREEN))
            self.platforms.append(Platform(300, 400, 80, 20, GREEN))
            self.platforms.append(Platform(450, 350, 80, 20, GREEN))
            self.platforms.append(Platform(250, 300, 80, 20, GREEN))
            self.platforms.append(Platform(400, 250, 80, 20, GREEN))
            self.platforms.append(Platform(550, 200, 80, 20, GREEN))
            self.platforms.append(Platform(700, 300, 80, 20, GREEN))
            
            self.enemies.append(Enemy(200, 420, 100))
            self.enemies.append(Enemy(350, 370, 100))
            self.enemies.append(Enemy(500, 320, 100))
            self.enemies.append(Enemy(650, 270, 100))
            
            for i in range(12):
                x = 200 + (i * 70)
                y = 150 + (i % 4) * 60
                self.coins.append(Coin(x, y))
            
            self.flag = Flag(1200, 150)
        
        elif self.current_level == 3:
            # Level 3 - Advanced platforming
            self.platforms.append(Platform(100, 450, 60, 20, GREEN))
            self.platforms.append(Platform(200, 400, 60, 20, GREEN))
            self.platforms.append(Platform(300, 450, 60, 20, GREEN))
            self.platforms.append(Platform(400, 400, 60, 20, GREEN))
            self.platforms.append(Platform(500, 450, 60, 20, GREEN))
            self.platforms.append(Platform(600, 400, 60, 20, GREEN))
            self.platforms.append(Platform(700, 350, 60, 20, GREEN))
            self.platforms.append(Platform(800, 300, 60, 20, GREEN))
            self.platforms.append(Platform(900, 250, 60, 20, GREEN))
            self.platforms.append(Platform(1000, 200, 60, 20, GREEN))
            self.platforms.append(Platform(1100, 150, 60, 20, GREEN))
            
            self.enemies.append(Enemy(150, 420, 50))
            self.enemies.append(Enemy(250, 370, 50))
            self.enemies.append(Enemy(350, 420, 50))
            self.enemies.append(Enemy(450, 370, 50))
            self.enemies.append(Enemy(550, 420, 50))
            self.enemies.append(Enemy(650, 320, 50))
            self.enemies.append(Enemy(750, 270, 50))
            self.enemies.append(Enemy(850, 220, 50))
            self.enemies.append(Enemy(950, 170, 50))
            
            for i in range(20):
                x = 150 + (i * 60)
                y = 100 + (i % 5) * 40
                self.coins.append(Coin(x, y))
            
            self.flag = Flag(2000, 100)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.game_state == "playing":
                    self.player.jump()
                if event.key == pygame.K_RETURN:
                    if self.game_state == "menu":
                        self.game_state = "playing"
                    elif self.game_state in ["game_over", "game_complete"]:
                        self.reset_game()
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.game_state = "menu"
                    else:
                        return False
                if event.key == pygame.K_r and self.game_state == "playing":
                    self.reset_level()
        
        # Handle continuous key presses
        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.move(-MOVE_SPEED)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.move(MOVE_SPEED)
            else:
                self.player.move(0)
        
        return True
    
    def update_camera(self):
        # Simple camera that follows the player
        target_x = self.player.x - SCREEN_WIDTH // 2
        self.camera_x += (target_x - self.camera_x) * 0.1
        
        # Clamp camera to level boundaries
        if self.current_level == 3:
            max_camera = 2400 - SCREEN_WIDTH
        else:
            max_camera = 1600 - SCREEN_WIDTH
            
        self.camera_x = max(0, min(self.camera_x, max_camera))
    
    def update(self):
        if self.game_state == "playing":
            # Update camera
            self.update_camera()
            
            # Update player
            result = self.player.update(self.platforms, self.enemies, self.coins, self.flag)
            
            # Update enemies
            for enemy in self.enemies:
                enemy.update(self.platforms)
            
            # Update coins
            for coin in self.coins:
                coin.update()
            
            # Update flag
            if self.flag:
                self.flag.update()
            
            # Check for level completion
            if result == "level_complete":
                self.game_state = "level_complete"
                self.level_complete_timer = 180  # 3 seconds at 60 FPS
            
            # Check for game over
            if self.player.lives <= 0:
                self.game_state = "game_over"
                game_over_sound.play()
        
        elif self.game_state == "level_complete":
            self.level_complete_timer -= 1
            if self.level_complete_timer <= 0:
                self.current_level += 1
                if self.current_level > 3:
                    self.game_state = "game_complete"
                else:
                    self.setup_level()
                    self.player.respawn()
                    self.camera_x = 0
                    self.game_state = "playing"
    
    def draw(self):
        # Draw background
        screen.fill(SKY_BLUE)
        
        # Draw parallax clouds
        for i in range(5):
            cloud_x = (self.camera_x * 0.3 + i * 300) % (SCREEN_WIDTH + 400) - 200
            cloud_y = 50 + i * 40
            cloud_size = 80 + i * 10
            self.draw_cloud(cloud_x, cloud_y, cloud_size)
        
        # Draw level elements with camera offset
        for platform in self.platforms:
            platform.draw()
        
        for coin in self.coins:
            # Only draw coins that are visible
            if -coin.width < coin.x - self.camera_x < SCREEN_WIDTH:
                coin.draw()
        
        for enemy in self.enemies:
            # Only draw enemies that are visible
            if -enemy.width < enemy.x - self.camera_x < SCREEN_WIDTH:
                enemy.draw()
        
        if self.flag and -self.flag.width < self.flag.x - self.camera_x < SCREEN_WIDTH:
            self.flag.draw()
        
        # Draw player
        self.player.draw()
        
        # Draw HUD (always on screen, not affected by camera)
        self.draw_hud()
        
        # Draw game state messages
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "game_over":
            self.draw_game_over()
        elif self.game_state == "level_complete":
            self.draw_level_complete()
        elif self.game_state == "game_complete":
            self.draw_game_complete()
    
    def draw_cloud(self, x, y, size):
        pygame.draw.ellipse(screen, WHITE, (x, y, size, size//2))
        pygame.draw.ellipse(screen, WHITE, (x + size//3, y - size//4, size//2, size//2))
        pygame.draw.ellipse(screen, WHITE, (x + size//2, y, size//2, size//3))
    
    def draw_hud(self):
        # Transparent background for HUD
        hud_bg = pygame.Surface((SCREEN_WIDTH, 70), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 128))
        screen.blit(hud_bg, (0, 0))
        
        # Draw HUD elements
        lives_text = font_medium.render(f"Lives: {self.player.lives}", True, WHITE)
        score_text = font_medium.render(f"Score: {self.player.score}", True, WHITE)
        coins_text = font_medium.render(f"Coins: {self.player.coins}", True, WHITE)
        level_text = font_medium.render(f"Level: {self.current_level}/3", True, WHITE)
        
        screen.blit(lives_text, (20, 20))
        screen.blit(score_text, (200, 20))
        screen.blit(coins_text, (SCREEN_WIDTH - 200, 20))
        screen.blit(level_text, (SCREEN_WIDTH - 150, 50))
        
        # Draw controls help
        if self.game_state == "playing":
            controls_text = font_small.render("Arrows/WASD: Move | Space: Jump | R: Restart Level | ESC: Menu", True, WHITE)
            screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2, SCREEN_HEIGHT - 30))
    
    def draw_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title_text = font_large.render("SUPER MARIO BROS.", True, RED)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 150))
        
        # Menu options
        start_text = font_medium.render("Press ENTER to Start", True, WHITE)
        screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 250))
        
        controls_text = font_small.render("Controls: Arrow Keys/WASD to Move, Space to Jump", True, WHITE)
        screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2, 300))
        
        quit_text = font_small.render("Press ESC to Quit", True, WHITE)
        screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, 350))
    
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        game_over_text = font_large.render("GAME OVER", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 200))
        
        score_text = font_medium.render(f"Final Score: {self.player.score}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 280))
        
        restart_text = font_medium.render("Press ENTER to Play Again", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 350))
    
    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        complete_text = font_large.render("LEVEL COMPLETE!", True, GREEN)
        screen.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, 200))
        
        if self.current_level < 3:
            next_text = font_medium.render(f"Get ready for Level {self.current_level + 1}!", True, WHITE)
            screen.blit(next_text, (SCREEN_WIDTH//2 - next_text.get_width()//2, 280))
        else:
            next_text = font_medium.render("Final level completed!", True, WHITE)
            screen.blit(next_text, (SCREEN_WIDTH//2 - next_text.get_width()//2, 280))
    
    def draw_game_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        complete_text = font_large.render("YOU WIN!", True, GREEN)
        screen.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, 180))
        
        congrats_text = font_medium.render("Congratulations! You completed all levels!", True, WHITE)
        screen.blit(congrats_text, (SCREEN_WIDTH//2 - congrats_text.get_width()//2, 250))
        
        score_text = font_medium.render(f"Final Score: {self.player.score}", True, YELLOW)
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 300))
        
        coins_text = font_medium.render(f"Coins Collected: {self.player.coins}", True, YELLOW)
        screen.blit(coins_text, (SCREEN_WIDTH//2 - coins_text.get_width()//2, 340))
        
        restart_text = font_medium.render("Press ENTER to Play Again", True, WHITE)
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 400))
    
    def reset_game(self):
        self.player = Player(100, 300)
        self.current_level = 1
        self.setup_level()
        self.camera_x = 0
        self.game_state = "playing"
    
    def reset_level(self):
        self.player.respawn()
        self.setup_level()
        self.camera_x = 0

# Main game loop
def main():
    game = Game()
    running = True
    
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
