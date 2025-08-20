# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from typing import Any, Mapping, TypeVar, Callable, TypedDict, NoReturn
from math import isfinite, isnan, inf, isinf

from .settings_dicts import SettingsDict, UISettingsDict


T = TypeVar('T')
E = TypeVar('E')


def raise_(ex: Exception) -> NoReturn:
    raise ex


def is_numpy_scalar(obj: Any) -> bool:
    # Without importing numpy
    return type(obj).__module__.startswith("numpy") and hasattr(obj, "item") and callable(getattr(obj, "item", None))


def coerce_float(val: Any) -> float:
    """Casts val to Python float, accepting int, float, np.float_, etc."""
    if isinstance(val, float):
        return val
    if isinstance(val, int):
        return float(val)
    if is_numpy_scalar(val):
        return float(val.item())
    raise TypeError(f"Expected float-like value, got {type(val)}")


def coerce_int(val: Any) -> int:
    """Casts val to int, accepting int, np.int_, etc."""
    if isinstance(val, int):
        return val
    if is_numpy_scalar(val):
        return int(val.item())
    raise TypeError(f"Expected int-like value, got {type(val)}")


def coerce_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    raise TypeError(f"Expected bool value, got {type(val)}")


def coerce_enum(enum_type: type[E], val: Any) -> E:
    if isinstance(val, enum_type):
        return val
    raise TypeError(f"Expected {enum_type.__name__} value, got {type(val)}")


def validate_number(
    val: float,
    *,
    min_val: float | None = None,
    max_val: float | None = None,
    allow_zero: bool = True,
    allow_inf: bool = False,
    allow_nan: bool = False,
    field: str = "value",
) -> float:
    if not isinstance(val, float):
        raise TypeError(f"{field} must be a float, got {type(val)}")
    if isnan(val):
        if not allow_nan:
            raise ValueError(f"{field} cannot be NaN.")
    elif not isfinite(val):
        if not allow_inf:
            raise ValueError(f"{field} cannot be infinite.")
        elif val < 0.0:
            raise ValueError(f"{field} cannot be negative infinity")
    else:
        if min_val is not None and val < min_val:
            raise ValueError(f"{field} must be >= {min_val}, got {val}")
        if max_val is not None and val > max_val:
            raise ValueError(f"{field} must be <= {max_val}, got {val}")
        if not allow_zero and val == 0.0:
            raise ValueError(f"{field} cannot be zero.")
    return val


class UISchemaEntry(TypedDict, total=False):
    type: Callable[[Any], Any]
    default: Any
    min: float
    max: float


UI_SETTINGS_SCHEMA: dict[str, UISchemaEntry] = {
    'ships': {'type': coerce_bool, 'default': True},
    'lives_remaining': {'type': coerce_bool, 'default': True},
    'accuracy': {'type': coerce_bool, 'default': True},
    'asteroids_hit': {'type': coerce_bool, 'default': True},
    'shots_fired': {'type': coerce_bool, 'default': True},
    'bullets_remaining': {'type': coerce_bool, 'default': True},
    'controller_name': {'type': coerce_bool, 'default': True},
    'scale': {'type': coerce_float, 'default': 1.0, 'min': 0.0}
}


def validate_ui_settings(ui: UISettingsDict) -> UISettingsDict:
    out: UISettingsDict = {}
    allowed_keys = set(UI_SETTINGS_SCHEMA)
    extra = set(ui) - allowed_keys
    if extra:
        raise ValueError(f"UI_settings contains unknown keys: {extra}")
    for k, spec in UI_SETTINGS_SCHEMA.items():
        if k in ui:
            try:
                val = spec['type'](ui[k])  # type: ignore[literal-required]
            except Exception as te:
                raise type(te)(f"UI_settings['{k}'] is invalid: {te} (got value {ui[k]!r})") from te  # type: ignore[literal-required]
            # min/max constraints if provided
            if 'min' in spec or 'max' in spec:
                try:
                    val = validate_number(
                        val,
                        min_val=spec.get('min'),
                        max_val=spec.get('max'),
                        field=f"UI_settings['{k}']"
                    )
                except Exception as ve:
                    raise type(ve)(f"UI_settings['{k}'] validation failed: {ve}") from ve
            out[k] = val  # type: ignore[literal-required]
        else:
            out[k] = spec['default']  # type: ignore[literal-required]
    return out


