# MAIN GAME LOOP
# Call this script to start the simulator
# Eventhandling

import sys
import pygame
from collections import deque
import pickle

from settings import WIDTH, GAME_WIDTH, PANEL_WIDTH, HEIGHT, FPS
from game_env import render_info_panel, end_simulation
from events import POACHER_ATTACK_ANIMAL, ANIMAL_KILLED, DRONE_DETECTED_POACHER, DRONE_CAUGHT_POACHER, DRONE_DETECTED_ANIMAL, DRONE_LOST_POACHER, DRONE_LOST_ANIMAL
from agents import Drone, Animal, Poacher
from states import Terminal, DroneFastSearch, DroneDeepSearch
from pso_optimizer import PSOOptimizer
from rl_optimizer import RLOptimizer


# Main game loop
def run(optimizer=None, headless=False):
    """Main function to run the simulation"""
    
    # Pygame setup if headless without display
    if not headless:
        # Initialize pygame
        pygame.init()
        # Set up the display
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Wildlife Protection Simulator")
        # Set up the clock for controlling frame rate
        clock = pygame.time.Clock()
        # Create rectangle for panel
        panel_rect = pygame.Rect(GAME_WIDTH, 0, PANEL_WIDTH, HEIGHT)
        # Create a transparent surface to visualize the scan range of agents
        transparent_surface = pygame.Surface((GAME_WIDTH, HEIGHT), pygame.SRCALPHA)
        # Initialize fonts
        pygame.font.init()
    else:
        # Initialize pygame without display
        pygame.init()
        screen = pygame.Surface((WIDTH, HEIGHT))

    
    # Load default optimizer if none is provided
    if optimizer is None:
        optimizer = PSOOptimizer()
    # Check if provided optimizer is correct instance
    elif isinstance(optimizer, PSOOptimizer) or isinstance(optimizer, RLOptimizer):
        pass
    else:
        raise ValueError(f"Unknown optimizer: {optimizer}")
    
    # Track simulation progress
    simulation_steps = 0
    outcome = None
    
    # Event log for displaying recent events (max 15 events)
    event_log = deque(maxlen=15)
    event_log.append(("Simulation started", pygame.time.get_ticks()))

    # Create agents
    drones = [Drone('good boy1', 100, 100), Drone('good boy2', 700, 100), Drone('good boy3', 100, 400)]
    animals = [Animal('elephant1', 400, 300), Animal('elephant2', 410, 300), Animal('elephant3', 400, 310), Animal('elephant4', 410, 310), 
               Animal('giraffe1', 700, 300), Animal('giraffe2', 710, 300), Animal('giraffe3', 700, 300), Animal('giraffe4', 710, 310)]
    poachers = [Poacher('bad boy1', 400, 500), Poacher('bad boy2', 650, 500)]

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
        simulation_steps += 1
        
        # Early termination to prevent hanging
        if simulation_steps > 2000:
            outcome = "timeout"
            running = False

        # Event handling
        for event in pygame.event.get():

            # Pygame quit event
            if event.type == pygame.QUIT:
                running = False
                break
            
            # animal attacked by poacher
            if event.type == POACHER_ATTACK_ANIMAL:
                animal = event.dict['animal']
                poacher = event.dict['poacher']
                
                # Reduce animal health
                animal.health -= poacher.attack_damage
                
                # if animal is dead, post animal killed event
                if animal.health <= 0:
                    pygame.event.post(pygame.event.Event(ANIMAL_KILLED, animal=animal, poacher=poacher))
            
            # animal killed event
            if event.type == ANIMAL_KILLED:
                animal = event.dict['animal']
                poacher = event.dict['poacher']
                
                # Set animal to terminal state & remove from alive sprites
                animal.set_state(Terminal())
                alive_animal_sprites.remove(animal)
                
                # Delete target from poacher
                poacher.target = None
                
                # Log the event
                event_log.append((f"Poacher {poacher.name} killed {animal.name}", pygame.time.get_ticks()))
                
                # Check if all animals are dead to end the game
                if len(alive_animal_sprites) == 0:
                    outcome = "defeat"
                    if not headless:
                        end_simulation(screen, "Defeat", {"poachers": 1 - len(alive_poacher_sprites) / len(poachers_sprites), "animals": len(alive_animal_sprites) / len(animals_sprites)})
                    running = False
                    continue  # Skip the rest of the loop since the game is over
                
            # poacher caught by drone
            if event.type == DRONE_CAUGHT_POACHER:
                poacher = event.dict['poacher']
                
                # Set poacher to terminal state & remove from alive sprites
                poacher.set_state(Terminal())
                alive_poacher_sprites.remove(poacher)
                
                # Log the event
                event_log.append((f"Drone caught poacher {poacher.name}", pygame.time.get_ticks()))
                
                # End simulation if all poachers are caught
                if len(alive_poacher_sprites) == 0:
                    outcome = "victory"
                    if not headless:
                        end_simulation(screen, "Victory", {"poachers": 1 - len(alive_poacher_sprites) / len(poachers_sprites), "animals": len(alive_animal_sprites) / len(animals_sprites)})
                    running = False
                    continue  # Skip the rest of the loop since the game is over
                
        # Update animals
        for animal in alive_animal_sprites:

            # Scan surroundings for poachers
            detected_poacher = animal.scan_surroundings(agents=alive_poacher_sprites, mode='nearest')

            # Update threat
            animal.threat = detected_poacher[2] if detected_poacher else None
            
            # Update my current herd
            animal.herd = [a[2] for a in animal.scan_surroundings(agents=alive_animal_sprites, mode='all')]
            
            # Check state transitions
            state = animal.active_state.check_transition()
            if state:
                animal.set_state(state)
                event_log.append((f"{animal.name} changed state to {state.__class__.__name__}", pygame.time.get_ticks()))
            
            # Perform the action of the current state
            animal.active_state.action()

        # Update poachers
        for poacher in alive_poacher_sprites:
            
            # Scan surroundings for the closest animal
            detected_agents = poacher.scan_surroundings(agents=alive_animal_sprites, mode='all')

            if detected_agents:
                # Update target if one is found and there is no current target
                target = detected_agents.pop()[2]
                poacher.target = target if poacher.target is None else poacher.target
                
                # Update memory of animal sightings with the closest animals
                temp_agents = sorted(detected_agents, key=lambda x: x[0], reverse=True) # Sort by distance
                for _, _, agent in temp_agents:
                    new_memory = ('animal', agent.position)
                    poacher.memory.appendleft(new_memory)
            
            else:
                poacher.target = None
            
            # Check state transitions
            state = poacher.active_state.check_transition()
            if state:
                poacher.set_state(state)
                event_log.append((f"{poacher.name} changed state to {state.__class__.__name__}", pygame.time.get_ticks()))

            # Perform the action of the current state
            poacher.active_state.action()

        # Update drones
        # 1. Update current sightings of animals and poachers
        detected_animal_sprites.empty()
        detected_poacher_sprites.empty()
        
        for drone in drones_sprites:
            # Scan surroundings for animals & add to detected
            detected_agents = drone.scan_surroundings(agents=animals_sprites, mode='all')
            for (_, _, agent) in detected_agents:
                detected_animal_sprites.add(agent)
            
            # If drone state is Low Altitude, also check for poachers & add to detected
            if isinstance(drone.active_state, DroneDeepSearch):
                detected_agents = drone.scan_surroundings(agents=alive_poacher_sprites, mode='all')
                for (_, _, agent) in detected_agents:
                    detected_poacher_sprites.add(agent)
            
        # 2. Push current state to optimizer and get drone actions
        drone_actions = optimizer.optimize(drones_sprites, detected_animal_sprites, detected_poacher_sprites)
        
        # Apply drone actions
        for drone, action in drone_actions.items():
            # Update drone state if needed
            if action['state']:
                drone.set_state(action['state'])
                event_log.append((f"{drone.name} changed state to {action['state'].__class__.__name__}", pygame.time.get_ticks()))
            
            # Set closest poacher as target to catch
            poacher = drone.scan_surroundings(agents=detected_poacher_sprites, mode='nearest')
            drone.target = poacher[2] if poacher else None
            
            # Perform state action with given parameters
            drone.active_state.action(action['direction'], action['speed_modifier'])

            
        # Update screen
        if not headless:
            clock.tick(FPS)
            screen.fill((30, 30, 30))  # Fill the entire screen with background color
            
            # Draw the game area
            # Clear the transparent surface
            transparent_surface.fill((0, 0, 0, 0))  # Completely transparent
        
            # Draw scan ranges for each agent type
            for agent in all_sprites:
                # Draw a circle on the transparent surface
                pygame.draw.circle(
                    surface=transparent_surface,
                    color=(*agent.image.get_at((5, 5))[:3], 50),  # Get agent color with 50 alpha
                    center=(int(agent.position.x), int(agent.position.y)),
                    radius=agent.scan_range * agent.active_state.scan_range_modifier,  # Scan range
                    width=1  # Line width
                )

            # Draw the game elements
            all_sprites.draw(screen)

            # Blit the transparent surface on top
            screen.blit(transparent_surface, (0, 0))
            
            # Render information panel
            render_info_panel(screen, drones_sprites, alive_animal_sprites, 
                            alive_poacher_sprites, event_log, panel_rect)
        
            pygame.display.flip()
    
    # Close pygame if not headless
    if not headless:
        pygame.quit()
        
    # return simulation results for analysis
    return {
        'outcome': outcome,
        'steps': simulation_steps,
        'poachers_caught_pct': 1 - len(alive_poacher_sprites) / len(poachers_sprites),
        'animals_alive_pct': len(alive_animal_sprites) / len(animals_sprites)
    }


