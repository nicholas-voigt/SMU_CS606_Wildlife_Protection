

# Define parameters for game environment and simulation

# Pygame Settings
GAME_WIDTH = 800
PANEL_WIDTH = 300
WIDTH = GAME_WIDTH + PANEL_WIDTH
HEIGHT = 600
FPS = 60

# Colors
DRONE_COLOR = (0, 0, 255)  # Blue
POACHER_COLOR = (255, 0, 0)  # Red
ANIMAL_COLOR = (0, 255, 0)  # Green


# Simulation Parameters
# Speeds
DRONE_SPEED = 20
POACHER_SPEED = 10
ANIMAL_SPEED = 5

# Scan Ranges
DRONE_SCAN_RANGE = 200

POACHER_SCAN_RANGE = 150
POACHER_ATTACK_RANGE = 50
POACHER_ATTACK_DURATION = 30
POACHER_KILL_RANGE = 10

ANIMAL_SCAN_RANGE = 100

# Additional Parameters
ANIMAL_THREAT_RANGE = 50

ANIMAL_HOTSPOTS = [
    (200, 300),  # Water hole
    (600, 400),  # Feeding area
    (300, 150),  # Forest clearing
]
