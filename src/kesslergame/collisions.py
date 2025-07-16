# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import math

def solve_quadratic(a: float, b: float, c: float) -> tuple[float, float]:
    """
    Solve the quadratic equation a*x**2 + b*x + c = 0 for real roots.

    Handles degenerate linear and constant cases. Returns a tuple of roots (t0, t1) in sorted order.
    If there are no real roots, returns (math.nan, math.nan). If linear, returns one solution repeated.

    Note: Does not handle floating point overflow.

    Args:
        a (float): Quadratic coefficient.
        b (float): Linear coefficient.
        c (float): Constant term.

    Returns:
        tuple[float, float]: Roots (t0, t1), sorted in ascending order, or (nan, nan) if no real roots.
    """
    if a == 0.0:
        # Linear case: bx + c = 0
        if b == 0.0:
            if c == 0.0:
                return 0.0, 0.0
            else:
                return math.nan, math.nan
        else:
            x = -c / b
            return x, x

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0.0:
        # No real solutions
        return math.nan, math.nan

    q = -0.5 * (b + math.copysign(math.sqrt(discriminant), b))
    if c == 0.0:
        x1 = -b / a
        if x1 < 0.0:
            return x1, 0.0
        else:
            return 0.0, x1

    # q cannot be 0 here
    x1 = q / a
    x2 = c / q
    if x1 <= x2:
        return x1, x2
    else:
        return x2, x1

def collision_time_interval(
    line_A: tuple[float, float],
    line_B: tuple[float, float],
    line_vel: tuple[float, float],
    circle_center: tuple[float, float],
    circle_vel: tuple[float, float],
    circle_radius: float
) -> tuple[float, float]:
    """
    Returns the time interval [t0, t1] where the moving segment (A,B) and moving circle intersect.
    Returns (nan, nan) if there is no interception.
    """

    ax, ay = line_A
    bx, by = line_B
    vx, vy = line_vel  # Both endpoints move the same way

    cx, cy = circle_center
    cvx, cvy = circle_vel
    r = circle_radius
    r_sq = r * r

    # Relative velocity: treat circle as stationary, move A and B at (line_vel - circle_vel)
    rvx = vx - cvx
    rvy = vy - cvy

    # Initial positions relative to circle's center
    # (Place circle at origin)
    a0x = ax - cx
    a0y = ay - cy
    b0x = bx - cx
    b0y = by - cy

    # Segment vector and length
    seg_dx = b0x - a0x
    seg_dy = b0y - a0y
    seg_len = math.hypot(seg_dx, seg_dy)  # Will be 12.0
    # For normalization later
    if seg_len == 0.:
        # Degenerate segment, treat as point
        # We'll just reduce to point vs circle, i.e., treat both A and B as A
        seg_dx = seg_dy = 0.0

    # Solve for when A and B independently are on the circle (corner-collisions)
    # For A
    k0 = a0x * a0x + a0y * a0y - r_sq
    k1 = 2.0 * (rvx * a0x + rvy * a0y)
    k2 = rvx * rvx + rvy * rvy

    t0_A, t1_A = solve_quadratic(k2, k1, k0)

    # For B
    q0 = b0x * b0x + b0y * b0y - r_sq
    q1 = 2.0 * (rvx * b0x + rvy * b0y)
    q2 = k2  # Same as velocity terms above

    t0_B, t1_B = solve_quadratic(q2, q1, q0)

    # Should check for NaNs - if both are nan, there's no possibility
    if math.isnan(t0_A) and math.isnan(t0_B):
        return (math.nan, math.nan)

    t0 = math.inf
    t1 = -math.inf
    for t in [t0_A, t0_B]:
        if not math.isnan(t):
            t0 = min(t0, t)
    for t in [t1_A, t1_B]:
        if not math.isnan(t):
            t1 = max(t1, t)

    # Mid-segment "side swipe" collisions
    # Compute the perpendicular axis n to the segment (A->B); positive to the left of AB
    # n = (dy, -dx) / seg_len as a unit normal (right-hand swap/flop)
    if seg_len > 0:
        nx = seg_dy / seg_len
        ny = -seg_dx / seg_len
    else:
        # Segment degenerate: side swipe not possible, skip this block
        nx = ny = 0.0

    # Project relative velocity onto normal axis
    v_proj_n = nx * rvx + ny * rvy
    # We always want v_proj_n positive, flip the normal if not
    if v_proj_n < 0.0:
        nx *= -1.0
        ny *= -1.0
        v_proj_n *= -1.0

    # Project vector from A to origin (circle center) onto normal axis
    r_a0_to_center_x = -a0x
    r_a0_to_center_y = -a0y
    ast_proj_n = r_a0_to_center_x * nx + r_a0_to_center_y * ny

    # Find when the center of the circle crosses the (possibly growing or shrinking) normal tube of radius r
    t_ast_center = ast_proj_n / v_proj_n if v_proj_n != 0.0 else math.inf
    t_diff_ast_radius = r / v_proj_n if v_proj_n != 0.0 else math.inf

    t0_mid = t_ast_center - t_diff_ast_radius
    t1_mid = t_ast_center + t_diff_ast_radius

    # The bullet's endpoints are at n=0; so check if these collision points lie within the inside of the segment
    def project_point_onto_segment_and_get_t(x1, y1, x2, y2, px, py) -> float:
        """
        Projects point P onto segment A->B, returns t in [0,1] where projection falls;
        If out of [0,1], the closest endpoint is closer than the interior.
        """
        dx = x2 - x1
        dy = y2 - y1
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-12:
            return 0.0
        px_rel = px - x1
        py_rel = py - y1
        t = (px_rel * dx + py_rel * dy) / len_sq
        return t

    # At time t0_mid, the whole segment translates by t*rv; check where the circle center projects onto segment
    a0x_t0m = a0x + rvx * t0_mid
    a0y_t0m = a0y + rvy * t0_mid
    b0x_t0m = b0x + rvx * t0_mid
    b0y_t0m = b0y + rvy * t0_mid
    # The circle remains at the origin
    t_proj_0 = project_point_onto_segment_and_get_t(a0x_t0m, a0y_t0m, b0x_t0m, b0y_t0m, 0.0, 0.0)

    a0x_t1m = a0x + rvx * t1_mid
    a0y_t1m = a0y + rvy * t1_mid
    b0x_t1m = b0x + rvx * t1_mid
    b0y_t1m = b0y + rvy * t1_mid
    t_proj_1 = project_point_onto_segment_and_get_t(a0x_t1m, a0y_t1m, b0x_t1m, b0y_t1m, 0.0, 0.0)

    # Only if the projected t is in [0,1] do we allow t0_mid or t1_mid to extend the window
    if 0.0 <= t_proj_0 <= 1.0:
        # This t0_mid corresponds to collision at the interior of the segment
        # This definitely happens before either end of the bullet collides
        #assert(t0_mid <= t0)
        #t0 = min(t0, t0_mid)
        t0 = t0_mid
    if 0.0 <= t_proj_1 <= 1.0:
        # This t1_mid corresponds to collision at the interior of the segment
        # This definitely happens after either end of the bullet finishes colliding
        #assert(t1_mid >= t1)
        #t1 = max(t1, t1_mid)
        t1 = t1_mid

    # If we never updated t0/t1, no collision
    if not (math.isfinite(t0) and math.isfinite(t1)):
        return (math.nan, math.nan)

    return (t0, t1)

