# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
    from .asteroid import Asteroid
from .state_models import MineDataList


class Mine:
    __slots__ = ('fuse_time', 'detonation_time', 'mass', 'radius', 'blast_radius', 'blast_pressure', 'owner', 'countdown_timer', 'detonating', 'x', 'y', '_state')
    def __init__(self, starting_position: tuple[float, float], owner: Ship) -> None:
        self.fuse_time: float = 3.0 # s
        self.detonation_time: float = 0.25 # s
        self.mass: float = 25.0  # kg
        self.radius: float = 12.0 # m
        self.blast_radius: float = 150.0 # m
        self.blast_pressure: float = 2000.0 # Pascals. I think.

        self.owner = owner
        self.countdown_timer: float = self.fuse_time
        self.detonating: bool = False
        self.x, self.y = starting_position

        # [x: float, y: float, mass: float, fuse_time: float, remaining_time: float]
        self._state: MineDataList = [
            self.x, self.y,
            self.mass,
            self.fuse_time,
            self.countdown_timer
        ]

    def update(self, delta_time: float = 1 / 30) -> None:
        self.countdown_timer -= delta_time
        # Sync the mutable state
        self._state[4] = self.countdown_timer
        if self.countdown_timer <= 1e-12:
            self.detonate()

    def detonate(self) -> None:
        # perform any detonation stuff here
        self.detonating = True

    def destruct(self) -> None:
        pass

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
        return (1.0 - dist / (self.blast_radius + obj.radius)) * self.blast_pressure * 2.0 * obj.radius
