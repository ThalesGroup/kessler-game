# Kessler Game - Settings Documentation

This document outlines all configurable settings for the `KesslerGame` class. These settings allow users to customize gameplay behavior, performance, and visual feedback.

## Initialization

To initialize a `KesslerGame`, pass a dictionary of settings to the constructor:

```python
from kesslergame import Scenario, KesslerGame, GraphicsType

game = KesslerGame(settings=game_settings)
```

---

## 🔧 Game Settings

| Setting                 | Type                      | Default                           | Description                                                                                   |
| ----------------------- | ------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------- |
| `frequency`             | `float`                   | `30.0`                            | Target number of updates per second (Hz).                                                     |
| `delta_time`            | `float`                   | `1.0 / frequency`                 | Time (in seconds) between simulation steps. Calculated automatically.                         |
| `perf_tracker`          | `bool`                    | `False`                           | Enables performance tracking features. Slight performance hit of a few percent.               |
| `prints_on`             | `bool`                    | `True`                            | Enables or disables debug printing (currently unused)                                         |
| `graphics_type`         | `GraphicsType` enum       | `GraphicsType.Tkinter`            | Graphics engine to use. Options include: `NoGraphics`, `Tkinter`, or `UnrealEngine`.          |
| `graphics_obj`          | `KesslerGraphics or None` | `None`                            | Custom graphics object instance, if applicable.                                               |
| `realtime_multiplier`   | `float`                   | `1.0` (or `0.0` for `NoGraphics`) | Controls simulation speed. `1.0` is real-time, higher values speed up the game. 0 is max speed|
| `frame_skip`            | `int`                     | `max(1, round(realtime_multiplier))` | Renders 1 out of every frame_skip frames. Helps graphics keep up with higher game speeds |
| `time_limit`            | `float`                   | `inf`                        | Time (s) after which the scenario stops. Overrides limit defined in Scenario.                 |
| `random_ast_splits`     | `bool`                    | `False`                           | Whether asteroids split at random angles upon destruction                                     |
| `competition_safe_mode` | `bool`                    | `True`                            | False sends mutable game_state and ship_state. This is a bit faster, but riskier             |

---

## UI Settings (`UI_settings`)

The `UI_settings` field controls which HUD/UI elements are shown during the game.

| Key                 | Type    | Default | Description                                |
| ------------------- | ------- | ------- | ------------------------------------------ |
| `ships`             | `bool`  | `True`  | Displays ships         .                   |
| `lives_remaining`   | `bool`  | `True`  | Shows how many lives are left.             |
| `accuracy`          | `bool`  | `True`  | Displays accuracy percentage               |
| `asteroids_hit`     | `bool`  | `True`  | Shows number of asteroids hit by each team |
| `shots_fired`       | `bool`  | `False` | Tracks number of shots fired.              |
| `bullets_remaining` | `bool`  | `True`  | Displays remaining bullets.                |
| `controller_name`   | `bool`  | `True`  | Shows the controller’s name.               |
| `scale`             | `float` | `1.0`   | Scaling factor for UI size.                |

### Special Values

* `'all'`: Use `'all'` to enable all available UI elements, and with a default UI scale of `1.0`.

```python
"UI_settings": "all"
```

---

## Example Configuration

```python
from kesslergame import KesslerGame, Scenario, GraphicsType
from my_controller import MyController

# Define Game Settings
game_settings = {
    'perf_tracker': True,
    'graphics_type': GraphicsType.Tkinter,
    'realtime_multiplier': 1.0,
    'graphics_obj': None,
    'frequency': 30,
    'UI_settings': {
        'ships': True,
        'lives_remaining': True,
        'accuracy': True,
        'asteroids_hit': True,
        'shots_fired': True,
        'bullets_remaining': True,
        'controller_name': True,
        'scale': 2.0
    }
}

game = KesslerGame(settings=game_settings)

my_controllers = [MyController(), MyController()]

my_scenario = Scenario(
    name="My Scenario",
    asteroid_states=[{"position": (100, 200), "angle": 45.0, "speed": 50, "size": 3}],
    ship_states=[{"position": (500, 400), "angle": 90}],
    map_size=(1000, 800),
    time_limit=30,
    seed=0
)

score, perf_data = game.run(scenario=my_scenario, controllers=my_controllers)
```

---

## Notes

* If running the game on a high DPI monitor, using a higher scale factor like 1.5 or 2.0 is recommended for easier viewing.
* If `settings` is `None`, all values fall back to their defaults.
* The `UI_settings` dictionary can be partial; unspecified keys will fall back to default behavior.
* Enums such as `GraphicsType` must be properly imported before use.
