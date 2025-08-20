# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations
from typing import TYPE_CHECKING

from .ship import Ship
from .bullet import Bullet
from .scenario import Scenario
from .team import Team
from .controller import KesslerController
if TYPE_CHECKING:
    from .kessler_game import StopReason


class Score:
    def __init__(self, scenario: Scenario) -> None:
        self.sim_time: float = 0.0
        self.stop_reason: StopReason | None = None
        self.final_controllers: list[KesslerController] | None = None

        # Initialize team classes to score team-specific scores
        all_ships = scenario.ships()
        unique_team_pairs = sorted({(ship.team, ship.team_name) for ship in all_ships}, key=lambda t: t[0])  # Use set for uniqueness, and sort by team id
        self.teams = [Team(int(tid), str(tname)) for tid, tname in unique_team_pairs]

        # Populate scenario initial conditions into score parameters
        for team in self.teams:
            team.total_asteroids = scenario.max_asteroids
            ships_on_team = [ship for ship in all_ships if team.team_id == ship.team]
            if scenario.bullet_limit is not None:
                team.total_bullets = scenario.bullet_limit * len(ships_on_team)
            else:
                team.total_bullets = -1

    def update(self, ships: list[Ship], bullets: list[Bullet], sim_time: float, controller_perf: list[float] | None = None) -> None:
        self.sim_time = sim_time
        # Count number of live bullets per ship
        live_bullets_dict: dict[int, int] = {}
        for bullet in bullets:
            live_bullets_dict[bullet.owner.id] = live_bullets_dict.get(bullet.owner.id, 0) + 1

        for team in self.teams:
            bullet_asteroid_hits = 0
            ship_asteroid_hits = 0
            ship_ship_hits = 0
            mine_asteroid_hits = 0
            mine_ship_hits = 0
            shots = 0
            bullets_remaining = 0
            live_bullets = 0
            mines_dropped = 0
            mines = 0
            asteroid_deaths = 0
            ship_deaths = 0
            mine_deaths = 0
            lives = 0

            for idx, ship in enumerate(ships):
                if ship.team == team.team_id:
                    bullet_asteroid_hits += ship.bullet_asteroid_hits
                    ship_asteroid_hits += ship.ship_asteroid_hits
                    ship_ship_hits += ship.ship_ship_hits
                    mine_asteroid_hits += ship.mine_asteroid_hits
                    mine_ship_hits += ship.mine_ship_hits
                    shots += ship.bullets_shot
                    bullets_remaining += ship.bullets_remaining
                    mines_dropped += ship.mines_dropped
                    mines += ship.mines_remaining
                    asteroid_deaths += ship.asteroid_deaths
                    ship_deaths += ship.ship_deaths
                    mine_deaths += ship.mine_deaths
                    lives += ship.lives
                    live_bullets += live_bullets_dict.get(ship.id, 0)
                    # Assume that the ships list and controller_perf lists are in the same consistent order
                    if controller_perf is not None and controller_perf[idx] > 0:
                        team.eval_times.append(controller_perf[idx])

            team.bullet_asteroid_hits = bullet_asteroid_hits
            team.ship_asteroid_hits = ship_asteroid_hits
            team.ship_ship_hits = ship_ship_hits
            team.mine_asteroid_hits = mine_asteroid_hits
            team.mine_ship_hits = mine_ship_hits
            team.shots_fired = shots
            team.bullets_remaining = bullets_remaining
            team.mines_dropped = mines_dropped
            team.mines_remaining = mines
            team.asteroid_deaths = asteroid_deaths
            team.ship_deaths = ship_deaths
            team.mine_deaths = mine_deaths
            team.lives_remaining = lives
            team.live_bullets = live_bullets

    def finalize(self, sim_time: float, stop_reason: StopReason, ships: list[Ship]) -> None:
        self.sim_time = sim_time
        self.stop_reason = stop_reason
        self.final_controllers = [ship.controller for ship in ships if ship.controller is not None]

    def __repr__(self) -> str:
        stop = self.stop_reason.name if self.stop_reason is not None else "None"
        teams_text = "\n  ".join(repr(team) for team in self.teams)
        return f"<Score(sim_time={self.sim_time:.2f}, stop_reason={stop},\n Teams:\n  {teams_text})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Score):
            return False

        if self.sim_time != other.sim_time or self.stop_reason != other.stop_reason:
            return False

        if len(self.teams) != len(other.teams):
            return False

        for team_self, team_other in zip(self.teams, other.teams):
            if team_self != team_other:
                return False

        return True
