# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from src.kesslergame import KesslerController
from typing import Dict, Tuple


class TestController(KesslerController):

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool]:
        """
        Method processed each time step by this controller.
        """

        thrust = 0
        turn_rate = 50
        fire = True

        return thrust, turn_rate, fire

    @property
    def name(self) -> str:
        return "Test Controller"
