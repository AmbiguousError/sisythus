import pygame
import math
import sys
import random

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (Shades of Black/Gray)
BLACK = (10, 10, 10)
# Background Layer Colors (Darkest furthest away)
FAR_BG_COLOR = (25, 25, 25)
MID_BG_COLOR = (40, 40, 40)
NEAR_BG_COLOR = (55, 55, 55) # Was DARK_GRAY2
# Main Hill Color
HILL_COLOR = (75, 75, 75) # Slightly lighter hill for more contrast
# Boulder/Sisyphus Colors
GRAY1 = (100, 100, 100) # Adjusted boulder color slightly
GRAY2 = (140, 140, 140) # Adjusted boulder shade slightly
LIGHT_GRAY = (170, 170, 170) # Sisyphus color
WHITE = (220, 220, 220)

# --- Updated Physics Parameters ---
GRAVITY_BASE = 0.15
PUSH_FORCE = 0.16
FRICTION = 0.985
SLOPE_STEEPNESS_FACTOR = 0.01 # This factor remains high
BOULDER_RADIUS = 80
SISYPHUS_WIDTH = 20
SISYPHUS_HEIGHT = 50

# Input Handling
PUSH_COOLDOWN = 100
MIN_PUSH_INTERVAL = 50

# --- Parallax Background Settings ---
# Further increased parallax factors for even faster scrolling
BG_LAYERS_PROPERTIES = [
    # Furthest Layer
    {'count': 15, 'parallax': 0.5, 'color': FAR_BG_COLOR, 'min_h': 80, 'max_h': 180, 'min_w': 30, 'max_w': 60, 'y_variation': 20}, # Was 0.3
    # Mid Layer
    {'count': 12, 'parallax': 0.75, 'color': MID_BG_COLOR, 'min_h': 60, 'max_h': 150, 'min_w': 25, 'max_w': 50, 'y_variation': 15}, # Was 0.6
    # Near Layer (replacing old rocks)
    {'count': 10, 'parallax': 0.95, 'color': NEAR_BG_COLOR, 'min_h': 50, 'max_h': 120, 'min_w': 20, 'max_w': 40, 'y_variation': 10}, # Was 0.85
]
# How far out to initially distribute background elements horizontally
BG_WORLD_WIDTH_FACTOR = 3.0 # Spread elements over 3 screen widths initially

# --- Game Setup ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("The Trial of Sisyphus")
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 74)
font_medium = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 36)
font_extra_small = pygame.font.Font(None, 28)

# --- Hill Function ---
HILL_START_Y = SCREEN_HEIGHT * 0.8
def get_hill_y(x):
    """Calculates the y-coordinate of the hill surface at horizontal position x."""
    effective_x = max(0, x)
    return HILL_START_Y - SLOPE_STEEPNESS_FACTOR * (effective_x ** 1.3)

def get_hill_angle(x):
    """Calculates the angle of the hill (in radians) at horizontal position x."""
    delta_x = 2
    y1 = get_hill_y(x)
    y2 = get_hill_y(x + delta_x)
    angle = math.atan2(-(y2 - y1), delta_x)
    max_angle = math.radians(88)
    return max(-max_angle, min(max_angle, angle))

# --- Game State Variables ---
INITIAL_BOULDER_X = 150.0
background_layers = []

def reset_game():
    """Resets the game to its initial state, including background elements."""
    global boulder_x, boulder_y, boulder_velocity_along_slope
    global sisyphus_x, sisyphus_y
    global camera_offset_x
    global max_x_reached, current_score
    global last_push_key, last_push_time, last_key_time
    global game_state
    global background_layers

    boulder_x = INITIAL_BOULDER_X
    boulder_y = get_hill_y(boulder_x)
    boulder_velocity_along_slope = 0.0
    sisyphus_x = boulder_x - BOULDER_RADIUS - SISYPHUS_WIDTH / 2
    sisyphus_y = boulder_y

    camera_offset_x = boulder_x - SCREEN_WIDTH / 2
    max_x_reached = boulder_x
    current_score = 0

    last_push_key = None
    last_push_time = 0
    last_key_time = 0

    game_state = "start_screen"

    background_layers = []
    initial_world_width = SCREEN_WIDTH * BG_WORLD_WIDTH_FACTOR
    for layer_props in BG_LAYERS_PROPERTIES: # Uses the updated BG_LAYERS_PROPERTIES
        layer_elements = []
        for i in range(layer_props['count']):
            element_x = random.uniform(-initial_world_width / 2, initial_world_width / 2) + INITIAL_BOULDER_X
            element_h = random.randint(layer_props['min_h'], layer_props['max_h'])
            element_w = random.randint(layer_props['min_w'], layer_props['max_w'])
            element_type = random.choice(['stalagmite', 'stalactite'])
            base_y = get_hill_y(element_x) + random.uniform(-layer_props['y_variation'], layer_props['y_variation'])

            layer_elements.append({
                'initial_x': element_x,
                'height': element_h,
                'width': element_w,
                'type': element_type,
                'base_y': base_y,
                'parallax': layer_props['parallax'], # This will now use the new faster values
                'color': layer_props['color']
            })
        background_layers.append(layer_elements)

