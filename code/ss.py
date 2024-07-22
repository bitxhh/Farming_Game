import pygame
from settings import *
from support import *
from timer import Timer
# from debug import debug


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer, toggle_shop):
        super().__init__(group)

        # import assets (animation)
        self.target_pos = (0, 0)
        self.animations = {}
        self.import_assets()

        # Первый кадр анимации
        self.status = 'down_idle'
        self.frame_index = 0

        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)

        self.z = LAYERS['main']

        # Атрибуты для передвижения
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)

        self.hitbox = self.rect.copy().inflate((-146, -140))
        self.collision_sprites = collision_sprites

        # timer
        self.timers = {
            'tool use': Timer(350, self.use_tool),
            'tool switch': Timer(200),
            'seed use': Timer(350, self.seed_use),
            'seed switch': Timer(200)
        }

        # tools
        self.tools = ['axe',
                      'hoe',
                      'water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]

        # семена
        self.seeds = ['corn',
                      'tomato']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]
        self.tree_sprites = tree_sprites
        self.interaction = interaction
        self.sleep = False
        self.soil_layer = soil_layer

        # inventory
        self.item_inventory = {
            'tomato': 0,
            'corn': 0,
            'wood': 0,
            'apple': 0}

        self.seed_inventory = {
            'corn': 5,
            'tomato': 5}
        self.money = 200
        self.toggle_shop = toggle_shop
        self.watering = pygame.mixer.Sound('audio/water.mp3')
        self.watering.set_volume(0.2)

    def use_tool(self):
        if self.selected_tool == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos[0], self.target_pos[1]):
                    tree.damage()

        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)
            self.watering.play()

    def get_target_pos(self):
        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

    def seed_use(self):
        if self.seed_inventory[self.selected_seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed, self.seed_inventory)

    def import_assets(self):
        self.animations = {'up': [], 'down': [], 'left': [], 'right': [],
                           'right_idle': [], 'left_idle': [], 'up_idle': [], 'down_idle': [],
                           'right_hoe': [], 'left_hoe': [], 'up_hoe': [], 'down_hoe': [],
                           'right_axe': [], 'left_axe': [], 'up_axe': [], 'down_axe': [],
                           'right_water': [], 'left_water': [], 'up_water': [], 'down_water': []}
        for animation in self.animations.keys():
            full_path = 'graphics/character/' + animation
            self.animations[animation] = import_folder_dict(full_path)

    def animate(self, dt):
        self.frame_index += 4 * dt * 2
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]

    def input(self):
        keys = pygame.key.get_pressed()

        if not self.timers['tool use'].active and not self.sleep:
            # direction
            if keys[pygame.K_a]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_d]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            if keys[pygame.K_w]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_s]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            # tool
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0

            if keys[pygame.K_q] and not self.timers['tool switch'].active:
                self.timers['tool switch'].activate()
                self.tool_index += 1
                self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
                self.selected_tool = self.tools[self.tool_index]

            # seeds
            if keys[pygame.K_LCTRL]:
                self.timers['seed use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0

            if keys[pygame.K_e] and not self.timers['seed switch'].active:
                self.timers['seed switch'].activate()
                self.seed_index += 1
                self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
                self.selected_seed = self.seeds[self.seed_index]

            if keys[pygame.K_RETURN]:
                collided_interaction_sprites = pygame.sprite.spritecollide(self, self.interaction, False)
                if collided_interaction_sprites:
                    if collided_interaction_sprites[0].name == 'Trader':
                        self.toggle_shop()
                    else:
                        self.status = 'left_idle'
                        self.sleep = True

    def get_status(self):
        # idle
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        # tool
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0:
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0:
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y > 0:
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0:
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery

    def move(self, dt):
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # horizontal movement
        self.pos.x += self.direction.x * player_speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * player_speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    def update(self, dt):
        self.input()
        self.get_status()
        self.update_timers()
        self.get_target_pos()
        self.move(dt)
        self.animate(dt)
