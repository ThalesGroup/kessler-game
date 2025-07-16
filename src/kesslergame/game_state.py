# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TypedDict
from .mine_state import MineState
from .asteroid_state import AsteroidState
from .ship_state import ShipState
from .bullet_state import BulletState

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
