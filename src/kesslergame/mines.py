# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .ship import Ship
    from .asteroid import Asteroid


class Mine:
    __slots__ = (
        'fuse_time', 'detonation_time', 'mass', 'radius', 'blast_radius',
        'blast_pressure', 'owner', 'countdown_timer', 'detonating', 'position',
        'velocity'
    )
    def __init__(self, starting_position: tuple[float, float], starting_velocity: tuple[float, float], owner: 'Ship') -> None:
        self.fuse_time: float = 3.0
        self.detonation_time: float = 0.25
        self.mass: float = 25.0  # kg
        self.radius: float = 12.0
        self.blast_radius: float = 150.0
        self.blast_pressure: float = 2000.0

        self.owner = owner
        self.countdown_timer: float = self.fuse_time
        self.detonating: bool = False
        self.position: tuple[float, float] = starting_position
        self.velocity: tuple[float, float] = starting_velocity

    def update(self, delta_time: float = 1/30) -> None: # TODO: is there collision detection on mines? should that make them either explode early or change their velocity? Threshold impact force to determine explosion or not?
        # Update the position based off the velocity
        self.position = (self.position[0] + self.velocity[0] * delta_time, self.position[1] + self.velocity[1] * delta_time)

        self.countdown_timer -= delta_time
        if self.countdown_timer <= 1e-15:
            self.detonate()

    def detonate(self) -> None:
        # perform any detonation stuff here
        self.detonating = True

    def destruct(self) -> None:
        pass

    @property
    def state(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "mass": self.mass,
            "fuse_time": self.fuse_time,
            "remaining_time": self.countdown_timer
        }

    def calculate_blast_force(self, dist: float, obj: 'Asteroid') -> float:
        """
        Calculates the blast force based on the blast radius, blast pressure, and a linear decrease in intensity from the mine location to the blast radius
        Also takes into account asteroid diameter to resolve total acceleration based on size/mass
        """
        return (1.0 - dist / (self.blast_radius + obj.radius)) * self.blast_pressure * 2.0 * obj.radius # TODO: is this realistic physics behaviour?
