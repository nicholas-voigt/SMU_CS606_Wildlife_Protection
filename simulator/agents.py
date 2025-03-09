# DEFINES THE BASE AGENT CLASS AND IT'S SUBCLASSES

import pygame
import random
from simulator.settings import WIDTH, HEIGHT, DRONE_SPEED, POACHER_SPEED, ANIMAL_SPEED

class Agent(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed):
        super().__init__()
        self.image = pygame.Surface((10, 10))  # Small square representation
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed
        self.position = pygame.Vector2(x, y)  # Continuous position

    def move_random(self):
        """Random movement for animals/poachers."""
        direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        direction = direction.normalize() if direction.length() > 0 else direction
        self.position += direction * self.speed
        self.rect.center = self.position  # Update pygame sprite position

class Drone(Agent):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 0, 255), DRONE_SPEED)  # Blue
        self.state = "high_altitude"  # Search states

    def search(self):
        """Implement drone search logic (e.g., move in patterns)."""
        self.move_random()  # Placeholder movement

class Animal(Agent):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 255, 0), ANIMAL_SPEED)  # Green

    def flee(self, threat_pos):
        """Move away from poacher."""
        direction = self.position - pygame.Vector2(threat_pos)
        direction = direction.normalize() if direction.length() > 0 else direction
        self.position += direction * self.speed
        self.rect.center = self.position

class Poacher(Agent):
    def __init__(self, x, y):
        super().__init__(x, y, (255, 0, 0), POACHER_SPEED)  # Red

    def hunt(self, animals):
        """Move towards nearest animal."""
        if animals:
            target = min(animals, key=lambda a: self.position.distance_to(a.position))
            direction = pygame.Vector2(target.position - self.position).normalize()
            self.position += direction * self.speed
            self.rect.center = self.position
    
    def kill(self, animal):
        """Kill the Animal"""
