# defines the high-level state representation in the simulation. 

import pygame

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
    
    def check_transition(self, state):
        """
        Check if the agent can transition to another state, to be implemented by subclasses
        Returns:
            bool: True if transition is possible, False otherwise
        """
        pass


# Drone states
class DroneHighAltitude(State):
    def __init__(self):
        super().__init__()
        
    def action(self):
        # High-Level Search for Animals
        if self.agent:
            # Perform scan for animals
            self.agent.scan_surroundings("Animal")
            
            # Get instructions for movement from controller
            direction = self.agent.controller.get_direction()
            
            # Move agent in the given direction
            self.agent.move(direction)
        return

    def check_transition(self, state='LowAltitude'):
        # Check if agent can transition to LowAltitude state -- true
        if state == 'LowAltitude':
            return True
        return False


class DroneLowAltitude(State):
    def __init__(self):
        super().__init__("low_altitude", speed_modifier=0.7, detection_range=50, detection_accuracy=0.9)
        
    def action(self):
        # Low-Level Search for Poachers 
        if self.agent:
            # Perform scan for poachers
            self.agent.scan_surroundings("Poacher")
            
            # Get instructions for movement from controller
            direction = self.agent.controller.get_direction()
            
            # Move agent in the given direction
            self.agent.move(direction)
        return

    def check_transition(self, state='HighAltitude'):
        # Check if agent can transition to HighAltitude state -- true
        if state == 'HighAltitude':
            return True
        return False


# Animal states
class AnimalIdle(State):
    def __init__(self):
        super().__init__("idle", speed_modifier=0.3)
        self.herd_cohesion=0.8
        
    def action(self):
        # Random grazing movement, tendency to stay with herd,
        if self.agent:
            # Perform scan for animals to stay with herd
            self.agent.scan_surroundings("Animals")
            
            # Set random direction but with tendency to stay with herd
            direction = pygame.Vector2(pygame.math.Vector2(0.2, 0.2).normalize() * self.parameters["speed_modifier"])
            
            # Move agent in the given direction
            self.agent.move(direction)
        return
            

class AnimalFleeing(State):
    def __init__(self):
        super().__init__("fleeing", speed_modifier=1.5)
        self.herd_cohesion = 0

    def action(self):
        # Fast movement away from threat
        if self.agent and hasattr(self.agent, 'threat_position'):
            flee_dir = self.agent.position - self.agent.threat_position
            return flee_dir.normalize() * self.parameters["speed_modifier"]
        return pygame.Vector2(0, 0)
    
    # # As inspiration:
    # def flee(self, threat_pos):
    #     """Move away from poacher - legacy method"""
    #     self.update_threat(threat_pos)
    #     self.update()

    # def flee_old(self, threat_pos):
    #     """Move away from poacher."""
    #     direction = self.position - pygame.Vector2(threat_pos)
    #     direction = direction.normalize() if direction.length() > 0 else direction
    #     self.position += direction * self.speed
    #     self.rect.center = self.position
    
    def check_transition(self, state='Idle'):
        # Check if agent can transition back to Idle state
        # if threat is far enough away
        # Transition to fleeing state triggered by event and not self-check
        if self.agent and hasattr(self.agent, 'threat_position'):
            distance = self.agent.position.distance_to(self.agent.threat_position)
            if distance > 150:
                return True
        return False


class AnimalDead(State):
    def __init__(self):
        super().__init__("dead", speed_modifier=0)
        
    def action(self):
        # Terminal state, Animal exists further but doesn't move or act
        return
    
    def check_transition(self, state='Idle'):
        # Agent can't transition to any other state
        return False


# Poacher states
class PoacherHunting(State):
    def __init__(self):
        super().__init__("hunting", speed_modifier=0.8, stealth=0.7)
        
    def action(self):
        # Stalking animals, trying to be stealthy
        if self.agent and hasattr(self.agent, 'target'):
            hunt_dir = self.agent.target.position - self.agent.position
            return hunt_dir.normalize() * self.parameters["speed_modifier"]
        return pygame.Vector2(0, 0)
    
    # As Inspiration:
        # def hunt(self, animals):
        # """Find nearest animal and move toward it"""
        # if animals:
        #     # Find the nearest animal
        #     self.target = min(animals, key=lambda a: self.position.distance_to(a.position))
            
        #     # If close enough, switch to attacking state
        #     distance = self.position.distance_to(self.target.position)
        #     if distance < self.attack_range and isinstance(self.state, PoacherHunting):
        #         self.set_state(self.attacking_state)
        #     elif distance >= self.attack_range and isinstance(self.state, PoacherAttacking):
        #         self.set_state(self.hunting_state)
            
        #     self.update()

    
    def check_transition(self, state='Attacking'):
        # Check if agent can transition to Attacking state
        # Transition to caught state triggered by event and not self-check
        if self.agent and hasattr(self.agent, 'target'):
            distance = self.agent.position.distance_to(self.agent.target.position)
            if distance < self.agent.attack_range:
                return True
        return False


class PoacherAttacking(State):
    def __init__(self):
        super().__init__("Attacking", speed_modifier=1.2, stealth=0.1)
        self.attack_time = 0
        
    def action(self):
        # Direct attack on animal
        self.attack_time += 1
        if self.agent and hasattr(self.agent, 'target'):
            attack_dir = self.agent.target.position - self.agent.position
            return attack_dir.normalize() * self.parameters["speed_modifier"]
        return pygame.Vector2(0, 0)
    
    # As Inspiration:
        # def kill(self, animal):
        # """Attack and possibly kill the animal"""
        # # Implement kill logic - for example:
        # if self.position.distance_to(animal.position) < 10:
        #     # Add kill logic here
        #     pass
    
    def check_transition(self, state='Hunting'):
        # Check if agent has to transition back to Hunting state
        # Transition to caught state triggered by event and not self-check
        if self.agent and hasattr(self.agent, 'target'):
            distance = self.agent.position.distance_to(self.agent.target.position)
            # If target is out of range or attack duration is over
            if distance >= self.agent.attack_range or self.attack_time >= self.agent.attack_duration:
                return True
            # If target is dead
            if self.agent.target.state == 'Dead':
                return True
        return False

    
class PoacherCaught(State):
    def __init__(self):
        super().__init__("caught", speed_modifier=0)
        
    def action(self):
        # Terminal state, Poacher exists further but doesn't move or act
        return
    
    def check_transition(self, state='Hunting'):
        # Agent can't transition to any other state
        return False