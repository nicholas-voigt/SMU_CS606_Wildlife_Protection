# MAIN GAME LOOP
# Call this script to start the simulator
# Eventhandling

import pygame
from simulator.agents import Drone, Animal, Poacher
from simulator.settings import WIDTH, HEIGHT, FPS, drones_to_deploy, poachers_to_deploy, animals_to_deploy


def run():
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Create agents
    drones = drones_to_deploy
    animals = poachers_to_deploy
    poachers = animals_to_deploy

    all_sprites = pygame.sprite.Group(drones + animals + poachers)
    
    # Handle agents in separate groups for easier access
    # if any of these alive groups is empty, the game is over TODO: Implement game over
    alive_animal_sprites = pygame.sprite.Group(animals)
    alive_poacher_sprites = pygame.sprite.Group(poachers)
    
    # Handle drone search globally since drones can communicate
    detected_animal_sprites = pygame.sprite.Group()
    detected_poacher_sprites = pygame.sprite.Group()
    
    # Define custom events for communication between agents
    # Poacher Events:
    # 1. Poacher has detected an animal
    POACHER_DETECT_ANIMAL = pygame.USEREVENT + 1
    # 2. Poacher has killed an animal
    POACHER_KILL_ANIMAL = pygame.USEREVENT + 2
    
    # Drone Events:
    # 1. Drone has detected a poacher
    DRONE_DETECT_POACHER = pygame.USEREVENT + 3
    # 2. Drone has detected an animal
    DRONE_DETECT_ANIMAL = pygame.USEREVENT + 4
    # 3. Drone has lost track of poacher
    DRONE_LOST_POACHER = pygame.USEREVENT + 5
    # 4. Drone has lost track of animal
    DRONE_LOST_ANIMAL = pygame.USEREVENT + 6
    

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


if __name__ == '__main__':
    run()