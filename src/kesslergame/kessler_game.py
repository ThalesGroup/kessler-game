# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import time
import math

from typing import Any, TypedDict, cast
from enum import Enum

from .scenario import Scenario
from .score import Score
from .controller import KesslerController
from .collisions import circle_line_collision_continuous, collision_time_interval
from .graphics import GraphicsType, GraphicsHandler, KesslerGraphics
from .mines import Mine
from .asteroid import Asteroid
from .ship import Ship
from .bullet import Bullet
from .settings_dicts import SettingsDict, UISettingsDict
from .state_models import GameState, ShipState


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
    def __init__(self, settings: SettingsDict | None = None) -> None:
        if settings is None:
            settings = {}
        # Game settings
        self.frequency: float = settings.get("frequency", 30.0)
        self.delta_time: float = 1.0 / settings.get("frequency", 30.0)
        self.perf_tracker: bool = settings.get("perf_tracker", False)
        self.prints_on: bool = settings.get("prints_on", True)
        self.graphics_type: GraphicsType = settings.get("graphics_type", GraphicsType.Tkinter)
        self.graphics_obj: KesslerGraphics | None = settings.get("graphics_obj", None)
        self.realtime_multiplier: float = settings.get("realtime_multiplier", 0.0 if self.graphics_type==GraphicsType.NoGraphics else 1.0)
        self.time_limit: float = settings.get("time_limit", float("inf"))
        self.random_ast_splits: bool = settings.get("random_ast_splits", False)
        self.competition_safe_mode: bool = settings.get("competition_safe_mode", True)

        # UI settings
        default_ui: UISettingsDict = {'ships': True, 'lives_remaining': True, 'accuracy': True,
                      'asteroids_hit': True, 'bullets_remaining': True, 'controller_name': True, 'scale': 1.0}
        UI_settings: UISettingsDict | str = settings.get("UI_settings", default_ui)
        if UI_settings == 'all':
            UI_settings = {'ships': True, 'lives_remaining': True, 'accuracy': True,
                                'asteroids_hit': True, 'shots_fired': True, 'bullets_remaining': True,
                                'controller_name': True, 'scale': 1.0}
        self.UI_settings = cast(UISettingsDict, UI_settings)
        
    def run(self, scenario: Scenario, controllers: list[KesslerController]) -> tuple[Score, PerfDict]:
        """
        Run an entire scenario from start to finish and return score and stop reason
        """

        ##################
        # INITIALIZATION #
        ##################
        # Initialize objects lists from scenario
        asteroids: list[Asteroid] = scenario.asteroids()
        ships: list[Ship] = scenario.ships() # Keep full list of ships (dead or alive) for score reporting
        liveships: list[Ship] = list(ships) # Maintain a parallel list of just live ships
        bullets: list[Bullet] = []
        mines: list[Mine] = []

        # Initialize Scoring class
        score = Score(scenario)

        # Initialize environment parameters
        stop_reason = StopReason.not_stopped
        sim_time: float = 0.0
        sim_frame: int = 0
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
        perf_dict: PerfDict = {
            'controller_times': [0.0] * len(ships),
            'total_controller_time': 0.0,
            'physics_update': 0.0,
            'collisions_check': 0.0,
            'score_update': 0.0,
            'graphics_draw': 0.0,
            'total_frame_time': 0.0
        }

        ######################
        # MAIN SCENARIO LOOP #
        ######################

        new_asteroids: list[Asteroid] = []

        # Maintain game_state dict to send to teams
        game_state: GameState = GameState(
            # Game entities
            ships=[ship.state for ship in liveships],
            asteroids=[asteroid.state for asteroid in asteroids],
            bullets=[bullet.state for bullet in bullets],
            mines=[mine.state for mine in mines],
            # Environment
            map_size=scenario.map_size,
            time_limit=time_limit,
            # Simulation timing
            time=sim_time,
            frame=sim_frame,
            delta_time=self.delta_time,
            frame_rate=self.frequency,
            # Game settings
            random_asteroid_splits=self.random_ast_splits,
            competition_safe_mode=self.competition_safe_mode
        )

        while stop_reason == StopReason.not_stopped:
            # Get perf time at the start of time step evaluation and initialize performance tracker
            step_start = time.perf_counter()

            # --- CALL CONTROLLER FOR EACH SHIP ------------------------------------------------------------------------

            # Initialize controller time recording in performance tracker
            if self.perf_tracker:
                t_start = time.perf_counter()

            # Loop through each controller/ship combo and apply their actions
            for ship_idx, ship in enumerate(liveships):
                # Generate game_state info to send to controller
                game_state_to_controller: GameState
                if self.competition_safe_mode:
                    # Must recreate GameState object, so competitors do not accidentally or maliciously modify the true game state
                    game_state_to_controller = GameState(
                        # Game entities
                        ships=[ship.state for ship in liveships],
                        asteroids=[asteroid.state for asteroid in asteroids],
                        bullets=[bullet.state for bullet in bullets],
                        mines=[mine.state for mine in mines],
                        # Environment
                        map_size=scenario.map_size,
                        time_limit=time_limit,
                        # Simulation timing
                        time=sim_time,
                        frame=sim_frame,
                        delta_time=self.delta_time,
                        frame_rate=self.frequency,
                        # Game settings
                        random_asteroid_splits=self.random_ast_splits,
                        competition_safe_mode=self.competition_safe_mode
                    )
                else:
                    game_state_to_controller = game_state
                # Evaluate each controller letting control be applied
                if controllers[ship_idx].ship_id != ship.id:
                    raise RuntimeError("Controller and ship ID do not match")
                ship.thrust, ship.turn_rate, ship.fire, ship.drop_mine = controllers[ship_idx].actions(ShipState(ship.ownstate), game_state_to_controller)

                # Update controller evaluation time if performance tracking
                if self.perf_tracker:
                    controller_time = time.perf_counter() - t_start if ship.alive else 0.00
                    perf_dict['controller_times'][ship_idx] += controller_time
                    t_start = time.perf_counter()

            if self.perf_tracker:
                perf_dict['total_controller_time'] += time.perf_counter() - step_start
                prev = time.perf_counter()

            # --- UPDATE STATE INFORMATION OF EACH OBJECT --------------------------------------------------------------

            # Update each Asteroid, Bullet, and Ship
            for bullet in bullets:
                bullet.update(self.delta_time)
            for mine in mines:
                mine.update(self.delta_time)
            for asteroid in asteroids:
                asteroid.update(self.delta_time, scenario.map_size)
            for ship in liveships:
                new_bullet, new_mine = ship.update(self.delta_time, scenario.map_size)
                if new_bullet is not None:
                    bullets.append(new_bullet)
                    game_state.add_bullet(new_bullet.state)
                if new_mine is not None:
                    mines.append(new_mine)
                    game_state.add_mine(new_mine.state)

            # Update performance tracker
            if self.perf_tracker:
                perf_dict['physics_update'] += time.perf_counter() - prev
                prev = time.perf_counter()

            # --- CHECK FOR COLLISIONS ---------------------------------------------------------------------------------

            # --- Check bullet-asteroid collisions ---
            bul_idx = 0
            num_buls = len(bullets)
            should_remove_bullet: bool = False
            while bul_idx < num_buls:
                bullet = bullets[bul_idx]
                should_remove_bullet = False
                ast_idx_to_remove: int = -1
                earliest_collision_time: float = math.inf
                for ast_idx, asteroid in enumerate(asteroids):
                    # Iterate through all asteroids, and if multiple collisions occur, find the one that occurs first
                    if circle_line_collision_continuous(
                        bullet.x, bullet.y, bullet.x + bullet.tail_delta_x, bullet.y + bullet.tail_delta_y, bullet.vx, bullet.vy,
                        asteroid.x, asteroid.y, asteroid.vx, asteroid.vy, asteroid.radius, self.delta_time
                    ):
                        collision_start_time, _ = collision_time_interval(bullet.x, bullet.y,
                                                                          bullet.x + bullet.tail_delta_x, bullet.y + bullet.tail_delta_y,
                                                                          bullet.vx, bullet.vy,
                                                                          asteroid.x, asteroid.y,
                                                                          asteroid.vx, asteroid.vy,
                                                                          asteroid.radius)
                        collision_time = max(-self.delta_time, collision_start_time)
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
                    # Mirror the change in the game_state dict
                    game_state.remove_asteroid(ast_idx_to_remove)
                # Cull any bullets past the map edge
                # It is important we do this after the asteroid-bullet collision checks occur,
                # in the case of bullets leaving the map but might hit an asteroid on the edge
                if not ((0.0 <= bullet.x <= scenario.map_size[0] and 0.0 <= bullet.y <= scenario.map_size[1])
                        or (0.0 <= bullet.x + bullet.tail_delta_x <= scenario.map_size[0] and 0.0 <= bullet.y + bullet.tail_delta_y <= scenario.map_size[1])):
                    should_remove_bullet = True
                # O(1) removal of bullet
                if should_remove_bullet:
                    bullet.destruct()
                    bullets[bul_idx] = bullets[-1]
                    bullets.pop()
                    num_buls -= 1
                    # Mirror the change in the game_state dict
                    game_state.remove_bullet(bul_idx)
                else:
                    bul_idx += 1

            # Add the new asteroids from the bullet-asteroid collisions
            if new_asteroids:
                asteroids.extend(new_asteroids)
                game_state.add_asteroids([asteroid.state for asteroid in new_asteroids]) # Mirror change in game_state dict
                new_asteroids.clear()
            
            # --- Check mine-asteroid and mine-ship effects ---
            mine_idx = 0
            num_mines = len(mines)
            while mine_idx < num_mines:
                mine = mines[mine_idx]
                if mine.detonating:
                    ast_idx = 0
                    num_asts = len(asteroids)
                    while ast_idx < num_asts:
                        asteroid = asteroids[ast_idx]
                        dx = asteroid.x - mine.x
                        dy = asteroid.y - mine.y
                        radius_sum = mine.blast_radius + asteroid.radius
                        if dx * dx + dy * dy <= radius_sum * radius_sum:
                            mine.owner.asteroids_hit += 1
                            mine.owner.mines_hit += 1
                            new_asteroids.extend(asteroid.destruct(impactor=mine, random_ast_split=self.random_ast_splits))
                            asteroids[ast_idx] = asteroids[-1]
                            asteroids.pop()
                            num_asts -= 1
                            # Mirror the change in the game_state dict
                            game_state.remove_asteroid(ast_idx)
                            # Don't advance ast_idx, must check the swapped-in asteroid
                        else:
                            ast_idx += 1
                    for ship in liveships:
                        if ship.alive and not ship.is_respawning:
                            dx = ship.x - mine.x
                            dy = ship.y - mine.y
                            radius_sum = mine.blast_radius + ship.radius
                            if dx * dx + dy * dy <= radius_sum * radius_sum:
                                # Ship destruct function.
                                ship.destruct(map_size=scenario.map_size)
                    mine.destruct()
                    # Swap and pop the mine
                    mines[mine_idx] = mines[-1]
                    mines.pop()
                    num_mines -= 1
                    # Mirror the change in the game_state dict
                    game_state.remove_mine(mine_idx)
                    # Don't advance mine_idx, must check the swapped-in mine
                else:
                    mine_idx += 1

            # Add new asteroids from mine-asteroid collisions
            if new_asteroids:
                asteroids.extend(new_asteroids)
                game_state.add_asteroids([asteroid.state for asteroid in new_asteroids]) # Mirror change in game_state dict
                new_asteroids.clear()
            
            # --- Check ship-asteroid collisions ---
            for ship in liveships:
                if ship.alive and not ship.is_respawning:
                    ast_idx = 0
                    num_asts = len(asteroids)
                    while ast_idx < num_asts:
                        asteroid = asteroids[ast_idx]
                        dx = ship.x - asteroid.x
                        dy = ship.y - asteroid.y
                        radius_sum = ship.radius + asteroid.radius
                        # Most of the time no collision occurs, so use early exit to optimize collision check
                        if abs(dx) <= radius_sum and abs(dy) <= radius_sum and dx * dx + dy * dy <= radius_sum * radius_sum:
                            # Asteroid destruct function and immediate removal
                            new_asteroids.extend(asteroid.destruct(impactor=ship, random_ast_split=self.random_ast_splits))
                            asteroids[ast_idx] = asteroids[-1]
                            asteroids.pop()
                            num_asts -= 1
                            # Mirror the change in the game_state dict
                            game_state.remove_asteroid(ast_idx)
                            # Ship destruct function. Add one to asteroids_hit
                            ship.asteroids_hit += 1
                            ship.destruct(map_size=scenario.map_size)
                            # Stop checking this ship's collisions
                            break
                        else:
                            ast_idx += 1
            
            # Add new asteroids from ship-asteroid collisions
            if new_asteroids:
                asteroids.extend(new_asteroids)
                game_state.add_asteroids([asteroid.state for asteroid in new_asteroids]) # Mirror change in game_state dict
                new_asteroids.clear()
            
            # --- Check ship-ship collisions ---
            for ship_idx, ship1 in enumerate(liveships):
                if ship1.alive:
                    for ship2 in liveships[ship_idx + 1:]:
                        if ship2.alive:
                            if not ship2.is_respawning and not ship1.is_respawning:
                                dx = ship1.x - ship2.x
                                dy = ship1.y - ship2.y
                                radius_sum = ship1.radius + ship2.radius
                                # Most of the time no collision occurs, so use early exit to optimize collision check
                                if abs(dx) <= radius_sum and abs(dy) <= radius_sum and dx * dx + dy * dy <= radius_sum * radius_sum:
                                    ship1.destruct(map_size=scenario.map_size)
                                    ship2.destruct(map_size=scenario.map_size)
            # Cull ships if not alive
            liveships = [ship for ship in liveships if ship.alive]

            # Update performance tracker with collisions timing
            if self.perf_tracker:
                perf_dict['collisions_check'] += time.perf_counter() - prev
                prev = time.perf_counter()

                # --- UPDATE SCORE CLASS -----------------------------------------------------------------------------------
                score.update(ships, sim_time, perf_dict['controller_times'])

                # Update performance tracker with score timing
                perf_dict['score_update'] += time.perf_counter() - prev
                prev = time.perf_counter()
            else:
                score.update(ships, sim_time)


            # --- UPDATE GRAPHICS --------------------------------------------------------------------------------------
            graphics.update(score, ships, asteroids, bullets, mines)

            # Update performance tracker with graphics timing
            if self.perf_tracker:
                perf_dict['graphics_draw'] += time.perf_counter() - prev
                prev = time.perf_counter()

            # --- CHECK STOP CONDITIONS --------------------------------------------------------------------------------
            sim_time += self.delta_time
            game_state.time = sim_time
            sim_frame += 1
            game_state.frame = sim_frame

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
                perf_dict['total_frame_time'] += time.perf_counter() - step_start

            # Hold simulation so that it runs at realtime ratio if specified, else let it pass
            if self.realtime_multiplier != 0.0:
                time_dif = time.perf_counter() - step_start
                while time_dif < self.delta_time / self.realtime_multiplier:
                    time_dif = time.perf_counter() - step_start

        ############################################
        # Finalization after scenario has been run #
        ############################################

        # Close graphics display
        graphics.close()

        # Finalize score class before returning
        score.finalize(sim_time, stop_reason, ships)

        # Return the score and stop condition
        return score, perf_dict


class TrainerEnvironment(KesslerGame):
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        """
        Instantiates a KesslerGame object with settings to optimize training time
        """
        if settings is None:
            settings = {}
        trainer_settings: SettingsDict = {
            'frequency': settings.get("frequency", 30.0),
            'perf_tracker': settings.get("perf_tracker", False),
            'prints_on': settings.get("prints_on", False),
            'graphics_type': GraphicsType.NoGraphics,
            'realtime_multiplier': 0,
            'time_limit': settings.get("time_limit", float("inf"))
        }
        super().__init__(trainer_settings)
