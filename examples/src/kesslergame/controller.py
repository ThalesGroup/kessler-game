# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import Dict, Tuple
import time

from .ship import Ship


class KesslerController:
    """
     A ship controller class for Kessler. This can be inherited to create custom controllers that can be passed to the
    game to operate within scenarios. A valid controller contains an actions method that takes in a ship object and ass
    game_state dictionary. This action method then sets the thrust, turn_rate, and fire commands on the ship object.
    """

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool, bool]:
        """
        Method processed each time step by this controller.
        """

        raise NotImplementedError('Your derived KesslerController must include an actions method for control input.')


    # Property to store the ID for the ship this controller is attached to during a scenario
    @property
    def ship_id(self):
        return self._ship_id if self._ship_id else 0

    @ship_id.setter
    def ship_id(self, value):
        self._ship_id = value

    @property
    def name(self) -> str:
        raise NotImplementedError(f"This controller {self.__class__} needs to have a name() property specified.")
