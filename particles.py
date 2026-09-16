"""Lightweight particle system. Pure pygame primitives, lifetime cleanup."""

import math
import random
import pygame

MAX_PARTICLES = 1400

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "size", "color", "gravity", "additive")

    def __init__(self, pos, vel, life, size, color, gravity=0.0, additive=True):
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.life = self.max_life = life
        self.size = size
        self.color = color
        self.gravity = gravity
        self.additive = additive

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf, add_surf):
        t = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * t))
        # color fades toward black == fake alpha, very cheap
        c = (int(self.color[0] * t), int(self.color[1] * t), int(self.color[2] * t))
        target = add_surf if self.additive else surf
        pygame.draw.circle(target, c, (int(self.x), int(self.y)), r)

class ParticleSystem:
    def __init__(self):
        self.particles = []
        # reusable additive surface (glow look without per-particle surfaces)
        self._add = pygame.Surface((SCREEN_W_, SCREEN_H_))
        self._add.set_colorkey((0, 0, 0))

    # ------------------------------------------------------------ emitters
    def _spawn(self, p):
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(p)
        else:  # recycle oldest instead of dropping new effects
            self.particles.pop(0)
            self.particles.append(p)

    def burst(self, pos, count, color, speed=(40, 180), life=(0.25, 0.7),
              size=(1, 4), gravity=0.0, spread=math.tau):
        """Radial explosion of particles."""
        for _ in range(count):
            a = random.uniform(0, spread)
            s = random.uniform(*speed)
            c = random.choice(color) if isinstance(color, list) else color
            self._spawn(Particle(pos, (math.cos(a) * s, math.sin(a) * s),
                                 random.uniform(*life), random.uniform(*size),
                                 c, gravity))

    def ring(self, pos, count, radius, color, life=(0.3, 0.6), size=(2, 4)):
        """Ring of particles (used by nova / boss slam telegraphs)."""
        for i in range(count):
            a = math.tau * i / count
            p = (pos[0] + math.cos(a) * radius, pos[1] + math.sin(a) * radius)
            v = (math.cos(a) * 60, math.sin(a) * 60)
            c = random.choice(color) if isinstance(color, list) else color
            self._spawn(Particle(p, v, random.uniform(*life),
                                 random.uniform(*size), c))

    def trail(self, pos, color, size=2, jitter=3.0):
        p = (pos[0] + random.uniform(-jitter, jitter),
             pos[1] + random.uniform(-jitter, jitter))
        v = (random.uniform(-18, 18), random.uniform(-18, 18))
        self._spawn(Particle(p, v, random.uniform(0.15, 0.35), size, color))

    def mote(self, pos, color):
        """Slow floating ambient mote."""
        v = (random.uniform(-12, 12), random.uniform(-26, -8))
        self._spawn(Particle(pos, v, random.uniform(2.0, 4.5),
                             random.uniform(1, 2.5), color, additive=True))

    def fountain(self, pos, count, color):
        """Upward celebratory burst (level up)."""
        for _ in range(count):
            a = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
            s = random.uniform(90, 260)
            self._spawn(Particle(pos, (math.cos(a) * s, math.sin(a) * s),
                                 random.uniform(0.6, 1.3), random.uniform(2, 5),
                                 color, gravity=260))

    # ------------------------------------------------------------ frame
    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surf):
        self._add.fill((0, 0, 0))
        for p in self.particles:
            p.draw(surf, self._add)
        surf.blit(self._add, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

# late import guard to avoid circular config import cost
from config import SCREEN_W as SCREEN_W_, SCREEN_H as SCREEN_H_  # noqa: E402