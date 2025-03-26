import pygame
import random
from optimizer import DroneOptimizer
from states import DroneHighAltitude, DroneLowAltitude

class PSOOptimizer(DroneOptimizer):
    """Particle Swarm Optimization for drone control"""
    
    def __init__(self, particles_per_drone=20, w=0.6, c1=1.5, c2=1.5):
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
                    'fitness': 0,
                    'last_position': None,
                    'stagnation_count': 0 
                }
                self.particles[drone.name].append(particle)
            
            # Initialize best positions
            self.best_positions[drone.name] = self.particles[drone.name][0]['position'].copy()
            self.global_best[drone.name] = self.particles[drone.name][0]['position'].copy()
    
    def calculate_fitness(self, position, detected_poachers, detected_animals,stagnation_count):
        fitness = 0
        
        # If we're in high altitude, prioritize searching for poachers
        if isinstance(self.current_drone.active_state, DroneHighAltitude):
            # Base fitness for being in high altitude
            fitness += 30
            
            """If we have detected animals, incentivize searching around their radius.
            But it also needs to search outside but close to the radius
            because a poacher might be hiding outside the radius"""
            # If we have detected animals, incentivize searching around their radius
            for animal in detected_animals:
                distance_to_animal = position.distance_to(animal.position)
                # Higher fitness for positions just outside the animal's radius
                # optimal_distance = animal.scan_range * 1.2  # 20% outside radius
                optimal_distance = random.uniform(animal.scan_range, animal.scan_range * 1.2)

                distance_diff = abs(distance_to_animal - optimal_distance)
                fitness += 100 / (distance_diff + 1)

                if stagnation_count > 15:
                    fitness -= 20
                
        # If we're in low altitude, prioritize monitoring detected entities
        else:
            # Prioritize poachers
            for poacher in detected_poachers:
                distance = position.distance_to(poacher.position)
                fitness += 100 / (distance + 1)

                if stagnation_count > 15:
                    fitness -= 20   
            
        return fitness
    
    def optimize(self, drones, detected_animals, detected_poachers):
        drone_actions = {}
        
        for drone in drones:
            self.current_drone = drone  # Store current drone for fitness calculation
            self.initialize_particles(drone)
            

            """For each particle, calculate the fitness.
            If the particle has been in the same position for too long, it will be penalized.
            current_best_fitness is the best fitness of the particle.
            global_best_fitness is the best fitness of the global best position.
            if the particle's fitness is greater than the current best fitness, update the current best fitness.
            if the particle's fitness is greater than the global best fitness, update the global best fitness.
            """
            # Update particles
            for particle in self.particles[drone.name]:
                # Calculate fitness
                particle['fitness'] = self.calculate_fitness(particle['position'], detected_poachers, detected_animals, particle['stagnation_count'])
                
                # Update personal best
                current_best_fitness = self.calculate_fitness(
                    self.best_positions[drone.name], detected_poachers, detected_animals, particle['stagnation_count'])
                
                if particle['fitness'] > current_best_fitness:
                    self.best_positions[drone.name] = particle['position'].copy()
                
                # Update global best
                global_best_fitness = self.calculate_fitness(
                    self.global_best[drone.name], detected_poachers, detected_animals, particle['stagnation_count'])
                
                if particle['fitness'] > global_best_fitness:
                    self.global_best[drone.name] = particle['position'].copy()
                
                """The cognitive parameter influences how much the drone is influenced by its own best position"""
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

                # Track how long the particle has stayed in a similar position
                if particle['last_position'] is not None:
                    if particle['position'].distance_to(particle['last_position']) < 5:
                        particle['stagnation_count'] += 1
                    else:
                        particle['stagnation_count'] = 0
                else:
                    particle['stagnation_count'] = 0  # initialize if not yet set

                # Update last known position
                particle['last_position'] = particle['position'].copy()

            
            # Determine drone actions based on global best
            direction = (self.global_best[drone.name] - drone.position).normalize() if (
                self.global_best[drone.name] - drone.position).length() > 0 else pygame.Vector2(0, 0)
            
            # Determine state based on detected entities
            new_state = None
            if detected_animals:
                # Check if we're within any animal's radius
                within_radius = False
                for animal in detected_animals:
                    if drone.position.distance_to(animal.position) <= drone.scan_range:
                        within_radius = True
                        break
                
                if within_radius:
                    # Only switch to low altitude if we're within an animal's radius
                    if not isinstance(drone.active_state, DroneLowAltitude):
                        new_state = DroneLowAltitude()
                else:
                    # If we detect animals but aren't within radius, stay in high altitude
                    if not isinstance(drone.active_state, DroneHighAltitude):
                        new_state = DroneHighAltitude()
            else:
                # If no animals detected, go to high altitude for wider search
                if not isinstance(drone.active_state, DroneHighAltitude):
                    new_state = DroneHighAltitude()
                    
            # Add drone actions to return dictionary
            drone_actions[drone] = {
                'state': new_state,
                'direction': direction,
                'speed_modifier': 1.0
            }
                
        return drone_actions