from src.kessler_game import KesslerController
from typing import Dict, Tuple


class TestController(KesslerController):

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool]:
        """
        Method processed each time step by this controller.
        """

        thrust = 0
        turn_rate = 50
        fire = True

        return thrust, turn_rate, fire
