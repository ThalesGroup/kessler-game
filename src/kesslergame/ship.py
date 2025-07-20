# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import math
import warnings

from .bullet import Bullet
from .mines import Mine
from .controller import KesslerController
from .state_models import ShipDataList


class Ship:
    __slots__ = (
        'controller', 'thrust', 'turn_rate', 'id', 'speed', 'x', 'y',
        'vx', 'vy', 'heading', 'lives', 'deaths', 'team', 'team_name',
        'fire', 'drop_mine', 'thrust_range', 'turn_rate_range', 'max_speed',
        'drag', 'radius', 'mass', '_respawning', '_respawn_time', '_fire_limiter',
        '_fire_time', '_mine_limiter', '_mine_deploy_time', 'mines_remaining',
        'bullets_remaining', 'bullets_shot', 'mines_dropped', 'bullets_hit',
        'mines_hit', 'asteroids_hit', 'custom_sprite_path', '_state', '_ownstate'
    )
    def __init__(self, ship_id: int,
                 position: tuple[float, float],
                 angle: float = 90.0,
                 lives: int = 3,
                 team: int = 1,
                 team_name: str | None = None,
                 bullets_remaining: int = -1,
                 mines_remaining: int = 0) -> None:
        """
        Instantiate a ship with default parameters and infinite bullets if not specified
        """

        # Control information
        self.controller: KesslerController | None = None

        # Ship custom graphics
        self.custom_sprite_path: str | None = None

        # State info
        self.id: int = ship_id
        self.speed: float = 0.0
        self.x, self.y = position
        self.vx, self.vy = (0.0, 0.0)
        self.heading: float = angle
        self.lives: int = lives
        self.deaths: int = 0
        self.team: int = team
        self.team_name: str = team_name if team_name is not None else 'Team ' + str(self.team)

        # Controller inputs
        self.thrust: float = 0.0
        self.turn_rate: float = 0.0
        self.fire: bool = False
        self.drop_mine: bool = False

        # Physical model constants/params
        self.thrust_range: tuple[float, float] = (-480.0, 480.0)  # m/s^2
        self.turn_rate_range: tuple[float, float] = (-180.0, 180.0)  # Degrees per second
        self.max_speed: float = 240.0  # Meters per second
        self.drag: float = 80.0  # m/s^2
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

        # [x: float, y: float, vx: float, vy: float, speed: float, heading: float, mass: float, radius: float, id: int, team: int, is_respawning: bool, lives_remaining: int, deaths: int]
        self._state: ShipDataList = [
            self.x, self.y,
            self.vx, self.vy,
            self.speed,
            self.heading,
            self.mass,
            self.radius,
            self.id,
            self.team,
            self.is_respawning,
            self.lives,
            self.deaths
        ]

        # Extends the shared state with more internal values
        self._ownstate: ShipDataList = self._state + [
            self.bullets_remaining,
            self.mines_remaining,
            self.can_fire,
            self.fire_wait_time,
            self.fire_rate,
            self.can_deploy_mine,
            self.mine_wait_time,
            self.mine_deploy_rate,
            self.respawn_time_left,
            self.respawn_time,
            self.thrust_range[0],
            self.thrust_range[1],
            self.turn_rate_range[0],
            self.turn_rate_range[1],
            self.max_speed,
            self.drag,
        ]

    def update_state(self) -> None:
        """Update flat state and ownstate lists."""
        self._state[0] = self.x
        self._state[1] = self.y
        self._state[2] = self.vx
        self._state[3] = self.vy
        self._state[4] = self.speed
        self._state[5] = self.heading
        self._state[6] = self.mass
        self._state[7] = self.radius
        self._state[8] = self.id
        self._state[9] = self.team
        self._state[10] = self.is_respawning
        self._state[11] = self.lives
        self._state[12] = self.deaths

        # Extend the state list with the ownstate fields
        self._ownstate[0:13] = self._state  # Shared part
        self._ownstate[13] = self.bullets_remaining
        self._ownstate[14] = self.mines_remaining
        self._ownstate[15] = self.can_fire
        self._ownstate[16] = self.fire_wait_time
        self._ownstate[17] = self.fire_rate
        self._ownstate[18] = self.can_deploy_mine
        self._ownstate[19] = self.mine_wait_time
        self._ownstate[20] = self.mine_deploy_rate
        self._ownstate[21] = self.respawn_time_left
        self._ownstate[22] = self.respawn_time
        self._ownstate[23] = self.thrust_range[0]
        self._ownstate[24] = self.thrust_range[1]
        self._ownstate[25] = self.turn_rate_range[0]
        self._ownstate[26] = self.turn_rate_range[1]
        self._ownstate[27] = self.max_speed
        self._ownstate[28] = self.drag

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    @property
    def state(self) -> ShipDataList:
        return self._state

    @property
    def ownstate(self) -> ShipDataList:
        return self._ownstate

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
        return 1.0 / self._fire_time

    @property
    def mine_deploy_rate(self) -> float:
        return 1.0 / self._mine_deploy_time

    @property
    def fire_wait_time(self) -> float:
        return self._fire_limiter

    @property
    def mine_wait_time(self) -> float:
        return self._mine_limiter

    def shoot(self) -> None:
        self.fire = True

    def update(self, delta_time: float = 1 / 30, map_size: tuple[int, int] = (1000, 800)) -> tuple[Bullet | None, Mine | None]:
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
            self.speed -= math.copysign(drag_amount, self.speed)

        # Bounds check the thrust
        if self.thrust < self.thrust_range[0] or self.thrust > self.thrust_range[1]:
            self.thrust = min(max(self.thrust_range[0], self.thrust), self.thrust_range[1])
            warnings.warn('Ship ' + str(self.id) + ' thrust command outside of allowable range', RuntimeWarning)

        # Store speed and heading BEFORE acceleration/thrust for integration
        initial_speed = self.speed
        initial_heading = math.radians(self.heading)  # convert to radians

        # Apply thrust
        self.speed += self.thrust * delta_time

        # Bounds check the speed
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        elif self.speed < -self.max_speed:
            self.speed = -self.max_speed

        # Bounds check the turn rate
        if self.turn_rate < self.turn_rate_range[0] or self.turn_rate > self.turn_rate_range[1]:
            self.turn_rate = min(max(self.turn_rate_range[0], self.turn_rate), self.turn_rate_range[1])
            warnings.warn('Ship ' + str(self.id) + ' turn rate command outside of allowable range', RuntimeWarning)

        # Analytic position integration, framerate independent
        # The shape that the ship traces out with a constant turn rate and thrust over the previous frame,
        # is a Euler spiral, or Clothoid. This shape can be analytically integrated! Yay!

        # Determine speed after full step
        unclamped_final_speed = initial_speed + self.thrust * delta_time
        max_speed = self.max_speed if initial_speed >= 0 else -self.max_speed  # handle negative speeds (e.g. asteroids reverse)

        # Time to hit max speed (if at all)
        t1: float | None = None
        if self.thrust != 0.0:
            to_max = (max_speed - initial_speed) / self.thrust
            if self.thrust > 0.0 and unclamped_final_speed > max_speed and 0.0 < to_max < delta_time:
                t1 = to_max
            elif self.thrust < 0.0 and unclamped_final_speed < max_speed and 0.0 < to_max < delta_time:
                t1 = to_max

        x0: float = self.x
        y0: float = self.y

        def spiral_integration(vi: float, a: float, theta0: float, omega: float, t: float) -> tuple[float, float]:
            """
            Returns (dx, dy) using either analytic or Taylor expansion for small omega.
            Args:
                vi: initial speed
                a: acceleration
                th0: initial heading (radians)
                omega: turn rate (rad/sec)
                t: duration (seconds)
            """
            if abs(omega) < 1e-4:
                # Taylor expansion with Horner's method
                cos_theta0 = math.cos(theta0)
                sin_theta0 = math.sin(theta0)
                t_sq = t * t
                # Horner: vi*t + 0.5*a*t^2
                dt_main = t * (vi + a * t * 0.5)
                # 0.5*vi*t^2*omega + (1/6)*a*t^3*omega = (omega * tt) * (0.5*vi + a * t / 6.0)
                smallterm = omega * t_sq * (0.5 * vi + a * t / 6.0)
                dx = cos_theta0 * dt_main - sin_theta0 * smallterm
                dy = sin_theta0 * dt_main + cos_theta0 * smallterm
            else:
                delta_theta = omega * t
                theta1 = theta0 + delta_theta
                sin_theta0 = math.sin(theta0)
                sin_theta1 = math.sin(theta1)
                cos_theta0 = math.cos(theta0)
                cos_theta1 = math.cos(theta1)
                sin_diff = sin_theta1 - sin_theta0
                cos_diff = cos_theta1 - cos_theta0
                dx = (vi * sin_diff + (a / omega) * (cos_diff + delta_theta * sin_theta1)) / omega
                dy = (-vi * cos_diff + (a / omega) * (sin_diff - delta_theta * cos_theta1)) / omega
            return dx, dy

        omega = math.radians(self.turn_rate)
        theta0 = initial_heading

        if t1 is None:
            # No exceeding limit within this step, use normal analytic integration
            dx, dy = spiral_integration(initial_speed, self.thrust, theta0, omega, delta_time)
            self.x = (x0 + dx) % map_size[0]
            self.y = (y0 + dy) % map_size[1]
        else:
            # 2-phase integration: (i) accelerate to speed limit, (ii) coast at v_max
            # Phase 1: accelerating from vi to vmax over t1
            dx1, dy1 = spiral_integration(initial_speed, self.thrust, theta0, omega, t1)
            theta1 = theta0 + omega * t1

            # Phase 2: constant (max) speed, no acceleration
            # speed is clamped
            t2 = delta_time - t1
            dx2, dy2 = spiral_integration(max_speed, 0.0, theta1, omega, t2)

            self.x = (x0 + dx1 + dx2) % map_size[0]
            self.y = (y0 + dy1 + dy2) % map_size[1]

        # Update the angle based on turning rate
        self.heading += self.turn_rate * delta_time

        # Keep the angle within [0, 360.0)
        self.heading %= 360.0

        # Use speed magnitude to get velocity vector
        rad_heading = math.radians(self.heading)
        self.vx = math.cos(rad_heading) * self.speed
        self.vy = math.sin(rad_heading) * self.speed

        # Update the state dict
        self.update_state()

        return new_bullet, new_mine

    def destruct(self, map_size: tuple[float, float]) -> None:
        """
        Called by the game when a ship collides with something and dies. Handles life decrementing and triggers respawn
        """
        self.lives -= 1
        self.deaths += 1
        spawn_position = self.position # (map_size[0]/2, map_size[1]/2)
        spawn_heading = self.heading
        self.respawn(spawn_position, spawn_heading)

    def respawn(self, position: tuple[float, float], heading: float = 90.0) -> None:
        """
        Called when we die and need to make a new ship.
        'respawning' is an invulnerability timer.
        """
        # If we are in the middle of respawning, this is non-zero.
        self._respawning = self._respawn_time

        # Set location and physical parameters
        self.x, self.y = position
        self.speed = 0.0
        self.vx, self.vy = (0.0, 0.0)
        self.heading = heading

    def deploy_mine(self) -> Mine | None:
        # if self.mines_remaining != 0 and not self._mine_limiter:
        if self.can_deploy_mine:
            # Remove respawn invincibility. Mine deployment limiter
            self._respawning = 0.0
            self._mine_limiter = self._mine_deploy_time

            if self.mines_remaining != -1: # Mines are limited
                self.mines_remaining -= 1
            self.mines_dropped += 1
            mine_x = self.position[0]
            mine_y = self.position[1]
            return Mine((mine_x, mine_y), owner=self)
        else:
            return None

    def fire_bullet(self) -> Bullet | None:
        # if self.bullets_remaining != 0 and not self._fire_limiter:
        if self.can_fire:
            # Remove respawn invincibility. Trigger fire limiter
            self._respawning = 0.0
            self._fire_limiter = self._fire_time

            # Bullet counters
            if self.bullets_remaining != -1: # Bullets are limited
                self.bullets_remaining -= 1
            self.bullets_shot += 1

            # Return the bullet object that was fired
            rad_heading = math.radians(self.heading)
            bullet_x = self.position[0] + self.radius * math.cos(rad_heading)
            bullet_y = self.position[1] + self.radius * math.sin(rad_heading)
            return Bullet((bullet_x, bullet_y), self.heading, owner=self)

        # Return nothing if we can't fire a bullet right now
        return None