def circle_line_collision_continuous(
    line_A: tuple[float, float],
    line_B: tuple[float, float],
    line_vel: tuple[float, float],
    circle_center: tuple[float, float],
    circle_vel: tuple[float, float],
    circle_radius: float,
    delta_time: float
) -> bool:
    # Returns whether a moving circle and line segment collided within the time interval [-delta_time, 0]

    # First, do a quick bounding box rejection check
    # Find the min/max x/y values that the bullet can take on, and then expand by the radius of the asteroid
    # This code can be written MUCH cleaner by creating a list and using max and min on it, however this unrolled version is many times faster when compiled with mypyc
    # This code is the most called function in the game, so speed is crucial
    rel_frame_vel_x = (line_vel[0] - circle_vel[0]) * delta_time
    rel_frame_vel_y = (line_vel[1] - circle_vel[1]) * delta_time

    # X
    if line_A[0] < line_B[0]:
        if rel_frame_vel_x >= 0.0:
            min_x = line_A[0] - rel_frame_vel_x
            max_x = line_B[0]
        else:
            min_x = line_A[0]
            max_x = line_B[0] - rel_frame_vel_x
    else:
        if rel_frame_vel_x >= 0.0:
            min_x = line_B[0] - rel_frame_vel_x
            max_x = line_A[0]
        else:
            min_x = line_B[0]
            max_x = line_A[0] - rel_frame_vel_x

    # Y
    if line_A[1] < line_B[1]:
        if rel_frame_vel_y >= 0.0:
            min_y = line_A[1] - rel_frame_vel_y
            max_y = line_B[1]
        else:
            min_y = line_A[1]
            max_y = line_B[1] - rel_frame_vel_y
    else:
        if rel_frame_vel_y >= 0.0:
            min_y = line_B[1] - rel_frame_vel_y
            max_y = line_A[1]
        else:
            min_y = line_B[1]
            max_y = line_A[1] - rel_frame_vel_y
    
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
        len_sq = dx * dx + dy * dy

        # If the endpoints are basically the same point,
        # just return squared dist to the (degenerate) endpoint.
        if len_sq < 1e-12:
            return x1 * x1 + y1 * y1

        # Compute the projection parameter t of the origin onto the segment,
        # where t=0 yields (x1, y1) and t=1 yields (x2, y2).
        # Clamp t to [0, 1] to stay on the segment.
        t = -(x1 * dx + y1 * dy) / len_sq
        # Avoid max/min to optimize for mypyc compilation
        if t > 1.0:
            t = 1.0
        elif t < 0.0:
            t = 0.0
        #t = max(0.0, min(1.0, t))

        # Compute the closest point's coordinates.
        px = x1 + t * dx
        py = y1 + t * dy

        # Return the squared distance from the origin to this closest point.
        return px * px + py * py

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
        # Avoid max/min to optimize for mypyc compilation
        if t > 1.0:
            t = 1.0
        elif t < 0.0:
            t = 0.0
        #t = max(0.0, min(1.0, t))

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

    cen_dist = 2.0 / c * math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))

    # If circle distance to line segment is less than circle radius, they are colliding
    return cen_dist < radius
