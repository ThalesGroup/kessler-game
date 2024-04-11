# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import List, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
    from .asteroid import Asteroid


class Mine:
    __slots__ = ('fuse_time', 'detonation_time', 'mass', 'radius', 'blast_radius', 'blast_pressure', 'owner', 'countdown_timer', 'detonating', 'position')
    def __init__(self, starting_position: List[float], owner: 'Ship') -> None:
        self.fuse_time = 3.0
        self.detonation_time = 0.25
        self.mass = 25.0  # mass units - kg?
        self.radius = 12.0
        self.blast_radius = 150.0
        self.blast_pressure = 2000.0

        self.owner = owner
        self.countdown_timer = self.fuse_time
        self.detonating = False
        self.position = starting_position

    def update(self, delta_time: float = 1/30) -> None:
        self.countdown_timer -= delta_time
        if self.countdown_timer <= 1e-15:
            self.detonate()

    def detonate(self) -> None:
        # perform any detonation stuff here
        self.detonating = True

    def destruct(self) -> None:
        pass

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "position": tuple(self.position),
            "mass": float(self.mass),
            "fuse_time": float(self.fuse_time),
            "remaining_time": float(self.countdown_timer)
        }

    def calculate_blast_force(self, dist: float, obj: 'Asteroid') -> float:
        """
        Calculates the blast force based on the blast radius, blast pressure, and a linear decrease in intensity from the mine location to the blast radius
        Also takes into account asteroid diameter to resolve total acceleration based on size/mass
        """
        return (-dist/self.blast_radius + 1) * self.blast_pressure * 2.0 * obj.radius
