import random
import logging
import os
from kesslergame import Scenario, KesslerGame, GraphicsType, KesslerController
from math import inf
from copy import deepcopy
import argparse
import time

# The idea behind this test, is that the competition safe mode should have no bearing on what the ship receives, all else being equal
# The only thing that changes is the competition_safe_mode setting which is passed to the ships, and the time the evaluation takes, and
# also whether it's safe to mutate the state. The competition safe mode True case tests mutations as well, making sure they do not affect the game.

# ------------------ Argument Parsing, Logging, Constants ------------------
parser = argparse.ArgumentParser(description='Run Kessler game competition safe mode equivalence and speed test.')
parser.add_argument('-seed', type=int, help='Seed value to use for the simulation (enables graphics by default).')
parser.add_argument('--nogui', action='store_true', help='Disable graphics, even if seed is specified.')
parser.add_argument('-trials', type=int, help='Specify max number of trials to run.')
args = parser.parse_args()

rand_seed = args.seed
GRAPHICS = rand_seed is not None and not args.nogui
FPS = 30

TRIALS = args.trials if args.trials is not None else (1 if rand_seed is not None else 100000000000)
TIME_LIMIT_DEFAULT = inf
WIDTH = 1000
HEIGHT = 800

thrust_range = (-480.0, 480.0)
turn_rate_range = (-180.0, 180.0)

log_filename = f'competition_safe_mode_equivalence_{os.getpid()}.log'


class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[FlushFileHandler(log_filename, mode='w')]
)


# ------------------ Controller & Utilities -------------------
class GamestateValidationController(KesslerController):
    def __init__(self, ship_state_dict_list, game_state_dict_list, ship_state_compact_list, game_state_compact_list, controller_idx=0, master_seed=0):
        self.next_change_frame = 0
        self.current_action = (0.0, 0.0, False, False)
        self.target_action = (0.0, 0.0, False, False)
        self.ship_state_dict_list = ship_state_dict_list
        self.game_state_dict_list = game_state_dict_list
        self.ship_state_compact_list = ship_state_compact_list
        self.game_state_compact_list = game_state_compact_list
        self.controller_idx = controller_idx
        self.master_seed = master_seed
        # Use a separate deterministic RNG for mutation
        self.mutation_rng = random.Random(master_seed + 100003 * controller_idx)

    def mutate_any(self, obj):
        """Recursively mutate one random value in a dict or list, using local RNG."""
        rng = self.mutation_rng
        if isinstance(obj, dict) and obj:
            key = rng.choice(list(obj.keys()))
            obj[key] = self.mutate_any(obj[key])
            return obj
        elif isinstance(obj, list) and obj:
            idx = rng.randrange(len(obj))
            obj[idx] = self.mutate_any(obj[idx])
            return obj
        elif isinstance(obj, tuple) and obj:
            idx = rng.randrange(len(obj))
            lst = list(obj)
            lst[idx] = self.mutate_any(lst[idx])
            return tuple(lst)
        # Mutate scalar types
        elif isinstance(obj, float):
            return obj + rng.uniform(1e3, 1e5)
        elif isinstance(obj, int):
            return obj + rng.randint(1, 1000)
        elif isinstance(obj, bool):
            return not obj
        elif isinstance(obj, str):
            return obj + "_mut"
        else:
            return None

    def actions(self, ship_state, game_state):
        self.ship_state_dict_list.append(deepcopy(ship_state.dict))
        self.game_state_dict_list.append(deepcopy(game_state.dict))
        self.ship_state_compact_list.append(deepcopy(ship_state.compact))
        self.game_state_compact_list.append(deepcopy(game_state.compact))

        # If safe mode is on, we want to randomly mutate and mess with the states, and it should have no effect on the game!
        if game_state.competition_safe_mode:
            # Step the controller's local mutation_rng forward by the frame, for deterministic variety
            self.mutation_rng.seed(self.master_seed + 100003 * self.controller_idx + 10000019 * game_state.frame)
            # Mess with the game_state dict and compact
            self.mutate_any(ship_state.dict)
            self.mutate_any(game_state.dict)
            # compact variants are either flat lists or dicts
            self.mutate_any(ship_state.compact)
            self.mutate_any(game_state.compact)

        frame = game_state.frame
        if frame >= self.next_change_frame:
            self.current_action = self.target_action
            thrust = random.uniform(*thrust_range)
            turn_rate = random.uniform(*turn_rate_range)
            fire = random.choice([True, False])
            drop_mine = random.choice([True, False])
            self.target_action = (thrust, turn_rate, fire, drop_mine)
            period = random.randint(1, 60)
            self.next_change_frame = frame + period
        total_period = self.next_change_frame - frame
        if total_period <= 0:
            progress = 1.0
        else:
            progress = 1.0 - (self.next_change_frame - frame) / total_period
        thrust = (1 - progress) * self.current_action[0] + progress * self.target_action[0]
        turn_rate = (1 - progress) * self.current_action[1] + progress * self.target_action[1]
        fire = self.target_action[2] if progress == 0 else False
        drop_mine = self.target_action[3] if progress == 0 else False
        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self): return "Gamestate Validation"


