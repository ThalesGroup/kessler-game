# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import math

def circle_line_collision_continuous(
    line_A: tuple[float, float],
    line_B: tuple[float, float],
    line_vel: tuple[float, float],
    circle_center: tuple[float, float],
    circle_vel: tuple[float, float],
    circle_radius: float,
    delta_time: float,
) -> bool:
    # First, do a quick bounding box rejection check
    # Find the min/max x/y values that the bullet can take on, and then expand by the radius of the asteroid
    x_values = (line_A[0], line_A[0] - (line_vel[0] - circle_vel[0]) * delta_time, line_B[0], line_B[0] - (line_vel[0] - circle_vel[0]) * delta_time)
    y_values = (line_A[1], line_A[1] - (line_vel[1] - circle_vel[1]) * delta_time, line_B[1], line_B[1] - (line_vel[1] - circle_vel[1]) * delta_time)
    min_x = min(x_values)
    max_x = max(x_values)
    min_y = min(y_values)
    max_y = max(y_values)
    if circle_center[0] + circle_radius < min_x or circle_center[0] - circle_radius > max_x or circle_center[1] + circle_radius < min_y or circle_center[1] - circle_radius > max_y:
        return False

    # The key insight is that, from the frame of reference of the asteroid, the bullet's path over the previous frame covers the shape of a parallelogram
    # So we can simplify this problem down to a stationary collision check between a circle centered at the origin, and a parallelogram
    
    # Fix frame of reference to circle
    # a and b are the head and tail of the bullet
    ax = line_A[0] - circle_center[0]
    ay = line_A[1] - circle_center[1]
    bx = line_B[0] - circle_center[0]
    by = line_B[1] - circle_center[1]
    vx = (line_vel[0] - circle_vel[0]) * delta_time # Per frame velocities
    vy = (line_vel[1] - circle_vel[1]) * delta_time
    # c and d are the head and tails of the bullet, delta_time in the past, forming the other two points of the parallelogram
    cx = ax - vx
    cy = ay - vy
    dx = bx - vx
    dy = by - vy

    rad_sq = circle_radius * circle_radius

    # Check whether any of the vertices of the parallelogram are within the circle
    # Actually this is redundant, since if we project and clamp and just check those, it will cover the cases where the corner is the closest
    # This might be a fast enough rejection check for it to be worth doing anyway
    #if ax * ax + ay * ay <= rad_sq or bx * bx + by * by <= rad_sq or cx * cx + cy * cy <= rad_sq or dx * dx + dy * dy <= rad_sq:
    #    return True

    # Project the point (0, 0), the center of the circle, onto each of the edges of the parallelogram
    def project_origin_onto_segment_dist_sq(x1: float, y1: float, x2: float, y2: float) -> float:
        # Given a segment from (x1, y1) to (x2, y2), project the origin (0, 0)
        # onto this segment and return the squared distance from the origin
        # to the closest point on the segment.
        dx = x2 - x1
        dy = y2 - y1
        len_sq = dx*dx + dy*dy

        # If the endpoints are basically the same point,
        # just return squared dist to the (degenerate) endpoint.
        if len_sq < 1e-12:
            return x1*x1 + y1*y1

        # Compute the projection parameter t of the origin onto the segment,
        # where t=0 yields (x1, y1) and t=1 yields (x2, y2).
        # Clamp t to [0, 1] to stay on the segment.
        t = -(x1*dx + y1*dy)/len_sq
        t = max(0.0, min(1.0, t))

        # Compute the closest point's coordinates.
        px = x1 + t*dx
        py = y1 + t*dy

        # Return the squared distance from the origin to this closest point.
        return px*px + py*py

    # Check whether any of these projected points with clamping are within the circle. If yes, there's a collision.
    if (
        project_origin_onto_segment_dist_sq(ax, ay, bx, by) <= rad_sq or # A - B
        project_origin_onto_segment_dist_sq(cx, cy, dx, dy) <= rad_sq or # C - D
        project_origin_onto_segment_dist_sq(ax, ay, cx, cy) <= rad_sq or # A - C
        project_origin_onto_segment_dist_sq(bx, by, dx, dy) <= rad_sq    # B - D
    ):
        return True

    # If still no collision, then the only way this can still be a collision is if the circle is completely contained within the parallelogram,
    # which is impossible in this case because the bullet is too short for an asteroid to fit between its ends.
    # But for completeness, for the general solution, you can uncomment the following code which checks whether the origin is within the parallelogram using a cross product orientation checker
    '''
    def is_origin_in_parallelogram(ax, ay, bx, by, cx, cy, dx, dy):
        def cross(xa, ya, xb, yb):
            return xa * yb - ya * xb
        corners = [(ax, ay), (bx, by), (dx, dy), (cx, cy)]
        sign = None
        for i in range(4):
            x0, y0 = corners[i]
            x1, y1 = corners[(i + 1) % 4]
            # Edge from (x0, y0) to (x1, y1)
            edge_x = x1 - x0
            edge_y = y1 - y0
            # Vector from (x0, y0) to origin (0, 0) is (-x0, -y0)
            cp = cross(edge_x, edge_y, -x0, -y0)
            if cp == 0.0:
                continue  # Origin is on the edge, consider inside
            if sign is None:
                sign = cp > 0.0
            else:
                if (cp > 0.0) != sign:
                    return False
        return True
    if is_origin_in_parallelogram(ax, ay, bx, by, cx, cy, dx, dy):
        return True
    '''
    return False

