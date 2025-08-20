# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import Any
import random
from math import isclose, hypot, degrees, radians, atan2, cos, sin

from .ship import Ship
from .asteroid import Asteroid
from .validate import validate_scenario_params


def wrap_asteroid(asteroid_dict: dict[str, Any], map_size: tuple[int, int]) -> dict[str, Any]:
    """
    Wrap the asteroid inbounds.
    Scenarios may be validly defined with asteroids out of bounds, and in these cases, the AI agent will see
    the asteroids out of bounds on frame 0, and inbounds (wrapped) on all subsequent frames.
    By wrapping the asteroids as a preprocessing stage, the agents can always assume asteroids are inbounds,
    reducing confusion, especially on the first critical frame of analyzing the map situation.
    """
    if "position" not in asteroid_dict:
        # Invalid asteroid, do not process
        return asteroid_dict
    x, y = asteroid_dict["position"]
    width, height = map_size
    x %= width
    y %= height
    asteroid_dict["position"] = (x, y)
    return asteroid_dict


def nudge_asteroid_away_from_border(asteroid_dict: dict[str, Any], map_size: tuple[int, int]) -> dict[str, Any]:
    """
    Due to the way the wrapping is done, it's possible for asteroids to oscillate between a boundary instead of smoothly passing through.
    For example, an asteroid with initial state {"position": (0, 0), "angle": 360.0, "speed": 100}
    in a 1000x800 map will cycle its y coordinate between 0.0 and 800.0

    This function preprocesses each asteroid state to avoid these initial states that cause oscillation,
    by taking asteroids exactly on the boundary and nudging them away.
    Not a perfect fix, and given enough time the asteroids may begin oscillating anyway, but this eliminates 99.9% of an issue which already was incredibly rare.
    """
    if "position" not in asteroid_dict:
        # Invalid asteroid, do not process
        return asteroid_dict
    x, y = asteroid_dict["position"]
    width, height = map_size
    speed = asteroid_dict["speed"]
    angle = radians(asteroid_dict["angle"])
    vx, vy = speed * cos(angle), speed * sin(angle)
    EPS = 1e-10
    # Check and nudge X
    if isclose(vx, 0.0, abs_tol=1e-14):
        if isclose(x, 0.0, abs_tol=1e-14):
            x += EPS
        elif isclose(x, width, abs_tol=1e-14):
            x -= EPS

    # Check and nudge Y
    if isclose(vy, 0.0, abs_tol=1e-14):
        if isclose(y, 0.0, abs_tol=1e-14):
            y += EPS
        elif isclose(y, height, abs_tol=1e-14):
            y -= EPS

    asteroid_dict["position"] = (x, y)
    return asteroid_dict


