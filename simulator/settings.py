

# Define parameters for game environment and simulation

# Pygame Settings
GAME_WIDTH = 800
PANEL_WIDTH = 300
WIDTH = GAME_WIDTH + PANEL_WIDTH
HEIGHT = 600
FPS = 10

# Colors
DRONE_COLOR = (0, 0, 255)  # Blue
POACHER_COLOR = (255, 0, 0)  # Red
ANIMAL_COLOR = (0, 255, 0)  # Green


# Simulation Parameters
# Drone Parameters
DRONE_SPEED = 10
DRONE_SCAN_RANGE = 200
DRONE_CATCH_RANGE = 25

# Poacher Parameters
POACHER_SPEED = 5
POACHER_SCAN_RANGE = 100
POACHER_ATTACK_RANGE = 50
POACHER_ATTACK_DURATION = 30
POACHER_KILL_RANGE = 10
POACHER_ATTACK_DAMAGE = 40

# Animal Parameters
ANIMAL_SPEED = 5
ANIMAL_SCAN_RANGE = 100
ANIMAL_THREAT_RANGE = 50
ANIMAL_SEPARATION = 20
ANIMAL_HEALTH = 100
