# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import json
from typing import Literal, overload, cast, Iterator, Any, TypedDict

class AsteroidStateDict(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    size: int
    mass: float
    radius: float


class BulletStateDict(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    tail_delta: tuple[float, float]
    heading: float
    mass: float
    length: float


class MineStateDict(TypedDict):
    position: tuple[float, float]
    mass: float
    fuse_time: float
    remaining_time: float


class ShipStateDict(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    speed: float
    heading: float
    mass: float
    radius: float
    id: int
    team: int
    is_respawning: bool
    lives_remaining: int
    deaths: int


class ShipOwnStateDict(ShipStateDict):
    bullets_remaining: int
    mines_remaining: int
    can_fire: bool
    fire_cooldown: float
    fire_rate: float
    can_deploy_mine: bool
    mine_cooldown: float
    mine_deploy_rate: float
    respawn_time_left: float
    respawn_time: float
    thrust_range: tuple[float, float]
    turn_rate_range: tuple[float, float]
    max_speed: float
    drag: float


class GameStateDict(TypedDict):
    ships: list[ShipStateDict]
    asteroids: list[AsteroidStateDict]
    bullets: list[BulletStateDict]
    mines: list[MineStateDict]
    map_size: tuple[int, int]
    time_limit: float
    time: float
    frame: int
    delta_time: float
    frame_rate: float
    random_asteroid_splits: bool
    competition_safe_mode: bool


class GameStateCompactDict(TypedDict):
    ships: list[list[float | int | bool]]
    asteroids: list[list[float | int]]
    bullets: list[list[float]]
    mines: list[list[float]]
    map_size: tuple[int, int]
    time_limit: float
    time: float
    frame: int
    delta_time: float
    frame_rate: float
    random_asteroid_splits: bool
    competition_safe_mode: bool


class AsteroidView:
    def __init__(self, data: list[float]):
        # [x: float, y: float, vx: float, vy: float, size: int, mass: float, radius: float]
        self._data = data

    @property
    def x(self) -> float:
        return self._data[0]

    @property
    def y(self) -> float:
        return self._data[1]

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def vx(self) -> float:
        return self._data[2]

    @property
    def vy(self) -> float:
        return self._data[3]

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    @property
    def size(self) -> int:
        return int(self._data[4])

    @property
    def mass(self) -> float:
        return self._data[5]

    @property
    def radius(self) -> float:
        return self._data[6]

    def dict(self) -> AsteroidStateDict:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "size": self.size,
            "mass": self.mass,
            "radius": self.radius,
        }

    @overload
    def __getitem__(self, key: Literal["x", "y", "vx", "vy", "mass", "radius"]) -> float: ...
    
    @overload
    def __getitem__(self, key: Literal["size"]) -> int: ...

    @overload
    def __getitem__(self, key: Literal["position", "velocity"]) -> tuple[float, float]: ...

    def __getitem__(self, key: str) -> float | int | tuple[float, float]:
        return cast(float | int | tuple[float, float], getattr(self, key))

    def __repr__(self) -> str:
        return f"<AsteroidView pos={self.position} vel={self.velocity} size={self.size} mass={self.mass} radius={self.radius}>"


class BulletView:
    def __init__(self, data: list[float]):
        # [x: float, y: float, vx: float, vy: float, tail_dx: float, tail_dy: float, heading: float, mass: float, length: float]
        self._data = data

    @property
    def x(self) -> float:
        return self._data[0]

    @property
    def y(self) -> float:
        return self._data[1]

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def vx(self) -> float:
        return self._data[2]

    @property
    def vy(self) -> float:
        return self._data[3]

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    @property
    def tail_dx(self) -> float:
        return self._data[4]

    @property
    def tail_dy(self) -> float:
        return self._data[5]

    @property
    def tail_delta(self) -> tuple[float, float]:
        return (self.tail_dx, self.tail_dy)

    @property
    def tail(self) -> tuple[float, float]:
        return (self.x + self.tail_dx, self.y + self.tail_dy)

    @property
    def heading(self) -> float:
        return self._data[6]

    @property
    def mass(self) -> float:
        return self._data[7]

    @property
    def length(self) -> float:
        return self._data[8]

    def dict(self) -> BulletStateDict:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "tail_delta": self.tail_delta,
            "heading": self.heading,
            "mass": self.mass,
            "length": self.length
        }

    @overload
    def __getitem__(self, key: Literal["x", "y", "vx", "vy", "tail_dx", "tail_dy", "heading", "mass", "length"]) -> float: ...
    
    @overload
    def __getitem__(self, key: Literal["position", "velocity", "tail_delta"]) -> tuple[float, float]: ...

    def __getitem__(self, key: str) -> float | tuple[float, float]:
        return cast(float | tuple[float, float], getattr(self, key))

    def __repr__(self) -> str:
        return (f"<BulletView pos={self.position} vel={self.velocity} "
                f"tail_delta={self.tail_delta} "
                f"heading={self.heading:.1f} mass={self.mass} length={self.length}>")


class MineView:
    def __init__(self, data: list[float]):
        # [x: float, y: float, mass: float, fuse_time: float, remaining_time: float]
        self._data = data

    @property
    def x(self) -> float:
        return self._data[0]

    @property
    def y(self) -> float:
        return self._data[1]

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def mass(self) -> float:
        return self._data[2]

    @property
    def fuse_time(self) -> float:
        return self._data[3]

    @property
    def remaining_time(self) -> float:
        return self._data[4]

    def dict(self) -> MineStateDict:
        return {
            "position": self.position,
            "mass": self.mass,
            "fuse_time": self.fuse_time,
            "remaining_time": self.remaining_time,
        }

    @overload
    def __getitem__(self, key: Literal["x", "y", "mass", "fuse_time", "remaining_time"]) -> float: ...
    
    @overload
    def __getitem__(self, key: Literal["position"]) -> tuple[float, float]: ...

    def __getitem__(self, key: str) -> float | tuple[float, float]:
        return cast(float | tuple[float, float], getattr(self, key))

    def __str__(self) -> str:
        return f"<MineView pos={self.position} remaining={self.remaining_time:.2f}>"


class ShipView:
    def __init__(self, data: list[float | int]):
        # [x, y, vx, vy, speed, heading, mass, radius, id, team, is_respawning, lives_remaining, deaths]
        self._data = data

    @property
    def x(self) -> float:
        return self._data[0]

    @property
    def y(self) -> float:
        return self._data[1]

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def vx(self) -> float:
        return self._data[2]

    @property
    def vy(self) -> float:
        return self._data[3]

    @property
    def velocity(self) -> tuple[float, float]:
        return (self.vx, self.vy)

    @property
    def speed(self) -> float:
        return self._data[4]

    @property
    def heading(self) -> float:
        return self._data[5]

    @property
    def mass(self) -> float:
        return self._data[6]

    @property
    def radius(self) -> float:
        return self._data[7]

    @property
    def id(self) -> int:
        return int(self._data[8])

    @property
    def team(self) -> int:
        return int(self._data[9])

    @property
    def is_respawning(self) -> bool:
        return bool(self._data[10])

    @property
    def lives_remaining(self) -> int:
        return int(self._data[11])

    @property
    def deaths(self) -> int:
        return int(self._data[12])

    def dict(self) -> ShipStateDict:
        return {
            "position": self.position,
            "velocity": self.velocity,
            "speed": self.speed,
            "heading": self.heading,
            "mass": self.mass,
            "radius": self.radius,
            "id": self.id,
            "team": self.team,
            "is_respawning": self.is_respawning,
            "lives_remaining": self.lives_remaining,
            "deaths": self.deaths,
        }

    @overload
    def __getitem__(self, key: Literal[
        "x", "y", "vx", "vy", "speed", "heading", "mass", "radius"
    ]) -> float: ...

    @overload
    def __getitem__(self, key: Literal[
        "id", "team", "lives_remaining", "deaths"
    ]) -> int: ...

    @overload
    def __getitem__(self, key: Literal["is_respawning"]) -> bool: ...

    @overload
    def __getitem__(self, key: Literal["position", "velocity"]) -> tuple[float, float]: ...

    def __getitem__(self, key: str) -> float | int | bool | tuple[float, float]:
        return cast(float | int | bool | tuple[float, float], getattr(self, key))

    def __str__(self) -> str:
        return (f"<ShipView id={self.id} team={self.team} pos={self.position} "
                f"vel={self.velocity} speed={self.speed:.2f} heading={self.heading:.1f} "
                f"lives={self.lives_remaining} deaths={self.deaths} respawning={self.is_respawning}>")


class ShipOwnView(ShipView):
    def __init__(self, data: list[float | int | bool]):
        # Extend ShipView list with the following:
        # [bullets_remaining: int, mines_remaining: int, can_fire: bool, fire_cooldown: float, fire_rate: float,
        #  can_deploy_mine: bool, mine_cooldown: float, mine_deploy_rate: float, respawn_time_left: float, respawn_time: float,
        #  thrust_min: float, thrust_max: float, turn_rate_min: float, turn_rate_max: float, max_speed: float, drag: float]
        super().__init__(data)
        self._own_data = data

    @property
    def bullets_remaining(self) -> int:
        return int(self._own_data[13])

    @property
    def mines_remaining(self) -> int:
        return int(self._own_data[14])

    @property
    def can_fire(self) -> bool:
        return bool(self._own_data[15])

    @property
    def fire_cooldown(self) -> float:
        return self._own_data[16]

    @property
    def fire_rate(self) -> float:
        return self._own_data[17]

    @property
    def can_deploy_mine(self) -> bool:
        return bool(self._own_data[18])

    @property
    def mine_cooldown(self) -> float:
        return self._own_data[19]

    @property
    def mine_deploy_rate(self) -> float:
        return self._own_data[20]

    @property
    def respawn_time_left(self) -> float:
        return self._own_data[21]

    @property
    def respawn_time(self) -> float:
        return self._own_data[22]

    @property
    def thrust_range(self) -> tuple[float, float]:
        return (self._own_data[23], self._own_data[24])

    @property
    def turn_rate_range(self) -> tuple[float, float]:
        return (self._own_data[25], self._own_data[26])

    @property
    def max_speed(self) -> float:
        return self._own_data[27]

    @property
    def drag(self) -> float:
        return self._own_data[28]

    @overload
    def __getitem__(self, key: Literal[
        "x", "y", "vx", "vy", "speed", "heading", "mass", "radius",
        "fire_cooldown", "fire_rate", "mine_cooldown", "mine_deploy_rate",
        "respawn_time_left", "respawn_time", "max_speed", "drag"
    ]) -> float: ...

    @overload
    def __getitem__(self, key: Literal[
        "id", "team", "lives_remaining", "deaths", "bullets_remaining", "mines_remaining"
    ]) -> int: ...

    @overload
    def __getitem__(self, key: Literal[
        "is_respawning", "can_fire", "can_deploy_mine"
    ]) -> bool: ...

    @overload
    def __getitem__(self, key: Literal[
        "position", "velocity", "thrust_range", "turn_rate_range"
    ]) -> tuple[float, float]: ...

    def __getitem__(self, key: str) -> float | int | bool | tuple[float, float]:
        return cast(float | int | bool | tuple[float, float], getattr(self, key))


class ShipState:
    """
    Wrapper around a single ship's data list, exposing a dict-like interface.

    Behaves like a read-only dictionary mapping property names to values, and
    internally wraps a ShipOwnView (which extends ShipView).
    """

    def __init__(self, ship: list[float | int]):
        self._ship_data = ship
        self._view = ShipOwnView(ship)

    def __getitem__(self, key: str) -> float | int | bool | tuple[float, float]:
        """Allow dict-style access to view attributes."""
        if hasattr(self._view, key):
            return cast(float | int | bool | tuple[float, float], getattr(self._view, key))
        raise KeyError(f"Key '{key}' not found in ship state.")

    def __repr__(self) -> str:
        return repr(self._view)

    def keys(self) -> list[str]:
        """Returns all accessible attribute names."""
        return [
            k for k in dir(self._view)
            if not k.startswith("_") and not callable(getattr(self._view, k))
        ]

    def items(self) -> list[tuple[str, float | int | bool | tuple[float, float]]]:
        """Returns all (key, value) pairs."""
        return [(k, getattr(self._view, k)) for k in self.keys()]

    def get_raw(self) -> list[float | int]:
        """Return the underlying ship list (mutable)."""
        return self._ship_data

    def __contains__(self, key: str) -> bool:
        return hasattr(self._view, key)

    def __len__(self) -> int:
        return len(self.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

class GameState:
    def __init__(self,
                 ships: list[list[float | int]],
                 asteroids: list[list[float | int]],
                 bullets: list[list[float]],
                 mines: list[list[float]],
                 map_size: tuple[int, int],
                 time_limit: float,
                 time: float,
                 frame: int,
                 delta_time: float,
                 frame_rate: float,
                 random_asteroid_splits: bool,
                 competition_safe_mode: bool):
        # Game entities
        self._ship_data = ships
        self._asteroid_data = asteroids
        self._bullet_data = bullets
        self._mine_data = mines
        # Environment
        self._map_size = map_size
        self._time_limit = time_limit
        # Simulation timing
        self._time = time
        self._frame = frame
        self._delta_time = delta_time
        self._frame_rate = frame_rate
        # Game settings
        self._random_asteroid_splits = random_asteroid_splits
        self._competition_safe_mode = competition_safe_mode

    @property
    def ships(self) -> list[ShipView]:
        return [ShipView(data) for data in self._ship_data]

    @property
    def asteroids(self) -> list[AsteroidView]:
        return [AsteroidView(data) for data in self._asteroid_data]

    @property
    def bullets(self) -> list[BulletView]:
        return [BulletView(data) for data in self._bullet_data]

    @property
    def mines(self) -> list[MineView]:
        return [MineView(data) for data in self._mine_data]

    @property
    def time(self) -> float:
        return self._time

    @time.setter
    def time(self, value: float) -> None:
        self._time = value

    @property
    def frame(self) -> int:
        return self._frame

    @frame.setter
    def frame(self, value: int) -> None:
        self._frame = value

    @property
    def delta_time(self) -> float:
        return self._delta_time

    @property
    def frame_rate(self) -> float:
        return self._frame_rate

    @property
    def map_size(self) -> tuple[int, int]:
        return self._map_size

    @property
    def time_limit(self) -> float:
        return self._time_limit

    @property
    def random_asteroid_splits(self) -> bool:
        return self._random_asteroid_splits

    @property
    def competition_safe_mode(self) -> bool:
        return self._competition_safe_mode

    def add_asteroid(self, asteroid_data: list[float | int]) -> None:
        self._asteroid_data.append(asteroid_data)

    def add_asteroids(self, asteroid_list: list[list[float | int]]) -> None:
        self._asteroid_data.extend(asteroid_list)

    def add_bullet(self, bullet_data: list[float]) -> None:
        self._bullet_data.append(bullet_data)

    def add_mine(self, mine_data: list[float]) -> None:
        self._mine_data.append(mine_data)

    def update_ships(self, ships_data: list[list[float | int | bool]]) -> None:
        self._ship_data = ships_data

    def remove_asteroid(self, index: int) -> None:
        """Remove asteroid at index using swap-and-pop O(1)"""
        last_index = len(self._asteroid_data) - 1
        if index < 0 or index > last_index:
            raise IndexError(f"Invalid asteroid index: {index}")
        # Swap the element at index with the end
        self._asteroid_data[index], self._asteroid_data[last_index] = self._asteroid_data[last_index], self._asteroid_data[index]
        # Pop the last element
        self._asteroid_data.pop()

    def remove_bullet(self, index: int) -> None:
        """Remove bullet at index using swap-and-pop O(1)"""
        last_index = len(self._bullet_data) - 1
        if index < 0 or index > last_index:
            raise IndexError(f"Invalid bullet index: {index}")
        self._bullet_data[index], self._bullet_data[last_index] = self._bullet_data[last_index], self._bullet_data[index]
        self._bullet_data.pop()

    def remove_mine(self, index: int) -> None:
        """Remove mine at index using swap-and-pop O(1)"""
        last_index = len(self._mine_data) - 1
        if index < 0 or index > last_index:
            raise IndexError(f"Invalid mine index: {index}")
        self._mine_data[index], self._mine_data[last_index] = self._mine_data[last_index], self._mine_data[index]
        self._mine_data.pop()

    def remove_ship(self, index: int) -> None:
        """Remove ship at index using swap-and-pop O(1)"""
        last_index = len(self._ship_data) - 1
        if index < 0 or index > last_index:
            raise IndexError(f"Invalid ship index: {index}")
        self._ship_data[index], self._ship_data[last_index] = self._ship_data[last_index], self._ship_data[index]
        self._ship_data.pop()

    def __getitem__(self, key: str) -> list[AsteroidView] | list[BulletView] | list[MineView] | list[ShipView] | tuple[int, int] | float | int | bool:
        match key:
            case "asteroids":
                return self.asteroids
            case "bullets":
                return self.bullets
            case "mines":
                return self.mines
            case "ships":
                return self.ships
            case "map_size":
                return self.map_size
            case "time":
                return self.time
            case "delta_time":
                return self.delta_time
            case "frame_rate":
                return self.frame_rate
            case "frame":
                return self.frame
            case "time_limit":
                return self.time_limit
            case "random_asteroid_splits":
                return self.random_asteroid_splits
            case "competition_safe_mode":
                return self.competition_safe_mode
            case _:
                raise KeyError(f"Key '{key}' not found in GameState")

    def __repr__(self) -> str:
        return (f"<GameState frame={self.frame} time={self.time:.2f}s "
                f"asteroids={len(self._asteroid_data)} "
                f"ships={len(self._ship_data)} bullets={len(self._bullet_data)} "
                f"mines={len(self._mine_data)}>")

    def __str__(self) -> str:
        return (f"GameState @ frame {self.frame} ({self.time:.2f}s)\n"
                f"  Asteroids: {len(self._asteroid_data)}\n"
                f"  Ships:     {len(self._ship_data)}\n"
                f"  Bullets:   {len(self._bullet_data)}\n"
                f"  Mines:     {len(self._mine_data)}\n")

    def dict(self) -> GameStateDict:
        """Return a plain dictionary representation of the game state."""
        return {
            "ships": [ShipView(ship_data).dict() for ship_data in self._ship_data],
            "asteroids": [AsteroidView(asteroid_data).dict() for asteroid_data in self._asteroid_data],
            "bullets": [BulletView(bullet_data).dict() for bullet_data in self._bullet_data],
            "mines": [MineView(mine_data).dict() for mine_data in self._mine_data],
            "map_size": self._map_size,
            "time_limit": self._time_limit,
            "time": self._time,
            "frame": self._frame,
            "delta_time": self._delta_time,
            "frame_rate": self._frame_rate,
            "random_asteroid_splits": self._random_asteroid_splits,
            "competition_safe_mode": self._competition_safe_mode,
        }
    
    def fast_compact(self) -> GameStateCompactDict:
        """Return a minimal raw list-based version of the game state for fast serialization. Recommended for agent training."""
        return {
            "ships": self._ship_data,
            "asteroids": self._asteroid_data,
            "bullets": self._bullet_data,
            "mines": self._mine_data,
            "map_size": self._map_size,
            "time_limit": self._time_limit,
            "time": self._time,
            "frame": self._frame,
            "delta_time": self._delta_time,
            "frame_rate": self._frame_rate,
            "random_asteroid_splits": self._random_asteroid_splits,
            "competition_safe_mode": self._competition_safe_mode,
        }


def run_tests() -> None:
    print("=== Testing AsteroidView ===")
    asteroid_data = [100.0, 200.0, 1.5, -0.5, 3, 150.0, 24.0]
    asteroid = AsteroidView(asteroid_data)
    print(asteroid)
    print("Position:", asteroid.position)
    print("Velocity:", asteroid.velocity)
    print("Size:", asteroid.size)
    print("Mass via __getitem__:", asteroid["mass"])
    print()

    print("=== Testing BulletView ===")
    bullet_data = [300.0, 400.0, 5.0, 5.5, 45.0, 10.0, 0.0, 0.0, 20.0]
    bullet = BulletView(bullet_data)
    print(bullet)
    print("Position:", bullet.position)
    print("Velocity:", bullet.velocity)
    print("Heading:", bullet.heading)
    print("Mass via __getitem__:", bullet["mass"])
    print()

    print("=== Testing MineView ===")
    mine_data = [500.0, 600.0, 50.0, 10.0, 7.5]
    mine = MineView(mine_data)
    print(mine)
    print("Position:", mine.position)
    print("Mass:", mine.mass)
    print("Fuse Time:", mine.fuse_time)
    print("Remaining Time via __getitem__:", mine["remaining_time"])
    print()

    print("=== Testing ShipView ===")
    ship_data = [
        700.0, 800.0,       # position x,y
        2.0, 3.0,           # velocity x,y
        3.6,                # speed
        90.0,               # heading
        100.0,              # mass
        15.0,               # radius
        1,                  # id
        2,                  # team
        False,              # is_respawning
        3,                  # lives_remaining
        1                   # deaths
    ]
    ship = ShipView(ship_data)
    print(ship)
    print("Position:", ship.position)
    print("Velocity:", ship.velocity)
    print("Is respawning:", ship.is_respawning)
    print("Lives remaining:", ship.lives_remaining)
    print("ID via __getitem__:", ship["id"])
    print()

    print("=== Testing ShipOwnView ===")
    ship_own_data = ship_data + [
        10,                 # bullets_remaining
        2,                  # mines_remaining
        True,               # can_fire
        0.5,                # fire_cooldown
        1.0,                # fire_rate
        True,               # can_deploy_mine
        0.3,                # mine_cooldown
        1.2,                # mine_deploy_rate
        5.0,                # respawn_time_left
        10.0,               # respawn_time
        0.1, 0.5,           # thrust_range (min, max)
        5.0, 10.0,          # turn_rate_range (min, max)
        20.0,               # max_speed
        0.05                # drag
    ]
    ship_own = ShipOwnView(ship_own_data)
    print(ship_own)
    print("Bullets remaining:", ship_own.bullets_remaining)
    print("Can fire:", ship_own.can_fire)
    print("Thrust range:", ship_own.thrust_range)
    print("Drag via __getitem__:", ship_own["drag"])
    print()

    print("=== Testing GameState ===")
    gs = GameState(
        asteroids=[asteroid_data],
        ships=[ship_data],
        bullets=[bullet_data],
        mines=[mine_data],
        map_size=(1024, 768),
        time=123.45,
        delta_time=1/30,
        frame_rate=30,
        frame=1234,
        time_limit=300.0,
        random_asteroid_splits=True,
        competition_safe_mode=False,
    )
    print(gs)
    print(str(gs))
    print("Asteroids in game state:", len(gs.asteroids))
    print("First asteroid position:", gs.asteroids[0].position)
    print()

if __name__ == "__main__":
    run_tests()