class Scenario:
    def __init__(
        self,
        name: str = "Scenario",
        num_asteroids: int | None = None,
        asteroid_states: list[dict[str, Any]] | None = None,
        ship_states: list[dict[str, Any]] | None = None,
        map_size: tuple[int, int] | None = None,
        seed: int | None = None,
        time_limit: float | None = None,
        ammo_limit_multiplier: float | None = None,
        bullet_limit: int | None = None,
        mine_limit: int | None = None,
        stop_if_no_ammo: bool | None = None,
        stop_if_no_asteroids: bool | None = None,
        stop_if_no_ships: bool | None = None
    ) -> None:
        """
        Represents the configuration and initial state of a game scenario,
        including ships, asteroids, map size, ammo limits, and victory conditions.

        Make sure to only set either 'num_asteroids' or 'asteroid_states'.

        :param name: Optional, name of the scenario
        :param num_asteroids: Optional, Number of asteroids
        :param asteroid_states: Optional, list of dictionaries representing asteroid starting states
        :param ship_states: Optional, Ship Starting states (list of dictionaries)
        :param seed: Optional seeding value to pass to random.seed() which is called before asteroid creation
        :param time_limit: Optional value for limiting the total duration of the scenario, will be set to infinity if 0 or not defined
        :param ammo_limit_multiplier: Optional value for limiting the number of bullets each ship will have
        :param stop_if_no_ammo: Optional flag for stopping the scenario if all ships run out of ammo
        :param stop_if_no_asteroids: Optional flag for stopping the scenario if no asteroids remain
        :param stop_if_no_ships: Optional flag for stopping the scenario if no ships remain
        """

        # Validate and coerce scenario params (dict of all fields except self)
        params = {
            "name": name,
            "num_asteroids": num_asteroids,
            "asteroid_states": asteroid_states,
            "ship_states": ship_states,
            "map_size": map_size,
            "seed": seed,
            "time_limit": time_limit,
            "ammo_limit_multiplier": ammo_limit_multiplier,
            "bullet_limit": bullet_limit,
            "mine_limit": mine_limit,
            "stop_if_no_ammo": stop_if_no_ammo,
            "stop_if_no_asteroids": stop_if_no_asteroids,
            "stop_if_no_ships": stop_if_no_ships,
        }
        # Remove keys where the argument is None
        params = {k: v for k, v in params.items() if v is not None}
        validated = validate_scenario_params(params)

        # Assign all validated/canonical values
        self._name: str = validated["name"]
        self.map_size: tuple[int, int] = validated["map_size"]
        self.asteroid_states: list[dict[str, Any]] = validated["asteroid_states"]
        self.ship_states: list[dict[str, Any]] = validated["ship_states"]
        self.seed: int | None = validated["seed"]
        self.time_limit: float | None = validated["time_limit"]
        self._ammo_limit_multiplier: float | None = validated["ammo_limit_multiplier"]
        self.bullet_limit: int | None = validated["bullet_limit"]
        self.mine_limit: int | None = validated["mine_limit"]
        self.stop_if_no_ammo: bool = validated["stop_if_no_ammo"]
        self.stop_if_no_asteroids: bool = validated["stop_if_no_asteroids"]
        self.stop_if_no_ships: bool = validated["stop_if_no_ships"]

        # If using ammo_limit_multiplier, estimate bullets now if not provided
        if self._ammo_limit_multiplier is not None and self.bullet_limit is None:
            if self._ammo_limit_multiplier == 0.0:
                self.bullet_limit = -1  # Unlimited
            else:
                estimated_asteroid_count = sum(
                    Scenario.count_asteroids(ast.get("size", 3)) for ast in self.asteroid_states
                )
                self.bullet_limit = max(0, round(estimated_asteroid_count * self._ammo_limit_multiplier))

        # Inject bullet/mine limits into ships, if global limit provided and not set in ship
        for ship in self.ship_states:
            if self.bullet_limit is not None and "bullets_remaining" not in ship:
                ship["bullets_remaining"] = self.bullet_limit
            if self.mine_limit is not None and "mines_remaining" not in ship:
                ship["mines_remaining"] = self.mine_limit

    @property
    def name(self) -> str | None:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        if not isinstance(name, str):
            raise ValueError(f"Scenario name must be a string, got {type(name).__name__}")
        self._name = name

    @property
    def num_starting_asteroids(self) -> float:
        return len(self.asteroid_states)

    @property
    def is_random(self) -> bool:
        """
        Indicates whether the scenario has randomized asteroids.
        Returns True if any asteroid state is unspecified (empty dict), else False.
        """
        return any(not state for state in self.asteroid_states)

    @property
    def max_asteroids(self) -> int:
        return sum([Scenario.count_asteroids(asteroid.size) for asteroid in self.asteroids()])

    @property
    def map_width(self) -> int:
        return self.map_size[0]

    @property
    def map_height(self) -> int:
        return self.map_size[1]

    @staticmethod
    def count_asteroids(asteroid_size: int) -> int:
        # Counting based off of each asteroid making 3 children when destroyed
        return sum([3 ** (size - 1) for size in range(1, asteroid_size + 1)])

    def asteroids(self) -> list[Asteroid]:
        """
        Create asteroid instances based on initial state definitions.
        :return: list of Asteroids
        """
        asteroids = []

        # Seed the random number generator via an optionally defined user seed
        if self.seed is not None:
            random.seed(self.seed)

        # Loop through and create AsteroidSprites based on starting state
        for asteroid_state in self.asteroid_states:
            if asteroid_state:  # Not an empty dictionary
                # Copy to avoid mutating original input
                asteroid_state = dict(asteroid_state)

                has_velocity = "velocity" in asteroid_state
                has_speed = "speed" in asteroid_state
                has_angle = "angle" in asteroid_state

                if has_velocity:
                    assert not (has_speed or has_angle)
                    vx, vy = asteroid_state.pop("velocity")
                    speed = hypot(vx, vy)
                    angle = degrees(atan2(vy, vx)) % 360.0
                    asteroid_state["speed"] = speed
                    asteroid_state["angle"] = angle

                # No need to change anything if velocity wasn't specified,
                # because the Asteroid constructor handles optional speed/angle

                # Apply position preprocessing as needed
                asteroid_state = wrap_asteroid(asteroid_state, self.map_size)
                if "speed" in asteroid_state and "angle" in asteroid_state:
                    asteroid_state = nudge_asteroid_away_from_border(asteroid_state, self.map_size)

                # Create the asteroid object
                asteroids.append(Asteroid(**asteroid_state))
            else:
                # Empty dict. Initialize a default random asteroid.
                asteroids.append(
                    Asteroid(
                        position=(
                            random.randrange(0, self.map_size[0]),
                            random.randrange(0, self.map_size[1])),
                    )
                )

        return asteroids

    def ships(self) -> list[Ship]:
        """
        Create ship game objects
        :return: list of Ship objects
        """
        # Loop through and create ShipSprites based on starting state
        return [Ship(idx + 1, **ship_state) for idx, ship_state in enumerate(self.ship_states)]