def train_optimizer(num_runs=50, optimizer_type='rl', model_filename='rl_model.pkl'):
    """Run multiple simulations to train & evaluate the optimizers"""
    # Statistics tracking
    stats = {
        'results': [],
        'poachers_caught_pct': [],
        'animals_alive_pct': [],
        'steps_per_run': [],
        'victories': 0,
        'defeats': 0,
        'timeouts': 0
    }
    
    if optimizer_type == 'rl':
        # Load RL optimizer
        optimizer = RLOptimizer()
    elif optimizer_type == 'pso':
        # Load PSO optimizer
        optimizer = PSOOptimizer()
        
    for run_num in range(1, num_runs+1):
        print(f"\n--- Starting Run {run_num}/{num_runs} ---")
        
        # load model if optimizer is RL and model exists
        if optimizer_type == 'rl':
            optimizer.load_model(model_filename)
        
        # Track current run performance 
        result = run(optimizer, headless=True)
        
        # Update statistics
        stats['results'].append(result['outcome'])
        stats['poachers_caught_pct'].append(result['poachers_caught_pct'])
        stats['animals_alive_pct'].append(result['animals_alive_pct'])
        stats['steps_per_run'].append(result['steps'])
        
        if optimizer_type == 'rl':
            optimizer.save_model(model_filename)
        
        # Print statistics so far
        print(f"Run {run_num} complete - {result['outcome']} in {result['steps']} steps")
        
    # Calculate final statistics
    stats['victories'] = stats['results'].count('victory')
    stats['defeats'] = stats['results'].count('defeat')
    stats['timeouts'] = stats['results'].count('timeout')
    
    # Print final statistics
    print("\n=== Training Complete ===")
    print(f"Total runs: {num_runs}")
    print(f"Victories: {stats['victories']} ({stats['victories']/num_runs*100:.1f}%)")
    print(f"Defeats: {stats['defeats']} ({stats['defeats']/num_runs*100:.1f}%)")
    print(f"Timeouts: {stats['timeouts']} ({stats['timeouts']/num_runs*100:.1f}%)")
    print(f"Average poachers caught: {sum(stats['poachers_caught_pct'])/len(stats['poachers_caught_pct']):.1f}%")
    print(f"Average animals surviving: {sum(stats['animals_alive_pct'])/len(stats['animals_alive_pct']):.1f}%")
    print(f"Average steps per run: {sum(stats['steps_per_run'])/len(stats['steps_per_run']):.1f}")
    
    # Save statistics to file
    with open('training_stats.pkl', 'wb') as stats_file:
        pickle.dump(stats, stats_file)
    
    return


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "train":
            type = sys.argv[2].lower() if len(sys.argv) > 2 else 'rl'
            num_runs = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            train_optimizer(num_runs=num_runs, optimizer_type=type)
        elif sys.argv[1].lower() in ["pso", "rl"]:
            # Regular single-run mode
            if sys.argv[1].lower() == "pso":
                print("Running with PSO optimizer")
                optimizer = PSOOptimizer()
            else:
                print("Running with RL optimizer")
                optimizer = RLOptimizer()
                optimizer.load_model('rl_model.pkl')
            run(optimizer)
        else:
            print("Usage: python main.py [train] [num_runs] [pso|rl]")
    else:
        # Default to PSO
        run()