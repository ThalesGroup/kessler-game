import math
import random
import pytest

from kesslergame import collisions


def intervals_intersect(a_start, a_end, b_start, b_end):
    """Return True if [a_start, a_end] intersects [b_start, b_end]."""
    return (a_start <= b_end) and (a_end >= b_start)


def assert_time_interval_consistency(
    ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
):
    cont = collisions.circle_line_collision_continuous(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
    )
    t0, t1 = collisions.circle_line_collision_time_interval(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r
    )

    if cont:
        # Continuous says there's a collision within [-dt, 0]
        assert not (math.isnan(t0) and math.isnan(t1)), (
            "Continuous=True but interval NaN"
        )
        # Must intersect the window [-dt, 0]
        assert intervals_intersect(t0, t1, -dt, 0.0), (
            f"Continuous=True but time interval {t0, t1} "
            f"does not intersect [-{dt}, 0]"
        )
    else:
        if math.isnan(t0) and math.isnan(t1):
            # No full collision interval, that's fine
            return
        # If time interval returned finite range, it must be outside [-dt, 0]
        assert not intervals_intersect(t0, t1, -dt, 0.0), (
            f"Continuous=False but time interval {t0, t1} intersects [-{dt}, 0]"
        )


def test_no_relative_motion_touching():
    # Line stationary, circle stationary, already colliding
    ax, ay = -1.0, 0.0
    bx, by = 1.0, 0.0
    lvx, lvy = 0.0, 0.0
    cx, cy = 0.0, 0.0
    cvx, cvy = 0.0, 0.0
    r = 0.5
    dt = 1.0
    # The origin-centered circle of radius 0.5 touches line segment from (-1,0) to (1,0)
    cont = collisions.circle_line_collision_continuous(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
    )
    t0, t1 = collisions.circle_line_collision_time_interval(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r
    )
    assert cont
    assert (t0, t1) == (-math.inf, math.inf)


def test_no_relative_motion_no_contact():
    # Line stationary, circle stationary, far apart
    ax, ay = -1.0, 10.0
    bx, by = 1.0, 10.0
    lvx, lvy = 0.0, 0.0
    cx, cy = 0.0, 0.0
    cvx, cvy = 0.0, 0.0
    r = 1.0
    dt = 1.0
    cont = collisions.circle_line_collision_continuous(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
    )
    t0, t1 = collisions.circle_line_collision_time_interval(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r
    )
    assert not cont
    assert math.isnan(t0) and math.isnan(t1)


def test_grazing_collision():
    # Circle grazes endpoint of moving line
    ax, ay = 0.0, 0.0
    bx, by = 1.0, 0.0
    lvx, lvy = 0.0, 0.0
    # Circle moving horizontally, just grazes point (0,0)
    cx, cy = -2.0, 1.0
    cvx, cvy = 1.0, 0.0
    r = 1.0
    dt = 2.0
    assert_time_interval_consistency(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
    )


@pytest.mark.parametrize("seed", range(10))
def test_randomized_consistency(seed):
    random.seed(seed)
    for _ in range(200_000):
        # Randomize positions and velocities
        ax = random.uniform(-5, 5)
        ay = random.uniform(-5, 5)
        bx = ax + random.uniform(-2, 2)
        by = ay + random.uniform(-2, 2)
        lvx = random.uniform(-3, 3)
        lvy = random.uniform(-3, 3)
        cx = random.uniform(-5, 5)
        cy = random.uniform(-5, 5)
        cvx = random.uniform(-3, 3)
        cvy = random.uniform(-3, 3)
        r = random.uniform(0.5, 3.0)
        dt = random.uniform(0.1, 3.0)

        assert_time_interval_consistency(
            ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
        )


def test_degenerate_segment_point_inside_circle():
    # Segment is a point, inside the circle
    ax = ay = bx = by = 0.0
    lvx = lvy = 0.0
    cx = cy = 0.0
    cvx = cvy = 0.0
    r = 1.0
    dt = 1.0
    cont = collisions.circle_line_collision_continuous(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r, dt
    )
    assert cont
    t0, t1 = collisions.circle_line_collision_time_interval(
        ax, ay, bx, by, lvx, lvy, cx, cy, cvx, cvy, r
    )
    assert (t0, t1) == (-math.inf, math.inf)


def test_discrete_collision_matches_geometry():
    # Circle at origin radius sqrt(2) should just collide with segment from (2,0) to (0,2)
    ax, ay = 2.0, 0.0
    bx, by = 0.0, 2.0
    # Circle centered at origin radius sqrt(2) - EPS should not collide
    assert not collisions.circle_line_collision_discrete(
        ax, ay, bx, by, 0.0, 0.0, math.sqrt(2) - 1e-12
    )
    # But radius sqrt(2) + EPS should collide
    assert collisions.circle_line_collision_discrete(
        ax, ay, bx, by, 0.0, 0.0, math.sqrt(2) + 1e-12
    )
