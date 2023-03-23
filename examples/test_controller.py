# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from src.kesslergame import KesslerController
from src.kesslergame.explanation import TTSController
from typing import Dict, Tuple


class TestController(TTSController):
    def __init__(self):
        self.my_heading = None

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool]:
        """
        Method processed each time step by this controller.
        """
        self.my_heading = round(ship_state['heading'])

        thrust = 0
        turn_rate = 50
        fire = True

        return thrust, turn_rate, fire

    @property
    def name(self) -> str:
        return "Test Controller"

    @property
    def explanation(self) -> str:
        exp = "My heading is "+ str(self.my_heading) + " degrees"
        return exp
