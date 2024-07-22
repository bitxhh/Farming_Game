import pygame
# from debug import debug
from level import Level
from settings import *


class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((window_width, window_height), vsync=1)
        self.clock = pygame.time.Clock()
        self.level = Level(self.display_surface)

        pygame.display.set_caption(title)
        pygame.display.set_icon(icon)

    def run(self):
        while True:
            dt = self.clock.tick() / 1000
            self.level.run(dt)
            pygame.display.update()


if __name__ == '__main__':
    main = Main()
    main.run()
