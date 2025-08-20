# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations

import time
import warnings

from math import inf, isfinite, isnan, ceil, radians, sin, cos
from typing import Any, TypedDict
from enum import Enum

from .scenario import Scenario
from .score import Score
from .controller import KesslerController
from .collisions import circle_line_collision_continuous, circle_line_collision_time_interval, ship_asteroid_continuous_collision_time, ship_ship_continuous_collision_time, time_until_exit, time_until_enter
from .graphics import GraphicsType, GraphicsHandler, KesslerGraphics
from .mines import Mine
from .asteroid import Asteroid
from .ship import Ship
from .bullet import Bullet
from .settings_dicts import SettingsDict
from .state_models import GameState, ShipState
from .collision_event import CollisionType, CollisionEvent
from .heapq_mypyc import heappush, heappop, heapify
from .validate import validate_game_settings


class StopReason(Enum):
    not_stopped = 0
    no_ships = 1
    no_asteroids = 2
    time_expired = 3
    out_of_bullets = 4


class PerfDict(TypedDict, total=False):
    controller_times: list[float]
    total_controller_time: float
    physics_update: float
    collisions_check: float
    score_update: float
    graphics_draw: float
    total_frame_time: float


class KesslerGame:
    def __init__(self, settings: SettingsDict | None = None) -> None:
        # Validate game settings
        if settings is None:
            settings = {}
        validated_settings = validate_game_settings(
            settings,
            GraphicsType=GraphicsType,
            KesslerGraphics=KesslerGraphics
        )

        # Assign validated settings
        self.frequency = validated_settings['frequency']
        if self.frequency < 5.0:
            warnings.warn("Framerates below 5 are not supported, and may cause bugs in ship movement and collision checking", RuntimeWarning)
        self.delta_time: float = 1.0 / self.frequency
        self.perf_tracker = validated_settings['perf_tracker']
        self.prints_on = validated_settings['prints_on']
        self.graphics_type = validated_settings['graphics_type']
        self.graphics_obj = validated_settings['graphics_obj']
        self.realtime_multiplier = validated_settings['realtime_multiplier']
        self.frame_skip = validated_settings['frame_skip']
        self.default_time_limit = validated_settings['time_limit'] if validated_settings['time_limit'] or validated_settings['time_limit'] == inf else inf
        self.random_ast_splits = validated_settings['random_ast_splits']
        self.competition_safe_mode = validated_settings['competition_safe_mode']
        self.UI_settings = validated_settings['UI_settings']

        self.collision_queue: list[CollisionEvent] = []

        # Persistent state lists
        self.ships: list[Ship] = []
        self.liveships: list[Ship] = []
        self.asteroids: list[Asteroid] = []
        self.bullets: list[Bullet] = []
        self.mines: list[Mine] = []

        # Current scenario
        self.scenario: Scenario

        # Score
        self.score: Score

        # Environment parameters
        self.stop_reason: StopReason
        self.sim_time: float
        self.sim_frame: int

        # Game state to pass to controllers
        self.game_state: GameState | None = None

        # Graphics
        self.graphics: GraphicsHandler

        # Performance tracker
        self.perf_dict: PerfDict

    def enqueue_bullet_asteroid_collisions(self, bullets: list[Bullet], asteroids: list[Asteroid], asteroid_past_time_clamp: float, asteroid_list_idx_offset: int = 0, already_a_heap: bool = False, bullet_idxs_to_skip: list[int] | None = None) -> None:
        # Collect all potential bullet-asteroid collisions
        # Since bullets do not wrap, we treat the bullet hitbox as being clamped at the map edge.
        # The way to calculate the collision time interval is elegant. It considers two virtual bullets,
        # the intersection of the two being the true bullet's position:
        # 1. The bullet that passes right through without getting clamped
        # 2. The bullet that is stationary, with its head right on the border, and the tail sticking into the map
        # The intersection of these two form the clamped bullet hitbox we're interested in, during the time
        # interval from when the bullet head first hits the edge, until the tail also leaves. This construction
        # is invalid before this time interval!

        # We might not be able to go back a full delta_time if the asteroid wasn't alive for that long yet!
        # So we clamp that time
        collision_past_time_clamp = min(asteroid_past_time_clamp, self.delta_time)

        # Prelookup and precompute constants used for wrapping to bullet's frame of reference
        map_width = self.scenario.map_width
        map_height = self.scenario.map_height
        half_map_width = 0.5 * map_width
        half_map_height = 0.5 * map_height

        for bul_idx, bullet in enumerate(bullets):
            if bullet_idxs_to_skip is not None and bul_idx in bullet_idxs_to_skip:
                continue

            bullet_vx = bullet.vx
            bullet_vy = bullet.vy

            # Find unclamped bullet path (as if bullet passes through the map edge)
            bullet_head_x = bullet.x
            bullet_head_y = bullet.y
            bullet_tail_x = bullet.x + bullet.tail_delta_x
            bullet_tail_y = bullet.y + bullet.tail_delta_y

            # Find when head and tail leave the visible map
            t_head_exit = time_until_exit(bullet_head_x, bullet_head_y, bullet_vx, bullet_vy, map_width, map_height)
            t_tail_exit = time_until_exit(bullet_tail_x, bullet_tail_y, bullet_vx, bullet_vy, map_width, map_height)
            assert t_head_exit <= t_tail_exit

            # Find when head and tail enter the visible map
            t_head_enter = time_until_enter(bullet_head_x, bullet_head_y, bullet_vx, bullet_vy, map_width, map_height)
            t_tail_enter = time_until_enter(bullet_tail_x, bullet_tail_y, bullet_vx, bullet_vy, map_width, map_height)
            assert t_head_enter <= t_tail_enter

            bullet_entirely_in_bounds: bool = t_head_exit >= 0.0 and t_tail_enter <= -collision_past_time_clamp

            if bullet_entirely_in_bounds:
                # This means that for the whole duration we're checking, the bullet is entirely within the map's visible bounds!
                # The tail has entered the map before the interval starts, and the head will not leave until after the interval ends.
                # This is the simplest case to handle. Do the normal collision check:
                for ast_idx, asteroid in enumerate(asteroids):
                    # Center the asteroid position relative to the bullet, accounting for wrapping of asteroids.
                    if asteroid.x - bullet.x > half_map_width:
                        ast_x_centered = asteroid.x - map_width
                    elif asteroid.x - bullet.x < -half_map_width:
                        ast_x_centered = asteroid.x + map_width
                    else:
                        ast_x_centered = asteroid.x

                    if asteroid.y - bullet.y > half_map_height:
                        ast_y_centered = asteroid.y - map_height
                    elif asteroid.y - bullet.y < -half_map_height:
                        ast_y_centered = asteroid.y + map_height
                    else:
                        ast_y_centered = asteroid.y

                    if circle_line_collision_continuous(
                        bullet_head_x, bullet_head_y,
                        bullet_tail_x, bullet_tail_y,
                        bullet_vx, bullet_vy,
                        ast_x_centered, ast_y_centered,
                        asteroid.vx, asteroid.vy,
                        asteroid.radius,
                        collision_past_time_clamp
                    ):
                        collision_start_time, _ = circle_line_collision_time_interval(
                            bullet_head_x, bullet_head_y,
                            bullet_tail_x, bullet_tail_y,
                            bullet_vx, bullet_vy,
                            ast_x_centered, ast_y_centered,
                            asteroid.vx, asteroid.vy,
                            asteroid.radius
                        )
                        if isnan(collision_start_time):
                            # This case should NEVER happen, but maybe due to some pathological numeric instability,
                            # it might be that the first function detected a barely collision, and then the second function
                            # missed it and the discriminant was -0.0000000000000001, and returns nan for collision time ¯\_(ツ)_/¯
                            # Include all relevant parameters in the warning
                            params = {
                                "bullet_head_x": bullet_head_x,
                                "bullet_head_y": bullet_head_y,
                                "bullet_tail_x": bullet_tail_x,
                                "bullet_tail_y": bullet_tail_y,
                                "bullet_vx": bullet_vx,
                                "bullet_vy": bullet_vy,
                                "ast_x_centered": ast_x_centered,
                                "ast_y_centered": ast_y_centered,
                                "asteroid_vx": asteroid.vx,
                                "asteroid_vy": asteroid.vy,
                                "asteroid_radius": asteroid.radius,
                                "collision_past_time_clamp": collision_past_time_clamp
                            }
                            warnings.warn(
                                f"Numeric instability in quadratic solver? Real bullet collision time is NaN.\n"
                                f"This should not happen. Please file a bug report with these parameters:\n{params}",
                                RuntimeWarning
                            )
                            continue
                        collision_time = max(-collision_past_time_clamp, collision_start_time)
                        assert -collision_past_time_clamp <= collision_time <= 0.0

                        # Calculate the distance between center of bullet and the asteroid at the time of collision, to use as a tiebreaker in ordering events
                        bul_x_mid_collision = 0.5 * (bullet_head_x + bullet_tail_x) + collision_time * bullet_vx
                        bul_y_mid_collision = 0.5 * (bullet_head_y + bullet_tail_y) + collision_time * bullet_vy
                        ast_x_collision = ast_x_centered + collision_time * asteroid.vx
                        ast_y_collision = ast_y_centered + collision_time * asteroid.vy
                        dx = ast_x_collision - bul_x_mid_collision
                        dy = ast_y_collision - bul_y_mid_collision
                        sq_dist = dx * dx + dy * dy

                        bul_head_x_collision = bullet_head_x + collision_time * bullet_vx
                        bul_head_y_collision = bullet_head_y + collision_time * bullet_vy
                        bul_tail_x_collision = bullet_tail_x + collision_time * bullet_vx
                        bul_tail_y_collision = bullet_tail_y + collision_time * bullet_vy
                        # Either the bullet head or tail should be inside the map bounds for this collision to be valid.
                        # This should be guaranteed, because at no point during this interval was the bullet expected to leave the map bound, and need to be clamped!
                        assert (((0.0 <= bul_head_x_collision <= map_width) and (0.0 <= bul_head_y_collision <= map_height))
                                or ((0.0 <= bul_tail_x_collision <= map_width) and (0.0 <= bul_tail_y_collision <= map_height)))

                        # It happens surprisingly frequently where an asteroid splits, and the three overlapping children asteroids get hit by a bullet.
                        # We need a tiebreaker for this situation, or else we get framerate dependent behavior
                        dot_bullet_vel_ast_vel_tiebreaker = bullet_vx * asteroid.vx + bullet_vy * asteroid.vy
                        collision_event = CollisionEvent(collision_time, sq_dist, bul_idx, ast_idx + asteroid_list_idx_offset, CollisionType.BULLET_ASTEROID, dot_bullet_vel_ast_vel_tiebreaker)
                        if already_a_heap:
                            heappush(self.collision_queue, collision_event)
                        else:
                            self.collision_queue.append(collision_event)
            else:
                # During the time interval we're checking, either the whole time or a part of the time,
                # the bullet is at least partially out of bounds and has to have its hitbox clipped at the edge.
                # To do this check, we create two virtual bullets! The first virtual bullet is just the regular bullet, but it's
                # allowed to go out of bounds.
                # The second virtual bullet is a stationary one, with the head at the map border where the bullet leaves, and the tail
                # also on the border where the bullet would first enter the map
                # If we find the collision time interval between the asteroid and these two virtual bullets, and take
                # their intersections, we'll have the true collision interval of the clamped bullet.

                # Precompute this virtual bullet as it's specific to just the bullet, and not specific to any asteroid
                # Virtual bullet 2: stationary bullet, where head and tails are pinned at the map border, along the bullet's line of travel
                # Remember that the t_clamp_start is a negative number. The bullet head at the end of the frame is already past bound.
                pinned_head_x = bullet_head_x + bullet_vx * t_head_exit
                pinned_head_y = bullet_head_y + bullet_vy * t_head_exit
                # Stick the tail of the bullet on the map border where the bullet would enter the map
                pinned_tail_x = bullet_tail_x + bullet_vx * t_tail_enter
                pinned_tail_y = bullet_tail_y + bullet_vy * t_tail_enter

                for ast_idx, asteroid in enumerate(asteroids):
                    # Center the asteroid position relative to the bullet, accounting for wrapping of asteroids.
                    if asteroid.x - bullet.x > half_map_width:
                        ast_x_centered = asteroid.x - map_width
                    elif asteroid.x - bullet.x < -half_map_width:
                        ast_x_centered = asteroid.x + map_width
                    else:
                        ast_x_centered = asteroid.x

                    if asteroid.y - bullet.y > half_map_height:
                        ast_y_centered = asteroid.y - map_height
                    elif asteroid.y - bullet.y < -half_map_height:
                        ast_y_centered = asteroid.y + map_height
                    else:
                        ast_y_centered = asteroid.y

                    # Virtual bullet 1: normal moving bullet that is unclamped as it goes beyond the border
                    hit1 = circle_line_collision_continuous(
                        bullet_head_x, bullet_head_y,
                        bullet_tail_x, bullet_tail_y,
                        bullet_vx, bullet_vy,
                        ast_x_centered, ast_y_centered,
                        asteroid.vx, asteroid.vy,
                        asteroid.radius,
                        collision_past_time_clamp
                    )
                    if not hit1:
                        continue
                    t1_start, t1_end = circle_line_collision_time_interval(
                        bullet_head_x, bullet_head_y,
                        bullet_tail_x, bullet_tail_y,
                        bullet_vx, bullet_vy,
                        ast_x_centered, ast_y_centered,
                        asteroid.vx, asteroid.vy,
                        asteroid.radius
                    )
                    if isnan(t1_start) or isnan(t1_end):
                        # This should never happen, but is here in case of numeric instability in a barely collision
                        # Include all relevant parameters in the warning
                        params = {
                            "bullet_head_x": bullet_head_x,
                            "bullet_head_y": bullet_head_y,
                            "bullet_tail_x": bullet_tail_x,
                            "bullet_tail_y": bullet_tail_y,
                            "bullet_vx": bullet_vx,
                            "bullet_vy": bullet_vy,
                            "ast_x_centered": ast_x_centered,
                            "ast_y_centered": ast_y_centered,
                            "asteroid_vx": asteroid.vx,
                            "asteroid_vy": asteroid.vy,
                            "asteroid_radius": asteroid.radius,
                            "collision_past_time_clamp": collision_past_time_clamp
                        }
                        warnings.warn(
                            f"Numeric instability in quadratic solver? VB1 collision time is NaN.\n"
                            f"This should not happen. Please file a bug report with these parameters:\n{params}",
                            RuntimeWarning
                        )
                        continue

                    # Use the virtual bullet 2 we computed for this bullet
                    hit2 = circle_line_collision_continuous(
                        pinned_head_x, pinned_head_y,
                        pinned_tail_x, pinned_tail_y,
                        0.0, 0.0,  # Stationary bullet for clamping to bound!
                        ast_x_centered, ast_y_centered,
                        asteroid.vx, asteroid.vy,
                        asteroid.radius,
                        collision_past_time_clamp
                    )
                    if not hit2:
                        continue
                    t2_start, t2_end = circle_line_collision_time_interval(
                        pinned_head_x, pinned_head_y,
                        pinned_tail_x, pinned_tail_y,
                        0.0, 0.0,
                        ast_x_centered, ast_y_centered,
                        asteroid.vx, asteroid.vy,
                        asteroid.radius
                    )
                    if isnan(t2_start) or isnan(t2_end):
                        # This should never happen, but is here in case of numeric instability in a barely collision
                        # Include all relevant parameters in the warning
                        params = {
                            "pinned_head_x": pinned_head_x,
                            "pinned_head_y": pinned_head_y,
                            "pinned_tail_x": pinned_tail_x,
                            "pinned_tail_y": pinned_tail_y,
                            "bullet_vx": 0.0,
                            "bullet_vy": 0.0,
                            "ast_x_centered": ast_x_centered,
                            "ast_y_centered": ast_y_centered,
                            "asteroid_vx": asteroid.vx,
                            "asteroid_vy": asteroid.vy,
                            "asteroid_radius": asteroid.radius,
                            "collision_past_time_clamp": collision_past_time_clamp
                        }
                        warnings.warn(
                            f"Numeric instability in quadratic solver? VB2 collision time is NaN.\n"
                            f"This should not happen. Please file a bug report with these parameters:\n{params}",
                            RuntimeWarning
                        )
                        continue

                    # Take the intersection of the intervals
                    # Use nested min/max instead of 3-arg min/max, because this is much faster for MyPyC compilation
                    # This clamps the interval time to the two collision times, the time we're interested in,
                    # and the time that the bullet is actually in the map
                    t_start = max(max(max(t1_start, t2_start), -collision_past_time_clamp), t_head_enter)
                    t_end = min(min(min(t1_end, t2_end), 0.0), t_tail_exit)

                    if t_start <= t_end:
                        # The interval actually exists and has nonnegative size
                        collision_time = t_start
                        assert -collision_past_time_clamp <= collision_time <= 0.0

                        # Calculate the distance between center of bullet and the asteroid at the time of collision, to use as a tiebreaker in ordering events
                        # This does not consider that the bullet could be clamped at the edge, and just uses the bullet passing through the border anyway.
                        bul_x_mid_collision = 0.5 * (bullet_head_x + bullet_tail_x) + collision_time * bullet_vx
                        bul_y_mid_collision = 0.5 * (bullet_head_y + bullet_tail_y) + collision_time * bullet_vy
                        ast_x_collision = ast_x_centered + collision_time * asteroid.vx
                        ast_y_collision = ast_y_centered + collision_time * asteroid.vy
                        dx = ast_x_collision - bul_x_mid_collision
                        dy = ast_y_collision - bul_y_mid_collision
                        sq_dist = dx * dx + dy * dy

                        bul_head_x_collision = bullet_head_x + collision_time * bullet_vx
                        bul_head_y_collision = bullet_head_y + collision_time * bullet_vy
                        bul_tail_x_collision = bullet_tail_x + collision_time * bullet_vx
                        bul_tail_y_collision = bullet_tail_y + collision_time * bullet_vy

                        # It happens surprisingly frequently where an asteroid splits, and the three overlapping children asteroids get hit by a bullet. We need a tiebreaker for this situation!
                        # Or else we get weird random indeterminate behavior, and there goes our framerate independence.
                        dot_bullet_vel_ast_vel_tiebreaker = bullet_vx * asteroid.vx + bullet_vy * asteroid.vy
                        collision_event = CollisionEvent(collision_time, sq_dist, bul_idx, ast_idx + asteroid_list_idx_offset, CollisionType.BULLET_ASTEROID, dot_bullet_vel_ast_vel_tiebreaker)
                        if already_a_heap:
                            heappush(self.collision_queue, collision_event)
                        else:
                            self.collision_queue.append(collision_event)

    def enqueue_ship_asteroid_collisions(self, ships: list[Ship], asteroids: list[Asteroid], asteroid_past_time_clamp: float, asteroid_list_idx_offset: int = 0, already_a_heap: bool = False) -> None:
        # Prelookup and precompute constants used for wrapping to bullet's frame of reference
        map_width = self.scenario.map_width
        map_height = self.scenario.map_height
        half_map_width = 0.5 * map_width
        half_map_height = 0.5 * map_height

        for ship_idx, ship in enumerate(ships):
            if ship.is_respawning_internal or not ship.alive:
                continue
            for ast_idx, asteroid in enumerate(asteroids):
                # Check for collisions in time interval [t - delta_time, t]
                if asteroid.x - ship.x > half_map_width:
                    ast_x_centered_around_ship = asteroid.x - map_width
                elif asteroid.x - ship.x < -half_map_width:
                    ast_x_centered_around_ship = asteroid.x + map_width
                else:
                    ast_x_centered_around_ship = asteroid.x

                if asteroid.y - ship.y > half_map_height:
                    ast_y_centered_around_ship = asteroid.y - map_height
                elif asteroid.y - ship.y < -half_map_height:
                    ast_y_centered_around_ship = asteroid.y + map_height
                else:
                    ast_y_centered_around_ship = asteroid.y
                assert ship.respawn_time_internal <= 1e-12, f"{ship.respawn_time_internal=}"
                collision_start_time = ship_asteroid_continuous_collision_time(
                    ship.x, ship.y, ship.radius, ship.speed, ship.integration_initial_states,
                    ast_x_centered_around_ship, ast_y_centered_around_ship, asteroid.vx, asteroid.vy, asteroid.radius, asteroid.speed,
                    max(-min(asteroid_past_time_clamp, self.delta_time), min(0.0, ship.respawn_time_internal)), 0.0  # Only check collisions starting from when the ship's respawn invincibility wore off
                )
                if not isnan(collision_start_time):
                    assert -self.delta_time <= collision_start_time <= 0.0  # Collision happened within past frame
                    # As a tiebreaker, we need to get the positions of the objects during the collision, which is at offset collision_start_time
                    # This is VERY IMPORTANT because if a ship was respawning and suddenly it wears off while the ship is inside multiple asteroids,
                    # the tiebreaker will be used, and the ship will collide with whatever is closer. Otherwise, framerate-dependent behavior will leak in,
                    # and asteroid order will then decide how it ends up in the queue and subsequently gets resolved.
                    ship_past_x, ship_past_y = ship.get_past_position(collision_start_time, self.scenario.map_size)
                    dx = abs((asteroid.x + asteroid.vx * collision_start_time) - ship_past_x)
                    dy = abs((asteroid.y + asteroid.vy * collision_start_time) - ship_past_y)
                    if dx > half_map_width:
                        dx = map_width - dx
                    if dy > half_map_height:
                        dy = map_height - dy
                    sq_dist = dx * dx + dy * dy

                    # Break ties in case everything else matches, including asteroid distance from the ship
                    ship_heading_collision = radians(ship.heading + ship.turn_rate * collision_start_time)
                    dot_product_tiebreaker_ship_ast = cos(ship_heading_collision) * asteroid.vx + sin(ship_heading_collision) * asteroid.vy
                    collision_event = CollisionEvent(collision_start_time, sq_dist, ship_idx, ast_idx + asteroid_list_idx_offset, CollisionType.SHIP_ASTEROID, dot_product_tiebreaker_ship_ast)
                    if already_a_heap:
                        heappush(self.collision_queue, collision_event)
                    else:
                        self.collision_queue.append(collision_event)

    def enqueue_ship_ship_collisions(self, ships: list[Ship]) -> None:
        # Prelookup and precompute constants used for wrapping to bullet's frame of reference
        map_width = self.scenario.map_width
        map_height = self.scenario.map_height
        half_map_width = 0.5 * map_width
        half_map_height = 0.5 * map_height

        num_ships = len(ships)
        for ship1_idx, ship1 in enumerate(ships):
            if ship1.alive and not ship1.is_respawning_internal:
                for ship2_idx in range(ship1_idx + 1, num_ships):
                    ship2 = ships[ship2_idx]
                    if ship2.alive and not ship2.is_respawning_internal:
                        # Check for collisions in time interval [t - delta_time, t]
                        # But clamp the start time to when both ships are out of respawn
                        if ship2.x - ship1.x > half_map_width:
                            ship2_x_centered_around_ship1 = ship2.x - map_width
                        elif ship2.x - ship1.x < -half_map_width:
                            ship2_x_centered_around_ship1 = ship2.x + map_width
                        else:
                            ship2_x_centered_around_ship1 = ship2.x

                        if ship2.y - ship1.y > half_map_height:
                            ship2_y_centered_around_ship1 = ship2.y - map_height
                        elif ship2.y - ship1.y < -half_map_height:
                            ship2_y_centered_around_ship1 = ship2.y + map_height
                        else:
                            ship2_y_centered_around_ship1 = ship2.y

                        collision_check_interval_start = max(-self.delta_time, min(0.0, max(ship1.respawn_time_internal, ship2.respawn_time_internal)))
                        collision_start_time = ship_ship_continuous_collision_time(
                            ship1.x, ship1.y, ship1.radius, ship1.speed, ship1.integration_initial_states,
                            ship2_x_centered_around_ship1, ship2_y_centered_around_ship1, ship2.radius, ship2.speed, ship2.integration_initial_states,
                            collision_check_interval_start, 0.0  # Clamp to when ships are out of respawn. Double max/min calls is MUCH faster than calling max/min with 3-4 args, in MyPyC compiled code!
                        )
                        if not isnan(collision_start_time):
                            assert -self.delta_time <= collision_start_time <= 0.0  # Collision happened within past frame
                            ship1_past_x, ship1_past_y = ship1.get_past_position(collision_start_time, self.scenario.map_size)
                            ship2_past_x, ship2_past_y = ship2.get_past_position(collision_start_time, self.scenario.map_size)
                            dx = abs(ship1_past_x - ship2_past_x)
                            dy = abs(ship1_past_y - ship2_past_y)
                            if dx > half_map_width:
                                dx = map_width - dx
                            if dy > half_map_height:
                                dy = map_height - dy
                            sq_dist = dx * dx + dy * dy

                            # This following test is to make sure that the ships end up in a definitely colliding state, and
                            # is good for ensuring framerate independence. So that at other framerates, the ships don't end up not actually colliding
                            # The root finder is meant to find the time that the ships begin colliding, but due to imprecision, it might find the time right before they start colliding.
                            radii_sum = ship1.radius + ship2.radius
                            radii_sum_sq = radii_sum * radii_sum
                            verified_collision: bool = True
                            if not (sq_dist + 1e-10 <= radii_sum_sq):
                                verified_collision = False
                                # Ships aren't colliding. Nudge the time forward and hope that makes them collide.
                                # Add an eps to REALLY make sure the ships are colliding!
                                # But we only want to do this if the root was found in the middle of the interval when the function
                                # dips down. If the interval start is negative, then we do NOT nudge this forward, or else wacky stuff
                                # will happen, and we get edge cases where the ship on the edge of respawn will have framerate dependence due
                                # to floating point error. Especially in mine-ship collisions which happen on integer seconds.
                                nudgification_factor = 1e-12
                                for i in range(64):
                                    # Instead of using a while loop, it's better to use a for loop and have an upper bound on this,
                                    # just so we don't infinite loop here in some super weird case
                                    collision_start_time += nudgification_factor
                                    if collision_start_time > 0.0:
                                        # We reached the end of the interval, so this is hopeless. These ships are not colliding!
                                        break

                                    ship1_past_x, ship1_past_y = ship1.get_past_position(collision_start_time, self.scenario.map_size)
                                    ship2_past_x, ship2_past_y = ship2.get_past_position(collision_start_time, self.scenario.map_size)
                                    dx = abs(ship1_past_x - ship2_past_x)
                                    dy = abs(ship1_past_y - ship2_past_y)
                                    if dx > half_map_width:
                                        dx = map_width - dx
                                    if dy > half_map_height:
                                        dy = map_height - dy
                                    sq_dist = dx * dx + dy * dy
                                    if sq_dist + 1e-10 <= radii_sum_sq:
                                        verified_collision = True
                                        break
                                    nudgification_factor *= 2.0  # Exponentially increase the nudge

                            if verified_collision:
                                collision_event = CollisionEvent(collision_start_time, sq_dist, ship1_idx, ship2_idx, CollisionType.SHIP_SHIP)
                                self.collision_queue.append(collision_event)

    def enqueue_mine_asteroid_collisions(self, mines: list[Mine], asteroids: list[Asteroid], asteroid_past_time_clamp: float, asteroid_list_idx_offset: int = 0, already_a_heap: bool = False) -> None:
        # Prelookup and precompute constants used for wrapping to bullet's frame of reference
        map_width = self.scenario.map_width
        map_height = self.scenario.map_height
        half_map_width = 0.5 * map_width
        half_map_height = 0.5 * map_height

        for mine_idx, mine in enumerate(mines):
            if mine.detonating:
                if mine.countdown_timer < -asteroid_past_time_clamp + CollisionEvent.TOLERANCE:
                    # The mine blows up earlier than we're allowed to check for it
                    continue
                for ast_idx, asteroid in enumerate(asteroids):
                    if abs(mine.countdown_timer) <= 1e-12:
                        # The mine is exploding on a frame boundary, so no need to rewind anything
                        ax = asteroid.x
                        ay = asteroid.y
                        collision_time = 0.0
                    else:
                        # Rewind objects
                        ax = asteroid.x + mine.countdown_timer * asteroid.vx
                        ay = asteroid.y + mine.countdown_timer * asteroid.vy
                        collision_time = min(0.0, mine.countdown_timer)  # This min clamp should be unnecessary, but just in case
                    dx = abs(ax - mine.x)
                    dy = abs(ay - mine.y)
                    if dx > half_map_width:
                        dx = map_width - dx
                    if dy > half_map_height:
                        dy = map_height - dy

                    radius_sum = mine.blast_radius + asteroid.radius
                    sq_dist = dx * dx + dy * dy
                    if sq_dist <= radius_sum * radius_sum:
                        collision_event = CollisionEvent(collision_time, sq_dist, mine_idx, ast_idx + asteroid_list_idx_offset, CollisionType.MINE_ASTEROID)
                        if already_a_heap:
                            heappush(self.collision_queue, collision_event)
                        else:
                            self.collision_queue.append(collision_event)

    def enqueue_mine_ship_collisions(self, mines: list[Mine], ships: list[Ship]) -> None:
        # Prelookup and precompute constants used for wrapping to bullet's frame of reference
        map_width = self.scenario.map_width
        map_height = self.scenario.map_height
        half_map_width = 0.5 * map_width
        half_map_height = 0.5 * map_height

        for mine_idx, mine in enumerate(mines):
            if mine.detonating:
                # For each live, non-respawning ship, apply damage only from the closest mine within range
                for ship_idx, ship in enumerate(ships):
                    if ship.is_respawning_internal or not ship.alive:
                        continue
                    if ship.respawn_time_internal + CollisionEvent.TOLERANCE >= mine.countdown_timer:
                        # The mine blew up before the ship got out of respawn invincibility
                        continue
                    if abs(mine.countdown_timer) <= 1e-12:
                        # The mine is exploding on a frame boundary, so no need to rewind anything
                        sx = ship.x
                        sy = ship.y
                        collision_time = 0.0
                    else:
                        # Rewind objects
                        sx, sy = ship.get_past_position(mine.countdown_timer, self.scenario.map_size)
                        collision_time = min(0.0, mine.countdown_timer)  # This min should be unnecessary, but just in case
                    dx = abs(sx - mine.x)
                    dy = abs(sy - mine.y)
                    if dx > half_map_width:
                        dx = map_width - dx
                    if dy > half_map_height:
                        dy = map_height - dy

                    radius_sum = mine.blast_radius + ship.radius
                    sq_dist = dx * dx + dy * dy
                    if sq_dist <= radius_sum * radius_sum:
                        collision_event = CollisionEvent(collision_time, sq_dist, mine_idx, ship_idx, CollisionType.MINE_SHIP)
                        self.collision_queue.append(collision_event)

    def run(self, scenario: Scenario, controllers: list[KesslerController]) -> tuple[Score, PerfDict]:
        """
        Run an entire scenario from start to finish and return score and stop reason
        """
        ##################
        # INITIALIZATION #
        ##################
        # Initialize objects lists from scenario
        self.scenario = scenario
        self.asteroids = self.scenario.asteroids()
        self.ships = self.scenario.ships()  # Keep full list of ships (dead or alive) for score reporting
        self.liveships = list(self.ships)  # Maintain a copied parallel list of just live ships
        self.bullets = []
        self.mines = []

        # Initialize Scoring class
        self.score = Score(self.scenario)

        # Initialize environment parameters
        self.stop_reason = StopReason.not_stopped
        self.sim_time = 0.0
        self.sim_frame = 0

        # Overwrite time limit from game settings if the scenario defines its own time limit
        if self.scenario.time_limit is not None:
            self.time_limit = self.scenario.time_limit
        else:
            self.time_limit = self.default_time_limit
        # Now that the game has decided the time limit, write back this time limit into the scenario
        # so that the graphics can display the correct time limit
        self.scenario.time_limit = self.time_limit

        # Assign controllers to each ship
        assert len(controllers) >= len(self.ships), f"There are not enough controllers ({len(controllers)}) to assign to the {len(self.ships)} ships!"
        for controller, ship in zip(controllers, self.ships):
            controller.ship_id = ship.id
            ship.controller = controller
            if hasattr(controller, "custom_sprite_path"):
                ship.custom_sprite_path = controller.custom_sprite_path

        # Initialize graphics display
        self.graphics = GraphicsHandler(type=self.graphics_type, scenario=self.scenario, UI_settings=self.UI_settings, graphics_obj=self.graphics_obj)

        # Initialize dictionary for performance tracking
        self.perf_dict = {
            'controller_times': [0.0] * len(self.ships),
            'total_controller_time': 0.0,
            'physics_update': 0.0,
            'collisions_check': 0.0,
            'score_update': 0.0,
            'graphics_draw': 0.0,
            'total_frame_time': 0.0
        }

        ships_to_cull: list[int] = []
        asteroids_to_cull: list[int] = []
        bullets_to_cull: list[int] = []
        mines_to_cull: list[int] = []
        new_asteroids: list[Asteroid] = []
        self.collision_queue.clear()

        # Maintain game_state dict to send to teams
        if not self.competition_safe_mode:
            self.game_state = GameState(
                # Game entities
                ships=[ship.state for ship in self.liveships],
                asteroids=[asteroid.state for asteroid in self.asteroids],
                bullets=[bullet.state for bullet in self.bullets],
                mines=[mine.state for mine in self.mines],
                # Environment
                map_size=self.scenario.map_size,
                time_limit=self.time_limit,
                # Simulation timing
                time=self.sim_time,
                frame=self.sim_frame,
                delta_time=self.delta_time,
                frame_rate=self.frequency,
                # Game settings
                random_asteroid_splits=self.random_ast_splits,
                competition_safe_mode=self.competition_safe_mode
            )

        ######################
        # MAIN SCENARIO LOOP #
        ######################

        while self.stop_reason == StopReason.not_stopped:
            # Get perf time at the start of time step evaluation and initialize performance tracker
            step_start = time.perf_counter()

            # --- CALL CONTROLLER FOR EACH SHIP ------------------------------------------------------------------------

            # Initialize controller time recording in performance tracker
            if self.perf_tracker:
                t_start = time.perf_counter()

            # Loop through each controller/ship combo and apply their actions
            for ship_idx, ship in enumerate(self.ships):
                if not ship.alive:
                    continue

                ship.update_state()  # The ship's state might have changed between the last update call and now, if it got hit
                if controllers[ship_idx].ship_id != ship.id:
                    raise RuntimeError("Controller and ship ID do not match")

                # Generate game_state info to send to controller
                ship_state_to_controller: ShipState
                game_state_to_controller: GameState
                if self.competition_safe_mode:
                    ship_state_to_controller = ShipState(ship.ownstate.copy())
                    # Must recreate GameState object, so competitors do not accidentally or maliciously modify the true game state
                    game_state_to_controller = GameState(
                        # Game entities
                        ships=[ship.state.copy() for ship in self.liveships],
                        asteroids=[asteroid.state.copy() for asteroid in self.asteroids],
                        bullets=[bullet.state.copy() for bullet in self.bullets],
                        mines=[mine.state.copy() for mine in self.mines],
                        # Environment
                        map_size=self.scenario.map_size,
                        time_limit=self.time_limit,
                        # Simulation timing
                        time=self.sim_time,
                        frame=self.sim_frame,
                        delta_time=self.delta_time,
                        frame_rate=self.frequency,
                        # Game settings
                        random_asteroid_splits=self.random_ast_splits,
                        competition_safe_mode=self.competition_safe_mode
                    )
                else:
                    ship_state_to_controller = ShipState(ship.ownstate)
                    assert self.game_state is not None
                    game_state_to_controller = self.game_state

                # Default null action
                thrust, turn_rate, fire, drop_mine = 0.0, 0.0, False, False

                try:
                    # Attempt to get and validate controller actions
                    proposed = controllers[ship_idx].actions(ship_state_to_controller, game_state_to_controller)

                    if not isinstance(proposed, (list, tuple)) or len(proposed) != 4:
                        raise ValueError(f"Controller {ship_idx} returned invalid action tuple: {proposed!r}")

                    raw_thrust, raw_turn_rate, raw_fire, raw_drop_mine = proposed

                    if not isinstance(raw_thrust, (int, float)) or not isfinite(float(raw_thrust)):
                        raise ValueError(f"Controller {ship_idx} thrust invalid: {raw_thrust!r}")
                    if not isinstance(raw_turn_rate, (int, float)) or not isfinite(float(raw_turn_rate)):
                        raise ValueError(f"Controller {ship_idx} turn_rate invalid: {raw_turn_rate!r}")
                    if not isinstance(raw_fire, bool):
                        raise TypeError(f"Controller {ship_idx} fire is not bool: {raw_fire!r}")
                    if not isinstance(raw_drop_mine, bool):
                        raise TypeError(f"Controller {ship_idx} drop_mine is not bool: {raw_drop_mine!r}")

                    # Only update if all checks passed
                    thrust = float(raw_thrust)  # Upcast potential ints to float
                    turn_rate = float(raw_turn_rate)  # Upcast potential ints to float
                    fire = raw_fire
                    drop_mine = raw_drop_mine
                except Exception as e:
                    if not self.competition_safe_mode:
                        raise  # In dev mode, fail loudly
                    # Log the error
                    print(f"[Competition Safe Mode] Controller {ship_idx} error: {e!r}. Assigning null actions for frame {self.sim_frame}.")

                ship.thrust = thrust
                ship.turn_rate = turn_rate
                ship.fire = fire
                ship.drop_mine = drop_mine

                # Update controller evaluation time if performance tracking
                if self.perf_tracker:
                    controller_time = time.perf_counter() - t_start if ship.alive else 0.00
                    self.perf_dict['controller_times'][ship_idx] += controller_time
                    t_start = time.perf_counter()

            if self.perf_tracker:
                self.perf_dict['total_controller_time'] += time.perf_counter() - step_start
                prev = time.perf_counter()

            # --- UPDATE TIME TO THE TIME AT THE END OF THIS FRAME -----------------------------------------------------
            self.sim_frame += 1
            self.sim_time = self.sim_frame / self.frequency  # Derive time from integer frames, to avoid accumulated floating point errors
            if not self.competition_safe_mode:
                assert self.game_state is not None
                self.game_state.time = self.sim_time
                self.game_state.frame = self.sim_frame

            # --- UPDATE STATE INFORMATION OF EACH OBJECT --------------------------------------------------------------

            # Update each Asteroid, Bullet, and Ship
            # Because the game_state stores a mutable reference to the internal states of the ship/asteroid/bullet/mine,
            # these updates automatically reflect in the game_state
            for ship in self.liveships:
                # The ships shoot at the start of the frame
                # These projectiles will get updated from the start of the frame to the end
                new_bullet, new_mine = ship.update(self.delta_time, self.scenario.map_size, True)
                if new_bullet is not None:
                    self.bullets.append(new_bullet)
                    if not self.competition_safe_mode:
                        assert self.game_state is not None
                        self.game_state.add_bullet(new_bullet.state)
                if new_mine is not None:
                    self.mines.append(new_mine)
                    if not self.competition_safe_mode:
                        assert self.game_state is not None
                        self.game_state.add_mine(new_mine.state)
            for asteroid in self.asteroids:
                asteroid.update(self.delta_time, self.scenario.map_size)
            for bullet in self.bullets:
                bullet.update(self.delta_time)
            for mine in self.mines:
                mine.update(self.delta_time)

            # Update performance tracker
            if self.perf_tracker:
                self.perf_dict['physics_update'] += time.perf_counter() - prev
                prev = time.perf_counter()

            # --- CHECK FOR COLLISIONS AND ENQUEUE ---

            assert not self.collision_queue  # Since the collision queue should be empty from the last frame
            self.enqueue_bullet_asteroid_collisions(self.bullets, self.asteroids, self.delta_time)
            self.enqueue_ship_asteroid_collisions(self.ships, self.asteroids, self.delta_time)
            self.enqueue_ship_ship_collisions(self.ships)

            # Check whether mines are detonating
            mines_to_cull.clear()
            mines_detonating: bool = False
            for mine_idx, mine in enumerate(self.mines):
                if mine.detonating:
                    mines_detonating = True
                    mines_to_cull.append(mine_idx)
                    mine.destruct()  # The mine destruct method currently does nothing
            if mines_detonating:
                self.enqueue_mine_asteroid_collisions(self.mines, self.asteroids, self.delta_time)
                self.enqueue_mine_ship_collisions(self.mines, self.ships)

            # Create priority queue in O(n). This is faster than doing heappush for each event, which would be O(nlogn) overall
            heapify(self.collision_queue)

            # --- RESOLVE COLLISIONS IN THE QUEUE UNTIL IT IS EMPTY ---

            # So earlier we advanced everything to the next frame, but then found when collisions happen.
            # This loop goes through the collision events one-by-one, rewinds both involved objects for each event,
            # and handles them. If new children asteroids get created, we advance those children to the end of the frame
            # and check for collisions, handling them recursively.
            # This way, all chain-reaction collisions get handled, and no events are missed.
            ships_to_cull.clear()
            asteroids_to_cull.clear()
            bullets_to_cull.clear()
            last_time_offset: float = -self.delta_time
            while self.collision_queue:
                event = heappop(self.collision_queue)
                dt = event.time_offset
                assert -self.delta_time <= dt <= 0.0  # All events must happen within the previous frame
                assert dt + CollisionEvent.TOLERANCE >= last_time_offset, f"The collision events are not monotonic! Last offset={last_time_offset}, current offset={dt}"
                last_time_offset = dt
                match event.collision_type:
                    case CollisionType.BULLET_ASTEROID:
                        # Rewind the bullet and asteroid to the time of collision, and handle it.
                        # Check new asteroid splits for collisions and add to the queue
                        bul_idx = event.object_a_idx
                        ast_idx = event.object_b_idx

                        if bul_idx in bullets_to_cull or ast_idx in asteroids_to_cull:
                            continue

                        bullet = self.bullets[bul_idx]
                        asteroid = self.asteroids[ast_idx]

                        # Rewind
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            bullet.update(dt)
                            asteroid.update(dt, self.scenario.map_size)

                        # Handle collision
                        bullets_to_cull.append(bul_idx)
                        asteroids_to_cull.append(ast_idx)

                        new_asteroids = asteroid.destruct(impactor=bullet, map_size=self.scenario.map_size, random_ast_split=self.random_ast_splits)
                        bullet.destruct()
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            for a in new_asteroids:
                                # This is a forward update, from the time of collision to the end of the frame!
                                a.update(-dt, self.scenario.map_size)
                        ast_idx_offset = len(self.asteroids)
                        self.asteroids.extend(new_asteroids)
                        if not self.competition_safe_mode:
                            assert self.game_state is not None
                            self.game_state.add_asteroids([a.state for a in new_asteroids])
                        # Take care of possible collision events from these children asteroids this frame
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            # Only do this if we have time left, and the collision didn't happen at the very end of the frame
                            self.enqueue_bullet_asteroid_collisions(self.bullets, new_asteroids, -dt, ast_idx_offset, True, bullets_to_cull)
                            self.enqueue_mine_asteroid_collisions(self.mines, new_asteroids, -dt, ast_idx_offset, True)
                            self.enqueue_ship_asteroid_collisions(self.ships, new_asteroids, -dt, ast_idx_offset, True)

                        # Track stats
                        bullet.owner.bullet_asteroid_hits += 1
                    case CollisionType.SHIP_ASTEROID:
                        ship_idx = event.object_a_idx
                        ast_idx = event.object_b_idx

                        if ship_idx in ships_to_cull or ast_idx in asteroids_to_cull:
                            continue

                        ship = self.ships[ship_idx]

                        assert ship.alive
                        if ship.is_respawning_internal:
                            # The ship is alive, but it's currently in respawn invulnerability, so skip
                            continue
                        asteroid = self.asteroids[ast_idx]

                        # Rewind
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            ship.update(dt, self.scenario.map_size, False)
                            asteroid.update(dt, self.scenario.map_size)

                        # Handle collision
                        new_asteroids = asteroid.destruct(impactor=ship, map_size=self.scenario.map_size, random_ast_split=self.random_ast_splits)
                        ship.destruct(map_size=self.scenario.map_size)

                        if abs(dt) > CollisionEvent.TOLERANCE:
                            for a in new_asteroids:
                                # This is a forward update, from the time of collision to the end of the frame!
                                a.update(-dt, self.scenario.map_size)
                        ast_idx_offset = len(self.asteroids)
                        self.asteroids.extend(new_asteroids)
                        if not self.competition_safe_mode:
                            assert self.game_state is not None
                            self.game_state.add_asteroids([a.state for a in new_asteroids])
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            self.enqueue_bullet_asteroid_collisions(self.bullets, new_asteroids, -dt, ast_idx_offset, True, bullets_to_cull)
                            self.enqueue_mine_asteroid_collisions(self.mines, new_asteroids, -dt, ast_idx_offset, True)
                            self.enqueue_ship_asteroid_collisions(self.ships, new_asteroids, -dt, ast_idx_offset, True)

                        if ship.alive:
                            if abs(dt) > CollisionEvent.TOLERANCE:
                                ship.update(-dt, self.scenario.map_size, False)
                        else:
                            ships_to_cull.append(ship_idx)
                        asteroids_to_cull.append(ast_idx)

                        # Track stats
                        ship.ship_asteroid_hits += 1
                        ship.asteroid_deaths += 1
                    case CollisionType.SHIP_SHIP:
                        ship1_idx = event.object_a_idx
                        ship2_idx = event.object_b_idx

                        if ship1_idx in ships_to_cull or ship2_idx in ships_to_cull:
                            continue

                        ship1 = self.ships[ship1_idx]
                        ship2 = self.ships[ship2_idx]

                        assert ship1.alive and ship2.alive
                        if ship1.is_respawning_internal or ship2.is_respawning_internal:
                            # The ship is alive, but it's currently in respawn invulnerability, so skip
                            continue

                        # Rollback
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            ship1.update(dt, self.scenario.map_size, False)
                            ship2.update(dt, self.scenario.map_size, False)

                        # Handle collision
                        ship1.destruct(map_size=self.scenario.map_size)
                        ship2.destruct(map_size=self.scenario.map_size)

                        # Roll forward to the end of the frame again if alive
                        if ship1.alive:
                            if abs(dt) > CollisionEvent.TOLERANCE:
                                ship1.update(-dt, self.scenario.map_size, False)
                        else:
                            ships_to_cull.append(ship1_idx)
                        if ship2.alive:
                            if abs(dt) > CollisionEvent.TOLERANCE:
                                ship2.update(-dt, self.scenario.map_size, False)
                        else:
                            ships_to_cull.append(ship2_idx)

                        # Track stats
                        ship1.ship_ship_hits += 1
                        ship2.ship_ship_hits += 1
                        ship1.ship_deaths += 1
                        ship2.ship_deaths += 1
                    case CollisionType.MINE_ASTEROID:
                        mine_idx = event.object_a_idx
                        ast_idx = event.object_b_idx

                        if ast_idx in asteroids_to_cull:
                            continue

                        mine = self.mines[mine_idx]
                        asteroid = self.asteroids[ast_idx]

                        # Rewind if necessary
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            mine.update(dt)
                            asteroid.update(dt, self.scenario.map_size)

                        # Handle collision
                        new_asteroids = asteroid.destruct(impactor=mine, map_size=self.scenario.map_size, random_ast_split=self.random_ast_splits)
                        asteroids_to_cull.append(ast_idx)

                        # Move the things back to the present
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            mine.update(-dt)
                            for a in new_asteroids:
                                # This is a forward update, from the time of collision to the end of the frame!
                                a.update(-dt, self.scenario.map_size)

                        ast_idx_offset = len(self.asteroids)
                        self.asteroids.extend(new_asteroids)
                        if not self.competition_safe_mode:
                            assert self.game_state is not None
                            self.game_state.add_asteroids([a.state for a in new_asteroids])
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            # Enqueue new collisions, but be super careful not to allow this same mine to hit the asteroids' children again!
                            # But the mine collision check should be avoiding this case where the time interval is the explosion time. So it should be fine.
                            self.enqueue_bullet_asteroid_collisions(self.bullets, new_asteroids, -dt, ast_idx_offset, True, bullets_to_cull)
                            self.enqueue_mine_asteroid_collisions(self.mines, new_asteroids, -dt, ast_idx_offset, True)
                            self.enqueue_ship_asteroid_collisions(self.ships, new_asteroids, -dt, ast_idx_offset, True)

                        # Track stats
                        mine.owner.mine_asteroid_hits += 1
                    case CollisionType.MINE_SHIP:
                        mine_idx = event.object_a_idx
                        ship_idx = event.object_b_idx

                        if ship_idx in ships_to_cull:
                            continue

                        mine = self.mines[mine_idx]
                        ship = self.ships[ship_idx]

                        assert ship.alive
                        if ship.is_respawning_internal:
                            # The ship is alive, but it's currently in respawn invulnerability, so skip
                            continue

                        # Rewind if necessary
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            mine.update(dt)
                            ship.update(dt, self.scenario.map_size, False)

                        # Handle collision
                        mine.destruct()
                        ship.destruct(map_size=self.scenario.map_size)

                        if not ship.alive:
                            ships_to_cull.append(ship_idx)

                        # Rewind if necessary
                        if abs(dt) > CollisionEvent.TOLERANCE:
                            mine.update(-dt)
                            ship.update(-dt, self.scenario.map_size, False)

                        # Track stats
                        mine.owner.mine_ship_hits += 1
                        ship.mine_deaths += 1

            # Now that all collisions are handled and resolved, the final step is to cull the removed objects
            # Cull asteroids using swap and pop, in reverse index order. The list of indices to cull is unique
            for ast_idx in sorted(asteroids_to_cull, reverse=True):
                self.asteroids[ast_idx] = self.asteroids[-1]
                self.asteroids.pop()
                if not self.competition_safe_mode:
                    assert self.game_state is not None
                    self.game_state.remove_asteroid(ast_idx)

            # Cull bullets that are off the map
            # It is tempting, but insufficient to cull a bullet if just both the head and tail are out of bounds.
            # Because in the case of if the tail and head were out of bounds, but the middle of the bullet was still inbounds in the corner of a map.
            # This is something that is geometrically plausible especially at higher framerates, and the ship is peeking its head into the map when shooting a bullet!
            for bul_idx, bullet in enumerate(self.bullets):
                if bul_idx in bullets_to_cull:
                    continue
                time_for_tail_to_leave = time_until_exit(bullet.x + bullet.tail_delta_x, bullet.y + bullet.tail_delta_y, bullet.vx, bullet.vy, self.scenario.map_width, self.scenario.map_height)
                if time_for_tail_to_leave <= 0.0:
                    # The bullet has left the map already
                    bullet.destruct()
                    bullets_to_cull.append(bul_idx)

            # Cull bullets using swap and pop, in reverse index order
            for bul_idx in sorted(bullets_to_cull, reverse=True):
                self.bullets[bul_idx] = self.bullets[-1]
                self.bullets.pop()
                if not self.competition_safe_mode:
                    assert self.game_state is not None
                    self.game_state.remove_bullet(bul_idx)

            if mines_detonating:
                # Must swap and pop with indices sorted in descending order
                # No need to sort, since they were collected in ascending order. Just reverse iterate.
                for mine_idx in reversed(mines_to_cull):
                    self.mines[mine_idx] = self.mines[-1]
                    self.mines.pop()
                    if not self.competition_safe_mode:
                        assert self.game_state is not None
                        self.game_state.remove_mine(mine_idx)

            # Cull ships if they are all out of lives
            if ships_to_cull:
                new_liveships = [ship for ship in self.liveships if ship.alive]
                self.liveships = new_liveships
                if not self.competition_safe_mode:
                    assert self.game_state is not None
                    self.game_state.update_ships([ship.state for ship in new_liveships])

            # Update performance tracker with collisions timing
            if self.perf_tracker:
                self.perf_dict['collisions_check'] += time.perf_counter() - prev
                prev = time.perf_counter()

                # --- UPDATE SCORE CLASS -----------------------------------------------------------------------------------
                self.score.update(self.ships, self.bullets, self.sim_time, self.perf_dict['controller_times'])

                # Update performance tracker with score timing
                self.perf_dict['score_update'] += time.perf_counter() - prev
                prev = time.perf_counter()
            else:
                self.score.update(self.ships, self.bullets, self.sim_time)

            # --- UPDATE GRAPHICS --------------------------------------------------------------------------------------
            if self.sim_frame % self.frame_skip == 0:
                self.graphics.update(self.score, self.ships, self.asteroids, self.bullets, self.mines)

                # Update performance tracker with graphics timing
                if self.perf_tracker:
                    self.perf_dict['graphics_draw'] += time.perf_counter() - prev
                    prev = time.perf_counter()

            # --- CHECK STOP CONDITIONS --------------------------------------------------------------------------------
            if self.scenario.stop_if_no_asteroids and not self.asteroids:
                # No asteroids remain
                self.stop_reason = StopReason.no_asteroids
            elif self.scenario.stop_if_no_ships and not self.liveships and not (self.mines or self.bullets):
                # No ships are alive and no mines exist and no bullets exist
                # Prevents unfairness where ship that dies before another gets score from its bullets as long as the other
                # is alive but the one that lives longer doesn't get the same benefit from its bullets/mines persisting
                # after it dies
                self.stop_reason = StopReason.no_ships
            elif (
                self.scenario.stop_if_no_ammo
                and all(ship.bullets_remaining == 0 and ship.mines_remaining == 0 for ship in self.liveships)
                and not (self.bullets or self.mines)
            ):
                # All live ships are out of bullets and no bullets/mines are on map
                self.stop_reason = StopReason.out_of_bullets
            elif isfinite(self.time_limit) and self.sim_frame >= ceil(self.time_limit * self.frequency):
                # Out of time
                self.stop_reason = StopReason.time_expired

            # --- FINISHING TIME STEP ----------------------------------------------------------------------------------
            # Get overall time step compute time
            if self.perf_tracker:
                self.perf_dict['total_frame_time'] += time.perf_counter() - step_start

            # Hold simulation so that it runs at realtime ratio if specified, else let it pass
            if self.realtime_multiplier != 0.0:
                target = step_start + self.delta_time / self.realtime_multiplier
                now = time.perf_counter()
                # Sleep for most of the wait. Subtract a small fudge factor to avoid oversleeping
                while now < target - 0.001:  # 1ms tolerance
                    time.sleep(0.0005)  # sleep 0.5ms
                    now = time.perf_counter()
                # Busy-wait for the remaining tiny interval, if any
                while now < target:
                    now = time.perf_counter()

        ############################################
        # Finalization after scenario has been run #
        ############################################

        # Close graphics display
        self.graphics.close()

        # Finalize score class before returning
        self.score.finalize(self.sim_time, self.stop_reason, self.ships)

        # Return the score and stop condition
        return self.score, self.perf_dict


class TrainerEnvironment(KesslerGame):
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        """
        Instantiates a KesslerGame object with settings to optimize training time
        """
        if settings is None:
            settings = {}
        trainer_settings: SettingsDict = {
            'frequency': settings.get("frequency", 30.0),
            'perf_tracker': settings.get("perf_tracker", False),
            'prints_on': settings.get("prints_on", False),
            'graphics_type': GraphicsType.NoGraphics,
            'realtime_multiplier': 0.0,
            'competition_safe_mode': False,  # This is faster. But must be careful to not mutate the game state given to the controller if this is used!
            'time_limit': settings.get("time_limit", inf)
        }
        super().__init__(trainer_settings)
