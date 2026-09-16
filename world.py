"""Procedurally generated magical arena background + vignette."""

import math
import random
import pygame
from config import SCREEN_W as W, SCREEN_H as H, C_BG_TOP, C_BG_BOTTOM, C_FLOOR, C_RUNE

def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

class World:
    def __init__(self):
        rng = random.Random(1337)   # fixed seed: same arena every run
        self.bg = self._build_background(rng)
        self.glow = self._build_center_glow()
        self.vignette = self._build_vignette()
        self.ambient_cd = 0.0

    # ------------------------------------------------------------------
    def _build_background(self, rng):
        surf = pygame.Surface((W, H))
        # vertical gradient
        for y in range(H):
            pygame.draw.line(surf, _lerp(C_BG_TOP, C_BG_BOTTOM, y / H), (0, y), (W, y))

        # stone floor tiles with grout
        tile = 64
        for ty in range(0, H, tile):
            for tx in range(0, W, tile):
                shade = rng.randint(-6, 6)
                c = (C_FLOOR[0] + shade, C_FLOOR[1] + shade, C_FLOOR[2] + shade)
                pygame.draw.rect(surf, c, (tx + 1, ty + 1, tile - 2, tile - 2),
                                 border_radius=4)
        # cracks
        for _ in range(26):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            pts = [(x, y)]
            for _ in range(rng.randint(2, 4)):
                x += rng.uniform(-40, 40)
                y += rng.uniform(-40, 40)
                pts.append((x, y))
            pygame.draw.lines(surf, (16, 12, 28), False, pts, 1)

        # ---- central magic circle
        cx, cy = W // 2, H // 2
        pygame.draw.circle(surf, C_RUNE, (cx, cy), 150, 2)
        pygame.draw.circle(surf, C_RUNE, (cx, cy), 138, 1)
        pygame.draw.circle(surf, C_RUNE, (cx, cy), 60, 1)
        # hexagram
        for rot in (0, math.pi / 3):
            pts = [(cx + 120 * math.cos(rot + math.tau * i / 3),
                    cy + 120 * math.sin(rot + math.tau * i / 3)) for i in range(3)]
            pygame.draw.polygon(surf, C_RUNE, pts, 1)
        # rune ticks around the circle
        for i in range(24):
            a = math.tau * i / 24
            x1, y1 = cx + 152 * math.cos(a), cy + 152 * math.sin(a)
            x2, y2 = cx + 164 * math.cos(a), cy + 164 * math.sin(a)
            pygame.draw.line(surf, C_RUNE, (x1, y1), (x2, y2), 2)

        # ---- scattered rune glyphs
        for _ in range(40):
            gx, gy = rng.uniform(30, W - 30), rng.uniform(30, H - 30)
            if abs(gx - cx) < 190 and abs(gy - cy) < 190:
                continue
            kind = rng.randint(0, 3)
            col = (C_RUNE[0] - 12, C_RUNE[1] - 12, C_RUNE[2] - 10)
            if kind == 0:
                pygame.draw.circle(surf, col, (gx, gy), rng.randint(4, 9), 1)
            elif kind == 1:
                pygame.draw.line(surf, col, (gx - 7, gy - 7), (gx + 7, gy + 7), 1)
                pygame.draw.line(surf, col, (gx - 7, gy + 7), (gx + 7, gy - 7), 1)
            elif kind == 2:
                pygame.draw.polygon(surf, col, [(gx, gy - 8), (gx - 7, gy + 6), (gx + 7, gy + 6)], 1)
            else:
                pygame.draw.rect(surf, col, (gx - 6, gy - 6, 12, 12), 1)

        # ---- decorative corner braziers
        for bx, by in [(60, 60), (W - 60, 60), (60, H - 60), (W - 60, H - 60)]:
            pygame.draw.circle(surf, (46, 38, 70), (bx, by), 22)
            pygame.draw.circle(surf, C_RUNE, (bx, by), 22, 2)
            pygame.draw.circle(surf, (70, 55, 120), (bx, by), 10)
        return surf

    def _build_center_glow(self):
        size = 420
        g = pygame.Surface((size, size))
        g.set_colorkey((0, 0, 0))
        c = size // 2
        for r in range(c, 0, -4):
            v = int(14 * (1 - r / c))
            pygame.draw.circle(g, (v, v // 2, v * 2), (c, c), r)
        return g

    def _build_vignette(self):
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        bands = 70
        for i in range(bands):
            a = int(85 * (1 - i / bands) ** 1.6)
            inset = i * 4
            pygame.draw.rect(v, (0, 0, 0, a),
                             (inset, inset, W - inset * 2, H - inset * 2), width=5)
        return v

    # ------------------------------------------------------------------
    def update(self, dt, particles):
        self.ambient_cd -= dt
        if self.ambient_cd <= 0:
            self.ambient_cd = 0.12
            particles.mote((random.uniform(0, W), random.uniform(H * 0.3, H)),
                           random.choice([(90, 70, 160), (60, 90, 160), (120, 80, 180)]))

    def draw(self, surf, t):
        surf.blit(self.bg, (0, 0))
        # pulsing center glow (additive)
        self.glow.set_alpha(0)  # alpha ignored under ADD; pulse via pre-scaled copy is overkill,
        surf.blit(self.glow, (W // 2 - 210, H // 2 - 210),
                  special_flags=pygame.BLEND_RGB_ADD)
        # slow rune pulse: a second additive pass whose brightness oscillates
        pulse = 0.5 + 0.5 * math.sin(t * 1.4)
        if pulse > 0.55:
            ring_c = (int(24 * pulse), int(12 * pulse), int(40 * pulse))
            pygame.draw.circle(surf, ring_c, (W // 2, H // 2), 150, 2)
        surf.blit(self.vignette, (0, 0))