def validate_game_settings(
    settings: SettingsDict,
    GraphicsType: Any,
    KesslerGraphics: type
) -> SettingsDict:
    SCHEMA: dict[str, dict[str, Any]] = {
        'frequency': {'type': coerce_float, 'default': 30.0, 'min': 0.0, 'field': 'frequency'},
        'perf_tracker': {'type': coerce_bool, 'default': False},
        'prints_on': {'type': coerce_bool, 'default': True},
        'graphics_type': {'type': lambda v: coerce_enum(GraphicsType, v), 'default': GraphicsType.Tkinter},
        'graphics_obj': {'type': lambda v: v if (v is None or isinstance(v, KesslerGraphics)) else raise_(TypeError("graphics_obj must be KesslerGraphics or None")), 'default': None},
        # Special logic for default depends on graphics_type
        'realtime_multiplier': {'type': coerce_float, 'default': None, 'min': 0.0, 'field': 'realtime_multiplier'},
        'frame_skip': {'type': coerce_int, 'default': None, 'min': 1, 'field': 'frame_skip'},
        'time_limit': {'type': coerce_float, 'default': inf, 'min': 0.0, 'allow_inf': True, 'field': 'time_limit'},
        'random_ast_splits': {'type': coerce_bool, 'default': False},
        'competition_safe_mode': {'type': coerce_bool, 'default': True},
        'UI_settings': {'type': lambda v: validate_ui_settings(v), 'default': None}
    }
    out: SettingsDict = {}
    for k, spec in SCHEMA.items():
        if k == 'realtime_multiplier':
            # Needs default based on graphics_type (has to be validated *after* graphics_type)
            continue
        if k == 'frame_skip':
            continue
        if k == 'UI_settings':
            continue

        # Coercion/type validation and error wrapping
        try:
            if k in settings:
                val = spec['type'](settings[k])  # type: ignore[literal-required]
            else:
                val = spec['default']
        except Exception as te:
            raise type(te)(f"game_settings['{k}'] is invalid: {te} (got value {settings.get(k, None)!r})") from te

        # Further min/max/inf/nan value validation, error wrapped
        if any(key in spec for key in ('min', 'max', 'allow_inf', 'allow_nan')):
            try:
                val = validate_number(
                    val,
                    min_val=spec.get('min'),
                    max_val=spec.get('max'),
                    allow_inf=spec.get('allow_inf', False),
                    allow_nan=spec.get('allow_nan', False),
                    field=spec.get('field', k)
                )
            except Exception as ve:
                raise type(ve)(f"game_settings['{k}'] validation failed: {ve}") from ve

        out[k] = val  # type: ignore[literal-required]

    # Default logic for realtime_multiplier depends on graphics_type (0 if NoGraphics, 1 otherwise)
    graphics_type = out['graphics_type']
    try:
        if 'realtime_multiplier' in settings:
            rt_mult = coerce_float(settings['realtime_multiplier'])
        else:
            rt_mult = 0.0 if getattr(graphics_type, "name", None) == "NoGraphics" else 1.0
        # Validate min/max if required
        spec = SCHEMA['realtime_multiplier']
        if rt_mult is not None and any(key in spec for key in ('min', 'max', 'allow_inf', 'allow_nan')):
            rt_mult = validate_number(
                rt_mult,
                min_val=spec.get('min'),
                max_val=spec.get('max'),
                allow_inf=spec.get('allow_inf', False),
                allow_nan=spec.get('allow_nan', False),
                field=spec.get('field', 'realtime_multiplier')
            )
    except Exception as te:
        raise type(te)(f"game_settings['realtime_multiplier'] is invalid: {te} (got value {settings.get('realtime_multiplier', None)!r})") from te
    out['realtime_multiplier'] = rt_mult

    # frame_skip logic
    try:
        if 'frame_skip' in settings:
            frame_skip = coerce_int(settings['frame_skip'])
        else:
            freq = out['frequency']
            frame_skip = int(freq) if out['realtime_multiplier'] == 0.0 else round(out['realtime_multiplier'])
        # Validate min/max for frame_skip if in schema
        spec = SCHEMA['frame_skip']
        if frame_skip is not None and any(key in spec for key in ('min', 'max', 'allow_inf', 'allow_nan')):
            frame_skip = int(validate_number(
                float(frame_skip),
                min_val=spec.get('min'),
                max_val=spec.get('max'),
                allow_inf=spec.get('allow_inf', False),
                allow_nan=spec.get('allow_nan', False),
                field=spec.get('field', 'frame_skip')
            ))
        frame_skip = max(1, frame_skip)
    except Exception as te:
        raise type(te)(f"game_settings['frame_skip'] is invalid: {te} (got value {settings.get('frame_skip', None)!r})") from te
    out['frame_skip'] = frame_skip

    # UI_settings
    try:
        if 'UI_settings' in settings:
            ui = settings['UI_settings']
            if not isinstance(ui, dict):
                raise TypeError(f"UI_settings must be a dict, got {type(ui).__name__}")
            out['UI_settings'] = validate_ui_settings(ui)
        else:
            out['UI_settings'] = validate_ui_settings({})
    except Exception as te:
        raise type(te)(f"game_settings['UI_settings'] is invalid: {te} (got value {settings.get('UI_settings', None)!r})") from te

    return out


