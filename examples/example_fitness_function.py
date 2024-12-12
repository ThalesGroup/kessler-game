# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.
import random

from src.kesslergame import KesslerController, KesslerGame, GraphicsType
from example_controller_fuzzy import FuzzyController
from example_scenarios import training_set


def exampleFitness(individual, settings=None):
    controller = FuzzyController(chromosome=individual)
    total_score = 0
    game_settings = {'perf_tracker': False,
                     'graphics_type': GraphicsType.NoGraphics,
                     'realtime_multiplier': 0,
                     'graphics_obj': None,
                     'frequency': 30}
    game = KesslerGame(settings=game_settings)  # Use this to visualize the game scenario
    for scenario in training_set:
        result, _ = game.run(scenario=scenario, controllers=[controller])
        scores = [team.asteroids_hit for team in result.teams]
        total_score += scores[0]

    return total_score,


if __name__ == "__main__":
    test_individual = [random.random() for _ in range(20)]
    print(test_individual)

    test_score = exampleFitness(individual=test_individual)
    print(test_score)

    # print(score.stop_reason)
    # print('Asteroids hit: ' + str([team.asteroids_hit for team in score.teams]))
    # print('Deaths: ' + str([team.deaths for team in score.teams]))
    # print('Accuracy: ' + str([team.accuracy for team in score.teams]))
    # print('Mean eval time: ' + str([team.mean_eval_time for team in score.teams]))
    # # test_controller = FuzzyController(individual)
    # print(test_controller)