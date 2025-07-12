import pygame

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill((120, 120, 120))  # Gray wall
        self.rect = self.image.get_rect(topleft=(x, y))