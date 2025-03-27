# defines the simulation environment
# handles rendering

import pygame
from settings import WIDTH, HEIGHT

def render_info_panel(screen, drones, animals, poachers, event_log, panel_rect):
    """Render the information panel showing agent states and details"""
    # Fill panel background with a slightly lighter color
    pygame.draw.rect(screen, (50, 50, 50), panel_rect)
    pygame.draw.line(screen, (100, 100, 100), (panel_rect.left, 0), (panel_rect.left, HEIGHT), 2)
    # Set fonts
    font = pygame.font.SysFont('Arial', 16)
    title_font = pygame.font.SysFont('Arial', 20, bold=True)

    # Panel title
    title = title_font.render("Agent Information", True, (255, 255, 255))
    screen.blit(title, (panel_rect.left + 10, 10))
    
    y_offset = 50  # Starting y position for text
    table_width = panel_rect.width - 20
    
    # Helper function to render a table
    def render_table(title_text, headers, data, row_height=25):
        nonlocal y_offset
        
        # Render section title
        section_title = title_font.render(title_text, True, (255, 255, 255))
        screen.blit(section_title, (panel_rect.left + 10, y_offset))
        y_offset += 30
        
        if not data:
            empty_text = font.render(f"No {title_text.lower()} active", True, (200, 200, 200))
            screen.blit(empty_text, (panel_rect.left + 20, y_offset))
            y_offset += 30
            return
        
        # Calculate column widths
        col_widths = [table_width // len(headers)] * len(headers)

        # Render headers
        for i, header in enumerate(headers):
            x_pos = panel_rect.left + 10 + sum(col_widths[:i])
            header_text = font.render(header, True, (200, 200, 200))
            screen.blit(header_text, (x_pos, y_offset))
        
        y_offset += row_height
        
        # Draw header separator line
        pygame.draw.line(screen, (150, 150, 150), 
                            (panel_rect.left + 10, y_offset - 5), 
                            (panel_rect.left + 10 + table_width, y_offset - 5), 1)
        
        # Render data rows
        for row_data in data:
            for i, cell in enumerate(row_data):
                x_pos = panel_rect.left + 10 + sum(col_widths[:i])
                cell_text = font.render(str(cell), True, (255, 255, 255))
                screen.blit(cell_text, (x_pos, y_offset))
            y_offset += row_height
        
        y_offset += 15  # Add space after table

    
    # Render drone table
    drone_data = [(drone.name, drone.active_state.__class__.__name__) for drone in drones]
    render_table("Drones", ["Name", "State"], drone_data)
    
    # Render animal table
    animal_data = [(animal.name, 
                   animal.active_state.__class__.__name__,
                   'Yes' if hasattr(animal, 'threat') and animal.threat else 'None') 
                  for animal in animals]
    render_table("Animals", ["Name", "State", "Threat"], animal_data)
    
    # Render poacher table
    poacher_data = [(poacher.name,
                    poacher.active_state.__class__.__name__,
                    'Yes' if hasattr(poacher, 'target') and poacher.target else 'None')
                   for poacher in poachers]
    render_table("Poachers", ["Name", "State", "Target"], poacher_data)

        
    # Add event log section
    if event_log:
        y_offset += 20  # Add space between previous content and event log
        
        # Event log title
        title_text = title_font.render("Event log", True, (255, 255, 255))
        screen.blit(title_text, (panel_rect.x + 10, panel_rect.y + y_offset))
        y_offset += 30
        
        # Display events (newest at the top)
        for event_text, timestamp in list(event_log)[-10:]:  # Show last 10 events
            time_str = f"{timestamp//1000:02d}:{(timestamp%1000)//10:02d}"  # Format as MM:SS
            log_entry = font.render(f"{time_str} - {event_text}", True, (200, 200, 200))
            screen.blit(log_entry, (panel_rect.x + 10, panel_rect.y + y_offset))
            y_offset += 20


def end_simulation(screen, type, info):
    """Render the end of simulation screen with the given message"""

    # Clear previous events to prevent stacking
    pygame.event.clear()

    # Create a semi-transparent dark overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    # Rendering instructions
    msg_font = pygame.font.SysFont('Arial', 32, bold=True)
    instr_font = pygame.font.SysFont('Arial', 24)

    if type == "Victory":
        # Display victory message in center of screen
        victory_text = msg_font.render("VICTORY! All poachers have been caught", True, (255, 255, 255))
        victory_rect = victory_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(victory_text, victory_rect)

    elif type == "Defeat":
        # Display defeat message in center of screen
        defeat_text = msg_font.render("DEFEAT! All animals have been killed", True, (255, 0, 0))
        defeat_rect = defeat_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(defeat_text, defeat_rect)

    # Add instruction to continue
    insights_text = instr_font.render(f"Poachers caught: {info['poachers'] * 100}%, Animals still alive: {info['animals'] * 100}%, Time taken: {pygame.time.get_ticks()}ms", True, (200, 200, 200))
    insights_rect = insights_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
    screen.blit(insights_text, insights_rect)   
    continue_text = instr_font.render("Press any key to exit", True, (200, 200, 200))
    continue_rect = continue_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
    screen.blit(continue_text, continue_rect)   
    
    pygame.display.flip()
    
    # Wait for key press
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # Post a QUIT event to be handled by the main game loop
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                waiting = False
    return