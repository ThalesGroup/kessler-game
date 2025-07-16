# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import math

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
from .bullet_state import BulletState

class Bullet:
    __slots__ = ('owner', 'speed', 'length', 'mass', 'position', 'heading', 'rad_heading', 'tail', 'velocity')
    def __init__(self, starting_position: tuple[float, float], starting_heading: float, owner: 'Ship') -> None:
        self.owner = owner
        self.speed: float = 800.0  # m/s
        self.length: float = 12.0
        self.mass: float = 1.0  # mass units - kg?
        self.position: tuple[float, float] = starting_position
        self.heading: float = starting_heading
        self.rad_heading: float = math.radians(starting_heading)
        cos_heading: float = math.cos(self.rad_heading)
        sin_heading: float = math.sin(self.rad_heading)
        self.tail: tuple[float, float] = (self.position[0] - self.length * cos_heading, self.position[1] - self.length * sin_heading)
        self.velocity: tuple[float, float] = (self.speed * cos_heading, self.speed * sin_heading)

    def update(self, delta_time: float = 1/30) -> None:
        # Update the position:
        self.position = (self.position[0] + self.velocity[0] * delta_time, self.position[1] + self.velocity[1] * delta_time)
        self.tail = (self.tail[0] + self.velocity[0] * delta_time, self.tail[1] + self.velocity[1] * delta_time)

    def destruct(self) -> None:
        pass

    @property
    def state(self) -> BulletState:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "heading": self.heading,
            "mass": self.mass
        }
