"""THE GREAT KUPER — final boss with two phases."""

import math
import random
import pygame
from config import SCREEN_W, SCREEN_H, ARENA_MARGIN, BOSS, C_BOSS
from spells import Projectile

class BossNova:
    """Boss ground slam: expanding ring that damages the PLAYER once."""

    def __init__(self, pos, max_radius, damage):
        self.pos = pygame.math.Vector2(pos)
        self.max_radius = max_radius
        self.damage = damage
        self.radius = 20.0
        self.done = False
        self.hit = False

    def update(self, dt, particles):
        self.radius += 420 * dt
        if self.radius >= self.max_radius:
            self.done = True
        if random.random() < 0.9:
            particles.ring(self.pos, 6, self.radius,
                           [(255, 90, 60), (255, 170, 60)], life=(0.15, 0.3))

    def check_player(self, player):
        from config import PLAYER_RADIUS
        if not self.hit and self.pos.distance_to(player.pos) <= self.radius + PLAYER_RADIUS:
            self.hit = True
            return self.damage
        return 0

    def draw(self, surf):
        t = 1.0 - self.radius / self.max_radius
        c = (int(255 * t), int(90 * t), int(50 * t))
        pygame.draw.circle(surf, c, (int(self.pos.x), int(self.pos.y)),
                           int(self.radius), width=max(2, int(12 * t)))

class GreatKuper:
    """Giant ridiculous wizard-demon. Phase 2 at 50% HP: pure KUPERFURY."""

    def __init__(self, pos):
        self.pos = pygame.math.Vector2(pos)
        self.radius = BOSS["radius"]
        self.max_hp = BOSS["hp"]
        self.hp = float(self.max_hp)
        self.speed = BOSS["speed1"]
        self.phase = 1
        self.spread_cd = 1.5
        self.aimed_cd = 1.0
        self.slam_cd = BOSS["slam_cd1"]
        self.contact_cd = 0.0
        self.hurt_t = 0.0
        self.t = random.uniform(0, 10)
        self.dead = False
        self.name = "THE GREAT KUPER"
        self.contact_damage = BOSS["contact"]
        self.score = BOSS["score"]
        self.xp = 0
        self.phase2_announced = False

    # ------------------------------------------------------------------
    def take_damage(self, amount):
        self.hp -= amount
        self.hurt_t = 0.1
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
        # phase transition
        if self.phase == 1 and self.hp <= self.max_hp * 0.5:
            self.phase = 2
            self.speed = BOSS["speed2"]
        return self.dead

    @property
    def phase_just_changed(self):
        return self.phase == 2

    def update(self, dt, player, slow, projectiles_out, boss_novas_out, particles):
        self.t += dt
        if self.contact_cd > 0:
            self.contact_cd -= dt
        if self.hurt_t > 0:
            self.hurt_t -= dt
        rage = slow  # time disintegrator slows the boss too (he is an enemy)

        # --- chase the player
        to_p = player.pos - self.pos
        d = to_p.length()
        if d > self.radius + 20:
            self.pos += (to_p / d) * self.speed * rage * dt
        self.pos.x = max(ARENA_MARGIN, min(SCREEN_W - ARENA_MARGIN, self.pos.x))
        self.pos.y = max(ARENA_MARGIN, min(SCREEN_H - ARENA_MARGIN, self.pos.y))

        aim = to_p / max(d, 1)

        # --- spread attack (fan of projectiles)
        self.spread_cd -= dt * rage
        if self.spread_cd <= 0:
            self.spread_cd = (BOSS["spread_cd1"] if self.phase == 1
                              else BOSS["spread_cd2"])
            n = 5 if self.phase == 1 else 8
            base = math.atan2(aim.y, aim.x)
            spread = math.radians(60 if self.phase == 1 else 90)
            for i in range(n):
                a = base - spread / 2 + spread * i / (n - 1)
                vel = pygame.math.Vector2(math.cos(a), math.sin(a)) * 240
                projectiles_out.append(Projectile(
                    self.pos, vel, 12, 9, C_BOSS, friendly=False))
            particles.burst(self.pos, 12, C_BOSS, speed=(40, 130),
                            life=(0.2, 0.5), size=(2, 4))

        # --- aimed heavy shot
        self.aimed_cd -= dt * rage
        if self.aimed_cd <= 0:
            self.aimed_cd = (BOSS["aimed_cd1"] if self.phase == 1
                             else BOSS["aimed_cd2"])
            projectiles_out.append(Projectile(
                self.pos, aim * 330, 16, 13, (255, 120, 240), friendly=False))

        # --- ground slam AoE
        self.slam_cd -= dt * rage
        if self.slam_cd <= 0:
            self.slam_cd = (BOSS["slam_cd1"] if self.phase == 1
                            else BOSS["slam_cd2"])
            boss_novas_out.append(BossNova(self.pos, BOSS["slam_radius"],
                                           BOSS["slam_dmg"]))
            particles.ring(self.pos, 24, 30, [(255, 110, 60), C_BOSS],
                           life=(0.3, 0.6), size=(2, 5))

        # ambient boss aura
        if random.random() < 0.5:
            a = random.uniform(0, math.tau)
            p = self.pos + pygame.math.Vector2(math.cos(a), math.sin(a)) * random.uniform(30, 60)
            particles.mote(p, C_BOSS if self.phase == 1 else (255, 90, 90))

    # ------------------------------------------------------------------
    def draw(self, surf, t):
        x, y = int(self.pos.x), int(self.pos.y + math.sin(self.t * 2) * 3)
        r = self.radius
        p2 = self.phase == 2
        body = (150, 45, 200) if not p2 else (200, 45, 70)

        pygame.draw.ellipse(surf, (8, 5, 12), (x - r, y + r - 8, r * 2, 16))

        # demon horns
        for s in (-1, 1):
            pygame.draw.polygon(surf, (240, 230, 200), [
                (x + s * (r - 10), y - r + 12),
                (x + s * (r + 20), y - r - 26),
                (x + s * (r - 26), y - r + 4)])

        # robe
        robe = [(x, y - r - 6), (x - r, y + r), (x + r, y + r)]
        pygame.draw.polygon(surf, body, robe)
        pygame.draw.polygon(surf, (30, 15, 45), robe, width=3)

        # giant hat
        pygame.draw.polygon(surf, (40, 20, 70) if not p2 else (60, 15, 25),
                            [(x - r + 6, y - r + 6), (x + r - 6, y - r + 6),
                             (x + 10, y - r - 70)])
        pygame.draw.ellipse(surf, (40, 20, 70) if not p2 else (60, 15, 25),
                            (x - r - 8, y - r - 2, (r + 8) * 2, 16))

        # burning eyes
        ec = (255, 240, 120) if not p2 else (255, 80, 40)
        glow = 5 + int(2 * math.sin(t * 8))
        pygame.draw.circle(surf, ec, (x - 16, y - 26), glow)
        pygame.draw.circle(surf, ec, (x + 16, y - 26), glow)
        pygame.draw.circle(surf, (20, 0, 0), (x - 16, y - 26), 2)
        pygame.draw.circle(surf, (20, 0, 0), (x + 16, y - 26), 2)

        # beard (yes, the demon has a beard, do not question it)
        pygame.draw.polygon(surf, (210, 205, 220),
                            [(x - 14, y - 16), (x + 14, y - 16), (x, y + 22)])

        # hurt flash
        if self.hurt_t > 0:
            pygame.draw.circle(surf, (255, 255, 255), (x, y - 10), r + 6, width=3)