"""Vale Verde: pequeno jogo de plataforma feito com Pygame."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame


WIDTH, HEIGHT = 960, 540
FPS = 60
GROUND_Y = 450
WORLD_END = 3850
GOAL_X = 3775
GRAVITY = 1750
SPEED = 310
JUMP_SPEED = -680
SKY = (159, 224, 248)
INK = (28, 62, 68)
CREAM = (255, 250, 227)

BASE = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
ASSETS = BASE / "assets"
SOUNDS = BASE / "sounds"


def image(path: str, size: tuple[int, int] | None = None) -> pygame.Surface:
    surface = pygame.image.load(str(ASSETS / path)).convert_alpha()
    return pygame.transform.smoothscale(surface, size) if size else surface


def animation(folder: str, action: str, height: int) -> list[pygame.Surface]:
    paths = sorted(
        (ASSETS / folder / action.lower()).glob("*.png"),
        key=lambda path: int(path.stem),
    )
    frames = []
    for path in paths:
        original = pygame.image.load(str(path)).convert_alpha()
        bounds = original.get_bounding_rect(min_alpha=8)
        cropped = original.subsurface(bounds)
        width = round(cropped.get_width() * height / cropped.get_height())
        frames.append(pygame.transform.smoothscale(cropped, (width, height)))
    if not frames:
        raise FileNotFoundError(f"Animação não encontrada: {folder}/{action}")
    return frames


class Audio:
    """Toca a ambientação em loop e os efeitos em seus eventos de jogo."""

    def __init__(self) -> None:
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as exc:
                print(f"Áudio indisponível: {exc}", file=sys.stderr)
                self.enabled = False
                return
        self.enabled = True
        pygame.mixer.set_num_channels(12)
        self.effects = {
            name: pygame.mixer.Sound(str(SOUNDS / f"{name}.mp3"))
            for name in ("die", "enemies", "hero-mata-enemies", "jump", "item")
        }
        for name, volume in (("die", 0.75), ("enemies", 0.42),
                             ("hero-mata-enemies", 0.7), ("jump", 0.6), ("item", 0.65)):
            self.effects[name].set_volume(volume)
        pygame.mixer.music.load(str(SOUNDS / "fundo-ambientacao.mp3"))
        pygame.mixer.music.set_volume(0.28)
        pygame.mixer.music.play(-1)

    def play(self, name: str) -> None:
        if self.enabled:
            self.effects[name].play()

    def pause(self) -> None:
        if self.enabled:
            pygame.mixer.music.pause()
            pygame.mixer.pause()

    def resume(self) -> None:
        if self.enabled:
            pygame.mixer.music.unpause()
            pygame.mixer.unpause()


@dataclass(frozen=True)
class Platform:
    x: int
    y: int
    width: int
    floating: bool = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, 24 if self.floating else HEIGHT - self.y)


PLATFORMS = [
    Platform(0, GROUND_Y, 700),
    Platform(820, GROUND_Y, 500),
    Platform(1530, GROUND_Y, 650),
    Platform(2320, GROUND_Y, 530),
    Platform(3010, GROUND_Y, 840),
    # Introdução: dois degraus levam à estrela alta.
    Platform(260, 355, 165, True),
    Platform(495, 290, 110, True),
    # Patrulha: há uma rota por cima, mas a estrela está no chão.
    Platform(900, 365, 240, True),
    # Travessia: a plataforma fica sobre o maior abismo.
    Platform(1365, 370, 130, True),
    Platform(1970, 365, 180, True),
    # Escalada: três alturas sucessivas.
    Platform(2360, 365, 205, True),
    Platform(2580, 290, 200, True),
    Platform(2720, 220, 150, True),
    # Reta final: cobertura para evitar os inimigos.
    Platform(3140, 350, 240, True),
]
GROUND = [p for p in PLATFORMS if not p.floating]
STAR_POSITIONS = [(550, 240), (1275, 400), (1430, 320), (2770, 170), (3630, 338)]
ENEMY_SPAWNS = [
    (1020, 880, 1130, "male", "walker"),
    (1210, 1180, 1270, "female", "sentry"),
    (1810, 1620, 2080, "female", "hopper"),
    (2530, 2380, 2750, "male", "walker"),
    (3290, 3100, 3410, "female", "hopper"),
    (3580, 3450, 3680, "male", "walker"),
]

# Cada objeto tem posição, tamanho e camada próprios. Os nomes referem-se aos PNGs
# do tileset; a camada "back" fica atrás das plataformas e "front" à frente delas.
SCENERY = [
    (110, "Tree_2", 178, 190, "back"), (415, "Tree_3", 155, 165, "back"),
    (1040, "Tree_2", 183, 190, "back"),
    (2010, "Tree_3", 190, 185, "back"),
    (2350, "Tree_3", 135, 145, "back"), (2650, "Tree_3", 140, 150, "back"),
    (2490, "Tree_2", 195, 205, "back"),
    (3120, "Tree_2", 150, 165, "back"), (3520, "Tree_3", 183, 190, "back"),
    (225, "Mushroom_1", 35, 30, "front"), (265, "Mushroom_2", 31, 27, "front"),
    (600, "Bush (3)", 81, 51, "front"), (395, "Tree_1", 92, 35, "front"),
    (840, "Tree_1", 90, 34, "front"), (1110, "Bush (2)", 106, 55, "front"),
    (1170, "Mushroom_2", 37, 31, "front"), (1250, "Mushroom_1", 28, 25, "front"),
    (1590, "Stone", 98, 57, "front"), (1690, "Stone", 67, 41, "front"),
    (1745, "Tree_1", 98, 38, "front"), (2070, "Stone", 89, 50, "front"),
    (2420, "Mushroom_1", 31, 27, "front"),
    (2460, "Mushroom_2", 39, 34, "front"), (2700, "Bush (1)", 122, 59, "front"),
    (2780, "Stone", 69, 40, "front"), (3150, "Bush (3)", 92, 51, "front"),
    (3310, "Tree_1", 100, 38, "front"), (3560, "Mushroom_2", 37, 31, "front"),
    (3610, "Bush (2)", 106, 53, "front"),
]


class Player:
    def __init__(self, art: dict[str, list[pygame.Surface]]):
        self.art = art
        self.rect = pygame.Rect(80, GROUND_Y - 72, 44, 72)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.vy = 0.0
        self.grounded = True
        self.facing = 1
        self.anim_time = 0.0
        self.invincible = 0.0

    def update(self, dt: float, movement: int, jump: bool) -> None:
        if movement:
            self.facing = movement
        self.x = max(0, min(WORLD_END - self.rect.width, self.x + movement * SPEED * dt))
        self.rect.x = round(self.x)
        if jump and self.grounded:
            self.vy = JUMP_SPEED
            self.grounded = False
        old_bottom = self.rect.bottom
        self.vy = min(self.vy + GRAVITY * dt, 900)
        self.y += self.vy * dt
        self.rect.y = round(self.y)
        self.grounded = False
        if self.vy >= 0:
            for platform in PLATFORMS:
                top = platform.y
                if old_bottom <= top + 5 and self.rect.bottom >= top and self.rect.right > platform.x + 8 and self.rect.left < platform.x + platform.width - 8:
                    self.rect.bottom = top
                    self.y = float(self.rect.y)
                    self.vy = 0
                    self.grounded = True
                    break
        self.invincible = max(0, self.invincible - dt)
        self.anim_time += dt

    def draw(self, screen: pygame.Surface, camera: int, moving: bool) -> None:
        if self.invincible and int(self.invincible * 12) % 2:
            return
        action = "Jump" if not self.grounded else "Run" if moving else "Idle"
        frames = self.art[action]
        frame = frames[int(self.anim_time * (11 if action == "Run" else 8)) % len(frames)]
        if self.facing < 0:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, (self.rect.centerx - camera - frame.get_width() // 2, self.rect.bottom - frame.get_height() + 3))


class Enemy:
    def __init__(self, x: int, left: int, right: int, kind: str, behavior: str,
                 art: dict[str, dict[str, list[pygame.Surface]]]):
        self.x = float(x)
        self.rect = pygame.Rect(x, GROUND_Y - 64, 42, 64)
        self.left, self.right = left, right
        self.behavior = behavior
        self.frames = art[kind]["Attack" if behavior == "sentry" else "Walk"]
        self.direction = -1
        self.time = 0.0
        self.alive = True

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        if self.behavior != "sentry":
            speed = 60 if self.behavior == "hopper" else 75
            self.x += self.direction * speed * dt
            if self.x <= self.left or self.x >= self.right:
                self.x = max(self.left, min(self.right, self.x))
                self.direction *= -1
        self.rect.x = round(self.x)
        self.time += dt
        hop = int(66 * math.sin(self.time * 3.3) ** 2) if self.behavior == "hopper" else 0
        self.rect.bottom = GROUND_Y - hop

    def draw(self, screen: pygame.Surface, camera: int) -> None:
        if not self.alive:
            return
        frame = self.frames[int(self.time * 9) % len(self.frames)]
        if self.direction < 0:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, (self.rect.centerx - camera - frame.get_width() // 2, self.rect.bottom - frame.get_height()))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Vale Verde — A Travessia")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.audio = Audio()
        self.font = pygame.font.SysFont("arial", 23, bold=True)
        self.small = pygame.font.SysFont("arial", 18, bold=True)
        self.title_font = pygame.font.SysFont("arial", 62, bold=True)
        self.background = image("tileset/background/BG.png", (1000, 750))
        self.tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.tiles = {n: image(f"tileset/terrain/{n}.png", (64, 64)) for n in
                      (1, 2, 3, 5, 7, 8, 9, 10, 13, 14, 15)}
        self.water = image("tileset/terrain/17.png", (64, 50))
        self.objects = {name: image(f"tileset/props/{name}.png") for name in
                        ("Bush (1)", "Bush (2)", "Bush (3)", "Bush (4)", "Mushroom_1",
                         "Mushroom_2", "Tree_1", "Tree_2", "Tree_3", "Stone", "Sign_1", "Sign_2")}
        self.scenery = [(x, pygame.transform.smoothscale(self.objects[name], (width, height)), layer)
                        for x, name, width, height, layer in SCENERY]
        self.hero_art = {action: animation("characters/hero", action, 82) for action in ("Idle", "Run", "Jump")}
        self.enemy_art = {kind: {action: animation(f"characters/enemies/{kind}", action, 68)
                                 for action in ("Walk", "Attack")}
                          for kind in ("male", "female")}
        self.state = "menu"
        self.camera = 0
        self.reset()

    def reset(self) -> None:
        self.player = Player(self.hero_art)
        self.enemies = [Enemy(*spawn, self.enemy_art) for spawn in ENEMY_SPAWNS]
        self.stars = set(range(len(STAR_POSITIONS)))
        self.lives = 3
        self.score = 0
        self.camera = 0
        self.visible_enemies: set[int] = set()

    def label(self, text: str, x: int, y: int, font: pygame.font.Font | None = None,
              color: tuple[int, int, int] = CREAM, center: bool = False) -> None:
        rendered = (font or self.font).render(text, True, color)
        self.screen.blit(rendered, (x - rendered.get_width() // 2 if center else x, y))

    def panel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (21, 54, 61), rect, border_radius=22)
        pygame.draw.rect(self.screen, (182, 229, 170), rect, 3, border_radius=22)

    def draw_background(self) -> None:
        self.screen.fill(SKY)
        offset = int(self.camera * 0.18) % 1000
        for x in (-offset, 1000 - offset):
            self.screen.blit(self.background, (x, -125))
        tones = [(255, 255, 255, 0), (250, 223, 150, 49), (145, 200, 255, 57),
                 (211, 176, 244, 54), (255, 178, 133, 57)]
        position = min(4.0, self.camera / 700)
        left = min(3, int(position))
        blend = position - left
        tint_color = tuple(round(tones[left][i] * (1 - blend) + tones[left + 1][i] * blend)
                           for i in range(4))
        self.tint.fill(tint_color)
        self.screen.blit(self.tint, (0, 0))

    def draw_scenery(self, layer: str) -> None:
        for x, art, item_layer in self.scenery:
            sx = x - self.camera
            if item_layer == layer and -art.get_width() < sx < WIDTH:
                self.screen.blit(art, (sx, GROUND_Y - art.get_height() + (8 if layer == "back" else 3)))

    def draw_water(self) -> None:
        for before, after in zip(GROUND, GROUND[1:]):
            start = before.x + before.width
            end = after.x
            if end < self.camera or start > self.camera + WIDTH:
                continue
            pygame.draw.rect(self.screen, (46, 149, 220),
                             (start - self.camera, 492, end - start, HEIGHT - 492))
            for x in range(start, end, 64):
                self.screen.blit(self.water, (x - self.camera, 480),
                                 pygame.Rect(0, 0, min(64, end - x), 50))

    def draw_world(self) -> None:
        self.draw_background()
        self.draw_scenery("back")
        self.draw_water()
        for platform in PLATFORMS:
            if platform.x + platform.width < self.camera or platform.x > self.camera + WIDTH:
                continue
            count = math.ceil(platform.width / 64)
            for i in range(count):
                sx = platform.x + i * 64 - self.camera
                if sx > WIDTH or sx < -64:
                    continue
                visible_tile = pygame.Rect(0, 0, min(64, platform.width - i * 64), 64)
                if platform.floating:
                    tile = 13 if i == 0 else 15 if i == count - 1 else 14
                    self.screen.blit(self.tiles[tile], (sx, platform.y), visible_tile)
                else:
                    top = 1 if i == 0 else 3 if i == count - 1 else 7 if (i + platform.x // 64) % 5 == 0 else 2
                    self.screen.blit(self.tiles[top], (sx, platform.y), visible_tile)
                    for row in range(platform.y + 64, HEIGHT, 64):
                        dirt = (5, 8, 9, 10)[(i * 3 + row // 64 + platform.x // 100) % 4]
                        self.screen.blit(self.tiles[dirt], (sx, row), visible_tile)
        self.draw_scenery("front")
        self.screen.blit(self.objects["Sign_1"], (110 - self.camera, GROUND_Y - 65))
        self.screen.blit(self.objects["Sign_2"], (GOAL_X - 18 - self.camera, GROUND_Y - 65))
        # Bandeira: o portal de chegada fica após o último inimigo.
        gx = GOAL_X - self.camera
        pygame.draw.line(self.screen, (81, 63, 50), (gx, GROUND_Y - 125), (gx, GROUND_Y), 6)
        pygame.draw.polygon(self.screen, (255, 195, 65), [(gx + 3, GROUND_Y - 122),
                                                           (gx + 66, GROUND_Y - 107),
                                                           (gx + 3, GROUND_Y - 91)])
        for index in self.stars:
            x, y = STAR_POSITIONS[index]
            sx = x - self.camera
            if -30 < sx < WIDTH + 30:
                points = []
                for j in range(10):
                    angle = -math.pi / 2 + j * math.pi / 5
                    radius = 17 if j % 2 == 0 else 8
                    points.append((sx + math.cos(angle) * radius, y + math.sin(angle) * radius))
                pygame.draw.polygon(self.screen, (255, 211, 54), points)
                pygame.draw.polygon(self.screen, (255, 245, 160), points, 2)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera, pygame.key.get_pressed()[pygame.K_a] or
                         pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_LEFT] or
                         pygame.key.get_pressed()[pygame.K_RIGHT])

    def draw_hud(self) -> None:
        self.panel(pygame.Rect(16, 14, 270, 46))
        self.label(f"Vidas: {self.lives}     Estrelas: {self.score}/5", 30, 24, self.small)
        pygame.draw.rect(self.screen, (26, 65, 65), (660, 25, 280, 16), border_radius=8)
        progress = max(0, min(1, self.player.rect.x / GOAL_X))
        pygame.draw.rect(self.screen, (255, 204, 66), (660, 25, max(8, int(280 * progress)), 16), border_radius=8)
        self.label("P: pausar", 824, 49, self.small, INK)

    def damage(self) -> None:
        if self.player.invincible > 0 or self.state != "playing":
            return
        self.audio.play("die")
        self.lives -= 1
        if self.lives <= 0:
            self.state = "lost"
        else:
            self.player = Player(self.hero_art)
            self.player.invincible = 1.5
            self.camera = 0

    def update(self, dt: float, jump: bool) -> None:
        keys = pygame.key.get_pressed()
        movement = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        previous_bottom = self.player.rect.bottom
        jumped = jump and self.player.grounded
        self.player.update(dt, movement, jump)
        if jumped:
            self.audio.play("jump")
        for enemy in self.enemies:
            enemy.update(dt)
            if enemy.alive and self.player.rect.colliderect(enemy.rect):
                if self.player.vy > 0 and previous_bottom <= enemy.rect.top + 16:
                    enemy.alive = False
                    self.player.vy = -400
                    self.player.grounded = False
                    self.audio.play("hero-mata-enemies")
                else:
                    self.damage()
                    break
        for index in list(self.stars):
            x, y = STAR_POSITIONS[index]
            if self.player.rect.colliderect(pygame.Rect(x - 18, y - 18, 36, 36)):
                self.stars.remove(index)
                self.score += 1
                self.audio.play("item")
        if self.player.rect.top > 500:
            self.damage()
        if self.player.rect.centerx >= GOAL_X and self.player.grounded:
            self.state = "won"
        target = max(0, min(WORLD_END - WIDTH, self.player.rect.centerx - WIDTH * 0.37))
        self.camera = round(target)
        if self.state == "playing":
            visible_now = {index for index, enemy in enumerate(self.enemies)
                           if enemy.alive and enemy.rect.right > self.camera
                           and enemy.rect.left < self.camera + WIDTH}
            for _ in visible_now - self.visible_enemies:
                self.audio.play("enemies")
            self.visible_enemies = visible_now

    def draw_overlay(self) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((11, 43, 48, 125))
        self.screen.blit(shade, (0, 0))
        self.panel(pygame.Rect(180, 94, 600, 350))
        if self.state == "menu":
            self.label("VALE VERDE", WIDTH // 2, 122, self.title_font, (255, 211, 91), True)
            self.label("A TRAVESSIA", WIDTH // 2, 195, self.font, CREAM, True)
            self.label("Atravesse os abismos e alcance a bandeira!", WIDTH // 2, 235, self.small, CREAM, True)
            self.label("A/D ou setas: mover    |    Espaço / W / ↑: saltar", WIDTH // 2, 285, self.small, CREAM, True)
            self.label("P: pausar    |    Esc: menu    |    Pise nos inimigos", WIDTH // 2, 316, self.small, CREAM, True)
            self.label("ENTER PARA JOGAR", WIDTH // 2, 375, self.font, (255, 211, 91), True)
        elif self.state == "paused":
            self.label("PAUSADO", WIDTH // 2, 178, self.title_font, (255, 211, 91), True)
            self.label("P ou Enter: continuar    |    Esc: menu", WIDTH // 2, 302, self.font, CREAM, True)
        else:
            won = self.state == "won"
            self.label("VITÓRIA!" if won else "FIM DE JOGO", WIDTH // 2, 155,
                       self.title_font, (255, 211, 91), True)
            self.label(f"Você coletou {self.score} de 5 estrelas." if won else "Suas vidas acabaram.",
                       WIDTH // 2, 265, self.font, CREAM, True)
            self.label("Enter: jogar novamente    |    Esc: menu", WIDTH // 2, 335, self.small, CREAM, True)

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.033)
            jump = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "menu":
                            running = False
                        else:
                            self.audio.resume()
                            self.state = "menu"
                            self.reset()
                    elif event.key == pygame.K_RETURN:
                        if self.state in ("menu", "won", "lost"):
                            self.reset()
                            self.state = "playing"
                        elif self.state == "paused":
                            self.audio.resume()
                            self.state = "playing"
                    elif event.key == pygame.K_p:
                        if self.state == "playing":
                            self.state = "paused"
                            self.audio.pause()
                        elif self.state == "paused":
                            self.state = "playing"
                            self.audio.resume()
                    elif event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        jump = True
            if self.state == "playing":
                self.update(dt, jump)
            self.draw_world()
            if self.state == "playing":
                self.draw_hud()
            else:
                self.draw_overlay()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    try:
        Game().run()
    except (FileNotFoundError, pygame.error) as exc:
        print(f"Erro ao carregar o jogo: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
