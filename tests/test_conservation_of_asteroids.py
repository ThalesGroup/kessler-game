import random
import logging
import os
from kesslergame import Scenario, KesslerGame, GraphicsType, KesslerController, StopReason
from math import inf
import argparse

# The idea behind this test is that if a scenario ended with zero asteroids, then the number of starting asteroids should equal
# the number of total asteroid hits across all teams.

# ------------------ Argument Parsing ------------------
parser = argparse.ArgumentParser(description='Run Asteroid Conservation Tests.')
parser.add_argument('-seed', type=int, help='Seed value for reproducibility (enables graphics by default).')
parser.add_argument('--nogui', action='store_true', help='Disable graphics, even if seed is specified.')
parser.add_argument('-trials', type=int, help='Number of trials to run.')
parser.add_argument('-fps', type=int, help='Override FPS for running scenarios.')
args = parser.parse_args()

# ------------------ Config ------------------
rand_seed = args.seed
GRAPHICS = rand_seed is not None and not args.nogui
FPS_OVERRIDE = args.fps
TRIALS = args.trials if args.trials is not None else (1 if rand_seed is not None else 100000000000)

WIDTH, HEIGHT = 1000, 800
TIME_LIMIT_DEFAULT = inf
COMPETITION_SAFE_MODE = False

thrust_range = (-480.0, 480.0)
turn_rate_range = (-180.0, 180.0)

# ------------------ Logging ------------------
log_filename = f'asteroid_conservation_{os.getpid()}.log'

class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[FlushFileHandler(log_filename, mode='w')]
)

# ------------------ Controller ------------------
class RandomController(KesslerController):
    def actions(self, ship_state, game_state):
        thrust = random.uniform(*thrust_range)
        turn_rate = random.uniform(*turn_rate_range)
        fire = random.choice([True, False])
        drop_mine = random.choice([True, False])
        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self):
        return "RandomController"

class SmoothRandomController(KesslerController):
    def __init__(self):
        self.next_change_frame = 0
        self.current_action = (0.0, 0.0, False, False)
        self.target_action = (0.0, 0.0, False, False)

    def actions(self, ship_state, game_state):
        frame = game_state.frame

        # time to pick a new target action?
        if frame >= self.next_change_frame:
            self.current_action = self.target_action
            thrust = random.uniform(*thrust_range)
            turn_rate = random.uniform(*turn_rate_range)
            fire = random.choice([True, False])
            drop_mine = random.choice([True, False])
            self.target_action = (thrust, turn_rate, fire, drop_mine)

            period = random.randint(1, 60)  # smooth period length
            self.next_change_frame = frame + period

        # Interpolation progress
        total_period = self.next_change_frame - frame
        if total_period <= 0:
            progress = 1.0
        else:
            progress = 1.0 - (self.next_change_frame - frame) / total_period

        # Smooth interpolate thrust and turn_rate
        thrust = (1 - progress) * self.current_action[0] + progress * self.target_action[0]
        turn_rate = (1 - progress) * self.current_action[1] + progress * self.target_action[1]

        # For fire/drop, just snap to target at start of period
        fire = self.target_action[2] if progress == 0 else False
        drop_mine = self.target_action[3] if progress == 0 else False

        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self):
        return "SmoothRandomController"

# ------------------ Helpers ------------------
def generate_asteroids(num_asteroids, width, height):
    asteroids = []
    for _ in range(num_asteroids):
        position = (random.uniform(0, width), random.uniform(0, height))
        speed = random.triangular(-300, 600, 0)
        angle = random.uniform(0, 360)
        size = random.randint(1, 4)
        asteroids.append({'position': position, 'speed': speed, 'angle': angle, 'size': size})
    return asteroids

def asteroid_potential_hits(size: int) -> int:
    """
    Recursive function to calculate total hits needed to destroy an asteroid of given size.
    size=1 -> 1
    size=2 -> 1 + 3*1 = 4
    size=3 -> 1 + 3*4 = 13
    size=4 -> 1 + 3*13 = 40
    """
    if size == 1:
        return 1
    return 1 + 3 * asteroid_potential_hits(size - 1)

# ------------------ Main Loop ------------------
for i in range(TRIALS):
    # Seed handling
    if rand_seed is None:
        seed = random.randint(0, 100_000_000_000)
    else:
        seed = rand_seed
    random.seed(seed)

    # Scenario setup
    num_ships = random.randint(1, 20)
    num_asteroids = random.randint(1, 1000)
    asteroids = generate_asteroids(num_asteroids, WIDTH, HEIGHT)

    # Compute expected total hits
    expected_hits = sum(asteroid_potential_hits(ast['size']) for ast in asteroids)

    ship_states = [{
        "position": (random.uniform(0.0, WIDTH), random.uniform(0.0, HEIGHT)),
        "angle": random.uniform(0.0, 360.0),
        "lives": 1_000_000_000,
        "team": random.randint(1, num_ships),
        "mines_remaining": random.randint(0, expected_hits)
    } for s in range(num_ships)]

    scenario = Scenario(
        name=f"Trial {i}",
        asteroid_states=asteroids,
        ship_states=ship_states,
        map_size=(WIDTH, HEIGHT),
        seed=seed,
        ammo_limit_multiplier=0,
        stop_if_no_ammo=False,
        stop_if_no_asteroids=True,
        stop_if_no_ships=False,
        time_limit=inf
    )

    controllers = [SmoothRandomController() for _ in range(num_ships)]

    settings = {
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

    if FPS_OVERRIDE:
        settings['frequency'] = FPS_OVERRIDE
    else:
        settings['frequency'] = random.randint(5, 60)

    game = KesslerGame(settings=settings)
    score, _ = game.run(scenario, controllers)

    if score.stop_reason == StopReason.no_asteroids:
        total_hits = sum(team.asteroids_hit for team in score.teams)
        if total_hits != expected_hits:
            logging.info(f"{seed} - MISMATCH: expected {expected_hits}, got {total_hits}")
            print(f"Asteroid Conservation Test Trial={i}/{TRIALS}, seed={seed} -> MISMATCH (expected {expected_hits}, got {total_hits})")
        else:
            print(f"Asteroid Conservation Test Trial={i}/{TRIALS}, seed={seed} -> PASSED (hits={total_hits})")
    else:
        print(f"Asteroid Conservation Test Trial={i}/{TRIALS}, seed={seed} -> Did not end with no_asteroids (reason={score.stop_reason})")
