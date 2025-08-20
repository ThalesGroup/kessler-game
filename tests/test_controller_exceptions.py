import random
import logging
from kesslergame import Scenario, KesslerGame, GraphicsType, KesslerController, StopReason
from math import inf
import argparse

# This test uses a controller that randomly will raise exceptions, and also output invalid values.
# The expected behavior is that, when COMPETITION_SAFE_MODE is True, the game should catch these errors and assign null actions to the ship for that timestep, and print a warning.
# When COMPETITION_SAFE_MODE is False, the game should raise the exception at the controller call site, without the error propagating into the game.

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Run Kessler game simulations.')
parser.add_argument('-seed', type=int, help='Seed value to use for the simulation (enables graphics by default).')
parser.add_argument('--nogui', action='store_true', help='Disable graphics, even if seed is specified.')
parser.add_argument('-trials', type=int, help='Specify max number of trials to run.')
args = parser.parse_args()

# Set seed and graphics flag
rand_seed = args.seed
GRAPHICS = rand_seed is not None and not args.nogui
FPS_OVERRIDE = 30

TRIALS = args.trials if args.trials is not None else (1 if rand_seed is not None else 100000000000)
TIME_LIMIT_DEFAULT = inf
COMPETITION_SAFE_MODE = True
WIDTH = 1000
HEIGHT = 800

thrust_range = (-480.0, 480.0)
turn_rate_range = (-180.0, 180.0)

EXCEPTION_PROBABILITY = 0.00001
INF_THRUST_PROBABILITY = 0.00001
NAN_THRUST_PROBABILITY = 0.00001
INF_TURN_PROBABILITY = 0.00001
NAN_TURN_PROBABILITY = 0.00001
WRONG_TUPLE_SIZE_PROBABILITY = 0.00001

class ExceptionalController(KesslerController):
    def __init__(self, actions_list: list[tuple[float, float, bool, bool]]):
        self.actions_list = actions_list

    def actions(self, ship_state: object, game_state: object) -> tuple[float, float, bool, bool]:
        """
        This controller executes predefined actions from the actions_list,
        and injects faults probabilistically for testing robustness.
        """
        # Trigger an exception
        if random.random() < EXCEPTION_PROBABILITY:
            raise RuntimeError("Injected exception for testing.")
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

        # Inject NaN/Inf/invalid outputs
        if random.random() < INF_THRUST_PROBABILITY:
            thrust = float('inf')
        if random.random() < NAN_THRUST_PROBABILITY:
            thrust = float('nan')
        if random.random() < INF_TURN_PROBABILITY:
            turn_rate = float('inf')
        if random.random() < NAN_TURN_PROBABILITY:
            turn_rate = float('nan')
        if random.random() < WRONG_TUPLE_SIZE_PROBABILITY:
            return (thrust, turn_rate, fire)  # Return wrong tuple size

        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self) -> str:
        return "Exceptional Controller"

def random_ship_states(number: int) -> list[dict]:
    ship_states = []
    for _ in range(number):
        state = {"position": (random.uniform(0.0, WIDTH), random.uniform(0.0, HEIGHT)),
                 "angle": random.uniform(0.0, 360.0),
                 "lives": random.randint(1, 50),
                 "team": random.randint(1, 2),
                 #"bullets_remaining": random.randint(1, 5000),
                 "mines_remaining": random.randint(0, 20)}
        ship_states.append(state)
    return ship_states

def randomly_initialized_controllers(number: int) -> list[ExceptionalController]:
    controllers = []
    for _ in range(number):
        actions_list = [(random.uniform(*thrust_range),
                         random.uniform(*turn_rate_range),
                         random.choice([True, False]),
                         random.choice([True, False])) for _ in range(62)]
        #actions_list[0] = (actions_list[0][0], actions_list[0][1], False, False)  # No fire/drop on first
        controllers.append(ExceptionalController(actions_list))
    return controllers

def check_scores(score_1, score_2, seed) -> bool:
    if score_1 != score_2:
        if (score_1.stop_reason == StopReason.no_asteroids and score_2.stop_reason == StopReason.no_asteroids) or (score_1.stop_reason == StopReason.no_ships and score_2.stop_reason == StopReason.no_ships):
            if len(score_1.teams) != len(score_2.teams):
                logging.info(f'{seed} - team length mismatch: {len(score_1.teams)} vs {len(score_2.teams)}')
                return False
            for t1, t2 in zip(score_1.teams, score_2.teams):
                if t1 != t2:
                    logging.info(f'{seed} - team data mismatch: {t1} vs {t2}')
                    return False
            return True
        else:
            logging.info(f'{seed} - score mismatch\nScore1: {score_1}\nScore2: {score_2}')
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

    print(f"Controller Exception Test Trial={i}/{TRIALS}, seed={seed}")

    num_ships = random.randint(1, 6)
    scenario = Scenario(name=f"Trial {i}",
                        num_asteroids=random.randint(1, 10),
                        ship_states=random_ship_states(num_ships),
                        map_size=(WIDTH, HEIGHT),
                        seed=seed,
                        ammo_limit_multiplier=random.uniform(0.0, 2.0),
                        stop_if_no_ammo=False,
                        stop_if_no_asteroids=False,
                        stop_if_no_ships=False,
                        time_limit=float(random.randint(2, 20)))
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

    # Just run the scenario once with this FPS
    settings = settings_base | {'frequency': FPS_OVERRIDE}
    game = KesslerGame(settings=settings)
    score, _ = game.run(scenario, controllers)
