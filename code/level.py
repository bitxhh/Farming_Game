import pygame
import sys
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from support import import_folder
from transition import Transition
from soil import SoilLayer
# from debug import debug
from sky import Rain, Sky
from random import randint
from Menu import Menu


class Level:
    def __init__(self, display_surface):

        self.shop_active = False
        self.player = None
        self.display_surface = display_surface

        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()
        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        self.rain = Rain(self.all_sprites)
        self.raining = randint(0, 10) > 3
        self.soil_layer.raining = self.raining
        self.sky = Sky()
        self.menu = Menu(self.player, self.toggle_shop)

        self.success = pygame.mixer.Sound('audio/success.wav')
        self.success.set_volume(0.3)

        self.music = pygame.mixer.Sound('audio/music.mp3')
        # self.music.play(loops=-1)

    def setup(self):
        tmx_data = load_pygame('data/map.tmx')
        # house
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x*tile_size, y*tile_size), surf, self.all_sprites, LAYERS['house bottom'])

        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x*tile_size, y*tile_size), surf, self.all_sprites)
        # zabor
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x * tile_size, y * tile_size), surf, [self.all_sprites, self.collision_sprites])

        # water
        water_frames = import_folder('graphics/water')
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water((x * tile_size, y * tile_size), water_frames, self.all_sprites)

        # wild flower
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        # tree
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree(pos=(obj.x, obj.y),
                 surf=obj.image,
                 group=[self.all_sprites, self.collision_sprites, self.tree_sprites],
                 name=obj.name,
                 player_add=self.player_add)

        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x*tile_size, y*tile_size), pygame.Surface((tile_size, tile_size)), self.collision_sprites)

        # general
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(pos=(obj.x, obj.y),
                                     group=self.all_sprites,
                                     collision_sprites=self.collision_sprites,
                                     tree_sprites=self.tree_sprites,
                                     interaction=self.interaction_sprites,
                                     soil_layer=self.soil_layer,
                                     toggle_shop=self.toggle_shop)
            if obj.name == 'Bed':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

            if obj.name == 'Trader':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, obj.name)

        Generic(
            pos=(0, 0),
            surface=pygame.image.load('graphics/world/ground.png').convert_alpha(),
            group=self.all_sprites,
            z=LAYERS['ground']
        )

    def player_add(self, item):
        self.player.item_inventory[item] += 1
        self.success.play()

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        if self.player.sleep:
            self.transition.play()

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def reset(self):
        self.soil_layer.update_plants()

        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 3
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_group.sprites():
                apple.kill()
            tree.create_fruit()

        self.sky.start_color = [255, 255, 255]

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player_add(plant.plant_type)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image, self.all_sprites, LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // tile_size][plant.rect.centerx // tile_size].remove('P')

    def run(self, dt):

        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)

        if self.shop_active:
            self.menu.update()
        else:
            self.all_sprites.update(dt)
            self.plant_collision()

        self.overlay.display()
        if self.raining and not self.shop_active:
            self.rain.update()
        self.sky.display(dt)

        self.event_loop()


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - window_width / 2
        self.offset.y = player.rect.centery - window_height / 2

        for layer in LAYERS.values():
            for sprite in sorted(self.sprites(), key=lambda allsprite: allsprite.rect.centery):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)
