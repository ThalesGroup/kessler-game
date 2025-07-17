# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
from .state_dicts import BulletState


class Bullet:
    __slots__ = ('owner', 'speed', 'length', 'mass', 'x', 'y', 'vx', 'vy', 'heading', 'rad_heading', 'tail_delta_x', 'tail_delta_y', '_state', '_position')
    def __init__(self, position: tuple[float, float], starting_heading: float, owner: 'Ship') -> None:
        self.owner: Ship = owner
        self.speed: float = 800.0  # m/s
        self.length: float = 12.0
        self.mass: float = 1.0  # mass units - kg?
        self.x, self.y = position
        self._position: list[float] = [self.x, self.y] # Mutable!
        self.heading: float = starting_heading
        self.rad_heading: float = math.radians(starting_heading)
        cos_heading: float = math.cos(self.rad_heading)
        sin_heading: float = math.sin(self.rad_heading)
        self.tail_delta_x, self.tail_delta_y = (-self.length * cos_heading, -self.length * sin_heading)
        self.vx, self.vy = (self.speed * cos_heading, self.speed * sin_heading)

        self._state: BulletState = {
            "position": self._position,
            "velocity": self.velocity,
            "heading": self.heading,
            "mass": self.mass
        }

    def update(self, delta_time: float = 1/30) -> None:
        # Update the position:
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        # Take advantage of mutability and quickly update the position
        self._position[0] = self.x
        self._position[1] = self.y

    def destruct(self) -> None:
        pass

    @property
    def state(self) -> BulletState:
        return self._state

    @property
    def position(self) -> list[float]:
        return self._position

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    @property
    def tail(self) -> tuple[float, float]:
        return (self.x + self.tail_delta_x, self.y + self.tail_delta_y)