def random_ship_states(number: int) -> list[dict]:
    ship_states = []
    for _ in range(number):
        state = {"position": (random.uniform(0.0, WIDTH), random.uniform(0.0, HEIGHT)),
                 "angle": random.uniform(0.0, 360.0),
                 "lives": random.randint(1, 50),
                 "team": random.randint(1, 2),
                 "mines_remaining": random.randint(0, 20)}
        ship_states.append(state)
    return ship_states


def check_scores(score_1, score_2, seed) -> bool:
    if score_1 != score_2:
        logging.info(f'SEED: {seed} - score mismatch\nScore1: {score_1}\nScore2: {score_2}')
        return False
    return True


# Utility for deep recursive compare with allowed per-run exclusion
def compare_dicts(a, b, path='', skip_keys=('competition_safe_mode',)):
    result = True
    if isinstance(a, dict) and isinstance(b, dict):
        keys = set(a) | set(b)
        for k in keys:
            if k in skip_keys:
                continue
            if k not in a or k not in b:
                logging.info(f'Missing key at {path}:{k}')
                result = False
            else:
                result &= compare_dicts(a[k], b[k], path + f'.{k}', skip_keys)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            logging.info(f'List/tuple length mismatch at {path}: {len(a)} vs {len(b)}')
            return False
        for idx, (ai, bi) in enumerate(zip(a, b)):
            result &= compare_dicts(ai, bi, path + f'[{idx}]', skip_keys)
    else:
        # Float comparison tolerance:
        if isinstance(a, float) and isinstance(b, float):
            if not (abs(a - b) <= 1e-12 or (a != a and b != b)):  # handle nan
                logging.info(f'Float mismatch at {path}: {a} vs {b}')
                return False
        elif a != b:
            logging.info(f'Value mismatch at {path}: {a!r} vs {b!r}')
            return False
    return result


def compare_lists(a_list, b_list, obj_type, trial, seed, cidx):
    if len(a_list) != len(b_list):
        logging.info(f'Trial={trial} seed={seed} Controller={cidx}: Frame count mismatch for {obj_type}: {len(a_list)} vs {len(b_list)}')
        return False
    passed = True
    for fidx, (a, b) in enumerate(zip(a_list, b_list)):
        if not compare_dicts(a, b) if 'dict' in obj_type else a == b:
            logging.info(f'Trial={trial} seed={seed} Controller={cidx} Frame={fidx}: {obj_type} mismatch')  # Details already in logger
            passed = False
    return passed


def compare_ship_compact_lists(a_list, b_list, trial, seed, cidx):
    if len(a_list) != len(b_list):
        logging.info(f'Trial={trial} seed={seed} Controller={cidx}: Frame count mismatch for ship_state.compact: {len(a_list)} vs {len(b_list)}')
        return False
    passed = True
    for fidx, (a, b) in enumerate(zip(a_list, b_list)):
        if a != b:
            logging.info(f'Trial={trial} seed={seed} Controller={cidx} Frame={fidx}: ship_state.compact mismatch: {a} != {b}')
            passed = False
    return passed


def compare_game_compact_lists(a_list, b_list, trial, seed, cidx):
    if len(a_list) != len(b_list):
        logging.info(f'Trial={trial} seed={seed} Controller={cidx}: Frame count mismatch for game_state.compact: {len(a_list)} vs {len(b_list)}')
        return False
    passed = True
    for fidx, (a, b) in enumerate(zip(a_list, b_list)):
        # Only ignore .competition_safe_mode
        acopy = dict(a)
        bcopy = dict(b)
        acopy.pop('competition_safe_mode', None)
        bcopy.pop('competition_safe_mode', None)
        if acopy != bcopy:
            logging.info(f'Trial={trial} seed={seed} Controller={cidx} Frame={fidx}: game_state.compact mismatch')
            passed = False
    return passed

# ------------------ Main loop ------------------

