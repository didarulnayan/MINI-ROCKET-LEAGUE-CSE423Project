from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# Camera-related variables
camera_pos = [0, -600, 400] 
look_at = [0, 0, 0]
fovY = 60  
FIELD_LENGTH = 800
FIELD_WIDTH = 500
GOAL_WIDTH = 100
GOAL_HEIGHT = 40
GOAL_DEPTH = 30

# Ball Physics Variables
ball_pos = [0, 0, 100] # Start in air
ball_vel = [0, 0, 0]   # Velocity vector
BALL_RADIUS = 10
GRAVITY = 0.8
BOUNCE_FACTOR = 0.8    
FRICTION = 0.98        

# Car Physics Variables
car_pos = [200, 0, 0]
car_angle = 180 # Facing center
car_velo = 0
CAR_WIDTH = 20
CAR_LENGTH = 35
CAR_HEIGHT = 15
CAR_SPEED_CAP = 6
CAR_ACCEL = 0.12
CAR_DECEL = 0.90
turn_speed = 5

# Defender Car Variables (Car 2 - Arrow Keys)
def_pos = [350, 0, 0]
def_angle = 180
def_velo = 0

keys_pressed = set() # Track multiple keys
special_keys_pressed = set() # Track arrow keys for defender

# Score
score = [0, 0] # [Left Team, Right Team]

# Game State
# 0: Welcome Screen
# 1: Toss Screen
# 2: Coin Flip Animation
# 4: Toss Result Screen
# 5: Team Selection Screen
# 3: Playing
# 6: Match Over
game_state = 0 

# Toss System Variables
player_choice = None  # 'heads' or 'tails'
toss_result = None    # 'heads' or 'tails'
toss_winner = None    # "You" or "Opponent"
coin_flip_frame = 0   # Animation frame counter
flip_duration = 240   # CHANGED: 4 seconds at 60fps (was 120)

# Team and Match Variables
player_team = None    # 'Red' or 'Blue'
match_duration = 90   # 90 seconds
remaining_time = 90
last_timer_update = 0

# NEW: Poppers Animation Variables
poppers = []  # List of particles: [x, y, z, vx, vy, vz, life, r, g, b]
goal_celebration_active = False
goal_celebration_time = 0

# Cheat Mode Variables
cheat_mode = False  # When True, cars move automatically to score goals

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1,1,1)):
    glColor3f(color[0], color[1], color[2])
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hollow_circle(radius, center_x, center_y, z=0, segments=100):
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        theta = 2.0 * math.pi * float(i) / float(segments)
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        glVertex3f(x + center_x, y + center_y, z)
    glEnd()

def draw_goal(x_pos, facing_right=True):
    glPushMatrix()
    glTranslatef(x_pos, 0, 0)
    if not facing_right:
        glRotatef(180, 0, 0, 1)

    # Posts
    glColor3f(1, 1, 1) # White
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # Front Frame
    glVertex3f(0, -GOAL_WIDTH/2, 0); glVertex3f(0, -GOAL_WIDTH/2, GOAL_HEIGHT)
    glVertex3f(0, GOAL_WIDTH/2, 0); glVertex3f(0, GOAL_WIDTH/2, GOAL_HEIGHT)
    glVertex3f(0, -GOAL_WIDTH/2, GOAL_HEIGHT); glVertex3f(0, GOAL_WIDTH/2, GOAL_HEIGHT)
    
    d = GOAL_DEPTH
    glVertex3f(d, -GOAL_WIDTH/2, 0); glVertex3f(d, -GOAL_WIDTH/2, GOAL_HEIGHT)
    glVertex3f(d, GOAL_WIDTH/2, 0); glVertex3f(d, GOAL_WIDTH/2, GOAL_HEIGHT)
    glVertex3f(d, -GOAL_WIDTH/2, GOAL_HEIGHT); glVertex3f(d, GOAL_WIDTH/2, GOAL_HEIGHT)
    
    # Connectors
    glVertex3f(0, -GOAL_WIDTH/2, GOAL_HEIGHT); glVertex3f(d, -GOAL_WIDTH/2, GOAL_HEIGHT)
    glVertex3f(0, GOAL_WIDTH/2, GOAL_HEIGHT); glVertex3f(d, GOAL_WIDTH/2, GOAL_HEIGHT)
    glVertex3f(0, -GOAL_WIDTH/2, 0); glVertex3f(d, -GOAL_WIDTH/2, 0)
    glVertex3f(0, GOAL_WIDTH/2, 0); glVertex3f(d, GOAL_WIDTH/2, 0)
    glEnd()
    
    # Net
    glLineWidth(1.0)
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_LINES)
    
    num_strands = 15
    for i in range(num_strands + 1):
        y = -GOAL_WIDTH/2 + (GOAL_WIDTH * i / num_strands)
        glVertex3f(d, y, 0); glVertex3f(d, y, GOAL_HEIGHT)
        glVertex3f(0, y, GOAL_HEIGHT); glVertex3f(d, y, GOAL_HEIGHT)

    num_h_strands = 10
    for i in range(num_h_strands + 1):
        z = GOAL_HEIGHT * i / num_h_strands
        glVertex3f(d, -GOAL_WIDTH/2, z); glVertex3f(d, GOAL_WIDTH/2, z)
        glVertex3f(0, -GOAL_WIDTH/2, z); glVertex3f(d, -GOAL_WIDTH/2, z)
        glVertex3f(0, GOAL_WIDTH/2, z); glVertex3f(d, GOAL_WIDTH/2, z)

    glEnd()
    glPopMatrix()

