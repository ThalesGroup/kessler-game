# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import List, Tuple, Dict, Any
import math

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship


class Bullet:
    __slots__ = ('owner', 'speed', 'length', 'mass', 'position', 'heading', 'rad_heading', 'tail', 'vx', 'vy', 'velocity')
    def __init__(self, starting_position: Tuple[float, float], starting_heading: float, owner: 'Ship') -> None:
        self.owner = owner
        self.speed = 800.0  # m/s
        self.length = 12.0
        self.mass = 1.0  # mass units - kg?
        self.position = starting_position
        self.heading = starting_heading
        self.rad_heading = math.radians(starting_heading)
        cos_heading = math.cos(self.rad_heading)
        sin_heading = math.sin(self.rad_heading)
        self.tail = (self.position[0] - self.length*cos_heading,
                     self.position[1] - self.length*sin_heading)
        self.vx = self.speed*cos_heading
        self.vy = self.speed*sin_heading
        self.velocity = [self.vx, self.vy]

    def update(self, delta_time: float = 1/30) -> None:
        # Update the position:
        self.position = (self.position[0] + self.velocity[0] * delta_time, self.position[1] + self.velocity[1] * delta_time)
        self.tail = (self.tail[0] + self.velocity[0] * delta_time, self.tail[1] + self.velocity[1] * delta_time)

    def destruct(self) -> None:
        pass

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "position": tuple(self.position),
            "velocity": tuple(self.velocity),
            "heading": float(self.heading),
            "mass": float(self.mass)
        }
