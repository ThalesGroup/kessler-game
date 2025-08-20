# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations

import random

from math import pi, cos, sin, sqrt, degrees, radians, atan2
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .ship import Ship
    from .bullet import Bullet
from .mines import Mine
from .state_models import AsteroidDataList


class Asteroid:
    """ Sprite that represents an asteroid. """
    __slots__ = ('size', 'num_children', 'radius', 'mass', 'x', 'y', 'vx', 'vy', 'angle', 'speed', 'turnrate', '_state')

    def __init__(self,
                 position: tuple[float, float],
                 speed: float | None = None,
                 angle: float | None = None,
                 size: int | None = None) -> None:
        """
        Constructor for Asteroid Sprite

        :param position:  Optional Starting position (x, y) position
        :param speed: Optional Starting Speed
        :param angle: Optional Starting heading angle (degrees)
        :param size: Optional Starting size (1 to 4 inclusive)
        """

        # Set size to 4 if none is specified. Notify if out of size range
        if size is not None:
            if 1 <= size <= 4:
                self.size = size
            else:
                raise ValueError("Asteroid size can only be between 1 and 4")
        else:
            self.size = 4

        # Set max speed based off of scaling factor
        speed_scaler: float = 2.0 + (4.0 - self.size) / 4.0
        max_speed: float = 60.0 * speed_scaler

        # Number of child asteroids spawned when this asteroid is destroyed
        self.num_children: int = 3

        # Set position as specified
        self.x, self.y = position

        # Set collision radius based on size
        self.radius: float = self.size * 8.0

        self.mass: float = 0.25 * pi * self.radius * self.radius

        # Use optional angle and speed arguments otherwise generate random angle and speed
        starting_angle_rad: float = radians(angle) if angle is not None else random.random() * 2.0 * pi
        starting_speed: float = speed if speed is not None else max_speed * random.random()

        # Set velocity based on starting angle and speed
        self.vx = starting_speed * cos(starting_angle_rad)
        self.vy = starting_speed * sin(starting_angle_rad)

        self.speed = abs(starting_speed)  # This is used for early rejection in collision detection

        # Random rotations for use in display or future use with complex hit box
        self.angle: float = random.uniform(0.0, 360.0)
        self.turnrate: float = random.uniform(-100, 100)

        # [x: float, y: float, vx: float, vy: float, size: int, mass: float, radius: float]
        self._state: AsteroidDataList = [
            self.x, self.y,
            self.vx, self.vy,
            self.size,
            self.mass,
            self.radius
        ]

    @property
    def state(self) -> AsteroidDataList:
        return self._state

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    def update(self, delta_time: float, map_size: tuple[int, int]) -> None:
        """ Move the asteroid based on velocity"""
        # Avoid attribute lookup using local var
        x = (self.x + self.vx * delta_time) % map_size[0]
        y = (self.y + self.vy * delta_time) % map_size[1]
        self.x = x
        self.y = y
        # Update mutable state (cache the lookup first)
        state = self._state
        state[0] = x
        state[1] = y
        self.angle += delta_time * self.turnrate

    def destruct(self, impactor: Bullet | Mine | Ship, map_size: tuple[int, int], random_ast_split: bool) -> list[Asteroid]:
        """ Spawn child asteroids"""
        # Split angle is the angle off of the new velocity vector for the two asteroids to the sides, the center child
        # asteroid continues on the new velocity path
        # If random_ast_split, the bound is the range within which uniform random angles will be selected, otherwise the
        # angle will be half of the bound
        split_angle_bound: float = 30.0
        if self.size != 1:
            if isinstance(impactor, Mine):
                if impactor.x - self.x > 0.5 * map_size[0]:
                    mine_x_wrapped = impactor.x - map_size[0]
                elif impactor.x - self.x < -0.5 * map_size[0]:
                    mine_x_wrapped = impactor.x + map_size[0]
                else:
                    mine_x_wrapped = impactor.x

                if impactor.y - self.y > 0.5 * map_size[1]:
                    mine_y_wrapped = impactor.y - map_size[1]
                elif impactor.y - self.y < -0.5 * map_size[1]:
                    mine_y_wrapped = impactor.y + map_size[1]
                else:
                    mine_y_wrapped = impactor.y

                delta_x = mine_x_wrapped - self.x
                delta_y = mine_y_wrapped - self.y

                dist = sqrt(delta_x * delta_x + delta_y * delta_y)
                force = impactor.calculate_blast_force(dist=dist, obj=self)
                a = force / self.mass
                # calculate "impulse" based on acc
                if dist != 0.0:
                    cos_theta = (self.x - mine_x_wrapped) / dist
                    sin_theta = (self.y - mine_y_wrapped) / dist
                else:
                    # Dist is 0! The mine is coincident with the asteroid. Just pretend the mine is right behind the asteroid
                    ast_speed = sqrt(self.vx * self.vx + self.vy * self.vy)
                    if ast_speed != 0.0:
                        cos_theta = self.vx / ast_speed
                        sin_theta = self.vy / ast_speed
                    else:
                        # NO WAY. The mine is coincident with the asteroid, AND the asteroid was stationary.
                        # How is that even possible? I'm baffled.
                        # Go buy a lottery ticket!
                        # Anyway, just pretend the angle is 0 in this case, and calculate the cos/sin of that
                        cos_theta = 1.0
                        sin_theta = 0.0
                vfx = self.vx + a * cos_theta
                vfy = self.vy + a * sin_theta

                # Calculate speed of resultant asteroid(s) based on velocity vector
                v = sqrt(vfx * vfx + vfy * vfy)
            else:
                # Impactor is a bullet or ship
                # Calculating new velocity vector of asteroid children based on bullet-asteroid collision/momentum
                # Currently collisions are considered perfectly inelastic i.e. the bullet is absorbed by the asteroid
                # This assumption doesn't matter much now due to the fact that bullets are "destroyed" by impact with the
                # asteroid and the bullet mass is significantly smaller than the asteroid. If this changes, these calculations
                # may need to change
                total_mass = impactor.mass + self.mass
                vfx = (impactor.mass * impactor.vx + self.mass * self.vx) / total_mass
                vfy = (impactor.mass * impactor.vy + self.mass * self.vy) / total_mass

                # Calculate speed of resultant asteroid(s) based on velocity vector
                v = sqrt(vfx * vfx + vfy * vfy)

            # Calculate angle of center asteroid for split (degrees)
            theta = degrees(atan2(vfy, vfx))

            if random_ast_split:
                # Use random angle offsets
                angle_offset_1 = split_angle_bound * random.random()
                angle_offset_2 = split_angle_bound * random.random()
                # Create the angles list
                angles = [
                    theta + angle_offset_1,
                    theta,
                    theta - angle_offset_2
                ]
            else:
                # Use a fixed half-angle offset
                angle_offset = split_angle_bound / 2.0
                # Create the angles list
                angles = [
                    theta + angle_offset,
                    theta,
                    theta - angle_offset
                ]
            return [Asteroid(position=(self.x, self.y), size=self.size - 1, speed=v, angle=angle) for angle in angles]
            # Old method of doing random splits
            # return [Asteroid(position=self.position, size=self.size-1) for _ in range(self.num_children)]
        else:
            return []

    def __repr__(self) -> str:
        return (
            f"<Asteroid("
            f"x={self.x}, y={self.y}, "
            f"vx={self.vx}, vy={self.vy}, "
            f"speed={self.speed}, angle={self.angle}, turnrate={self.turnrate}, "
            f"size={self.size}, radius={self.radius}, mass={self.mass}, "
            f"num_children={self.num_children}"
            f")>"
        )
