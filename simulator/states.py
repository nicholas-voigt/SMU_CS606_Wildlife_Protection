# defines the high-level state representation in the simulation. 

import pygame
import random
import math

from events import POACHER_KILLED_ANIMAL, DRONE_DETECTED_POACHER, DRONE_CAUGHT_POACHER,DRONE_DETECTED_ANIMAL, DRONE_LOST_POACHER, DRONE_LOST_ANIMAL
from settings import ANIMAL_HOTSPOTS

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
        super().__init__(speed_modifier=0.3)
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
        super().__init__(speed_modifier=1.5)
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

            # Check distance to threat
            distance = self.agent.position.distance_to(self.agent.threat.position)
            
            # If threat is close enough, stay in fleeing state
            if distance < self.agent.threat_range:
                return None # Transition to dead state triggered by event and not self-check
        
        # Transition to Idle state if threat is lost or not in range
        return AnimalIdle()



# Poacher states
class PoacherIdle(State):
    def __init__(self):
        super().__init__(speed_modifier=0.5, scan_range_modifier=1.0, detection_probability=1.0)
    
    """    
    def action(self):
        # Random movement, trying to find a target target search in main.py
        # Get instructions for movement from controller
        direction = pygame.Vector2(random.randint(-1, 1), random.randint(-1, 1))

        # Move agent in the given direction
        self.agent.move(direction, mode='direction')
        return
    
    def check_transition(self):
        # Check if agent has a target & transition to Hunting state
        if self.agent.target:
            return PoacherHunting()
        
        return None  # Transition to dead state triggered by event and not self-check
    """
    
    def action(self):
        # If we have memory of animal locations, move toward the most recent memory
        if self.agent.memory:
            # Get the most recent memory that hasn't expired
            current_time = pygame.time.get_ticks()
            valid_memories = [m for m in self.agent.memory if current_time - m['time'] < self.agent.memory_timeout]
            
            if valid_memories:
                # Move toward the most recent memory
                target_pos = valid_memories[0]['position']
                direction = target_pos - self.agent.position
                self.agent.move(direction, mode='direction')
                return
        
        # If no valid memories, check hotspots
        if hasattr(self, 'current_hotspot') and self.current_hotspot is not None:
            # Continue moving to current hotspot
            hotspot_position = pygame.Vector2(ANIMAL_HOTSPOTS[self.current_hotspot])
            if self.agent.position.distance_to(hotspot_position) < 20:
                # Reached hotspot, pick another one
                self.current_hotspot = random.randint(0, len(ANIMAL_HOTSPOTS) - 1)
            direction = hotspot_position - self.agent.position
            self.agent.move(direction, mode='direction')
        else:
            # Pick a random hotspot
            self.current_hotspot = random.randint(0, len(ANIMAL_HOTSPOTS) - 1)
        
        # Implement a more strategic search pattern - move in expanding circles or follow terrain features
        current_tick = pygame.time.get_ticks() // 60  # Change direction every 60 ticks
        angle = current_tick % 8 * 45  # 8 directions, changing over time
        direction = pygame.Vector2(
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        )
        self.agent.move(direction, mode='direction')
     

class PoacherHunting(State):
    def __init__(self):
        super().__init__(speed_modifier=1.0, scan_range_modifier=1.0, detection_probability=1.0)
        
        # Poacher to follow tracks if animals flee
        self.last_seen_position = None
        self.tracking_time = 0
        self.max_tracking_time = 300  # Give up after 300 frames
        
    def action(self):
        """
        # Hunt the target animal
        # Move agent towards the position of the target
        self.agent.move(self.agent.target.position, mode='position')
        return
        """
        # If target exists, update last known position and move toward it
        if self.agent.target:
            self.last_seen_position = self.agent.target.position.copy()
            self.tracking_time = 0
            self.agent.move(self.agent.target.position, mode='position')
        # If target was lost but we have a last seen position, track it for a while
        elif self.last_seen_position and self.tracking_time < self.max_tracking_time:
            self.tracking_time += 1
            self.agent.move(self.last_seen_position, mode='position')
        return
        
        
    def check_transition(self):
        # CheckCheck if agent can transition to Attacking state
        # Check if agent has a target in range
        if self.agent.target:

            # Check distance to target
            distance = self.agent.position.distance_to(self.agent.target.position)

            # If target is in attack range, transition to attacking state
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

        # check if animal is in kill range
        if self.agent.position.distance_to(self.agent.target.position) < self.agent.kill_range:

            # create and post kill event
            kill_event = pygame.event.Event(POACHER_KILLED_ANIMAL, {'animal': self.agent.target, 'poacher': self.agent})
            pygame.event.post(kill_event)
            
            # set target to None
            self.agent.target = None

        # if animal is not in kill range, move towards animal
        else:
            self.agent.move(self.agent.target.position, mode='position')
        return
    
    def check_transition(self):
        # Check if agent still has a target
        if self.agent.target:

            # Check distance to target
            distance = self.agent.position.distance_to(self.agent.target.position)
            
            # If target is in attack range, stay in Attacking state
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
    