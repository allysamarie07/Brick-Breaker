import cv2
import mediapipe as mp
import pygame
import numpy as np
import random
import time
import os
import json

# ---------------- SIZE CONFIG ----------------
CURSOR_SIZE = (40, 40)
BALL_SIZE = (30, 30)
POWERUP_SIZE = (60, 60)

PADDLE_SIZES = {
    "easy": (240, 20),
    "medium": (180, 20),
    "hard": (130, 20)
}

PADDLE_MIN = 80
PADDLE_MAX = 350

BRICK_SIZES = {
    "easy": {"width": 90, "height": 50},
    "medium": {"width": 80, "height": 45},
    "hard": {"width": 55, "height": 40}
}

BRICK_CONFIG = {
    "easy": {"cols":14, "rows":7, "spacing":8, "start_y":80, "paddle_y":150},
    "medium": {"cols":16, "rows":9, "spacing":6, "start_y":80, "paddle_y":150},
    "hard": {"cols":24, "rows":12, "spacing":4, "start_y":60, "paddle_y":150}
}

# ---------------- INIT ----------------
pygame.init()
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# 🔊 AUDIO INIT (ADDED)
pygame.mixer.init()

MUSIC_PATH = "music"

menu_music = os.path.join(MUSIC_PATH, "MainMenu.mp3")
easy_music = os.path.join(MUSIC_PATH, "EasyRound.mp3")
medium_music = os.path.join(MUSIC_PATH, "MediumRound.mp3")
hard_music = os.path.join(MUSIC_PATH, "HardRound.mp3")
gameover_music = os.path.join(MUSIC_PATH, "GameOver.mp3")

brick_sound = pygame.mixer.Sound(os.path.join(MUSIC_PATH, "Brick.mp3"))
brick_sound.set_volume(0.5)

current_music = None

def play_music(music_file, loop=True):
    global current_music
    if current_music != music_file:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1 if loop else 0)
        current_music = music_file

# ---------------- LOAD IMAGES ----------------
IMG_PATH = "images"

bg = pygame.image.load(os.path.join(IMG_PATH, "bg.jpg"))
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

brick_red = pygame.image.load(os.path.join(IMG_PATH, "red.png"))
brick_gray = pygame.image.load(os.path.join(IMG_PATH, "gray.png"))
ball_img = pygame.image.load(os.path.join(IMG_PATH, "ball.png"))
cursor_img = pygame.image.load(os.path.join(IMG_PATH, "cursor.png"))

x2_img = pygame.image.load(os.path.join(IMG_PATH, "x2.png"))
long_img = pygame.image.load(os.path.join(IMG_PATH, "long.png"))
short_img = pygame.image.load(os.path.join(IMG_PATH, "short.png"))

ball_img = pygame.transform.scale(ball_img, BALL_SIZE)
cursor_img = pygame.transform.scale(cursor_img, CURSOR_SIZE)
x2_img = pygame.transform.scale(x2_img, POWERUP_SIZE)
long_img = pygame.transform.scale(long_img, POWERUP_SIZE)
short_img = pygame.transform.scale(short_img, POWERUP_SIZE)

# ---------------- MEDIAPIPE ----------------
mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
face_mesh = mp_face.FaceMesh(refine_landmarks=True)
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
cap = cv2.VideoCapture(0)

# ---------------- GAME VARIABLES ----------------
state = "menu"
difficulty = "easy"

cursor_x, cursor_y = WIDTH//2, HEIGHT//2
hover_target = None
hover_start_time = 0

# Peace sign detection variables
peace_sign_active = False
peace_sign_start_time = 0
PEACE_SIGN_HOLD_DURATION = 2.0  # seconds to hold peace sign to quit

paddle_y = HEIGHT - 150
paddle_width = PADDLE_SIZES["easy"][0]
paddle_height = 20

balls = []
bricks = []
powerups = []
particles = []

score = 0
combo = 0
level_number = 1

# ---------------- HIGH SCORE SYSTEM ----------------
HIGHSCORE_FILE = "highscores.json"

def load_high_scores():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"easy": 0, "medium": 0, "hard": 0}
    return {"easy": 0, "medium": 0, "hard": 0}

def save_high_scores(high_scores):
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump(high_scores, f)

def update_high_score(diff, new_score):
    high_scores = load_high_scores()
    if new_score > high_scores.get(diff, 0):
        high_scores[diff] = new_score
        save_high_scores(high_scores)
        return True
    return False

high_scores = load_high_scores()

# ============================================================================
# ENHANCED AESTHETIC DESIGN SYSTEM
# ============================================================================

