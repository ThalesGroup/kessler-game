# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TypedDict

class BulletState(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]
    heading: float
    mass: float
