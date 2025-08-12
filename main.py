import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# ---------------------------------------------
# Utilidades de vectores (2D)
# ---------------------------------------------

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


# ---------------------------------------------
# Geometría del hexágono
# ---------------------------------------------

def regular_polygon(center: Tuple[int, int], radius: float, sides: int, start_angle_deg: float = -90.0) -> List[Tuple[float, float]]:
    """Genera vértices CCW de un polígono regular."""
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
    t: Tuple[float, float]  # tangente unitaria (p1->p2)
    n: Tuple[float, float]  # normal hacia adentro (para vértices CCW)
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
        # Para CCW, normal hacia adentro = rotación -90°: (-ty, tx)
        inward = (-t[1], t[0])
        edges.append(Edge(p1, p2, t, inward, L))
    return edges


# ---------------------------------------------
# Pelota y simulación
# ---------------------------------------------

@dataclass
class Ball:
    pos: Tuple[float, float]
    vel: Tuple[float, float]
    radius: float
    color: Tuple[int, int, int] = (240, 80, 80)


class World:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Hexágono centrado
        self.center = (width // 2, height // 2)
        self.hex_radius = min(width, height) * 0.38
        self.verts = regular_polygon(self.center, self.hex_radius, 6)
        self.edges = build_edges(self.verts)

        # Pelota
        start_angle = random.uniform(0, 2 * math.pi)
        start_offset = (math.cos(start_angle) * self.hex_radius * 0.2,
                        math.sin(start_angle) * self.hex_radius * 0.2)
        self.ball = Ball(
            pos=add(self.center, start_offset),
            vel=(random.uniform(120, 180), random.uniform(120, 180)),
            radius=12.0,
        )

        # Física del rebote lento
        self.restitucion = 0.45  # coeficiente de rebote bajo (rebota "lento")
        self.friccion_tangencial = 0.015  # disipación a lo largo de la pared
        self.damping_global = 0.000  # ligera pérdida por segundo (0 = sin damping global)

    def step(self, dt: float):
        # Integración simple de posición
        self.ball.pos = add(self.ball.pos, mul(self.ball.vel, dt))

        # Pequeño damping global (opcional)
        if self.damping_global > 0:
            self.ball.vel = mul(self.ball.vel, max(0.0, 1.0 - self.damping_global * dt))

        # Resolver colisiones con cada arista del hexágono
        for edge in self.edges:
            self._resolve_edge_collision(edge, dt)

        # Asegurar que la pelota se mantiene dentro (reparación robusta)
        self._snap_inside()

        # Limitar velocidad mínima para evitar quedarse "pegada"
        speed = length(self.ball.vel)
        if speed < 30.0:
            # Reinyectar algo de velocidad hacia el centro
            dir_to_center = normalize(sub(self.center, self.ball.pos))
            self.ball.vel = add(self.ball.vel, mul(dir_to_center, 40.0))

    def _resolve_edge_collision(self, edge: Edge, dt: float):
        c = self.ball.pos
        r = self.ball.radius

        # Distancia firmada al infinito de la línea (inward normal)
        to_c = sub(c, edge.p1)
        s = dot(edge.n, to_c)  # positivo si dentro, negativo si fuera

        # Proyección a lo largo del borde para saber si choca con el segmento o los vértices
        u = clamp(dot(to_c, edge.t), 0.0, edge.length)
        q = add(edge.p1, mul(edge.t, u))  # punto más cercano del segmento
        cq = sub(c, q)
        dist = length(cq)

        # Caso A: choque con el lado (proyección interna) usando distancia a la línea
        hits_side = (0.0 < u < edge.length) and (s < r)

        # Caso B: choque con un vértice (proyección fuera del segmento)
        hits_vertex = (u == 0.0 or u == edge.length) and (dist < r)

        if not (hits_side or hits_vertex):
            return

        # Normal de colisión
        if hits_side:
            n = edge.n  # ya apunta hacia adentro
            penetration = r - s
        else:
            # Colisión con vértice: normal desde vértice más cercano hacia la pelota
            if u == 0.0:
                vtx = edge.p1
            else:
                vtx = edge.p2
            n = normalize(sub(c, vtx))
            if n == (0.0, 0.0):
                n = edge.n  # fallback
            penetration = r - length(sub(c, vtx))

        # Solo reflejar si nos movemos hacia la pared
        vn = dot(self.ball.vel, n)
        if vn < 0.0:
            vt = sub(self.ball.vel, mul(n, vn))  # componente tangencial
            # Rebote con restitución reducida (rebota más lento)
            new_vn = -vn * self.restitucion
            # Fricción tangencial (reduce deslizamiento a lo largo del borde)
            vt = mul(vt, max(0.0, 1.0 - self.friccion_tangencial))
            self.ball.vel = add(mul(n, new_vn), vt)

        # Corrección posicional mínima para sacar la pelota de la pared
        k_slop = 0.001
        correction = mul(n, max(0.0, penetration + k_slop))
        self.ball.pos = add(self.ball.pos, correction)

    def _snap_inside(self):
        # Garante que la pelota permanezca dentro del polígono (por si hay acumulación numérica)
        # Verifica cada arista y mueve la pelota hacia adentro si fuera necesario.
        for edge in self.edges:
            c = self.ball.pos
            s = dot(edge.n, sub(c, edge.p1))
            if s < 0.0:  # está fuera, empujar hacia adentro
                self.ball.pos = add(self.ball.pos, mul(edge.n, -s + 0.1))


# ---------------------------------------------
# Render con Pygame
# ---------------------------------------------

COLOR_BG = (15, 16, 20)
COLOR_HEX = (80, 160, 220)
COLOR_HEX_FILL = (25, 30, 40)


def draw_world(screen: pygame.Surface, world: World):
    # Relleno del hexágono
    pygame.draw.polygon(screen, COLOR_HEX_FILL, world.verts)
    # Borde
    pygame.draw.polygon(screen, COLOR_HEX, world.verts, width=3)

    # Pelota
    pygame.draw.circle(screen, world.ball.color, (int(world.ball.pos[0]), int(world.ball.pos[1])), int(world.ball.radius))


def run():
    pygame.init()
    pygame.display.set_caption("Pelota rebotando en hexágono (rebote lento)")

    W, H = 900, 900
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()
    world = World(W, H)

    running = True
    # Para ver el rebote más "lento", usar dt fijo (tipo cámara lenta)
    fixed_dt = None  # por ejemplo, 1/120.0 para timestep fijo; dejar None para adaptativo

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Tiempo
        if fixed_dt is not None:
            dt = fixed_dt
            clock.tick(int(1.0 / dt))
        else:
            dt_ms = clock.tick(120)  # limitar a ~120 FPS
            dt = dt_ms / 1000.0

        world.step(dt)

        screen.fill(COLOR_BG)
        draw_world(screen, world)
        # Texto con instrucciones
        _draw_hint(screen)

        pygame.display.flip()

    pygame.quit()
    return 0


def _draw_hint(screen: pygame.Surface):
    font = pygame.font.SysFont("consolas,arial", 16)
    hint = "ESC para salir — Rebote lento (rest=0.45, fricción=0.015)"
    surf = font.render(hint, True, (180, 200, 220))
    screen.blit(surf, (12, 12))


if __name__ == "__main__":
    sys.exit(run())