def draw_banners():
    banner_height = 30
    offset = 40 
    segment_length = 50
    
    glBegin(GL_QUADS)
    # Long sides
    num_x = int(FIELD_LENGTH / segment_length)
    for i in range(num_x):
        color = (0.8, 0, 0) if i % 2 == 0 else (0, 0, 0.8)
        glColor3f(*color)
        x1 = -FIELD_LENGTH/2 + i * segment_length
        x2 = x1 + segment_length
        # Top
        y = FIELD_WIDTH/2 + offset
        glVertex3f(x1, y, 0); glVertex3f(x2, y, 0); glVertex3f(x2, y, banner_height); glVertex3f(x1, y, banner_height)
        # Bottom
        y = -FIELD_WIDTH/2 - offset
        glVertex3f(x1, y, 0); glVertex3f(x2, y, 0); glVertex3f(x2, y, banner_height); glVertex3f(x1, y, banner_height)

    # Short sides
    num_y = int(FIELD_WIDTH / segment_length)
    for i in range(num_y):
        color = (0.8, 0.8, 0) if i % 2 == 0 else (0, 0.5, 0)
        glColor3f(*color)
        y1 = -FIELD_WIDTH/2 + i * segment_length
        y2 = y1 + segment_length
        # Right
        x = FIELD_LENGTH/2 + offset
        glVertex3f(x, y1, 0); glVertex3f(x, y2, 0); glVertex3f(x, y2, banner_height); glVertex3f(x, y1, banner_height)
        # Left
        x = -FIELD_LENGTH/2 - offset
        glVertex3f(x, y1, 0); glVertex3f(x, y2, 0); glVertex3f(x, y2, banner_height); glVertex3f(x, y1, banner_height)

    glEnd()

def draw_welcome_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Gradient Background
    glBegin(GL_QUADS)
    glColor3f(0.05, 0.05, 0.2)
    glVertex2f(0, 0)
    glColor3f(0.2, 0.0, 0.2)
    glVertex2f(1000, 0)
    glColor3f(0.0, 0.0, 0.1)
    glVertex2f(1000, 800)
    glColor3f(0.0, 0.2, 0.3)
    glVertex2f(0, 800)
    glEnd()
    
    # Decorative Circles
    glColor3f(1, 0.8, 0)
    glBegin(GL_LINE_LOOP)
    for i in range(100):
        theta = 2.0 * 3.14159 * i / 100.0
        x = 60 * math.cos(theta) + 150
        y = 60 * math.sin(theta) + 650
        glVertex2f(x, y)
    glEnd()
    
    glColor3f(0, 1, 1)
    glBegin(GL_LINE_LOOP)
    for i in range(100):
        theta = 2.0 * 3.14159 * i / 100.0
        x = 100 * math.cos(theta) + 850
        y = 100 * math.sin(theta) + 150
        glVertex2f(x, y)
    glEnd()
    
    # Title
    draw_text(360, 500, "ROCKET FOOTBALL 3D", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.5, 0))
    draw_text(362, 502, "ROCKET FOOTBALL 3D", GLUT_BITMAP_TIMES_ROMAN_24, (1, 1, 0))
    
    # Instructions
    draw_text(420, 400, "Press SPACE to Start", color=(0, 1, 0))
    
    # Controls
    draw_text(350, 300, "Controls: WASD to Drive | Arrow Keys to Look", color=(0.7, 0.7, 1))
    draw_text(350, 270, "Objective: Push the Ball into the Goal!", color=(0.7, 0.7, 1))
    draw_text(380, 200, "Avoid the field boundaries!", color=(1, 0.3, 0.3))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glutSwapBuffers()

def draw_toss_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.1, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glColor3f(0.2, 0.0, 0.2)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    draw_text(400, 600, "COIN TOSS", GLUT_BITMAP_TIMES_ROMAN_24, (1, 1, 0))
    draw_text(300, 500, "Choose Your Side:", GLUT_BITMAP_HELVETICA_18, (1, 1, 1))
    draw_text(350, 400, "Press H for HEADS", color=(0, 1, 0))
    draw_text(350, 350, "Press T for TAILS", color=(0, 1, 0))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glutSwapBuffers()

