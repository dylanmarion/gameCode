import pygame

class HoleRoom:
    """A large underground room accessed through holes in boss rooms"""
    
    def __init__(self, tile_size):
        self.tile_size = tile_size
        
        # Create a large room (40x30 tiles)
        self.room_width = 40
        self.room_height = 30
        self.world_width = self.room_width * tile_size
        self.world_height = self.room_height * tile_size
        
        # Create tilemap for the hole room
        self.tilemap = self.create_hole_room_tilemap()
        
        # Player spawn position (center of room)
        self.spawn_x = (self.room_width // 2) * tile_size
        self.spawn_y = (self.room_height // 2) * tile_size
    
    def create_hole_room_tilemap(self):
        """Create the tilemap for the hole room - just walls and floor, no exit"""
        tilemap = []
        
        for y in range(self.room_height):
            row = []
            for x in range(self.room_width):
                # Create walls around the perimeter
                if (x == 0 or x == self.room_width - 1 or 
                    y == 0 or y == self.room_height - 1):
                    row.append(1)  # Wall
                else:
                    row.append(0)  # Floor
            tilemap.append(row)
        
        return tilemap
    
    def check_exit_collision(self, player_rect):
        """No exit functionality - this room is a dead end"""
        return False
