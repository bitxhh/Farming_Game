from os import walk
import pygame


def import_folder(path):
    surface_dict = {}

    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            name = int(image.split('.')[0])
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[name] = image_surf

    mykeys = sorted(list(surface_dict.keys()))
    sorted_folder = {i: surface_dict[i] for i in mykeys}
    return list(sorted_folder.values())


def import_folder_dict(path):
    surface_dict = {}
    for _, _, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[image.split('.')[0]] = image_surf
    return surface_dict