def draw_coin_flip():
    """Animated coin flip - SLOWER VERSION"""
    global coin_flip_frame
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # White Background
    glBegin(GL_QUADS)
    glColor3f(1, 1, 1)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    cx, cy = 500, 550
    base_radius = 80
    
    # SLOWER TEXT ANIMATION
    text_cycle = (coin_flip_frame // 20) % 6  # CHANGED: from 10 to 20
    texts = ["FLIPPING", "FLIPPING.", "FLIPPING..", "FLIPPING...", "FLIP!", "TOSSING"]
    current_text = texts[text_cycle]
    text_y = 200 + math.sin(coin_flip_frame * 0.08) * 10  # CHANGED: from 0.15 to 0.08
    brightness = 0.5 + 0.5 * abs(math.sin(coin_flip_frame * 0.1))  # CHANGED: from 0.2 to 0.1
    draw_text(400, text_y, current_text, GLUT_BITMAP_TIMES_ROMAN_24, (brightness * 0.2, brightness * 0.2, brightness * 0.2))
    
    # SLOWER COIN ROTATION
    rotation_offset = (coin_flip_frame * 6) % 360  # CHANGED: from 12 to 6
    flip_angle = (coin_flip_frame * 8) % 360  # CHANGED: from 15 to 8
    scale_x = abs(math.cos(math.radians(flip_angle)))
    if scale_x < 0.15: scale_x = 0.15
    radius_x = base_radius * scale_x
    radius_y = base_radius
    
    glColor3f(1, 0.84, 0)
    glBegin(GL_POLYGON)
    for i in range(100):
        theta = 2.0 * math.pi * i / 100.0
        x = cx + radius_x * math.cos(theta)
        y = cy + radius_y * math.sin(theta)
        glVertex2f(x, y)
    glEnd()
    
    glColor3f(0.7, 0.55, 0)
    glLineWidth(3.0)
    glBegin(GL_LINE_LOOP)
    for i in range(100):
        theta = 2.0 * math.pi * i / 100.0
        x = cx + radius_x * math.cos(theta)
        y = cy + radius_y * math.sin(theta)
        glVertex2f(x, y)
    glEnd()
    
    if scale_x > 0.3:
        glColor3f(0.8, 0.65, 0)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for i in range(8):
            angle = math.radians(rotation_offset + i * 45)
            x1 = cx + (radius_x * 0.3) * math.cos(angle)
            y1 = cy + (radius_y * 0.3) * math.sin(angle)
            x2 = cx + (radius_x * 0.7) * math.cos(angle)
            y2 = cy + (radius_y * 0.7) * math.sin(angle)
            glVertex2f(x1, y1)
            glVertex2f(x2, y2)
        glEnd()
    
    glColor3f(0.6, 0.45, 0)
    glBegin(GL_POLYGON)
    for i in range(20):
        theta = 2.0 * math.pi * i / 20.0
        x = cx + (radius_x * 0.15) * math.cos(theta)
        y = cy + (radius_y * 0.15) * math.sin(theta)
        glVertex2f(x, y)
    glEnd()
    
    glLineWidth(1.0)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glutSwapBuffers()

def draw_toss_result():
    """Display toss result"""
    global toss_result, toss_winner
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.1, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glColor3f(0.2, 0.0, 0.2)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    draw_text(360, 550, "COIN RESULT", GLUT_BITMAP_TIMES_ROMAN_24, (1, 1, 0))
    draw_text(420, 480, toss_result.upper(), GLUT_BITMAP_TIMES_ROMAN_24, (0, 1, 1))
    
    if toss_winner == "You":
        draw_text(370, 450, "YOU WON THE TOSS!", GLUT_BITMAP_TIMES_ROMAN_24, (0, 1, 0))
    else:
        draw_text(350, 450, "OPPONENT WON THE TOSS!", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0, 0))
    
    draw_text(300, 300, "Press SPACE to continue to Team Selection", color=(1, 1, 1))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glutSwapBuffers()