def circle_line_collision_discrete(line_A: tuple[float, float], line_B: tuple[float, float], center: tuple[float, float], radius: float) -> bool:
    # Accurate version of the discrete collision check
    
    # Quick rejection check:
    # Check if circle edge is within the outer bounds of the line segment (offset for radius)
    x_bounds = [min(line_A[0], line_B[0]) - radius, max(line_A[0], line_B[0]) + radius]
    if center[0] < x_bounds[0] or center[0] > x_bounds[1]:
        return False
    y_bounds = [min(line_A[1], line_B[1]) - radius, max(line_A[1], line_B[1]) + radius]
    if center[1] < y_bounds[0] or center[1] > y_bounds[1]:
        return False

    # This works by taking the circle's center, and projecting it onto the line segment's line, and clamping it to the line segment.
    # This process will yield the point on the line segment that is closest to the circle's center.
    # We can then check whether this point is inside the circle.

    # Fix frame of reference to the circle center. Shift the segment so the circle is at the origin
    ax = line_A[0] - center[0]
    ay = line_A[1] - center[1]
    bx = line_B[0] - center[0]
    by = line_B[1] - center[1]

    # Now project the origin (0, 0), the center of the circle, onto the segment A-B
    dx = bx - ax
    dy = by - ay
    len_sq = dx * dx + dy * dy

    # If the segment is degenerate (very short), just use the distance to one of the endpoints
    if len_sq < 1e-12:
        dist_sq = ax * ax + ay * ay
    else:
        # Compute projection parameter t of origin onto line defined by segment A-B
        # Clamp t to [0, 1] to project onto the actual segment
        t = -(ax * dx + ay * dy) / len_sq
        t = max(0.0, min(1.0, t))

        # Compute closest point on segment to the circle's center (which is now at origin)
        px = ax + t * dx
        py = ay + t * dy

        # Compute squared distance from circle center (origin) to this point
        dist_sq = px * px + py * py

    # If the squared distance of the closest point on line segment to the center of circle is less than or equal to the squared radius, there is a collision
    return dist_sq <= radius * radius

def circle_line_collision_old(line_A: tuple[float, float], line_B: tuple[float, float], center: tuple[float, float], radius: float) -> bool:
    # Old collision check, which was discrete, and also had false positives:
    
    # Check if circle edge is within the outer bounds of the line segment (offset for radius)
    # Not 100% accurate (some false positives) but fast and rare inaccuracies
    x_bounds = [min(line_A[0], line_B[0]) - radius, max(line_A[0], line_B[0]) + radius]
    if center[0] < x_bounds[0] or center[0] > x_bounds[1]:
        return False
    y_bounds = [min(line_A[1], line_B[1]) - radius, max(line_A[1], line_B[1]) + radius]
    if center[1] < y_bounds[0] or center[1] > y_bounds[1]:
        return False

    # calculate side lengths of triangle formed from the line segment and circle center point
    a = math.dist(line_A, center)
    b = math.dist(line_B, center)
    c = math.dist(line_A, line_B)

    # Heron's formula to calculate area of triangle and resultant height (distance from circle center to line segment)
    s = 0.5 * (a + b + c)

    cen_dist = 2.0 / c * math.sqrt(max(0.0, s * (s-a) * (s-b) * (s-c)))

    # If circle distance to line segment is less than circle radius, they are colliding
    return cen_dist < radius
