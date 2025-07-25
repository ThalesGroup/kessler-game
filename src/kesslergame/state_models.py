# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations
from typing import Literal, overload, cast, Iterator, TypedDict, TypeAlias, Any
import builtins
import copy


ShipDataList: TypeAlias = list[float | int | bool]
AsteroidDataList: TypeAlias = list[float | int]
BulletDataList: TypeAlias = list[float]
MineDataList: TypeAlias = list[float]


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
    ships: list[ShipDataList]
    asteroids: list[AsteroidDataList]
    bullets: list[BulletDataList]
    mines: list[MineDataList]
    map_size: tuple[int, int]
    time_limit: float
    time: float
    frame: int
    delta_time: float
    frame_rate: float
    random_asteroid_splits: bool
    competition_safe_mode: bool


class AsteroidView:
    __slots__ = ("_data",)

    def __init__(self, data: AsteroidDataList):
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
        assert(isinstance(self._data[4], int))
        return self._data[4]

    @property
    def mass(self) -> float:
        return self._data[5]

    @property
    def radius(self) -> float:
        return self._data[6]

    @property
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

    def __format__(self, format_spec: str) -> str:
        fmt = format_spec or ".2f"
        return (
            f"<Asteroid "
            f"pos=({format(self.x, fmt)}, {format(self.y, fmt)}) "
            f"vel=({format(self.vx, fmt)}, {format(self.vy, fmt)}) "
            f"size={self.size} "
            f"mass={format(self.mass, fmt)} "
            f"radius={format(self.radius, fmt)}>"
        )
    
    def __repr__(self) -> str:
        return (
            f"<Asteroid "
            f"position=({self.x}, {self.y}) "
            f"velocity=({self.vx}, {self.vy}) "
            f"size={self.size} "
            f"mass={self.mass} "
            f"radius={self.radius}>"
        )

    def __copy__(self) -> AsteroidView:
        return type(self)(self._data)

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> AsteroidView:
        copied_data = copy.deepcopy(self._data, memo)
        result = type(self)(copied_data)
        memo[id(self)] = result
        return result


class BulletView:
    __slots__ = ("_data",)

    def __init__(self, data: BulletDataList):
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

    @property
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

    def __format__(self, format_spec: str) -> str:
        fmt = format_spec or ".2f"
        return (
            f"<Bullet "
            f"pos=({format(self.x, fmt)}, {format(self.y, fmt)}) "
            f"vel=({format(self.vx, fmt)}, {format(self.vy, fmt)}) "
            f"tail_delta=({format(self.tail_dx, fmt)}, {format(self.tail_dy, fmt)}) "
            f"heading={format(self.heading, fmt)} "
            f"mass={format(self.mass, fmt)} "
            f"length={format(self.length, fmt)}>"
        )

    def __repr__(self) -> str:
        return (
            f"<Bullet "
            f"position=({self.x}, {self.y}) "
            f"velocity=({self.vx}, {self.vy}) "
            f"tail_delta=({self.tail_dx}, {self.tail_dy}) "
            f"heading={self.heading} "
            f"mass={self.mass} "
            f"length={self.length}>"
        )

    def __copy__(self) -> BulletView:
        return type(self)(self._data)

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> BulletView:
        copied_data = copy.deepcopy(self._data, memo)
        result = type(self)(copied_data)
        memo[id(self)] = result
        return result


class MineView:
    __slots__ = ("_data",)

    def __init__(self, data: MineDataList):
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

    @property
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

    def __format__(self, format_spec: str) -> str:
        fmt = format_spec or ".2f"
        return (
            f"<Mine "
            f"pos=({format(self.x, fmt)}, {format(self.y, fmt)}) "
            f"mass={format(self.mass, fmt)} "
            f"fuse_time={format(self.fuse_time, fmt)} "
            f"remaining_time={format(self.remaining_time, fmt)}>"
        )

    def __repr__(self) -> str:
        return (
            f"<Mine "
            f"position=({self.x}, {self.y}) "
            f"mass={self.mass} "
            f"fuse_time={self.fuse_time} "
            f"remaining_time={self.remaining_time}>"
        )

    def __copy__(self) -> MineView:
        return type(self)(self._data)

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> MineView:
        copied_data = copy.deepcopy(self._data, memo)
        result = type(self)(copied_data)
        memo[id(self)] = result
        return result


