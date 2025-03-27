# defines the high-level state representation in the simulation. 

import pygame
import random
import math

from events import POACHER_ATTACK_ANIMAL, ANIMAL_KILLED, DRONE_DETECTED_POACHER, DRONE_CAUGHT_POACHER,DRONE_DETECTED_ANIMAL, DRONE_LOST_POACHER, DRONE_LOST_ANIMAL
from settings import FPS

class State:
    def __init__(self, speed_modifier=1.0, scan_range_modifier=1.0, detection_probability=1.0):
        self.agent = None
        self.speed_modifier = speed_modifier
        self.scan_range_modifier = scan_range_modifier
        self.detection_probability = detection_probability
    
    def enter(self, agent):
        """Called when an agent enters this state"""
        self.agent = agent
        
    def exit(self):
        """Called when an agent exits this state"""
        self.agent = None
    
    def action(self):
        """Action logic for this state, to be implemented by subclasses"""
        pass
    
    def check_transition(self):
        """
        Check if the agent can transition to another state, to be implemented by subclasses
        Returns:
            state_object of state if transition is possible/necessary, None otherwise
        """
        pass


# Drone states
class DroneHighAltitude(State):
    def __init__(self):
        super().__init__()
        
    def action(self):
        # Implementation of state action through optimizer
        return

    def check_transition(self):
        # always true for low altitude state
        return DroneLowAltitude()


class DroneLowAltitude(State):
    def __init__(self):
        super().__init__(speed_modifier=0.7, scan_range_modifier=0.5, detection_probability=0.9)

    def action(self):
        # Implementation of state action through optimizer
        return

    def check_transition(self):
        # always true for high altitude state
        return DroneHighAltitude()


# Animal states
class AnimalIdle(State):
    def __init__(self):
        super().__init__(speed_modifier=0.5)
        self.herd_cohesion=0.8
        self.separation_weight = 1.2
        self.random_weight = 0.3
        
    def action(self):
        # Random grazing movement, tendency to stay with herd
        # No herd members, move randomly
        if not self.agent.herd:
            direction = pygame.Vector2(random.randint(-1, 1), random.randint(-1, 1))

        # If herd members are present, calculate cohesion and separation vectors
        else:
            cohesion_vector = pygame.Vector2(0, 0)
            herd_center = pygame.Vector2(0, 0)
            separation_vector = pygame.Vector2(0, 0)
            random_vector = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            
            # Calculate vectors for each herd member            
            for animal in self.agent.herd:
                # Calculate herd center for cohesion vector
                herd_center += animal.position
                
                # Check distance to animal for separation vector
                distance = self.agent.position.distance_to(animal.position)
                if distance < self.agent.separation:
                    
                    # Move away from the other animal
                    away_vector = self.agent.position - animal.position
                    if away_vector.length() > 0:

                        # The closer the other animal, the stronger the separation force
                        separation_vector += away_vector / max(1, distance)

            # Calculate cohesion vector from herd center
            cohesion_vector = herd_center / len(self.agent.herd) - self.agent.position
            if cohesion_vector.length() > 0:
                cohesion_vector.normalize_ip()
            
            # Combine all vectors with their weights
            direction = (
                cohesion_vector * self.herd_cohesion +
                separation_vector * self.separation_weight +
                random_vector * self.random_weight
                )

        # Move agent in the given direction
        self.agent.move(direction, mode='direction')
        return
    
    def check_transition(self):
        # Check if agent has a threat in sight
        if self.agent.threat:

            # Check distance to threat
            distance = self.agent.position.distance_to(self.agent.threat.position)
            
            # If threat is close enough, transition to fleeing state
            if distance < self.agent.threat_range:
                return AnimalFleeing()
        
        # Stay in Idle state if no threat is in sight or not in range
        return None  # Transition to dead state triggered by event and not self-check
            

class AnimalFleeing(State):
    def __init__(self):
        super().__init__(speed_modifier=1.0)
        self.herd_cohesion = 0

    def action(self):
        # Fast movement away from threat
        # Caclulate direction to flee from threat
        direction = pygame.Vector2(self.agent.position - self.agent.threat.position)

        # Move agent in the opposite direction
        self.agent.move(direction, mode='direction')
        return
        
    def check_transition(self):
        # Check if agent has a threat in sight
        if self.agent.threat:

            # Calc distance to threat & check if close enough to keep fleeing
            distance = self.agent.position.distance_to(self.agent.threat.position)
            if distance < self.agent.threat_range:
                return None # Transition to dead state triggered by event and not self-check
        
        # Transition to Idle state if threat is lost or not in range
        return AnimalIdle()



