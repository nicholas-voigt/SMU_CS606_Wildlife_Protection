# Definition of Agent class as subclass of Pygame Sprite
# Agents are the entities in the simulation that interact with the environment
# An agent is a state machine that can be in one of several states at a time
# The agent's behavior (actions, movements, ...) is determined by the current state
# The agent can change states based on certain conditions
# Current Agents implemented: Drone, Animal, Poacher

import pygame
import heapq
from collections import deque

from settings import *
from states import DroneFastSearch, AnimalIdle, PoacherIdle


class Agent(pygame.sprite.Sprite):
    def __init__(self, name, x, y, color):
        """
        Initialize the base agent class as subclass of Pygame Sprite.
        Args:
            name: str, name of the agent
            x: int, x-coordinate of the agent
            y: int, y-coordinate of the agent
            color: tuple, RGB color of the agent
        """
        super().__init__()
        # Basic identifiers 
        self.name = name
        self.type = None
        
        # State properties
        self.active_state = None
        
        # Agent properties
        self.controller = None
        self.base_speed = 0
        self.position = pygame.Vector2(x, y)
        self.scan_range = 0
        self.memory = deque(maxlen=3)  # Memory queue of tuples to store last sightings (agent_type, position)
        
        # Pygame sprite setup for rendering
        self.image = pygame.Surface((10, 10))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))

    def set_state(self, new_state):
        """
        Change the agent's state. Called from updated method after transition conditions were checked.
        Exits the current state and enters the new state.
        Args:
            new_state: state object
        """
        # Exit the current state if exists (in initialization no current state)
        if self.active_state:
            self.active_state.exit()
        
        # Set new active state
        self.active_state = new_state

        # Enter the new state
        self.active_state.enter(agent=self)
        return
    
    def move(self, vector: pygame.Vector2, speed=None, mode='direction'):
        """
        Move agent to the given position if within speed range, else on a vector towards it.
        Args:
            vector: pygame.Vector2, can be position to move to or direction to move in
            speed: int (optional), speed to move with, if None method uses base speed
            mode: str, 'direction' or 'position', whether vector is a direction or a position
        """
        # use given speed if specified or calculate the velocity to move with
        velocity = speed if speed is not None else self.base_speed * self.active_state.speed_modifier
        
        # If vector is a position, calculate the direction vector
        if mode == 'position':
            
            # Calculate distance to the target position & check if it can be reached
            distance = self.position.distance_to(vector)
            if distance <= velocity:
                
                # Update the agents position to the target position
                self.position = vector
            
            # Calculate the direction towards target position & move agent
            else:
                direction = pygame.Vector2(vector - self.position)
                direction.normalize_ip()
                self.position += direction * velocity
        
        # If vector is a direction, move the agent in that direction
        elif mode == 'direction':
            if vector.length() > 0:
                vector.normalize_ip()
                self.position += vector * velocity
        
        else:
            raise ValueError(f"Invalid mode: {mode}")
        
        # Keep agent within boundaries
        self.position.x = max(0, min(GAME_WIDTH, self.position.x))
        self.position.y = max(0, min(HEIGHT, self.position.y))

        # Update the sprite position
        self.rect.center = self.position
        return
    
    def scan_surroundings(self, agents, mode='all'):
        """
        Scan the environment for the given agents within scan range.
        Args:
            agents: list of agents to check for
            mode: str, 'all' or 'nearest', whether to return all detected agents or only the nearest one
        Returns:
            detected_agents: list, heapified list of detected agents with (distance, tie_breaker, agent) tuples for mode all or single tuple for mode nearest. If no agents found, returns empty list.
        """

        # Create a heap to store detected agents
        detected_agents = []
        heapq.heapify(detected_agents)
        tie_breaker = 0

        # Check each agent in the list
        for agent in agents:
            
            # Skip self
            if agent == self:
                continue

            # Calculate the distance to the agent
            distance = self.position.distance_to(agent.position)

            # If the agent is within the scan range, add it to the heap
            if distance < self.scan_range * self.active_state.scan_range_modifier:
                heapq.heappush(detected_agents, (self.position.distance_to(agent.position), tie_breaker, agent))
                tie_breaker += 1

        # Return the detected agents
        # If mode is 'nearest', return only the nearest agent
        if mode == 'nearest' and detected_agents:
            return detected_agents[0]
        
        # If mode is 'all', return all detected agents or an empty list if none were detected
        else:
            return detected_agents


class Drone(Agent):
    def __init__(self, name, x, y):
        super().__init__(name=name, x=x, y=y, color=DRONE_COLOR)
        self.type = 'Drone'
        self.base_speed = DRONE_SPEED
        self.scan_range = DRONE_SCAN_RANGE
        self.catch_range = DRONE_CATCH_RANGE
        self.target = None 
        # Set initial state
        self.set_state(DroneFastSearch())


class Animal(Agent):
    def __init__(self, name, x, y):
        super().__init__(name=name, x=x, y=y, color=ANIMAL_COLOR)
        self.type = 'Animal'
        self.herd = None
        self.base_speed = ANIMAL_SPEED
        self.scan_range = ANIMAL_SCAN_RANGE
        self.threat_range = ANIMAL_THREAT_RANGE
        self.separation = ANIMAL_SEPARATION
        self.threat = None
        self.health = ANIMAL_HEALTH
        # Set initial state
        self.set_state(AnimalIdle())
            

class Poacher(Agent):
    def __init__(self, name, x, y):
        super().__init__(name=name, x=x, y=y, color=POACHER_COLOR)  
        self.type = 'Poacher'
        self.base_speed = POACHER_SPEED
        self.scan_range = POACHER_SCAN_RANGE
        self.attack_range = POACHER_ATTACK_RANGE
        self.attack_duration = POACHER_ATTACK_DURATION
        self.attack_damage = POACHER_ATTACK_DAMAGE
        self.kill_range = POACHER_KILL_RANGE
        self.target = None 
        # Set initial state
        self.set_state(PoacherIdle())
