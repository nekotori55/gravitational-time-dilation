import math
import os
from math import sqrt

import pygame
import pygame.freetype
from pygame import Vector2
import scipy

os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]
import mpv


pygame.init()
pygame.display.set_caption("Physically innacurate gravitational time dilation")
screen = pygame.display.set_mode((1280, 720))
w = screen.get_width()
h = screen.get_height()
clock = pygame.time.Clock()
GAME_FONT = pygame.freetype.SysFont('Bahnschrift', 30)

playback_speed = 1
player = mpv.MPV(ytdl=True, loop=True)
player.play('ticking_sound.wav')

BACKGROUND_COLOR = "black"
BLACK_HOLE_COLOR = "gray"
OBJECT_COLOR = "blue"
CLOCK_COLOR = "white"
TEXT_COLOR = (255, 255, 255)
# TEXT_COLOR = (0, 0, 0)

G = scipy.constants.gravitational_constant
c = scipy.constants.speed_of_light

METERS_PER_PIXEL = 100

MASS_OF_SUN = 1.989e30
BLACK_HOLE_MASS = MASS_OF_SUN * 15  # kg
BLACK_HOLE_POS = Vector2(w / 2, h / 2) * METERS_PER_PIXEL

OBJECT_MASS = MASS_OF_SUN * 1e-5
OBJECT_RADIUS = 1500
OBJECT_START_POSITION = Vector2(-100, 100) * METERS_PER_PIXEL
# OBJECT_START_SPEED = Vector2(1, -0.53) * 1e6 * METERS_PER_PIXEL * 1.2
OBJECT_START_SPEED = Vector2(6, -10) * 1e5 * METERS_PER_PIXEL * 1.2
# OBJECT_START_SPEED = Vector2(1, -0.3) * 1e6 * METERS_PER_PIXEL * 1.2

INITIAL_TIME_SCALE = 1 / 1e7


def main():
    running = True
    delta_time = 0
    object_clock = 0

    time_scale = INITIAL_TIME_SCALE

    black_hole_pos = BLACK_HOLE_POS
    object_pos = OBJECT_START_POSITION
    object_velocity = OBJECT_START_SPEED
    camera_offset = Vector2(0.0)
    camera_zoom = 1
    trails = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    time_scale *= 2
                elif event.key == pygame.K_LEFT:
                    time_scale /= 2

        screen.fill(BACKGROUND_COLOR)

        force = calculate_attraction_force(m1=OBJECT_MASS, m2=BLACK_HOLE_MASS,
                                           r=black_hole_pos.distance_to(object_pos))
        object_acceleration = black_hole_pos - object_pos
        object_acceleration.scale_to_length(calculate_acceleration(force, OBJECT_MASS))

        distance = (black_hole_pos - object_pos).magnitude()
        bh_schwartzchild_radius = calculate_schwarzchild_radius(BLACK_HOLE_MASS)
        dilation_coefficient = calculate_gravitational_time_dilation(bh_schwartzchild_radius, distance)
        dilated_time = delta_time * dilation_coefficient

        object_velocity += object_acceleration * dilated_time

        object_pos += object_velocity * dilated_time
        object_clock += dilated_time / time_scale

        # RENDERING
        for i in range(len(trails) - 1):
            # print(len(trails))
            pygame.draw.line(screen, (255 - trails[i][1] * 255, trails[i][1] * 255, trails[i][1] * 255), width=2,
                             start_pos=trails[i][0] + camera_offset,
                             end_pos=trails[i + 1][0] + camera_offset)

        camera_offset = - object_pos / METERS_PER_PIXEL + Vector2(w / 2, h / 2)

        vis_black_hole_pos = (black_hole_pos / METERS_PER_PIXEL / camera_zoom + camera_offset)
        vis_black_hole_radius = calculate_schwarzchild_radius(mass=BLACK_HOLE_MASS) / METERS_PER_PIXEL * camera_zoom

        vis_object_pos = ((object_pos / METERS_PER_PIXEL) + camera_offset)
        vis_object_radius = OBJECT_RADIUS / METERS_PER_PIXEL * camera_zoom

        trails.append((vis_object_pos - camera_offset, dilation_coefficient))
        if len(trails) > 3000:
            trails.pop(0)

        vis_object_acceleration = object_acceleration / METERS_PER_PIXEL
        vis_object_velocity = object_velocity / METERS_PER_PIXEL

        # black hole
        pygame.draw.circle(screen, BLACK_HOLE_COLOR, vis_black_hole_pos, vis_black_hole_radius)

        # acceleration direction
        line_end_pos = vis_object_pos + Vector2(vis_object_radius, 0).rotate_rad(object_clock * math.pi / 1000 * 2)
        pygame.draw.line(screen, "green", width=2, start_pos=vis_object_pos,
                         end_pos=vis_object_pos + vis_object_acceleration.clamp_magnitude(80))
        # velocity direction
        pygame.draw.line(screen, "red", width=2, start_pos=vis_object_pos,
                         end_pos=vis_object_pos + vis_object_velocity.clamp_magnitude(60))

        # object
        pygame.draw.circle(screen, OBJECT_COLOR, vis_object_pos, vis_object_radius)
        # object internal clock
        pygame.draw.line(screen, CLOCK_COLOR, width=2, start_pos=vis_object_pos, end_pos=line_end_pos)

        # Hints
        GAME_FONT.render_to(screen, (5, 5 + 35 * 0), f"Time dilation coefficient: {dilation_coefficient:.3f}",
                            TEXT_COLOR)
        GAME_FONT.render_to(screen, (5, 5 + 35 * 1), f"Velocity: ~{object_velocity.magnitude():.2E} km/s", TEXT_COLOR)
        GAME_FONT.render_to(screen, (5, 5 + 35 * 2), f"Acceleration: ~{object_acceleration.magnitude():.2E} km/s^2",
                            TEXT_COLOR)
        GAME_FONT.render_to(screen, (5, 5 + 35 * 3), f"Black hole radius: ~{bh_schwartzchild_radius:.2E} km",
                            TEXT_COLOR)
        GAME_FONT.render_to(screen, (5, 5 + 35 * 4),
                            f"Distance to event horizon: ~{distance - bh_schwartzchild_radius:.2E} km", TEXT_COLOR)

        if delta_time != 0:
            speed = max(dilation_coefficient, 0.1)
            player.speed = speed

        pygame.display.flip()
        delta_time = clock.tick(60) * time_scale


def calculate_schwarzchild_radius(mass):
    return 2 * G * mass / (c ** 2)


def calculate_attraction_force(m1, m2, r):
    return G * m1 * m2 / (r ** 2)


def calculate_gravitational_time_dilation(schw_radius, radius):
    sus = 1 - (1 + 0.5 * 0) * schw_radius / radius
    if sus < 0:
        return 0
    else:
        return sqrt(sus)


def calculate_acceleration(force, mass):
    return force / mass


if __name__ == '__main__':
    main()
