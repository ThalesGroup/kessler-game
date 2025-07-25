# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
from .state_models import BulletDataList


class Bullet:
    __slots__ = ('owner', 'speed', 'length', 'mass', 'x', 'y', 'vx', 'vy', 'heading', 'tail_delta_x', 'tail_delta_y', '_state')
    def __init__(self, position: tuple[float, float], heading: float, owner: Ship) -> None:
        self.owner: Ship = owner
        self.speed: float = 800.0  # m/s
        self.length: float = 12.0 # m
        self.mass: float = 1.0  # kg
        self.x, self.y = position
        self.heading: float = heading
        rad_heading: float = math.radians(heading)
        cos_heading: float = math.cos(rad_heading)
        sin_heading: float = math.sin(rad_heading)
        self.tail_delta_x = -self.length * cos_heading
        self.tail_delta_y = -self.length * sin_heading
        self.vx = self.speed * cos_heading
        self.vy = self.speed * sin_heading

        # [x: float, y: float, vx: float, vy: float, tail_dx: float, tail_dy: float, heading: float, mass: float, length: float]
        self._state: BulletDataList = [
            self.x, self.y,
            self.vx, self.vy,
            self.tail_delta_x, self.tail_delta_y,
            self.heading,
            self.mass,
            self.length
        ]

    def update(self, delta_time: float = 1 / 30) -> None:
        # Update the position:
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        # Keep _state in sync
        self._state[0] = self.x
        self._state[1] = self.y

    def destruct(self) -> None:
        pass

    @property
    def state(self) -> BulletDataList:
        return self._state

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    @property
    def tail(self) -> tuple[float, float]:
        return (self.x + self.tail_delta_x, self.y + self.tail_delta_y)
