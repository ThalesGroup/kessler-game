# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import Tuple, Dict, List, Any, Optional, TYPE_CHECKING, Union
import random
import math

if TYPE_CHECKING:
    from .ship import Ship
    from .bullet import Bullet
from .mines import Mine

class Asteroid:
    """ Sprite that represents an asteroid. """
    __slots__ = ('size', 'max_speed', 'num_children', 'radius', 'mass', 'vx', 'vy', 'velocity', 'position', 'angle', 'turnrate')
    def __init__(self,
                 position: Tuple[float, float],
                 speed: Optional[float] = None,
                 angle: Optional[float] = None,
                 size: Optional[int] = None) -> None:
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
        speed_scaler = 2.0 + (4.0 - self.size) / 4.0
        self.max_speed = 60.0 * speed_scaler

        # Number of child asteroids spawned when this asteroid is destroyed
        self.num_children = 3

        # Set collision radius based on size # TODO May need to change once size can be visualized
        self.radius = self.size * 8.0

        self.mass = 0.25*math.pi*self.radius*self.radius

        # Use optional angle and speed arguments otherwise generate random angle and speed
        starting_angle = angle if angle is not None else random.random()*360.0
        starting_speed = speed if speed is not None else random.random()*self.max_speed - self.max_speed/2.0

        # Set velocity based on starting angle and speed
        # self.velocity = [
        #     -starting_speed * math.sin(math.radians(starting_angle)),
        #     starting_speed * math.cos(math.radians(starting_angle))
        # ]

        self.vx = starting_speed*math.cos(math.radians(starting_angle))
        self.vy = starting_speed*math.sin(math.radians(starting_angle))
        self.velocity = (self.vx, self.vy)

        # Set position as specified
        self.position = position

        # Random rotations for use in display or future use with complex hit box
        self.angle: float = random.uniform(0.0, 360.0)
        self.turnrate: float = random.uniform(-100, 100)

    @property
    def state(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "size": self.size,
            "mass": self.mass,
            "radius": self.radius
        }

    def update(self, delta_time: float = 1/30) -> None:
        """ Move the asteroid based on velocity"""
        self.position = (self.position[0] + self.velocity[0] * delta_time, self.position[1] + self.velocity[1] * delta_time)
        self.angle += delta_time * self.turnrate

    def destruct(self, impactor: Union['Bullet', 'Mine', 'Ship']) -> list['Asteroid']:
        """ Spawn child asteroids"""

        if self.size != 1:
            if isinstance(impactor, Mine):
                delta_x = impactor.position[0] - self.position[0]
                delta_y = impactor.position[1] - self.position[1]
                dist = math.sqrt(delta_x*delta_x + delta_y*delta_y)
                F = impactor.calculate_blast_force(dist=dist, obj=self)
                a = F/self.mass
                # calculate "impulse" based on acc
                if dist != 0.0:
                    cos_theta = (self.position[0] - impactor.position[0])/dist
                    sin_theta = (self.position[1] - impactor.position[1])/dist
                    vfx = self.vx + a*cos_theta
                    vfy = self.vy + a*sin_theta

                    # Calculate speed of resultant asteroid(s) based on velocity vector
                    v = math.sqrt(vfx*vfx + vfy*vfy)
                    # Split angle is the angle off of the new velocity vector for the two asteroids to the sides, the center child
                    # asteroid continues on the new velocity path
                    split_angle = 15.0
                else:
                    vfx = self.vx
                    vfy = self.vy
                    
                    # Calculate speed of resultant asteroid(s) based on velocity vector
                    # This v calculation matches the speed you would get in the nonzero dist case, if you take the limit as dist -> 0
                    v = math.sqrt(vfx*vfx + vfy*vfy + a*a)
                    # Split angle is the angle off of the new velocity vector for the two asteroids to the sides, the center child
                    # asteroid continues on the new velocity path
                    split_angle = 120.0
            else:
                # Calculating new velocity vector of asteroid children based on bullet-asteroid collision/momentum
                # Currently collisions are considered perfectly inelastic i.e. the bullet is absorbed by the asteroid
                # This assumption doesn't matter much now due to the fact that bullets are "destroyed" by impact with the
                # asteroid and the bullet mass is significantly smaller than the asteroid. If this changes, these calculations
                # may need to change

                impactor_vx = impactor.velocity[0]
                impactor_vy = impactor.velocity[1]

                vfx = (1/(impactor.mass + self.mass))*(impactor.mass*impactor_vx + self.mass*self.vx)
                vfy = (1/(impactor.mass + self.mass))*(impactor.mass*impactor_vy + self.mass*self.vy)

                # Calculate speed of resultant asteroid(s) based on velocity vector
                v = math.sqrt(vfx*vfx + vfy*vfy)
                # Split angle is the angle off of the new velocity vector for the two asteroids to the sides, the center child
                # asteroid continues on the new velocity path
                split_angle = 15.0
            # Calculate angle of center asteroid for split (degrees)
            theta = math.degrees(math.atan2(vfy, vfx))
            angles = [theta + split_angle, theta, theta - split_angle]

            return [Asteroid(position=self.position, size=self.size-1, speed=v, angle=angle) for angle in angles]

                # Old method of doing random splits
                # return [Asteroid(position=self.position, size=self.size-1) for _ in range(self.num_children)]
        else:
            return []
