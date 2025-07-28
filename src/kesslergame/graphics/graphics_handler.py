# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .graphics_base import KesslerGraphics
    from ..scenario import Scenario
    from ..ship import Ship
    from ..asteroid import Asteroid
    from ..bullet import Bullet
    from ..mines import Mine
    from ..score import Score
    from ..settings_dicts import UISettingsDict


class GraphicsType(Enum):
    NoGraphics = 0
    UnrealEngine = 1
    Tkinter = 2
    Pyplot = 3
    Custom = 4


class GraphicsHandler:
    def __init__(self, type: GraphicsType = GraphicsType.NoGraphics, scenario: Scenario | None = None, UI_settings: UISettingsDict | None = None, graphics_obj: KesslerGraphics | None = None) -> None:
        """
        Create a graphics handler utilizing the assigned graphics engine defined from GraphicsType
        """
        self.type = type
        self.graphics: KesslerGraphics | None
        if graphics_obj is not None:
            self.graphics = graphics_obj
            if not issubclass(graphics_obj.__class__, KesslerGraphics):
                raise ValueError('Settings "graphics_obj" must be a child of type "KesslerGraphics"')
        else:
            match self.type:
                case GraphicsType.NoGraphics:
                    self.graphics = None
                case GraphicsType.UnrealEngine:
                    from .graphics_ue import GraphicsUE
                    self.graphics = GraphicsUE()
                case GraphicsType.Tkinter:
                    from .graphics_tk import GraphicsTK
                    self.graphics = GraphicsTK(UI_settings)
                case GraphicsType.Pyplot:
                    from .graphics_plt import GraphicsPLT
                    self.graphics = GraphicsPLT()
                case GraphicsType.Custom:
                    #if graphics_obj is None:
                    raise ValueError('"graphics_obj" must be defined in settings when using GraphicsType.Custom')
                    #else:
                    #    self.graphics = graphics_obj

        if self.type != GraphicsType.NoGraphics:
            assert self.graphics is not None
            assert scenario is not None
            self.graphics.start(scenario)

    def update(self, score: Score, ships: list[Ship], asteroids: list[Asteroid], bullets: list[Bullet], mines: list[Mine]) -> None:
        """
        Update the graphics draw with new simulation data each simulation time-step
        """
        if self.type != GraphicsType.NoGraphics:
            assert self.graphics is not None
            self.graphics.update(score, ships, asteroids, bullets, mines)

    def close(self) -> None:
        """
        Finalize and close the graphics window
        """
        if self.type != GraphicsType.NoGraphics:
            assert self.graphics is not None
            self.graphics.close()
