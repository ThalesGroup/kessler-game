# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import warnings
from math import cos, sin, copysign, radians

from .bullet import Bullet
from .mines import Mine
from .controller import KesslerController
from .state_models import ShipDataList
from .math_utils import analytic_ship_movement_integration


class Ship:
    __slots__ = (
        'controller', 'thrust', 'turn_rate', 'id', 'speed', 'x', 'y',
        'vx', 'vy', 'heading', 'lives', 'team', 'team_name',
        'fire', 'drop_mine', 'thrust_range', 'turn_rate_range', 'max_speed',
        'drag', 'radius', 'mass', '_respawning', '_respawn_time',
        '_fire_limiter', '_fire_time', '_mine_limiter', '_mine_deploy_time', 'bullets_remaining',
        'mines_remaining', 'bullets_shot', 'mines_dropped', 'bullet_asteroid_hits',
        'ship_asteroid_hits', 'ship_ship_hits', 'mine_ship_hits', 'mine_asteroid_hits',
        'asteroid_deaths', 'ship_deaths', 'mine_deaths',
        'custom_sprite_path', 'integration_initial_states', '_state', '_ownstate'
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

        # The controller gets assigned later
        self.controller: KesslerController | None = None

        # Ship custom graphics, assigned later
        self.custom_sprite_path: str | None = None

        # State info
        self.id: int = ship_id
        self.team: int = team
        self.team_name: str = team_name if team_name is not None else 'Team ' + str(self.team)

        self.speed: float = 0.0
        self.x, self.y = position
        self.vx, self.vy = (0.0, 0.0)
        self.heading: float = angle
        self.lives: int = lives

        # To be able to perform continuous collision detection between the ship and other objects,
        # We need to store the stages of integration over the previous frame
        # So that the integration can be re-done in reverse to trace out the ship's exact path.
        # The start and end times are in reverse-chronological order! And the initial states are also at the start time, which is the latest time.
        # The tuple is (start_time_in_s_from_beginning_of_frame, integration_duration_s, v0, a, theta0, omega, full_integral_dx, full_integral_dy)
        self.integration_initial_states: list[tuple[float, float, float, float, float, float, float, float]] = []

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
        self._respawning: float = 0.0  # seconds
        self._respawn_time: float = 3.0  # seconds
        self._fire_limiter: float = 0.0  # seconds
        self._fire_time: float = 1.0 / 10.0  # seconds
        self._mine_limiter: float = 0.0  # second
        self._mine_deploy_time: float = 1.0  # seconds

        # Track bullet/mine statistics
        assert bullets_remaining >= -1, f"Bullets remaining is not at least -1: {bullets_remaining}"
        self.bullets_remaining: int = bullets_remaining
        assert mines_remaining >= -1, f"Mines remaining is not at least -1: {mines_remaining}"
        self.mines_remaining: int = mines_remaining
        self.bullets_shot: int = 0
        self.mines_dropped: int = 0

        # Asteroid hit statistics
        self.bullet_asteroid_hits: int = 0
        self.ship_asteroid_hits: int = 0
        self.ship_ship_hits: int = 0
        self.mine_asteroid_hits: int = 0
        self.mine_ship_hits: int = 0

        # Death statistics
        self.asteroid_deaths: int = 0
        self.ship_deaths: int = 0
        self.mine_deaths: int = 0

        # [x: float, y: float, vx: float, vy: float, speed: float, heading: float, mass: float, radius: float, id: int, team: int, is_respawning: bool, lives_remaining: int]
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
            self.lives
        ]

        # Extends the shared state with the ownstate values
        # [bullets_remaining: int, mines_remaining: int, can_fire: bool, fire_wait_time: float, fire_rate: float, can_deploy_mine: bool, mine_wait_time: float, mine_deploy_rate: float, respawn_time_left: float, respawn_time: float, thrust_range_min: float, thrust_range_max: float, turn_rate_range_min: float, turn_rate_range_max: float, max_speed: float, drag: float]
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
        # Constant values are commented out, as they do not need updating
        # Cache the class attribute lookup into local variables
        state = self._state
        state[0] = self.x
        state[1] = self.y
        state[2] = self.vx
        state[3] = self.vy
        state[4] = self.speed
        state[5] = self.heading
        #state[6] = self.mass
        #state[7] = self.radius
        #state[8] = self.id
        #state[9] = self.team
        state[10] = self.is_respawning
        state[11] = self.lives

        # Extend the state list with the ownstate fields
        ownstate = self._ownstate
        ownstate[0:12] = state  # Shared part
        ownstate[12] = self.bullets_remaining
        ownstate[13] = self.mines_remaining
        ownstate[14] = self.can_fire
        ownstate[15] = self.fire_wait_time
        #ownstate[16] = self.fire_rate
        ownstate[17] = self.can_deploy_mine
        ownstate[18] = self.mine_wait_time
        #ownstate[19] = self.mine_deploy_rate
        ownstate[20] = self.respawn_time_left
        #ownstate[21] = self.respawn_time
        #ownstate[22] = self.thrust_range[0]
        #ownstate[23] = self.thrust_range[1]
        #ownstate[24] = self.turn_rate_range[0]
        #ownstate[25] = self.turn_rate_range[1]
        #ownstate[26] = self.max_speed
        #ownstate[27] = self.drag

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
        return self.lives > 0

    @property
    def is_respawning(self) -> bool:
        # Externally, if a ship's respawn expires right this instant, we say it's no longer respawning
        return self._respawning > 1e-12

    @property
    def is_respawning_internal(self) -> bool:
        # Internally, if a ship's respawn comes off this instant, we still treat it as invulnerable
        return self._respawning > -1e-12

    @property
    def respawn_time_left(self) -> float:
        clamped_to_zero = max(0.0, self._respawning)
        if clamped_to_zero <= 1e-12:
            return 0.0
        else:
            return clamped_to_zero

    @property
    def respawn_time_internal(self) -> float:
        # This can go negative! This internally tracks when the ship got out of respawn,
        # so it's important this keeps getting subtracted into the negatives.
        # This, despite being a internal "private" variable, is accessed from an outside class
        return self._respawning

    @property
    def respawn_time(self) -> float:
        # This is a constant, which is the respawn invulnerability time that the ship gets
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
        # Note that this cooldown does NOT get reset when the ship dies.
        return self._fire_limiter

    @property
    def mine_wait_time(self) -> float:
        # Note that this cooldown does NOT get reset when the ship dies.
        return self._mine_limiter

    @property
    def asteroids_hit(self) -> int:
        return self.bullet_asteroid_hits + self.ship_asteroid_hits + self.mine_asteroid_hits

    @property
    def ships_hit(self) -> int:
        return self.ship_ship_hits + self.mine_ship_hits

    @property
    def deaths(self) -> int:
        return self.asteroid_deaths + self.ship_deaths + self.mine_deaths

    def shoot(self) -> None:
        self.fire = True

    def get_past_position(self, delta_time: float, map_size: tuple[int, int]) -> tuple[float, float]:
        # We have recorded how we did the forward integration, so we use that history to do the backward integration.
        assert self.integration_initial_states, "Cannot rollback ship state without a preceding forward update!"
        # Accumulate the pieces of the integral
        dx_sum = 0.0
        dy_sum = 0.0
        # To get the position of the ship in the past, we integrate its position backward
        # using the integration intervals we stored in the ship state when it was integrating it forward in time.
        # If the integral is split into multiple time segments, add them all up going backward in time,
        # until we hit delta_time, the end point of the integration

        # Keep in mind that the start_t and end_t are reverse chronological! So it starts in the future, and ends in the past!
        for ship_initial_state in self.integration_initial_states:
            start_t, end_t, v0, a, theta0, omega, dx, dy = ship_initial_state
            assert end_t - start_t <= 0.0
            if end_t < delta_time <= start_t:
                # We need to include this interval since t lies in the middle of it
                dx, dy = analytic_ship_movement_integration(v0, a, theta0, omega, delta_time - start_t)
                dx_sum += dx
                dy_sum += dy
                assert delta_time - start_t <= 0.0
                break  # Break since no more full intervals will lie beyond this, as the integral is assumed to be from 0 to t, where t <= 0
            else:
                # This interval is fully included within t. Add the full integral amount
                assert delta_time <= end_t
                dx_sum += dx
                dy_sum += dy
                assert end_t - start_t <= 0.0
        return ((self.x + dx_sum) % map_size[0], (self.y + dy_sum) % map_size[1])

    def update(self, delta_time: float, map_size: tuple[int, int], allow_shooting: bool) -> tuple[Bullet | None, Mine | None]:
        """
        Update our position and other particulars.
        """

        # Handle shooting and mining
        if allow_shooting:
            new_bullet = self.fire_bullet(map_size) if self.fire else None
            new_mine = self.deploy_mine() if self.drop_mine else None
        else:
            new_bullet = None
            new_mine = None

        # Bounds check the thrust
        if self.thrust < self.thrust_range[0] or self.thrust > self.thrust_range[1]:
            self.thrust = min(max(self.thrust_range[0], self.thrust), self.thrust_range[1])
            warnings.warn('Ship ' + str(self.id) + ' thrust command outside of allowable range', RuntimeWarning)

        # Bounds check the turn rate
        if self.turn_rate < self.turn_rate_range[0] or self.turn_rate > self.turn_rate_range[1]:
            self.turn_rate = min(max(self.turn_rate_range[0], self.turn_rate), self.turn_rate_range[1])
            warnings.warn('Ship ' + str(self.id) + ' turn rate command outside of allowable range', RuntimeWarning)

        # The tricky part about integration the ship's movement with thrust and drag, is that
        # there is a speed cap, and there is also the zero boundary.
        # If the ship hits the speed cap in the middle of the frame, the integration gets split up into two phases.
        # If the ship has a thrust magnitude of less than drag, and drag causes the ship to stop, technically
        # the ship undergoes INFINITELY many periods of integration, because drag will cause it to infinitely oscillate
        # around 0 speed. But of course we will just treat this as having zero net acceleration, and the ship stays at 0 speed.
        # This is a special case we have to detect, so we don't oscillate the ship, or cause it to bypass the zero boundary.
        if delta_time == 0.0:
            # Update the mutable state
            self.update_state()
            return new_bullet, new_mine
        elif delta_time > 0.0:
            # Store speed and heading BEFORE acceleration/thrust for integration
            initial_speed = self.speed
            theta0 = radians(self.heading)  # convert to radians
            self.integration_initial_states.clear()

            is_moving: bool = abs(initial_speed) > 1e-12

            # Get direction of motion for drag
            if is_moving:
                motion_sign = copysign(1.0, initial_speed)
            else:
                motion_sign = copysign(1.0, self.thrust) if abs(self.thrust) > 1e-12 else 0.0

            # Drag will always oppose the direction of motion
            # If the ship is not moving, then drag will be zero.
            drag_acc = -self.drag * motion_sign

            # NOTE: When testing this, there was identical behavior of framerates down to 2 FPS, but 1 FPS gave different behavior.
            # Took a while to realize the issue is that at a delta_time of 1 second, the ship can both cross the 0 boundary, AND accelerate to hit the speed cap in the same frame!
            # This does NOT handle that case robustly. It doesn't check for that. Please do not run the game at lower than 2 FPS!

            # Combine thrust and drag into one net acceleration
            # This constant acceleration will apply for the entire duration of this frame, unless we hit the speed cap or hit 0
            # If we hit the speed cap, we do 0 acceleration after that time for the rest of the frame
            # If we hit speed 0, the direction of drag will change right after. We consider two cases:
            # 1. Net acc doesn't change sign change, so the ship will continue accelerating in the same direction, just with 2*drag less acceleration
            #    To handle, we split up the integration into period 1 with thrust + drag, and period 2 with thrust - drag, where these two quantities have the same sign
            # 2. Net acc changes sign, meaning the ship will infinitely oscillate across the 0 boundary every infinitesimal timestep forward.
            #    To handle this, we split up the integration into period 1 with net_acc, and period 2 with 0 acceleration to simulate the infinite oscillations
            net_acc = self.thrust + drag_acc  # m/s^2
            if not is_moving and abs(drag_acc) > abs(self.thrust):
                net_acc = 0.0
            # We perform analytic position integration, which is framerate independent
            # The shape that the ship traces out with a constant turn rate and thrust over the previous frame is a type of spiral
            # This spiral can be analytically integrated! Yay!

            x0: float = self.x
            y0: float = self.y
            omega = radians(self.turn_rate)

            # Determine if we need to break the frame into two parts
            t1: float | None = None
            v1: float = 0.0
            accel_phase2 = 0.0  # default to coasting at max speed, or stopped in second phase

            if is_moving and net_acc * initial_speed < 0.0:  # Net accel is opposite sign from direction of movement
                # Case 1: drag will bring us to a stop
                assert net_acc != 0.0
                t_to_stop = -initial_speed / net_acc  # This is a positive number, and net_acc is nonzero
                assert t_to_stop >= 0.0
                if 0.0 <= t_to_stop < delta_time:
                    t1 = t_to_stop
                    v1 = 0.0  # Fully stopped
                    # Drag now goes the other way, since our speed has crossed the zero boundary and drag will oppose our new speed
                    # if sign(self.thrust + drag_acc) == sign(self.thrust - drag_acc)
                    # This statement is logically equivalent to the faster-to-evaluate:
                    if abs(drag_acc) <= abs(self.thrust):
                        # The thrust is enough to carry us through the "zero valley" without falling back into it and infinitely oscillating
                        accel_phase2 = self.thrust - drag_acc
                    else:
                        # Thrust too weak. We fall into zero valley and infinitely oscillate!
                        accel_phase2 = 0.0  # Infinite oscillations around 0. Essentially simulate that with 0 acceleration to bypass oscillations.
            else:
                # Case 2: acceleration would exceed max speed eventually
                max_speed = copysign(self.max_speed, initial_speed + net_acc * delta_time)
                if net_acc != 0.0 and delta_time != 0.0:
                    to_max = (max_speed - initial_speed) / net_acc
                    assert to_max >= 0.0
                    # If we'll achieve and exceed max speed within this frame
                    if 0.0 <= to_max < delta_time:
                        assert ((net_acc > 0.0 and initial_speed <= max_speed) or (net_acc < 0.0 and initial_speed >= max_speed))
                        # The starting point for the second integration phase is starting at max speed,
                        # at the time when we will achieve max speed from the first phase
                        t1 = to_max
                        v1 = max_speed
                        accel_phase2 = 0.0

            if t1 is None or abs(t1 - delta_time) < 1e-12:
                # No exceeding limit within this step, use normal single-phase analytic integration
                dx, dy = analytic_ship_movement_integration(initial_speed, net_acc, theta0, omega, delta_time)
                self.x = (x0 + dx) % map_size[0]
                self.y = (y0 + dy) % map_size[1]
                self.speed = initial_speed + net_acc * delta_time
                # Append the end state, so we can reverse-integrate later by plugging in a negative time
                self.integration_initial_states.append((0.0, -delta_time, self.speed, net_acc, theta0 + omega * delta_time, omega, -dx, -dy))
            elif abs(t1) < 1e-12:
                assert v1 is not None
                # The first period is just zero length, so just skip it
                # This happens a lot when the ship is gunning it at full throttle, so handle it separately
                # Constant speed or stopped in this second phase, no acceleration
                dx, dy = analytic_ship_movement_integration(v1, accel_phase2, theta0, omega, delta_time)

                self.x = (x0 + dx) % map_size[0]
                self.y = (y0 + dy) % map_size[1]
                self.speed += accel_phase2 * delta_time  # Skip the first phase of speed integration, and just do the second phase

                # Append the end state, so we can reverse-integrate later by plugging in a negative time
                self.integration_initial_states.append((0.0, -delta_time, self.speed, accel_phase2, theta0 + omega * delta_time, omega, -dx, -dy))
            else:
                assert v1 is not None
                # 2-phase integration splitting frame into two periods. 1: accelerate to speed limit or zero, 2: coasting or stationary
                # Phase 1: accelerating from v0 to v1 over t1
                dx1, dy1 = analytic_ship_movement_integration(initial_speed, net_acc, theta0, omega, t1)
                theta1 = theta0 + omega * t1
                self.speed = v1  # Either stopped or clamped

                # Phase 2: constant speed or stopped, no acceleration
                t2 = delta_time - t1
                dx2, dy2 = analytic_ship_movement_integration(v1, accel_phase2, theta1, omega, t2)

                self.x = (x0 + dx1 + dx2) % map_size[0]
                self.y = (y0 + dy1 + dy2) % map_size[1]
                self.speed += accel_phase2 * t2

                # Append the end state, so we can reverse-integrate later by plugging in a negative time
                self.integration_initial_states.append((0.0, -t2, self.speed, accel_phase2, theta1 + omega * t2, omega, -dx2, -dy2))
                # And append the midpoint of the integration
                self.integration_initial_states.append((-t2, -delta_time, v1, net_acc, theta1, omega, -dx1, -dy1))

            # Clamp speed after acceleration (This is only needed in case of floating point error, but is otherwise unnecessary)
            if abs(self.speed) > self.max_speed:
                self.speed = copysign(self.max_speed, self.speed)
            elif abs(self.speed) <= 1e-12:
                # Let's be nice and just make it 0.0. Because I just tripped myself up with a ship_state.speed == 0.0 comparison when testing XD
                self.speed = 0.0

            # Update the angle based on turning rate
            self.heading += self.turn_rate * delta_time

            # Keep the angle within [0, 360.0)
            self.heading %= 360.0

            # Use speed magnitude to get velocity vector
            rad_heading = radians(self.heading)
            self.vx = cos(rad_heading) * self.speed
            self.vy = sin(rad_heading) * self.speed
        else:
            # This is a negative-time update, which rolls-back a portion of the frame we last updated forward.
            # We have recorded how we did the forward integration, so we use that history to do the backward integration.
            assert self.integration_initial_states, "Cannot rollback ship state without a preceding forward update!"
            # Accumulate the pieces of the integral
            dx_sum = 0.0
            dy_sum = 0.0
            speed_sum = 0.0
            # To get the position of the ship in the past, we integrate its position backward
            # using the integration intervals we stored in the ship state when it was integrating it forward in time.
            # If the integral is split into multiple time segments, add them all up going backward in time,
            # until we hit delta_time, the end point of the integration

            # Keep in mind that the start_t and end_t are reverse chronological! So it starts in the future, and ends in the past!
            for ship_initial_state in self.integration_initial_states:
                start_t, end_t, v0, a, theta0, omega, dx, dy = ship_initial_state
                assert end_t - start_t <= 0.0
                if end_t < delta_time <= start_t:
                    # We need to include this interval since t lies in the middle of it
                    dx, dy = analytic_ship_movement_integration(v0, a, theta0, omega, delta_time - start_t)
                    dx_sum += dx
                    dy_sum += dy
                    speed_sum += a * (delta_time - start_t)  # This time diff results in a negative number
                    assert delta_time - start_t <= 0.0
                    break  # Break since no more full intervals will lie beyond this, as the integral is assumed to be from 0 to t, where t <= 0
                else:
                    # This interval is fully included within t. Add the full integral amount
                    assert delta_time <= end_t
                    dx_sum += dx
                    dy_sum += dy
                    speed_sum += a * (end_t - start_t)  # This time diff results in a negative number
                    assert end_t - start_t <= 0.0

            self.x += dx_sum
            self.y += dy_sum
            self.x %= map_size[0]
            self.y %= map_size[1]
            self.speed += speed_sum

            # Don't forget to reverse-integrate the other quantities too!
            # Clamp speed after acceleration (This is only needed in case of floating point error, but is otherwise unnecessary)
            if abs(self.speed) > self.max_speed:
                self.speed = copysign(self.max_speed, self.speed)
            elif abs(self.speed) <= 1e-12:
                # Let's be nice and just make it 0.0. Because I just tripped myself up with a ship_state.speed == 0.0 comparison when testing XD
                self.speed = 0.0

            # Update the angle based on turning rate
            self.heading += self.turn_rate * delta_time

            # Keep the angle within [0, 360.0)
            self.heading %= 360.0

            # Use speed magnitude to get velocity vector
            rad_heading = radians(self.heading)
            self.vx = cos(rad_heading) * self.speed
            self.vy = sin(rad_heading) * self.speed

            self.integration_initial_states.clear()  # Clear the state so that we don't attempt to do a second rollback which would be invalid

        # Decrement respawn timer unconditionally, and allow it to go negative
        # This helps the continuous simulation know when the respawn time wore off mid-frame
        self._respawning -= delta_time

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

        # Update the mutable state
        self.update_state()

        return new_bullet, new_mine

    def destruct(self, map_size: tuple[float, float]) -> None:
        """
        Called by the game when a ship collides with something and dies. Handles life decrementing and triggers respawn
        """
        self.lives -= 1
        spawn_position = self.position  # (map_size[0]/2, map_size[1]/2)
        spawn_heading = self.heading
        if self.lives > 0:
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

            if self.mines_remaining != -1:
                # Mines are limited
                self.mines_remaining -= 1
            self.mines_dropped += 1
            mine_x = self.x
            mine_y = self.y
            return Mine((mine_x, mine_y), owner=self)
        else:
            return None

    def fire_bullet(self, map_size: tuple[int, int]) -> Bullet | None:
        # if self.bullets_remaining != 0 and not self._fire_limiter:
        if self.can_fire:
            # Remove respawn invincibility. Trigger fire limiter
            self._respawning = 0.0
            self._fire_limiter = self._fire_time

            # Bullet counters
            if self.bullets_remaining != -1:
                # Bullets are limited
                self.bullets_remaining -= 1
            self.bullets_shot += 1

            # Return the bullet object that was fired
            rad_heading = radians(self.heading)
            # We wrap the start point of the bullet, since the ship could be peeking through a boundary
            # and the bullet should end up on the other side.
            # From here on out, the bullet does NOT get wrapped past map bounds!
            bullet_x = (self.x + self.radius * cos(rad_heading)) % map_size[0]
            bullet_y = (self.y + self.radius * sin(rad_heading)) % map_size[1]
            return Bullet((bullet_x, bullet_y), self.heading, owner=self)

        # Return nothing if we can't fire a bullet right now
        return None

    def __repr__(self) -> str:
        return (
            f"<Ship("
            f"id={self.id}, team={self.team}, team_name='{self.team_name}', "
            f"x={self.x}, y={self.y}, vx={self.vx}, vy={self.vy}, "
            f"speed={self.speed}, heading={self.heading}, "
            f"lives={self.lives}, is_respawning={self.is_respawning}, "
            f"bullets_remaining={self.bullets_remaining}, mines_remaining={self.mines_remaining}, "
            f"can_fire={self.can_fire}, can_deploy_mine={self.can_deploy_mine}, "
            f"thrust={self.thrust}, turn_rate={self.turn_rate}"
            f")>"
        )