def draw_team_selection_screen():
    """Team selection screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    glBegin(GL_QUADS)
    glColor3f(0.05, 0.05, 0.1); glVertex2f(0, 0); glVertex2f(1000, 0)
    glColor3f(0.1, 0, 0); glVertex2f(1000, 800); glVertex2f(0, 800)
    glEnd()
    
    header = f"{toss_winner.upper()} WON! PICK A TEAM"
    draw_text(350, 600, header, GLUT_BITMAP_TIMES_ROMAN_24, (1, 1, 0))
    
    glColor3f(0.8, 0, 0); glBegin(GL_QUADS)
    glVertex2f(200, 300); glVertex2f(450, 300); glVertex2f(450, 450); glVertex2f(200, 450)
    glEnd()
    draw_text(280, 360, "RED (Press R)", color=(1, 1, 1))
    
    glColor3f(0, 0, 0.8); glBegin(GL_QUADS)
    glVertex2f(550, 300); glVertex2f(800, 300); glVertex2f(800, 450); glVertex2f(550, 450)
    glEnd()
    draw_text(630, 360, "BLUE (Press B)", color=(1, 1, 1))
    
    draw_text(350, 200, "Note: Red Team Attacks First!", color=(1, 0.5, 0))
    
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST); glutSwapBuffers()

def draw_game_over_screen():
    """Final Score Screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    glBegin(GL_QUADS); glColor3f(0, 0, 0); glVertex2f(0, 0); glVertex2f(1000, 0); glVertex2f(1000, 800); glVertex2f(0, 800); glEnd()
    draw_text(400, 600, "MATCH FINISHED!", GLUT_BITMAP_TIMES_ROMAN_24, (1, 1, 1))
    result_text = f"Final Score: {score[0]} - {score[1]}"
    draw_text(420, 500, result_text, GLUT_BITMAP_TIMES_ROMAN_24, (0, 1, 1))
    
    if score[0] > score[1]: win_msg = "LEFT TEAM WINS!"
    elif score[1] > score[0]: win_msg = "RIGHT TEAM WINS!"
    else: win_msg = "IT'S A DRAW!"
    
    draw_text(420, 400, win_msg, color=(1, 1, 0))
    draw_text(380, 300, "Press SPACE to Restart Game", color=(0.7, 0.7, 0.7))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST); glutSwapBuffers()

def draw_flag(x, y):
    glPushMatrix()
    glTranslatef(x, y, 0)
    
    # Pole
    glColor3f(1, 1, 1)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 40)
    glEnd()
    
    # Flag
    glColor3f(1, 0, 0)
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 0, 40)
    glVertex3f(0, 0, 30)
    glVertex3f(15, 0, 35)
    glEnd()
    
    glPopMatrix()

def draw_ball():
    global ball_pos
    glPushMatrix()
    glTranslatef(ball_pos[0], ball_pos[1], ball_pos[2])
    
    glColor3f(1, 1, 1)
    glutSolidSphere(BALL_RADIUS, 20, 20)
    
    glColor3f(0, 0, 0)
    glutWireSphere(BALL_RADIUS + 0.1, 10, 10)
    
    glPopMatrix()

def draw_car(pos, angle, body_color=(1, 0.3, 0)):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(angle, 0, 0, 1)

    # Main Body
    glPushMatrix()
    glTranslatef(0, 0, CAR_HEIGHT/2)
    glColor3f(*body_color) 
    glScalef(CAR_LENGTH, CAR_WIDTH, CAR_HEIGHT * 0.6)
    glutSolidCube(1)
    glPopMatrix()
    
    # Cabin
    glPushMatrix()
    glTranslatef(CAR_LENGTH * 0.1, 0, CAR_HEIGHT * 0.9)
    glColor3f(body_color[0]*0.9, body_color[1]*0.9, body_color[2]*0.9)
    glScalef(CAR_LENGTH * 0.5, CAR_WIDTH * 0.8, CAR_HEIGHT * 0.6)
    glutSolidCube(1)
    glPopMatrix()
    
    # Windshield
    glPushMatrix()
    glTranslatef(CAR_LENGTH * 0.3, 0, CAR_HEIGHT * 0.9)
    glColor3f(0.3, 0.7, 0.9)
    glScalef(CAR_LENGTH * 0.15, CAR_WIDTH * 0.75, CAR_HEIGHT * 0.5)
    glutSolidCube(1)
    glPopMatrix()
    
    # Wheels
    wheel_positions = [
        (CAR_LENGTH * 0.3, CAR_WIDTH * 0.55, CAR_HEIGHT * 0.3),
        (CAR_LENGTH * 0.3, -CAR_WIDTH * 0.55, CAR_HEIGHT * 0.3),
        (-CAR_LENGTH * 0.3, CAR_WIDTH * 0.55, CAR_HEIGHT * 0.3),
        (-CAR_LENGTH * 0.3, -CAR_WIDTH * 0.55, CAR_HEIGHT * 0.3),
    ]
    
    for wx, wy, wz in wheel_positions:
        glPushMatrix()
        glTranslatef(wx, wy, wz)
        glColor3f(0.1, 0.1, 0.1); glRotatef(90, 1, 0, 0); glutSolidTorus(2, 4, 8, 12)
        glColor3f(0.7, 0.7, 0.7); glutSolidTorus(0.5, 2.5, 6, 10)
        glPopMatrix()

    glPopMatrix()

