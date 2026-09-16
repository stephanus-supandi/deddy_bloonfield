"""Main Game class: state machine, waves, collisions, effects, audio."""

import math
import random
import pygame
from config import (
    SCREEN_W as W, SCREEN_H as H, FPS,
    STATE_TITLE, STATE_PLAYING, STATE_PAUSED, STATE_LEVELUP,
    STATE_GAME_OVER, STATE_VICTORY,
    WAVE_DEFS, WAVE_START_DELAY, WAVE_BREAK_DELAY,
    DISINT_DURATION, TIME_SLOW_FACTOR,
    DEATH_MESSAGES, FLAVOR_LINES, xp_needed, PLAYER_RADIUS,
)
from player import Player
from enemies import make_enemy
from boss import GreatKuper
from particles import ParticleSystem
from world import World
import ui

# ============================================================ procedural audio
class SoundManager:
    """Tiny procedural SFX. Fully optional — game runs silently on failure."""

    RATE = 22050

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(self.RATE, -16, 1, 512)
            self.sounds["bolt"]   = self._tone(760, 0.07, 0.10, slide_to=1250)
            self.sounds["blast"]  = self._tone(180, 0.30, 0.22, slide_to=60)
            self.sounds["boom"]   = self._noise(0.35, 0.25)
            self.sounds["nova"]   = self._tone(300, 0.40, 0.18, slide_to=900)
            self.sounds["disint"] = self._tone(520, 0.55, 0.12, slide_to=130)
            self.sounds["hit"]    = self._tone(220, 0.06, 0.12, slide_to=140)
            self.sounds["hurt"]   = self._tone(160, 0.18, 0.22, slide_to=70, square=True)
            self.sounds["die"]    = self._noise(0.25, 0.18)
            self.sounds["levelup"] = self._arp([440, 554, 659, 880], 0.09, 0.14)
            self.sounds["roar"]   = self._tone(90, 0.70, 0.28, slide_to=55, square=True)
            self.sounds["slam"]   = self._noise(0.45, 0.30)
            self.enabled = True
        except Exception:
            self.enabled = False   # no audio device / mixer failure: play silent

    def _tone(self, freq, dur, vol, slide_to=None, square=False):
        n = int(self.RATE * dur)
        buf = bytearray()
        for i in range(n):
            t = i / self.RATE
            f = freq + (slide_to - freq) * (t / dur) if slide_to else freq
            v = vol * (math.sin(2 * math.pi * f * t) if not square
                       else (1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0))
            v *= (1 - t / dur)          # linear decay envelope
            s = int(max(-1.0, min(1.0, v)) * 32767)
            buf += int(s).to_bytes(2, "little", signed=True)
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _noise(self, dur, vol):
        n = int(self.RATE * dur)
        buf = bytearray()
        for i in range(n):
            t = i / self.RATE
            v = random.uniform(-vol, vol) * (1 - t / dur)
            buf += int(v * 32767).to_bytes(2, "little", signed=True)
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _arp(self, freqs, step, vol):
        buf = bytearray()
        for f in freqs:
            n = int(self.RATE * step)
            for i in range(n):
                t = i / self.RATE
                v = vol * math.sin(2 * math.pi * f * t) * (1 - t / step)
                buf += int(v * 32767).to_bytes(2, "little", signed=True)
        return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

# ============================================================ upgrade pool
def _up_maxhp(p):
    p.max_hp += 25
    p.heal(25)

def _up_damage(p):
    p.damage_mult *= 1.25

def _up_speed(p):
    p.speed *= 1.12

def _up_attackspeed(p):
    p.cd_mult = max(0.45, p.cd_mult * 0.85)

def _up_radius(p):
    p.radius_mult *= 1.20

def _up_heal(p):
    p.heal(p.max_hp * 0.5)

