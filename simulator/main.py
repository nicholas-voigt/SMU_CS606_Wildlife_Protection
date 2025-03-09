# MAIN GAME LOOP: HANDLES RENDERING, UPDATING AND INPUT

import pygame
from simulator.agents import Drone, Animal, Poacher
from simulator.settings import WIDTH, HEIGHT, FPS

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Create agents
drones = [Drone(100, 100)]
animals = [Animal(400, 300), Animal(420, 320)]
poachers = [Poacher(600, 400)]

all_sprites = pygame.sprite.Group(drones + animals + poachers)

# Main loop
running = True
while running:
    clock.tick(FPS)
    screen.fill((30, 30, 30))  # Background color

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update agents
    for drone in drones:
        drone.search()
    for animal in animals:
        animal.flee(poachers[0].position)
    for poacher in poachers:
        poacher.hunt(animals)

    # Draw agents
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()