# Poacher states
class PoacherIdle(State):
    """
    Poacher idle state, tries to find animals to hunt. 
    Uses the agents memory of prior seen animals and their locations. If memory exists, moves toward the most recent memory.
    If no memory exists, move in strategic search pattern (expanding circles)
    """
    
    def __init__(self):
        super().__init__(speed_modifier=0.5, scan_range_modifier=1.0, detection_probability=1.0)
        self.search_time = 0
        self.time_since_direction_change = 0
        self.search_angle = random.randint(0, 360)
        self.max_interval = FPS * 5  # Change direction every 3 seconds

    def action(self):
        # If memory of animal locations, move towards the most recent memory
        if self.agent.memory:
            # Get the most recent memory & move towards it
            target_position = self.agent.memory[0][1]
            self.agent.move(target_position, mode='position')
        
        # Follow search pattern of expanding circles
        else:
            # Change direction every few seconds
            self.search_time += 1
            self.time_since_direction_change += 1      

            # Calculate direction change interval using logarithmic growth
            # This will start small and grow toward max_interval
            direction_change_interval = self.max_interval * (1 - 1 / math.log(1 + self.search_time / 2))
            
            # Change direction when interval is reached
            if self.time_since_direction_change >= direction_change_interval:
                self.search_angle = (self.search_angle + 45) % 360
                self.time_since_direction_change = 0
            
            # Create direction vector from angle with increasing magnitude
            direction = pygame.Vector2(math.cos(math.radians(self.search_angle)), math.sin(math.radians(self.search_angle)))
            self.agent.move(direction, mode='direction')
        return
    
    def check_transition(self):
        # Check if agent has a target & transition to Hunting state
        if self.agent.target:
            return PoacherHunting()
        
        return None  # Transition to dead state triggered by event and not self-check


class PoacherHunting(State):
    """
    Poacher hunting state, moves towards the target animal to attack it.
    Can only be in this state if a target animal is in sight.
    """
    def __init__(self):
        super().__init__(speed_modifier=1.2, scan_range_modifier=1.0, detection_probability=1.0)
        
    def action(self):
        # Get target position and move towards it
        target_position = self.agent.target.position
        self.agent.move(target_position, mode='position')
        return
        
        
    def check_transition(self):
        # Transition options: Attacking state, Idle state
        if self.agent.target:
            
            # If target is in attack range, transition to attacking state
            distance = self.agent.position.distance_to(self.agent.target.position)
            if distance < self.agent.attack_range:
                return PoacherAttacking()
            
            # If target is out of attack range, stay in Hunting state
            else:
                return None
        
        # Transition to Idle state if target is lost
        else:
            return PoacherIdle()


class PoacherAttacking(State):
    def __init__(self):
        super().__init__(speed_modifier=1.5, scan_range_modifier=1.0, detection_probability=1.0)
        self.attack_time = 0
        
    def action(self):
        # Direct attack on animal
        self.attack_time += 1

        # if animal is in range create and post attack event
        if self.agent.position.distance_to(self.agent.target.position) < self.agent.kill_range:
            attack_event = pygame.event.Event(POACHER_ATTACK_ANIMAL, {'animal': self.agent.target, 'poacher': self.agent})
            pygame.event.post(attack_event)
            
        # if animal is not in range, move towards animal
        else:
            self.agent.move(self.agent.target.position, mode='position')
        return
    
    def check_transition(self):
        # Check if agent still has a target (not lost or dead) & is still in attack range
        if self.agent.target:
            distance = self.agent.position.distance_to(self.agent.target.position)
            if distance < self.agent.attack_range:
                return None
            
            # If target is out of attack range, transition back to Hunting state
            else:
                return PoacherHunting()
            
        # Transition to Idle state if target is lost or dead  --> target = None
        return PoacherIdle()

    
class Terminal(State):
    def __init__(self):
        super().__init__(speed_modifier=0, scan_range_modifier=0, detection_probability=0)
        
    def action(self):
        # Terminal state, agent exists further bot does not move anymore
        return
    
    def check_transition(self):
        # Agent can't transition to any other state
        return None
    