UPGRADE_POOL = [
    ("VITALITY RUNES", "+25 Max HP (and heal 25)", _up_maxhp),
    ("FORBIDDEN SYLLABUS", "+25% spell damage", _up_damage),
    ("CAFFEINATED BOOTS", "+12% movement speed", _up_speed),
    ("TENURE OF HASTE", "-15% spell cooldowns", _up_attackspeed),
    ("WIDER KUPERFIELD", "+20% spell radius", _up_radius),
    ("EMERGENCY TEA", "heal 50% of max HP", _up_heal),
]

# ============================================================ game
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.game_surf = pygame.Surface((W, H))   # offscreen buffer for shake
        self.clock = pygame.time.Clock()
        self.world = World()
        self.particles = ParticleSystem()
        self.sounds = SoundManager()
        self.t = 0.0
        self.running = True
        self.start_rect = pygame.Rect(W // 2 - 130, 460, 260, 64)
        self.quit_rect = pygame.Rect(W // 2 - 130, 540, 260, 64)
        self.state = STATE_TITLE
        self.reset()

    # ------------------------------------------------------------------ setup
    def reset(self):
        self.player = Player(pygame.math.Vector2(W / 2, H / 2 + 120))
        self.enemies = []
        self.boss = None
        self.player_projectiles = []
        self.enemy_projectiles = []
        self.novas = []
        self.boss_novas = []
        self.particles.particles.clear()
        self.float_texts = []
        self.wave_index = -1
        self.wave_timer = WAVE_START_DELAY
        self.score = 0
        self.shake = 0.0
        self.flash_timer = 0.0
        self.flash_color = (255, 255, 255)
        self.time_slow_timer = 0.0
        self.banner = None                 # (text, sub, life, max_life)
        self.pending_levelups = 0
        self.upgrade_choices = None
        self.victory_timer = None
        self.gameover_t = 0.0
        self.flavor_cd = 25.0

    @property
    def xp_need(self):
        return xp_needed(self.player.level)

    @property
    def wave_display(self):
        return max(1, self.wave_index + 1)

    @property
    def enemies_left(self):
        if self.state not in (STATE_PLAYING, STATE_PAUSED, STATE_LEVELUP):
            return None
        return len(self.enemies) + (1 if self.boss else 0)

    def start_game(self):
        self.reset()
        self.state = STATE_PLAYING
        pygame.mouse.set_visible(False)

    # ------------------------------------------------------------------ loop
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.t += dt
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    # ------------------------------------------------------------------ events
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False

            elif e.type == pygame.KEYDOWN:
                if self.state == STATE_TITLE:
                    if e.key == pygame.K_RETURN:
                        self.start_game()
                    elif e.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == STATE_PLAYING:
                    if e.key == pygame.K_ESCAPE:
                        self.state = STATE_PAUSED
                        pygame.mouse.set_visible(True)

                elif self.state == STATE_PAUSED:
                    if e.key == pygame.K_ESCAPE:
                        self.state = STATE_PLAYING
                        pygame.mouse.set_visible(False)
                    elif e.key == pygame.K_q:
                        self.running = False

                elif self.state == STATE_LEVELUP:
                    if e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        idx = e.key - pygame.K_1
                        if idx < len(self.upgrade_choices):
                            self.upgrade_choices[idx][2](self.player)
                            self.particles.fountain(self.player.pos, 30,
                                                    (255, 220, 120))
                            self.pending_levelups -= 1
                            if self.pending_levelups <= 0:
                                self.upgrade_choices = None
                                self.state = STATE_PLAYING
                                pygame.mouse.set_visible(False)

                elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
                    if e.key == pygame.K_r:
                        self.start_game()
                    elif e.key == pygame.K_ESCAPE:
                        self.running = False

            elif e.type == pygame.MOUSEBUTTONDOWN and self.state == STATE_TITLE:
                if e.button == 1:
                    if self.start_rect.collidepoint(e.pos):
                        self.start_game()
                    elif self.quit_rect.collidepoint(e.pos):
                        self.running = False

    # ------------------------------------------------------------------ update
    def update(self, dt):
        self.world.update(dt, self.particles)
        self.particles.update(dt)
        self.float_texts = [f for f in self.float_texts if f.update(dt)]

        if self.banner:
            self.banner[2] -= dt
            if self.banner[2] <= 0:
                self.banner = None

        if self.state == STATE_PLAYING:
            self.update_playing(dt)
        elif self.state == STATE_GAME_OVER:
            self.gameover_t += dt

        # decay effects in all gameplay-ish states
        self.shake = max(0.0, self.shake - 26 * dt)
        self.flash_timer = max(0.0, self.flash_timer - 3.2 * dt)

    def update_playing(self, dt):
        p = self.player
        keys = pygame.key.get_pressed()

        # ---- movement (normalized in player.move)
        d = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:    d.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  d.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  d.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: d.x += 1
        p.move(dt, d)
        p.aim_at(pygame.mouse.get_pos())

        # ---- casting
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and p.can_cast("bolt"):
            self.player_projectiles.append(p.cast_bolt(self.particles))
            self.sounds.play("bolt")
        if keys[pygame.K_SPACE] and p.can_cast("blast"):
            self.player_projectiles.append(p.cast_blast(self.particles))
            self.sounds.play("blast")
            self.add_shake(4)
        if keys[pygame.K_q] and p.can_cast("nova"):
            self.novas.append(p.cast_nova(self.particles))
            self.sounds.play("nova")
            self.add_flash((255, 140, 255), 0.5)
            self.add_shake(7)
        if keys[pygame.K_e] and p.can_cast("disint"):
            p.cds["disint"] = p.cd_max["disint"] * p.cd_mult
            self.time_slow_timer = DISINT_DURATION
            self.sounds.play("disint")
            self.particles.burst(p.pos, 40, (160, 120, 255), speed=(60, 260),
                                 life=(0.4, 1.0), size=(2, 5))
            self.add_float(p.pos + pygame.math.Vector2(0, -46),
                           "TIME DISINTEGRATOR!", (190, 150, 255), 26)

        if self.time_slow_timer > 0:
            self.time_slow_timer = max(0.0, self.time_slow_timer - dt)

        slow = TIME_SLOW_FACTOR if self.time_slow_timer > 0 else 1.0
        p.update(dt, self.particles, self.time_slow_timer > 0)

        # ---- waves
        self.update_waves(dt)

        # ---- entities
        for e in self.enemies:
            e.update(dt, p, slow, self.enemy_projectiles, self.particles)
        if self.boss and not self.boss.dead:
            before_phase = self.boss.phase
            self.boss.update(dt, p, slow, self.enemy_projectiles,
                             self.boss_novas, self.particles)
            if self.boss.phase != before_phase:
                self.on_boss_phase2()
        self.boss_novas = [n for n in self.boss_novas
                           if (n.update(dt, self.particles), not n.done)[1]]

        self.player_projectiles = [pr for pr in self.player_projectiles
                                   if pr.update(dt, self.particles)]
        slow_dt = dt * slow
        self.enemy_projectiles = [pr for pr in self.enemy_projectiles
                                  if pr.update(slow_dt, self.particles)]
        #self.enemy_projectiles = [pr for pr in self.enemy_projectiles
        #                          if pr.update(dt, self.particles * slow if False else dt)]
        # enemy projectiles are slowed by time disintegrator too
        # (already handled below via speed scaling on spawn-time; keep simple: they fly)

        for n in self.novas:
            n.update(dt, self.particles)
        self.novas = [n for n in self.novas if not n.done]

        # ---- collisions
        self.handle_collisions(slow)

        # ---- death check
        if p.dead and self.state == STATE_PLAYING:
            self.state = STATE_GAME_OVER
            self.gameover_t = 0.0
            pygame.mouse.set_visible(True)
            self.particles.burst(p.pos, 60, [(255, 90, 90), (255, 200, 120)],
                                 speed=(80, 320), life=(0.5, 1.2), size=(2, 6))
            self.sounds.play("hurt")

        # ---- victory delay after boss death
        if self.victory_timer is not None:
            self.victory_timer -= dt
            if self.victory_timer <= 0 and self.state == STATE_PLAYING:
                self.state = STATE_VICTORY
                pygame.mouse.set_visible(True)

        # ---- pending level-ups open the choice screen
        if self.pending_levelups > 0 and self.state == STATE_PLAYING \
                and self.victory_timer is None:
            self.upgrade_choices = random.sample(UPGRADE_POOL, 3)
            self.state = STATE_LEVELUP
            pygame.mouse.set_visible(True)
            self.sounds.play("levelup")

        # ---- occasional flavor text (never during the boss fight)
        self.flavor_cd -= dt
        if self.flavor_cd <= 0 and not self.boss:
            self.flavor_cd = random.uniform(22, 40)
            self.add_float((W / 2, H - 70), random.choice(FLAVOR_LINES),
                           (140, 135, 165), 20)

    # ------------------------------------------------------------------ waves
    def update_waves(self, dt):
        if self.victory_timer is not None:
            return
        battlefield_empty = not self.enemies and self.boss is None
        if battlefield_empty and self.wave_index + 1 < len(WAVE_DEFS):
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.wave_index += 1
                self.spawn_wave(self.wave_index)
                self.wave_timer = WAVE_BREAK_DELAY

    def spawn_wave(self, idx):
        defn = WAVE_DEFS[idx]
        if "boss" in defn:
            self.boss = GreatKuper((W / 2, 130))
            self.banner = ["THE GREAT KUPER", "he read the forbidden stack overflow post",
                           3.0, 3.0]
            self.add_shake(10)
            self.sounds.play("roar")
        else:
            total = sum(defn.values())
            for kind, count in defn.items():
                for _ in range(count):
                    self.enemies.append(make_enemy(kind, self.random_edge_pos()))
            self.banner = [f"WAVE {idx + 1}", f"{total} fools approach", 2.4, 2.4]

    def random_edge_pos(self):
        m = 50
        for _ in range(12):
            side = random.randint(0, 3)
            if side == 0:    pos = (random.uniform(m, W - m), m)
            elif side == 1:  pos = (random.uniform(m, W - m), H - m)
            elif side == 2:  pos = (m, random.uniform(m, H - m))
            else:            pos = (W - m, random.uniform(m, H - m))
            v = pygame.math.Vector2(pos)
            if v.distance_to(self.player.pos) > 190:
                return v
        return pygame.math.Vector2(m, m)

    def on_boss_phase2(self):
        self.banner = ["PHASE 2", "KUPERFURY UNLEASHED", 2.4, 2.4]
        self.add_shake(12)
        self.add_flash((255, 80, 80), 0.6)
        self.sounds.play("roar")
        self.particles.burst(self.boss.pos, 50, [(255, 90, 90), (255, 180, 80)],
                             speed=(100, 340), life=(0.4, 1.0), size=(2, 6))

    # ------------------------------------------------------------------ combat
    def handle_collisions(self, slow):
        p = self.player

        # ---- player projectiles vs enemies / boss
        for proj in list(self.player_projectiles):
            hit_target = None
            for e in self.enemies:
                if proj.pos.distance_to(e.pos) <= proj.radius + e.radius:
                    hit_target = e
                    break
            if hit_target is None and self.boss and not self.boss.dead:
                if proj.pos.distance_to(self.boss.pos) <= proj.radius + self.boss.radius:
                    hit_target = self.boss
            if hit_target is not None:
                self.player_projectiles.remove(proj)
                if proj.explode:
                    self.explode(proj)
                else:
                    self.damage_target(hit_target, proj.damage, proj.pos, proj.color)
                    self.sounds.play("hit")

        # ---- novas vs enemies / boss
        for nova in self.novas:
            targets = list(self.enemies)
            if self.boss and not self.boss.dead:
                targets.append(self.boss)
            for tgt in nova.newly_hit(targets):
                self.damage_target(tgt, nova.damage, tgt.pos, (255, 140, 255))

        # ---- boss slams vs player
        for bn in self.boss_novas:
            dmg = bn.check_player(p)
            if dmg:
                self.hurt_player(dmg, big=True)

        # ---- enemy projectiles vs player
        for proj in list(self.enemy_projectiles):
            if proj.pos.distance_to(p.pos) <= proj.radius + PLAYER_RADIUS:
                self.enemy_projectiles.remove(proj)
                self.particles.burst(proj.pos, 8, proj.color, speed=(30, 120),
                                     life=(0.15, 0.4), size=(1, 3))
                self.hurt_player(proj.damage)

        # ---- enemy contact damage
        for e in self.enemies:
            if e.contact_cd <= 0 and \
                    e.pos.distance_to(p.pos) <= e.radius + PLAYER_RADIUS:
                e.contact_cd = 0.9
                self.hurt_player(e.contact_damage)
        if self.boss and not self.boss.dead and self.boss.contact_cd <= 0 and \
                self.boss.pos.distance_to(p.pos) <= self.boss.radius + PLAYER_RADIUS:
            self.boss.contact_cd = 1.0
            self.hurt_player(self.boss.contact_damage, big=True)

    def explode(self, proj):
        """Kuper Blast impact: AoE + shake + flash + boom."""
        self.particles.burst(proj.pos, 34,
                             [(255, 170, 60), (255, 100, 40), (255, 230, 150)],
                             speed=(90, 340), life=(0.25, 0.7), size=(2, 6))
        self.particles.ring(proj.pos, 16, proj.blast_radius * 0.5,
                            (255, 160, 60), life=(0.2, 0.45), size=(2, 4))
        self.add_shake(9)
        self.add_flash((255, 170, 80), 0.35)
        self.sounds.play("boom")
        self.damage_target_at(proj.pos, 0, None)  # direct target already outside
        targets = list(self.enemies)
        if self.boss and not self.boss.dead:
            targets.append(self.boss)
        for tgt in targets:
            if proj.pos.distance_to(tgt.pos) <= proj.blast_radius + tgt.radius:
                dmg = proj.damage if tgt is not None else 0
                self.damage_target(tgt, proj.blast_damage, tgt.pos, (255, 160, 60))

    def damage_target(self, target, damage, pos, color):
        died = target.take_damage(damage)
        self.particles.burst(pos, 6, color, speed=(40, 150),
                             life=(0.15, 0.4), size=(1, 3))
        if died:
            self.on_kill(target)

    def damage_target_at(self, pos, damage, target):
        pass  # kept for clarity; explosion AoE handled in explode()

    def on_kill(self, target):
        is_boss = isinstance(target, GreatKuper)
        self.score += target.score
        self.particles.burst(target.pos, 26 if not is_boss else 90,
                             [(255, 220, 120), (255, 120, 80), (200, 140, 255)],
                             speed=(70, 280) if not is_boss else (120, 460),
                             life=(0.3, 0.9), size=(2, 5))
        self.sounds.play("die")
        if is_boss:
            target.dead = True
            self.boss = None
            self.add_shake(18)
            self.add_flash((255, 255, 255), 1.0)
            self.sounds.play("boom")
            self.victory_timer = 2.2
            self.add_float(target.pos, "+5000", (255, 230, 150), 34)
            self.banner = ["KUPER DOWN", "impossible. absolutely impossible.", 2.2, 2.2]
            return
        self.enemies.remove(target)
        # XP + score feedback
        ups = self.player.gain_xp(target.xp)
        self.pending_levelups += ups
        self.add_float(target.pos, f"+{target.xp} XP", (140, 220, 255), 18)
        if ups:
            self.particles.fountain(self.player.pos, 26, (255, 230, 140))
        # absurd death message (30% chance, or always for demons)
        if random.random() < 0.3 or target.radius >= 28:
            msg = random.choice(DEATH_MESSAGES)
            self.add_float(target.pos + pygame.math.Vector2(0, -22),
                           msg, (255, 200, 120), 17)

    def hurt_player(self, dmg, big=False):
        if self.player.take_damage(dmg):
            self.add_shake(10 if big else 5)
            self.add_flash((255, 60, 60), 0.5 if big else 0.25)
            self.sounds.play("hurt")
            self.particles.burst(self.player.pos, 12, (255, 90, 90),
                                 speed=(60, 200), life=(0.2, 0.5), size=(1, 4))

    # ------------------------------------------------------------------ fx
    def add_shake(self, amount):
        self.shake = min(22, self.shake + amount)

    def add_flash(self, color, amount):
        self.flash_color = color
        self.flash_timer = max(self.flash_timer, amount)

    def add_float(self, pos, s, color=(230, 225, 245), size=20):
        self.float_texts.append(ui.FloatingText(pos, s, color, size))

    # ------------------------------------------------------------------ draw
    def draw(self):
        gs = self.game_surf
        self.world.draw(gs, self.t)
        mouse = pygame.mouse.get_pos()

        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_LEVELUP,
                          STATE_GAME_OVER, STATE_VICTORY):
            # ---- world entities
            for bn in self.boss_novas:
                bn.draw(gs)
            for n in self.novas:
                n.draw(gs)
            for e in self.enemies:
                e.draw(gs, self.t)
            if self.boss and not self.boss.dead:
                self.boss.draw(gs, self.t)
            if not self.player.dead:
                self.player.draw(gs, self.t, self.time_slow_timer > 0)
            for pr in self.enemy_projectiles:
                pr.draw(gs)
            for pr in self.player_projectiles:
                pr.draw(gs)
            self.particles.draw(gs)

            # time-slow tint
            if self.time_slow_timer > 0:
                tint = pygame.Surface((W, H), pygame.SRCALPHA)
                tint.fill((110, 70, 220, 26))
                gs.blit(tint, (0, 0))

            for f in self.float_texts:
                f.draw(gs)

            # flash overlay
            if self.flash_timer > 0:
                fl = pygame.Surface((W, H), pygame.SRCALPHA)
                a = int(min(160, 160 * self.flash_timer))
                fl.fill((*self.flash_color, a))
                gs.blit(fl, (0, 0))

            # custom crosshair
            if self.state == STATE_PLAYING:
                cx, cy = mouse
                pygame.draw.circle(gs, (200, 240, 255), (cx, cy), 9, 1)
                pygame.draw.circle(gs, (200, 240, 255), (cx, cy), 2)

            # ---- HUD
            ui.draw_hud(gs, self.player, self)
            if self.boss and not self.boss.dead:
                ui.draw_boss_bar(gs, self.boss)
            if self.banner:
                txt, sub, life, max_life = self.banner
                ui.draw_banner(gs, txt, sub, life / max_life)

            # ---- state overlays
            if self.state == STATE_PAUSED:
                ui.draw_pause(gs)
            elif self.state == STATE_LEVELUP:
                ui.draw_level_up(gs, [(n, d) for n, d, _ in self.upgrade_choices],
                                 self.t)
            elif self.state == STATE_GAME_OVER:
                ui.draw_game_over(gs, self.score, self.gameover_t)
            elif self.state == STATE_VICTORY:
                ui.draw_victory(gs, self.score, self.t)

            # ---- screen shake: blit buffer with random offset
            off = (random.uniform(-self.shake, self.shake),
                   random.uniform(-self.shake, self.shake)) if self.shake > 0.3 \
                else (0, 0)
            self.screen.fill((0, 0, 0))
            self.screen.blit(gs, off)

        elif self.state == STATE_TITLE:
            self.particles.draw(gs)
            ui.draw_title(gs, self.t, self.start_rect, self.quit_rect, mouse)
            self.screen.blit(gs, (0, 0))

        pygame.display.flip()