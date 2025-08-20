# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
    from .asteroid import Asteroid
from .state_models import MineDataList


class Mine:
    __slots__ = ('fuse_time', 'detonation_time', 'mass', 'radius', 'blast_radius', 'blast_pressure', 'owner', 'countdown_timer', 'x', 'y', '_state')

    def __init__(self, starting_position: tuple[float, float], owner: Ship) -> None:
        self.fuse_time: float = 3.0  # s
        self.detonation_time: float = 0.25  # s
        self.mass: float = 25.0  # kg
        self.radius: float = 12.0  # m
        self.blast_radius: float = 150.0  # m
        self.blast_pressure: float = 2000.0  # Pascals. I think.

        self.owner = owner
        self.countdown_timer: float = self.fuse_time
        self.x, self.y = starting_position

        # [x: float, y: float, mass: float, fuse_time: float, remaining_time: float]
        self._state: MineDataList = [
            self.x, self.y,
            self.mass,
            self.fuse_time,
            self.countdown_timer
        ]

    def update(self, delta_time: float) -> None:
        # Avoid attribute lookup using local var
        countdown_timer = self.countdown_timer - delta_time
        self.countdown_timer = countdown_timer
        # Sync the mutable state
        self._state[4] = countdown_timer

    def destruct(self) -> None:
        pass

    @property
    def detonating(self) -> bool:
        return self.countdown_timer <= 1e-12

    @property
    def state(self) -> MineDataList:
        return self._state

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    def calculate_blast_force(self, dist: float, obj: Asteroid) -> float:
        """
        Calculates the blast force based on the blast radius, blast pressure, and a linear decrease in intensity from the mine location to the blast radius
        Also takes into account asteroid diameter to resolve total acceleration based on size/mass
        """
        # Multiplication order precedence groups together the constant terms on the right, for more optimization opportunity in other game implementations
        return (1.0 - dist / (self.blast_radius + obj.radius)) * (self.blast_pressure * (2.0 * obj.radius))

    def __repr__(self) -> str:
        return (
            f"<Mine("
            f"x={self.x}, y={self.y}, "
            f"mass={self.mass}, radius={self.radius}, "
            f"blast_radius={self.blast_radius}, blast_pressure={self.blast_pressure}, "
            f"fuse_time={self.fuse_time}, countdown_timer={self.countdown_timer}, "
            f"detonating={self.detonating}, owner={self.owner}"
            f")>"
        )