class ShipView:
    __slots__ = ("_data",)

    def __init__(self, data: ShipDataList):
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
        assert(isinstance(self._data[8], int))
        return self._data[8]

    @property
    def team(self) -> int:
        assert(isinstance(self._data[9], int))
        return self._data[9]

    @property
    def is_respawning(self) -> bool:
        assert(isinstance(self._data[10], bool))
        return self._data[10]

    @property
    def lives_remaining(self) -> int:
        assert(isinstance(self._data[11], int))
        return self._data[11]

    @property
    def deaths(self) -> int:
        assert(isinstance(self._data[12], int))
        return self._data[12]

    @property
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

    def __format__(self, format_spec: str) -> str:
        fmt = format_spec or ".2f"
        return (
            f"<Ship "
            f"pos=({format(self.x, fmt)}, {format(self.y, fmt)}) "
            f"vel=({format(self.vx, fmt)}, {format(self.vy, fmt)}) "
            f"speed={format(self.speed, fmt)} "
            f"heading={format(self.heading, fmt)} "
            f"mass={format(self.mass, fmt)} "
            f"radius={format(self.radius, fmt)} "
            f"id={self.id} team={self.team} "
            f"is_respawning={self.is_respawning} "
            f"lives_remaining={self.lives_remaining} "
            f"deaths={self.deaths}>"
        )

    def __repr__(self) -> str:
        return (
            f"<Ship "
            f"position={self.position} velocity={self.velocity} "
            f"speed={self.speed} heading={self.heading} mass={self.mass} "
            f"radius={self.radius} id={self.id} team={self.team} "
            f"is_respawning={self.is_respawning} "
            f"lives_remaining={self.lives_remaining} "
            f"deaths={self.deaths}>"
        )

    def __copy__(self) -> ShipView:
        return type(self)(self._data)

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> ShipView:
        copied_data = copy.deepcopy(self._data, memo)
        result = type(self)(copied_data)
        memo[id(self)] = result
        return result


class ShipOwnView(ShipView):
    __slots__ = ("_own_data",)

    def __init__(self, data: ShipDataList):
        # Extend ShipView list with the following:
        # [bullets_remaining: int, mines_remaining: int, can_fire: bool, fire_cooldown: float, fire_rate: float,
        #  can_deploy_mine: bool, mine_cooldown: float, mine_deploy_rate: float, respawn_time_left: float, respawn_time: float,
        #  thrust_min: float, thrust_max: float, turn_rate_min: float, turn_rate_max: float, max_speed: float, drag: float]
        super().__init__(data)
        self._own_data = data

    @property
    def bullets_remaining(self) -> int:
        assert(isinstance(self._own_data[13], int))
        return self._own_data[13]

    @property
    def mines_remaining(self) -> int:
        assert(isinstance(self._own_data[14], int))
        return self._own_data[14]

    @property
    def can_fire(self) -> bool:
        assert(isinstance(self._own_data[15], bool))
        return self._own_data[15]

    @property
    def fire_cooldown(self) -> float:
        return self._own_data[16]

    @property
    def fire_rate(self) -> float:
        return self._own_data[17]

    @property
    def can_deploy_mine(self) -> bool:
        assert(isinstance(self._own_data[18], bool))
        return self._own_data[18]

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

    def __format__(self, format_spec: str) -> str:
        fmt = format_spec or ".2f"
        return (
            f"<OwnShip "
            f"pos=({format(self.x, fmt)}, {format(self.y, fmt)}) "
            f"vel=({format(self.vx, fmt)}, {format(self.vy, fmt)}) "
            f"speed={format(self.speed, fmt)} heading={format(self.heading, fmt)} "
            f"mass={format(self.mass, fmt)} radius={format(self.radius, fmt)} "
            f"id={self.id} team={self.team} is_respawning={self.is_respawning} "
            f"lives_remaining={self.lives_remaining} deaths={self.deaths} "
            f"bullets_remaining={self.bullets_remaining} mines_remaining={self.mines_remaining} "
            f"can_fire={self.can_fire} fire_cooldown={format(self.fire_cooldown, fmt)} "
            f"fire_rate={format(self.fire_rate, fmt)} can_deploy_mine={self.can_deploy_mine} "
            f"mine_cooldown={format(self.mine_cooldown, fmt)} mine_deploy_rate={format(self.mine_deploy_rate, fmt)} "
            f"respawn_time_left={format(self.respawn_time_left, fmt)} respawn_time={format(self.respawn_time, fmt)} "
            f"thrust_range=({format(self.thrust_range[0], fmt)}, {format(self.thrust_range[1], fmt)}) "
            f"turn_rate_range=({format(self.turn_rate_range[0], fmt)}, {format(self.turn_rate_range[1], fmt)}) "
            f"max_speed={format(self.max_speed, fmt)} drag={format(self.drag, fmt)}>"
        )

    def __repr__(self) -> str:
        return (
            f"<OwnShip position={self.position} velocity={self.velocity} speed={self.speed} "
            f"heading={self.heading} mass={self.mass} radius={self.radius} id={self.id} team={self.team} "
            f"is_respawning={self.is_respawning} lives_remaining={self.lives_remaining} deaths={self.deaths} "
            f"bullets_remaining={self.bullets_remaining} mines_remaining={self.mines_remaining} can_fire={self.can_fire} "
            f"fire_cooldown={self.fire_cooldown} fire_rate={self.fire_rate} can_deploy_mine={self.can_deploy_mine} "
            f"mine_cooldown={self.mine_cooldown} mine_deploy_rate={self.mine_deploy_rate} "
            f"respawn_time_left={self.respawn_time_left} respawn_time={self.respawn_time} "
            f"thrust_range={self.thrust_range} turn_rate_range={self.turn_rate_range} "
            f"max_speed={self.max_speed} drag={self.drag}>"
        )
    
    def __copy__(self) -> ShipOwnView:
        new_obj = type(self)(self._own_data)
        return new_obj

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> ShipOwnView:
        copied_data = copy.deepcopy(self._own_data, memo)
        result = type(self)(copied_data)
        memo[id(self)] = result
        return result


