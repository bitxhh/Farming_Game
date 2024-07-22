import pygame.sprite
from random import choice
from settings import *
from pytmx.util_pygame import load_pygame
from support import *


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']

class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)

        self.plant_type = plant_type
        self.frames = import_folder_dict(f'graphics/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = check_watered

        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        self.image = self.frames[str(self.age)]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-20, -self.rect.height * 0.9)
            
            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[str(int(self.age))]
            self.rect = self.image
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))


class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']


class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):

        self.raining = None
        self.hit_rects = None
        self.grid = list()
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.soil_surfs = import_folder_dict('graphics/soil/')
        self.water_surfs = import_folder('graphics/soil_water')
        self.create_soil_grid()
        self.create_hit_rects()

        self.plant = pygame.mixer.Sound('audio/plant.wav')
        self.plant.set_volume(0.2)
        self.hoe_sound = pygame.mixer.Sound('audio/hoe.wav')
        self.hoe_sound.set_volume(0.07)

    def create_soil_grid(self):
        ground = pygame.image.load('graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // tile_size, ground.get_height() // tile_size
        self.grid = [[[] for _ in range(h_tiles)] for _ in range(v_tiles)]
        for x, y, _ in load_pygame('data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * tile_size
                    y = index_row * tile_size
                    rect = pygame.Rect(x, y, tile_size, tile_size)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        self.hoe_sound.play()
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                x = rect.x // tile_size
                y = rect.y // tile_size

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // tile_size
                y = soil_sprite.rect.y // tile_size
                self.grid[y][x].append('W')

                WaterTile(pos=soil_sprite.rect.topleft,
                          surf=choice(self.water_surfs),
                          groups=[self.all_sprites, self.water_sprites])

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * tile_size
                    y = index_row * tile_size
                    WaterTile(pos=(x, y),
                              surf=choice(self.water_surfs),
                              groups=[self.all_sprites, self.water_sprites])

    def remove_water(self):
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // tile_size
        y = pos[1] // tile_size
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def plant_seed(self, target_pos, seed, inventory):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                self.plant.play()
                x = soil_sprite.rect.x // tile_size
                y = soil_sprite.rect.y // tile_size
                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    inventory[seed] -= 1
                    Plant(seed,
                          [self.all_sprites, self.plant_sprites,  self.collision_sprites], 
                          soil_sprite, 
                          self.check_watered)

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                    top = 'X' in self.grid[index_row - 1][index_col]
                    bottom = 'X' in self.grid[index_row + 1][index_col]
                    right = 'X' in row[index_col + 1]
                    left = 'X' in row[index_col - 1]

                    top_left = 'X' in self.grid[index_row - 1][index_col-1]
                    top_right = 'X' in self.grid[index_row - 1][index_col+1]
                    bottom_left = 'X' in self.grid[index_row + 1][index_col - 1]
                    bottom_right = 'X' in self.grid[index_row + 1][index_col + 1]

                    tile_type = 'o'

                    if all((top, bottom, left, right)):
                        tile_type = 'x'

                    # horizontal
                    if left and not any((top, bottom, right)):
                        tile_type = 'r'
                    if right and not any((top, bottom, left)):
                        tile_type = 'l'
                    if left and right and not any((top, bottom)):
                        tile_type = 'lr'

                    # verticals
                    if top and not any((bottom, left, right)):
                        tile_type = 'b'
                    if bottom and not any((top, left, right)):
                        tile_type = 't'
                    if bottom and top and not any((left, right)):
                        tile_type = 'tb'

                    # corners
                    if left and bottom and not any((top, right)):
                        tile_type = 'tr'
                    if right and bottom and not any((left, top)):
                        tile_type = 'tl'
                    if left and top and not any((bottom, right)):
                        tile_type = 'br'
                    if right and top and not any((left, bottom)):
                        tile_type = 'bl'

                    # T shapes
                    if all((top, bottom, right)) and not left:
                        tile_type = 'tbr'
                    if all((top, bottom, left)) and not right:
                        tile_type = 'tbl'
                    if all((top, left, right)) and not bottom:
                        tile_type = 'lrb'
                    if all((left, bottom, right)) and not top:
                        tile_type = 'lrt'

                    # other
                    if all((top, left, right)) and (top_left or top_right) and not bottom:
                        tile_type = 'bm'
                    if all((bottom, left, right)) and (bottom_right or bottom_left) and not top:
                        tile_type = 'tm'
                    if all((left, top, bottom)) and (bottom_left or top_left) and not right:
                        tile_type = 'rm'
                    if all((right, top, bottom)) and (bottom_right or top_right) and not left:
                        tile_type = 'lm'

                    SoilTile(
                        pos=(index_col * tile_size, index_row * tile_size),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites])
