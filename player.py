"""DEADLY KUPERFIELD himself — the wizard who should not have passed."""

import math
import random
import pygame
from config import (
    SCREEN_W, SCREEN_H, ARENA_MARGIN, PLAYER_MAX_HP, PLAYER_SPEED, PLAYER_RADIUS,
    BOLT_CD, BOLT_SPEED, BOLT_DAMAGE, BOLT_RADIUS,
    BLAST_CD, BLAST_SPEED, BLAST_DAMAGE, BLAST_RADIUS,
    BLAST_EXPLODE_RAD, BLAST_EXPLODE_DMG,
    NOVA_CD, NOVA_MAX_RADIUS, NOVA_DAMAGE, NOVA_SPEED,
    DISINT_CD, DISINT_DURATION, xp_needed,
    C_PLAYER, C_HAT, C_EYE_GLOW, C_BOLT, C_BLAST, C_NOVA,
)
from spells import Projectile, Nova

class Player:
    def __init__(self, pos):
        self.pos = pygame.math.Vector2(pos)
        self.aim = pygame.math.Vector2(1, 0)
        self.max_hp = PLAYER_MAX_HP
        self.hp = float(self.max_hp)
        self.speed = PLAYER_SPEED
        self.level = 1
        self.xp = 0
        # upgrade multipliers
        self.damage_mult = 1.0
        self.cd_mult = 1.0          # lower = faster casting
        self.radius_mult = 1.0
        # cooldown trackers
        self.cds = {"bolt": 0.0, "blast": 0.0, "nova": 0.0, "disint": 0.0}
        self.cd_max = {"bolt": BOLT_CD, "blast": BLAST_CD,
                       "nova": NOVA_CD, "disint": DISINT_CD}
        self.invuln = 0.0           # brief mercy invulnerability after a hit
        self.walk_t = 0.0
        self.dead = False

    # ---------------------------------------------------------------- movement
    def move(self, dt, dir_vec):
        if dir_vec.length_squared() > 0:
            dir_vec = dir_vec.normalize()      # diagonals are NOT faster
            self.pos += dir_vec * self.speed * dt
            self.walk_t += dt * 10
        self.pos.x = max(ARENA_MARGIN, min(SCREEN_W - ARENA_MARGIN, self.pos.x))
        self.pos.y = max(ARENA_MARGIN, min(SCREEN_H - ARENA_MARGIN, self.pos.y))

    def aim_at(self, mouse_pos):
        v = pygame.math.Vector2(mouse_pos) - self.pos
        if v.length_squared() > 1:
            self.aim = v.normalize()

    @property
    def angle(self):
        return math.atan2(self.aim.y, self.aim.x)

    @property
    def staff_tip(self):
        return self.pos + self.aim * 30

    # ---------------------------------------------------------------- spells
    def _tick_cooldowns(self, dt):
        for k in self.cds:
            if self.cds[k] > 0:
                self.cds[k] = max(0.0, self.cds[k] - dt)
        if self.invuln > 0:
            self.invuln = max(0.0, self.invuln - dt)

    def can_cast(self, name):
        return self.cds[name] <= 0.0

    def _effective_cd(self, name):
        return self.cd_max[name] * self.cd_mult

    def cast_bolt(self, particles):
        self.cds["bolt"] = self._effective_cd("bolt")
        tip = self.staff_tip
        vel = self.aim * BOLT_SPEED
        dmg = BOLT_DAMAGE * self.damage_mult
        r = BOLT_RADIUS * self.radius_mult
        particles.burst(tip, 5, C_BOLT, speed=(30, 90), life=(0.1, 0.25), size=(1, 2))
        return Projectile(tip, vel, dmg, r, C_BOLT, friendly=True)

    def cast_blast(self, particles):
        self.cds["blast"] = self._effective_cd("blast")
        tip = self.staff_tip
        vel = self.aim * BLAST_SPEED
        dmg = BLAST_DAMAGE * self.damage_mult
        r = BLAST_RADIUS * self.radius_mult
        br = BLAST_EXPLODE_RAD * self.radius_mult
        particles.burst(tip, 14, [C_BLAST, (255, 220, 140)], speed=(50, 160),
                        life=(0.2, 0.5), size=(2, 4))
        return Projectile(tip, vel, dmg, r, C_BLAST, friendly=True,
                          explode=True, blast_radius=br, blast_damage=dmg * 0.6)

    def cast_nova(self, particles):
        self.cds["nova"] = self._effective_cd("nova")
        particles.burst(self.pos, 26, C_NOVA, speed=(80, 240),
                        life=(0.3, 0.7), size=(2, 4))
        return Nova(self.pos, NOVA_MAX_RADIUS * self.radius_mult,
                    NOVA_DAMAGE * self.damage_mult, C_NOVA, NOVA_SPEED)

    # ---------------------------------------------------------------- combat
    def take_damage(self, amount):
        if self.invuln > 0 or self.dead:
            return False
        self.hp -= amount
        self.invuln = 0.35
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
        return True

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_xp(self, amount):
        """Returns number of level-ups gained."""
        self.xp += amount
        ups = 0
        while self.xp >= xp_needed(self.level):
            self.xp -= xp_needed(self.level)
            self.level += 1
            ups += 1
        return ups

    # ---------------------------------------------------------------- frame
    def update(self, dt, particles, time_slow_active):
        self._tick_cooldowns(dt)
        # floating wizard aura motes
        if random.random() < 0.35:
            a = random.uniform(0, math.tau)
            p = self.pos + pygame.math.Vector2(math.cos(a), math.sin(a)) * random.uniform(10, 22)
            particles.mote(p, C_EYE_GLOW if not time_slow_active else (170, 120, 255))

    def draw(self, surf, t, time_slow_active):
        p = self.pos
        ang = self.angle
        bob = math.sin(self.walk_t) * 1.6
        x, y = int(p.x), int(p.y + bob)

        # shadow
        pygame.draw.ellipse(surf, (8, 6, 14), pygame.Rect(x - 17, y + 12, 34, 10))

        # time-disintegrator aura
        if time_slow_active:
            pulse = 26 + 5 * math.sin(t * 9)
            pygame.draw.circle(surf, (90, 55, 170), (x, y), int(pulse), width=3)
            pygame.draw.circle(surf, (140, 90, 230), (x, y), int(pulse * 0.7), width=1)

        # cloak / robe (triangle body)
        robe = [(x, y - 16), (x - 17, y + 16), (x + 17, y + 16)]
        pygame.draw.polygon(surf, C_PLAYER, robe)
        pygame.draw.polygon(surf, (40, 22, 84), robe, width=2)

        # head
        pygame.draw.circle(surf, (205, 175, 150), (x, y - 18), 8)

        # giant dramatic wizard hat, tip leans toward aim
        tipx = x + int(math.cos(ang) * 10)
        tipy = y - 52 + int(math.sin(ang) * 4)
        hat = [(x - 13, y - 22), (x + 13, y - 22), (tipx, tipy)]
        pygame.draw.polygon(surf, C_HAT, hat)
        pygame.draw.ellipse(surf, C_HAT, pygame.Rect(x - 16, y - 26, 32, 9))
        pygame.draw.circle(surf, (255, 210, 90), (tipx, tipy), 3)  # hat star

        # glowing eyes (offset toward aim direction)
        ex = x + int(math.cos(ang) * 4)
        ey = y - 19 + int(math.sin(ang) * 3)
        perp = ang + math.pi / 2
        for s in (-1, 1):
            gx = ex + int(math.cos(perp) * 3 * s)
            gy = ey + int(math.sin(perp) * 3 * s)
            pygame.draw.circle(surf, C_EYE_GLOW, (gx, gy), 2)

        # staff pointing at the cursor, orb at the tip
        hx, hy = x - int(math.cos(ang) * 6), y + 4
        tx, ty = int(p.x + math.cos(ang) * 30), int(p.y + math.sin(ang) * 30 + bob)
        pygame.draw.line(surf, (110, 75, 40), (hx, hy), (tx, ty), 3)
        glow_r = 5 + int(2 * math.sin(t * 7))
        pygame.draw.circle(surf, (60, 120, 200), (tx, ty), glow_r + 4)
        pygame.draw.circle(surf, (160, 220, 255), (tx, ty), glow_r)

        # damage flash
        if self.invuln > 0.15:
            pygame.draw.circle(surf, (255, 90, 90), (x, y - 6), 22, width=2)