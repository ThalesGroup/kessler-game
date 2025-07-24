# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TypedDict

from .graphics import GraphicsType, KesslerGraphics


class UISettingsDict(TypedDict, total=False):
    ships: bool
    lives_remaining: bool
    accuracy: bool
    asteroids_hit: bool
    shots_fired: bool
    bullets_remaining: bool
    controller_name: bool
    scale: float


class SettingsDict(TypedDict, total=False):
    frequency: float
    perf_tracker: bool
    prints_on: bool
    graphics_type: GraphicsType
    graphics_obj: KesslerGraphics | None
    realtime_multiplier: float
    frame_skip: int
    time_limit: float
    random_ast_splits: bool
    competition_safe_mode: bool
    UI_settings: UISettingsDict | str
