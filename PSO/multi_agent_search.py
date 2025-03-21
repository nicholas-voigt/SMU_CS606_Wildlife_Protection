import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from IPython.display import display, HTML

class PSODroneSearch:
    # PSO Parameters
    NUM_PARTICLES = 20  # Number of particles (drones)
    MAX_ITER = 100  # Maximum iterations
    W = 0.5  # Inertia weight
    C1 = 1.5  # Cognitive coefficient
    C2 = 1.5  # Social coefficient

    # Search Area Parameters
    AREA_SIZE = 100
    MAX_SPEED = 5
    MAX_SCAN_RADIUS = 20
    MIN_SCAN_RADIUS = 5

    def __init__(self):
        super().__init__()
        # Initialize target locations with greater separation
        self.animal_location = np.array([np.random.randint(0, self.AREA_SIZE), 
                                       np.random.randint(0, self.AREA_SIZE)], dtype=float)
        
        # Place poacher 10-20 units away from herd in a random direction
        random_angle = np.random.uniform(0, 2 * np.pi)
        random_distance = np.random.uniform(10, 20)
        poacher_offset = np.array([
            random_distance * np.cos(random_angle),
            random_distance * np.sin(random_angle)
        ])
        self.poacher_location = np.clip(
            self.animal_location + poacher_offset,
            0, self.AREA_SIZE
        ).astype(float)
        
        # Initialize Particles (Drones)
        self.particles = np.random.randint(0, self.AREA_SIZE, (self.NUM_PARTICLES, 2))
        self.initial_locations = np.copy(self.particles)
        self.velocities = np.random.uniform(-self.MAX_SPEED, self.MAX_SPEED, 
                                          (self.NUM_PARTICLES, 2))
        self.scan_radii = np.full(self.NUM_PARTICLES, self.MAX_SCAN_RADIUS)

        # Best solutions
        self.personal_best_positions = np.copy(self.particles)
        self.global_best_position = self.personal_best_positions[0]
        self.personal_best_scores = np.full(self.NUM_PARTICLES, np.inf)
        self.global_best_score = np.inf

        # Setting detection to False. When True, Drones will change their velocity and radius, and remember the last known herd location
        self.herd_detected = False
        self.last_known_herd_location = None

        # Adjust movement parameters
        self.herd_speed = 1.0
        self.poacher_speed = 0.7  # Slightly slower than herd
        self.herd_direction = np.random.rand(2) * 2 - 1
        self.poacher_direction = np.random.rand(2) * 2 - 1
        
        # Add minimum distance parameter
        self.min_poacher_distance = 8  # Minimum distance poacher keeps from herd
        self.max_poacher_distance = 25  # Maximum distance before poacher moves closer

        # Initialize animation history
        self.animation_history = {
            'particles': [],
            'animal_loc': [],
            'poacher_loc': []
        }

    def fitness_function(self, particle, scan_radius):
        """
        Fitness function: Lower value is better.
        1. Time to find an animal (distance to animal)
        2. Time to find a poacher after animal is detected
        """
        distance_to_animal = np.linalg.norm(particle - self.animal_location)
        if distance_to_animal <= scan_radius:
            distance_to_poacher = np.linalg.norm(particle - self.poacher_location)
            return distance_to_poacher  # Prioritize finding the poacher
        return distance_to_animal  # Prioritize detecting the animal first

    def update_target_positions(self):
        """Update positions of animal herd and poacher with distance constraints"""
        # Random direction changes for herd
        if np.random.rand() < 0.1:  # 10% chance to change direction
            self.herd_direction = np.random.rand(2) * 2 - 1
            self.herd_direction = self.herd_direction / np.linalg.norm(self.herd_direction)
        
        # Update herd position
        self.animal_location += self.herd_direction * self.herd_speed
        self.animal_location = np.clip(self.animal_location, 0, self.AREA_SIZE)
        
        # Calculate current distance between poacher and herd
        poacher_to_herd = self.animal_location - self.poacher_location
        current_distance = np.linalg.norm(poacher_to_herd)
        
        # Update poacher direction based on distance
        if current_distance < self.min_poacher_distance:
            # Move away from herd if too close
            self.poacher_direction = -poacher_to_herd / current_distance
        elif current_distance > self.max_poacher_distance:
            # Move toward herd if too far
            self.poacher_direction = poacher_to_herd / current_distance
        else:
            # Random movement while maintaining distance
            if np.random.rand() < 0.15:  # 15% chance to change direction
                perpendicular = np.array([-poacher_to_herd[1], poacher_to_herd[0]])
                perpendicular = perpendicular / np.linalg.norm(perpendicular)
                random_angle = np.random.uniform(-np.pi/4, np.pi/4)
                self.poacher_direction = (np.cos(random_angle) * perpendicular + 
                                        np.sin(random_angle) * poacher_to_herd / current_distance)
        
        # Update poacher position
        self.poacher_location += self.poacher_direction * self.poacher_speed
        self.poacher_location = np.clip(self.poacher_location, 0, self.AREA_SIZE)
        
        # Handle boundary collisions for herd
        if any(self.animal_location <= 0) or any(self.animal_location >= self.AREA_SIZE):
            self.herd_direction *= -1

    def run_search(self):
        # Store initial state
        self.animation_history['particles'].append(np.copy(self.particles))
        self.animation_history['animal_loc'].append(np.copy(self.animal_location))
        self.animation_history['poacher_loc'].append(np.copy(self.poacher_location))

        for iteration in range(self.MAX_ITER):
            # Update target positions
            self.update_target_positions()
            
            # Existing PSO logic
            for i in range(self.NUM_PARTICLES):
                score = self.fitness_function(self.particles[i], self.scan_radii[i])
                
                if score < self.personal_best_scores[i]:
                    self.personal_best_scores[i] = score
                    self.personal_best_positions[i] = self.particles[i]
                
                if score < self.global_best_score:
                    self.global_best_score = score
                    self.global_best_position = self.particles[i]
            
            # Update drone positions
            for i in range(self.NUM_PARTICLES):
                r1, r2 = np.random.rand(), np.random.rand()
                self.velocities[i] = (self.W * self.velocities[i] +
                                    self.C1 * r1 * (self.personal_best_positions[i] - self.particles[i]) +
                                    self.C2 * r2 * (self.global_best_position - self.particles[i]))
                self.velocities[i] = np.clip(self.velocities[i], -self.MAX_SPEED, self.MAX_SPEED)
                
                self.particles[i] = self.particles[i] + self.velocities[i]
                self.particles[i] = np.clip(self.particles[i], 0, self.AREA_SIZE)
                
                # Adapt scanning radius
                if np.linalg.norm(self.particles[i] - self.animal_location) <= self.scan_radii[i]:
                    self.scan_radii[i] = self.MIN_SCAN_RADIUS
                else:
                    self.scan_radii[i] = self.MAX_SCAN_RADIUS
            
            # Store state for animation
            self.animation_history['particles'].append(np.copy(self.particles))
            self.animation_history['animal_loc'].append(np.copy(self.animal_location))
            self.animation_history['poacher_loc'].append(np.copy(self.poacher_location))
            
            # Add trails for movement visualization
            if len(self.animation_history['animal_loc']) > 1:
                self.animation_history.setdefault('animal_trail', []).append(
                    np.copy(self.animation_history['animal_loc'][-2:]))
                self.animation_history.setdefault('poacher_trail', []).append(
                    np.copy(self.animation_history['poacher_loc'][-2:]))
            
            if self.global_best_score < 1.0:
                print(f"Poacher found at {self.global_best_position} in {iteration} iterations!")
                break

    def create_animation(self, filename='pso_search.gif', fps=10):
        fig, ax = plt.subplots(figsize=(8, 8))
        
        def animate(frame):
            ax.clear()
            
            # Get data for current frame
            particles = self.animation_history['particles'][frame]
            animal_loc = self.animation_history['animal_loc'][frame]
            poacher_loc = self.animation_history['poacher_loc'][frame]
            
            # Plot initial positions
            if frame == 0:
                ax.scatter(self.initial_locations[:, 0], self.initial_locations[:, 1],
                          c='black', marker='s', alpha=0.3, label='Initial Positions')
            
            # Plot movement trails
            if frame > 0:
                # Plot last few positions to show movement trail
                trail_length = 10
                start_idx = max(0, frame - trail_length)
                animal_trail = np.array(self.animation_history['animal_loc'][start_idx:frame+1])
                poacher_trail = np.array(self.animation_history['poacher_loc'][start_idx:frame+1])
                
                ax.plot(animal_trail[:, 0], animal_trail[:, 1], 'b-', alpha=0.2)
                ax.plot(poacher_trail[:, 0], poacher_trail[:, 1], 'r-', alpha=0.2)
            
            # Plot current positions
            ax.scatter(particles[:, 0], particles[:, 1],
                      c='green', marker='s', label='Drones')
            ax.scatter(poacher_loc[0], poacher_loc[1],
                      c='red', marker='x', s=100, label='Poacher')
            ax.scatter(animal_loc[0], animal_loc[1],
                      c='blue', marker='o', s=100, label='Animal')
            
            ax.set_xlim(0, self.AREA_SIZE)
            ax.set_ylim(0, self.AREA_SIZE)
            ax.grid(True)
            ax.set_title(f'Search Progress - Frame {frame}')
            ax.legend()
        
        # Create animation
        num_frames = len(self.animation_history['particles'])
        anim = FuncAnimation(fig, animate, frames=num_frames, 
                           interval=1000/fps, blit=False)
        
        # Save as GIF
        writer = PillowWriter(fps=fps)
        anim.save(filename, writer=writer)
        plt.close()
        
        print(f"Animation saved as {filename}")
        
        try:
            return HTML(anim.to_jshtml())
        except:
            return None

    def plot_results(self):
        plt.figure(figsize=(8, 8))
        # Plot in order of desired layering (bottom to top)
        plt.scatter(self.initial_locations[:, 0], self.initial_locations[:, 1], 
                   c='black', marker='s', label='Initial Positions')
        plt.scatter(self.particles[:, 0], self.particles[:, 1], 
                   c='green', marker='s', label='Drones')
        plt.scatter(self.poacher_location[0], self.poacher_location[1], 
                   c='red', marker='x', label='Poacher')
        plt.scatter(self.animal_location[0], self.animal_location[1], 
                   c='blue', marker='o', s=100, label='Animal')  # Made animal marker larger
        plt.legend()
        plt.xlim(0, self.AREA_SIZE)
        plt.ylim(0, self.AREA_SIZE)
        plt.grid()
        plt.title("Final Drone Positions after PSO Search")
        plt.show()
        print(f"Animal location: {self.animal_location}")
        print(f"Poacher location: {self.poacher_location}")

def main():
    pso_search = PSODroneSearch()
    pso_search.run_search()
    pso_search.create_animation()  # Creates and saves the GIF
    pso_search.plot_results()     # Still show final results

if __name__ == "__main__":
    main() 