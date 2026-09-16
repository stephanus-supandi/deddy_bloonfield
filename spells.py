"""Projectiles and the DEADLY NOVA area effect."""

import math
import random
import pygame
from config import (SCREEN_W, SCREEN_H, C_NOVA)

class Projectile:
    """Generic magic projectile. friendly=True hits enemies, False hits player."""

    def __init__(self, pos, vel, damage, radius, color, friendly=True,
                 explode=False, blast_radius=0, blast_damage=0, trail=True):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.damage = damage
        self.radius = radius
        self.color = color
        self.friendly = friendly
        self.explode = explode              # kuper blast style AoE on impact
        self.blast_radius = blast_radius
        self.blast_damage = blast_damage
        self.trail = trail
        self.t = random.uniform(0, 10)      # phase for wobble visuals

    def update(self, dt, particles):
        self.t += dt
        self.pos += self.vel * dt
        if self.trail:
            particles.trail(self.pos, self.color, size=max(1, self.radius // 2))
        m = 60
        return (-m < self.pos.x < SCREEN_W + m and -m < self.pos.y < SCREEN_H + m)

    def draw(self, surf):
        x, y = int(self.pos.x), int(self.pos.y)
        pulse = 1.0 + 0.18 * math.sin(self.t * 22)
        r = self.radius * pulse
        # outer glow
        glow = tuple(int(c * 0.35) for c in self.color)
        pygame.draw.circle(surf, glow, (x, y), int(r * 2.1))
        pygame.draw.circle(surf, self.color, (x, y), int(r))
        pygame.draw.circle(surf, (255, 255, 255), (x, y), max(1, int(r * 0.45)))

class Nova:
    """Expanding ring AoE. Damages each entity at most once."""

    def __init__(self, pos, max_radius, damage, color=C_NOVA, speed=520.0):
        self.pos = pygame.math.Vector2(pos)
        self.max_radius = max_radius
        self.damage = damage
        self.color = color
        self.speed = speed
        self.radius = 12.0
        self.hit_ids = set()
        self.done = False

    def update(self, dt, particles):
        self.radius += self.speed * dt
        if self.radius >= self.max_radius:
            self.done = True
        if random.random() < 0.9:
            particles.ring(self.pos, 5, self.radius, self.color,
                           life=(0.15, 0.3), size=(1, 3))

    def newly_hit(self, entities):
        """Return entities touched by the ring front for the first time."""
        hits = []
        for e in entities:
            if id(e) in self.hit_ids:
                continue
            d = self.pos.distance_to(e.pos)
            if d <= self.radius + e.radius:
                self.hit_ids.add(id(e))
                hits.append(e)
        return hits

    def draw(self, surf):
        t = 1.0 - self.radius / self.max_radius
        c = tuple(int(v * t) for v in self.color)
        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.circle(surf, c, (x, y), int(self.radius), width=max(2, int(10 * t)))
        inner = tuple(int(v * t * 0.5) for v in self.color)
        pygame.draw.circle(surf, inner, (x, y), int(self.radius * 0.72), width=2)