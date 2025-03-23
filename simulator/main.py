# MAIN GAME LOOP
# Call this script to start the simulator
# Eventhandling

import sys
import pygame

from settings import WIDTH, GAME_WIDTH, PANEL_WIDTH, HEIGHT, FPS
from game_env import render_info_panel
from events import POACHER_KILLED_ANIMAL, DRONE_DETECTED_POACHER, DRONE_CAUGHT_POACHER, DRONE_DETECTED_ANIMAL, DRONE_LOST_POACHER, DRONE_LOST_ANIMAL
from agents import Drone, Animal, Poacher
from states import Terminal, DroneHighAltitude, DroneLowAltitude
from pso_optimizer import PSOOptimizer
from rl_optimizer import RLOptimizer


# Main game loop
def run(optimizer_type='pso'):
    
    # Pygame setup
    # Initialize pygame
    pygame.init()
    # Set up the display
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wildlife Protection Simulator") 
    clock = pygame.time.Clock()
    # Create rectangles for game area and panel
    game_rect = pygame.Rect(0, 0, GAME_WIDTH, HEIGHT)
    panel_rect = pygame.Rect(GAME_WIDTH, 0, PANEL_WIDTH, HEIGHT)
    # Initialize fonts
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 16)
    title_font = pygame.font.SysFont('Arial', 20, bold=True)

    
    # Select optimizer based on type
    if optimizer_type.lower() == "pso":
        optimizer = PSOOptimizer()
    elif optimizer_type.lower() == "rl":
        optimizer = RLOptimizer()
    else:
        raise ValueError(f"Unknown optimizer type: {optimizer_type}")

    # Create agents
    drones = []
    animals = [Animal('elephant', 400, 300), Animal('giraffe', 420, 320)]
    poachers = [Poacher('bad boy', 600, 400)]

    # drones = [Drone('good boy', 100, 100)]
    # animals = [Animal('elephant', 400, 300), Animal(420, 320)]
    # poachers = [Poacher('bad boy', 600, 400)]


    all_sprites = pygame.sprite.Group(drones + animals + poachers)
    
    # Handle agents in separate groups for easier access
    animals_sprites = pygame.sprite.Group(animals)
    poachers_sprites = pygame.sprite.Group(poachers)
    drones_sprites = pygame.sprite.Group(drones)

    # Track alive agents seperately,
    # if any of these alive groups is empty, the game is over
    alive_animal_sprites = pygame.sprite.Group(animals)
    alive_poacher_sprites = pygame.sprite.Group(poachers)
    
    # Handle drone search globally since drones can communicate
    detected_animal_sprites = pygame.sprite.Group()
    detected_poacher_sprites = pygame.sprite.Group()
    

    # Main loop
    running = True
    while running:

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

        # Update drones
        # empty the global list of detected agents first and then rebuild
        detected_animal_sprites.empty()
        detected_poacher_sprites.empty()
        for drone in drones_sprites:
            # Scan surroundings for animals
            detected_agents = drone.scan_surroundings(agents=animals_sprites, mode='all')
                
            # Add detected animals to the global list
            for (_, _, agent) in detected_agents:
                detected_animal_sprites.add(agent)
            
            # If drone state is Low Altitude, also check for poachers
            if isinstance(drone.active_state, DroneLowAltitude):
                # Scan surroundings for poachers
                detected_agents = drone.scan_surroundings(agents=poachers_sprites, mode='all')
                
                # Add detected poachers to the global list
                for (_, _, agent) in detected_agents:
                    detected_poacher_sprites.add(agent)
        
        # Get drone actions from optimizer
        drone_actions = optimizer.optimize(drones_sprites, detected_animal_sprites, detected_poacher_sprites)
        
        # Apply drone actions
        for drone, action in drone_actions.items():
            # Update drone state if needed
            if action['state']:
                drone.set_state(action['state'])
            
            # Move drone in the specified direction with specified speed
            drone.move(action['direction'], action['speed_modifier'] * drone.base_speed)
            
            # You can also invoke other drone actions here based on the optimizer's output
            

        # Update screen
        clock.tick(FPS)
        screen.fill((30, 30, 30))  # Fill the entire screen with background color
        
        # Draw all sprites (they will only be visible in the game area)
        all_sprites.draw(screen)
        
        # Render information panel
        render_info_panel(screen, drones_sprites, alive_animal_sprites, 
                         alive_poacher_sprites, panel_rect, font, title_font)
        
        pygame.display.flip()
        
    pygame.quit()


if __name__ == '__main__':
    # Default to PSO if no argument provided
    optimizer_type = sys.argv[1] if len(sys.argv) > 1 else "pso"
    run(optimizer_type)