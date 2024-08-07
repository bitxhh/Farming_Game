import pygame
from settings import *


class Overlay:
    def __init__(self, player):

        # general sett
        self.display_surface = pygame.display.get_surface()
        self.player = player

        # imports
        overlay_path = 'graphics/overlay/'
        self.tool_surf = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in player.tools}
        self.seed_surf = {seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in player.seeds}

    def display(self):
        # tools
        tool_surf = self.tool_surf[self.player.selected_tool]
        tool_rect = tool_surf.get_rect(midbottom=overlay_pos['tool'])
        self.display_surface.blit(tool_surf, tool_rect)

        # seeds
        seed_surf = self.seed_surf[self.player.selected_seed]
        seed_rect = seed_surf.get_rect(midbottom=overlay_pos['seed'])
        self.display_surface.blit(seed_surf, seed_rect)
