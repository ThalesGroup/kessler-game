# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import numpy as np


class Team:
    def __init__(self, id, name):
        self.team_id = id
        self.team_name = name

        self.total_bullets = 0
        self.total_asteroids = 0

        self.asteroids_hit = 0
        self.bullets_hit = 0
        self.shots_fired = 0
        self.bullets_remaining = 0
        self.deaths = 0
        self.eval_times = []
        self.lives_remaining = 0

    @property
    def accuracy(self) -> float:
        return self.bullets_hit / self.shots_fired if self.shots_fired else 0

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
        return np.mean(self.eval_times)

    @property
    def median_eval_time(self) -> float:
        return np.median(self.eval_times)

    @property
    def min_eval_time(self) -> float:
        return min(self.eval_times)

    @property
    def max_eval_time(self) -> float:
        return max(self.eval_times)
