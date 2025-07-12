import pygame
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, walls):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((0, 255, 0))  # Green square
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 5
        self.walls = walls
        
        # Health system
        self.health = 100
        self.max_health = 100
        
        # Shooting system
        self.last_shot_time = 0
        self.shot_cooldown = 200  # milliseconds

    def move(self, dx, dy):
        # Horizontal movement
        self.rect.x += dx
        collided = pygame.sprite.spritecollideany(self, self.walls)
        if collided:
            if dx > 0:
                self.rect.right = collided.rect.left
            elif dx < 0:
                self.rect.left = collided.rect.right

    # Vertical movement
        self.rect.y += dy
        collided = pygame.sprite.spritecollideany(self, self.walls)
        if collided:
            if dy > 0:
                self.rect.bottom = collided.rect.top
            elif dy < 0:
                self.rect.top = collided.rect.bottom

    def handle_input(self):
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: dy = -self.speed
        if keys[pygame.K_s]: dy = self.speed
        if keys[pygame.K_a]: dx = -self.speed
        if keys[pygame.K_d]: dx = self.speed
        self.move(dx, dy)

    def update(self):
        self.handle_input()

    def shoot(self, mouse_x, mouse_y, camera):
        """Shoot a bullet toward the mouse cursor"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time < self.shot_cooldown:
            return None
            
        # Calculate world coordinates of mouse click
        world_mouse_x = mouse_x + camera.rect.x
        world_mouse_y = mouse_y + camera.rect.y
        
        # Create bullet with target coordinates
        from entities.bullet import Bullet
        bullet = Bullet(self.rect.centerx, self.rect.centery, world_mouse_x, world_mouse_y, self.walls)
        self.last_shot_time = current_time
        return bullet
    
    def take_damage(self, damage):
        """Take damage and return True if player dies"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            return True
        return False
    
    def draw_health_bar(self, screen, camera):
        """Draw player health bar"""
        bar_width = 200
        bar_height = 20
        health_ratio = self.health / self.max_health
        
        # Position at top of screen
        bar_x = 10
        bar_y = 10
        
        # Background (dark red)
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Health (green)
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))
        # Border
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Health text
        font = pygame.font.Font(None, 24)
        health_text = f"HP: {self.health}/{self.max_health}"
        text_surface = font.render(health_text, True, (255, 255, 255))
        screen.blit(text_surface, (bar_x + bar_width + 10, bar_y))