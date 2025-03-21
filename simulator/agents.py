# Definition of Agent class as subclass of Pygame Sprite
# Agents are the entities in the simulation that interact with the environment
# An agent is a state machine that can be in one of several states at a time
# The agent's behavior (actions, movements, ...) is determined by the current state
# The agent can change states based on certain conditions
# Current Agents implemented: Drone, Animal, Poacher

import pygame
import random
from collections import defaultdict
from simulator.states import *
from simulator.settings import *


class Agent(pygame.sprite.Sprite):
    def __init__(self, name, states: defaultdict, x, y, color):
        """
        Initialize the base agent class as subclass of Pygame Sprite.
        Args:
            states: defaultdict, dictionary of states for the agent
            x: int, x-coordinate of the agent
            y: int, y-coordinate of the agent
            color: tuple, RGB color of the agent
            speed: int, speed of the agent
        """
        super().__init__()
        # Basic identifiers 
        self.name = name
        self.type = None
        
        # State properties
        self.states = states
        self.active_state = None
        
        # Agent properties
        self.base_speed = None
        self.position = pygame.Vector2(x, y)
        self.scan_range = None
        self.detected_agents = []
        
        # Pygame sprite setup for rendering
        self.image = pygame.Surface((10, 10))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        """
        Update the agent. This includes performing the state action and validating requirements for state change.
        """
        pass
        
    def set_state(self, new_state):
        """
        Change the agent's state. Called from updated method after transition conditions were checked.
        Exits the current state and enters the new state.
        Args:
            new_state: str, name of the new state
        """
        # Exit the current state, in startup no current state
        if self.active_state:
            self.active_state.exit()
        # Enter the new state
        self.active_state = new_state
        self.active_state.enter()
        return
    
    def move(self, direction):
        """
        Move agent in the given direction with the speed specified in the state.
        Args:
            direction: pygame.Vector2, direction to move in
        """
        if direction.length() > 0:
            self.position += direction * self.base_speed * self.active_state.speed_modifier
            # Keep agent within boundaries
            self.position.x = max(0, min(WIDTH, self.position.x))
            self.position.y = max(0, min(HEIGHT, self.position.y))
            self.rect.center = self.position
    
    def scan_surroundings(self, type: str):
        """
        Scan the environment for other agents of type within scan range. Detection depends also on probability.
        Args:
            type: str, type of agent to scan for
        """
        # Implement scanning logic - for example:
        # Check for nearby agents of type within scan range
        pass


class Drone(Agent):
    def __init__(self, name, x, y):
        super().__init__(
            name=name,
            states={'HighAltitude': DroneHighAltitude(), 'LowAltitude': DroneLowAltitude()}, 
            x=x, y=y, color=(0, 0, 255)  # Blue
            )
        self.type = 'Drone'
        self.base_speed = DRONE_SPEED
        self.scan_range = DRONE_SCAN_RANGE
        # Set initial state
        self.set_state(self.states['HighAltitude'])
    
    def update(self):
        """Update the agent"""
        # Perform the action of the current state
        self.active_state.action()
        
        # Call controller to check if state transition is needed
        if self.active_state.check_transition() and controller.evaluate_state_transition(self):
            # Transition to the new state
            if isinstance(self.active_state, DroneHighAltitude):
                self.set_state(self.states['LowAltitude'])
            else:
                self.set_state(self.states['HighAltitude'])


class Animal(Agent):
    def __init__(self, name, x, y):
        super().__init__(
            name=name, speed=ANIMAL_SPEED, scan_range=ANIMAL_SCAN_RANGE, 
            states={'Idle': AnimalIdle(), 'Flee': AnimalFleeing(), 'Dead': AnimalDead()}, 
            x=x, y=y, color=(0, 255, 0)  # Green
            )
        self.type = 'Animal'
        self.base_speed = ANIMAL_SPEED
        self.scan_range = ANIMAL_SCAN_RANGE
        # Set initial state
        self.set_state(self.states['Idle'])
        
    def update(self):
        """Update the agent"""
        # Perform the action of the current state
        self.active_state.action()
        
        # Check if the agent should transition to another state
        for state_name, state in self.states.items():
            if self.active_state.check_transition(state_name):
                self.set_state(state)
                break
        
    # def update_threat(self, threat_pos):
    #     """Update known threat position --> questionable method should go into scan_surroundings"""
    #     self.threat_position = pygame.Vector2(threat_pos)
    #     # If threat is close enough, switch to fleeing state
    #     distance = self.position.distance_to(self.threat_position)
    #     if distance < 150 and isinstance(self.state, AnimalIdle):
    #         self.set_state(self.fleeing_state)
    #     elif distance >= 150 and isinstance(self.state, AnimalFleeing):
    #         self.set_state(self.idle_state)
            

class Poacher(Agent):
    def __init__(self, name, x, y):
        super().__init__(
            name=name, 
            states={'Hunting': PoacherHunting(), 'Attacking': PoacherAttacking(), 'Caught': PoacherCaught()}, 
            x=x, y=y, color=(0, 255, 0)  # Green
            )  
        self.type = 'Poacher'
        self.base_speed = POACHER_SPEED
        self.scan_range = POACHER_SCAN_RANGE
        self.stealth = 0.7  # TODO: What is this?
        self.attack_range = 30
        self.attack_duration = 5
        # Set initial state
        self.set_state(self.states['Hunting'])

    def update(self):
        """Update the agent"""
        # Perform the action of the current state
        self.active_state.action()
        
        # Check if the agent should transition to another state
        for state_name, state in self.states.items():
            if self.active_state.check_transition(state_name):
                self.set_state(state)
                break