reset_game()

def render_text_multiline(text, font, color, surface, x, start_y, line_spacing):
    lines = text.split('\n')
    current_y = start_y
    for line in lines:
        text_surface = font.render(line, True, color)
        text_rect = text_surface.get_rect(center=(x, current_y))
        surface.blit(text_surface, text_rect)
        current_y += text_surface.get_height() + line_spacing

running = True
while running:
    time_now = pygame.time.get_ticks()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_state == "start_screen":
                if event.key == pygame.K_SPACE: game_state = "ready_to_play"
            elif game_state == "ready_to_play":
                if event.key == pygame.K_z or event.key == pygame.K_x:
                    game_state = "playing"
                    current_key = 'z' if event.key == pygame.K_z else 'x'
                    boulder_velocity_along_slope += PUSH_FORCE
                    last_push_key = current_key
                    last_push_time = time_now
                    last_key_time = time_now
            elif game_state == "playing":
                current_key = None
                if event.key == pygame.K_z: current_key = 'z'
                elif event.key == pygame.K_x: current_key = 'x'
                if current_key and current_key != last_push_key and (time_now - last_key_time > MIN_PUSH_INTERVAL):
                    boulder_velocity_along_slope += PUSH_FORCE
                    last_push_key = current_key
                    last_push_time = time_now
                    last_key_time = time_now
                elif current_key:
                    last_key_time = time_now
            elif game_state == "game_over":
                 if event.key == pygame.K_SPACE: reset_game()

    if game_state == "playing":
        current_hill_angle = get_hill_angle(boulder_x)
        gravity_effect = GRAVITY_BASE + abs(math.sin(current_hill_angle)) * 0.20
        gravity_force_along_slope = gravity_effect * math.sin(current_hill_angle)

        boulder_velocity_along_slope -= gravity_force_along_slope
        boulder_velocity_along_slope *= FRICTION

        delta_x = boulder_velocity_along_slope * math.cos(current_hill_angle)
        boulder_x += delta_x
        boulder_y = get_hill_y(boulder_x)

        offset_distance = BOULDER_RADIUS + SISYPHUS_WIDTH * 0.3
        sisyphus_x = boulder_x - offset_distance * math.cos(current_hill_angle)
        sisyphus_y = boulder_y + offset_distance * math.sin(current_hill_angle)

        max_x_reached = max(max_x_reached, boulder_x)
        current_score = int(max(0, max_x_reached - INITIAL_BOULDER_X))

        if boulder_velocity_along_slope < 0.01 and boulder_x > INITIAL_BOULDER_X + 5:
            game_state = "game_over"

        target_camera_offset = boulder_x - SCREEN_WIDTH / 2
        camera_offset_x += (target_camera_offset - camera_offset_x) * 0.08

    screen.fill(BLACK)

    for layer in background_layers:
        for element in layer:
            element_world_x = element['initial_x'] + (camera_offset_x * element['parallax']) # Parallax calculation
            element_screen_x = element_world_x - camera_offset_x

            if -element['width'] < element_screen_x < SCREEN_WIDTH + element['width']:
                if element['type'] == 'stalagmite':
                    base_y = element['base_y']
                    base_y = min(base_y, SCREEN_HEIGHT + element['height'])
                    top_y = max(-element['height'], base_y - element['height'])
                    if base_y > -element['height']:
                         pygame.draw.polygon(screen, element['color'], [
                             (element_screen_x - element['width'] / 2, base_y),
                             (element_screen_x, top_y),
                             (element_screen_x + element['width'] / 2, base_y)
                         ])
                else: # Stalactite
                    pygame.draw.polygon(screen, element['color'], [
                         (element_screen_x - element['width'] / 2, 0),
                         (element_screen_x, element['height']),
                         (element_screen_x + element['width'] / 2, 0)
                     ])

    current_hill_angle_for_drawing = get_hill_angle(boulder_x if game_state == "playing" else INITIAL_BOULDER_X)
    points = []
    step = 10
    draw_camera_offset = camera_offset_x

    for screen_x_loop in range(-step, SCREEN_WIDTH + step*2, step):
        world_x = screen_x_loop + draw_camera_offset
        world_y = get_hill_y(world_x)
        screen_y = max(-SCREEN_HEIGHT, min(SCREEN_HEIGHT * 2, world_y))
        points.append((screen_x_loop, screen_y))
    if points:
        points.append((SCREEN_WIDTH + step, SCREEN_HEIGHT))
        points.append((-step, SCREEN_HEIGHT))
        if len(points) > 2:
             pygame.draw.polygon(screen, HILL_COLOR, points)

    display_boulder_x = boulder_x
    display_boulder_y = boulder_y
    display_sisyphus_x = sisyphus_x
    display_sisyphus_y = sisyphus_y
    display_hill_angle = current_hill_angle_for_drawing

    if game_state == "start_screen" or game_state == "ready_to_play":
        display_boulder_x = INITIAL_BOULDER_X
        display_boulder_y = get_hill_y(INITIAL_BOULDER_X)
        display_hill_angle = get_hill_angle(INITIAL_BOULDER_X)
        offset_distance_static = BOULDER_RADIUS + SISYPHUS_WIDTH * 0.3
        display_sisyphus_x = display_boulder_x - offset_distance_static * math.cos(display_hill_angle)
        display_sisyphus_y = display_boulder_y + offset_distance_static * math.sin(display_hill_angle)

    boulder_screen_x = int(display_boulder_x - camera_offset_x)
    boulder_screen_y = int(display_boulder_y)
    sisyphus_screen_x = int(display_sisyphus_x - camera_offset_x)
    sisyphus_screen_y = int(display_sisyphus_y)

    pygame.draw.circle(screen, GRAY1, (boulder_screen_x, boulder_screen_y), BOULDER_RADIUS)
    shade_offset_x = int(BOULDER_RADIUS * 0.3 * math.cos(display_hill_angle + math.pi/2))
    shade_offset_y = int(BOULDER_RADIUS * 0.3 * -math.sin(display_hill_angle + math.pi/2))
    pygame.draw.circle(screen, GRAY2, (boulder_screen_x + shade_offset_x, boulder_screen_y + shade_offset_y), int(BOULDER_RADIUS * 0.8))

    sisyphus_angle_rad = display_hill_angle
    sisyphus_angle_deg = math.degrees(sisyphus_angle_rad)
    sisyphus_surf = pygame.Surface((SISYPHUS_WIDTH, SISYPHUS_HEIGHT), pygame.SRCALPHA)
    sisyphus_surf.fill((0,0,0,0))
    pygame.draw.rect(sisyphus_surf, LIGHT_GRAY, (0, 0, SISYPHUS_WIDTH, SISYPHUS_HEIGHT))
    rotated_surf = pygame.transform.rotate(sisyphus_surf, sisyphus_angle_deg)
    pivot_offset_y = SISYPHUS_HEIGHT * 0.4
    rotated_rect = rotated_surf.get_rect(center=(sisyphus_screen_x, sisyphus_screen_y - pivot_offset_y))
    screen.blit(rotated_surf, rotated_rect.topleft)

    if game_state != "start_screen":
        score_text = font_small.render(f"Distance: {current_score}", True, WHITE)
        screen.blit(score_text, (10, 10))

    if game_state == "start_screen":
        title_text_surf = font_large.render("The Trial of Sisyphus", True, WHITE)
        title_text_rect = title_text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 180))
        screen.blit(title_text_surf, title_text_rect)

        history_text = (
            "In Greek myth, Sisyphus, a cunning king, twice cheated Death.\n"
            "For his hubris, Zeus condemned him to an eternal punishment:\n"
            "to roll a colossal boulder up a hill, only for it to roll back down\n"
            "each time it neared the summit, for all eternity."
        )
        render_text_multiline(history_text, font_extra_small, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80, 5)

        objective_text = "Objective: Push the boulder as far up the hill as you can."
        obj_text_surf = font_small.render(objective_text, True, WHITE)
        obj_text_rect = obj_text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(obj_text_surf, obj_text_rect)

        controls_text = "Controls: Alternately press 'Z' and 'X' to push."
        ctrl_text_surf = font_small.render(controls_text, True, WHITE)
        ctrl_text_rect = ctrl_text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        screen.blit(ctrl_text_surf, ctrl_text_rect)

        start_prompt_text = font_medium.render("Press SPACE to Begin the Trial", True, WHITE)
        start_prompt_rect = start_prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        screen.blit(start_prompt_text, start_prompt_rect)


    if game_state == "game_over":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 10, 180))
        screen.blit(overlay, (0, 0))
        lost_text = font_large.render("The Boulder Stopped", True, LIGHT_GRAY)
        score_final_text = font_small.render(f"Furthest Distance: {current_score}", True, WHITE)
        restart_text = font_small.render("A new day. Press SPACE to try again.", True, WHITE)
        screen.blit(lost_text, (SCREEN_WIDTH // 2 - lost_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(score_final_text, (SCREEN_WIDTH // 2 - score_final_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()