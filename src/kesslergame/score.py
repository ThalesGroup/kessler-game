# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import List, Optional, TYPE_CHECKING

import numpy as np

from .ship import Ship
from .asteroid import Asteroid
from .scenario import Scenario
from .team import Team
if TYPE_CHECKING:
    from .kessler_game import StopReason


class Score:
    def __init__(self, scenario: Scenario) -> None:
        self.sim_time: float = 0.0
        self.stop_reason: Optional['StopReason'] = None


        # Initialize team classes to score team-specific scores
        team_ids = [ship.team for ship in scenario.ships()]
        team_names = [ship.team_name for ship in scenario.ships()]
        self.teams = [Team(int(team_id), str(team_name)) for team_id, team_name in zip(np.unique(team_ids), np.unique(team_names))]

        # Populate scenario initial conditions into score parameters
        for team in self.teams:
            team.total_asteroids = scenario.max_asteroids
            for ship in scenario.ships():
                if team.team_id == ship.team:
                    team.total_bullets += scenario.bullet_limit

    def update(self, ships: List[Ship], sim_time: float, controller_perf: Optional[List[float]] = None) -> None:
        self.sim_time = sim_time
        for team in self.teams:
            ast_hit, bul_hit, shots, bullets, deaths, lives = (0, 0, 0, 0, 0, 0)
            for idx, ship in enumerate(ships):
                if team.team_id == ship.team:
                    ast_hit += ship.asteroids_hit
                    bul_hit += ship.bullets_hit
                    shots += ship.bullets_shot
                    bullets += ship.bullets_remaining
                    deaths += ship.deaths
                    lives += ship.lives
                    if controller_perf is not None and controller_perf[idx] > 0:
                        team.eval_times.append(controller_perf[idx])
            team.asteroids_hit, team.bullets_hit, team.shots_fired, team.bullets_remaining, team.deaths, team.lives_remaining = (ast_hit, bul_hit, shots, bullets, deaths, lives)

    def finalize(self, sim_time: float, stop_reason: 'StopReason', ships: List[Ship]) -> None:
        self.sim_time = sim_time
        self.stop_reason = stop_reason
        self.final_controllers = [ship.controller for ship in ships]
