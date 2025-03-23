from abc import ABC, abstractmethod
import pygame
from states import DroneHighAltitude, DroneLowAltitude

class DroneOptimizer(ABC):
    """
    Abstract base class for drone optimization algorithms.
    Any optimizer must implement the optimize method.
    """
    
    @abstractmethod
    def optimize(self, drones, detected_animals, detected_poachers):
        """
        Determine optimal drone actions based on current simulation state.
        
        Args:
            drones: pygame.sprite.Group - All drone sprites
            detected_animals: pygame.sprite.Group - All detected animal sprites
            detected_poachers: pygame.sprite.Group - All detected poacher sprites
            
        Returns:
            dict: Dictionary mapping drone objects to their action parameters:
                {
                    drone_object: {
                        'state': DroneState object or None,
                        'direction': pygame.Vector2 position vector,
                        'speed_modifier': float, 0.0 <= speed_modifier <= 1.0
                    }
                }
        """
        pass