# NEW: Poppers Functions
def create_goal_poppers():
    """Create celebration poppers from all 4 corners of the field"""
    global poppers, goal_celebration_active, goal_celebration_time
    import time
    
    poppers = []
    goal_celebration_active = True
    goal_celebration_time = time.time()
    
    # Four corner positions
    corners = [
        (FIELD_LENGTH/2, FIELD_WIDTH/2, 0),    # Top-right
        (FIELD_LENGTH/2, -FIELD_WIDTH/2, 0),   # Bottom-right
        (-FIELD_LENGTH/2, FIELD_WIDTH/2, 0),   # Top-left
        (-FIELD_LENGTH/2, -FIELD_WIDTH/2, 0),  # Bottom-left
    ]
    
    # Create particles from each corner
    for cx, cy, cz in corners:
        for i in range(40):  # 40 particles per corner
            # Random angle and speed
            angle_h = random.uniform(0, 2 * math.pi)  # Horizontal angle
            angle_v = random.uniform(math.pi/6, math.pi/3)  # Vertical angle (30-60 degrees)
            speed = random.uniform(8, 15)
            
            # Velocity components
            vx = speed * math.cos(angle_v) * math.cos(angle_h)
            vy = speed * math.cos(angle_v) * math.sin(angle_h)
            vz = speed * math.sin(angle_v)
            
            # Random color
            r = random.uniform(0.5, 1.0)
            g = random.uniform(0.5, 1.0)
            b = random.uniform(0.5, 1.0)
            
            # Life in frames
            life = random.randint(60, 120)  # 1-2 seconds
            
            # Add particle: [x, y, z, vx, vy, vz, life, r, g, b]
            poppers.append([cx, cy, cz, vx, vy, vz, life, r, g, b])

def update_poppers():
    """Update popper particles"""
    global poppers, goal_celebration_active
    import time
    
    # Remove dead particles
    poppers = [p for p in poppers if p[6] > 0]
    
    # Update remaining particles
    for particle in poppers:
        # Update position
        particle[0] += particle[3]  # x += vx
        particle[1] += particle[4]  # y += vy
        particle[2] += particle[5]  # z += vz
        
        # Apply gravity
        particle[5] -= GRAVITY * 1.5  # vz -= gravity
        
        # Ground collision
        if particle[2] < 0:
            particle[2] = 0
            particle[5] = -particle[5] * 0.6  # Bounce with damping
        
        # Decrease life
        particle[6] -= 1
    
    # Check if celebration is over
    if goal_celebration_active and time.time() - goal_celebration_time > 3:
        goal_celebration_active = False

def draw_poppers():
    """Draw popper particles as small spheres"""
    for particle in poppers:
        glPushMatrix()
        glTranslatef(particle[0], particle[1], particle[2])
        # Fade out effect by changing alpha
        alpha = particle[6] / 120.0  # Normalize life to 0-1
        glColor4f(particle[7], particle[8], particle[9], alpha)
        gluSphere(gluNewQuadric(), 5, 6, 6)  # Small sphere for each particle
        glPopMatrix()

def cheat_mode_ai():
    """AI logic for cheat mode - both cars automatically try to score goals"""
    global car_pos, car_angle, car_velo, def_pos, def_angle, def_velo, ball_pos, keys_pressed, special_keys_pressed
    
    if not cheat_mode:
        return
    
    # Clear manual controls when in cheat mode
    keys_pressed.clear()
    special_keys_pressed.clear()
    
    # Helper function to move car towards a target
    def move_car_towards_target(car_x, car_y, car_ang, target_x, target_y, is_attacker=True):
        dx = target_x - car_x
        dy = target_y - car_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 10:  # Close enough
            return car_ang, 0
        
        # Calculate target angle
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # Normalize angles to 0-360
        while target_angle < 0:
            target_angle += 360
        while car_ang < 0:
            car_ang += 360
        
        # Find shortest rotation direction
        angle_diff = target_angle - car_ang
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360
        
        # Apply turning
        turn_speed = 5  # AI turn speed
        if abs(angle_diff) > turn_speed:
            if angle_diff > 0:
                new_angle = car_ang + turn_speed
            else:
                new_angle = car_ang - turn_speed
        else:
            new_angle = target_angle
        
        # Move forward if facing roughly towards target
        if abs(angle_diff) < 45:  # Within 45 degrees
            velocity = min(8, distance * 0.3)  # Speed based on distance
        else:
            velocity = 0
        
        return new_angle, velocity
    
    # AI Logic for both cars
    ball_x, ball_y = ball_pos[0], ball_pos[1]
    
    # Attacker (Player 1) - aims for right goal (positive X)
    target_goal_x = FIELD_LENGTH/2 - 50  # Just inside goal area
    target_goal_y = 0
    
    # If ball is on attacker's side or close, go for the ball first
    if ball_x < 100 or (abs(ball_x - car_pos[0]) < abs(ball_x - def_pos[0])):
        # Go towards ball
        car_angle, car_velo = move_car_towards_target(car_pos[0], car_pos[1], car_angle, ball_x, ball_y, True)
    else:
        # Go towards goal
        car_angle, car_velo = move_car_towards_target(car_pos[0], car_pos[1], car_angle, target_goal_x, target_goal_y, True)
    
    # Defender (Player 2) - aims for left goal (negative X)  
    target_goal_x = -FIELD_LENGTH/2 + 50  # Just inside goal area
    target_goal_y = 0
    
    # If ball is on defender's side or close, go for the ball first
    if ball_x > -100 or (abs(ball_x - def_pos[0]) < abs(ball_x - car_pos[0])):
        # Go towards ball
        def_angle, def_velo = move_car_towards_target(def_pos[0], def_pos[1], def_angle, ball_x, ball_y, False)
    else:
        # Go towards goal
        def_angle, def_velo = move_car_towards_target(def_pos[0], def_pos[1], def_angle, target_goal_x, target_goal_y, False)