class ShipState:
    """
    Wrapper around a single ship's data list, exposing a dict-like interface.

    Behaves like a read-only dictionary mapping property names to values, and
    internally wraps a ShipOwnView (which extends ShipView).
    """

    __slots__ = ("_ship_data", "_view")

    def __init__(self, ship: ShipDataList):
        self._ship_data = ship
        self._view = ShipOwnView(ship)

    @property
    def x(self) -> float:
        return self._view.x

    @property
    def y(self) -> float:
        return self._view.y

    @property
    def position(self) -> tuple[float, float]:
        return self._view.position

    @property
    def vx(self) -> float:
        return self._view.vx

    @property
    def vy(self) -> float:
        return self._view.vy

    @property
    def velocity(self) -> tuple[float, float]:
        return self._view.velocity

    @property
    def speed(self) -> float:
        return self._view.speed

    @property
    def heading(self) -> float:
        return self._view.heading

    @property
    def mass(self) -> float:
        return self._view.mass

    @property
    def radius(self) -> float:
        return self._view.radius

    @property
    def id(self) -> int:
        return self._view.id

    @property
    def team(self) -> int:
        return self._view.team

    @property
    def is_respawning(self) -> bool:
        return self._view.is_respawning

    @property
    def lives_remaining(self) -> int:
        return self._view.lives_remaining

    @property
    def deaths(self) -> int:
        return self._view.deaths

    # ShipOwnView properties

    @property
    def bullets_remaining(self) -> int:
        return self._view.bullets_remaining

    @property
    def mines_remaining(self) -> int:
        return self._view.mines_remaining

    @property
    def can_fire(self) -> bool:
        return self._view.can_fire

    @property
    def fire_cooldown(self) -> float:
        return self._view.fire_cooldown

    @property
    def fire_rate(self) -> float:
        return self._view.fire_rate

    @property
    def can_deploy_mine(self) -> bool:
        return self._view.can_deploy_mine

    @property
    def mine_cooldown(self) -> float:
        return self._view.mine_cooldown

    @property
    def mine_deploy_rate(self) -> float:
        return self._view.mine_deploy_rate

    @property
    def respawn_time_left(self) -> float:
        return self._view.respawn_time_left

    @property
    def respawn_time(self) -> float:
        return self._view.respawn_time

    @property
    def thrust_range(self) -> tuple[float, float]:
        return self._view.thrust_range

    @property
    def turn_rate_range(self) -> tuple[float, float]:
        return self._view.turn_rate_range

    @property
    def max_speed(self) -> float:
        return self._view.max_speed

    @property
    def drag(self) -> float:
        return self._view.drag

    def __getitem__(self, key: str) -> float | int | bool | tuple[float, float]:
        """Allow dict-style access to view attributes."""
        if hasattr(self._view, key):
            return cast(float | int | bool | tuple[float, float], getattr(self._view, key))
        raise KeyError(f"Key '{key}' not found in ship state.")

    def keys(self) -> list[str]:
        """Returns all accessible attribute names."""
        return [
            k for k in dir(self._view)
            if not k.startswith("_") and not callable(getattr(self._view, k))
        ]

    def items(self) -> list[tuple[str, float | int | bool | tuple[float, float]]]:
        """Returns all (key, value) pairs."""
        return [(k, getattr(self._view, k)) for k in self.keys()]

    @property
    def compact(self) -> ShipDataList:
        """Return the underlying ship list (mutable)."""
        return self._ship_data

    @property
    def dict(self) -> ShipOwnStateDict:
        """Return a plain dictionary representation of this ship's own state."""
        return {
            "position": self._view.position,
            "velocity": self._view.velocity,
            "speed": self._view.speed,
            "heading": self._view.heading,
            "mass": self._view.mass,
            "radius": self._view.radius,
            "id": self._view.id,
            "team": self._view.team,
            "is_respawning": self._view.is_respawning,
            "lives_remaining": self._view.lives_remaining,
            "deaths": self._view.deaths,
            "bullets_remaining": self._view.bullets_remaining,
            "mines_remaining": self._view.mines_remaining,
            "can_fire": self._view.can_fire,
            "fire_cooldown": self._view.fire_cooldown,
            "fire_rate": self._view.fire_rate,
            "can_deploy_mine": self._view.can_deploy_mine,
            "mine_cooldown": self._view.mine_cooldown,
            "mine_deploy_rate": self._view.mine_deploy_rate,
            "respawn_time_left": self._view.respawn_time_left,
            "respawn_time": self._view.respawn_time,
            "thrust_range": self._view.thrust_range,
            "turn_rate_range": self._view.turn_rate_range,
            "max_speed": self._view.max_speed,
            "drag": self._view.drag,
        }

    def __contains__(self, key: str) -> bool:
        return hasattr(self._view, key)

    def __len__(self) -> int:
        return len(self.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def __repr__(self) -> str:
        inner = repr(self._view)
        if inner.startswith("<OwnShip"):
            inner = "<ShipState" + inner[len("<OwnShip"):]
        documentation = "\nProperties: Same as keys in ShipState, along with .dict -> dict, .compact -> dict"
        return inner + documentation

    def __format__(self, format_spec: str) -> str:
        inner = format(self._view, format_spec)
        if inner.startswith("<OwnShip"):
            inner = "<ShipState" + inner[len("<OwnShip"):]
        return inner

    def __copy__(self) -> ShipState:
        return type(self)(self._ship_data)

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> ShipState:
        if id(self) in memo:
            return cast(ShipState, memo[id(self)])
        copied_data = copy.deepcopy(self._ship_data, memo)
        result = type(self)(copied_data)
        memo[id(self)] = result
        return result


class GameState:
    __slots__ = (
        "_ship_data",
        "_asteroid_data",
        "_bullet_data",
        "_mine_data",
        "_map_size",
        "_time_limit",
        "_time",
        "_frame",
        "_delta_time",
        "_frame_rate",
        "_random_asteroid_splits",
        "_competition_safe_mode",
    )

    def __init__(self,
                 ships: list[ShipDataList],
                 asteroids: list[AsteroidDataList],
                 bullets: list[BulletDataList],
                 mines: list[MineDataList],
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

    def add_asteroid(self, asteroid_data: AsteroidDataList) -> None:
        self._asteroid_data.append(asteroid_data)

    def add_asteroids(self, asteroid_list: list[AsteroidDataList]) -> None:
        self._asteroid_data.extend(asteroid_list)

    def add_bullet(self, bullet_data: BulletDataList) -> None:
        self._bullet_data.append(bullet_data)

    def add_mine(self, mine_data: MineDataList) -> None:
        self._mine_data.append(mine_data)

    def update_ships(self, ships_data: list[ShipDataList]) -> None:
        self._ship_data = ships_data

    def remove_asteroid(self, index: int) -> None:
        """Remove asteroid at index using swap-and-pop O(1)"""
        # Swap the element at index with the end
        self._asteroid_data[index] = self._asteroid_data[-1]
        # Pop the last element
        self._asteroid_data.pop()

    def remove_bullet(self, index: int) -> None:
        """Remove bullet at index using swap-and-pop O(1)"""
        self._bullet_data[index] = self._bullet_data[-1]
        self._bullet_data.pop()

    def remove_mine(self, index: int) -> None:
        """Remove mine at index using swap-and-pop O(1)"""
        self._mine_data[index] = self._mine_data[-1]
        self._mine_data.pop()

    def remove_ship(self, index: int) -> None:
        """Remove ship at index using swap-and-pop O(1)"""
        self._ship_data[index] = self._ship_data[-1]
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
        return (f"<GameState frame={self.frame} time={self.time}s "
                f"asteroids={len(self._asteroid_data)} "
                f"ships={len(self._ship_data)} bullets={len(self._bullet_data)} "
                f"mines={len(self._mine_data)}>\n"
                f"Properties: ships, asteroids, bullets, mines, "
                f"map_size, time_limit, time, frame, delta_time, "
                f"frame_rate, random_asteroid_splits, competition_safe_mode, "
                f".dict -> dict, .compact -> dict")

    def __str__(self) -> str:
        return (f"GameState @ frame {self.frame} ({self.time}s)\n"
                f"  Asteroids: {len(self._asteroid_data)}\n"
                f"  Ships:     {len(self._ship_data)}\n"
                f"  Bullets:   {len(self._bullet_data)}\n"
                f"  Mines:     {len(self._mine_data)}\n"
                f"Properties: ships, asteroids, bullets, mines, "
                f"map_size, time_limit, time, frame, delta_time, "
                f"frame_rate, random_asteroid_splits, competition_safe_mode, "
                f".dict -> dict, .compact -> dict")

    @property
    def dict(self) -> GameStateDict:
        """Return a plain dictionary representation of the game state."""
        return {
            "ships": [ShipView(ship_data).dict for ship_data in self._ship_data],
            "asteroids": [AsteroidView(asteroid_data).dict for asteroid_data in self._asteroid_data],
            "bullets": [BulletView(bullet_data).dict for bullet_data in self._bullet_data],
            "mines": [MineView(mine_data).dict for mine_data in self._mine_data],
            "map_size": self._map_size,
            "time_limit": self._time_limit,
            "time": self._time,
            "frame": self._frame,
            "delta_time": self._delta_time,
            "frame_rate": self._frame_rate,
            "random_asteroid_splits": self._random_asteroid_splits,
            "competition_safe_mode": self._competition_safe_mode,
        }
    
    @property
    def compact(self) -> GameStateCompactDict:
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

    def __copy__(self) -> GameState:
        return type(self)(
            ships=self._ship_data,
            asteroids=self._asteroid_data,
            bullets=self._bullet_data,
            mines=self._mine_data,
            map_size=self._map_size,
            time_limit=self._time_limit,
            time=self._time,
            frame=self._frame,
            delta_time=self._delta_time,
            frame_rate=self._frame_rate,
            random_asteroid_splits=self._random_asteroid_splits,
            competition_safe_mode=self._competition_safe_mode
        )

    def __deepcopy__(self, memo: builtins.dict[int, Any]) -> GameState:
        if id(self) in memo:
            return cast(GameState, memo[id(self)])
        result = type(self)(
            ships=copy.deepcopy(self._ship_data, memo),
            asteroids=copy.deepcopy(self._asteroid_data, memo),
            bullets=copy.deepcopy(self._bullet_data, memo),
            mines=copy.deepcopy(self._mine_data, memo),
            map_size=self._map_size,
            time_limit=self._time_limit,
            time=self._time,
            frame=self._frame,
            delta_time=self._delta_time,
            frame_rate=self._frame_rate,
            random_asteroid_splits=self._random_asteroid_splits,
            competition_safe_mode=self._competition_safe_mode
        )
        memo[id(self)] = result
        return result
