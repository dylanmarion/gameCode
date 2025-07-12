import pygame
import math

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y, walls):
        super().__init__()
        self.image = pygame.Surface((6, 6))
        self.image.fill((255, 255, 0))  # Yellow bullet
        self.rect = self.image.get_rect(center=(start_x, start_y))
        self.walls = walls
        
        # Calculate direction
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.velocity_x = (dx / distance) * 8  # Bullet speed
            self.velocity_y = (dy / distance) * 8
        else:
            self.velocity_x = 0
            self.velocity_y = 0
            
        # Bullet properties
        self.damage = 2
        self.max_distance = 400
        self.distance_traveled = 0
        
    def update(self):
        """Update bullet position and check for collisions"""
        # Move bullet
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        # Track distance
        self.distance_traveled += abs(self.velocity_x) + abs(self.velocity_y)
        
        # Remove if traveled too far
        if self.distance_traveled > self.max_distance:
            self.kill()
            return
            
        # Check wall collision
        if pygame.sprite.spritecollideany(self, self.walls):
            self.kill()
            return
            
    def check_enemy_collision(self, enemies):
        """Check for collision with enemies and return hit enemy"""
        hit_enemy = pygame.sprite.spritecollideany(self, enemies)
        if hit_enemy:
            self.kill()  # Remove bullet on hit
            return hit_enemy
        return None
