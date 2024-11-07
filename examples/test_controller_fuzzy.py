# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.
import skfuzzy.control

from src.kesslergame import KesslerController
from typing import Dict, Tuple
import skfuzzy.control as ctrl
import skfuzzy as skf
import numpy as np


class FuzzyController(KesslerController):
    def __init__(self):
        """
        Any variables or initialization desired for the controller can be set up here
        """
        ...
        self.aiming_fis = None
        self.aiming_fis_sim = None
        self.normalization_dist = None
        self.create_fuzzy_systems()

    def create_aiming_fis(self):
        distance = ctrl.Antecedent(np.linspace(0.0, 1.0, 11), "distance")
        angle = ctrl.Antecedent(np.linspace(-1.0, 1.0, 11), "angle")

        aiming_angle = ctrl.Consequent(np.linspace(-1.0, 1.0, 11), "aiming_angle")

        distance.automf(3, names=["close", "medium", "far"])
        angle.automf(3, names=["negative", "zero", "positive"])

        aiming_angle["negative"] = skf.trimf(aiming_angle.universe, [-1.0, -1.0, 0.0])
        aiming_angle["zero"] = skf.trimf(aiming_angle.universe, [-1.0, 0.0, 1.0])
        aiming_angle["positive"] = skf.trimf(aiming_angle.universe, [0.0, 1.0, 1.0])

        rule1 = ctrl.Rule(distance["close"] & angle["negative"], aiming_angle["negative"])
        rule2 = ctrl.Rule(distance["medium"] & angle["negative"], aiming_angle["negative"])
        rule3 = ctrl.Rule(distance["far"] & angle["negative"], aiming_angle["negative"])
        rule4 = ctrl.Rule(distance["close"] & angle["zero"], aiming_angle["zero"])
        rule5 = ctrl.Rule(distance["medium"] & angle["zero"], aiming_angle["zero"])
        rule6 = ctrl.Rule(distance["far"] & angle["zero"], aiming_angle["zero"])
        rule7 = ctrl.Rule(distance["close"] & angle["positive"], aiming_angle["positive"])
        rule8 = ctrl.Rule(distance["medium"] & angle["positive"], aiming_angle["positive"])
        rule9 = ctrl.Rule(distance["far"] & angle["positive"], aiming_angle["positive"])

        rules = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9]
        self.aiming_fis = ctrl.ControlSystem(rules)
        self.aiming_fis_sim = ctrl.ControlSystemSimulation(self.aiming_fis)

    def create_fuzzy_systems(self):
        self.create_aiming_fis()

    def find_nearest_asteroid(self, ship_state: Dict, game_state: Dict):
        # asteroid_list = [asteroid for asteroid in game_state["asteroids"]]
        asteroid_dist = [np.sqrt((ship_state["position"][0] - asteroid["position"][0])**2 + (ship_state["position"][1] - asteroid["position"][1])**2) for asteroid in game_state["asteroids"]]
        ast_dist = min(asteroid_dist)
        ast_idx = asteroid_dist.index(ast_dist)

        return ast_idx, ast_dist

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool, bool]:
        """
        Method processed each time step by this controller to determine what control actions to take

        Arguments:
            ship_state (dict): contains state information for your own ship
            game_state (dict): contains state information for all objects in the game

        Returns:
            float: thrust control value
            float: turn-rate control value
            bool: fire control value. Shoots if true
            bool: mine deployment control value. Lays mine if true
        """
        nearest_ast_idx, nearest_ast_dist = self.find_nearest_asteroid(ship_state, game_state)

        nearest_ast = game_state["asteroids"][nearest_ast_idx]
        dx = nearest_ast["position"][0] - ship_state["position"][0]
        dy = nearest_ast["position"][1] - ship_state["position"][1]

        angle_to_ast = np.arctan2(dy, dx)*180/np.pi
        relative_angle = ship_state["heading"] - angle_to_ast

        if relative_angle < -180.0:
            relative_angle = -180.0
        elif relative_angle > 180.0:
            relative_angle = 180.0

        norm_relative_angle = relative_angle/180.0

        ast_distance = np.sqrt(dx**2 + dy**2)
        if not self.normalization_dist:
            self.normalization_dist = np.sqrt(game_state["map_size"][0]**2 + game_state["map_size"][1]**2)/2

        norm_ast_distance = ast_distance/self.normalization_dist

        thrust = 0
        self.aiming_fis_sim.input["angle"] = norm_relative_angle
        self.aiming_fis_sim.input["distance"] = norm_ast_distance

        self.aiming_fis_sim.compute()
        desired_aim_angle = self.aiming_fis_sim.output["aiming_angle"]*10.0

        turn_rate = 0
        # turn at maximum turn rate until at desired aim angle
        if desired_aim_angle < 0.0:
            turn_rate = ship_state["turn_rate_range"][1]
        elif desired_aim_angle > 0.0:
            turn_rate = ship_state["turn_rate_range"][0]

        # print(ship_state["heading"], angle_to_ast, ast_distance)
        print(relative_angle, norm_relative_angle)
        # print(relative_angle)
        # print(norm_relative_angle, norm_ast_distance)
        # print(desired_aim_angle, turn_rate)


        fire = True
        drop_mine = False

        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self) -> str:
        """
        Simple property used for naming controllers such that it can be displayed in the graphics engine

        Returns:
            str: name of this controller
        """
        return "Test Controller"

    # @property
    # def custom_sprite_path(self) -> str:
    #     return "Neo.png"
