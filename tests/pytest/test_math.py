import random
import math
import pytest
from kesslergame import math_utils

def approx_equal(a, b, tol=1e-9):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)

# -------------------------------
# Tests for solve_quadratic
# -------------------------------

def test_solve_quadratic_known_roots_many():
    random.seed(1)
    for _ in range(100000):
        r1 = random.uniform(-1e3, 1e3)
        r2 = random.uniform(-1e3, 1e3)
        a = 1.0
        b = -(r1 + r2)
        c = r1 * r2
        x0, x1 = math_utils.solve_quadratic(a, b, c)
        expected_roots = sorted((r1, r2))
        actual_roots = sorted((x0, x1))
        assert approx_equal(expected_roots[0], actual_roots[0])
        assert approx_equal(expected_roots[1], actual_roots[1])

def test_solve_quadratic_no_real_roots():
    x0, x1 = math_utils.solve_quadratic(1, 0, 1)
    assert math.isnan(x0) and math.isnan(x1)

def test_solve_quadratic_linear_case():
    x0, x1 = math_utils.solve_quadratic(0, 2, -4)
    assert approx_equal(x0, 2.0)
    assert approx_equal(x1, 2.0)

def test_solve_quadratic_all_zero_deg():
    x0, x1 = math_utils.solve_quadratic(0, 0, 0)
    assert approx_equal(x0, 0.0)
    assert approx_equal(x1, 0.0)

def test_solve_quadratic_linear_unsolvable():
    x0, x1 = math_utils.solve_quadratic(0, 0, 5)
    assert math.isnan(x0) and math.isnan(x1)

# -------------------------------
# project_point_onto_segment_and_get_t
# -------------------------------

def test_project_point_on_segment_basic():
    t = math_utils.project_point_onto_segment_and_get_t(0, 0, 10, 0, 5, 0)
    assert approx_equal(t, 0.5)
    t = math_utils.project_point_onto_segment_and_get_t(0, 0, 10, 0, -5, 0)
    assert t < 0
    t = math_utils.project_point_onto_segment_and_get_t(0, 0, 10, 0, 15, 0)
    assert t > 1

def test_project_point_segment_degenerate():
    t = math_utils.project_point_onto_segment_and_get_t(0, 0, 0, 0, 1, 1)
    assert math.isnan(t)

# -------------------------------
# analytic_ship_movement_integration
# -------------------------------

def rk4_integrate_ship(v0, a, theta0, omega, delta_t, n_steps):
    """Integrates the ship motion ODE using classical RK4. Returns (dx, dy)."""
    h = delta_t / n_steps
    x = 0.0
    y = 0.0
    v = v0
    theta = theta0
    for _ in range(n_steps):
        k1_x = v * math.cos(theta)
        k1_y = v * math.sin(theta)
        k1_v = a
        k1_theta = omega

        v_mid = v + 0.5 * h * k1_v
        theta_mid = theta + 0.5 * h * k1_theta
        k2_x = v_mid * math.cos(theta_mid)
        k2_y = v_mid * math.sin(theta_mid)
        k2_v = a
        k2_theta = omega

        v_mid = v + 0.5 * h * k2_v
        theta_mid = theta + 0.5 * h * k2_theta
        k3_x = v_mid * math.cos(theta_mid)
        k3_y = v_mid * math.sin(theta_mid)
        k3_v = a
        k3_theta = omega

        v_end = v + h * k3_v
        theta_end = theta + h * k3_theta
        k4_x = v_end * math.cos(theta_end)
        k4_y = v_end * math.sin(theta_end)
        k4_v = a
        k4_theta = omega

        x += (h / 6.0) * (k1_x + 2*k2_x + 2*k3_x + k4_x)
        y += (h / 6.0) * (k1_y + 2*k2_y + 2*k3_y + k4_y)
        v += (h / 6.0) * (k1_v + 2*k2_v + 2*k3_v + k4_v)
        theta += (h / 6.0) * (k1_theta + 2*k2_theta + 2*k3_theta + k4_theta)
    return x, y


def test_ship_integrator_matches_rk4_baseline():
    """
    Ensure analytic_ship_movement_integration matches a high-accuracy RK4
    numerical integration for both small-omega (Taylor) and normal branches.
    """
    v0, a, theta0, delta_t = 10.0, 2.0, 0.3, 1.0
    for omega in [0.0, 1e-4, 0.05, 0.5]:  # test both regimes
        dx_exact, dy_exact = math_utils.analytic_ship_movement_integration(v0, a, theta0, omega, delta_t)
        dx_rk4, dy_rk4 = rk4_integrate_ship(v0, a, theta0, omega, delta_t, n_steps=2000)
        assert math.isclose(dx_exact, dx_rk4, rel_tol=1e-9, abs_tol=1e-6)
        assert math.isclose(dy_exact, dy_rk4, rel_tol=1e-9, abs_tol=1e-6)


