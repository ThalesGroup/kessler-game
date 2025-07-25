# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import time
import numpy as np
import sys

from kesslergame import Scenario, KesslerGame, GraphicsType
from test_controller import TestController
from graphics_both import GraphicsBoth

# Define game scenario
my_test_scenario = Scenario(name='Test Scenario',
                            num_asteroids=10,
                            ship_states=[
                                {'position': (400, 400), 'angle': 90, 'lives': 3, 'team': 1, "mines_remaining": 3},
                                # {'position': (400, 600), 'angle': 90, 'lives': 3, 'team': 2, "mines_remaining": 3},
                            ],
                            map_size=(1000, 800),
                            time_limit=60,
                            ammo_limit_multiplier=0,
                            stop_if_no_ammo=False)

# Define Game Settings
game_settings = {'perf_tracker': True,
                 'graphics_type': GraphicsType.NoGraphics,
                 'realtime_multiplier': 0,
                 'graphics_obj': None,
                 'frequency': 30}

runs = 5000
timings = np.zeros(runs)

for ii in range(runs):
    game = KesslerGame(settings=game_settings)  # Use this to visualize the game scenario
    # game = TrainerEnvironment(settings=game_settings)  # Use this for max-speed, no-graphics simulation

    # Evaluate the game
    pre = time.perf_counter()
    score, perf_data = game.run(scenario=my_test_scenario, controllers=[TestController(), TestController()])
    timings[ii] = time.perf_counter()-pre
    print("\r", "Progress: {:.2f}".format((ii/(runs-1))*100.0) + "%", end="")
    # text = "\nProgress: {}".format((ii/runs)*100.0) + "%"
    # sys.stdout.write(text)
    # sys.stdout.flush()


print("\nMax eval time:" + str(np.max(timings)))
print("Min eval time:" + str(np.min(timings)))
print("Avg eval time:" + str(np.mean(timings)))
print("Var eval time:" + str(np.var(timings)))

np.savetxt("mypyc_timings.csv", timings, delimiter=",", fmt="%12f")

# Print out some general info about the result
# print('Scenario eval time: '+str(time.perf_counter()-pre))
# print(score.stop_reason)
# print('Asteroids hit: ' + str([team.asteroids_hit for team in score.teams]))
# print('Deaths: ' + str([team.deaths for team in score.teams]))
# print('Accuracy: ' + str([team.accuracy for team in score.teams]))
# print('Mean eval time: ' + str([team.mean_eval_time for team in score.teams]))
