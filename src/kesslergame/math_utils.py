# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from math import sin, cos, nan, inf, copysign, sqrt
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
    if abs(delta_t) < 1e-15:
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

def find_first_leq_zero(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-8,
    max_iter: int = 50
) -> float:
    """
    Finds the smallest value t in [a, b] such that f(t) <= 0.
    If no such t exists, returns nan.
    Strategy:
    - If f(a) <= 0, return a.
    - If f(a) > 0 and f(b) <= 0, bisect for smallest t where f(t) <= 0.
    - If f(a) > 0 and f(b) > 0, estimate derivatives. if critical point found, it's a min so search for it.
      If min is below zero, bisect to find leftmost solution.
    - Otherwise, return nan.
    Parameters:
        f (Callable[[float], float]): The function to evaluate.
        a (float): Lower bound of the interval.
        b (float): Upper bound of the interval.
        tol (float): Tolerance for root finding.
        max_iter (int): Maximum bisection iterations.
    Returns:
        float: The smallest t in [a,b] with f(t)<=0, or nan if none exists.
    """

    def estimate_derivative(f: Callable[[float], float], x: float, h: float = 1e-8) -> float:
        """
        Estimate the derivative of f at x via finite difference.
        """
        return (f(x + h) - f(x)) / h

    def bisect_first_below_zero(
        f: Callable[[float], float], 
        left: float, 
        right: float
    ) -> float:
        """
        Standard bisection to find smallest t in [left, right] with f(t) <= 0.
        Assumes f(left) > 0, f(right) <= 0.
        """
        for _ in range(max_iter):
            mid: float = (left + right) / 2
            if f(mid) <= 0:
                right = mid
            else:
                left = mid
            if abs(right - left) < tol:
                return right if f(right) <= 0 else nan
        return right if f(right) <= 0 else nan

    def bisect_derivative_zero(
        f: Callable[[float], float],
        left: float,
        right: float
    ) -> float:
        """
        Bisection search for t in [left, right] where f'(t) = 0.
        Assumes f'(left) < 0, f'(right) > 0.
        Returns approximate critical point.
        """
        for _ in range(max_iter):
            mid: float = (left + right) / 2
            d_left: float = estimate_derivative(f, left)
            d_mid: float = estimate_derivative(f, mid)

            if d_left * d_mid <= 0:
                right = mid
            else:
                left = mid
            if abs(right - left) < tol:
                return (left + right) / 2
        return (left + right) / 2

    fa: float = f(a)
    fb: float = f(b)
    if fa <= 0:
        return a
    if fb <= 0:
        return bisect_first_below_zero(f, a, b)

    # Estimate derivatives at endpoints
    da: float = estimate_derivative(f, a)
    db: float = estimate_derivative(f, b)
    if da < 0 and db > 0:
        # Possible minimum inside
        t_c: float = bisect_derivative_zero(f, a, b)
        f_tc: float = f(t_c)
        if f_tc <= 0:
            # Bisect for first zero between a and t_c
            return bisect_first_below_zero(f, a, t_c)

    # Otherwise: no such t
    return nan