def test_ship_integrator_fuzz_against_rk4():
    """
    Fuzz test analytic_ship_movement_integration vs RK4.
    Randomizes parameters to hit both branches and wide ranges.
    """
    random.seed(0)
    for _ in range(1000):
        v0 = random.uniform(-100, 100)        # can handle backwards?
        a = random.uniform(-50, 50)
        theta0 = random.uniform(-math.pi, math.pi)
        omega = random.uniform(-1.0, 1.0)     # includes small and large |omega|
        delta_t = random.uniform(1e-4, 0.2)   # short & long integration

        dx_exact, dy_exact = math_utils.analytic_ship_movement_integration(v0, a, theta0, omega, delta_t)
        dx_rk4, dy_rk4 = rk4_integrate_ship(v0, a, theta0, omega, delta_t, n_steps=5000)

        assert math.isclose(dx_exact, dx_rk4, rel_tol=1e-9, abs_tol=1e-7), \
            f"dx mismatch: params={(v0,a,theta0,omega,delta_t)}, exact={dx_exact}, rk4={dx_rk4}"
        assert math.isclose(dy_exact, dy_rk4, rel_tol=1e-9, abs_tol=1e-7), \
            f"dy mismatch: params={(v0,a,theta0,omega,delta_t)}, exact={dy_exact}, rk4={dy_rk4}"

# -------------------------------
# circle_circle_collision_time_interval
# -------------------------------

def test_circle_circle_collision_simple():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 1, 0, 1.0,
        10, 0, -1, 0, 1.0
    )  # moving toward each other
    assert approx_equal(t_enter, 4.0)
    assert approx_equal(t_exit, 6.0)

def test_circle_circle_collision_no_collision():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 1, 0, 1.0,
        10, 0, 1, 0, 1.0
    )  # moving apart
    assert math.isnan(t_enter) and math.isnan(t_exit)

def test_circle_circle_collision_always():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 0, 0, 5.0,
        0, 0, 0, 0, 5.0
    )  # same location, big radius
    assert t_enter == -math.inf and t_exit == math.inf

def test_circle_circle_collision_tangent():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 0, 1, 1.0,
        0, 2, 0, -1, 1.0
    )
    assert approx_equal(t_enter, 0.0)
    assert approx_equal(t_exit, 2.0)

def test_circle_circle_collision_grazing():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 1, 0, 1.0,
        0, 3.01, -1, 0, 1.0
    )
    # Minimum separation is > 2, so no collision
    assert math.isnan(t_enter) and math.isnan(t_exit)

def test_circle_circle_collision_coincident_no_radii():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 0, 0, 0.0,
        0, 0, 0, 0, 0.0
    )
    # Points that intersect forever
    assert math.isinf(t_enter) and t_enter == float('-inf')
    assert math.isinf(t_exit) and t_exit == float('inf')

def test_circle_circle_collision_coincident_moving():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 1, 0, 1.0,
        0, 0, -1, 0, 1.0
    )
    # Start overlapped, moving apart
    assert approx_equal(t_enter, -1.0) and approx_equal(t_exit, 1.0)

def test_circle_circle_collision_one_stationary():
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 0, 0, 1.0,
        3, 0, -1, 0, 1.0
    )
    # moving toward each other
    assert approx_equal(t_enter, 1.0)
    assert approx_equal(t_exit, 5.0)

def test_circle_circle_collision_divzero():
    # Both delta x/y and delta vx/vy exactly zero (should not crash)
    t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
        0, 0, 1, 1, 1.0,
        0, 0, 1, 1, 1.0
    )
    assert t_enter == -math.inf and t_exit == math.inf  # Always overlapping, moving together

def test_circle_circle_collision_fuzz():
    for _ in range(100000):
        ax = random.uniform(-1000, 1000)
        ay = random.uniform(-1000, 1000)
        bx = random.uniform(-1000, 1000)
        by = random.uniform(-1000, 1000)
        vax = random.uniform(-100, 100)
        vay = random.uniform(-100, 100)
        vbx = random.uniform(-100, 100)
        vby = random.uniform(-100, 100)
        ra  = abs(random.gauss(1, 30))
        rb  = abs(random.gauss(1, 30))
        t_enter, t_exit = math_utils.circle_circle_collision_time_interval(
            ax, ay, vax, vay, ra, bx, by, vbx, vby, rb
        )
        # Should be real numbers, nans, or inf, but *never* crash nor non-real non-nan
        assert isinstance(t_enter, float) and isinstance(t_exit, float)

# -------------------------------
# find_first_leq_zero
# -------------------------------

def test_find_first_leq_zero_linear():
    # Looking for the first t where value <= 0 in [0, 5]
    f = lambda t: (-t + 2, -1, 0)  # decreasing to zero at t=2
    t = math_utils.find_first_leq_zero(f, 0, 5)
    assert approx_equal(t, 2.0)

def test_find_first_leq_zero_quadratic_minimum():
    # f(t) = (t-2)^2 - 1: roots at 1, 3
    f = lambda t: ((t - 2)**2 - 1, 2*(t - 2), 2.0)
    t = math_utils.find_first_leq_zero(f, 0, 5)
    assert approx_equal(t, 1.0)

def test_find_first_leq_zero_no_crossing():
    f = lambda t: (t**2 + 1, 2*t, 2.0)
    t = math_utils.find_first_leq_zero(f, 0, 5)
    assert math.isnan(t)

def test_segmentation_vs_slow():
    def quad_f(t):
        return ((t - 1)**2 - 0.25, 2*(t - 1), 2.0)
    slow = math_utils.find_first_leq_zero_robust_slow(quad_f, 0, 5)
    seg  = math_utils.find_first_leq_zero_segmented(quad_f, 0, 5, max_interval_size=0.5)
    assert approx_equal(slow, seg)
