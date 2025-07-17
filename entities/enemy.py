import pygame
import random
import math

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, walls, enemy_type="basic"):
        super().__init__()
        self.enemy_type = enemy_type
        self.walls = walls
        self.wall_spatial_grid = None  # Will be set from outside
        
        # Visual properties
        self.image = pygame.Surface((30, 30))
        self.base_color = None
        if enemy_type == "basic":
            self.base_color = (255, 0, 0)  # Red square
            self.speed = 1
            self.health = 3
            self.damage = 1
        elif enemy_type == "fast":
            self.base_color = (255, 100, 0)  # Orange square
            self.speed = 2
            self.health = 2
            self.damage = 1
        elif enemy_type == "tank":
            self.base_color = (150, 0, 0)  # Dark red square
            self.speed = 0.5
            self.health = 5
            self.damage = 2
        
        self.image.fill(self.base_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.max_health = self.health
        
        # AI properties
        self.target = None
        self.detection_range = 200
        self.attack_range = 35
        self.last_attack_time = 0
        self.attack_cooldown = 1000  # milliseconds
        
        # Movement properties
        self.velocity_x = 0
        self.velocity_y = 0
        self.wander_timer = 0
        self.wander_direction = random.uniform(0, 2 * math.pi)
        
    def find_target(self, player):
        """Check if player is within detection range"""
        distance = math.sqrt((self.rect.centerx - player.rect.centerx)**2 + 
                           (self.rect.centery - player.rect.centery)**2)
        if distance <= self.detection_range:
            self.target = player
        else:
            self.target = None
            
    def move_towards_target(self):
        """Move towards the target player"""
        if not self.target:
            return
            
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0 and distance > self.attack_range:
            # Normalize and apply speed
            self.velocity_x = (dx / distance) * self.speed
            self.velocity_y = (dy / distance) * self.speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0
            
    def wander(self):
        """Random wandering behavior when no target"""
        current_time = pygame.time.get_ticks()
        
        # Change direction every 2-4 seconds
        if self.wander_timer == 0 or current_time - self.wander_timer > random.randint(2000, 4000):
            self.wander_direction = random.uniform(0, 2 * math.pi)
            self.wander_timer = current_time
            
        # Move in wander direction at half speed
        self.velocity_x = math.cos(self.wander_direction) * self.speed * 0.3
        self.velocity_y = math.sin(self.wander_direction) * self.speed * 0.3
        
    def move(self, dx, dy):
        """Move with optimized collision detection using spatial grid"""
        # Early exit if not moving
        if dx == 0 and dy == 0:
            return
        
        # Use spatial grid if available, otherwise fall back to distance-based filtering
        if self.wall_spatial_grid:
            nearby_walls = self.wall_spatial_grid.get_nearby_objects(self.rect, padding=20)
        else:
            # Fallback to distance-based filtering
            nearby_walls = []
            enemy_center_x = self.rect.centerx
            enemy_center_y = self.rect.centery
            
            # Only check walls within a reasonable distance
            check_distance = 60  # Adjust based on your tile size and enemy size
            
            for wall in self.walls:
                wall_center_x = wall.rect.centerx
                wall_center_y = wall.rect.centery
                
                # Use Manhattan distance for speed (no sqrt needed)
                distance = abs(enemy_center_x - wall_center_x) + abs(enemy_center_y - wall_center_y)
                
                if distance <= check_distance:
                    nearby_walls.append(wall)
        
        # If no nearby walls, skip collision detection entirely
        if not nearby_walls:
            self.rect.x += dx
            self.rect.y += dy
            return
        
        # Horizontal movement
        self.rect.x += dx
        collided = pygame.sprite.spritecollideany(self, nearby_walls)
        if collided:
            if dx > 0:
                self.rect.right = collided.rect.left
            elif dx < 0:
                self.rect.left = collided.rect.right
            self.velocity_x = 0  # Stop horizontal movement on collision
            
        # Vertical movement
        self.rect.y += dy
        collided = pygame.sprite.spritecollideany(self, nearby_walls)
        if collided:
            if dy > 0:
                self.rect.bottom = collided.rect.top
            elif dy < 0:
                self.rect.top = collided.rect.bottom
            self.velocity_y = 0  # Stop vertical movement on collision
            
    def attack_player(self, player):
        """Attack the player if in range and cooldown is ready"""
        if not self.target:
            return False
            
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time < self.attack_cooldown:
            return False
            
        distance = math.sqrt((self.rect.centerx - player.rect.centerx)**2 + 
                           (self.rect.centery - player.rect.centery)**2)
        
        if distance <= self.attack_range:
            self.last_attack_time = current_time
            player.take_damage(self.damage)
            return True
        return False
        
    def take_damage(self, damage):
        """Take damage and return True if enemy is killed"""
        self.health -= damage
        if self.health <= 0:
            return True
        return False
        
    def update(self, player):
        """Update enemy AI and movement"""
        self.find_target(player)
        
        # Update visual state based on target
        if self.target:
            # Brighten color when targeting player
            color = tuple(min(255, c + 50) for c in self.base_color)
            self.image.fill(color)
        else:
            self.image.fill(self.base_color)
        
        if self.target:
            self.move_towards_target()
            self.attack_player(player)
        else:
            self.wander()
            
        # Apply movement
        self.move(self.velocity_x, self.velocity_y)
        
    def draw_health_bar(self, screen, camera):
        """Draw a health bar above the enemy"""
        if self.health < self.max_health:
            bar_width = 25
            bar_height = 4
            health_ratio = self.health / self.max_health
            
            # Position above enemy
            bar_x = self.rect.centerx - bar_width // 2 - camera.rect.x
            bar_y = self.rect.top - 8 - camera.rect.y
            
            # Background (red)
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # Health (green)
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))
