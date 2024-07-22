import pygame.mixer

from settings import *
from random import randint, choice


class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surface, group, z=LAYERS['main']):
        super().__init__(group)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.z = z
        self.hitbox = self.rect.inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)


class Interaction(Generic):
    def __init__(self, pos, size, group, name):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, group)
        self.name = name


class Water(Generic):
    def __init__(self, pos, frames, group):

        self.frames = frames
        self.frame_index = 0

        super().__init__(
            pos=pos,
            surface=self.frames[self.frame_index],
            group=group,
            z=LAYERS['water'])

    def animate(self, dt):
        self.frame_index += 5 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


class WildFlower(Generic):
    def __init__(self, pos, surf, group):
        super().__init__(pos, surf, group)
        self.hitbox = self.rect.copy().inflate((-20, -self.rect.height * 0.9))


class Particle(Generic):
    def __init__(self, pos, surf, group, z, duration=200):
        super().__init__(pos, surf, group, z)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        if current_time - self.start_time > self.duration:
            self.kill()

        # masks
        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0, 0, 0))
        self.image = new_surf


class Tree(Generic):
    def __init__(self, pos, surf, group, name, player_add):
        super().__init__(pos, surf, group)

        self.health = 9
        self.alive = True
        stump_path = f'graphics/stumps/{"small" if name == "Small" else "large"}.png'
        self.stump_surface = pygame.image.load(stump_path).convert_alpha()

        self.apple_surf = pygame.image.load('graphics/fruit/apple.png')
        self.apple_pos = APPLE_POS[name]
        self.apple_group = pygame.sprite.Group()
        self.create_fruit()
        self.player_add = player_add
        self.axe_sound = pygame.mixer.Sound('audio/axe.mp3')
        self.critical_damage = 3

    def damage(self):
        self.health -= 1
        print(self.health)
        self.axe_sound.play()

        if (len(self.apple_group.sprites())) > 0:
            random_apple = choice(self.apple_group.sprites())
            Particle(pos=random_apple.rect.topleft,
                     surf=random_apple.image,
                     group=self.groups()[0],
                     z=LAYERS['fruit'])
            self.player_add('apple')
            print('яблоку пиздец')
            random_apple.kill()

    def check_status(self):
        if self.health == self.critical_damage:
            Particle(pos=self.rect.topleft,
                     surf=self.image,
                     group=self.groups()[0],
                     z=LAYERS['fruit'],
                     duration=500)
            self.player_add('wood')
            self.image = self.stump_surface
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)
            self.critical_damage += 1
        if self.health == 0:
            Particle(pos=self.rect.topleft,
                     surf=self.image,
                     group=self.groups()[0],
                     z=LAYERS['fruit'],
                     duration=500)
            self.player_add('wood')
            self.alive = False
            self.kill()

    def update(self, dt):
        if self.alive:
            self.check_status()

    def create_fruit(self):
        for pos in self.apple_pos:
            if randint(0, 10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Generic((x, y), self.apple_surf, [self.apple_group, self.groups()[0]], LAYERS['fruit'])

