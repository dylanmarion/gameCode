"""
Spatial Grid for optimized collision detection
"""
import pygame
from collections import defaultdict

class SpatialGrid:
    def __init__(self, cell_size=64):
        self.cell_size = cell_size
        self.grid = defaultdict(list)
        
    def clear(self):
        """Clear all objects from the grid"""
        self.grid.clear()
        
    def insert(self, obj, rect):
        """Insert an object into the grid based on its rect"""
        # Calculate which grid cells this object occupies
        min_x = rect.left // self.cell_size
        max_x = rect.right // self.cell_size
        min_y = rect.top // self.cell_size
        max_y = rect.bottom // self.cell_size
        
        # Add object to all cells it occupies
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                self.grid[(x, y)].append(obj)
                
    def get_nearby_objects(self, rect, padding=0):
        """Get all objects near the given rect"""
        # Expand rect by padding
        expanded_rect = pygame.Rect(
            rect.left - padding,
            rect.top - padding,
            rect.width + 2 * padding,
            rect.height + 2 * padding
        )
        
        # Find which cells to check
        min_x = expanded_rect.left // self.cell_size
        max_x = expanded_rect.right // self.cell_size
        min_y = expanded_rect.top // self.cell_size
        max_y = expanded_rect.bottom // self.cell_size
        
        # Collect all objects from relevant cells
        nearby_objects = set()
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                nearby_objects.update(self.grid[(x, y)])
                
        return list(nearby_objects)
        
    def build_from_sprite_group(self, sprite_group):
        """Build the grid from a pygame sprite group"""
        self.clear()
        for sprite in sprite_group:
            self.insert(sprite, sprite.rect)