def update_physics():
    global ball_pos, ball_vel, car_pos, car_velo, car_angle, score
    global def_pos, def_velo, def_angle
    
    # Cheat mode AI (overrides manual controls if active)
    cheat_mode_ai()
    
    # Ball Physics
    ball_vel[2] -= GRAVITY
    
    ball_pos[0] += ball_vel[0]
    ball_pos[1] += ball_vel[1]
    ball_pos[2] += ball_vel[2]
    
    # Ground Collision
    if ball_pos[2] < BALL_RADIUS:
        ball_pos[2] = BALL_RADIUS
        ball_vel[2] = -ball_vel[2] * BOUNCE_FACTOR
        ball_vel[0] *= FRICTION
        ball_vel[1] *= FRICTION
        if abs(ball_vel[2]) < GRAVITY * 2:
            ball_vel[2] = 0

    # Wall Collision
    limit_x = FIELD_LENGTH/2 - BALL_RADIUS
    limit_y = FIELD_WIDTH/2 - BALL_RADIUS
    
    if abs(ball_pos[0]) > limit_x:
        # Check if goal
        if abs(ball_pos[1]) < (GOAL_WIDTH/2 - BALL_RADIUS) and ball_pos[2] < GOAL_HEIGHT:
            # GOAL SCORED!
            if ball_pos[0] > 0:
                score[0] += 1
            else:
                score[1] += 1
            print(f"GOAL! Score: {score[0]} - {score[1]}")
            
            # NEW: Trigger poppers animation
            create_goal_poppers()
            
            # Reset ball
            ball_pos = [0, 0, 100]
            ball_vel = [0, 0, 0]
        else:
            ball_pos[0] = math.copysign(limit_x, ball_pos[0])
            ball_vel[0] *= -1

    if abs(ball_pos[1]) > limit_y:
        ball_pos[1] = math.copysign(limit_y, ball_pos[1])
        ball_vel[1] *= -1

    # FIXED CAR PHYSICS - Attacker (WASD)
    if b'w' in keys_pressed:
        car_velo += CAR_ACCEL
    if b's' in keys_pressed:
        car_velo -= CAR_ACCEL
    
    car_velo = max(-CAR_SPEED_CAP, min(CAR_SPEED_CAP, car_velo))
    car_velo *= CAR_DECEL
    
    # FIXED TURNING - Only turn when moving
    if abs(car_velo) > 0.5:
        turn_amount = turn_speed * (abs(car_velo) / CAR_SPEED_CAP)
        if b'a' in keys_pressed:
            car_angle += turn_amount
        if b'd' in keys_pressed:
            car_angle -= turn_amount

    rad = math.radians(car_angle)
    car_pos[0] += math.cos(rad) * car_velo
    car_pos[1] += math.sin(rad) * car_velo
    
    # FIXED DEFENDER PHYSICS (Arrows)
    if GLUT_KEY_UP in special_keys_pressed:
        def_velo += CAR_ACCEL
    if GLUT_KEY_DOWN in special_keys_pressed:
        def_velo -= CAR_ACCEL
    
    def_velo = max(-CAR_SPEED_CAP, min(CAR_SPEED_CAP, def_velo))
    def_velo *= CAR_DECEL
    
    # FIXED TURNING - Only turn when moving
    if abs(def_velo) > 0.5:
        turn_amount = turn_speed * (abs(def_velo) / CAR_SPEED_CAP)
        if GLUT_KEY_LEFT in special_keys_pressed:
            def_angle += turn_amount
        if GLUT_KEY_RIGHT in special_keys_pressed:
            def_angle -= turn_amount

    rad_def = math.radians(def_angle)
    def_pos[0] += math.cos(rad_def) * def_velo
    def_pos[1] += math.sin(rad_def) * def_velo

    # Constraints - Both players can move freely around the field
    car_pos[0] = max(-FIELD_LENGTH/2 + CAR_LENGTH/2, min(FIELD_LENGTH/2 - CAR_LENGTH/2, car_pos[0]))
    car_pos[1] = max(-FIELD_WIDTH/2 + CAR_WIDTH/2, min(FIELD_WIDTH/2 - CAR_WIDTH/2, car_pos[1]))
    
    # Defender can also move freely (same constraints as attacker)
    def_pos[0] = max(-FIELD_LENGTH/2 + CAR_LENGTH/2, min(FIELD_LENGTH/2 - CAR_LENGTH/2, def_pos[0]))
    def_pos[1] = max(-FIELD_WIDTH/2 + CAR_WIDTH/2, min(FIELD_WIDTH/2 - CAR_WIDTH/2, def_pos[1]))

    # Ball-Car Collisions
    for p, v in [(car_pos, car_velo), (def_pos, def_velo)]:
        dist_sq = (ball_pos[0] - p[0])**2 + (ball_pos[1] - p[1])**2
        min_dist = BALL_RADIUS + CAR_WIDTH
        
        if dist_sq < min_dist**2 and ball_pos[2] < (CAR_HEIGHT + BALL_RADIUS):
            dist = math.sqrt(dist_sq) or 0.01
            nx, ny = (ball_pos[0] - p[0])/dist, (ball_pos[1] - p[1])/dist
            
            ball_vel[0] += nx * abs(v) * 1.5
            ball_vel[1] += ny * abs(v) * 1.5
            ball_vel[2] += 2
            
            ball_pos[0] += nx * 5
            ball_pos[1] += ny * 5

