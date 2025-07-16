# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from __future__ import annotations
from typing import TYPE_CHECKING
from tkinter import *

if TYPE_CHECKING:
    from ..ship import Ship
    from ..asteroid import Asteroid
    from ..bullet import Bullet
    from ..mines import Mine
    from ..score import Score
    from ..scenario import Scenario


class KesslerGraphics:
    def start(self, scenario: Scenario) -> None:
        raise NotImplementedError('Your derived KesslerGraphics must include a start() method.')

    def update(self, score: Score, ships: list[Ship], asteroids: list[Asteroid], bullets: list[Bullet], mines: list[Mine]) -> None:
        raise NotImplementedError('Your derived KesslerGraphics must include an update() method.')

    def close(self) -> None:
        raise NotImplementedError('Your derived KesslerGraphics must include a close() method.')
