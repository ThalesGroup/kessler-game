# Kessler Game - Settings Documentation

This document outlines all configurable settings for the `KesslerGame` class. These settings allow users to customize gameplay behavior, performance, and visual feedback.

## Initialization

To initialize a `KesslerGame`, pass a dictionary of settings to the constructor:

```python
game = KesslerGame(settings=game_settings)
```

---

## 🔧 Game Settings

| Setting                 | Type                      | Default                           | Description                                                                               |
| ----------------------- | ------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------- |
| `frequency`             | `float`                   | `30.0`                            | Target number of updates per second (Hz).                                                 |
| `delta_time`            | `float`                   | `1.0 / frequency`                 | Time (in seconds) between simulation steps. Calculated automatically.                     |
| `perf_tracker`          | `bool`                    | `False`                           | Enables performance tracking features.                                                    |
| `prints_on`             | `bool`                    | `True`                            | Enables or disables debug printing.                                                       |
| `graphics_type`         | `GraphicsType` enum       | `GraphicsType.Tkinter`            | Graphics engine to use. Options include: `NoGraphics`, `Tkinter`, or `UnrealEngine`.      |
| `graphics_obj`          | `KesslerGraphics or None` | `None`                            | Custom graphics object instance, if applicable.                                           |
| `realtime_multiplier`   | `float`                   | `1.0` (or `0.0` for `NoGraphics`) | Controls simulation speed. `1.0` is real-time, higher values speed up the game.           |
| `time_limit`            | `float`                   | `math.inf`                        | Time (in seconds) after which the game stops automatically.                               |
| `random_ast_splits`     | `bool`                    | `False`                           | Whether asteroids split into random sizes upon destruction.                               |
| `competition_safe_mode` | `bool`                    | `True`                            | Disables features not allowed in competition environments (e.g., certain visual outputs). |

---

## UI Settings (`UI_settings`)

The `UI_settings` field controls which HUD/UI elements are shown during the game.

| Key                 | Type    | Default | Description                              |
| ------------------- | ------- | ------- | ---------------------------------------- |
| `ships`             | `bool`  | `True`  | Displays ship locations.                 |
| `lives_remaining`   | `bool`  | `True`  | Shows how many lives are left.           |
| `accuracy`          | `bool`  | `True`  | Displays accuracy stats.                 |
| `asteroids_hit`     | `bool`  | `True`  | Shows number of asteroids hit.           |
| `shots_fired`       | `bool`  | `False` | (Optional) Tracks number of shots fired. |
| `bullets_remaining` | `bool`  | `True`  | Displays remaining bullets.              |
| `controller_name`   | `bool`  | `True`  | Shows the controller’s name.             |
| `scale`             | `float` | `1.0`   | Scaling factor for UI size.              |

### Special Values

* `'all'`: Use `'all'` to enable all available UI elements with a default scale of `1.0`.

```python
"UI_settings": "all"
```

---

## Example Configuration

```python
from kessler_sim.graphics import GraphicsType

# Define Game Settings
game_settings = {
    'perf_tracker': True,
    'graphics_type': GraphicsType.NoGraphics if not GRAPHICS else GraphicsType.Tkinter,
    'realtime_multiplier': 1.0,
    'graphics_obj': None,
    'frequency': 30.0,
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
```

---

## Notes

* If `settings` is `None`, all values fall back to their defaults.
* The `UI_settings` dictionary can be partial; unspecified keys will fall back to default behavior.
* Enums such as `GraphicsType` must be properly imported before use.