# ---------------- ENHANCED COLOR PALETTE ----------------
MENU_COLORS = {
    "primary": (86, 124, 228),
    "primary_dark": (45, 85, 165),
    "primary_light": (140, 175, 255),

    "easy": (76, 217, 100),
    "easy_dark": (46, 180, 75),
    "easy_glow": (140, 255, 160),

    "medium": (255, 204, 0),
    "medium_dark": (220, 170, 0),
    "medium_glow": (255, 235, 120),

    "hard": (255, 100, 100),
    "hard_dark": (210, 60, 60),
    "hard_glow": (255, 160, 160),

    "gold": (255, 215, 100),
    "gold_dark": (200, 170, 60),
    "white": (255, 255, 255),
    "off_white": (240, 245, 255),
    "light_gray": (180, 190, 210),
    "dark_bg": (20, 25, 40),
    "darker_bg": (10, 15, 25),
}

# ---------------- ENHANCED TEXT RENDERING ----------------
def draw_enhanced_text(text, size, x, y, color=(255,255,255), 
                       align="center", shadow=True, glow=False, glow_intensity=3):
    """Enhanced text with shadow and optional glow effects"""
    font = pygame.font.SysFont("Arial", size, bold=True)

    text_surf = font.render(text, True, color)

    if align == "center":
        text_rect = text_surf.get_rect(center=(x, y))
    elif align == "left":
        text_rect = text_surf.get_rect(topleft=(x, y))
    else:
        text_rect = text_surf.get_rect(topright=(x, y))

    # Glow effect
    if glow:
        glow_color = tuple(min(255, c + 50) for c in color[:3])
        for i in range(glow_intensity * 2, 0, -1):
            alpha = int(80 - (i * 15))
            if alpha > 0:
                glow_surf = font.render(text, True, glow_color)
                glow_surf.set_alpha(alpha)
                offset = i // 2
                glow_rect = glow_surf.get_rect(center=text_rect.center)
                screen.blit(glow_surf, (glow_rect.x + offset, glow_rect.y))
                screen.blit(glow_surf, (glow_rect.x - offset, glow_rect.y))

    # Drop shadow
    if shadow:
        shadow_surf = font.render(text, True, (20, 25, 35))
        shadow_surf.set_alpha(180)
        shadow_rect = shadow_surf.get_rect(center=(text_rect.centerx + 2, text_rect.centery + 2))
        screen.blit(shadow_surf, shadow_rect)

    screen.blit(text_surf, text_rect)
    return text_rect

