# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from math import sin, cos, nan, inf, copysign, sqrt, isnan, ceil
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
    Projects point P onto the infinite line defined by segment A(x1, y1) -> B(x2, y2),
    and returns the parametric position t such that:

        (x, y) = (1 - t) * (x1, y1) + t * (x2, y2)

    - t = 0 corresponds to point A
    - t = 1 corresponds to point B
    - t < 0 means the projection falls before A (outside the segment)
    - t > 1 means the projection falls after B (outside the segment)

    Note: The result is not clamped to [0, 1]. This is intentional!!
    If the segment is degenerate (length close to 0), returns NaN.
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
    Returns (dx, dy) using either analytic or Taylor expansion for small omega
    Args:
        v0: initial speed (units/sec)
        a: acceleration (units/sec^2)
        theta0: initial heading (radians)
        omega: turn rate (rad/sec)
        dt: t1 - t0, the time interval to integrate over (seconds)
    """
    if abs(delta_t) < 1e-12:
        # Integrating over basically no time into the future
        return 0.0, 0.0
    if abs(omega) < 0.15:
        # Omega is relatively small, and the divisions in the analytic solution are numerically unstable
        # Use a 3rd order Taylor/Maclaurin series to get a much more accurate result near 0
        # Without this code, with omega near 0, the ship starts teleporting due to floating point wackiness! It's funny
        # The cutoff of 0.15 was found by testing some values for the constants,
        # and making a plot of the absolute error between the Taylor and analytic graphs.
        # 0.15 tends to minimize this max absolute error at below 1e-10, and is the balance point.
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
        # The Sympy code to set up dynamics and integrate is as follows.
        # You may need to algebraically manipulate the result to get it into the same nice form.

        # from sympy import *
        # x0, y0, v0, theta0, omega, delta_x, delta_y, t, delta_t, a = symbols('x0 y0 v0 theta0 omega delta_x delta_y t delta_t a')
        # v_t = v0 + a * t
        # theta_t = theta0 + omega * t
        # delta_x_expr = integrate(v_t * cos(theta_t), (t, 0, delta_t))
        # delta_y_expr = integrate(v_t * sin(theta_t), (t, 0, delta_t))

        delta_theta = omega * delta_t
        theta1 = theta0 + delta_theta
        cos_theta0 = cos(theta0)
        cos_theta1 = cos(theta1)
        sin_theta0 = sin(theta0)
        sin_theta1 = sin(theta1)
        sin_diff = sin_theta1 - sin_theta0
        cos_diff = cos_theta1 - cos_theta0
        omega_reciprocal = 1.0 / omega
        dx = omega_reciprocal * (v0 * sin_diff + omega_reciprocal * (a * (cos_diff + delta_theta * sin_theta1)))
        dy = omega_reciprocal * (-v0 * cos_diff + omega_reciprocal * (a * (sin_diff - delta_theta * cos_theta1)))
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
    if speed_sq < 1e-12:
        if dist_sq <= sep_sq:
            return -inf, inf  # Always overlapping
        else:
            return nan, nan  # Never collide

    # Already outside and moving away (or tangent and moving apart)
    if dot >= 0.0 and dist_sq > sep_sq:
        return nan, nan

    # Avoid division by zero if exactly at same center initially
    if dist_sq < 1e-12:
        # Starts at same point
        root_term = sqrt(sep_sq / speed_sq)
        t_mid = 0.0
        return -root_term, root_term

    # sin check: if angle too wide, paths never intersect within radius band
    cos_theta_sq = (dot * dot) / (dist_sq * speed_sq)
    sin_theta_sq = 1.0 - cos_theta_sq
    # Clamp due to floating point error
    if sin_theta_sq < 0.0:
        sin_theta_sq = 0.0
    elif sin_theta_sq > 1.0:
        sin_theta_sq = 1.0
    min_sin_sq = sep_sq / dist_sq

    if sin_theta_sq > min_sin_sq:
        return nan, nan  # Will miss each other

    # Compute collision time interval centered around closest approach
    discriminant = (sep_sq - dist_sq * sin_theta_sq) / speed_sq
    if discriminant < 0.0:
        return nan, nan  # No real solution

    root_term = sqrt(discriminant)
    t_mid = -dot / speed_sq

    t_enter = t_mid - root_term
    t_exit = t_mid + root_term
    return t_enter, t_exit


def find_first_leq_zero(
    f: Callable[[float], tuple[float, float, float]],
    a: float,
    b: float,
    tol: float = 1e-12,
    max_iterations: int = 80  # This is way overkill, and 30 is probably fine. But this is so rare to use more than just a few iterations, that this won't slow down the game.
) -> float:
    """
    Finds the smallest t in [a, b] such that f(t) <= 0, using Newton's method
    Newton's method is made to return the right endpoint, to be safe and return f(t) <= 0 and not > 0
    This assumes the input function has continuous derivatives, and is smooth!

    The function f must return a triple: (f(t), f'(t), f''(t))
    """

    # Root-finding using Newton's method, with bisection fallback if Newton update jumps out of bounds
    def newton_root(f: Callable[[float], tuple[float, float, float]], x0: float, x1: float) -> float:
        # It's assumed that the input function is a decreasing function, where f(x0) > 0 and f(x1) < 0
        # We assume there's just ONE ROOT
        # If there are multiple roots, this will only return one of them, and it's not guaranteed to return
        # the earliest of them, which is what we need!
        # This will find the point where f(x) == 0
        # More precisely, it finds the smallest x such that f(x) < 0, so slightly past the root!
        x_low, x_high = x0, x1
        x = 0.5 * (x0 + x1)  # Start in the middle
        fx, dfx, _ = f(x)  # Initial evaluation
        for _ in range(max_iterations):
            if -tol < fx <= 0.0:
                return x  # Close enough!

            if abs(dfx) < tol or isnan(dfx):
                # If the slope is 0 or NaN, just do a bisection step
                x_new = 0.5 * (x_low + x_high)
            else:
                x_new = x - fx / dfx  # Newton update!
                # Make sure it's still in [x0, x1]
                if not (x0 <= x_new <= x1):
                    # It's not, so fallback to bisection
                    x_new = 0.5 * (x_low + x_high)
                elif abs(x_new - x) < tol:
                    # The newton step is tiny, and has stalled.
                    # It probably converged
                    return x_new
            x = x_new

            # Update bounds based on sign of f(x)
            fx, dfx, _ = f(x)
            if fx > 0.0:
                # Bisect right
                x_low = x
            else:
                # Bisect left
                x_high = x

            # Check for convergence
            if abs(x_high - x_low) < tol:
                return x_high
        return x_high  # Didn't converge, but just return x_high anyway and hope nothing goes wrong ¯\_(ツ)_/¯

    # Root-finding for f'(x) using Newton's method, with bisection fallback if Newton update jumps out of bounds
    def newton_minimum(f: Callable[[float], tuple[float, float, float]], x0: float, x1: float) -> float:
        # It's assumed that the input function has a local minimum in [x0, x1]
        # We're looking for the point where f'(x) == 0
        # We assume there's just one critical point (minimum or maximum)
        # Assume that f'(x0) < 0 and f'(x1) > 0, so this is an increasing function
        x_low, x_high = x0, x1
        x = 0.5 * (x0 + x1)  # Start in the middle
        _, dfx, ddfx = f(x)  # Initial evaluation
        for _ in range(max_iterations):
            _, dfx, ddfx = f(x)
            if abs(dfx) < tol:
                return x  # Found a minimum (or stationary point)!

            if abs(ddfx) < tol or isnan(ddfx):
                # If the second derivative is 0 or NaN, just do a bisection step
                x_new = 0.5 * (x_low + x_high)
            else:
                x_new = x - dfx / ddfx  # Newton update!
                # Make sure it's still in [x0, x1]
                if not (x0 <= x_new <= x1):
                    # It's not, fallback to bisection
                    x_new = 0.5 * (x_low + x_high)
                elif abs(x_new - x) < tol:
                    # The newton step is tiny, and has stalled.
                    # It probably converged
                    return x_new
            x = x_new

            # Update bounds based on sign of f'(x)
            _, dfx, ddfx = f(x)
            if dfx > 0.0:
                # Bisect left
                x_high = x
            else:
                # Bisect right
                x_low = x

            # Check for convergence
            if abs(x_high - x_low) < tol:
                return x
        return x  # Didn't converge, but just return x anyway and hope nothing goes wrong ¯\_(ツ)_/¯

    # Classic bisection method. Slower but guaranteed if f changes sign
    def bisection_root(f: Callable[[float], tuple[float, float, float]], x0: float, x1: float) -> float:
        f0, _, _ = f(x0)  # Cache initial f(x0)
        f1, _, _ = f(x1)  # Cache initial f(x1)
        assert f0 * f1 <= 0.0
        for _ in range(max_iterations):
            xm = 0.5 * (x0 + x1)
            fm, _, _ = f(xm)
            if -tol < fm <= 0.0:
                return xm  # Close enough!

            # Update the interval based on the sign of fm
            if f0 * fm < 0.0:
                x1 = xm      # Root is in [x0, xm]
                f1 = fm      # f(x1) becomes f(xm)
            else:
                x0 = xm      # Root is in [xm, x1]
                f0 = fm      # f(x0) becomes f(xm)

            if abs(x1 - x0) < tol:
                return x1  # Interval is tiny. return right point, which is hopefully <= 0

        return x1  # Didn't converge, but return our best guess

    def bisection_on_second_derivative(f: Callable[[float], tuple[float, float, float]], x0: float, x1: float) -> float:
        _, _, dd0 = f(x0)
        _, _, dd1 = f(x1)
        assert dd0 * dd1 <= 0.0
        for _ in range(max_iterations):
            xm = 0.5 * (x0 + x1)
            _, _, ddm = f(xm)
            if abs(ddm) < tol:
                return xm
            if dd0 * ddm < 0.0:
                # Bisect left
                x1 = xm
                dd1 = ddm
            else:
                # Bisect right
                x0 = xm
                dd0 = ddm
            if abs(x1 - x0) < tol:
                return xm
        # Didn't converge, but return best guess
        return 0.5 * (x0 + x1)

    # Main logic
    fa, da, dda = f(a)
    if fa <= 0.0:
        return a  # Already satisfies condition at the left endpoint

    fb, db, ddb = f(b)

    if dda * ddb >= 0.0:
        # The second derivative PROBABLY does not change signs in the interval,
        # meaning there is no inflection point and no multiple roots
        if fb <= 0.0:
            # There’s ONLY ONE root somewhere between a and b
            return newton_root(f, a, b)

        # If f is decreasing then increasing (da < 0, db > 0), there may be a minimum inside
        if da < 0.0 and db > 0.0:
            t_min = newton_minimum(f, a, b)
            fmin, _, _ = f(t_min)
            if fmin <= 0.0:
                # The minimum is below zero. Find where it goes from positive to negative
                return newton_root(f, a, t_min)
    else:
        # The concavity of the function (second derivative) changes in this interval, so
        # it's possible that the function can seem to not want to dip down,
        # but actually it has a couple extra turning points in there, and really does dip down!
        # This function could be cubic-shaped.
        t_inflect = bisection_on_second_derivative(f, a, b)
        fi, di, ddi = f(t_inflect)
        if fi <= 0.0:
            # We know fa is positive, so this brackets a single root!
            return newton_root(f, a, t_inflect)
        elif da < 0.0 and di > 0.0:
            # There's a minimum between a and the inflection point! Find it!
            t_min = newton_minimum(f, a, t_inflect)
            fmin, _, _ = f(t_min)
            if fmin <= 0.0:
                return newton_root(f, a, t_min)
        if fb <= 0.0:
            # We know fi is positive, so this brackets a root!
            return newton_root(f, t_inflect, b)
        elif di < 0.0 and db > 0.0:
            # There's a minimum between the inflection point and b! Find it!
            t_min = newton_minimum(f, t_inflect, b)
            fmin, _, _ = f(t_min)
            if fmin <= 0.0:
                return newton_root(f, a, t_min)  # Tempting to do Newton between t_inflect and t_min, but this is safer

    # Hail Mary fallback: brute force sample the interval a bunch lol
    # Nvm, just give up at this point. The juice is not worth the squeeze!
    '''
    N = 100  # Subdivide the interval finely
    for i in range(1, N + 1):
        x0 = a + (b - a) * (i - 1) / N
        x1 = a + (b - a) * i / N
        x0 = max(x0, a)
        x1 = min(x1, b)
        f0, _, _ = f(x0)
        f1, _, _ = f(x1)
        if f0 > 0.0 and f1 <= 0.0:
            # We found a sign change, so apply bisection
            return bisection_root(f, x0, x1)
    '''
    # Dang, couldn't find anything :(
    return nan


def find_first_leq_zero_segmented(
    f: Callable[[float], tuple[float, float, float]],
    a: float,
    b: float,
    tol: float = 1e-12,
    max_iterations: int = 80,
    max_interval_size: float = 0.02
) -> float:
    """
    Wrapper for find_first_leq_zero that segments the interval [a, b]
    into smaller intervals of size <= max_interval_size, to improve robustness
    for poorly-behaved functions.
    """

    if a >= b:
        return nan  # Invalid interval

    n_segments: int = ceil((b - a) / max_interval_size)
    seg_size: float = (b - a) / n_segments

    for i in range(n_segments):
        x0 = a + i * seg_size
        x1 = a + (i + 1) * seg_size
        x1 = min(x1, b)  # Clamp to b, just in case of floating point shenanigans

        result = find_first_leq_zero(f, x0, x1, tol=tol, max_iterations=max_iterations)
        if not isnan(result):
            return result
    return nan  # No zero-crossing found


def find_first_leq_zero_robust_slow(
    f: Callable[[float], tuple[float, float, float]],
    a: float,
    b: float,
    tol: float = 1e-12,
    max_iterations: int = 80
) -> float:
    """
    Finds the smallest t in [a, b] such that f(t) <= 0
    This is used for debugging and cross-checking the fast function. It is slow!

    The function f must return a triple: (f(t), f'(t), f''(t))
    """

    # Classic bisection method. Slower but guaranteed if f changes sign
    def bisection_root(f: Callable[[float], tuple[float, float, float]], x0: float, x1: float) -> float:
        f0, _, _ = f(x0)  # Cache initial f(x0)
        f1, _, _ = f(x1)  # Cache initial f(x1)
        assert f0 * f1 <= 0.0
        for _ in range(max_iterations):
            xm = 0.5 * (x0 + x1)
            fm, _, _ = f(xm)
            if -tol < fm <= 0.0:
                return xm  # Close enough!

            # Update the interval based on the sign of fm
            if f0 * fm < 0.0:
                x1 = xm      # Root is in [x0, xm]
                f1 = fm      # f(x1) becomes f(xm)
            else:
                x0 = xm      # Root is in [xm, x1]
                f0 = fm      # f(x0) becomes f(xm)

            if abs(x1 - x0) < tol:
                return x1  # Interval is tiny. return right point, which is hopefully <= 0

        return x1  # Didn't converge, but return our best guess

    fa, da, dda = f(a)
    if fa <= 0.0:
        return a  # Already satisfies condition at the left endpoint

    # Brute force sample a bunch of intervals
    N = 1000  # Subdivide the interval finely
    for i in range(1, N + 1):
        x0 = a + (b - a) * (i - 1) / N
        x1 = a + (b - a) * i / N
        x0 = max(x0, a)
        x1 = min(x1, b)
        f0, _, _ = f(x0)
        f1, _, _ = f(x1)
        if f0 > 0.0 and f1 <= 0.0:
            # We found a sign change, so apply bisection
            return bisection_root(f, x0, x1)
    return nan


def find_first_leq_zero_no_derivs(
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

    # This is UNUSED. Kept for legacy purposes, but this is not robust or good. Please do not use this.

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