# All allowed ship_state keys with their (type, default, constraints)
SHIP_STATE_SCHEMA: dict[str, dict[str, Any]] = {
    'position': {'type': 'tuple2', 'required': True},
    'angle': {'type': 'float', 'default': 90.0},
    'lives': {'type': 'int', 'default': 3, 'min': 1},
    'team': {'type': 'int', 'default': 1, 'min': 1},
    'team_name': {'type': 'str', 'default': None},
    'bullets_remaining': {'type': 'int', 'default': None, 'min': -1},  # -1 for infinite
    'mines_remaining': {'type': 'int', 'default': None, 'min': -1},  # -1 for infinite
}


def validate_ship_state(ship: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(ship, dict):
        raise TypeError("Each ship state must be a dict.")
    out: dict[str, Any] = {}
    allowed_keys = set(SHIP_STATE_SCHEMA)
    extra = set(ship) - allowed_keys
    if extra:
        raise ValueError(f"ship_state contains unknown keys: {extra}")
    for k, spec in SHIP_STATE_SCHEMA.items():
        if spec.get('required', False) and k not in ship:
            raise ValueError(f"ship_state missing required field '{k}'")
        if k in ship:
            val = ship[k]
            if spec['type'] == 'tuple2':
                # Must be tuple or list of length 2 of numbers
                if not (isinstance(val, (tuple, list)) and len(val) == 2):
                    raise TypeError("ship_state['position'] must be tuple/list of length 2")
                x, y = val
                try:
                    x_f = coerce_float(x)
                except TypeError as te:
                    raise TypeError(f"ship_state['{k}'][0] is invalid: {te} (got value {x!r})")
                try:
                    y_f = coerce_float(y)
                except TypeError as te:
                    raise TypeError(f"ship_state['{k}'][1] is invalid: {te} (got value {y!r})")
                try:
                    x_valid = validate_number(
                        x_f, allow_inf=False, allow_nan=False, field=f"ship_state['{k}'][0]"
                    )
                    y_valid = validate_number(
                        y_f, allow_inf=False, allow_nan=False, field=f"ship_state['{k}'][1]"
                    )
                except Exception as ve:
                    raise type(ve)(f"ship_state['{k}'] element validation failed: {ve}")
                val_out = (x_valid, y_valid)
                out[k] = val_out
            elif spec['type'] == 'float':
                try:
                    val_f = coerce_float(val)
                except TypeError as te:
                    raise TypeError(f"ship_state['{k}'] is invalid: {te} (got value {val!r})")
                try:
                    val_valid = validate_number(
                        val_f,
                        min_val=spec.get('min'),
                        max_val=spec.get('max'),
                        field=f"ship_state['{k}']"
                    )
                except Exception as ve:
                    raise type(ve)(f"ship_state['{k}'] validation failed: {ve}")
                out[k] = val_valid
            elif spec['type'] == 'int':
                try:
                    val_i = coerce_int(val)
                except TypeError as te:
                    raise TypeError(f"ship_state['{k}'] is invalid: {te} (got value {val!r})")
                if 'min' in spec and val_i < spec['min']:
                    raise ValueError(f"ship_state['{k}'] must be >= {spec['min']}")
                out[k] = val_i
            elif spec['type'] == 'str':
                if val is not None and not isinstance(val, str):
                    raise TypeError(f"ship_state['{k}'] must be str or None")
                out[k] = val
        else:
            # Set default. Handle str type default value
            if spec['default'] is not None:
                out[k] = spec['default']
    return out


ASTEROID_STATE_SCHEMA: dict[str, dict[str, Any]] = {
    'position': {'type': 'tuple2', 'required': True},
    'speed': {'type': 'float', 'default': None},
    'angle': {'type': 'float', 'default': None},
    'velocity': {'type': 'tuple2', 'default': None},  # (vx, vy), mutually exclusive with speed/angle!
    'size': {'type': 'int', 'default': 4, 'min': 1, 'max': 4}
}


def validate_asteroid_state(asteroid: Mapping[str, Any], map_size: tuple[int, int]) -> dict[str, Any]:
    if not isinstance(asteroid, dict):
        raise TypeError("Each asteroid state must be a dict.")
    out: dict[str, Any] = {}
    allowed_keys = set(ASTEROID_STATE_SCHEMA)
    extra = set(asteroid) - allowed_keys
    if extra:
        raise ValueError(f"asteroid_state contains unknown keys: {extra}")
    # Mutual exclusion check
    if 'velocity' in asteroid and ('speed' in asteroid or 'angle' in asteroid):
        raise ValueError("Asteroid state cannot contain both 'velocity' and 'speed' or 'angle'. If specifying 'velocity', please omit 'speed/angle'.")

    for k, spec in ASTEROID_STATE_SCHEMA.items():
        if spec.get('required', False) and k not in asteroid:
            raise ValueError(f"asteroid_state missing required field '{k}'")
        if k in asteroid:
            val = asteroid[k]
            if spec['type'] == 'tuple2':
                if not (isinstance(val, (tuple, list)) and len(val) == 2):
                    raise TypeError(f"asteroid_state['{k}'] must be tuple/list of length 2")
                x, y = val
                try:
                    x_f = coerce_float(x)
                except TypeError as te:
                    raise TypeError(f"asteroid_state['{k}'][0] is invalid: {te} (got value {x!r})")
                try:
                    y_f = coerce_float(y)
                except TypeError as te:
                    raise TypeError(f"asteroid_state['{k}'][1] is invalid: {te} (got value {y!r})")
                try:
                    x_valid = validate_number(
                        x_f, allow_inf=False, allow_nan=False, field=f"asteroid_state['{k}'][0]"
                    )
                    y_valid = validate_number(
                        y_f, allow_inf=False, allow_nan=False, field=f"asteroid_state['{k}'][1]"
                    )
                except Exception as ve:
                    raise type(ve)(f"asteroid_state['{k}'] element validation failed: {ve}")
                val_out = (x_valid, y_valid)
                out[k] = val_out
            elif spec['type'] == 'float':
                if val is not None:
                    try:
                        val_f = coerce_float(val)
                    except TypeError as te:
                        raise TypeError(f"asteroid_state['{k}'] is invalid: {te} (got value {val!r})")
                    try:
                        val_valid = validate_number(
                            val_f,
                            min_val=spec.get('min'),
                            max_val=spec.get('max'),
                            field=f"asteroid_state['{k}']"
                        )
                    except Exception as ve:
                        raise type(ve)(f"asteroid_state['{k}'] validation failed: {ve}")
                    out[k] = val_valid
            elif spec['type'] == 'int':
                try:
                    val_i = coerce_int(val)
                except TypeError as te:
                    raise TypeError(f"asteroid_state['{k}'] is invalid: {te} (got value {val!r})")
                # Restrict sizes to [1, 4]:
                if 'min' in spec and val_i < spec['min']:
                    raise ValueError(f"asteroid_state['{k}'] must be >= {spec['min']}")
                if 'max' in spec and val_i > spec['max']:
                    raise ValueError(f"asteroid_state['{k}'] must be <= {spec['max']}")
                out[k] = val_i
        else:
            if 'default' in spec and spec['default'] is not None:
                out[k] = spec['default']
    return out


def validate_scenario_params(params: dict[str, Any]) -> dict[str, Any]:
    """
    Validates and returns a new dict of scenario parameters with lists of validated ship/asteroid dicts
    Cross-field conflicts (e.g., both scenario and ships specify bullets/mines) are checked
    """
    # num_asteroids OR asteroid_states, not both, not neither
    asteroid_states = params.get("asteroid_states")
    num_asteroids = params.get("num_asteroids")
    if asteroid_states is not None and num_asteroids is not None:
        raise ValueError("Specify only one of asteroid_states or num_asteroids, not both.")
    if asteroid_states is None and num_asteroids is None:
        raise ValueError("Specify asteroid_states (list of dict) or num_asteroids (int).")

    # Validate map_size
    map_size_val = params.get("map_size", (1000, 800))
    if not (isinstance(map_size_val, (tuple, list)) and len(map_size_val) == 2 and all(isinstance(x, int) and x > 0 for x in map_size_val)):
        raise ValueError(f"map_size must be a tuple of two positive ints, got {map_size_val!r}")

    map_size: tuple[int, int] = (int(map_size_val[0]), int(map_size_val[1]))

    # Asteroid states
    if asteroid_states is not None:
        if not isinstance(asteroid_states, list):
            raise TypeError("asteroid_states must be a list")
        valid_asteroids = [validate_asteroid_state(ast, map_size) if ast else {} for ast in asteroid_states]
    else:
        n = coerce_int(num_asteroids)
        if n < 0:
            raise ValueError("num_asteroids must be nonnegative.")
        valid_asteroids = [{} for _ in range(n)]  # All randomized/default

    # Ship states
    ship_states_val = params.get("ship_states")
    if ship_states_val is not None:
        if not isinstance(ship_states_val, list):
            raise TypeError("ship_states must be a list")
        valid_ships = [validate_ship_state(ship) for ship in ship_states_val]
    else:
        map_width, map_height = map_size
        valid_ships = [validate_ship_state({'position': (map_width / 2.0, map_height / 2.0)})]

    # Scalar params
    res: dict[str, Any] = {}

    # name
    name_val = params.get("name", "Scenario")
    if not isinstance(name_val, str):
        raise ValueError("Scenario name must be a string")
    res["name"] = name_val

    res["map_size"] = map_size
    res["asteroid_states"] = valid_asteroids
    res["ship_states"] = valid_ships

    # seed
    seed_val = params.get("seed")
    if seed_val is not None:
        res["seed"] = coerce_int(seed_val)
    else:
        res["seed"] = None

    # time_limit
    time_limit_val = params.get("time_limit")
    if time_limit_val is None:
        res["time_limit"] = None
    else:
        fval = coerce_float(time_limit_val)
        if fval == 0.0 or (isinf(fval) and fval > 0.0):
            res["time_limit"] = inf
        elif fval > 0.0:
            res["time_limit"] = fval
        else:
            raise ValueError("time_limit must be positive, or 0 or inf for unlimited")

    # ammo_limit_multiplier
    ammo_lim_val = params.get("ammo_limit_multiplier")
    if ammo_lim_val is not None:
        fl = coerce_float(ammo_lim_val)
        if fl < 0.0:
            raise ValueError("ammo_limit_multiplier must be >= 0.0 (0.0 means unlimited)")
        res["ammo_limit_multiplier"] = fl
    else:
        res["ammo_limit_multiplier"] = None

    # bullet_limit / mine_limit
    bullet_limit_val = params.get("bullet_limit")
    if bullet_limit_val is not None:
        bullet_limit_int = coerce_int(bullet_limit_val)
        if bullet_limit_int < -1:
            raise ValueError("bullet_limit must be -1 for unlimited, or a nonnegative integer")
        res["bullet_limit"] = bullet_limit_int
    else:
        res["bullet_limit"] = None

    mine_limit_val = params.get("mine_limit")
    if mine_limit_val is not None:
        mine_limit_int = coerce_int(mine_limit_val)
        if mine_limit_int < -1:
            raise ValueError("mine_limit must be -1 or >= 0")
        res["mine_limit"] = mine_limit_int
    else:
        res["mine_limit"] = None

    # ENFORCE CROSS-LIMITS: bullets/mines scenario vs per-ship
    has_bullet_limit = res["bullet_limit"] is not None
    has_mine_limit = res["mine_limit"] is not None

    any_ship_bullets = any("bullets_remaining" in ship for ship in valid_ships)
    any_ship_mines = any("mines_remaining" in ship for ship in valid_ships)

    if has_bullet_limit and any_ship_bullets:
        raise ValueError(
            "Both 'bullets_remaining' in a ship_state and 'bullet_limit' in scenario are set. "
            "Please only specify in one place or the other."
        )
    if has_mine_limit and any_ship_mines:
        raise ValueError(
            "Both 'mines_remaining' in a ship_state and 'mine_limit' in scenario are set. "
            "Please only specify in one place or the other."
        )

    # Mutually exclusive: ammo_limit_multiplier and bullet_limit
    if res["ammo_limit_multiplier"] is not None and res["bullet_limit"] is not None:
        raise ValueError("Both 'ammo_limit_multiplier' and 'bullet_limit' are specified. Please define at most one.")

    # Validate per-ship constraints
    for ship in valid_ships:
        if "bullets_remaining" in ship:
            if not isinstance(ship["bullets_remaining"], int) or ship["bullets_remaining"] < -1:
                raise ValueError("Ship's bullets_remaining must be an integer of -1 for infinite, or nonnegative.")
        if "mines_remaining" in ship:
            if not isinstance(ship["mines_remaining"], int) or ship["mines_remaining"] < -1:
                raise ValueError("Ship's mines_remaining must be an integer of -1 for infinite, or nonnegative.")

    # stop conditions
    for fld, dflt in [("stop_if_no_ammo", False), ("stop_if_no_asteroids", True), ("stop_if_no_ships", True)]:
        val: Any = params.get(fld, dflt)
        if val is not None:
            val2 = coerce_bool(val)
            res[fld] = val2
        else:
            res[fld] = val

    return res