def draw_field():
    # Grass
    glColor3f(0.13, 0.55, 0.13)
    glBegin(GL_QUADS)
    glVertex3f(-FIELD_LENGTH/2 - 100, -FIELD_WIDTH/2 - 100, -1)
    glVertex3f(FIELD_LENGTH/2 + 100, -FIELD_WIDTH/2 - 100, -1)
    glVertex3f(FIELD_LENGTH/2 + 100, FIELD_WIDTH/2 + 100, -1)
    glVertex3f(-FIELD_LENGTH/2 - 100, FIELD_WIDTH/2 + 100, -1)
    glEnd()

    draw_banners()

    # Lines
    glColor3f(1, 1, 1)
    glLineWidth(2.0)
    
    glBegin(GL_LINE_LOOP)
    glVertex3f(-FIELD_LENGTH/2, -FIELD_WIDTH/2, 0.1)
    glVertex3f(FIELD_LENGTH/2, -FIELD_WIDTH/2, 0.1)
    glVertex3f(FIELD_LENGTH/2, FIELD_WIDTH/2, 0.1)
    glVertex3f(-FIELD_LENGTH/2, FIELD_WIDTH/2, 0.1)
    glEnd()

    glBegin(GL_LINES)
    glVertex3f(0, -FIELD_WIDTH/2, 0.1)
    glVertex3f(0, FIELD_WIDTH/2, 0.1)
    glEnd()

    draw_hollow_circle(60, 0, 0, 0.1)
    
    # Corner Flags
    draw_flag(FIELD_LENGTH/2, FIELD_WIDTH/2)
    draw_flag(FIELD_LENGTH/2, -FIELD_WIDTH/2)
    draw_flag(-FIELD_LENGTH/2, FIELD_WIDTH/2)
    draw_flag(-FIELD_LENGTH/2, -FIELD_WIDTH/2)

    # Goals
    draw_goal(FIELD_LENGTH/2, facing_right=True) 
    draw_goal(-FIELD_LENGTH/2, facing_right=False)

def reset_game():
    """Reset game"""
    global ball_pos, ball_vel, car_pos, car_angle, car_velo, score, game_state
    global def_pos, def_angle, def_velo
    global player_choice, toss_result, toss_winner, coin_flip_frame, remaining_time
    global poppers, goal_celebration_active
    
    ball_pos = [0, 0, 100]
    ball_vel = [0, 0, 0]
    car_pos = [200, 0, 0]
    car_angle = 180
    car_velo = 0
    def_pos = [350, 0, 0]
    def_angle = 180
    def_velo = 0
    score = [0, 0]
    player_choice = None
    toss_result = None
    toss_winner = None
    coin_flip_frame = 0
    remaining_time = 90
    poppers = []
    goal_celebration_active = False
    game_state = 1
    
