# Kessler Game: API Documentation

# For version 2.X.X

## Overview

Kessler is a game designed for training and evaluating AI/ML agents in a 2D asteroid-shooter environment. Each frame, the game provides agent-controlled AIs with:

- `game_state` — an instance of the `GameState` class
- `ship_state` — an instance of the `ShipState` class (specific to the agent's ship)

These objects encapsulate the full exact state of the deterministic game.

Agents can interact with these objects using:
- **Python-style property access** (e.g. `ship_state.velocity`)
- **Dictionary-style access** (e.g., `ship_state["velocity"]`)
- **Raw list formats** using `fast_compact()`
- **Classic dictionary format** via `dict()`

IMPORTANT: When the game setting competition_safe_mode is disabled, mutating game_state or ship_state will alter the internal game state, and this is undefined behavior.
Additionally, any references to the data within this may change from frame-to-frame. They may not be static.
If you choose to disable safe mode for the speed benefit, please make sure to interact with these objects in a read-only manner, and copy data out that you would like to store.

---

## `ShipState` (Full Agent State)

Represents the full state of the agent’s own ship, including controls and cooldowns.

### Access Methods:
- `ship_state.position` → `(x, y)` tuple
- `ship_state["position"]`
- `ship_state.dict()` → `ShipOwnStateDict`
- `ship_state.fast_compact()` → `ShipDataList`

### Attributes:

| Name                | Type                 | Description                                |
|---------------------|----------------------|--------------------------------------------|
| `x`, `y`            | `float`              | Position components                        |
| `vx`, `vy`          | `float`              | Velocity components                        |
| `position`          | `tuple[float, float]`| (x, y) coordinate                          |
| `velocity`          | `tuple[float, float]`| (vx, vy) vector                            |
| `speed`             | `float`              | Scalar speed (m/s)                         |
| `heading`           | `float`              | Facing angle (degrees)                     |
| `mass`, `radius`    | `float`              | Physical properties (kg, m)                |
| `id`, `team`        | `int`                | Identifiers                                |
| `is_respawning`     | `bool`               | If the ship is currently respawning        |
| `lives_remaining`   | `int`                | Lives left                                 |
| `deaths`            | `int`                | Total deaths so far                        |

#### Combat + Cooldowns:

| Name                | Type                 | Description                                |
|---------------------|----------------------|--------------------------------------------|
| `bullets_remaining` | `int`                | Remaining bullets                          |
| `mines_remaining`   | `int`                | Remaining mines                            |
| `can_fire`          | `bool`               | Whether ship can fire                      |
| `fire_cooldown`     | `float`              | Time left before firing again (s)          |
| `fire_rate`         | `float`              | Time between shots (s)                     |
| `can_deploy_mine`   | `bool`               | Whether a mine can be deployed             |
| `mine_cooldown`     | `float`              | Time left before deploying another mine (s)|
| `mine_deploy_rate`  | `float`              | Time between mine drops (s)                |

#### Respawn & Movement:

| Name                  | Type                  | Description                                |
|-----------------------|-----------------------|--------------------------------------------|
| `respawn_time_left`   | `float`               | Time until respawn (if respawning)         |
| `respawn_time`        | `float`               | Full respawn duration                      |
| `thrust_range`        | `tuple[float, float]` | Allowed thrust control range               |
| `turn_rate_range`     | `tuple[float, float]` | Allowed turning control range              |
| `max_speed`           | `float`               | Speed cap                                  |
| `drag`                | `float`               | Drag coefficient                           |

---

## `GameState` (Full World State)

### Access Methods:
- `game_state.asteroids` → list of `AsteroidView`
- `game_state["bullets"]`
- `game_state.dict()` → `GameStateDict`
- `game_state.fast_compact()` → `GameStateCompactDict`

### Properties:

| Name                    | Type                     | Description                            |
|-------------------------|--------------------------|----------------------------------------|
| `ships`                 | `list[ShipView]`         | All ships (includes enemies)           |
| `asteroids`             | `list[AsteroidView]`     | Asteroids on screen                    |
| `bullets`               | `list[BulletView]`       | Active bullets                         |
| `mines`                 | `list[MineView]`         | Active mines                           |
| `map_size`              | `tuple[int, int]`        | World boundaries                       |
| `time_limit`            | `float`                  | Match duration in seconds              |
| `time`                  | `float`                  | Elapsed time                           |
| `frame`                 | `int`                    | Current frame number                   |
| `delta_time`            | `float`                  | Seconds per frame                      |
| `frame_rate`            | `float`                  | Target frame rate                      |
| `random_asteroid_splits`| `bool`                   | Asteroid fragmentation randomness      |
| `competition_safe_mode` | `bool`                   | If in fairness-safe mode               |

---

## Compact Representation

### `fast_compact()`
Returns a raw, fast format for training which should be over twice as fast to read the data from.
This is recommended for advanced users who want the maximum speed, and are formatting the input data in their own way.

- `game_state.fast_compact()` → `GameStateCompactDict`
- `ship_state.fast_compact()` → `ShipDataList`

#### Running game_state.fast_compact() might return a dictionary that looks like:
```
{
    "ships": [
        [385.0607585391769, 747.9475394887982, -4.408728476930471e-14, -240.0, 240.0, 270.0, 300.0, 20.0, 1, 1, False, 3, 0]
    ],
    "asteroids": [
        [600.0000000000009, 233.673456, 100.0, -2.4492935982947064e-14, 3, 452.3893421169302, 24.0],
        [500.0, 33.67345800000012, -3.6739403974420595e-14, -200.0, 1, 50.26548245743669, 8.0],
        [500.0, 733.773458, -5.510910596163089e-14, -300.0, 4, 804.247719318987, 32.0],
    ],
    "bullets": [
        [279.15311794985496, 681.3712368493217, -247.21359549995788, 760.8452130361229, 3.708203932499368, -11.412678195541844, 108.0, 1.0, 12.0],
        [42.00744880738853, 340.4369113621759, -647.2135954999578, 470.2282018339786, 9.708203932499368, -7.0534230275096785, 144.0, 1.0, 12.0],
        [66.13819320973143, 24.133503779823066, -800.0, 9.797174393178826e-14, 12.0, -1.4695761589768238e-15, 180.0, 1.0, 12.0],
    ],
    "mines": [],
    "map_size": (1000, 800),
    "time_limit": inf,
    "time": 0.9999999999999999,
    "frame": 30,
    "delta_time": 0.03333333333333333,
    "frame_rate": 30.0,
    "random_asteroid_splits": False,
    "competition_safe_mode": True,
}
```

The schema for ships is:
`[x: float, y: float, vx: float, vy: float, speed: float, heading: float, mass: float, radius: float, id: int, team: int, is_respawning: bool, lives_remaining: int, deaths: int]`

The schema for asteroids is:
`[x: float, y: float, vx: float, vy: float, size: int, mass: float, radius: float]`

The schema for bullets is:
`[x: float, y: float, vx: float, vy: float, tail_dx: float, tail_dy: float, heading: float, mass: float, length: float]`

The schema for mines is:
`[x: float, y: float, mass: float, fuse_time: float, remaining_time: float]`

#### ship_state.fast_compact() may return a single list that looks like:
`[395.29566377267156, 786.1447258308528, -120.00000000000011, -207.84609690826522, 240.0, 240.0, 300.0, 20.0, 1, 1, False, 3, 0, -1, 0, True, 0.0, 10.0, False, 0.0, 1.0, 0.0, 3.0, -480.0, 480.0, -180.0, 180.0, 240.0, 80.0]`

With its schema being:
`[x: float, y: float, vx: float, vy: float, speed: float, heading: float, mass: float, radius: float, id: int, team: int, is_respawning: bool, lives_remaining: int, deaths: int, bullets_remaining: int, mines_remaining: int, can_fire: bool, fire_wait_time: float, fire_rate: float, can_deploy_mine: bool, mine_wait_time: float, mine_deploy_rate: float, respawn_time_left: float, respawn_time: float, thrust_range_min: float, thrust_range_max: float, turn_rate_range_min: float, turn_rate_range_max: float, max_speed: float, drag: float]`

### `dict()`
Returns classic human-readable nested dictionaries:

- `game_state.dict()` → `GameStateDict`
- `ship_state.dict()` → `ShipOwnStateDict`

A GameStateDict may look like:
```
{
    "ships": [
        {
            "position": (399.65078544722854, 792.8510251106526),
            "velocity": (-141.06846055019358, -194.16407864998737),
            "speed": 240.0,
            "heading": 234.0,
            "mass": 300.0,
            "radius": 20.0,
            "id": 1,
            "team": 1,
            "is_respawning": False,
            "lives_remaining": 3,
            "deaths": 0,
        }
    ],
    "asteroids": [
        {
            "position": (580.0000000000007, 233.673456),
            "velocity": (100.0, -2.4492935982947064e-14),
            "size": 3,
            "mass": 452.3893421169302,
            "radius": 24.0,
        },
        {
            "position": (500.0, 73.67345800000011),
            "velocity": (-3.6739403974420595e-14, -200.0),
            "size": 1,
            "mass": 50.26548245743669,
            "radius": 8.0,
        },
        {
            "position": (500.0, 793.773458),
            "velocity": (-5.510910596163089e-14, -300.0),
            "size": 4,
            "mass": 804.247719318987,
            "radius": 32.0,
        },
    ],
    "bullets": [
        {
            "position": (328.5958370498464, 529.2021942420971),
            "velocity": (-247.21359549995788, 760.8452130361229),
            "tail_delta": (3.708203932499368, -11.412678195541844),
            "heading": 108.0,
            "mass": 1.0,
            "length": 12.0,
        },
    ],
    "mines": [
        {
            "position": (500.0, 1.0),
            "mass": 25.0,
            "fuse_time": 3.0,
            "remaining_time": 2.100000000000003,
        }
    ],
    "map_size": (1000, 800),
    "time_limit": inf,
    "time": 0.7999999999999999,
    "frame": 24,
    "delta_time": 0.03333333333333333,
    "frame_rate": 30.0,
    "random_asteroid_splits": False,
    "competition_safe_mode": True,
}
```

A ShipOwnStateDict may look like:
```
{
    "position": (410.3373183067637, 4.719622244585683),
    "velocity": (-178.35475811457462, -160.59134552612596),
    "speed": 240.0,
    "heading": 222.0,
    "mass": 300.0,
    "radius": 20.0,
    "id": 1,
    "team": 1,
    "is_respawning": False,
    "lives_remaining": 3,
    "deaths": 0,
    "bullets_remaining": -1,
    "mines_remaining": 0,
    "can_fire": True,
    "fire_cooldown": 0.0,
    "fire_rate": 10.0,
    "can_deploy_mine": False,
    "mine_cooldown": 0.0,
    "mine_deploy_rate": 1.0,
    "respawn_time_left": 0.0,
    "respawn_time": 3.0,
    "thrust_range": (-480.0, 480.0),
    "turn_rate_range": (-180.0, 180.0),
    "max_speed": 240.0,
    "drag": 80.0,
}
```

---

## `ShipView`, `AsteroidView`, `BulletView`, `MineView`

These are wrappers over raw lists and allow attribute-style and dictionary-style access to individual game entities.

Any attribute that is available in the dictionary view will also be available as attributes.

Attribute access is recommended for simplicity, and there are some shorthands. For example: `asteroid.x, asteroid.y, asteroid.vx, asteroid.vy` are simpler ways to get the position and velocity compared to
`asteroid["position"][0], asteroid["position"][1], asteroid["velocity"][0], asteroid["velocity"][1]`

### Example (for any View):

```python
asteroid = game_state.asteroids[0]
print(asteroid.x, asteroid.velocity)         # via properties
print(asteroid["x"], asteroid["velocity"])   # via dict-like access
