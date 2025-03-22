# Define parameters for game environment and simulation

from simulator.states import *
from simulator.agents import Drone, Animal, Poacher


# Simulation Instance
drones_to_deploy = [Drone(100, 100)]
poachers_to_deploy = [Animal(400, 300), Animal(420, 320)]
animals_to_deploy = [Poacher(600, 400)]

# Pygame Settings
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
DRONE_COLOR = (0, 0, 255)  # Blue
POACHER_COLOR = (255, 0, 0)  # Red
ANIMAL_COLOR = (0, 255, 0)  # Green


# Simulation Parameters
# Speeds
DRONE_SPEED = 3
POACHER_SPEED = 1.5
ANIMAL_SPEED = 2

# Scan Ranges
DRONE_SCAN_RANGE = 150
POACHER_SCAN_RANGE = 100
ANIMAL_SCAN_RANGE = 50

# States
DRONE_STATES = {
    'HighAltitude': DroneHighAltitude(), 
    'LowAltitude': DroneLowAltitude()
    }
POACHER_STATES = {
    'Hunting': PoacherHunting(),
    'Attacking': PoacherAttacking(),
    'Caught': PoacherCaught()
    }
ANIMAL_STATES = {
    'Idle': AnimalIdle(),
    'Fleeing': AnimalFleeing(),
    'Dead': AnimalDead()
    }
