# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TypedDict


class AsteroidState(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    size: int
    mass: float
    radius: float


class BulletState(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    heading: float
    mass: float


class MineState(TypedDict):
    position: tuple[float, float]
    mass: float
    fuse_time: float
    remaining_time: float


class ShipState(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    speed: float
    heading: float
    mass: float
    radius: float
    id: int
    team: int
    is_respawning: bool
    lives_remaining: int
    deaths: int


class ShipOwnState(ShipState):
    bullets_remaining: int
    mines_remaining: int
    can_fire: bool
    fire_cooldown: float
    fire_rate: float
    can_deploy_mine: bool
    mine_cooldown: float
    mine_deploy_rate: float
    respawn_time_left: float
    respawn_time: float
    thrust_range: tuple[float, float]
    turn_rate_range: tuple[float, float]
    max_speed: float
    drag: float


class GameStateDict(TypedDict):
    asteroids: list[AsteroidState]
    ships: list[ShipState]
    bullets: list[BulletState]
    mines: list[MineState]
    map_size: tuple[int, int]
    time: float
    delta_time: float
    frame_rate: float
    sim_frame: int
    time_limit: float
    random_asteroid_splits: bool
