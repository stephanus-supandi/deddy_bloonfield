"""Global configuration constants for DEADLY KUPERFIELD."""

# ---------------------------------------------------------------- display
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
ARENA_MARGIN = 34          # invisible wall inset so entities stay on screen

# ---------------------------------------------------------------- colors
C_BG_TOP      = (22, 16, 40)
C_BG_BOTTOM   = (8, 6, 16)
C_FLOOR       = (30, 25, 48)
C_RUNE        = (58, 46, 100)
C_PLAYER      = (90, 55, 170)
C_HAT         = (48, 28, 96)
C_EYE_GLOW    = (120, 255, 255)
C_BOLT        = (140, 220, 255)
C_BLAST       = (255, 160, 60)
C_NOVA        = (255, 120, 255)
C_TIME        = (150, 110, 255)
C_ENEMY_PROJ  = (140, 255, 120)
C_HP          = (220, 60, 70)
C_XP          = (90, 200, 255)
C_BOSS        = (170, 60, 220)

# ---------------------------------------------------------------- player
PLAYER_MAX_HP       = 100
PLAYER_SPEED        = 265.0
PLAYER_RADIUS       = 14

BOLT_CD             = 0.16
BOLT_SPEED          = 620.0
BOLT_DAMAGE         = 12
BOLT_RADIUS         = 6

BLAST_CD            = 1.4
BLAST_SPEED         = 380.0
BLAST_DAMAGE        = 45
BLAST_RADIUS        = 14
BLAST_EXPLODE_RAD   = 95
BLAST_EXPLODE_DMG   = 28

NOVA_CD             = 6.5
NOVA_MAX_RADIUS     = 210
NOVA_DAMAGE         = 55
NOVA_SPEED          = 520.0

DISINT_CD           = 15.0
DISINT_DURATION     = 5.0
TIME_SLOW_FACTOR    = 0.32   # enemies move/attack at this speed multiplier

# ---------------------------------------------------------------- enemies
BLOON  = dict(hp=30,  speed=108, radius=14, contact=8,  xp=12, score=100)
NECRO  = dict(hp=45,  speed=72,  radius=16, contact=6,  xp=25, score=250,
              range=270, shoot_cd=2.0, proj_speed=230, proj_dmg=10)
DEMON  = dict(hp=230, speed=56,  radius=28, contact=22, xp=60, score=500)

BOSS   = dict(hp=2800, speed1=52, speed2=88, radius=58, contact=30, score=5000,
              spread_cd1=2.2, spread_cd2=1.25,
              aimed_cd1=1.5,  aimed_cd2=0.85,
              slam_cd1=6.0,   slam_cd2=4.2,
              slam_radius=260, slam_dmg=28)

# ---------------------------------------------------------------- waves
WAVE_DEFS = [
    {"bloon": 5},                        # WAVE 1 -> 5
    {"bloon": 6, "necro": 2},            # WAVE 2 -> 8
    {"bloon": 8, "necro": 3, "demon": 1},# WAVE 3 -> 12
    {"bloon": 9, "necro": 4, "demon": 2},# WAVE 4 -> 15
    {"boss": 1},                         # WAVE 5 -> THE GREAT KUPER
]
WAVE_START_DELAY = 1.6
WAVE_BREAK_DELAY = 2.6

# ---------------------------------------------------------------- xp curve
def xp_needed(level: int) -> int:
    return 50 + level * 40

# ---------------------------------------------------------------- flavor
DEATH_MESSAGES = [
    "KUPER HAS LEFT THE CHAT",
    "MAGICALLY UNEMPLOYED",
    "SPELL ERROR: WIZARD TOO DEAD",
    "HE SHOULD HAVE STUDIED PYTHON",
    "UNINSTALLED FROM REALITY",
    "SEGMENTATION FAULT (CORE DUMPED)",
    "404: LIFE NOT FOUND",
    "KUPERFIELD'D",
    "RATIO + YOU'RE DEAD",
    "RETURNED TO THE KUPER-QUEUE",
]
FLAVOR_LINES = [
    "the arena smells of ozone and bad decisions",
    "somewhere, a magic school is crying",
    "KUPERFIELD mutters forbidden syntax under his breath",
    "the runes disapprove. the runes always disapprove.",
]

# ---------------------------------------------------------------- states
STATE_TITLE     = "TITLE"
STATE_PLAYING   = "PLAYING"
STATE_PAUSED    = "PAUSED"
STATE_LEVELUP   = "LEVELUP"
STATE_GAME_OVER = "GAME_OVER"
STATE_VICTORY   = "VICTORY"