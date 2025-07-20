# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import math
import warnings
import numpy as np
from typing import Any, Optional

from .bullet import Bullet
from .mines import Mine
from .controller import KesslerController


class Ship:
    __slots__ = (
        'controller', 'thrust', 'turn_thrust', 'id', 'speed', 'position',
        'velocity', 'angular_velocity', 'heading', 'lives', 'deaths', 'team', 'team_name',
        'fire', 'drop_mine', 'thrust_range', 'turn_thrust_range', 'max_speed', 'max_angular_speed',
        'drag', 'radius', 'mass', '_respawning', '_respawn_time', '_fire_limiter',
        '_fire_time', '_mine_limiter', '_mine_deploy_time', 'mines_remaining',
        'bullets_remaining', 'bullets_shot', 'mines_dropped', 'bullets_hit',
        'mines_hit', 'asteroids_hit', 'custom_sprite_path'
    )
    def __init__(self, ship_id: int,
                 position: tuple[float, float],
                 angle: float = 90.0,
                 lives: int = 3,
                 team: int = 1,
                 team_name: Optional[str] = None,
                 bullets_remaining: int = -1,
                 mines_remaining: int = 0) -> None:
        """
        Instantiate a ship with default parameters and infinite bullets if not specified
        """

        # Control information
        self.controller: Optional[KesslerController] = None

        # Ship custom graphics
        self.custom_sprite_path: Optional[str] = None

        # State info
        self.id: int = ship_id
        self.speed: float = 0.0
        self.position: tuple[float, float] = position
        self.velocity: tuple[float, float] = (0.0, 0.0)
        self.angular_velocity: float = 0.0
        self.heading: float = angle
        self.lives: int = lives
        self.deaths: int = 0
        self.team: int = team
        self.team_name: str = team_name if team_name is not None else 'Team ' + str(self.team)

        # Controller inputs
        self.thrust: float = 0.0
        self.turn_thrust: float = 0.0
        self.fire: bool = False
        self.drop_mine: bool = False

        # Physical model constants/params
        self.thrust_range: tuple[float, float] = (-480.0, 480.0)  # m/s^2
        self.turn_thrust_range: tuple[float, float] = (-180.0, 180.0)  # degrees/s^2
        self.max_speed: float = 240.0  # Meters per second
        self.max_angular_speed: float = 360.0 # degrees per second
        self.drag: float = 0.0  # m/s^2
        self.radius: float = 20.0  # meters
        self.mass: float = 300.0  # kg - reasonable? max asteroid mass currently is ~490 kg

        # Manage respawns/firing via timers
        self._respawning: float = 0.0 # seconds
        self._respawn_time: float = 3.0 # seconds
        self._fire_limiter: float = 0.0 # seconds
        self._fire_time: float = 1.0 / 10.0 # seconds
        self._mine_limiter: float = 0.0 # second
        self._mine_deploy_time: float = 1.0 # seconds

        # Track bullet/mine statistics
        self.mines_remaining: int = mines_remaining
        self.bullets_remaining: int = bullets_remaining
        self.bullets_shot: int = 0
        self.mines_dropped: int = 0
        self.bullets_hit: int = 0    # Number of bullets that hit an asteroid
        self.mines_hit: int = 0      # Number of asteroids hit by mines
        self.asteroids_hit: int = 0  # Number of asteroids hit (including ship collision)


    @property
    def state(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "angular_velocity": self.angular_velocity,
            "speed": self.speed,
            "heading": self.heading,
            "mass": self.mass,
            "radius": self.radius,
            "id": self.id,
            "team": self.team,
            "is_respawning": True if self.is_respawning else False,
            "lives_remaining": self.lives,
            "deaths": self.deaths,
        }

    @property
    def ownstate(self) -> dict[str, Any]:
        return {**self.state,
                "bullets_remaining": self.bullets_remaining,
                "mines_remaining": self.mines_remaining,
                "can_fire": self.can_fire,
                "fire_cooldown": self.fire_wait_time,
                "fire_rate": self.fire_rate,
                "can_deploy_mine": self.can_deploy_mine,
                "mine_cooldown": self.mine_wait_time,
                "mine_deploy_rate": self.mine_deploy_rate,
                "respawn_time_left": self.respawn_time_left,
                "respawn_time": self.respawn_time,
                "thrust_range": self.thrust_range,
                "turn_thrust_range": self.turn_thrust_range,
                "max_speed": self.max_speed,
                "max_angular_speed": self.max_angular_speed,
                "drag": self.drag,
        }

    @property
    def alive(self) -> bool:
        return True if self.lives > 0 else False

    @property
    def is_respawning(self) -> bool:
        return True if self._respawning else False

    @property
    def respawn_time_left(self) -> float:
        return self._respawning

    @property
    def respawn_time(self) -> float:
        return self._respawn_time

    @property
    def can_fire(self) -> bool:
        return (not self._fire_limiter) and self.bullets_remaining != 0

    @property
    def can_deploy_mine(self) -> bool:
        return (not self._mine_limiter) and self.mines_remaining != 0

    @property
    def fire_rate(self) -> float:
        return 1 / self._fire_time

    @property
    def mine_deploy_rate(self) -> float:
        return 1 / self._mine_deploy_time

    @property
    def fire_wait_time(self) -> float:
        return self._fire_limiter

    @property
    def mine_wait_time(self) -> float:
        return self._mine_limiter

    def shoot(self) -> None:
        self.fire = True

    def update(self, delta_time: float = 1 / 30) -> tuple[Optional[Bullet], Optional[Mine]]:
        """
        Update our position and other particulars.
        """

        # Fire a bullet if instructed to
        if self.fire:
            new_bullet = self.fire_bullet()
        else:
            new_bullet = None

        if self.drop_mine:
            new_mine = self.deploy_mine()
        else:
            new_mine = None

        # Decrement respawn timer (if necessary)
        if self._respawning != 0.0:
            self._respawning -= delta_time
            if self._respawning <= 1e-12:
                self._respawning = 0.0

        # Decrement fire limit timer (if necessary)
        if self._fire_limiter != 0.0:
            self._fire_limiter -= delta_time
            if self._fire_limiter <= 1e-12:
                self._fire_limiter = 0.0

        # Decrement mine deployment limit timer (if necessary)
        if self._mine_limiter != 0.0:
            self._mine_limiter -= delta_time
            if self._mine_limiter <= 1e-12:
                self._mine_limiter = 0.0

        # Apply drag. Fully stop the ship if it would cross zero speed in this time (prevents oscillation)
        drag_amount = self.drag * delta_time
        if drag_amount > abs(self.speed):
            self.speed = 0.0
        else:
            self.speed -= drag_amount * np.sign(self.speed)

        # Bounds check the thrust
        if self.thrust < self.thrust_range[0] or self.thrust > self.thrust_range[1]:
            self.thrust = min(max(self.thrust_range[0], self.thrust), self.thrust_range[1])
            warnings.warn('Ship ' + str(self.id) + ' thrust command outside of allowable range', RuntimeWarning)

        # Apply thrust
        self.velocity = (
            self.velocity[0] + self.thrust * delta_time * math.cos(math.radians(self.heading)),
            self.velocity[1] + self.thrust * delta_time * math.sin(math.radians(self.heading))
        )

        # Calculate speed based on velocity
        self.speed = math.hypot(self.velocity[0], self.velocity[1])

        # Bounds check the speed and update velocity accordingly
        if self.speed > self.max_speed:
            scale: float = self.max_speed / self.speed
            self.velocity = (self.velocity[0]*scale, self.velocity[1]*scale)
            self.speed = self.max_speed

        # Bounds check the turn thrust
        if self.turn_thrust < self.turn_thrust_range[0] or self.turn_thrust > self.turn_thrust_range[1]:
            self.turn_thrust = min(max(self.turn_thrust_range[0], self.turn_thrust), self.turn_thrust_range[1])
            warnings.warn('Ship ' + str(self.id) + ' turn thrust command outside of allowable range', RuntimeWarning)

        # Update the angular velocity based on turning thrust
        self.angular_velocity += self.turn_thrust * delta_time

        # Bounds check the angular velocity
        if self.angular_velocity > self.max_angular_speed:
            self.angular_velocity = self.max_angular_speed
        elif self.angular_velocity < -self.max_angular_speed:
            self.angular_velocity = -self.max_angular_speed

        # Update the heading based on angular velocity
        self.heading += self.angular_velocity * delta_time

        # Keep the angle within (0, 360)
        self.heading %= 360.0

        # Update the position based off the velocities
        self.position = (self.position[0] + self.velocity[0] * delta_time, self.position[1] + self.velocity[1] * delta_time)

        return new_bullet, new_mine

    def destruct(self, map_size: tuple[float, float]) -> None:
        """
        Called by the game when a ship collides with something and dies. Handles life decrementing and triggers respawn
        """
        self.lives -= 1
        self.deaths +=1
        # spawn_position = [map_size[0] / 2,
        #                   map_size[1] / 2]
        spawn_position = self.position
        spawn_heading = self.heading
        self.respawn(spawn_position, spawn_heading)

    def respawn(self, position: tuple[float, float], heading: float = 90.0) -> None:
        """
        Called when we die and need to make a new ship.
        'respawning' is an invulnerability timer.
        """
        # If we are in the middle of respawning, this is non-zero.
        self._respawning = self._respawn_time

        # Set location and physical parameters # TODO: realistic physics for respawn - change nothing? check interactions on collision with objects
        self.position = position
        self.speed = 0.0
        self.angular_velocity = 0.0
        self.velocity = (0.0, 0.0)
        self.heading = heading

    def deploy_mine(self) -> Mine | None: # TODO: decrease ship mass by 1x mine mass?
        # if self.mines_remaining != 0 and not self._mine_limiter:
        if self.can_deploy_mine:

            # Remove respawn invincibility. Mine deployment limiter
            self._respawning = 0.0
            self._mine_limiter = self._mine_deploy_time

            if self.mines_remaining > 0:
                self.mines_remaining -= 1
            self.mines_dropped += 1
            return Mine(self.position, self.velocity, owner=self)
        else:
            return None

    def fire_bullet(self) -> Bullet | None:
        # if self.bullets_remaining != 0 and not self._fire_limiter:
        if self.can_fire:

            # Remove respawn invincibility. Trigger fire limiter
            self._respawning = 0.0
            self._fire_limiter = self._fire_time

            # Bullet counters
            if self.bullets_remaining > 0:
                self.bullets_remaining -= 1
            self.bullets_shot += 1

            # Return the bullet object that was fired
            rad_heading = math.radians(self.heading)
            bullet_x = self.position[0] + self.radius * math.cos(rad_heading)
            bullet_y = self.position[1] + self.radius * math.sin(rad_heading)
            return Bullet((bullet_x, bullet_y), self.heading, owner=self)

        # Return nothing if we can't fire a bullet right now
        return None
