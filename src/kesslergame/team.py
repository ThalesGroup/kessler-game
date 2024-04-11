# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import numpy as np


class Team:
    def __init__(self, id: int, name: str) -> None:
        self.team_id = id
        self.team_name = name

        self.total_bullets: int = 0
        self.total_asteroids: int = 0

        self.asteroids_hit: int = 0
        self.bullets_hit: int = 0
        self.shots_fired: int = 0
        self.bullets_remaining: int = 0
        self.deaths: int = 0
        self.eval_times: list[float] = []
        self.lives_remaining: int = 0

    @property
    def accuracy(self) -> float:
        return self.bullets_hit / self.shots_fired if self.shots_fired else 0.0

    @property
    def fraction_total_asteroids_hit(self) -> float:
        return self.asteroids_hit / self.total_asteroids

    @property
    def fraction_bullets_used(self) -> float:
        return self.shots_fired / self.total_bullets

    @property
    def ratio_bullets_needed(self) -> float:
        return self.shots_fired / self.total_asteroids

    @property
    def mean_eval_time(self) -> float:
        if self.eval_times:
            return float(np.mean(self.eval_times))
        else:
            return 0.0

    @property
    def median_eval_time(self) -> float:
        if self.eval_times:
            return float(np.median(self.eval_times))
        else:
            return 0.0

    @property
    def min_eval_time(self) -> float:
        if self.eval_times:
            return min(self.eval_times)
        else:
            return 0.0

    @property
    def max_eval_time(self) -> float:
        if self.eval_times:
            return max(self.eval_times)
        else:
            return 0.0
