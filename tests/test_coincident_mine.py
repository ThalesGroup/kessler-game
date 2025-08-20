import random
from kesslergame import Scenario, KesslerGame, GraphicsType, KesslerController
from math import atan2, hypot, degrees

# This test defines three scenarios where the mine explodes at the exact same coordinate as the asteroid.
# The expected behavior is that the asteroid should split in the direction it was originally moving.
# If the asteroid is not moving, then it defaults to an angle of 0, which is to the right.

# Expected behaviors:
# All cases: The mines explode on top of the asteroid with a distance of exactly 0. The game should not divide by zero, and should not crash.
# Case 1: The asteroid splits and continues in its direction of travel
# Case 2: The asteroid splits and continues in its direction of travel
# Case 3: The asteroid splits, and as it was not traveling, it defaults to splitting with an angle of 0, and a (cos, sin) of (1, 0)

# Set seed and graphics flag
GRAPHICS = True
FPS = 30

COMPETITION_SAFE_MODE = True
WIDTH = 1000
HEIGHT = 800

thrust_range = (-480.0, 480.0)
turn_rate_range = (-180.0, 180.0)

class MineTest(KesslerController):
    def __init__(self):
        pass

    def actions(self, ship_state: object, game_state: object) -> tuple[float, float, bool, bool]:
        time_s = game_state.time
        time_f = game_state.frame
        framerate = game_state.frame_rate
        thrust = None
        turn_rate = None
        fire = False
        drop_mine = False
        if time_f == 0:
            thrust, turn_rate, fire, drop_mine = 480, 0, False, True
        elif time_s < 1:
            thrust, turn_rate, fire, drop_mine = 480, 0, False, False,
        else:
            thrust, turn_rate, fire, drop_mine = 0, 0, False, False
        #print(f"Frame {time_f}, outputting {thrust} {turn_rate} {fire} {drop_mine}")
        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self) -> str:
        return "Mine Test"

ship_states_1 = [
    {
        "position": (500, 400.00000000000074),
        "angle": 90,
        "lives": 3,
        "mines_remaining": 1,
    }
]

asteroid_states_1 = [
    {
        "position": (500, 0),
        "angle": 90,
        "speed": 400/3,
        "size": 4
    }
]

mine_test_1 = Scenario(name=f"Mine Test 1",
                    asteroid_states=asteroid_states_1,
                    ship_states=ship_states_1,
                    map_size=(WIDTH, HEIGHT),
                    seed=0,
                    ammo_limit_multiplier=random.uniform(0.0, 2.0),
                    stop_if_no_ammo=False,
                    stop_if_no_asteroids=False,
                    stop_if_no_ships=False,
                    time_limit=6.0)


ship_states_2 = [
    {
        "position": (500.00000000000273, 400.00000000000045),
        "angle": 0,
        "lives": 3,
        "mines_remaining": 1,
    }
]

asteroid_states_2 = [
    {
        "position": (792, 123),
        "angle": degrees(atan2(400 - 123, 500 - 792)),
        "speed": hypot(400 - 123, 500 - 792)/3,
        "size": 4
    }
]

mine_test_2 = Scenario(name=f"Mine Test 2",
                    asteroid_states=asteroid_states_2,
                    ship_states=ship_states_2,
                    map_size=(WIDTH, HEIGHT),
                    seed=0,
                    ammo_limit_multiplier=random.uniform(0.0, 2.0),
                    stop_if_no_ammo=False,
                    stop_if_no_asteroids=False,
                    stop_if_no_ships=False,
                    time_limit=6.0)


ship_states_3 = [
    {
        "position": (500, 400),
        "angle": 0,
        "lives": 3,
        "mines_remaining": 1,
    }
]

asteroid_states_3 = [
    {
        "position": (500, 400),
        "angle": 0,
        "speed": 0,
        "size": 4
    }
]

mine_test_3 = Scenario(name=f"Mine Test 3",
                    asteroid_states=asteroid_states_3,
                    ship_states=ship_states_3,
                    map_size=(WIDTH, HEIGHT),
                    seed=0,
                    ammo_limit_multiplier=random.uniform(0.0, 2.0),
                    stop_if_no_ammo=False,
                    stop_if_no_asteroids=False,
                    stop_if_no_ships=False,
                    time_limit=6.0)

controllers = [MineTest()]

settings = {
    'perf_tracker': True,
    'graphics_type': GraphicsType.NoGraphics if not GRAPHICS else GraphicsType.Tkinter,
    'realtime_multiplier': 1.0 if GRAPHICS else 0.0,
    'frame_skip': 1,
    'graphics_obj': None,
    'frequency': FPS,
    'perf_tracker': False,
    "competition_safe_mode": COMPETITION_SAFE_MODE,
    'UI_settings': {'ships': True, 'lives_remaining': True, 'accuracy': True,
                    'asteroids_hit': True, 'shots_fired': True, 'bullets_remaining': True,
                    'controller_name': True, 'scale': 2.0}
}

game = KesslerGame(settings=settings)
score, _ = game.run(mine_test_1, controllers)
score, _ = game.run(mine_test_2, controllers)
score, _ = game.run(mine_test_3, controllers)
