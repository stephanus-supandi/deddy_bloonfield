"""HUD, title / pause / game-over / victory / level-up screens, floating text."""

import math
import pygame
from config import (
    SCREEN_W as W, SCREEN_H as H, C_HP, C_XP, C_TIME,
)

_fonts = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _fonts[key] = f
    return _fonts[key]

def text(surf, s, size, pos, color=(230, 225, 245), center=True, bold=False,
         shadow=None):
    img = get_font(size, bold).render(s, True, color)
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    if shadow:
        si = get_font(size, bold).render(s, True, shadow)
        surf.blit(si, r.move(2, 2))
    surf.blit(img, r)
    return r

def draw_bar(surf, rect, frac, fg, bg=(24, 18, 34), border=(100, 88, 150)):
    frac = max(0.0, min(1.0, frac))
    pygame.draw.rect(surf, bg, rect, border_radius=4)
    if frac > 0:
        inner = pygame.Rect(rect.x + 2, rect.y + 2,
                            max(2, int((rect.w - 4) * frac)), rect.h - 4)
        pygame.draw.rect(surf, fg, inner, border_radius=3)
    pygame.draw.rect(surf, border, rect, 1, border_radius=4)

def panel(surf, rect, alpha=170):
    p = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    p.fill((12, 9, 22, alpha))
    pygame.draw.rect(p, (100, 84, 170, 255), p.get_rect(), 2, border_radius=8)
    surf.blit(p, rect.topleft)

# --------------------------------------------------------------------- HUD
SPELL_ROWS = [
    ("LMB", "MAGIC BOLT", "bolt", (140, 220, 255)),
    ("SPACE", "KUPER BLAST", "blast", (255, 160, 60)),
    ("Q", "DEADLY NOVA", "nova", (255, 120, 255)),
    ("E", "TIME DISINTEGRATOR", "disint", (150, 110, 255)),
]

