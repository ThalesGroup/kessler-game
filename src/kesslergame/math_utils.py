# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from math import sin, cos, nan, inf, copysign, sqrt, isclose, isnan
from typing import Callable


def solve_quadratic(a: float, b: float, c: float) -> tuple[float, float]:
    """
    Solve the quadratic equation a*x**2 + b*x + c = 0 for real roots.

    Handles degenerate linear and constant cases. Returns a tuple of roots (t0, t1) in sorted order.
    If there are no real roots, returns (nan, nan). If linear, returns one solution repeated.

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
                return nan, nan
        else:
            x = -c / b
            return x, x

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0.0:
        # No real solutions
        return nan, nan

    q = -0.5 * (b + copysign(sqrt(discriminant), b))
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


def project_point_onto_segment_and_get_t(x1: float, y1: float, x2: float, y2: float, px: float, py: float) -> float:
    """
    Projects point P onto segment A->B, returns t in [0,1] where projection falls;
    If out of [0,1], the closest endpoint is closer than the interior.
    """
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-12:
        return nan
    px_rel = px - x1
    py_rel = py - y1
    t = (px_rel * dx + py_rel * dy) / len_sq
    return t


def analytic_ship_movement_integration(v0: float, a: float, theta0: float, omega: float, delta_t: float) -> tuple[float, float]:
    """
    Returns (dx, dy) using either analytic or Taylor expansion for small omega.
    Args:
        v0: initial speed
        a: acceleration
        theta0: initial heading (radians)
        omega: turn rate (rad/sec)
        dt: t1 - t0, the time interval to integrate over (seconds)
    """
    if abs(delta_t) < 1e-12:
        # Integrating over basically no time into the future
        return 0.0, 0.0
    if abs(omega) < 0.15:
        # Omega is very small, and the divisions in the analytic solution have numerical instability
        # Use a 2nd order Taylor/Maclaurin series to get a much more accurate result near 0
        # Also without this code, with omega near 0, the ship starts teleporting!
        # The cutoff of 0.15 was found by testing some values for the constants,
        # and making a plot of the absolute error between the Taylor and analytic graphs.
        # 0.15 tends to minimize this max absolute error at about 1e-11, and is the balance point.
        cos_theta0 = cos(theta0)
        sin_theta0 = sin(theta0)

        delta_t2 = delta_t * delta_t
        delta_t3 = delta_t2 * delta_t
        delta_t4 = delta_t3 * delta_t
        a_delta_t = a * delta_t

        # Derivatives were found by taking limits as omega approaches zero, of the derivatives of the analytic solution
        omega0_common = delta_t * (a_delta_t / 2.0 + v0)
        omega0_deriv_common = delta_t2 * (a_delta_t / 3.0 + v0 / 2.0)
        omega0_second_deriv_common = delta_t3 * (a_delta_t / 4.0 + v0 / 3.0)
        omega0_third_deriv_common = delta_t4 * (a_delta_t / 5.0 + v0 / 4.0)

        delta_x_omega0 = omega0_common * cos_theta0
        delta_x_deriv_omega0 = -omega0_deriv_common * sin_theta0
        delta_x_second_deriv_omega0 = -omega0_second_deriv_common * cos_theta0
        delta_x_third_deriv_omega0 = omega0_third_deriv_common * sin_theta0

        delta_y_omega0 = omega0_common * sin_theta0
        delta_y_deriv_omega0 = omega0_deriv_common * cos_theta0
        delta_y_second_deriv_omega0 = -omega0_second_deriv_common * sin_theta0
        delta_y_third_deriv_omega0 = -omega0_third_deriv_common * cos_theta0
        
        # Assemble Taylor polynomials and evaluate for dx and dy
        dx = delta_x_omega0 + omega * (delta_x_deriv_omega0 + omega * (delta_x_second_deriv_omega0 / 2.0 + omega * delta_x_third_deriv_omega0 / 6.0))
        dy = delta_y_omega0 + omega * (delta_y_deriv_omega0 + omega * (delta_y_second_deriv_omega0 / 2.0 + omega * delta_y_third_deriv_omega0 / 6.0))
    else:
        # Exact analytic solution
        # The Sympy code to set up dynamics and integrate is as follows:

        # from sympy import *
        # x0, y0, v0, theta0, omega, delta_x, delta_y, t, delta_t, a = symbols('x0 y0 v0 theta0 omega delta_x delta_y t delta_t a')
        # v_t = v0 + a * t
        # theta_t = theta0 + omega * t
        # delta_x_expr = integrate(v_t * cos(theta_t), (t, 0, delta_t))
        # delta_y_expr = integrate(v_t * sin(theta_t), (t, 0, delta_t))
        
        delta_theta = omega * delta_t
        theta1 = theta0 + delta_theta
        sin_theta0 = sin(theta0)
        sin_theta1 = sin(theta1)
        cos_theta0 = cos(theta0)
        cos_theta1 = cos(theta1)
        sin_diff = sin_theta1 - sin_theta0
        cos_diff = cos_theta1 - cos_theta0
        dx = (v0 * sin_diff + (a / omega) * (cos_diff + delta_theta * sin_theta1)) / omega
        dy = (-v0 * cos_diff + (a / omega) * (sin_diff - delta_theta * cos_theta1)) / omega
    return dx, dy


def circle_circle_collision_time_interval(
    ax: float, ay: float, vax: float, vay: float, ra: float,
    bx: float, by: float, vbx: float, vby: float, rb: float
) -> tuple[float, float]:
    """
    Returns (t_enter, t_exit) if the two circles will collide,
    or (nan, nan) if there's no collision in the future.
    Can return (-inf, inf) if the circles collide always and ever.
    """
    # This linalg version is mathematically the same as setting up a quadratic and solving it, but is faster since it simplifies things

    separation = ra + rb

    dx = ax - bx
    dy = ay - by
    dvx = vax - vbx
    dvy = vay - vby

    dist_sq = dx * dx + dy * dy
    speed_sq = dvx * dvx + dvy * dvy
    dot = dx * dvx + dy * dvy
    sep_sq = separation * separation

    # Both stationary. Either overlapping forever or never
    if isclose(speed_sq, 0.0):
        if dist_sq <= sep_sq:
            return -inf, inf # Always overlapping
        else:
            return nan, nan # Never collide

    # Already outside and moving away (or tangent and moving apart)
    if dot >= 0.0 and dist_sq > sep_sq:
        return nan, nan

    # sin check: if angle too wide, paths never intersect within radius band
    cos_theta_sq = (dot * dot) / (dist_sq * speed_sq)
    sin_theta_sq = 1.0 - cos_theta_sq
    min_sin_sq = sep_sq / dist_sq

    if sin_theta_sq > min_sin_sq:
        return nan, nan  # Will miss each other

    # Compute collision time interval centered around closest approach
    root_term = sqrt((sep_sq - dist_sq * sin_theta_sq) / speed_sq)
    t_mid = -dot / speed_sq

    t_enter = t_mid - root_term
    t_exit  = t_mid + root_term

    return t_enter, t_exit


def find_first_leq_zero(
    f: Callable[[float], tuple[float, float, float]],
    a: float,
    b: float,
    tol: float = 1e-12,
    max_iter: int = 20
) -> float:
    """
    Finds the smallest t in [a, b] such that f(t) <= 0, using analytic derivatives.
    f must return (f(t), f'(t), f''(t))
    """

    # Newton's method for root-finding: f(x) == 0
    def newton_root(f: Callable[[float], tuple[float, float, float]], x0: float, x1: float) -> float:
        x = x0
        for _ in range(max_iter):
            fx, dfx, _ = f(x)
            if abs(fx) < tol:
                return x
            if dfx == 0.0 or isnan(dfx):
                x = 0.5 * (x + x1)
                continue
            x_new = x - fx / dfx
            # Clamp to [x0, x1]
            if not (x0 <= x_new <= x1):
                x_new = 0.5 * (x + x1 if fx > 0 else x0 + x)
            if abs(x_new - x) < tol:
                return x_new
            x = x_new
        # Fallback, check both ends
        for t in [x, x0, x1]:
            fx, _, _ = f(t)
            if abs(fx) < tol or fx <= 0:
                return t
        return nan

    # Newton's method for finding minimum: f'(x) == 0
    def newton_minimum(f: Callable[[float], tuple[float, float, float]], a: float, b: float) -> float:
        x = 0.5 * (a + b)
        for _ in range(max_iter):
            _, dfx, ddfx = f(x)
            if abs(dfx) < tol:
                return x
            if ddfx == 0.0 or isnan(ddfx):
                x = 0.5 * (x + b)
                continue
            x_new = x - dfx / ddfx
            if not (a <= x_new <= b):
                x_new = 0.5 * (a + x)
            if abs(x_new - x) < tol:
                return x_new
            x = x_new
        return x

    fa, da, _ = f(a)
    if fa <= 0.0:
        return a

    fb, db, _ = f(b)
    if fb <= 0.0:
        # Bracket [a, b]: Use Newton's method
        return newton_root(f, a, b)

    if da < 0 and db > 0:
        t_min = newton_minimum(f, a, b)
        fmin, _, _ = f(t_min)
        if fmin <= 0.0:
            # Root must be to left of minimum;
            return newton_root(f, a, t_min)
    return nan


def find_first_leq_zero_slow(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-12,
    max_iter: int = 40
) -> float:
    """
    Finds the smallest t in [a, b] such that f(t) <= 0.
    - If f(a) <= 0, returns a.
    - If f(a) > 0 and f(b) <= 0, uses bisection to find the smallest t where f(t) <= 0
    - If f(a) > 0 and f(b) > 0, estimates derivatives at endpoints:
        * If derivative at a < 0 and at b > 0, searches for a minimum (critical point)
        * If minimum dips below zero, finds the leftmost t with bisection
    - Derivative estimation never evaluates f outside [a, b]
    - Returns nan if no such t exists
    """

    def estimate_derivative(f: Callable[[float], float], t: float, a: float, b: float, h: float = 1e-8) -> float:
        """
        Numerically estimates the derivative of f at t, within [a, b]
        - Uses central difference by default
        - Uses forward difference at or near the left endpoint
        - Uses backward difference at or near the right endpoint
        - Does not evaluate f outside [a, b]
        """
        if t - h <= a:
            # Forward difference (clamp to [a, b])
            return (f(min(t + h, b)) - f(t)) / h
        elif t + h >= b:
            # Backward difference (clamp to [a, b])
            return (f(t) - f(max(t - h, a))) / h
        else:
            # Central difference
            return (f(t + h) - f(t - h)) / (2.0 * h)

    def bisect_first_below_zero(
        f: Callable[[float], float], 
        a: float, 
        b: float
    ) -> float:
        """
        Bisection to find smallest t in [a, b] with f(t) <= 0.
        Assumes f(a) > 0, f(b) <= 0.
        """
        for _ in range(max_iter):
            mid: float = 0.5 * (a + b)
            f_mid: float = f(mid)
            if f_mid <= 0.0:
                b = mid
            else:
                a = mid
            if abs(b - a) < tol:
                return b if f(b) <= 0.0 else nan
        return b if f(b) <= 0.0 else nan

    def bisect_derivative_zero(
        f: Callable[[float], float], 
        a: float, 
        b: float
    ) -> float:
        """
        Bisection to find t in [a, b] where derivative is approximately zero
        Assumes derivative(a) < 0, derivative(b) > 0
        This assumes there's no inflection points or any weirdness. The function is assumed to dip down and go back up again at the end of the interval,
        and this looks for the critical point (minimum) in the middle of the interval
        """
        left: float = a
        right: float = b

        for _ in range(max_iter):
            mid: float = 0.5 * (left + right)
            d_mid: float = estimate_derivative(f, mid, a, b)
            if abs(d_mid) < tol:
                return mid
            if d_mid > 0.0:
                # Bring in the right bound
                right = mid
            else:
                # Bring in the left bound
                left = mid
            if abs(right - left) < tol:
                return 0.5 * (left + right)
        return 0.5 * (left + right)

    fa: float = f(a)
    if fa <= 0.0:
        # Bam we have our answer
        return a
    
    fb: float = f(b)
    if fb <= 0.0:
        # f(a) is positive and f(b) is negative. By intermediate value theorem, at least one root exists.
        # By the nature of our problem, only one root will exist. Not possible to have more roots.
        return bisect_first_below_zero(f, a, b)

    da: float = estimate_derivative(f, a, a, b)
    db: float = estimate_derivative(f, b, a, b)
    if da < 0.0 and db > 0.0:
        # The function is positive at endpoints, but it's concave-up over this interval.
        # It might dip down below 0 during this interval! Find the minimum, and check if it's negative.
        t_c: float = bisect_derivative_zero(f, a, b)
        f_tc: float = f(t_c)
        if f_tc <= 0.0:
            return bisect_first_below_zero(f, a, t_c)
    return nan
