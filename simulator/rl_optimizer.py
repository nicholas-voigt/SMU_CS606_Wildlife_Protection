import pygame
import random
import numpy as np
from collections import deque
from optimizer import DroneOptimizer
from states import DroneHighAltitude, DroneLowAltitude
from events import DRONE_CAUGHT_POACHER

class RLOptimizer(DroneOptimizer):
    """Reinforcement Learning Optimizer for drone control"""
    
    def __init__(self, learning_rate=0.1, 
                 discount_factor=0.95, 
                 initial_exploration_rate=1.0,
                 min_exploration_rate=0.1, 
                 exploration_decay=0.995,
                 catch_threshold=20):  # Added catch threshold
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = initial_exploration_rate
        self.min_exploration_rate = min_exploration_rate
        self.exploration_decay = exploration_decay
        self.catch_threshold = catch_threshold  # Distance threshold for catching poachers
        self.q_table = {}  # {state_key: {action_key: q_value}}
        
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
        """Simplified state discretization"""
        # Drone position in a coarser grid (4×4)
        grid_x = min(3, max(0, int(drone.position.x / (800/4))))
        grid_y = min(3, max(0, int(drone.position.y / (600/4))))
        
        # Binary detection flags (detected or not)
        animals_detected = min(1, len(detected_animals))
        poachers_detected = min(1, len(detected_poachers))
        
        # Altitude state
        altitude = 1 if isinstance(drone.active_state, DroneLowAltitude) else 0
        
        # Create state key
        state_key = (grid_x, grid_y, animals_detected, poachers_detected, altitude)
        
        return state_key
    
    def calculate_reward(self, drone, detected_animals, detected_poachers):
        """Simplified reward calculation"""
        reward = 0
        
        # Binary rewards for detection
        if detected_animals:
            reward += 2
        
        if detected_poachers:
            reward += 5
            
            # Bonus for being close to poachers
            for poacher in detected_poachers:
                if drone.position.distance_to(poacher.position) < 20:
                    reward += 3
                    break
        
        # Simple state penalty
        if detected_poachers and not isinstance(drone.active_state, DroneLowAltitude):
            reward -= 2
        elif not detected_animals and not detected_poachers and not isinstance(drone.active_state, DroneHighAltitude):
            reward -= 1
        
        return reward
    
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
            'speed_modifier': action[3]  # Use the speed from the action
        }
    
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
    
    def choose_action(self, state):
        """Select action using epsilon-greedy policy"""
        # Ensure state has an entry in Q-table
        if state not in self.q_table:
            self.q_table[state] = {}
            
        # Select random action (exploration)
        if random.random() < self.exploration_rate:
            return random.choice(self.actions)
        
        # Select best action (exploitation)
        if not self.q_table[state]:
            return random.choice(self.actions)
        else:
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
            if isinstance(drone.active_state, DroneLowAltitude):  # Only catch in low altitude
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
            
            # Process previous experience if availables
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
        
    def get_performance_metrics(self):
        """Return basic performance metrics for monitoring"""
        if not self.rewards_history:
            return {"avg_reward": 0, "exploration_rate": self.exploration_rate}
            
        # Calculate average reward over last 50 steps
        recent_rewards = self.rewards_history[-50:] if len(self.rewards_history) > 50 else self.rewards_history
        avg_reward = sum(recent_rewards) / len(recent_rewards)
        
        return {
            "avg_reward": avg_reward,
            "exploration_rate": self.exploration_rate,
            "q_table_size": len(self.q_table)
        }