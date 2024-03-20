# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from enum import Enum
from typing import Optional, Dict, List
from .graphics_base import KesslerGraphics
from ..scenario import Scenario
from ..ship import Ship
from ..asteroid import Asteroid
from ..bullet import Bullet
from ..mines import Mine
from ..score import Score

class GraphicsType(Enum):
    NoGraphics = 0
    UnrealEngine = 1
    Tkinter = 2
    Pyplot = 3
    Custom = 4


class GraphicsHandler:
    def __init__(self, type: GraphicsType = GraphicsType.NoGraphics, scenario: Optional[Scenario] = None, UI_settings: Optional[Dict[str, bool]] = None, graphics_obj: Optional[KesslerGraphics] = None) -> None:
        """
        Create a graphics handler utilizing the assigned graphics engine defined from GraphicsType
        """
        self.type = type
        self.graphics: Optional[KesslerGraphics]
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

    def update(self, score: Score, ships: List[Ship], asteroids: List[Asteroid], bullets: List[Bullet], mines: List[Mine]) -> None:
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
