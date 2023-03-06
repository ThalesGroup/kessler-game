# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from src.kesslergame import KesslerController
from typing import Dict, Tuple


class TestController(KesslerController):
    def __init__(self):
        self.eval_frames = 0

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool]:
        """
        Method processed each time step by this controller.
        """

        thrust = 0
        turn_rate = 90
        fire = True
        self.eval_frames +=1

        return thrust, turn_rate, fire

    @property
    def name(self) -> str:
        return "Test Controller"
