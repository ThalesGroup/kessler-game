# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import time

import math
from typing import Dict, Any, List, Tuple, TypedDict, Optional
from enum import Enum
from collections import OrderedDict

from .scenario import Scenario
from .score import Score
from .controller import KesslerController
from .collisions import circle_line_collision
from .graphics import GraphicsType, GraphicsHandler
from .mines import Mine
from .asteroid import Asteroid
from .ship import Ship
from .bullet import Bullet
from .graphics import KesslerGraphics


class StopReason(Enum):
    not_stopped = 0
    no_ships = 1
    no_asteroids = 2
    time_expired = 3
    out_of_bullets = 4


class PerfDict(TypedDict, total=False):
    controller_times: List[float]
    total_controller_time: float
    physics_update: float
    collisions_check: float
    score_update: float
    graphics_draw: float
    total_frame_time: float


class KesslerGame:
    def __init__(self, settings: Optional[Dict[str, Any]] = None) -> None:

        if settings is None:
            settings = {}
        # Game settings
        self.frequency: float = settings.get("frequency", 30.0)
        self.time_step: float = 1 / settings.get("frequency", 30.0)
        self.perf_tracker: bool = settings.get("perf_tracker", True)
        self.prints_on: bool = settings.get("prints_on", True)
        self.graphics_type: GraphicsType = settings.get("graphics_type", GraphicsType.Tkinter)
        self.graphics_obj: Optional[KesslerGraphics] = settings.get("graphics_obj", None)
        self.realtime_multiplier: float = settings.get("realtime_multiplier", 0 if self.graphics_type==GraphicsType.NoGraphics else 1)
        self.time_limit: float = settings.get("time_limit", float("inf"))

        # UI settings
        default_ui = {'ships': True, 'lives_remaining': True, 'accuracy': True,
                      'asteroids_hit': True, 'bullets_remaining': True, 'controller_name': True}
        self.UI_settings = settings.get("UI_settings", default_ui)
        if self.UI_settings == 'all':
            self.UI_settings = {'ships': True, 'lives_remaining': True, 'accuracy': True,
                                'asteroids_hit': True, 'shots_fired': True, 'bullets_remaining': True,
                                'controller_name': True}
        
    def run(self, scenario: Scenario, controllers: List[KesslerController]) -> Tuple[Score, List[PerfDict]]:
        """
        Run an entire scenario from start to finish and return score and stop reason
        """

        ##################
        # INITIALIZATION #
        ##################
        # Initialize objects lists from scenario
        asteroids: List[Asteroid] = scenario.asteroids()
        ships: List[Ship] = scenario.ships()
        bullets: List[Bullet] = []
        mines: List[Mine] = []

        # Initialize Scoring class
        score = Score(scenario)

        # Initialize environment parameters
        stop_reason = StopReason.not_stopped
        sim_time: float = 0.0
        step: int = 0
        time_limit = scenario.time_limit if scenario.time_limit else self.time_limit

        # Assign controllers to each ship
        for controller, ship in zip(controllers, ships):
            controller.ship_id = ship.id
            ship.controller = controller

        # Initialize graphics display
        graphics = GraphicsHandler(type=self.graphics_type, scenario=scenario, UI_settings=self.UI_settings, graphics_obj=self.graphics_obj)

        # Initialize list of dictionary for performance tracking (will remain empty if perf_tracker is false
        perf_list: List[PerfDict] = []

        ######################
        # MAIN SCENARIO LOOP #
        ######################
        bullet_remove_idxs: list[int] = []
        asteroid_remove_idxs: set[int] = set()
        mine_remove_idxs: list[int] = []
        new_asteroids: list[Asteroid] = []
        while stop_reason == StopReason.not_stopped:

            # Get perf time at the start of time step evaluation and initialize performance tracker
            step_start = time.perf_counter()
            perf_dict: PerfDict = {}

            # --- CALL CONTROLLER FOR EACH SHIP ------------------------------------------------------------------------
            # Get all live ships
            liveships = [ship for ship in ships if ship.alive]

            # Generate game_state info to send to controllers
            game_state = {
                'asteroids': [asteroid.state for asteroid in asteroids],
                'ships': [ship.state for ship in liveships],
                'bullets': [bullet.state for bullet in bullets],
                'mines': [mine.state for mine in mines],
                'map_size': scenario.map_size,
                'time': sim_time,
                'delta_time': self.time_step,
                'sim_frame': step,
                'time_limit': time_limit
            }

            # Initialize controller time recording in performance tracker
            if self.perf_tracker:
                perf_dict['controller_times'] = []
                t_start = time.perf_counter()

            # Loop through each controller/ship combo and apply their actions
            for idx, ship in enumerate(ships):
                if ship.alive:
                    # Reset controls on ship to defaults
                    ship.thrust = 0.0
                    ship.turn_rate = 0.0
                    ship.fire = False
                    # Evaluate each controller letting control be applied
                    if controllers[idx].ship_id != ship.id:
                        raise RuntimeError("Controller and ship ID do not match")
                    ship.thrust, ship.turn_rate, ship.fire, ship.drop_mine = controllers[idx].actions(ship.ownstate, game_state)

                # Update controller evaluation time if performance tracking
                if self.perf_tracker:
                    controller_time = time.perf_counter() - t_start if ship.alive else 0.00
                    perf_dict['controller_times'].append(controller_time)
                    t_start = time.perf_counter()

            if self.perf_tracker:
                perf_dict['total_controller_time'] = time.perf_counter() - step_start
                prev = time.perf_counter()

            # --- UPDATE STATE INFORMATION OF EACH OBJECT --------------------------------------------------------------

            # Update each Asteroid, Bullet, and Ship
            for bullet in bullets:
                bullet.update(self.time_step)
            for mine in mines:
                mine.update(self.time_step)
            for asteroid in asteroids:
                asteroid.update(self.time_step)
            for ship in liveships:
                if ship.alive:
                    new_bullet, new_mine = ship.update(self.time_step)
                    if new_bullet is not None:
                        bullets.append(new_bullet)
                    if new_mine is not None:
                        mines.append(new_mine)

            # Cull any bullets past the map edge
            bullets = [bullet
                       for bullet
                       in bullets
                       if 0.0 <= bullet.position[0] <= scenario.map_size[0]
                       and 0.0 <= bullet.position[1] <= scenario.map_size[1]]

            # Wrap ships and asteroids to other side of map
            for ship in liveships:
                ship.position = (ship.position[0] % scenario.map_size[0], ship.position[1] % scenario.map_size[1])

            for asteroid in asteroids:
                asteroid.position = (asteroid.position[0] % scenario.map_size[0], asteroid.position[1] % scenario.map_size[1])

            # Update performance tracker with
            if self.perf_tracker:
                perf_dict['physics_update'] = time.perf_counter() - prev
                prev = time.perf_counter()

            # --- CHECK FOR COLLISIONS ---------------------------------------------------------------------------------


            # --- Check asteroid-bullet collisions ---
            for idx_bul, bullet in enumerate(bullets):
                for idx_ast, asteroid in enumerate(asteroids):
                    if idx_ast in asteroid_remove_idxs:
                        continue
                    # If collision occurs
                    if circle_line_collision(bullet.position, bullet.tail, asteroid.position, asteroid.radius):
                        # Increment hit values on ship that fired bullet then destruct bullet and mark for removal
                        bullet.owner.asteroids_hit += 1
                        bullet.owner.bullets_hit += 1
                        bullet.destruct()
                        bullet_remove_idxs.append(idx_bul)
                        # Asteroid destruct function and mark for removal
                        asteroids.extend(asteroid.destruct(impactor=bullet))
                        asteroid_remove_idxs.add(idx_ast)
                        # Stop checking this bullet
                        break
            # Cull bullets and asteroids that are marked for removal
            if bullet_remove_idxs:
                bullets = [bullet for idx, bullet in enumerate(bullets) if idx not in bullet_remove_idxs]
                bullet_remove_idxs.clear()

            # --- Check mine-asteroid and mine-ship effects ---
            for idx_mine, mine in enumerate(mines):
                if mine.detonating:
                    for idx_ast, asteroid in enumerate(asteroids):
                        if idx_ast in asteroid_remove_idxs:
                            continue
                        dx = asteroid.position[0] - mine.position[0]
                        dy = asteroid.position[1] - mine.position[1]
                        radius_sum = mine.blast_radius + asteroid.radius
                        if dx * dx + dy * dy <= radius_sum * radius_sum:
                            mine.owner.asteroids_hit += 1
                            mine.owner.mines_hit += 1
                            new_asteroids.extend(asteroid.destruct(impactor=mine))
                            asteroid_remove_idxs.add(idx_ast)
                    for ship in liveships:
                        if not ship.is_respawning:
                            dx = ship.position[0] - mine.position[0]
                            dy = ship.position[1] - mine.position[1]
                            radius_sum = mine.blast_radius + ship.radius
                            if dx * dx + dy * dy <= radius_sum * radius_sum:
                                # Ship destruct function.
                                ship.destruct(map_size=scenario.map_size)
                    if idx_mine not in mine_remove_idxs:
                        mine_remove_idxs.append(idx_mine)
                    mine.destruct()
            if mine_remove_idxs:
                mines = [mine for idx, mine in enumerate(mines) if idx not in mine_remove_idxs]
                mine_remove_idxs.clear()
            if new_asteroids:
                asteroids.extend(new_asteroids)
                new_asteroids.clear()


            # --- Check asteroid-ship collisions ---
            for ship in liveships:
                if not ship.is_respawning:
                    for idx_ast, asteroid in enumerate(asteroids):
                        if idx_ast in asteroid_remove_idxs:
                            continue
                        dx = ship.position[0] - asteroid.position[0]
                        dy = ship.position[1] - asteroid.position[1]
                        radius_sum = ship.radius + asteroid.radius
                        # Most of the time no collision occurs, so use early exit to optimize collision check
                        if abs(dx) <= radius_sum and abs(dy) <= radius_sum and dx * dx + dy * dy <= radius_sum * radius_sum:
                            # Asteroid destruct function and mark for removal
                            asteroids.extend(asteroid.destruct(impactor=ship))
                            asteroid_remove_idxs.add(idx_ast)
                            # Ship destruct function. Add one to asteroids_hit
                            ship.asteroids_hit += 1
                            ship.destruct(map_size=scenario.map_size)
                            # Stop checking this ship's collisions
                            break
            # Cull ships if not alive and asteroids that are marked for removal
            liveships = [ship for ship in liveships if ship.alive]
            if asteroid_remove_idxs:
                asteroids = [asteroid for idx, asteroid in enumerate(asteroids) if idx not in asteroid_remove_idxs]
                asteroid_remove_idxs.clear()

            # --- Check ship-ship collisions ---
            for i, ship1 in enumerate(liveships):
                for ship2 in liveships[i + 1:]:
                    if not ship2.is_respawning and not ship1.is_respawning:
                        dx = ship1.position[0] - ship2.position[0]
                        dy = ship1.position[1] - ship2.position[1]
                        radius_sum = ship1.radius + ship2.radius
                        # Most of the time no collision occurs, so use early exit to optimize collision check
                        if abs(dx) <= radius_sum and abs(dy) <= radius_sum and dx * dx + dy * dy <= radius_sum * radius_sum:
                            ship1.destruct(map_size=scenario.map_size)
                            ship2.destruct(map_size=scenario.map_size)
            # Cull ships that are not alive
            liveships = [ship for ship in liveships if ship.alive]

            # Update performance tracker with collisions timing
            if self.perf_tracker:
                perf_dict['collisions_check'] = time.perf_counter() - prev
                prev = time.perf_counter()

            # --- UPDATE SCORE CLASS -----------------------------------------------------------------------------------
            if self.perf_tracker:
                score.update(ships, sim_time, perf_dict['controller_times'])
            else:
                score.update(ships, sim_time)

            # Update performance tracker with score timing
            if self.perf_tracker:
                perf_dict['score_update'] = time.perf_counter() - prev
                prev = time.perf_counter()


            # --- UPDATE GRAPHICS --------------------------------------------------------------------------------------
            graphics.update(score, ships, asteroids, bullets, mines)

            # Update performance tracker with graphics timing
            if self.perf_tracker:
                perf_dict['graphics_draw'] = time.perf_counter() - prev
                prev = time.perf_counter()

            # --- CHECK STOP CONDITIONS --------------------------------------------------------------------------------
            sim_time += self.time_step
            step += 1

            # No asteroids remain
            if not asteroids:
                stop_reason = StopReason.no_asteroids
            # No ships are alive
            elif not liveships:
                stop_reason = StopReason.no_ships
            # All live ships are out of bullets and no bullets are on map
            elif not sum([ship.bullets_remaining for ship in liveships]) and not len(bullets)>0 and scenario.stop_if_no_ammo:
                stop_reason = StopReason.out_of_bullets
            # Out of time
            elif sim_time > time_limit:
                stop_reason = StopReason.time_expired

            # --- FINISHING TIME STEP ----------------------------------------------------------------------------------
            # Get overall time step compute time
            if self.perf_tracker:
                perf_dict['total_frame_time'] = time.perf_counter() - step_start
                perf_list.append(perf_dict)

            # Hold simulation so that it runs at realtime ratio if specified, else let it pass
            if self.realtime_multiplier != 0:
                time_dif = time.perf_counter() - step_start
                while time_dif < (self.time_step/self.realtime_multiplier):
                    time_dif = time.perf_counter() - step_start

        ############################################
        # Finalization after scenario has been run #
        ############################################

        # Close graphics display
        graphics.close()

        # Finalize score class before returning
        score.finalize(sim_time, stop_reason, ships)

        # Return the score and stop condition
        return score, perf_list


class TrainerEnvironment(KesslerGame):
    def __init__(self, settings: Optional[Dict[str, Any]] = None) -> None:
        """
        Instantiates a KesslerGame object with settings to optimize training time
        """
        if settings is None:
            settings = {}
        trainer_settings = {
            'frequency': settings.get("frequency", 30.0),
            'perf_tracker': settings.get("perf_tracker", False),
            'prints_on': settings.get("prints_on", False),
            'graphics_type': GraphicsType.NoGraphics,
            'realtime_multiplier': 0,
            'time_limit': settings.get("time_limit", float("inf"))
        }
        super().__init__(trainer_settings)
