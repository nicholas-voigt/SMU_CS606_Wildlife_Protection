# defines the simulation environment
# handles rendering

import pygame
from settings import WIDTH, HEIGHT

def render_info_panel(screen, drones, animals, poachers, panel_rect, font, title_font):
    """Render the information panel showing agent states and details"""
    # Fill panel background with a slightly lighter color
    pygame.draw.rect(screen, (50, 50, 50), panel_rect)
    pygame.draw.line(screen, (100, 100, 100), (panel_rect.left, 0), (panel_rect.left, HEIGHT), 2)
    
    # Panel title
    title = title_font.render("Agent Information", True, (255, 255, 255))
    screen.blit(title, (panel_rect.left + 10, 10))
    
    y_offset = 50  # Starting y position for text
    
    # Display drone information
    drone_title = title_font.render("Drones:", True, (100, 200, 255))
    screen.blit(drone_title, (panel_rect.left + 10, y_offset))
    y_offset += 30
    
    if len(drones) == 0:
        text = font.render("No drones active", True, (200, 200, 200))
        screen.blit(text, (panel_rect.left + 20, y_offset))
        y_offset += 25
    else:
        for drone in drones:
            name_text = font.render(f"Name: {drone.name}", True, (255, 255, 255))
            state_text = font.render(f"State: {drone.active_state.__class__.__name__}", True, (255, 255, 255))
            screen.blit(name_text, (panel_rect.left + 20, y_offset))
            screen.blit(state_text, (panel_rect.left + 20, y_offset + 20))
            y_offset += 50
    
    y_offset += 10
    
    # Display animal information
    animal_title = title_font.render("Animals:", True, (100, 255, 100))
    screen.blit(animal_title, (panel_rect.left + 10, y_offset))
    y_offset += 30
    
    for animal in animals:
        name_text = font.render(f"Name: {animal.name}", True, (255, 255, 255))
        state_text = font.render(f"State: {animal.active_state.__class__.__name__}", True, (255, 255, 255))
        threat_text = font.render(f"Threat: {'Yes' if hasattr(animal, 'threat') and animal.threat else 'None'}", True, (255, 255, 255))
        screen.blit(name_text, (panel_rect.left + 20, y_offset))
        screen.blit(state_text, (panel_rect.left + 20, y_offset + 20))
        screen.blit(threat_text, (panel_rect.left + 20, y_offset + 40))
        y_offset += 70
    
    y_offset += 10
    
    # Display poacher information
    poacher_title = title_font.render("Poachers:", True, (255, 100, 100))
    screen.blit(poacher_title, (panel_rect.left + 10, y_offset))
    y_offset += 30
    
    for poacher in poachers:
        name_text = font.render(f"Name: {poacher.name}", True, (255, 255, 255))
        state_text = font.render(f"State: {poacher.active_state.__class__.__name__}", True, (255, 255, 255))
        target_text = font.render(f"Target: {'Yes' if hasattr(poacher, 'target') and poacher.target else 'None'}", True, (255, 255, 255))
        screen.blit(name_text, (panel_rect.left + 20, y_offset))
        screen.blit(state_text, (panel_rect.left + 20, y_offset + 20))
        screen.blit(target_text, (panel_rect.left + 20, y_offset + 40))
        y_offset += 70