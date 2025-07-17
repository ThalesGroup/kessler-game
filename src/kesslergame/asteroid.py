# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TYPE_CHECKING, Union
import random
import math

if TYPE_CHECKING:
    from .ship import Ship
    from .bullet import Bullet
from .mines import Mine
from .state_dicts import AsteroidState

class Asteroid:
    """ Sprite that represents an asteroid. """
    __slots__ = ('size', 'num_children', 'radius', 'mass', 'x', 'y', 'vx', 'vy', 'angle', 'turnrate', '_state', '_position')
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
        if size:
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

        # Set collision radius based on size # TODO May need to change once size can be visualized
        self.radius: float = self.size * 8.0

        self.mass: float = 0.25 * math.pi * self.radius * self.radius

        # Use optional angle and speed arguments otherwise generate random angle and speed
        starting_angle_rad: float = math.radians(angle) if angle is not None else random.random() * 2.0 * math.pi
        starting_speed: float = speed if speed is not None else random.random() * max_speed - max_speed / 2.0

        # Set velocity based on starting angle and speed
        self.vx = starting_speed * math.cos(starting_angle_rad)
        self.vy = starting_speed * math.sin(starting_angle_rad)

        # Set position as specified
        self.x, self.y = position
        # It is important that this is a mutable list, even though conceptually it is a tuple
        self._position: list[float] = list(position)

        # Random rotations for use in display or future use with complex hit box
        self.angle: float = random.uniform(0.0, 360.0)
        self.turnrate: float = random.uniform(-100, 100)

        self._state: AsteroidState = {
            "position": self._position,
            "velocity": self.velocity,
            "size": self.size,
            "mass": self.mass,
            "radius": self.radius
        }

    @property
    def state(self) -> AsteroidState:
        return self._state
    
    @property
    def position(self) -> list[float]:
        return self._position

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    def update(self, delta_time: float = 1 / 30, map_size: tuple[int, int] = (1000, 800)) -> None:
        """ Move the asteroid based on velocity"""
        self.x = (self.x + self.vx * delta_time) % map_size[0]
        self.y = (self.y + self.vy * delta_time) % map_size[1]
        # Update the state dict without a dict lookup, using the mutable list storing position
        self._position[0] = self.x
        self._position[1] = self.y
        self.angle += delta_time * self.turnrate

    def destruct(self, impactor: Union['Bullet', 'Mine', 'Ship'], random_ast_split: bool) -> list['Asteroid']:
        """ Spawn child asteroids"""
        # Split angle is the angle off of the new velocity vector for the two asteroids to the sides, the center child
        # asteroid continues on the new velocity path
        # If random_ast_split, the bound is the range within which uniform random angles will be selected, otherwise the
        # angle will be half of the bound
        split_angle_bound: float = 30.0
        if self.size != 1:
            if isinstance(impactor, Mine):
                delta_x = impactor.position[0] - self.x
                delta_y = impactor.position[1] - self.y
                dist = math.sqrt(delta_x * delta_x + delta_y * delta_y)
                F = impactor.calculate_blast_force(dist=dist, obj=self)
                a = F / self.mass
                # calculate "impulse" based on acc
                if dist != 0.0:
                    cos_theta = (self.x - impactor.position[0]) / dist
                    sin_theta = (self.y - impactor.position[1]) / dist
                    vfx = self.vx + a * cos_theta
                    vfy = self.vy + a * sin_theta

                    # Calculate speed of resultant asteroid(s) based on velocity vector
                    v = math.sqrt(vfx * vfx + vfy * vfy)
                else:
                    vfx = self.vx
                    vfy = self.vy
                    
                    # Calculate speed of resultant asteroid(s) based on velocity vector
                    # This v calculation matches the speed you would get in the nonzero dist case, if you take the limit as dist -> 0
                    v = math.sqrt(vfx * vfx + vfy * vfy + a * a)
                    # Split angle is the angle off of the new velocity vector for the two asteroids to the sides, the center child
                    # asteroid continues on the new velocity path
                    split_angle_bound *= 8.0
            else:
                # Calculating new velocity vector of asteroid children based on bullet-asteroid collision/momentum
                # Currently collisions are considered perfectly inelastic i.e. the bullet is absorbed by the asteroid
                # This assumption doesn't matter much now due to the fact that bullets are "destroyed" by impact with the
                # asteroid and the bullet mass is significantly smaller than the asteroid. If this changes, these calculations
                # may need to change

                impactor_vx = impactor.velocity[0]
                impactor_vy = impactor.velocity[1]

                vfx = (1.0 / (impactor.mass + self.mass)) * (impactor.mass * impactor_vx + self.mass * self.vx)
                vfy = (1.0 / (impactor.mass + self.mass)) * (impactor.mass * impactor_vy + self.mass * self.vy)

                # Calculate speed of resultant asteroid(s) based on velocity vector
                v = math.sqrt(vfx * vfx + vfy * vfy)

            # Calculate angle of center asteroid for split (degrees)
            theta = math.degrees(math.atan2(vfy, vfx))

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
