# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import TypedDict

class MineState(TypedDict):
    position: tuple[float, float]
    mass: float
    fuse_time: float
    remaining_time: float
