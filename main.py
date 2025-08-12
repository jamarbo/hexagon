import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# -----------------------------
# Utilidades de vectores (2D)
# -----------------------------

def dot(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def sub(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return (a[0] - b[0], a[1] - b[1])


def add(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
    return (a[0] + b[0], a[1] + b[1])


def mul(a: Tuple[float, float], s: float) -> Tuple[float, float]:
    return (a[0] * s, a[1] * s)


def length(v: Tuple[float, float]) -> float:
    return math.hypot(v[0], v[1])


def normalize(v: Tuple[float, float]) -> Tuple[float, float]:
    l = length(v)
    if l <= 1e-8:
        return (0.0, 0.0)
    return (v[0] / l, v[1] / l)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# -----------------------------
# Geometría del hexágono
# -----------------------------

def regular_polygon(center: Tuple[int, int], radius: float, sides: int, start_angle_deg: float = -90.0) -> List[Tuple[float, float]]:
    cx, cy = center
    verts = []
    for i in range(sides):
        ang = math.radians(start_angle_deg + 360.0 * i / sides)
        x = cx + radius * math.cos(ang)
        y = cy + radius * math.sin(ang)
        verts.append((x, y))
    return verts


@dataclass
class Edge:
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    t: Tuple[float, float]
    n: Tuple[float, float]
    length: float


def build_edges(verts_ccw: List[Tuple[float, float]]) -> List[Edge]:
    edges: List[Edge] = []
    n = len(verts_ccw)
    for i in range(n):
        p1 = verts_ccw[i]
        p2 = verts_ccw[(i + 1) % n]
        e = sub(p2, p1)
        L = length(e)
        if L < 1e-8:
            continue
        t = (e[0] / L, e[1] / L)
        inward = (-t[1], t[0])  # normal hacia adentro para CCW
        edges.append(Edge(p1, p2, t, inward, L))
    return edges


# -----------------------------
# Pelota y simulación
# -----------------------------

@dataclass
class Ball:
    pos: Tuple[float, float]
    vel: Tuple[float, float]
    radius: float
    color: Tuple[int, int, int]


class World:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Hexágono centrado
        self.center = (width // 2, height // 2)
        self.hex_radius = min(width, height) * 0.38
        self.verts = regular_polygon(self.center, self.hex_radius, 6)
        self.edges = build_edges(self.verts)

        # Física global
        self.gravity = (0.0, 900.0)
        self.restitucion_pared = 0.5
        self.restitucion_bolas = 0.9
        self.friccion_tangencial = 0.02
        self.damping_global = 0.0

        # Shake del contenedor (accionado por usuario, no automático)
        self.shake_offset = (0.0, 0.0)
        self.shake_vel = (0.0, 0.0)
        self.shake_acc = (0.0, 0.0)
        self.shake_active = False
        # Dinámica tipo resorte-amortiguador hacia el centro (offset=0)
        self.shake_k = 40.0  # rigidez
        self.shake_d = 8.0   # amortiguamiento
        self.shake_impulse = 500.0  # velocidad inicial por burst (px/s)

        # Pelotas
        self.balls: List[Ball] = []
        self._spawn_balls(10)

    def step(self, dt: float):
        # Actualizar shake y geometría
        self._update_shake(dt)

        # Aceleración efectiva (inercial): g - a_contenedor
        effective_g = add(self.gravity, mul(self.shake_acc, -1.0))

        # Integración simple
        for b in self.balls:
            b.vel = add(b.vel, mul(effective_g, dt))
            if self.damping_global > 0:
                b.vel = mul(b.vel, max(0.0, 1.0 - self.damping_global * dt))
            b.pos = add(b.pos, mul(b.vel, dt))

        # Colisión pared-bola (pared moviéndose con velocidad de shake)
        wall_v = self.shake_vel
        for b in self.balls:
            for e in self.edges:
                self._resolve_edge_collision(b, e, wall_v)
            self._snap_inside(b)

        # Colisiones entre bolas
        n = len(self.balls)
        for i in range(n):
            for j in range(i + 1, n):
                self._resolve_ball_collision(self.balls[i], self.balls[j])

        # Evitar dormir totalmente
        for b in self.balls:
            if length(b.vel) < 12.0:
                b.vel = add(b.vel, mul(normalize(sub(self.center, b.pos)), 16.0))

    def _resolve_edge_collision(self, ball: Ball, edge: Edge, wall_vel: Tuple[float, float]):
        c = ball.pos
        r = ball.radius

        to_c = sub(c, edge.p1)
        s = dot(edge.n, to_c)

        u = clamp(dot(to_c, edge.t), 0.0, edge.length)
        q = add(edge.p1, mul(edge.t, u))
        cq = sub(c, q)
        dist = length(cq)

        hits_side = (0.0 < u < edge.length) and (s < r)
        hits_vertex = (u == 0.0 or u == edge.length) and (dist < r)
        if not (hits_side or hits_vertex):
            return

        if hits_side:
            n = edge.n
            penetration = r - s
        else:
            vtx = edge.p1 if u == 0.0 else edge.p2
            n = normalize(sub(c, vtx))
            if n == (0.0, 0.0):
                n = edge.n
            penetration = r - length(sub(c, vtx))

        v_wall_n = dot(wall_vel, n)
        vn = dot(ball.vel, n)
        vn_rel = vn - v_wall_n
        if vn_rel < 0.0:
            vt = sub(ball.vel, mul(n, vn))
            new_vn_rel = -self.restitucion_pared * vn_rel
            new_vn = new_vn_rel + v_wall_n
            vt = mul(vt, max(0.0, 1.0 - self.friccion_tangencial))
            ball.vel = add(mul(n, new_vn), vt)

        k_slop = 0.001
        ball.pos = add(ball.pos, mul(n, max(0.0, penetration + k_slop)))

    def _snap_inside(self, ball: Ball):
        for e in self.edges:
            s = dot(e.n, sub(ball.pos, e.p1))
            if s < 0.0:
                ball.pos = add(ball.pos, mul(e.n, -s + 0.1))

    def _resolve_ball_collision(self, a: Ball, b: Ball):
        n = sub(b.pos, a.pos)
        dist = length(n)
        rsum = a.radius + b.radius
        if dist <= 1e-8:
            ang = random.uniform(0, 2*math.pi)
            n = (math.cos(ang), math.sin(ang))
            dist = 1.0
        else:
            n = (n[0]/dist, n[1]/dist)

        overlap = rsum - dist
        if overlap <= 0:
            return

        ma = max(1.0, a.radius * a.radius)
        mb = max(1.0, b.radius * b.radius)
        inv_ma = 1.0/ma
        inv_mb = 1.0/mb
        total_inv = inv_ma + inv_mb
        corr = mul(n, overlap / total_inv)
        a.pos = sub(a.pos, mul(corr, inv_ma))
        b.pos = add(b.pos, mul(corr, inv_mb))

        rv = sub(b.vel, a.vel)
        vel_n = dot(rv, n)
        if vel_n > 0:
            return
        e = self.restitucion_bolas
        j = -(1 + e) * vel_n / (inv_ma + inv_mb)
        imp = mul(n, j)
        a.vel = sub(a.vel, mul(imp, inv_ma))
        b.vel = add(b.vel, mul(imp, inv_mb))

    def _spawn_balls(self, n: int):
        colors = [
            (240, 80, 80), (80, 200, 120), (80, 160, 240), (230, 180, 70),
            (200, 100, 220), (60, 220, 200), (240, 120, 160), (150, 150, 255), (255, 140, 90)
        ]
        attempts = 0
        while len(self.balls) < n and attempts < 5000:
            attempts += 1
            rad = random.uniform(9.0, 16.0)
            ang = random.uniform(0, 2*math.pi)
            rr = random.uniform(0.0, self.hex_radius - rad)
            p = add(self.center, (rr*math.cos(ang), rr*math.sin(ang)))
            ok = True
            for e in self.edges:
                if dot(e.n, sub(p, e.p1)) < rad + 2.0:
                    ok = False
                    break
            if not ok:
                continue
            for b in self.balls:
                if length(sub(p, b.pos)) < rad + b.radius + 2.0:
                    ok = False
                    break
            if not ok:
                continue
            v = (random.uniform(-120, 120), random.uniform(-60, 0))
            color = random.choice(colors)
            self.balls.append(Ball(p, v, rad, color))

    def _update_shake(self, dt: float):
        # Dinámica: offset'' = -k*offset - d*offset'
        # Integración explícita simple
        if not self.shake_active and length(self.shake_vel) < 1e-4 and length(self.shake_offset) < 1e-4:
            # En reposo en el centro
            self.shake_offset = (0.0, 0.0)
            self.shake_vel = (0.0, 0.0)
            self.shake_acc = (0.0, 0.0)
            self.verts = regular_polygon(self.center, self.hex_radius, 6)
            self.edges = build_edges(self.verts)
            return

        # a = -k*x - d*v
        ax = -self.shake_k * self.shake_offset[0] - self.shake_d * self.shake_vel[0]
        ay = -self.shake_k * self.shake_offset[1] - self.shake_d * self.shake_vel[1]
        self.shake_acc = (ax, ay)
        self.shake_vel = (self.shake_vel[0] + ax * dt, self.shake_vel[1] + ay * dt)
        self.shake_offset = (self.shake_offset[0] + self.shake_vel[0] * dt,
                              self.shake_offset[1] + self.shake_vel[1] * dt)

        # Umbral para parar
        if length(self.shake_vel) < 1e-2 and length(self.shake_offset) < 1e-2:
            self.shake_active = False
            self.shake_offset = (0.0, 0.0)
            self.shake_vel = (0.0, 0.0)
            self.shake_acc = (0.0, 0.0)

        moved_center = add(self.center, self.shake_offset)
        self.verts = regular_polygon(moved_center, self.hex_radius, 6)
        self.edges = build_edges(self.verts)

    def shake_burst(self, magnitude: float = 1.0):
        # Aplica un impulso de velocidad al contenedor en dirección aleatoria
        ang = random.uniform(0, 2*math.pi)
        v = self.shake_impulse * max(0.0, magnitude)
        self.shake_vel = add(self.shake_vel, (v * math.cos(ang), v * math.sin(ang)))
        self.shake_active = True


# -----------------------------
# Render con Pygame
# -----------------------------

COLOR_BG = (15, 16, 20)
COLOR_HEX = (80, 160, 220)
COLOR_HEX_FILL = (25, 30, 40)


def draw_world(screen: pygame.Surface, world: World):
    pygame.draw.polygon(screen, COLOR_HEX_FILL, world.verts)
    pygame.draw.polygon(screen, COLOR_HEX, world.verts, width=3)
    for b in world.balls:
        pygame.draw.circle(screen, b.color, (int(b.pos[0]), int(b.pos[1])), int(b.radius))


def run():
    pygame.init()
    pygame.display.set_caption("Pelotas con gravedad + shake en hexágono")
    W, H = 900, 900
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    world = World(W, H)

    running = True
    fixed_dt = None
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    world.shake_burst(1.0)

        if fixed_dt is not None:
            dt = fixed_dt
            clock.tick(int(1.0/dt))
        else:
            dt_ms = clock.tick(120)
            dt = dt_ms/1000.0

        world.step(dt)

        screen.fill(COLOR_BG)
        draw_world(screen, world)
        _draw_hint(screen)
        pygame.display.flip()

    pygame.quit()
    return 0


def _draw_hint(screen: pygame.Surface):
    font = pygame.font.SysFont("consolas,arial", 16)
    hint = "SPACE: shake | ESC: salir"
    surf = font.render(hint, True, (180, 200, 220))
    screen.blit(surf, (12, 12))


if __name__ == "__main__":
    sys.exit(run())
