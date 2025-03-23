import pygame
import random
from simulator.optimizer import DroneOptimizer
from simulator.states import DroneHighAltitude, DroneLowAltitude

class PSOOptimizer(DroneOptimizer):
    """Particle Swarm Optimization for drone control"""
    
    def __init__(self, particles_per_drone=20, w=0.5, c1=1.5, c2=1.5):
        self.particles_per_drone = particles_per_drone
        self.w = w  # Inertia weight
        self.c1 = c1  # Cognitive parameter
        self.c2 = c2  # Social parameter
        self.particles = {}  # {drone_id: [particles]}
        self.best_positions = {}  # {drone_id: best_position}
        self.global_best = {}  # {drone_id: global_best}
        
    def initialize_particles(self, drone):
        """Initialize particles for a drone if not already initialized"""
        if drone.name not in self.particles:
            self.particles[drone.name] = []
            for _ in range(self.particles_per_drone):
                # Random position in the game area
                particle = {
                    'position': pygame.Vector2(random.uniform(0, 800), random.uniform(0, 600)),
                    'velocity': pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)),
                    'fitness': 0
                }
                self.particles[drone.name].append(particle)
            
            # Initialize best positions
            self.best_positions[drone.name] = self.particles[drone.name][0]['position'].copy()
            self.global_best[drone.name] = self.particles[drone.name][0]['position'].copy()
    
    def calculate_fitness(self, position, detected_poachers, detected_animals):
        """Calculate fitness of a position based on distance to poachers/animals"""
        fitness = 0
        
        # Prioritize poachers
        for poacher in detected_poachers:
            distance = position.distance_to(poacher.position)
            fitness += 100 / (distance + 1)  # Higher fitness for closer poachers
            
        # Secondary priority: animals (for monitoring)
        for animal in detected_animals:
            distance = position.distance_to(animal.position)
            fitness += 50 / (distance + 1)
            
        return fitness
    
    def optimize(self, drones, detected_animals, detected_poachers):
        drone_actions = {}
        
        for drone in drones:
            self.initialize_particles(drone)
            
            # Update particles
            for particle in self.particles[drone.name]:
                # Calculate fitness
                particle['fitness'] = self.calculate_fitness(
                    particle['position'], detected_poachers, detected_animals)
                
                # Update personal best
                current_best_fitness = self.calculate_fitness(
                    self.best_positions[drone.name], detected_poachers, detected_animals)
                
                if particle['fitness'] > current_best_fitness:
                    self.best_positions[drone.name] = particle['position'].copy()
                
                # Update global best
                global_best_fitness = self.calculate_fitness(
                    self.global_best[drone.name], detected_poachers, detected_animals)
                
                if particle['fitness'] > global_best_fitness:
                    self.global_best[drone.name] = particle['position'].copy()
                
                # Update velocity and position
                r1, r2 = random.random(), random.random()
                cognitive = self.c1 * r1 * (self.best_positions[drone.name] - particle['position'])
                social = self.c2 * r2 * (self.global_best[drone.name] - particle['position'])
                
                particle['velocity'] = (self.w * particle['velocity'] + cognitive + social)
                # Limit velocity
                if particle['velocity'].length() > 5:
                    particle['velocity'].scale_to_length(5)
                    
                particle['position'] += particle['velocity']
                
                # Keep within bounds
                particle['position'].x = max(0, min(800, particle['position'].x))
                particle['position'].y = max(0, min(600, particle['position'].y))
            
            # Determine drone actions based on global best
            direction = (self.global_best[drone.name] - drone.position).normalize() if (
                self.global_best[drone.name] - drone.position).length() > 0 else pygame.Vector2(0, 0)
            
            # Determine state based on detected entities
            new_state = None
            if detected_poachers:
                # If poachers detected, go to low altitude for better tracking
                if not isinstance(drone.active_state, DroneLowAltitude):
                    new_state = DroneLowAltitude()
            elif not detected_animals and not detected_poachers:
                # If nothing detected, go to high altitude for wider search
                if not isinstance(drone.active_state, DroneHighAltitude):
                    new_state = DroneHighAltitude()
                    
            # Add drone actions to return dictionary
            drone_actions[drone] = {
                'state': new_state,
                'direction': direction,
                'speed_modifier': 1.0
            }
                
        return drone_actions