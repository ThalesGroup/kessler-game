# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import time

from src.kesslergame import Scenario


# Small game scenario with 5 random (seeded) asteroid initial conditions
scenario1 = Scenario(name='Scenario 1',
                            num_asteroids=5,
                            seed=3,
                            ship_states=[
                                {'position': (400, 400), 'angle': 90, 'lives': 3, 'team': 1, "mines_remaining": 3},
                                # {'position': (400, 600), 'angle': 90, 'lives': 3, 'team': 2, "mines_remaining": 3},
                            ],
                            map_size=(1000, 800),
                            time_limit=30,
                            ammo_limit_multiplier=0,
                            stop_if_no_ammo=False)


# Slightly bigger game scenario with 10 random (seeded) asteroid initial conditions
scenario2 = Scenario(name='Scenario 2',
                            num_asteroids=10,
                            seed=3,
                            ship_states=[
                                {'position': (400, 400), 'angle': 90, 'lives': 3, 'team': 1, "mines_remaining": 3},
                                # {'position': (400, 600), 'angle': 90, 'lives': 3, 'team': 2, "mines_remaining": 3},
                            ],
                            map_size=(1000, 800),
                            time_limit=30,
                            ammo_limit_multiplier=0,
                            stop_if_no_ammo=False)

training_set = [scenario1,
                scenario2]
