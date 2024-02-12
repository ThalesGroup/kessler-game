# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import List, Tuple, Dict, Any
import math


class Bullet:
    def __init__(self, starting_position: List[float], starting_heading: float, owner):
        self.owner = owner
        self.speed = 800  # m/s
        self.length = 12
        self.mass = 1  # mass units - kg?
        self.position = starting_position
        self.heading = starting_heading
        self.rad_heading = math.pi*starting_heading/180
        self.tail = [self.position[0] - self.length * math.cos(self.rad_heading),
                     self.position[1] - self.length * math.sin(self.rad_heading)]
        self.vx = self.speed*math.cos(self.rad_heading)
        self.vy = self.speed*math.sin(self.rad_heading)
        self.velocity = [self.vx, self.vy]

    def update(self, delta_time=1/30):
        # Update the position:
        self.position = [pos + v * delta_time for pos, v in zip(self.position, self.velocity)]
        self.tail = [pos + v * delta_time for pos, v in zip(self.tail, self.velocity)]

    def destruct(self):
        ...

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "position": tuple(self.position),
            "velocity": tuple(self.velocity),
            "heading": float(self.heading),
            "mass": float(self.mass)
        }