def draw_hud(surf, player, game):
    # top-left identity + bars
    text(surf, "DEADLY KUPERFIELD", 26, (160, 24), (235, 210, 255), bold=True,
         shadow=(40, 10, 60))
    hp_frac = player.hp / player.max_hp
    draw_bar(surf, pygame.Rect(20, 44, 260, 18), hp_frac, C_HP)
    text(surf, f"HP {int(player.hp)}/{int(player.max_hp)}", 18, (150, 53),
         (255, 235, 235))
    need = game.xp_need
    draw_bar(surf, pygame.Rect(20, 68, 260, 12), player.xp / need, C_XP)
    text(surf, f"XP {player.xp} / {need}", 16, (150, 74), (220, 240, 255))
    text(surf, f"LEVEL {player.level}", 22, (70, 100), (255, 230, 160),
         center=False, bold=True)
    text(surf, f"WAVE {game.wave_display}", 22, (200, 100), (200, 255, 210),
         center=False, bold=True)

    # score top-right
    text(surf, f"SCORE: {game.score}", 26, (W - 20, 26), (255, 235, 170),
         center=False, bold=True, shadow=(60, 40, 10))
    if game.enemies_left is not None:
        text(surf, f"ENEMIES: {game.enemies_left}", 20, (W - 20, 52),
             (220, 210, 240), center=False)

    # time-slow status
    if game.time_slow_timer > 0:
        text(surf, f"TIME FROZEN  {game.time_slow_timer:.1f}s", 22, (W // 2, 96),
             C_TIME, bold=True)

    # spell cooldown panel bottom-left
    pw, ph = 300, 110
    rect = pygame.Rect(14, H - ph - 12, pw, ph)
    panel(surf, rect, alpha=140)
    y = rect.y + 8
    for key, name, cdkey, col in SPELL_ROWS:
        frac = 1.0
        mx = player.cd_max[cdkey] * player.cd_mult
        if mx > 0:
            frac = 1.0 - player.cds[cdkey] / mx
        ready = frac >= 1.0
        c = col if ready else (90, 85, 105)
        text(surf, f"{key:<6} {name}", 17, (rect.x + 8, y), c, center=False)
        draw_bar(surf, pygame.Rect(rect.x + pw - 66, y + 2, 56, 8), frac,
                 col if ready else (70, 65, 90))
        y += 24

    # controls reminder bottom-right
    text(surf, "WASD move | MOUSE aim | ESC pause", 17, (W - 16, H - 20),
         (150, 145, 175), center=False)

def draw_boss_bar(surf, boss):
    w = 620
    rect = pygame.Rect(W // 2 - w // 2, 18, w, 22)
    text(surf, "THE GREAT KUPER", 26, (W // 2, 48 + 0), (255, 180, 255),
         bold=True, shadow=(60, 10, 60))
    draw_bar(surf, rect.move(0, -20), boss.hp / boss.max_hp, (200, 60, 220),
             border=(230, 150, 255))
    if boss.phase == 2:
        text(surf, "PHASE 2 - KUPERFURY", 18,
            (W // 2, 62), (255, 90, 90), bold=True)

# ------------------------------------------------------------------ screens
def draw_title(surf, t, start_rect, quit_rect, mouse_pos):
    bob = math.sin(t * 1.6) * 8
    pulse = 0.5 + 0.5 * math.sin(t * 3)
    c1 = (255, int(90 + 80 * pulse), int(60 + 60 * pulse))
    text(surf, "DEADLY", 110, (W // 2, 200 + bob), c1, bold=True,
         shadow=(80, 10, 40))
    text(surf, "KUPERFIELD", 110, (W // 2, 300 + bob), (210, 160, 255),
         bold=True, shadow=(50, 10, 80))
    text(surf, "THE WIZARD WHO SHOULD NOT HAVE PASSED", 26, (W // 2, 372),
         (200, 195, 225))
    text(surf, "MAGIC SCHOOL", 26, (W // 2, 400), (200, 195, 225))

    _button(surf, start_rect, "START", mouse_pos, (90, 200, 120))
    _button(surf, quit_rect, "QUIT", mouse_pos, (200, 90, 90))
    text(surf, "ENTER = start    ESC = quit", 20, (W // 2, 620), (150, 145, 175))
    text(surf, "a legally distinct kuperfield production", 16, (W // 2, 690),
         (100, 95, 125))

def _button(surf, rect, label, mouse_pos, color):
    hover = rect.collidepoint(mouse_pos)
    panel(surf, rect, alpha=230 if hover else 170)
    pygame.draw.rect(surf, color, rect, 3 if hover else 2, border_radius=8)
    text(surf, label, 30, rect.center, color if not hover else (255, 255, 255),
         bold=True)

def draw_pause(surf):
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((5, 3, 12, 180))
    surf.blit(dim, (0, 0))
    text(surf, "PAUSED", 80, (W // 2, H // 2 - 60), (230, 220, 255), bold=True)
    text(surf, "the magic waits. dramatically.", 24, (W // 2, H // 2), (180, 170, 210))
    text(surf, "ESC — resume      Q — quit", 24, (W // 2, H // 2 + 60),
         (150, 145, 175))

def draw_game_over(surf, score, t):
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((10, 2, 4, 200))
    surf.blit(dim, (0, 0))
    shake = math.sin(t * 30) * max(0.0, 2 - t) * 2
    text(surf, "YOU HAVE BEEN", 56, (W // 2 + shake, 230), (255, 120, 120), bold=True)
    text(surf, "KUPERFIELD'D", 96, (W // 2 - shake, 320), (255, 70, 70), bold=True,
         shadow=(90, 0, 0))
    text(surf, f"SCORE: {score}", 40, (W // 2, 430), (255, 230, 170))
    text(surf, "R — TRY AGAIN      ESC — QUIT", 26, (W // 2, 520), (200, 195, 225))

def draw_victory(surf, score, t):
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((4, 2, 14, 200))
    surf.blit(dim, (0, 0))
    text(surf, "THE GREAT KUPER", 52, (W // 2, 190), (220, 170, 255), bold=True)
    text(surf, "HAS BEEN DEFEATED", 52, (W // 2, 250), (220, 170, 255), bold=True)
    text(surf, "SOMEHOW.", 40, (W // 2, 320), (255, 240, 200), bold=True)
    text(surf, "DEADLY KUPERFIELD", 60, (W // 2, 400), (140, 255, 200), bold=True)
    text(surf, "WINS.", 60, (W // 2, 460), (140, 255, 200), bold=True)
    text(surf, f"SCORE: {score}", 40, (W // 2, 540), (255, 230, 170))
    text(surf, "R — PLAY AGAIN      ESC — QUIT", 26, (W // 2, 620), (200, 195, 225))

def draw_level_up(surf, choices, t):
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((5, 3, 15, 190))
    surf.blit(dim, (0, 0))
    glow = (255, int(210 + 40 * math.sin(t * 6)), 120)
    text(surf, "LEVEL UP!", 72, (W // 2, 130), glow, bold=True,
         shadow=(90, 50, 0))
    text(surf, "choose your forbidden upgrade", 26, (W // 2, 190), (200, 190, 230))
    for i, (name, desc) in enumerate(choices):
        rect = pygame.Rect(W // 2 - 260, 240 + i * 110, 520, 88)
        panel(surf, rect, alpha=220)
        pygame.draw.rect(surf, (150, 110, 255), rect, 2, border_radius=8)
        text(surf, f"[{i + 1}]  {name}", 30, (rect.x + 20, rect.y + 26),
             (255, 235, 180), center=False, bold=True)
        text(surf, desc, 22, (rect.x + 20, rect.y + 60), (200, 195, 225),
             center=False)
    text(surf, "press 1, 2 or 3", 22, (W // 2, 620), (150, 145, 175))

def draw_banner(surf, banner_text, sub, frac):
    """Wave banner: frac goes 1 -> 0 over its lifetime."""
    alpha = min(1.0, frac * 3) * min(1.0, (1 - frac) * 5 + 0.2)
    y = int(H * 0.30)
    text(surf, banner_text, 64, (W // 2, y),
         tuple(int(c * alpha) for c in (255, 220, 150)), bold=True,
         shadow=(60, 30, 0))
    if sub:
        text(surf, sub, 26, (W // 2, y + 48),
             tuple(int(c * alpha) for c in (210, 200, 235)))

class FloatingText:
    def __init__(self, pos, s, color=(230, 225, 245), size=20, life=1.1, vy=-46):
        self.x, self.y = pos
        self.s, self.color, self.size = s, color, size
        self.life = self.max_life = life
        self.vy = vy

    def update(self, dt):
        self.y += self.vy * dt
        self.vy *= (1 - 1.2 * dt)
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        t = max(0.0, self.life / self.max_life)
        c = tuple(int(v * (0.4 + 0.6 * t)) for v in self.color)
        text(surf, self.s, self.size, (int(self.x), int(self.y)), c)