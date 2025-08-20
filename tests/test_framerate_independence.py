import random
import logging
import os
from kesslergame import Scenario, KesslerGame, GraphicsType, KesslerController, StopReason
from math import inf
import argparse

# The purpose of this test is to ensure that the game's physics work the same way regardless of framerate (within reasonable bounds)
# A controller that only changes its action each second is used. For integer framerates, the seconds are guaranteed to be multiples of
# the two framerates used, so this ensures that the same actions are commanded in both cases, at the same times.
# This test can catch many bugs in the game's physics.
# The expected behavior of this test is that mismatches should occur about one in a million trials, due to numeric imprecision. The game should also never crash.
# 100% framerate independence is not possible due to floating point precision error, and the butterfly effect over long scenarios.

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Run Kessler game simulations.')
parser.add_argument('-seed', type=int, help='Seed value to use for the simulation (enables graphics by default).')
parser.add_argument('--nogui', action='store_true', help='Disable graphics, even if seed is specified.')
parser.add_argument('-trials', type=int, help='Specify max number of trials to run.')
parser.add_argument('-fps', type=int, help='Override to run the scenario with a specific FPS.')
args = parser.parse_args()

# Set seed and graphics flag
rand_seed = args.seed
GRAPHICS = rand_seed is not None and not args.nogui
FPS_OVERRIDE = args.fps

TRIALS = args.trials if args.trials is not None else 100000000000
TIME_LIMIT_DEFAULT = inf
COMPETITION_SAFE_MODE = False
WIDTH = 1000
HEIGHT = 800

thrust_range = (-480.0, 480.0)
turn_rate_range = (-180.0, 180.0)

# Setup logging
log_filename = f'mismatches_{os.getpid()}.log'

class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[FlushFileHandler(log_filename, mode='w')]
)

class FramerateIndependentController(KesslerController):
    def __init__(self, actions_list: list[tuple[float, float, bool, bool]]):
        self.actions_list = actions_list

    def actions(self, ship_state: object, game_state: object) -> tuple[float, float, bool, bool]:
        """
        This controller executes predefined actions from the actions_list.
        Each second, it will execute a different action. And the controller can only shoot or drop mines once per second.
        """
        time_s = game_state.time
        time_f = game_state.frame
        framerate = game_state.frame_rate
        thrust = None
        turn_rate = None
        fire = False
        drop_mine = False
        for second, action in enumerate(self.actions_list):
            # second is an integer, where if the floor of the time in seconds is equal to it, it will do that action
            if time_f == second * int(framerate):
                fire = action[2]
                drop_mine = action[3]
            if second * int(framerate) <= time_f < (second + 1) * int(framerate):
                thrust = action[0]
                turn_rate = action[1]
                break
        if thrust is None or turn_rate is None:
            # Ran out of planned actions. Just use the final one for the rest of time.
            thrust, turn_rate, fire, drop_mine = self.actions_list[-1]
        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self) -> str:
        return "FPS Indep Test"

def random_ship_states(number: int) -> list[dict]:
    ship_states = []
    for _ in range(number):
        state = {"position": (random.uniform(0.0, WIDTH), random.uniform(0.0, HEIGHT)),
                 "angle": random.uniform(0.0, 360.0),
                 "lives": random.randint(1, 100),
                 "team": random.randint(1, 2),
                 #"bullets_remaining": random.randint(1, 5000),
                 "mines_remaining": random.randint(0, 50)}
        ship_states.append(state)
    return ship_states

def randomly_initialized_controllers(number: int) -> list[FramerateIndependentController]:
    controllers = []
    for _ in range(number):
        actions_list = [(random.uniform(*thrust_range),
                         random.uniform(*turn_rate_range),
                         random.choice([True, False]),
                         random.choice([True, False])) for _ in range(62)]
        #actions_list[0] = (actions_list[0][0], actions_list[0][1], False, False)  # No fire/drop on first
        controllers.append(FramerateIndependentController(actions_list))
    return controllers

def check_scores(score_1, score_2, seed) -> bool:
    if score_1 != score_2:
        if (score_1.stop_reason == StopReason.no_asteroids and score_2.stop_reason == StopReason.no_asteroids) or (score_1.stop_reason == StopReason.no_ships and score_2.stop_reason == StopReason.no_ships):
            if len(score_1.teams) != len(score_2.teams):
                logging.info(f'SEED: {seed} - team length mismatch: {len(score_1.teams)} vs {len(score_2.teams)}')
                return False
            for t1, t2 in zip(score_1.teams, score_2.teams):
                if t1 != t2:
                    logging.info(f'SEED: {seed} - team data mismatch: {t1} vs {t2}')
                    return False
            return True
        else:
            logging.info(f'SEED: {seed} - score mismatch\nScore1: {score_1}\nScore2: {score_2}')
            return False
    return True

# Main loop
for i in range(TRIALS):
    if rand_seed is None:
        random.seed()
        seed = random.randint(0, 100_000_000_000)
    else:
        seed = rand_seed
    random.seed(seed)

    framerate1 = random.randint(5, 60)
    framerate2 = framerate1
    while framerate1 == framerate2:
        framerate2 = random.randint(5, 60)

    print(f"Framerate Independence Test Trial={i}/{TRIALS}, seed={seed}, framerates: {framerate1} and {framerate2}")

    num_ships = random.randint(1, 10)
    scenario = Scenario(name=f"Trial {i}",
                        num_asteroids=random.randint(1, 50),
                        ship_states=random_ship_states(num_ships),
                        map_size=(WIDTH, HEIGHT),
                        seed=seed,
                        ammo_limit_multiplier=random.uniform(0.0, 2.0),
                        stop_if_no_ammo=False,
                        stop_if_no_asteroids=False,
                        stop_if_no_ships=False,
                        time_limit=float(random.randint(2, 30)))
    controllers = randomly_initialized_controllers(num_ships)

    settings_base = {
        'perf_tracker': True,
        'graphics_type': GraphicsType.NoGraphics if not GRAPHICS else GraphicsType.Tkinter,
        'realtime_multiplier': 1.0 if GRAPHICS else 0.0,
        'frame_skip': 1,
        'graphics_obj': None,
        'time_limit': TIME_LIMIT_DEFAULT,
        'perf_tracker': False,
        "competition_safe_mode": COMPETITION_SAFE_MODE,
        'UI_settings': {'ships': True, 'lives_remaining': True, 'accuracy': True,
                        'asteroids_hit': True, 'shots_fired': True, 'bullets_remaining': True,
                        'controller_name': True, 'scale': 2.0}
    }

    if FPS_OVERRIDE is None:
        settings_1 = settings_base | {'frequency': framerate1}
        settings_2 = settings_base | {'frequency': framerate2}

        game_1 = KesslerGame(settings=settings_1)
        score_1, _ = game_1.run(scenario, controllers)

        game_2 = KesslerGame(settings=settings_2)
        score_2, _ = game_2.run(scenario, controllers)

        if not check_scores(score_1, score_2, seed):
            print(f"Mismatch found. Seed logged: {seed}")
    else:
        # Just run the scenario once with this FPS
        settings = settings_base | {'frequency': FPS_OVERRIDE}
        game = KesslerGame(settings=settings)
        score, _ = game.run(scenario, controllers)
