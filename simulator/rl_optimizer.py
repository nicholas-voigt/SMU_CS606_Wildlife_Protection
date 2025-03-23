import pygame
import random
import numpy as np
from simulator.optimizer import DroneOptimizer
from simulator.states import DroneHighAltitude, DroneLowAltitude

class RLOptimizer(DroneOptimizer):
    """Reinforcement Learning Optimizer for drone control"""
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.2):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.q_table = {}  # {state_key: {action_key: q_value}}
        self.previous_states = {}  # {drone_name: previous_state}
        self.previous_actions = {}  # {drone_name: previous_action}
        
    def discretize_state(self, drone, detected_animals, detected_poachers):
        """Convert continuous state to discrete state for Q-learning"""
        # Create a simple grid-based state representation
        grid_size = 5  # 5x5 grid for simplicity
        
        # Drone position in grid
        grid_x = min(grid_size-1, max(0, int(drone.position.x / (800/grid_size))))
        grid_y = min(grid_size-1, max(0, int(drone.position.y / (600/grid_size))))
        
        # Count nearby entities in each quadrant (NE, NW, SE, SW)
        quadrants = [(0,0), (0,0), (0,0), (0,0)]  # (animals, poachers) for each quadrant
        
        for animal in detected_animals:
            dx = animal.position.x - drone.position.x
            dy = animal.position.y - drone.position.y
            quadrant_idx = (0 if dy < 0 else 2) + (0 if dx < 0 else 1)
            quadrants[quadrant_idx] = (quadrants[quadrant_idx][0] + 1, quadrants[quadrant_idx][1])
            
        for poacher in detected_poachers:
            dx = poacher.position.x - drone.position.x
            dy = poacher.position.y - drone.position.y
            quadrant_idx = (0 if dy < 0 else 2) + (0 if dx < 0 else 1)
            quadrants[quadrant_idx] = (quadrants[quadrant_idx][0], quadrants[quadrant_idx][1] + 1)
        
        # Create state key
        state_key = (
            grid_x, grid_y,
            quadrants[0][0], quadrants[0][1],
            quadrants[1][0], quadrants[1][1],
            quadrants[2][0], quadrants[2][1],
            quadrants[3][0], quadrants[3][1],
            1 if isinstance(drone.active_state, DroneLowAltitude) else 0
        )
        
        return state_key
    
    def get_reward(self, drone, detected_animals, detected_poachers):
        """Calculate reward based on current situation"""
        reward = 0
        
        # Reward for detecting animals
        reward += len(detected_animals) * 1
        
        # Higher reward for detecting poachers
        reward += len(detected_poachers) * 5
        
        # Penalty for being in wrong state
        if detected_poachers and not isinstance(drone.active_state, DroneLowAltitude):
            reward -= 2  # Penalty for not being in low altitude when poachers detected
        
        return reward
    
    def get_actions(self, drone):
        """Get possible discrete actions for the drone"""
        # 8 movement directions + 2 altitude states = 16 possible actions
        actions = []
        for direction in [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]:
            for altitude in [0, 1]:  # 0=high, 1=low
                actions.append((direction[0], direction[1], altitude))
        return actions
    
    def action_to_params(self, action, drone):
        """Convert discrete action to continuous parameters"""
        direction = pygame.Vector2(action[0], action[1])
        if direction.length() > 0:
            direction.normalize()
            
        new_state = None
        if action[2] == 1 and not isinstance(drone.active_state, DroneLowAltitude):
            new_state = DroneLowAltitude()
        elif action[2] == 0 and not isinstance(drone.active_state, DroneHighAltitude):
            new_state = DroneHighAltitude()
            
        return {
            'state': new_state,
            'direction': direction,
            'speed_modifier': 1.0
        }
    
    def optimize(self, drones, detected_animals, detected_poachers):
        drone_actions = {}
        
        for drone in drones:
            # Get current state
            state = self.discretize_state(drone, detected_animals, detected_poachers)
            
            # Get reward if we have a previous state
            if drone.name in self.previous_states:
                reward = self.get_reward(drone, detected_animals, detected_poachers)
                
                # Q-learning update
                old_state = self.previous_states[drone.name]
                old_action = self.previous_actions[drone.name]
                
                # Initialize Q-values if needed
                if old_state not in self.q_table:
                    self.q_table[old_state] = {}
                if old_action not in self.q_table[old_state]:
                    self.q_table[old_state][old_action] = 0.0
                    
                # Get max Q-value for current state
                if state not in self.q_table:
                    self.q_table[state] = {}
                max_q = max([0] + list(self.q_table[state].values())) if self.q_table[state] else 0
                
                # Update Q-value
                self.q_table[old_state][old_action] += self.learning_rate * (
                    reward + self.discount_factor * max_q - self.q_table[old_state][old_action]
                )
            
            # Choose action (exploration vs exploitation)
            actions = self.get_actions(drone)
            if state not in self.q_table:
                self.q_table[state] = {}
                
            if random.random() < self.exploration_rate:
                # Exploration: random action
                action = random.choice(actions)
            else:
                # Exploitation: best known action
                if not self.q_table[state]:
                    action = random.choice(actions)
                else:
                    action = max(self.q_table[state], key=self.q_table[state].get)
            
            # Store state and action for next update
            self.previous_states[drone.name] = state
            self.previous_actions[drone.name] = action
            
            # Convert action to drone parameters
            drone_actions[drone] = self.action_to_params(action, drone)
            
        return drone_actions