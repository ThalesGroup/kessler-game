# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TypedDict

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
