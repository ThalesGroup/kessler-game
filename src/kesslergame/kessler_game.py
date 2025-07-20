# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import time
import math

from typing import Any, TypedDict, Optional
from enum import Enum

from .scenario import Scenario
from .score import Score
from .controller import KesslerController
from .collisions import circle_line_collision_continuous, collision_time_interval
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
    controller_times: list[float]
    total_controller_time: float
    physics_update: float
    collisions_check: float
    score_update: float
    graphics_draw: float
    total_frame_time: float

class KesslerGame:
    def __init__(self, settings: Optional[dict[str, Any]] = None) -> None:
        if settings is None:
            settings = {}
        # Game settings
        self.frequency: float = settings.get("frequency", 30.0)
        self.time_step: float = 1.0 / settings.get("frequency", 30.0)
        self.perf_tracker: bool = settings.get("perf_tracker", True)
        self.prints_on: bool = settings.get("prints_on", True)
        self.graphics_type: GraphicsType = settings.get("graphics_type", GraphicsType.Tkinter)
        self.graphics_obj: Optional[KesslerGraphics] = settings.get("graphics_obj", None)
        self.realtime_multiplier: float = settings.get("realtime_multiplier", 0 if self.graphics_type==GraphicsType.NoGraphics else 1)
        self.time_limit: float = settings.get("time_limit", float("inf"))
        self.random_ast_splits = settings.get("random_ast_splits", False)

        # UI settings
        default_ui = {'ships': True, 'lives_remaining': True, 'accuracy': True,
                      'asteroids_hit': True, 'bullets_remaining': True, 'controller_name': True, 'scale': 1.0}
        self.UI_settings = settings.get("UI_settings", default_ui)
        if self.UI_settings == 'all':
            self.UI_settings = {'ships': True, 'lives_remaining': True, 'accuracy': True,
                                'asteroids_hit': True, 'shots_fired': True, 'bullets_remaining': True,
                                'controller_name': True, 'scale': 1.0}
        
    def run(self, scenario: Scenario, controllers: list[KesslerController]) -> tuple[Score, list[PerfDict]]:
        """
        Run an entire scenario from start to finish and return score and stop reason
        """

        ##################
        # INITIALIZATION #
        ##################
        # Initialize objects lists from scenario
        asteroids: list[Asteroid] = scenario.asteroids()
        ships: list[Ship] = scenario.ships()
        bullets: list[Bullet] = []
        mines: list[Mine] = []

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
            if hasattr(controller, "custom_sprite_path"):
                ship.custom_sprite_path = controller.custom_sprite_path

        # Initialize graphics display
        graphics = GraphicsHandler(type=self.graphics_type, scenario=scenario, UI_settings=self.UI_settings, graphics_obj=self.graphics_obj)

        # Initialize list of dictionary for performance tracking (will remain empty if perf_tracker is false
        perf_list: list[PerfDict] = []

        ######################
        # MAIN SCENARIO LOOP #
        ######################

        # Conceptually these following collections should just be sets, but lists can be faster if there's very few elements
        bullet_remove_idxs: list[int] = []
        mine_remove_idxs: list[int] = []
        new_asteroids: list[Asteroid] = []
        while stop_reason == StopReason.not_stopped:
            # Get perf time at the start of time step evaluation and initialize performance tracker
            step_start = time.perf_counter()
            perf_dict: PerfDict = {}

            # --- CALL CONTROLLER FOR EACH SHIP ------------------------------------------------------------------------
            # Get all live ships
            liveships = [ship for ship in ships if ship.alive]

            # Initialize controller time recording in performance tracker
            if self.perf_tracker:
                perf_dict['controller_times'] = []
                t_start = time.perf_counter()

            # Loop through each controller/ship combo and apply their actions
            for idx, ship in enumerate(ships):
                if ship.alive:
                    # Generate game_state info to send to controller
                    # It is important we regenerate this for each controller, so they do not tamper it for the next controller
                    game_state: dict[str, Any] = {
                        'asteroids': [asteroid.state for asteroid in asteroids],
                        'ships': [ship.state for ship in liveships],
                        'bullets': [bullet.state for bullet in bullets],
                        'mines': [mine.state for mine in mines],
                        'map_size': scenario.map_size,
                        'time': sim_time,
                        'delta_time': self.time_step,
                        'frame_rate': self.frequency,
                        'sim_frame': step,
                        'time_limit': time_limit,
                        'random_asteroid_splits': self.random_ast_splits
                    }
                    # Reset controls on ship to defaults
                    ship.thrust = 0.0
                    ship.turn_thrust = 0.0
                    ship.fire = False
                    # Evaluate each controller letting control be applied
                    if controllers[idx].ship_id != ship.id:
                        raise RuntimeError("Controller and ship ID do not match")
                    ship.thrust, ship.turn_thrust, ship.fire, ship.drop_mine = controllers[idx].actions(ship.ownstate, game_state)

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
            bul_idx = 0
            num_buls = len(bullets)
            should_remove_bullet: bool = False
            while bul_idx < num_buls:
                should_remove_bullet = False
                bullet = bullets[bul_idx]

                ast_idx_to_remove: int = -1
                earliest_collision_time: float = math.inf

                for ast_idx, asteroid in enumerate(asteroids):
                    # Iterate through all asteroids, and if multiple collisions occur, find the one that occurs first
                    if circle_line_collision_continuous(
                        bullet.position, bullet.tail, bullet.velocity,
                        asteroid.position, asteroid.velocity, asteroid.radius, self.time_step
                    ):
                        collision_start_time, collision_end_time = collision_time_interval(
                            bullet.position, bullet.tail, bullet.velocity,
                            asteroid.position, asteroid.velocity, asteroid.radius)
                        collision_time = max(-self.time_step, collision_start_time)
                        assert(collision_time <= 0.0)
                        if collision_time < earliest_collision_time:
                            earliest_collision_time = collision_time
                            ast_idx_to_remove = ast_idx
                if ast_idx_to_remove != -1:
                    # Increment hit values on ship that fired bullet then destruct bullet and mark for removal
                    bullet.owner.asteroids_hit += 1
                    bullet.owner.bullets_hit += 1
                    should_remove_bullet = True
                    asteroid = asteroids[ast_idx_to_remove]
                    # Asteroid destruct function and immediate removal
                    new_asteroids.extend(asteroid.destruct(impactor=bullet, random_ast_split=self.random_ast_splits))
                    # Swap and pop, O(1) removal of asteroid
                    asteroids[ast_idx_to_remove] = asteroids[-1]
                    asteroids.pop()
                # Cull any bullets past the map edge
                # It is important we do this after the asteroid-bullet collision checks occur,
                # in the case of bullets leaving the map but might hit an asteroid on the edge
                if not ((0.0 <= bullet.position[0] <= scenario.map_size[0] and 0.0 <= bullet.position[1] <= scenario.map_size[1])
                        or (0.0 <= bullet.tail[0] <= scenario.map_size[0] and 0.0 <= bullet.tail[1] <= scenario.map_size[1])):
                    should_remove_bullet = True
                # O(1) removal of bullet
                if should_remove_bullet:
                    bullet.destruct()
                    bullets[bul_idx] = bullets[-1]
                    bullets.pop()
                    num_buls -= 1
                else:
                    bul_idx += 1

            # Add the new asteroids from the bullet-asteroid collisions
            if new_asteroids:
                asteroids.extend(new_asteroids)
                new_asteroids.clear()
            # --- Check mine-asteroid and mine-ship effects ---
            for idx_mine, mine in enumerate(mines):
                if mine.detonating:
                    i = 0
                    num_asts = len(asteroids)
                    while i < num_asts:
                        asteroid = asteroids[i]
                        dx = asteroid.position[0] - mine.position[0]
                        dy = asteroid.position[1] - mine.position[1]
                        radius_sum = mine.blast_radius + asteroid.radius
                        if dx * dx + dy * dy <= radius_sum * radius_sum:
                            mine.owner.asteroids_hit += 1
                            mine.owner.mines_hit += 1
                            new_asteroids.extend(asteroid.destruct(impactor=mine, random_ast_split=self.random_ast_splits))
                            last_idx = len(asteroids) - 1
                            if i != last_idx:
                                asteroids[i] = asteroids[last_idx]
                            asteroids.pop()
                            num_asts -= 1
                            # Don't advance i, must check the swapped-in asteroid
                        else:
                            i += 1
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
            # Add new asteroids from mine-asteroid collisions
            if new_asteroids:
                asteroids.extend(new_asteroids)
                new_asteroids.clear()
            # --- Check asteroid-ship collisions ---
            for ship in liveships:
                if not ship.is_respawning:
                    i = 0
                    num_asts = len(asteroids)
                    while i < num_asts:
                        asteroid = asteroids[i]
                        dx = ship.position[0] - asteroid.position[0]
                        dy = ship.position[1] - asteroid.position[1]
                        radius_sum = ship.radius + asteroid.radius
                        # Most of the time no collision occurs, so use early exit to optimize collision check
                        if abs(dx) <= radius_sum and abs(dy) <= radius_sum and dx * dx + dy * dy <= radius_sum * radius_sum:
                            # Asteroid destruct function and immediate removal
                            new_asteroids.extend(asteroid.destruct(impactor=ship, random_ast_split=self.random_ast_splits))
                            last_idx = len(asteroids) - 1
                            if i != last_idx:
                                asteroids[i] = asteroids[last_idx]
                            asteroids.pop()
                            num_asts -= 1
                            # Ship destruct function. Add one to asteroids_hit
                            ship.asteroids_hit += 1
                            ship.destruct(map_size=scenario.map_size)
                            # Stop checking this ship's collisions
                            break
                        else:
                            i += 1
            # Cull ships if not alive
            liveships = [ship for ship in liveships if ship.alive]
            # Add new asteroids from ship-asteroid collisions
            if new_asteroids:
                asteroids.extend(new_asteroids)
                new_asteroids.clear()
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

            if not asteroids:
                # No asteroids remain
                stop_reason = StopReason.no_asteroids
            elif not liveships and not (len(mines) > 0 or len(bullets) > 0):
                # No ships are alive and no mines exist and no bullets exist
                # Prevents unfairness where ship that dies before another gets score from its bullets as long as the other
                # is alive but the one that lives longer doesn't get the same benefit from its bullets/mines persisting
                # after it dies
                stop_reason = StopReason.no_ships
            elif not sum([ship.bullets_remaining for ship in liveships]) > 0 \
                    and not sum([ship.mines_remaining for ship in liveships])\
                    and not (len(bullets) > 0 or len(mines) > 0) \
                    and scenario.stop_if_no_ammo:
                # All live ships are out of bullets and no bullets are on map
                stop_reason = StopReason.out_of_bullets
            elif sim_time > time_limit:
                # Out of time
                stop_reason = StopReason.time_expired

            # --- FINISHING TIME STEP ----------------------------------------------------------------------------------
            # Get overall time step compute time
            if self.perf_tracker:
                perf_dict['total_frame_time'] = time.perf_counter() - step_start
                perf_list.append(perf_dict)

            # Hold simulation so that it runs at realtime ratio if specified, else let it pass
            if self.realtime_multiplier != 0:
                time_dif = time.perf_counter() - step_start
                while time_dif < (self.time_step / self.realtime_multiplier):
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
    def __init__(self, settings: Optional[dict[str, Any]] = None) -> None:
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
