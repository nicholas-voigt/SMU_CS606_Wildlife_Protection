# MAIN GAME LOOP
# Call this script to start the simulator
# Eventhandling

import pygame
from events import POACHER_KILLED_ANIMAL, DRONE_DETECTED_POACHER, DRONE_CAUGHT_POACHER, DRONE_DETECTED_ANIMAL, DRONE_LOST_POACHER, DRONE_LOST_ANIMAL
from agents import Drone, Animal, Poacher
from states import Terminal
from settings import WIDTH, HEIGHT, FPS


# Main game loop
def run():
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Create agents
    drones = []
    animals = [Animal('elephant', 400, 300), Animal('giraffe', 420, 320)]
    poachers = [Poacher('bad boy', 600, 400)]

    # drones = [Drone('good boy', 100, 100)]
    # animals = [Animal('elephant', 400, 300), Animal(420, 320)]
    # poachers = [Poacher('bad boy', 600, 400)]


    all_sprites = pygame.sprite.Group(drones + animals + poachers)
    
    # Handle agents in separate groups for easier access
    # if any of these alive groups is empty, the game is over
    alive_animal_sprites = pygame.sprite.Group(animals)
    alive_poacher_sprites = pygame.sprite.Group(poachers)
    drones_sprites = pygame.sprite.Group(drones)
    
    # Handle drone search globally since drones can communicate
    detected_animal_sprites = pygame.sprite.Group()
    detected_poacher_sprites = pygame.sprite.Group()
    

    # Main loop
    running = True
    while running:
        clock.tick(FPS)
        screen.fill((30, 30, 30))  # Background color

        # Event handling
        for event in pygame.event.get():

            # Pygame quit event
            if event.type == pygame.QUIT:
                running = False
            
            # animal killed by poacher
            if event.type == POACHER_KILLED_ANIMAL:
                animal = event.animal
                animal.set_state(Terminal)
                alive_animal_sprites.remove(animal)
                if len(alive_animal_sprites) == 0:
                    print("Game Over! Poachers have killed all animals")
                    running = False
            
            # poacher caught by drone
            if event.type == DRONE_CAUGHT_POACHER:
                poacher = event.poacher
                poacher.set_state(Terminal)
                alive_poacher_sprites.remove(poacher)
                if len(alive_poacher_sprites) == 0:
                    print("Congratulations! All poachers have been caught")
                    running = False
            
            # animal detected by drone
            if event.type == DRONE_DETECTED_ANIMAL:
                animal = event.animal
                detected_animal_sprites.add(animal)

            # poacher detected by drone
            if event.type == DRONE_DETECTED_POACHER:
                poacher = event.poacher
                detected_poacher_sprites.add(poacher)
            
            # drone lost track of poacher
            if event.type == DRONE_LOST_POACHER:
                poacher = event.poacher
                detected_poacher_sprites.remove(poacher)
            
            # drone lost track of animal
            if event.type == DRONE_LOST_ANIMAL:
                animal = event.animal
                detected_animal_sprites.remove(animal)
        
        # Update animals
        for animal in alive_animal_sprites:

            # Scan surroundings for poachers
            detected_agent = animal.scan_surroundings(agents=alive_poacher_sprites, mode='nearest')

            # Update threat
            animal.threat = detected_agent[2] if detected_agent else None
            
            # Check state transitions
            state = animal.active_state.check_transition()
            if state:
                animal.set_state(state)
            
            # Perform the action of the current state
            animal.active_state.action()

        # Update poachers
        for poacher in alive_poacher_sprites:

            # If poacher has no target, search animals
            if not poacher.target:

                # Scan surroundings for the closest animal
                detected_agent = poacher.scan_surroundings(agents=alive_animal_sprites, mode='nearest')

                # Update target
                poacher.target = detected_agent[2] if detected_agent else None

            # Check state transitions
            state = poacher.active_state.check_transition()
            if state:
                poacher.set_state(state)

            # Perform the action of the current state
            poacher.active_state.action()

        for drone in drones_sprites:
            # Scan surroundings for poachers and animals
            # TODO: How do I implement state check here?
            drone.update()

        # Draw agents
        all_sprites.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    run()