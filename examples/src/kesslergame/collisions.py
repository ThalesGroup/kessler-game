# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import numpy as np
import math

def circle_line_collision(line_A, line_B, center, radius):
    # Check if circle edge is within the outer bounds of the line segment (offset for radius)
    # Not 100% accurate (some false positives) but fast and rare inaccuracies
    x_bounds = [min(line_A[0], line_B[0])-radius, max(line_A[0], line_B[0])+radius]
    if center[0] < x_bounds[0] or center[0] > x_bounds[1]:
        return False
    y_bounds = [min(line_A[1], line_B[1])-radius, max(line_A[1], line_B[1])+radius]
    if center[1] < y_bounds[0] or center[1] > y_bounds[1]:
        return False

    # calculate side lengths of triangle formed from the line segment and circle center point
    # round to 4 decimal places to prevent floating point error sqrt(-0) later
    a = round(math.dist(line_A, center), 4)
    b = round(math.dist(line_B, center), 4)
    c = round(math.dist(line_A, line_B), 4)

    # Heron's formula to calculate area of triangle and resultant height (distance from circle center to line segment)
    s = 0.5 * (a + b + c)

    cen_dist = 2 / c * np.sqrt(s * (s-a) * (s-b) * (s-c))

    # If circle distance to line segment is less than circle radius, they are colliding
    if cen_dist < radius:
        return True
    return False



