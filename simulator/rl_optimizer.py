import pygame
import random
import numpy as np
import pickle
import os
from collections import deque
from optimizer import DroneOptimizer
from states import DroneFastSearch, DroneDeepSearch
from events import DRONE_CAUGHT_POACHER

class RLOptimizer(DroneOptimizer):
    """Reinforcement Learning Optimizer"""
    
    def __init__(self, 
                 learning_rate=0.95,                    # agent updates knowledge (Q-values) based on new experience (1=learn quick, 0=learn slow)
                 discount_factor=0.7,                   # determine importance of future rewards v/s immediate ones (1=long term, 0=immediate)
                 initial_exploration_rate=0.8,          # probability of taking random action v/s best-known (1=always explore, 0=never explore)
                 min_exploration_rate=0.15,             # min randomness/exploration agent will maintain
                 exploration_decay=0.98,                # exploration probability rate decreases over time (<1 = gradually decrease)
                 catch_threshold=30,                    # threshold for drone to catch poacher
                 exploration_bonus_weight=3.0,          # increased weight for exploration bonus
                 exploration_penalty_multiplier=3.0,    # multiplier for penalty on frequently visited locations
                 map_width=800,                         # width of the map
                 map_height=600,                        # height of the map
                 grid_x_divisions=16,                   # number of horizontal grid divisions
                 grid_y_divisions=12                    # number of vertical grid divisions
                 ):  
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = initial_exploration_rate
        self.min_exploration_rate = min_exploration_rate
        self.exploration_decay = exploration_decay
        self.catch_threshold = catch_threshold
        self.exploration_bonus_weight = exploration_bonus_weight
        self.exploration_penalty_multiplier = exploration_penalty_multiplier
        
        # Map and grid configuration
        self.map_width = map_width
        self.map_height = map_height
        self.grid_x_divisions = grid_x_divisions
        self.grid_y_divisions = grid_y_divisions
        
        self.q_table = {}  # {state_key: {action_key: q_value}}
        
        # Track exploration of grid locations
        self.grid_exploration_count = {}  # {(grid_x, grid_y): visit_count}
        self.recent_locations = deque(maxlen=10)  # Track recently visited locations
        
        # Simple experience replay buffer
        self.replay_buffer = deque(maxlen=100)
        
        # State tracking for each drone
        self.previous_states = {}  # {drone_name: previous_state}
        self.previous_actions = {}  # {drone_name: previous_action}
        
        # Performance metrics
        self.rewards_history = []
        self.episode_step = 0
        
        # Simplified action space - 8 directions × 2 altitudes
        self.actions = []
        for direction in [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]:
            for altitude in [0, 1]:  # 0=high, 1=low
                self.actions.append((direction[0], direction[1], altitude, 1.0))  # Fixed speed
    
    def discretize_state(self, drone, detected_animals, detected_poachers):
        """
        Discretize drone position into a grid with flexible divisions
        
        Args:
            drone: Drone object with position attribute
            detected_animals: List of detected animals
            detected_poachers: List of detected poachers
        
        Returns:
            A state key representing the drone's discretized location and context
        """
        # Calculate grid cell based on flexible divisions
        grid_x = min(
            self.grid_x_divisions - 1, 
            max(0, int(drone.position.x / (self.map_width / self.grid_x_divisions)))
        )
        grid_y = min(
            self.grid_y_divisions - 1, 
            max(0, int(drone.position.y / (self.map_height / self.grid_y_divisions)))
        )
        
        # Track grid exploration
        grid_location = (grid_x, grid_y)
        if grid_location not in self.grid_exploration_count:
            self.grid_exploration_count[grid_location] = 0
        self.grid_exploration_count[grid_location] += 1
        
        # Update recent locations
        if grid_location not in self.recent_locations:
            self.recent_locations.append(grid_location)
        
        # Binary detection flags (detected or not)
        animals_detected = min(1, len(detected_animals))
        poachers_detected = min(1, len(detected_poachers))
        
        # Altitude state
        altitude = 1 if isinstance(drone.active_state, DroneDeepSearch) else 0
        
        # Create state key
        state_key = (grid_x, grid_y, animals_detected, poachers_detected, altitude)
        
        return state_key
    
    def calculate_reward(self, drone, detected_animals, detected_poachers):
        """Enhanced reward calculation with stronger exploration incentives"""
        reward = 0
        
        # Rewards for detection
        if detected_animals:
            reward += 30
        
        if detected_poachers:
            reward += 100
            
            # Proximity bonus
            for poacher in detected_poachers:
                distance = drone.position.distance_to(poacher.position)
                proximity_bonus = max(0, 15 - (distance / 30))
                reward += proximity_bonus
        
        # Penalty for no detection
        if not detected_poachers and not detected_animals:
            reward -= 20
        
        # Exploration bonus
        grid_x = min(self.grid_x_divisions - 1, max(0, int(drone.position.x / (self.map_width/self.grid_x_divisions))))
        grid_y = min(self.grid_y_divisions - 1, max(0, int(drone.position.y / (self.map_height/self.grid_y_divisions))))
        grid_location = (grid_x, grid_y)
        
        if grid_location in self.grid_exploration_count:
            visit_count = self.grid_exploration_count[grid_location]
            
            # Exploration penalty
            exploration_penalty = -self.exploration_penalty_multiplier * (visit_count ** 0.7)
            
            # Exploration bonus
            exploration_bonus = self.exploration_bonus_weight * (1 / (visit_count ** 0.5))
            
            reward += exploration_bonus + exploration_penalty
        
        return reward
    
    def choose_action(self, state):
        """Select action using epsilon-greedy policy with bias towards unexplored areas"""
        # Ensure state has an entry in Q-table
        if state not in self.q_table:
            self.q_table[state] = {}
            
        # Select random action (exploration)
        if random.random() < self.exploration_rate:
            return random.choice(self.actions)
        
        # Select best action (exploitation)
        if not self.q_table[state]:
            return random.choice(self.actions)
        
        # Bias towards less explored locations
        grid_location = (state[0], state[1])
        
        # If current location is one of the least visited, prioritize it
        sorted_locations = sorted(self.grid_exploration_count.items(), key=lambda x: x[1])
        least_visited_locations = [loc for loc, _ in sorted_locations[:3]]
        
        if grid_location in least_visited_locations:
            # Increase probability of choosing an action that keeps us in this location
            actions_in_state = [action for action in self.q_table[state].keys()]
            return max(actions_in_state, key=lambda a: self.q_table[state].get(a, 0) + random.random())
        
        # Normal action selection
        return max(self.q_table[state], key=self.q_table[state].get)
        
    def optimize(self, drones, detected_animals, detected_poachers):
        drone_actions = {}
        self.episode_step += 1
        
        # Decay exploration periodically
        if self.episode_step >= 100:
            self.episode_step = 0
            self.exploration_rate = max(
                self.min_exploration_rate, 
                self.exploration_rate * self.exploration_decay
            )
        
        for drone in drones:
            # Check if drone can catch any poachers - with probability based on distance
            if isinstance(drone.active_state, DroneDeepSearch):  # Only catch in low altitude
                for poacher in detected_poachers:
                    distance = drone.position.distance_to(poacher.position)
                    
                    # Calculate catch probability - highest when very close, decreasing as distance increases
                    # The closer to the threshold, the lower the probability
                    if distance < self.catch_threshold:
                        catch_probability = 1.0 - (distance / self.catch_threshold) * 0.8
                        
                        # Roll the dice to see if catch succeeds
                        if random.random() < catch_probability:
                            # Post the caught poacher event
                            catch_event = pygame.event.Event(DRONE_CAUGHT_POACHER, {'poacher': poacher})
                            pygame.event.post(catch_event)
                            # Add extra reward for catching a poacher
                            if drone.name in self.previous_states:
                                self.rewards_history.append(10)  # Big reward for catch
                            break
            
            # Rest of the method remains unchanged
            # Get current state
            current_state = self.discretize_state(drone, detected_animals, detected_poachers)
            
            # Process previous experience if available
            if drone.name in self.previous_states:
                prev_state = self.previous_states[drone.name]
                prev_action = self.previous_actions[drone.name]
                
                # Calculate reward
                reward = self.calculate_reward(drone, detected_animals, detected_poachers)
                
                # Store experience and update Q-table immediately
                self.replay_buffer.append((prev_state, prev_action, reward, current_state))
                self.update_q_table()
                
                # Track rewards
                self.rewards_history.append(reward)
            
            # Choose next action
            action = self.choose_action(current_state)
            
            # Store state and action for next update
            self.previous_states[drone.name] = current_state
            self.previous_actions[drone.name] = action
            
            # Convert action to drone parameters
            drone_actions[drone] = self.action_to_params(action, drone)
            
        return drone_actions
    
    def update_q_table(self):
        """Simple Q-learning update"""
        if not self.replay_buffer:
            return
            
        # Just use the most recent experience
        experience = self.replay_buffer[-1]
        state, action, reward, next_state = experience
        
        # Initialize Q-values if needed
        if state not in self.q_table:
            self.q_table[state] = {}
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0.0
                
        # Get max Q-value for next state
        if next_state not in self.q_table or not self.q_table[next_state]:
            next_max_q = 0
        else:
            next_max_q = max(self.q_table[next_state].values())
                
        # Update Q-value using Q-learning formula
        current_q = self.q_table[state][action]
        self.q_table[state][action] = current_q + self.learning_rate * (
            reward + self.discount_factor * next_max_q - current_q
        )

    def action_to_params(self, action, drone):
        """Convert discrete action to continuous parameters"""
        direction = pygame.Vector2(action[0], action[1])
        if direction.length() > 0:
            direction.normalize()
            
        new_state = None
        if action[2] == 1 and not isinstance(drone.active_state, DroneDeepSearch):
            new_state = DroneDeepSearch()
        elif action[2] == 0 and not isinstance(drone.active_state, DroneFastSearch):
            new_state = DroneFastSearch()
            
        return {
            'state': new_state,
            'direction': direction,
            'speed_modifier': action[3]  # Use the speed from the action
        }

    def get_performance_metrics(self):
        """Return basic performance metrics for monitoring"""
        if not self.rewards_history:
            return {
                "avg_reward": 0, 
                "exploration_rate": self.exploration_rate,
                "unique_grid_locations": len(self.grid_exploration_count),
                "grid_configuration": {
                    "map_width": self.map_width,
                    "map_height": self.map_height,
                    "x_divisions": self.grid_x_divisions,
                    "y_divisions": self.grid_y_divisions
                }
            }
            
        # Calculate average reward over last 50 steps
        recent_rewards = self.rewards_history[-50:] if len(self.rewards_history) > 50 else self.rewards_history
        avg_reward = sum(recent_rewards) / len(recent_rewards)
        
        return {
            "avg_reward": avg_reward,
            "exploration_rate": self.exploration_rate,
            "q_table_size": len(self.q_table),
            "unique_grid_locations": len(self.grid_exploration_count),
            "grid_exploration": dict(sorted(self.grid_exploration_count.items(), key=lambda x: x[1], reverse=True)[:5]),
            "least_visited_locations": dict(sorted(self.grid_exploration_count.items(), key=lambda x: x[1])[:5]),
            "grid_configuration": {
                "map_width": self.map_width,
                "map_height": self.map_height,
                "x_divisions": self.grid_x_divisions,
                "y_divisions": self.grid_y_divisions
            }
        }
    
    def save_model(self, filename='rl_model.pkl'):
        """Save the Q-table and learning parameters to a file"""
        model_data = {
            'q_table': self.q_table,
            'exploration_rate': self.exploration_rate,
            'grid_exploration_count': self.grid_exploration_count,
            'rewards_history': self.rewards_history,
            'episode_step': self.episode_step
        }
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        # print(f"Model saved to {filename}")
    
    def load_model(self, filename='rl_model.pkl'):
        """Load the Q-table and learning parameters from a file"""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
                self.q_table = model_data['q_table']
                self.exploration_rate = model_data['exploration_rate']
                self.grid_exploration_count = model_data['grid_exploration_count']
                self.rewards_history = model_data['rewards_history']
                self.episode_step = model_data['episode_step']
            # print(f"Model loaded from {filename}")
            return True
        return False