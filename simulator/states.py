# defines the high-level state representation in the simulation. 

import pygame
import random

from events import POACHER_KILLED_ANIMAL, DRONE_DETECTED_POACHER, DRONE_CAUGHT_POACHER, DRONE_DETECTED_ANIMAL, DRONE_LOST_POACHER, DRONE_LOST_ANIMAL

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
        
    def action(self):
        # Random grazing movement, tendency to stay with herd,
        # TODO: Implement herd cohesion
            
        # Set direction to move in as random
        direction = pygame.Vector2(random.randint(-1, 1), random.randint(-1, 1))
        
        # Move agent in the given direction
        self.agent.move(direction)
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
        direction = self.agent.position - self.agent.threat.position

        # Move agent in the opposite direction
        self.agent.move(direction)
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
        
    def action(self):
        # Random movement, trying to find a target target search in main.py
        # Get instructions for movement from controller
        direction = pygame.Vector2(random.randint(-1, 1), random.randint(-1, 1))

        # Move agent in the given direction
        self.agent.move(direction)
        return
    
    def check_transition(self):
        # Check if agent has a target & transition to Hunting state
        if self.agent.target:
            return PoacherHunting()
        
        return None  # Transition to dead state triggered by event and not self-check
    

class PoacherHunting(State):
    def __init__(self):
        super().__init__(speed_modifier=0.7, scan_range_modifier=1.0, detection_probability=1.0)
        
    def action(self):
        # Hunt the target animal
        # Caclulate direction towards target
        direction = self.agent.target.position - self.agent.position

        # Move agent in the direction of the target
        self.agent.move(direction)
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
        super().__init__(speed_modifier=1.2, scan_range_modifier=1.0, detection_probability=1.0)
        self.attack_time = 0
        
    def action(self):
        # Direct attack on animal
        self.attack_time += 1

        # check if animal is in kill range
        if self.agent.position.distance_to(self.agent.target.position) < self.agent.kill_range:

            # create and post kill event
            kill_event = pygame.event.Event(POACHER_KILLED_ANIMAL, {'animal': self.agent.target})
            pygame.event.post(kill_event)
            
            # set target to None
            self.agent.target = None

        # if animal is not in kill range, move towards animal
        else:

            # Caclulate direction towards target
            direction = self.agent.target.position - self.agent.position

            # Move agent in the direction of the target
            self.agent.move(direction)
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
    