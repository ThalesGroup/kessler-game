# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from statistics import mean, median


class Team:
    def __init__(self, id: int, name: str) -> None:
        self.team_id = id
        self.team_name = name

        self.total_bullets: int = 0
        self.total_asteroids: int = 0

        # Asteroid hit statistics
        self.bullet_asteroid_hits: int = 0
        self.ship_asteroid_hits: int = 0
        self.ship_ship_hits: int = 0
        self.mine_asteroid_hits: int = 0
        self.mine_ship_hits: int = 0

        self.shots_fired: int = 0
        self.bullets_missed: int = 0
        self.bullets_remaining: int = 0
        self.live_bullets: int = 0
        self.mines_dropped: int = 0
        self.mines_remaining: int = 0

        # Death statistics
        self.asteroid_deaths: int = 0
        self.ship_deaths: int = 0
        self.mine_deaths: int = 0

        self.eval_times: list[float] = []
        self.lives_remaining: int = 0

    @property
    def asteroids_hit(self) -> int:
        return self.bullet_asteroid_hits + self.ship_asteroid_hits + self.mine_asteroid_hits

    @property
    def ships_hit(self) -> int:
        return self.ship_ship_hits + self.mine_ship_hits

    @property
    def deaths(self) -> int:
        return self.asteroid_deaths + self.ship_deaths + self.mine_deaths

    @property
    def accuracy(self) -> float:
        # This is the ratio of the bullets hit, to the total number of bullets that were fired from the ships
        return self.bullet_asteroid_hits / self.shots_fired if self.shots_fired != 0 else 0.0

    @property
    def confirmed_accuracy(self) -> float:
        # This is the ratio of bullets hit, to the total number of inactive bullets (either left the map or hit)
        # This is better for a live display of accuracy, so bullets en-route to an asteroid do not hurt the accuracy
        inactive_bullets = self.shots_fired - self.live_bullets
        return self.bullet_asteroid_hits / inactive_bullets if inactive_bullets != 0 else 0.0

    @property
    def fraction_total_asteroids_hit(self) -> float:
        return self.asteroids_hit / self.total_asteroids if self.total_asteroids != 0 else 0.0

    @property
    def fraction_bullets_used(self) -> float:
        return self.shots_fired / self.total_bullets if self.total_bullets != 0 else 0.0

    @property
    def ratio_bullets_needed(self) -> float:
        return self.shots_fired / self.total_asteroids if self.total_asteroids != 0 else 0.0

    @property
    def mean_eval_time(self) -> float:
        if self.eval_times:
            return float(mean(self.eval_times))
        else:
            return 0.0

    @property
    def median_eval_time(self) -> float:
        if self.eval_times:
            return float(median(self.eval_times))
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

    def __repr__(self) -> str:
        return (
            f"Team {self.team_id} ({self.team_name}): "
            f"Asteroid Hits (Bullet={self.bullet_asteroid_hits}, "
            f"Ship={self.ship_asteroid_hits}, Mine={self.mine_asteroid_hits}, "
            f"Total={self.asteroids_hit}), "
            f"Ship Hits (Ship={self.ship_ship_hits}, "
            f"Mine={self.mine_ship_hits}, Total={self.ships_hit}), "
            f"Shots Fired={self.shots_fired}, Bullets Remaining={self.bullets_remaining}, "
            f"Mines Dropped={self.mines_dropped}, Mines Remaining={self.mines_remaining}, "
            f"Deaths (Asteroid={self.asteroid_deaths}, Ship={self.ship_deaths}, "
            f"Mine={self.mine_deaths}, Total={self.deaths}), "
            f"Lives Remaining={self.lives_remaining}, "
            f"Eval Times={self.eval_times}"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return False

        return (
            self.team_id == other.team_id and
            self.team_name == other.team_name and
            self.total_bullets == other.total_bullets and
            self.total_asteroids == other.total_asteroids and
            self.bullet_asteroid_hits == other.bullet_asteroid_hits and
            self.ship_asteroid_hits == other.ship_asteroid_hits and
            self.ship_ship_hits == other.ship_ship_hits and
            self.mine_asteroid_hits == other.mine_asteroid_hits and
            self.mine_ship_hits == other.mine_ship_hits and
            self.asteroid_deaths == other.asteroid_deaths and
            self.ship_deaths == other.ship_deaths and
            self.mine_deaths == other.mine_deaths and
            self.shots_fired == other.shots_fired and
            self.bullets_remaining == other.bullets_remaining and
            self.mines_dropped == other.mines_dropped and
            self.mines_remaining == other.mines_remaining and
            self.lives_remaining == other.lives_remaining
            # and self.eval_times == other.eval_times
        )
