# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from enum import Enum
import numpy as np

class GraphicsType(Enum):
    NoGraphics = 0
    UnrealEngine = 1
    Tkinter = 2
    Pyplot = 3


class GraphicsHandler:

    def __init__(self, type: GraphicsType=GraphicsType.NoGraphics, scenario=None, UI_settings=None):
        """
        Create a graphics handler utilizing the assigned graphics engine defined from GraphicsType
        """
        self.type = type
        match self.type:
            case GraphicsType.NoGraphics:
                self.graphics = None
            case GraphicsType.UnrealEngine:
                from .graphics_ue import GraphicsUE
                self.graphics = GraphicsUE(scenario.map_size, len(scenario.ships()), len(np.unique([ship.team for ship in scenario.ships()])))
            case GraphicsType.Tkinter:
                from .graphics_tk import GraphicsTK
                self.graphics = GraphicsTK(scenario, UI_settings)
            case GraphicsType.Pyplot:
                from .graphics_plt import GraphicsPLT
                self.graphics = GraphicsPLT(scenario.map_size)
                self.graphics.plot_first(scenario.ships(), [], scenario.asteroids())

    def update(self, score, ships, asteroids, bullets):
        """
        Update the graphics draw with new simulation data each simulation time-step
        """
        match self.type:
            case GraphicsType.NoGraphics:
                ...
            case GraphicsType.UnrealEngine:
                self.graphics.update(score, ships, asteroids, bullets)
            case GraphicsType.Tkinter:
                self.graphics.update(score, ships, asteroids, bullets)
            case GraphicsType.Pyplot:
                self.graphics.update(ships, asteroids, bullets)

    def close(self):
        """
        Finalize and close the graphics window
        """
        match self.type:
            case GraphicsType.NoGraphics:
                ...
            case GraphicsType.UnrealEngine:
                ...
            case GraphicsType.Tkinter:
                self.graphics.close()
            case GraphicsType.Pyplot:
                self.graphics.close()