for i in range(TRIALS):
    # Seed setup
    if rand_seed is None:
        random.seed()
        seed = random.randint(0, 100_000_000_000)
    else:
        seed = rand_seed
    random.seed(seed)

    print(f"Competition Safe Mode Equivalence Test Trial={i}, seed={seed}")

    num_ships = random.randint(1, 10)
    scenario = Scenario(
                        name=f"Trial {i}",
                        num_asteroids=random.randint(1, 30),
                        ship_states=random_ship_states(num_ships),
                        map_size=(WIDTH, HEIGHT),
                        seed=seed,
                        ammo_limit_multiplier=random.uniform(0.0, 2.0),
                        stop_if_no_ammo=random.choice([True, False]),
                        stop_if_no_asteroids=random.choice([True, False]),
                        stop_if_no_ships=random.choice([True, False]),
                        time_limit=float(random.randint(1, 15))
    )

    # Structure: for each controller, we store a dict of 4 output lists for each mode
    output_data = {
        True: [],  # competition safe mode ON
        False: []  # competition safe mode OFF
    }

    scores = {}

    timings = {}

    for mode in (True, False):
        # Prepare new random/ship starting conditions per run (identical, since seeded)
        random.seed(seed)

        # Rebuild controller output lists per mode
        # For each controller: maintain lists:
        ship_state_dicts = [[] for _ in range(num_ships)]
        game_state_dicts = [[] for _ in range(num_ships)]
        ship_state_compacts = [[] for _ in range(num_ships)]
        game_state_compacts = [[] for _ in range(num_ships)]
        controllers = [
            GamestateValidationController(
                ship_state_dicts[j],
                game_state_dicts[j],
                ship_state_compacts[j],
                game_state_compacts[j],
                controller_idx=j,
                master_seed=seed
            )
            for j in range(num_ships)
        ]

        settings = {
            'graphics_type': GraphicsType.NoGraphics if not GRAPHICS else GraphicsType.Tkinter,
            'realtime_multiplier': 1.0 if GRAPHICS else 0.0,
            'frame_skip': 1,
            'graphics_obj': None,
            'time_limit': TIME_LIMIT_DEFAULT,
            'perf_tracker': False,
            'frequency': FPS,
            "competition_safe_mode": mode,
            'UI_settings': {'ships': True, 'lives_remaining': True, 'accuracy': True,
                            'asteroids_hit': True, 'shots_fired': True, 'bullets_remaining': True,
                            'controller_name': True, 'scale': 2.0}
        }

        game = KesslerGame(settings=settings)
        t0 = time.perf_counter()
        score, _ = game.run(scenario, controllers)
        t1 = time.perf_counter()

        timings[mode] = t1 - t0
        scores[mode] = score
        # Store results
        output_data[mode] = [
            {
                "ship_state_dicts": ship_state_dicts[j],
                "game_state_dicts": game_state_dicts[j],
                "ship_state_compacts": ship_state_compacts[j],
                "game_state_compacts": game_state_compacts[j],
            }
            for j in range(num_ships)
        ]

    # --- Comparison ---
    all_passed = True

    for cidx in range(num_ships):
        on = output_data[True][cidx]
        off = output_data[False][cidx]
        # Compare dict outputs:
        all_passed &= compare_lists(on['ship_state_dicts'], off['ship_state_dicts'], "ship_state.dict", i, seed, cidx)
        all_passed &= compare_lists(on['game_state_dicts'], off['game_state_dicts'], "game_state.dict", i, seed, cidx)
        all_passed &= compare_ship_compact_lists(on['ship_state_compacts'], off['ship_state_compacts'], i, seed, cidx)
        all_passed &= compare_game_compact_lists(on['game_state_compacts'], off['game_state_compacts'], i, seed, cidx)

    # --- Score comparison ---
    all_passed &= check_scores(scores[True], scores[False], seed)

    # --- Benchmarking ---
    t_on = timings[True]
    t_off = timings[False]
    speedup = t_on / t_off if t_off > 0.0 else (1.0 if t_on == 0.0 and t_off == 0.0 else float('inf'))
    print(f'Trial={i}/{TRIALS} seed={seed} - SafeMode OFF: {t_off:.2f}s, ON: {t_on:.2f}s, Speedup: {speedup:.2f}X (should be >1.0 if safe mode off is faster)')

    if not all_passed:
        print(f"[ERROR] Trial={i}/{TRIALS} Seed={seed} -- see log {log_filename}")
    else:
        print(f"[PASS] Trial={i}/{TRIALS} Seed={seed} -- all frames MATCH")

print(f'Done! Log saved at {log_filename}')
