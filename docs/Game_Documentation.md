# Kessler Game: API Documentation

# For version 2.X.X

## Overview

Kessler is a game designed for training and evaluating AI/ML agents in a 2D asteroid-shooter environment. Each frame, the game provides agent-controlled AIs with:

- `game_state` — an instance of the `GameState` class
- `ship_state` — an instance of the `ShipState` class (specific to the agent's ship)

Agents can interact with these objects using:
- **Python-style property access**
- **Dictionary-style access (e.g., `ship_state["velocity"]`)**
- **Raw list formats** using `fast_compact()`
- **Classic dictionary format** via `dict()`

---

## `ShipState` (Per-Agent State)

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
| `speed`             | `float`              | Scalar speed                               |
| `heading`           | `float`              | Facing angle (radians)                     |
| `mass`, `radius`    | `float`              | Physical properties                        |
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
| `fire_cooldown`     | `float`              | Time left before firing again              |
| `fire_rate`         | `float`              | Seconds between shots                      |
| `can_deploy_mine`   | `bool`               | Whether a mine can be deployed             |
| `mine_cooldown`     | `float`              | Time left before deploying another mine    |
| `mine_deploy_rate`  | `float`              | Seconds between mine drops                 |

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

## Compact Representations

### `fast_compact()`
Returns a raw, fast format for training:

- `game_state.fast_compact()` → `GameStateCompactDict`
- `ship_state.fast_compact()` → `ShipDataList`

### `dict()`
Returns classic human-readable nested dictionaries:

- `game_state.dict()` → `GameStateDict`
- `ship_state.dict()` → `ShipOwnStateDict`

---

## `ShipView`, `AsteroidView`, `BulletView`, `MineView`

These are wrappers over raw lists and allow attribute-style and dictionary-style access to individual game entities.

### Example (for any View):

```python
asteroid = game_state.asteroids[0]
print(asteroid.x, asteroid.velocity)         # via properties
print(asteroid["x"], asteroid["velocity"])   # via dict-like access
print(asteroid.dict())                       # classic dict format