def draw_gradient_text(text, size, x, y, colors, align="center"):
    """Draw text with vertical gradient coloring"""
    font = pygame.font.SysFont("Arial", size, bold=True)

    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect()

    gradient = pygame.Surface(text_rect.size, pygame.SRCALPHA)

    for y_offset in range(text_rect.height):
        ratio = y_offset / text_rect.height
        color_idx = int(ratio * (len(colors) - 1))
        next_idx = min(color_idx + 1, len(colors) - 1)
        local_ratio = (ratio * (len(colors) - 1)) - color_idx

        r = int(colors[color_idx][0] * (1 - local_ratio) + colors[next_idx][0] * local_ratio)
        g = int(colors[color_idx][1] * (1 - local_ratio) + colors[next_idx][1] * local_ratio)
        b = int(colors[color_idx][2] * (1 - local_ratio) + colors[next_idx][2] * local_ratio)

        pygame.draw.line(gradient, (r, g, b), (0, y_offset), (text_rect.width, y_offset))

    text_with_alpha = text_surf.convert_alpha()
    gradient.blit(text_with_alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    if align == "center":
        gradient_rect = gradient.get_rect(center=(x, y))
    elif align == "left":
        gradient_rect = gradient.get_rect(topleft=(x, y))
    else:
        gradient_rect = gradient.get_rect(topright=(x, y))

    shadow = font.render(text, True, (20, 25, 35))
    shadow.set_alpha(150)
    screen.blit(shadow, (gradient_rect.x + 3, gradient_rect.y + 3))

    screen.blit(gradient, gradient_rect)
    return gradient_rect

# ---------------- ENHANCED GLASS BUTTON ----------------
def draw_glass_button(rect, text, is_hovered, progress=0, color_scheme="blue"):
    """Modern glassmorphism-style button with smooth animations"""

    color_map = {
        "easy": (MENU_COLORS["easy"], MENU_COLORS["easy_dark"], MENU_COLORS["easy_glow"]),
        "medium": (MENU_COLORS["medium"], MENU_COLORS["medium_dark"], MENU_COLORS["medium_glow"]),
        "hard": (MENU_COLORS["hard"], MENU_COLORS["hard_dark"], MENU_COLORS["hard_glow"]),
        "blue": (MENU_COLORS["primary"], MENU_COLORS["primary_dark"], MENU_COLORS["primary_light"]),
        "gold": (MENU_COLORS["gold"], MENU_COLORS["gold_dark"], (255, 240, 180)),
        "green": (MENU_COLORS["easy"], MENU_COLORS["easy_dark"], MENU_COLORS["easy_glow"]),
    }

    base, dark, glow = color_map.get(color_scheme, color_map["blue"])

    button_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

    # Glass background
    bg_alpha = 200 if is_hovered else 140
    glass_color = (*base, bg_alpha)

    corner_radius = 16
    pygame.draw.rect(button_surf, glass_color, 
                     (0, 0, rect.width, rect.height), border_radius=corner_radius)

    # Progress fill animation
    if progress > 0:
        fill_height = int(rect.height * progress)
        fill_rect = pygame.Rect(0, rect.height - fill_height, rect.width, fill_height)

        for y in range(fill_rect.y, rect.height):
            fill_ratio = (y - fill_rect.y) / fill_height if fill_height > 0 else 0
            r = int(dark[0] + (base[0] - dark[0]) * fill_ratio)
            g = int(dark[1] + (base[1] - dark[1]) * fill_ratio)
            b = int(dark[2] + (base[2] - dark[2]) * fill_ratio)
            pygame.draw.line(button_surf, (r, g, b, 220), 
                           (0, y), (rect.width, y))

    # Hover glow effect
    if is_hovered:
        for i in range(4, 0, -1):
            glow_surf = pygame.Surface((rect.width + i*8, rect.height + i*8), pygame.SRCALPHA)
            glow_alpha = 40 - (i * 8)
            pygame.draw.rect(glow_surf, (*glow, glow_alpha), 
                           glow_surf.get_rect(), border_radius=corner_radius + i*2)
            screen.blit(glow_surf, (rect.x - i*4, rect.y - i*4))

    # Border
    border_color = glow if is_hovered else (255, 255, 255, 120)
    border_width = 3 if is_hovered else 2
    pygame.draw.rect(button_surf, border_color, 
                     (0, 0, rect.width, rect.height), border_width, border_radius=corner_radius)

    # Inner highlight
    highlight_rect = pygame.Rect(2, 2, rect.width-4, rect.height//3)
    pygame.draw.rect(button_surf, (255, 255, 255, 40), highlight_rect, border_radius=corner_radius-2)

    screen.blit(button_surf, rect)

    # Button text
    text_color = (255, 255, 255)
    text_y_offset = -2 if is_hovered else 0

    draw_enhanced_text(text, 32, rect.centerx, rect.centery + text_y_offset,
                      color=text_color, align="center",
                      shadow=True, glow=is_hovered, glow_intensity=2)

    # Progress indicator bar
    if progress > 0 and progress < 1:
        bar_height = 4
        bar_width = int((rect.width - 20) * progress)
        bar_y = rect.bottom - 10

        pygame.draw.rect(screen, (255, 255, 255, 60), 
                        (rect.x + 10, bar_y, rect.width - 20, bar_height), 
                        border_radius=2)

        if bar_width > 0:
            for x in range(bar_width):
                ratio = x / bar_width
                r = int(255 - (255 - glow[0]) * ratio)
                g = int(255 - (255 - glow[1]) * ratio)
                b = int(255 - (255 - glow[2]) * ratio)
                pygame.draw.rect(screen, (r, g, b), 
                               (rect.x + 10 + x, bar_y, 1, bar_height))

# ---------------- ENHANCED HIGH SCORE PANEL ----------------
def draw_high_score_panel(x, y, scores, scale=1.0):
    """Elegant high score panel with full black background and smooth corners"""
    panel_width = int(320 * scale)
    panel_height = int(220 * scale)

    # Create the panel surface
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)

    # Full black background with smooth corners (rounded rectangle)
    corner_radius = 20
    pygame.draw.rect(panel, (0, 0, 0, 255), 
                    (0, 0, panel_width, panel_height), border_radius=corner_radius)

    # Optional: subtle border for definition
    pygame.draw.rect(panel, (60, 60, 60, 255), 
                    (0, 0, panel_width, panel_height), 2, border_radius=corner_radius)

    screen.blit(panel, (x - panel_width//2, y))

    # Title
    title_size = int(28 * scale)
    draw_enhanced_text("HIGH SCORES", title_size, x, y + int(20 * scale), 
                      color=(255, 255, 255), align="center",
                      glow=True, glow_intensity=2)

    # Score entries
    difficulties = [
        ("easy", "EASY", MENU_COLORS["easy"]),
        ("medium", "MEDIUM", MENU_COLORS["medium"]),
        ("hard", "HARD", MENU_COLORS["hard"])
    ]

    entry_size = int(22 * scale)
    score_size = int(24 * scale)
    spacing = int(45 * scale)
    start_y = y + int(55 * scale)

    for i, (key, label, color) in enumerate(difficulties):
        entry_y = start_y + i * spacing

        # Indicator dot
        dot_radius = int(6 * scale)
        pygame.draw.circle(screen, color, (x - panel_width//2 + int(25 * scale), entry_y), dot_radius)
        pygame.draw.circle(screen, (255, 255, 255), (x - panel_width//2 + int(25 * scale), entry_y), dot_radius - 2)

        # Label
        draw_enhanced_text(label, entry_size, x - panel_width//2 + int(45 * scale), entry_y - 8,
                          color=(200, 200, 200), align="left", shadow=True)

        # Score
        score_val = scores.get(key, 0)
        score_color = MENU_COLORS["gold"] if score_val > 0 else (150, 150, 150)
        draw_enhanced_text(str(score_val), score_size, x + panel_width//2 - int(20 * scale), entry_y - 8,
                          color=score_color, align="right", shadow=True)

# ---------------- PEACE SIGN DETECTION ----------------
def detect_peace_sign(hand_landmarks):
    """
    Detect if hand is making a peace/V sign
    Returns True if index and middle fingers are extended, others are curled
    """
    if hand_landmarks is None:
        return False

    landmarks = hand_landmarks.landmark

    # Finger tip indices in MediaPipe Hands
    INDEX_TIP = 8
    INDEX_PIP = 6
    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    RING_TIP = 16
    RING_PIP = 14
    PINKY_TIP = 20
    PINKY_PIP = 18

    # Check if index finger is extended (tip above PIP joint - y is inverted in screen coords)
    index_extended = landmarks[INDEX_TIP].y < landmarks[INDEX_PIP].y

    # Check if middle finger is extended
    middle_extended = landmarks[MIDDLE_TIP].y < landmarks[MIDDLE_PIP].y

    # Check if ring finger is curled (tip below PIP joint)
    ring_curled = landmarks[RING_TIP].y > landmarks[RING_PIP].y

    # Check if pinky is curled
    pinky_curled = landmarks[PINKY_TIP].y > landmarks[PINKY_PIP].y

    # Peace sign: index and middle extended, ring and pinky curled
    return index_extended and middle_extended and ring_curled and pinky_curled

def draw_peace_sign_indicator(x, y, is_active, progress=0):
    """Draw a visual indicator for peace sign quit gesture"""
    # Draw hand icon background
    icon_size = 80
    bg_rect = pygame.Rect(x - icon_size//2, y - icon_size//2, icon_size, icon_size)

    # Background circle
    pygame.draw.circle(screen, (30, 40, 60, 180), (x, y), icon_size//2)
    pygame.draw.circle(screen, (100, 150, 200, 150), (x, y), icon_size//2, 3)

    # Draw "V" or peace symbol text
    if is_active:
        # Pulsing effect when active
        pulse = int(5 * (1 + 0.3 * (1 if int(time.time() * 8) % 2 else 0.7)))
        pygame.draw.circle(screen, (255, 100, 100, 100), (x, y), icon_size//2 + pulse)
        color = (255, 100, 100)
        text = "V"
    else:
        color = (180, 190, 210)
        text = "V"

    draw_enhanced_text(text, 48, x, y, color=color, align="center", glow=is_active)

    # Progress ring for quit action
    if progress > 0:
        # Draw circular progress
        import math
        center = (x, y)
        radius = icon_size//2 + 10

        # Background ring
        pygame.draw.circle(screen, (60, 70, 90), center, radius, 4)

        # Progress arc
        points = []
        for angle in range(-90, int(-90 + 360 * progress) + 1, 5):
            rad = math.radians(angle)
            px = center[0] + radius * math.cos(rad)
            py = center[1] + radius * math.sin(rad)
            points.append((px, py))

        if len(points) > 1:
            pygame.draw.lines(screen, (255, 100, 100), False, points, 6)

    # Label
    draw_enhanced_text("Peace sign to Quit", 20, x, y + icon_size//2 + 20, 
                      color=(160, 170, 190), align="center", shadow=False)

# ---------------- MENU BACKGROUND PARTICLES ----------------
menu_particles = []
last_particle_time = 0

def update_menu_background():
    """Floating particles for menu ambiance"""
    global last_particle_time

    current_time = time.time()

    if current_time - last_particle_time > 0.5:
        menu_particles.append({
            "x": random.randint(0, WIDTH),
            "y": HEIGHT + 20,
            "size": random.randint(3, 8),
            "speed": random.uniform(0.5, 2),
            "opacity": random.randint(30, 80),
            "color": random.choice([
                MENU_COLORS["primary"],
                MENU_COLORS["easy"],
                MENU_COLORS["medium"],
                MENU_COLORS["gold"]
            ])
        })
        last_particle_time = current_time

    for p in menu_particles[:]:
        p["y"] -= p["speed"]

        if p["y"] < 100:
            p["opacity"] = max(0, p["opacity"] - 2)

        if p["opacity"] <= 0 or p["y"] < -20:
            menu_particles.remove(p)
            continue

        surf = pygame.Surface((p["size"] * 4, p["size"] * 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p["color"], p["opacity"] // 3), 
                         (p["size"] * 2, p["size"] * 2), p["size"] * 2)
        pygame.draw.circle(surf, (*p["color"], p["opacity"]), 
                         (p["size"] * 2, p["size"] * 2), p["size"])
        screen.blit(surf, (p["x"] - p["size"] * 2, p["y"] - p["size"] * 2))

# ---------------- HOVER LOGIC ----------------
def handle_hover_logic(rect, is_hovered, action):
    global hover_target, hover_start_time
    if is_hovered:
        if hover_target != rect:
            hover_target = rect
            hover_start_time = time.time()
        else:
            elapsed = time.time() - hover_start_time
            progress = min(elapsed / 2, 1)

            if elapsed >= 2:
                hover_target = None
                action()
            return progress
    else:
        if hover_target == rect:
            hover_target = None
    return 0

# ---------------- PARTICLES (unchanged) ----------------
def spawn_particles(x,y):
    for _ in range(10):
        particles.append({
            "x":x,"y":y,
            "dx":random.uniform(-3,3),
            "dy":random.uniform(-3,3),
            "life":random.randint(20,40)
        })

def update_particles():
    for p in particles[:]:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        p["life"] -= 1
        pygame.draw.circle(screen,(255,200,50),(int(p["x"]),int(p["y"])),3)
        if p["life"] <= 0:
            particles.remove(p)

# ---------------- BRICK FORMATIONS (unchanged) ----------------
def get_formation_positions(formation_type, cols, rows, spacing, w, h, start_y_override=None):
    positions = []

    total_width = cols * w + (cols - 1) * spacing
    start_x = (WIDTH - total_width) // 2

    start_y = start_y_override if start_y_override is not None else 80

    if formation_type == "rectangle":
        for r in range(rows):
            for c in range(cols):
                x = start_x + c * (w + spacing)
                y = start_y + r * (h + spacing)
                positions.append((x, y))

    elif formation_type == "v_shape":
        center_col = cols // 2
        for r in range(rows):
            spread = min(r + 1, center_col, cols//3)
            for offset in range(-spread, spread + 1):
                c = center_col + offset
                if 0 <= c < cols:
                    x = start_x + c * (w + spacing)
                    y = start_y + r * (h + spacing)
                    positions.append((x, y))

    elif formation_type == "u_shape":
        for r in range(rows):
            for c in range(cols):
                if c == 0 or c == cols - 1 or r == rows - 1:
                    x = start_x + c * (w + spacing)
                    y = start_y + r * (h + spacing)
                    positions.append((x, y))

    elif formation_type == "a_shape":
        center_col = cols // 2
        for r in range(rows):
            spread = min(rows - r - 1, center_col, cols//3)
            if spread >= 0:
                for offset in range(-spread, spread + 1):
                    c = center_col + offset
                    if 0 <= c < cols:
                        x = start_x + c * (w + spacing)
                        y = start_y + r * (h + spacing)
                        positions.append((x, y))

    elif formation_type == "diamond":
        center_col = cols // 2
        center_row = rows // 2
        for r in range(rows):
            row_dist = abs(r - center_row)
            max_spread = min(center_col - row_dist, cols//3)
            if max_spread >= 0:
                for offset in range(-max_spread, max_spread + 1):
                    c = center_col + offset
                    if 0 <= c < cols:
                        x = start_x + c * (w + spacing)
                        y = start_y + r * (h + spacing)
                        positions.append((x, y))

    elif formation_type == "checkerboard":
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2 == 0:
                    x = start_x + c * (w + spacing)
                    y = start_y + r * (h + spacing)
                    positions.append((x, y))

    elif formation_type == "cross":
        center_col = cols // 2
        center_row = rows // 2
        for r in range(rows):
            for c in range(cols):
                if c == center_col or r == center_row:
                    x = start_x + c * (w + spacing)
                    y = start_y + r * (h + spacing)
                    positions.append((x, y))

    elif formation_type == "circle":
        center_col = cols // 2
        center_row = rows // 2
        for r in range(rows):
            for c in range(cols):
                dist = ((c - center_col) ** 2 / (center_col ** 2 + 0.1) + 
                       (r - center_row) ** 2 / (center_row ** 2 + 0.1)) ** 0.5
                if dist <= 0.8:
                    x = start_x + c * (w + spacing)
                    y = start_y + r * (h + spacing)
                    positions.append((x, y))

    return positions

# ---------------- BRICKS (unchanged) ----------------
def create_bricks(level, formation=None):
    global bricks, brick_red_s, brick_gray_s, current_formation

    bricks = []

    if formation is None:
        formations = ["rectangle", "v_shape", "u_shape", "a_shape", "diamond", 
                   "checkerboard", "cross", "circle"]
        formation = random.choice(formations)

    current_formation = formation

    cfg = BRICK_CONFIG[level]
    cols, rows = cfg["cols"], cfg["rows"]
    spacing = cfg["spacing"]
    start_y = cfg.get("start_y", 80)

    size_cfg = BRICK_SIZES[level]
    w = size_cfg["width"]
    h = size_cfg["height"]

    brick_red_s = pygame.transform.scale(brick_red,(w,h))
    brick_gray_s = pygame.transform.scale(brick_gray,(w,h))

    positions = get_formation_positions(formation, cols, rows, spacing, w, h, start_y)

    for x, y in positions:
        hp = 2 if (level!="easy" and random.random()<0.5) else 1
        bricks.append({"rect":pygame.Rect(x,y,w,h),"hp":hp})

# ---------------- POWERUPS (unchanged) ----------------
def spawn_powerup(x,y):
    chance = {"easy":0.3,"medium":0.5,"hard":0.1}[difficulty]
    if random.random() < chance:
        p_type = random.choices(["x2","long","short"],weights=[0.6,0.2,0.2])[0]
        powerups.append({"x":x,"y":y,"type":p_type, "width":POWERUP_SIZE[0], "height":POWERUP_SIZE[1]})

# ---------------- RESET (unchanged) ----------------
def reset_game(level, keep_score=False, next_level=False):
    global balls, difficulty, powerups, paddle_width, score, combo, level_number, paddle_y

    if not keep_score and not next_level:
        score = 0
        combo = 0
        level_number = 1
    elif next_level:
        level_number += 1

    difficulty = level

    cfg = BRICK_CONFIG[level]
    paddle_y = HEIGHT - cfg.get("paddle_y", 150)

    create_bricks(level)
    powerups.clear()

    paddle_width = PADDLE_SIZES[level][0]

    speed = {"easy":random.uniform(7.0, 8.0),"medium":random.uniform(9.0, 10.0),"hard":random.uniform(11.0, 12.0)}[level]

    ball_x = cursor_x
    ball_y = paddle_y - BALL_SIZE[1] - 5

    balls = [{
        "x": ball_x,
        "y": ball_y,
        "dx": random.choice([-speed,speed]),
        "dy": -speed
    }]

# ---------------- NEXT LEVEL (unchanged) ----------------
def next_level():
    global state
    reset_game(difficulty, keep_score=True, next_level=True)
    state = "game"

# ---------------- ACTIONS (unchanged) ----------------
def start_easy():
    global state
    reset_game("easy")
    state="game"

def start_medium():
    global state
    reset_game("medium")
    state="game"

def start_hard():
    global state
    reset_game("hard")
    state="game"

def restart_game():
    global state
    reset_game(difficulty)
    state="game"

def go_to_menu():
    global state, score, combo, level_number, peace_sign_active, peace_sign_start_time
    if state == "gameover":
        update_high_score(difficulty, score)
    # Reset peace sign detection when going to menu
    peace_sign_active = False
    peace_sign_start_time = 0
    state="menu"

def quit_game():
    global running
    running = False

# ---------------- MAIN LOOP ----------------
running=True
hand_landmarks = None

while running:
    screen.blit(bg,(0,0))

    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False

    # Process camera frame
    ret,frame=cap.read()
    if not ret: 
        break

    frame=cv2.flip(frame,1)
    rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

    # Process face for cursor control
    result=face_mesh.process(rgb)
    if result.multi_face_landmarks:
        nose=result.multi_face_landmarks[0].landmark[1]
        cursor_x=int(nose.x*WIDTH)
        cursor_y=int(nose.y*HEIGHT)

    # Process hands for peace sign detection
    hand_result = hands.process(rgb)
    if hand_result.multi_hand_landmarks:
        hand_landmarks = hand_result.multi_hand_landmarks[0]
    else:
        hand_landmarks = None

    # === STATE HANDLING  ===
    if state=="game":
        if difficulty == "easy":
            play_music(easy_music)
        elif difficulty == "medium":
            play_music(medium_music)
        elif difficulty == "hard":
            play_music(hard_music)

        paddle=pygame.Rect(cursor_x-paddle_width//2,paddle_y,paddle_width,paddle_height)
        pygame.draw.rect(screen,(200,200,255),paddle,border_radius=10)

        # BALLS
        for ball in balls:
            ball["x"]+=ball["dx"]
            ball["y"]+=ball["dy"]

            if ball["x"]<=0 or ball["x"]>=WIDTH: 
                ball["dx"]*=-1
            if ball["y"]<=0: 
                ball["dy"]*=-1

            ball_rect = pygame.Rect(ball["x"], ball["y"], *BALL_SIZE)

            if ball_rect.colliderect(paddle) and ball["dy"]>0:
                ball["y"]=paddle.top-BALL_SIZE[1]
                ball["dy"]=-abs(ball["dy"])

                hit_pos=(ball["x"]+BALL_SIZE[0]//2)-paddle.centerx
                normalized=hit_pos/(paddle.width/2)
                ball["dx"]=normalized*8

                combo=0

            screen.blit(ball_img,(ball["x"],ball["y"]))

        # BRICKS (FIXED: Removed the incorrect 'break' statement)
        for brick in bricks[:]:
            if brick["hp"] == 2:
                screen.blit(brick_gray_s, brick["rect"])
            else:
                screen.blit(brick_red_s, brick["rect"])

            hit = False
            for ball in balls:
                ball_rect = pygame.Rect(ball["x"], ball["y"], *BALL_SIZE)

                if brick["rect"].colliderect(ball_rect):
                    brick_sound.play()
                    ball["dy"] *= -1
                    brick["hp"] -= 1
                    hit = True
                    break  # Only break out of the ball loop, not the brick loop

            if hit:
                if brick["hp"] <= 0:
                    spawn_powerup(brick["rect"].x,brick["rect"].y)
                    combo += 1
                    score += 10 * combo
                    spawn_particles(brick["rect"].centerx,brick["rect"].centery)

                    if brick in bricks:
                        bricks.remove(brick)

        if not bricks:
            next_level()

        # POWERUPS
        for p in powerups[:]:
            p["y"]+=4
            img = x2_img if p["type"]=="x2" else long_img if p["type"]=="long" else short_img
            screen.blit(img,(p["x"],p["y"]))

            powerup_rect = pygame.Rect(p["x"], p["y"], p["width"], p["height"])

            if powerup_rect.colliderect(paddle):
                if p["type"]=="x2":
                    balls += [{"x":b["x"],"y":b["y"],"dx":-b["dx"],"dy":b["dy"]} for b in balls]

                elif p["type"]=="long":
                    paddle_width=min(PADDLE_MAX,paddle_width+40)

                elif p["type"]=="short":
                    paddle_width=max(PADDLE_MIN,paddle_width-40)

                powerups.remove(p)

        balls=[b for b in balls if b["y"]<=HEIGHT]
        if not balls:
            update_high_score(difficulty, score)
            state="gameover"

        update_particles()

        # Game HUD
        font = pygame.font.SysFont("Arial", 35, True)
        level_text = font.render(f"Level: {level_number}", True, (255,255,255))
        screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 40))

        score_text = font.render(f"Score: {score}", True, (255,215,100))
        screen.blit(score_text, (120, 40))

        combo_text = font.render(f"Combo: x{combo}", True, (255,200,0))
        screen.blit(combo_text, (120, 80))

    elif state=="menu":
        play_music(menu_music)
        # ENHANCED MAIN MENU DESIGN
        update_menu_background()

        # Main title with gradient
        title_y = 120

        # Title glow
        for i in range(5, 0, -1):
            glow_surf = pygame.font.SysFont("Arial", 80, bold=True).render(
                "BRICK BREAKER", True, (100, 150, 255))
            glow_surf.set_alpha(40 - i * 6)
            glow_rect = glow_surf.get_rect(center=(WIDTH//2 + i, title_y + i))
            screen.blit(glow_surf, glow_rect)

        # Main title
        draw_gradient_text("BRICK BREAKER", 72, WIDTH//2, title_y,
                          [(255, 255, 255), (200, 230, 255), (140, 190, 255)])

        # Subtitle
        draw_enhanced_text("Face-Controlled Arcade Action", 26, WIDTH//2, title_y + 55,
                          color=(180, 200, 230), align="center",
                          glow=True, glow_intensity=1)

        # --- BALANCED LAYOUT: Buttons on left, High scores on right ---

        # Button column (left side)
        button_width = 280
        button_height = 70
        button_x = WIDTH//2 - 350  # Left of center
        start_y = 280
        spacing = 85

        buttons = [
            ("EASY", "easy", start_easy, start_y),
            ("MEDIUM", "medium", start_medium, start_y + spacing),
            ("HARD", "hard", start_hard, start_y + spacing * 2)
        ]

        for text, scheme, action, by in buttons:
            rect = pygame.Rect(button_x, by, button_width, button_height)

            is_hover = rect.collidepoint(cursor_x, cursor_y)
            progress = handle_hover_logic(rect, is_hover, action)

            draw_glass_button(rect, text, is_hover, progress, scheme)

            # Description on hover
            if is_hover:
                desc_y = by + button_height + 8
                descriptions = {
                    "easy": "Relaxed pace • Larger paddle • Perfect for beginners",
                    "medium": "Balanced challenge • Standard gameplay",
                    "hard": "Fast balls • Small paddle • Expert only"
                }
                desc_color = {
                    "easy": (140, 220, 160),
                    "medium": (255, 220, 140),
                    "hard": (255, 160, 160)
                }
                draw_enhanced_text(descriptions[scheme], 18, rect.centerx, desc_y,
                                  color=desc_color[scheme], align="center", shadow=False)

        # High scores panel (right side, aligned with buttons)
        panel_x = WIDTH//2 + 200
        panel_y = 280
        draw_high_score_panel(panel_x, panel_y, high_scores, scale=1.0)

        # Instructions at bottom
        inst_y = HEIGHT - 150

        # Instruction card
        inst_card = pygame.Surface((500, 50), pygame.SRCALPHA)
        pygame.draw.rect(inst_card, (30, 40, 60, 150), inst_card.get_rect(), border_radius=25)
        pygame.draw.rect(inst_card, (100, 150, 200, 100), inst_card.get_rect(), 2, border_radius=25)
        screen.blit(inst_card, (WIDTH//2 - 250, inst_y - 25))

        draw_enhanced_text("Hover over a button and hold to select", 22, WIDTH//2, inst_y,
                          color=(160, 180, 210), align="center",
                          glow=True, glow_intensity=1)

        # Peace sign quit indicator (bottom right)
        peace_x = WIDTH - 100
        peace_y = HEIGHT - 100

        # Check for peace sign
        is_peace = detect_peace_sign(hand_landmarks)

        if is_peace:
            if not peace_sign_active:
                peace_sign_active = True
                peace_sign_start_time = time.time()
            else:
                elapsed = time.time() - peace_sign_start_time
                peace_progress = min(elapsed / PEACE_SIGN_HOLD_DURATION, 1)

                if elapsed >= PEACE_SIGN_HOLD_DURATION:
                    quit_game()

                draw_peace_sign_indicator(peace_x, peace_y, True, peace_progress)
        else:
            peace_sign_active = False
            peace_sign_start_time = 0
            draw_peace_sign_indicator(peace_x, peace_y, False, 0)

        screen.blit(cursor_img,(cursor_x,cursor_y))

    elif state=="gameover":
        play_music(gameover_music)
        # Game over with ENHANCED glass button design (same as menu)

        # Title
        draw_enhanced_text("GAME OVER", 70, WIDTH//2, 180, 
                          color=(255, 100, 100), align="center",
                          glow=True, glow_intensity=3)

        # Score info
        draw_enhanced_text(f"Final Score: {score}", 40, WIDTH//2, 270,
                          color=(255, 255, 255), align="center", glow=True)

        draw_enhanced_text(f"Level Reached: {level_number}", 35, WIDTH//2, 320,
                          color=(200, 200, 255), align="center")

        current_high = high_scores.get(difficulty, 0)
        is_new_high = score >= current_high and score > 0

        if is_new_high:
            draw_enhanced_text("NEW HIGH SCORE!", 35, WIDTH//2, 370,
                              color=(255, 215, 100), align="center",
                              glow=True, glow_intensity=3)
        else:
            draw_enhanced_text(f"High Score: {current_high}", 30, WIDTH//2, 370,
                              color=(150, 255, 150), align="center")

        # --- ENHANCED GLASS BUTTONS for Game Over ---
        button_width = 280
        button_height = 70

        # Try Again button (green scheme like Easy)
        restart_rect = pygame.Rect(WIDTH//2 - button_width//2, 430, button_width, button_height)
        restart_hover = restart_rect.collidepoint(cursor_x, cursor_y)
        restart_progress = handle_hover_logic(restart_rect, restart_hover, restart_game)
        draw_glass_button(restart_rect, "TRY AGAIN", restart_hover, restart_progress, "green")

        # Main Menu button (blue scheme)
        menu_rect = pygame.Rect(WIDTH//2 - button_width//2, 520, button_width, button_height)
        menu_hover = menu_rect.collidepoint(cursor_x, cursor_y)
        menu_progress = handle_hover_logic(menu_rect, menu_hover, go_to_menu)
        draw_glass_button(menu_rect, "MAIN MENU", menu_hover, menu_progress, "blue")

        # Peace sign quit indicator (bottom right)
        peace_x = WIDTH - 100
        peace_y = HEIGHT - 100

        is_peace = detect_peace_sign(hand_landmarks)

        if is_peace:
            if not peace_sign_active:
                peace_sign_active = True
                peace_sign_start_time = time.time()
            else:
                elapsed = time.time() - peace_sign_start_time
                peace_progress = min(elapsed / PEACE_SIGN_HOLD_DURATION, 1)

                if elapsed >= PEACE_SIGN_HOLD_DURATION:
                    quit_game()

                draw_peace_sign_indicator(peace_x, peace_y, True, peace_progress)
        else:
            peace_sign_active = False
            peace_sign_start_time = 0
            draw_peace_sign_indicator(peace_x, peace_y, False, 0)

        screen.blit(cursor_img,(cursor_x,cursor_y))

    # FIXED: These must be inside the while loop, after the state handling
    pygame.display.update()
    clock.tick(60)

# FIXED: These must be outside the while loop, after it ends
cap.release()
pygame.quit()