def idle():
    global coin_flip_frame, game_state, toss_result, toss_winner, player_choice
    global remaining_time, last_timer_update
    
    # Coin flip animation
    if game_state == 2:
        coin_flip_frame += 1
        if coin_flip_frame >= flip_duration:
            toss_result = random.choice(['heads', 'tails'])
            toss_winner = "You" if toss_result == player_choice else "Opponent"
            game_state = 4
            coin_flip_frame = 0
    
    # Playing
    if game_state == 3:
        update_physics()
        update_poppers()  # NEW: Update poppers
        
        # Timer
        current_time = glutGet(GLUT_ELAPSED_TIME)
        delta = (current_time - last_timer_update) / 1000.0
        remaining_time -= delta
        last_timer_update = current_time
        
        if remaining_time <= 0:
            remaining_time = 0
            game_state = 6
    
    glutPostRedisplay()

def keyboardListener(key, x, y):
    global keys_pressed, game_state, player_choice, coin_flip_frame, camera_pos
    global player_team, car_pos, car_angle, def_pos, def_angle, ball_pos, ball_vel, last_timer_update
    
    if (key == b'r' or key == b'R') and game_state != 5:
        reset_game()
        glutPostRedisplay()
        return

    if game_state == 0:
        if key == b' ':
            game_state = 1
            glutPostRedisplay()
        return
    
    if game_state == 1:
        if key == b'h' or key == b'H':
            player_choice = 'heads'
            game_state = 2
            coin_flip_frame = 0
            glutPostRedisplay()
        elif key == b't' or key == b'T':
            player_choice = 'tails'
            game_state = 2
            coin_flip_frame = 0
            glutPostRedisplay()
        return
    
    if game_state == 4:
        if key == b' ':
            game_state = 5
            glutPostRedisplay()
        return

    if game_state == 5:
        if key == b'r' or key == b'R':
            player_team = 'Red'
            game_state = 3
            car_pos = [-200, 0, 0]
            car_angle = 0
            def_pos = [350, 0, 0]
            def_angle = 180
            ball_pos = [-50, 0, 10]
            ball_vel = [0, 0, 0]
            last_timer_update = glutGet(GLUT_ELAPSED_TIME)
            glutPostRedisplay()
        elif key == b'b' or key == b'B':
            player_team = 'Blue'
            game_state = 3
            car_pos = [200, 0, 0]
            car_angle = 180
            def_pos = [-350, 0, 0]
            def_angle = 0
            ball_pos = [-50, 0, 10]
            ball_vel = [0, 0, 0]
            last_timer_update = glutGet(GLUT_ELAPSED_TIME)
            glutPostRedisplay()
        return

    if game_state == 6:
        if key == b' ':
            reset_game()
        return
    
    if game_state == 3:
        # Camera controls
        step = 20
        cx, cy, cz = camera_pos
        if key == b'j' or key == b'J': cx -= step
        if key == b'l' or key == b'L': cx += step
        if key == b'i' or key == b'I': cy += step
        if key == b'k' or key == b'K': cy -= step
        camera_pos = [cx, cy, cz]

        # Cheat mode toggle
        if key == b'c' or key == b'C':
            global cheat_mode
            cheat_mode = not cheat_mode
            print(f"Cheat mode: {'ON' if cheat_mode else 'OFF'}")

        keys_pressed.add(key.lower())
        glutPostRedisplay()

def keyboardUpListener(key, x, y):
    global keys_pressed
    k = key.lower()
    if k in keys_pressed:
        keys_pressed.remove(k)

def specialKeyListener(key, x, y):
    global special_keys_pressed
    special_keys_pressed.add(key)
    glutPostRedisplay()

def specialKeyUpListener(key, x, y):
    global special_keys_pressed
    if key in special_keys_pressed:
        special_keys_pressed.remove(key)
    glutPostRedisplay()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],  
              look_at[0], look_at[1], look_at[2],  
              0, 0, 1)

def showScreen():
    global game_state
    
    if game_state == 0:
        draw_welcome_screen()
        return
    elif game_state == 1:
        draw_toss_screen()
        return
    elif game_state == 2:
        draw_coin_flip()
        return
    elif game_state == 4:
        draw_toss_result()
        return
    elif game_state == 5:
        draw_team_selection_screen()
        return
    elif game_state == 6:
        draw_game_over_screen()
        return

    # game_state == 3: Playing
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    setupCamera()
    draw_field()
    draw_ball()
    
    # NEW: Draw poppers
    draw_poppers()
    
    # Cars
    atk_color = (1, 0.4, 0) if player_team == 'Red' else (0.1, 0.4, 1)
    def_color = (0.1, 0.4, 1) if player_team == 'Red' else (1, 0.4, 0)
    
    draw_car(car_pos, car_angle, atk_color)
    draw_car(def_pos, def_angle, def_color)
    
    draw_text(10, 770, f"Score: {score[0]} - {score[1]}")
    draw_text(10, 740, f"Time Remaining: {int(remaining_time)}s")
    draw_text(10, 710, "P1: WASD | P2: Arrows | Cam: I/J/K/L | C: Cheat Mode | R: Restart", color=(1,1,1))

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"ROCKET FOOTBALL 3D")

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialKeyUpListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":

    main()
