# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

#import os
from tkinter import *
from typing import List
#from PIL import Image, ImageTk  # type: ignore[import-untyped]

from ..ship import Ship
from ..asteroid import Asteroid
from ..bullet import Bullet
from ..mines import Mine
from ..score import Score
from ..scenario import Scenario


class KesslerGraphics:
    def start(self, scenario: Scenario) -> None:
        raise NotImplementedError('Your derived KesslerController must include a start() method.')

    def update(self, score: Score, ships: List[Ship], asteroids: List[Asteroid], bullets: List[Bullet], mines: List[Mine]) -> None:
        raise NotImplementedError('Your derived KesslerController must include an update() method.')

    def close(self) -> None:
        raise NotImplementedError('Your derived KesslerController must include a close() method.')
