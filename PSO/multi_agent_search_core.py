import numpy as np

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
        self.velocities = np.random.uniform(-self.MAX_SPEED, self.MAX_SPEED, (self.NUM_PARTICLES, 2))
        self.scan_radii = np.full(self.NUM_PARTICLES, self.MAX_SCAN_RADIUS)

        # Best solutions
        self.personal_best_positions = np.copy(self.particles)
        self.global_best_position = self.personal_best_positions[0]
        self.personal_best_scores = np.full(self.NUM_PARTICLES, np.inf)
        self.global_best_score = np.inf

        # Movement parameters
        self.herd_speed = 1.0
        self.poacher_speed = 0.7
        self.herd_direction = np.random.rand(2) * 2 - 1
        self.poacher_direction = np.random.rand(2) * 2 - 1
        
        # Distance parameters
        self.min_poacher_distance = 8
        self.max_poacher_distance = 25

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
            # Random movement while maintaining distance.
            # Just to create movement to simulate poachers move around to get better angle.
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
        for iteration in range(self.MAX_ITER):
            # Update target positions
            self.update_target_positions()
            
            # Update personal and global bests
            for i in range(self.NUM_PARTICLES):
                score = self.fitness_function(self.particles[i], self.scan_radii[i])
                
                if score < self.personal_best_scores[i]:
                    self.personal_best_scores[i] = score
                    self.personal_best_positions[i] = self.particles[i]
                
                if score < self.global_best_score:
                    self.global_best_score = score
                    self.global_best_position = self.particles[i]
            
            # Update velocities and positions
            for i in range(self.NUM_PARTICLES):
                r1, r2 = np.random.rand(), np.random.rand()
                self.velocities[i] = (self.W * self.velocities[i] +
                                    self.C1 * r1 * (self.personal_best_positions[i] - self.particles[i]) +
                                    self.C2 * r2 * (self.global_best_position - self.particles[i]))
                self.velocities[i] = np.clip(self.velocities[i], -self.MAX_SPEED, self.MAX_SPEED)
                
                self.particles[i] = self.particles[i] + self.velocities[i]
                self.particles[i] = np.clip(self.particles[i], 0, self.AREA_SIZE)
                
                # Adapt scanning radius
                '''If the Drone is within its scan radius of the Herd:
                scan radius is set to a minimum value (self.MIN_SCAN_RADIUS)
                If the Drone is outside its scan radius of the Herd:
                scan radius is set to a maximum value (self.MAX_SCAN_RADIUS)'''

                if np.linalg.norm(self.particles[i] - self.animal_location) <= self.scan_radii[i]:
                    self.scan_radii[i] = self.MIN_SCAN_RADIUS
                else:
                    self.scan_radii[i] = self.MAX_SCAN_RADIUS
            
            if self.global_best_score < 1.0:
                print(f"Poacher found at {self.global_best_position} in {iteration} iterations!")
                break

def main():
    pso_search = PSODroneSearch()
    pso_search.run_search()
    print(f"Final animal location: {pso_search.animal_location}")
    print(f"Final poacher location: {pso_search.poacher_location}")

if __name__ == "__main__":
    main() 