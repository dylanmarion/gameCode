import pygame

class Room:
    def __init__(self, x, y, w, h, room_type="normal"):
        self.rect = pygame.Rect(x, y, w, h)
        self.center = self.rect.center
        self.revealed = False
        self.room_type = room_type  # "normal", "chest", "spawn", "shop", "boss"
        self.single_connection = False  # Special rooms should only have one connection
        self.connections = []  # Track which rooms this is connected to