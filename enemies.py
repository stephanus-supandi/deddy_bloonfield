"""BLOON MINION, NECROMANCER, KUPER DEMON."""

import math
import random
import pygame
from config import (
    SCREEN_W, SCREEN_H, ARENA_MARGIN,
    BLOON, NECRO, DEMON, C_ENEMY_PROJ,
)
from spells import Projectile

class Enemy:
    """Base enemy. Subclasses override stats + draw."""

    def __init__(self, pos, cfg):
        self.pos = pygame.math.Vector2(pos)
        self.max_hp = cfg["hp"]
        self.hp = float(self.max_hp)
        self.speed = cfg["speed"]
        self.radius = cfg["radius"]
        self.contact_damage = cfg["contact"]
        self.xp = cfg["xp"]
        self.score = cfg["score"]
        self.contact_cd = 0.0
        self.hurt_t = 0.0
        self.wobble = random.uniform(0, math.tau)

    # ------------------------------------------------------------------
    def take_damage(self, amount):
        self.hp -= amount
        self.hurt_t = 0.12
        return self.hp <= 0

    def _clamp(self):
        self.pos.x = max(ARENA_MARGIN, min(SCREEN_W - ARENA_MARGIN, self.pos.x))
        self.pos.y = max(ARENA_MARGIN, min(SCREEN_H - ARENA_MARGIN, self.pos.y))

    def update(self, dt, player, slow, projectiles_out, particles):
        """Simple chase AI: direction vector * speed * dt."""
        self.wobble += dt * 6
        if self.contact_cd > 0:
            self.contact_cd -= dt
        if self.hurt_t > 0:
            self.hurt_t -= dt
        to_player = player.pos - self.pos
        d = to_player.length()
        if d > 1:
            self.move(dt, to_player / d, slow)
        self._clamp()

    def move(self, dt, dir_norm, slow):
        self.pos += dir_norm * self.speed * slow * dt

    def draw(self, surf, t):
        raise NotImplementedError

    def _hp_pip(self, surf, x, y, w=26):
        if self.hp < self.max_hp:
            frac = max(0.0, self.hp / self.max_hp)
            pygame.draw.rect(surf, (30, 20, 20), (x - w // 2, y, w, 3))
            pygame.draw.rect(surf, (230, 70, 70), (x - w // 2, y, int(w * frac), 3))

class BloonMinion(Enemy):
    """A sinister balloon that chose violence. Chases and body-slams."""

    def __init__(self, pos):
        super().__init__(pos, BLOON)
        self.name = "BLOON MINION"

    def update(self, dt, player, slow, projectiles_out, particles):
        super().update(dt, player, slow, projectiles_out, particles)
        if random.random() < 0.10 * slow:
            particles.trail(self.pos + pygame.math.Vector2(0, self.radius), (220, 80, 80), size=1)

    def draw(self, surf, t):
        x, y = int(self.pos.x), int(self.pos.y + math.sin(self.wobble) * 2.5)
        # string + knot (it IS a balloon)
        pygame.draw.line(surf, (160, 160, 170), (x, y + self.radius),
                         (x + int(math.sin(self.wobble) * 4), y + self.radius + 9), 1)
        pygame.draw.polygon(surf, (190, 50, 50),
                            [(x - 3, y + self.radius - 1), (x + 3, y + self.radius - 1),
                             (x, y + self.radius + 4)])
        pygame.draw.circle(surf, (220, 70, 70), (x, y), self.radius)
        pygame.draw.circle(surf, (255, 150, 150), (x - 4, y - 5), 4)  # shine
        # angry eyes
        pygame.draw.circle(surf, (255, 255, 255), (x - 4, y - 1), 3)
        pygame.draw.circle(surf, (255, 255, 255), (x + 4, y - 1), 3)
        pygame.draw.circle(surf, (20, 10, 10), (x - 4, y), 1)
        pygame.draw.circle(surf, (20, 10, 10), (x + 4, y), 1)
        pygame.draw.line(surf, (60, 10, 10), (x - 7, y - 6), (x - 2, y - 4), 2)
        pygame.draw.line(surf, (60, 10, 10), (x + 7, y - 6), (x + 2, y - 4), 2)
        self._hp_pip(surf, x, y - self.radius - 8)

class Necromancer(Enemy):
    """Ranged caster. Keeps its distance and hurls dark magic."""

    def __init__(self, pos):
        super().__init__(pos, NECRO)
        self.name = "NECROMANCER"
        self.shoot_cd = random.uniform(0.6, NECRO["shoot_cd"])
        self.preferred = NECRO["range"]

    def update(self, dt, player, slow, projectiles_out, particles):
        self.wobble += dt * 6
        if self.contact_cd > 0:
            self.contact_cd -= dt
        if self.hurt_t > 0:
            self.hurt_t -= dt
        to_player = player.pos - self.pos
        d = to_player.length()
        if d > 1:
            n = to_player / d
            # keep preferred distance: approach if far, back off if too close
            if d > self.preferred + 30:
                self.move(dt, n, slow)
            elif d < self.preferred - 60:
                self.move(dt, -n, slow)
            else:  # strafe
                self.move(dt, pygame.math.Vector2(-n.y, n.x), slow * 0.6)
        self._clamp()
        # shoot
        self.shoot_cd -= dt * slow
        if self.shoot_cd <= 0 and d < 520:
            self.shoot_cd = NECRO["shoot_cd"] * random.uniform(0.85, 1.2)
            vel = (to_player / max(d, 1)) * NECRO["proj_speed"]
            projectiles_out.append(Projectile(
                self.pos, vel, NECRO["proj_dmg"], 7, C_ENEMY_PROJ,
                friendly=False))
            particles.burst(self.pos, 6, C_ENEMY_PROJ, speed=(30, 80),
                            life=(0.15, 0.35), size=(1, 3))

    def draw(self, surf, t):
        x, y = int(self.pos.x), int(self.pos.y + math.sin(self.wobble * 0.7) * 2)
        pygame.draw.ellipse(surf, (8, 6, 12), (x - 14, y + 12, 28, 8))
        robe = [(x, y - 18), (x - 14, y + 15), (x + 14, y + 15)]
        pygame.draw.polygon(surf, (52, 66, 52), robe)
        pygame.draw.polygon(surf, (28, 38, 30), robe, width=2)
        # hood
        pygame.draw.circle(surf, (40, 52, 42), (x, y - 16), 9)
        pygame.draw.circle(surf, (12, 16, 12), (x, y - 15), 6)
        # glowing eyes
        glow = 2 + int(math.sin(t * 5 + self.wobble) >= 0)
        pygame.draw.circle(surf, (170, 255, 120), (x - 3, y - 15), glow)
        pygame.draw.circle(surf, (170, 255, 120), (x + 3, y - 15), glow)
        self._hp_pip(surf, x, y - 30)

class KuperDemon(Enemy):
    """Large, slow, extremely rude."""

    def __init__(self, pos):
        super().__init__(pos, DEMON)
        self.name = "KUPER DEMON"

    def update(self, dt, player, slow, projectiles_out, particles):
        super().update(dt, player, slow, projectiles_out, particles)
        if random.random() < 0.15 * slow:
            particles.trail(self.pos, (200, 90, 40), size=2)

    def draw(self, surf, t):
        x, y = int(self.pos.x), int(self.pos.y + math.sin(self.wobble * 0.6) * 2)
        r = self.radius
        pygame.draw.ellipse(surf, (10, 6, 8), (x - r, y + r - 6, r * 2, 12))
        # horns
        pygame.draw.polygon(surf, (230, 220, 190),
                            [(x - r + 4, y - r + 6), (x - r - 8, y - r - 14), (x - r + 14, y - r + 2)])
        pygame.draw.polygon(surf, (230, 220, 190),
                            [(x + r - 4, y - r + 6), (x + r + 8, y - r - 14), (x + r - 14, y - r + 2)])
        pygame.draw.circle(surf, (130, 32, 32), (x, y), r)
        pygame.draw.circle(surf, (90, 20, 20), (x, y), r, width=3)
        # eyes + grin
        pygame.draw.circle(surf, (255, 220, 60), (x - 9, y - 6), 4)
        pygame.draw.circle(surf, (255, 220, 60), (x + 9, y - 6), 4)
        pygame.draw.circle(surf, (20, 10, 0), (x - 9, y - 6), 2)
        pygame.draw.circle(surf, (20, 10, 0), (x + 9, y - 6), 2)
        pygame.draw.arc(surf, (250, 240, 220),
                        (x - 12, y - 2, 24, 16), math.pi * 1.15, math.pi * 1.85, 2)
        self._hp_pip(surf, x, y - r - 10, w=40)

def make_enemy(kind, pos):
    if kind == "bloon":
        return BloonMinion(pos)
    if kind == "necro":
        return Necromancer(pos)
    if kind == "demon":
        return KuperDemon(pos)
    raise ValueError(f"unknown enemy kind: {kind}")