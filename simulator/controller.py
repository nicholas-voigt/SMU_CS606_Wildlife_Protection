
import pygame
import random

class Controller():
    def __init__(self, agent):
        self.agent = agent
        pass

    def get_direction(self):
        """
        Get the direction the agent should move in.
        Returns:
            direction: pygame.Vector2, direction to move in
        """
        pass

    def evaluate_state_transition(self):
        """
        Evaluate if the agent (drone) should change the state.
        Returns:
            transition: bool, True if the agent should transition to a new state
        """
        pass
