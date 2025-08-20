# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations

from typing import ClassVar
from enum import IntEnum


class CollisionType(IntEnum):
    BULLET_ASTEROID = 0
    SHIP_ASTEROID = 1
    SHIP_SHIP = 2
    MINE_ASTEROID = 3
    MINE_SHIP = 4


class CollisionEvent:
    __slots__ = ("time_offset", "distance", "object_a_idx", "object_b_idx", "collision_type", "collision_specific_final_tiebreaker", "insertion_order")

    TOLERANCE: ClassVar[float] = 1e-10
    WEAK_TOLERANCE: ClassVar[float] = 1e-6
    _counter: ClassVar[int] = 0  # class-level monotonic counter

    def __init__(self, time_offset: float, distance: float, object_a_idx: int, object_b_idx: int, collision_type: CollisionType, specific_tiebreaker: float = 0.0):
        """
        Represents a collision event between two game objects at a specific time.

        :param time_offset: Time (in seconds) relative to the end of the frame. Must be in [-dt, 0.0].
        :param distance: Squared wrapped distance between the colliding objects. Used to break ties
        :param object_a_idx: Index of first object involved in the collision.
        :param object_b_idx: Index of second object involved in the collision.
        :param collision_type: Type of collision as defined in CollisionType enum.
        """
        self.time_offset: float = time_offset  # Time offset in seconds relative to frame end, e.g., -0.001
        self.distance: float = distance  # Distance between centers of colliding objects. Squared!
        # Time offset should be in range [-delta_time, 0.0]
        self.object_a_idx = object_a_idx
        self.object_b_idx = object_b_idx
        self.collision_type = collision_type
        self.collision_specific_final_tiebreaker: float = specific_tiebreaker
        # The sort order is: time offset, collision type, distance, collision specific final tiebreaker, insertion order

        # Assign and increment insertion_order
        self.insertion_order = CollisionEvent._counter
        CollisionEvent._counter += 1

    # Hand-implement each of the comparison dunders for speed, instead of using one for the others

    # Tolerant float comparison helpers
    @staticmethod
    def _less(a: float, b: float) -> bool:
        return a < b - CollisionEvent.TOLERANCE

    @staticmethod
    def _greater(a: float, b: float) -> bool:
        return a > b + CollisionEvent.TOLERANCE

    @staticmethod
    def _equal(a: float, b: float) -> bool:
        return abs(a - b) <= CollisionEvent.TOLERANCE

    @staticmethod
    def _weak_less(a: float, b: float) -> bool:
        return a < b - CollisionEvent.WEAK_TOLERANCE

    @staticmethod
    def _weak_greater(a: float, b: float) -> bool:
        return a > b + CollisionEvent.WEAK_TOLERANCE

    @staticmethod
    def _weak_equal(a: float, b: float) -> bool:
        return abs(a - b) <= CollisionEvent.WEAK_TOLERANCE

    def __lt__(self, other: CollisionEvent) -> bool:
        if self._less(self.time_offset, other.time_offset):
            return True
        if self._greater(self.time_offset, other.time_offset):
            return False

        if self.collision_type < other.collision_type:
            return True
        if self.collision_type > other.collision_type:
            return False

        if self._weak_less(self.distance, other.distance):
            return True
        if self._weak_greater(self.distance, other.distance):
            return False

        if self._less(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return True
        if self._greater(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return False

        # Final tiebreaker: insertion order
        return self.insertion_order < other.insertion_order

    def __le__(self, other: CollisionEvent) -> bool:
        if self._less(self.time_offset, other.time_offset):
            return True
        if self._greater(self.time_offset, other.time_offset):
            return False

        if self.collision_type < other.collision_type:
            return True
        if self.collision_type > other.collision_type:
            return False

        if self._weak_less(self.distance, other.distance):
            return True
        if self._weak_greater(self.distance, other.distance):
            return False

        if self._less(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return True
        if self._greater(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return False

        return self.insertion_order <= other.insertion_order

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CollisionEvent):
            return NotImplemented
        return (
            self._equal(self.time_offset, other.time_offset)
            and self.collision_type == other.collision_type
            and self._weak_equal(self.distance, other.distance)
            and self._equal(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker)
            and self.insertion_order == other.insertion_order
        )

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, CollisionEvent):
            return NotImplemented
        return (
            not self._equal(self.time_offset, other.time_offset)
            or self.collision_type != other.collision_type
            or not self._weak_equal(self.distance, other.distance)
            or not self._equal(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker)
            or self.insertion_order != other.insertion_order
        )

    def __gt__(self, other: CollisionEvent) -> bool:
        if self._greater(self.time_offset, other.time_offset):
            return True
        if self._less(self.time_offset, other.time_offset):
            return False

        if self.collision_type > other.collision_type:
            return True
        if self.collision_type < other.collision_type:
            return False

        if self._weak_greater(self.distance, other.distance):
            return True
        if self._weak_less(self.distance, other.distance):
            return False

        if self._greater(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return True
        if self._less(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return False

        return self.insertion_order > other.insertion_order

    def __ge__(self, other: CollisionEvent) -> bool:
        if self._greater(self.time_offset, other.time_offset):
            return True
        if self._less(self.time_offset, other.time_offset):
            return False

        if self.collision_type > other.collision_type:
            return True
        if self.collision_type < other.collision_type:
            return False

        if self._weak_greater(self.distance, other.distance):
            return True
        if self._weak_less(self.distance, other.distance):
            return False

        if self._greater(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return True
        if self._less(self.collision_specific_final_tiebreaker, other.collision_specific_final_tiebreaker):
            return False

        return self.insertion_order >= other.insertion_order

    def __repr__(self) -> str:
        return (
            f"<CollisionEvent time_offset={self.time_offset}s distance={self.distance} "
            f"type={self.collision_type} obj_a_idx={self.object_a_idx} obj_b_idx={self.object_b_idx} "
            f"collision_specific_final_tiebreaker={self.collision_specific_final_tiebreaker} "
            f"insertion_order={self.insertion_order}>"
        )
