# Definition of pygame events

import pygame

# Define custom events for communication between agents
# 1. Animal has been killed by a poacher (event data: animal, poacher)
ANIMAL_KILLED = pygame.USEREVENT + 1
# 2. Drone has detected a poacher
DRONE_DETECTED_POACHER = pygame.USEREVENT + 2
# 3. Drone has caught a poacher
DRONE_CAUGHT_POACHER = pygame.USEREVENT + 3
# 4. Drone has detected an animal
DRONE_DETECTED_ANIMAL = pygame.USEREVENT + 4
# 5. Drone has lost track of poacher
DRONE_LOST_POACHER = pygame.USEREVENT + 5
# 6. Drone has lost track of animal
DRONE_LOST_ANIMAL = pygame.USEREVENT + 6
# 7. Poacher attacks an animal (event data: animal, poacher)
POACHER_ATTACK_ANIMAL = pygame.USEREVENT + 7
    
