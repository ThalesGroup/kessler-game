# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.


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

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self):
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
    def heading(self) -> float:
        return self._data[6]

    @property
    def mass(self) -> float:
        return self._data[7]

    @property
    def length(self) -> float:
        return self._data[8]

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self):
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

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self):
        return f"<MineView pos={self.position} remaining={self.remaining_time:.2f}>"


class ShipView:
    def __init__(self, data: list[float | int]):
        # []
        self._data = data

    @property
    def position(self) -> list[float]:
        return self._data[0]

    @property
    def velocity(self) -> list[float]:
        return self._data[1]

    @property
    def speed(self) -> float:
        return self._data[2]

    @property
    def heading(self) -> float:
        return self._data[3]

    @property
    def mass(self) -> float:
        return self._data[4]

    @property
    def radius(self) -> float:
        return self._data[5]

    @property
    def id(self) -> int:
        return self._data[6]

    @property
    def team(self) -> int:
        return self._data[7]

    @property
    def is_respawning(self) -> bool:
        return self._data[8]

    @property
    def lives_remaining(self) -> int:
        return self._data[9]

    @property
    def deaths(self) -> int:
        return self._data[10]

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __repr__(self):
        return f"<ShipView id={self.id} team={self.team} pos={self.position}>"


class GameState:
    def __init__(self,
                 asteroids: list[list[float]],
                 bullets: list[list[float]],
                 mines: list[list[float]],
                 ships: list[list[float | int]],
                 map_size: tuple[int, int],
                 time: float,
                 delta_time: float,
                 frame: int,
                 time_limit: float,
                 random_asteroid_splits: bool,
                 competition_safe_mode: bool):
        
        self._asteroid_data = asteroids
        self._bullet_data = bullets
        self._mine_data = mines
        self._ship_data = ships

        self.map_size = map_size
        self.time = time
        self.delta_time = delta_time
        self.frame = frame
        self.time_limit = time_limit
        self.random_asteroid_splits = random_asteroid_splits
        self.competition_safe_mode = competition_safe_mode

        self.frame_rate = 1.0 / delta_time if delta_time != 0 else float('inf')

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
    def ships(self) -> list[ShipView]:
        return [ShipView(data) for data in self._ship_data]

    def __getitem__(self, key: str):
        return {
            "asteroids": self.asteroids,
            "bullets": self.bullets,
            "mines": self.mines,
            "ships": self.ships,
            "map_size": self.map_size,
            "time": self.time,
            "delta_time": self.delta_time,
            "frame_rate": self.frame_rate,
            "frame": self.frame,
            "time_limit": self.time_limit,
            "random_asteroid_splits": self.random_asteroid_splits,
            "competition_safe_mode": self.competition_safe_mode
        }[key]

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

