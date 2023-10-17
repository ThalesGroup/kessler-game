# -*- coding: utf-8 -*-

from .controller import KesslerController
from typing import Dict, Tuple
from inputs import get_gamepad
import math
import threading
import time


class GamepadController(KesslerController):

    def __init__(self):
        self.gamepad = XboxController()
        # tracker to determine if human paused game
        self.paused = False
        self.time_last_paused = 0.0
        # can only toggle pausing every 0.5 seconds
        self.pause_time_buffer = 0.5

    def actions(self, ship_state: Dict, game_state: Dict) -> Tuple[float, float, bool, bool]:
        """
        Read in the current gamepad state, and create the appropriate actions
        """

        self.pause_handler()

        # deadzones (both left and right using same currently)
        joystick_deadzone = 0.05
        trigger_deadzone = 0.05

        # Set thrust control
        if abs(self.gamepad.LeftJoystickY) > joystick_deadzone:
            thrust = self.gamepad.LeftJoystickY * 480.0
        else:
            thrust = 0

        # Set turn control
        if abs(self.gamepad.RightJoystickX) > joystick_deadzone:
            turn_rate = -1 * self.gamepad.RightJoystickX * 180.0
        else:
            turn_rate = 0

        # Setfire control
        if self.gamepad.RightTrigger > trigger_deadzone:
            fire = True
        else:
            fire = False

        # Set drop mine control
        # if self.gamepad.LeftTrigger > trigger_deadzone:
        if self.gamepad.RightBumper:
            drop_mine = True
        else:
            drop_mine = False

        return thrust, turn_rate, fire, drop_mine

    @property
    def name(self) -> str:
        return "Gamepad Controller"

    def explanation(self):
        exp = None
        return exp

    def pause_handler(self):

        break_pause = False
        if time.perf_counter() - self.time_last_paused > self.pause_time_buffer and self.gamepad.Back == 1:
            pause_time = time.perf_counter()
            while break_pause is False:
                if time.perf_counter() - pause_time > self.pause_time_buffer and self.gamepad.Back == 1:
                    break_pause = True
            self.time_last_paused = time.perf_counter()

class XboxController(object):
    """
    Class for Xbox inputs credit to Kevin Hughes and the TensorCart project.
    Copyright (c) 2017 Kevin Hughes
    MIT License
    """

    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()


    def read(self):
        x = self.LeftJoystickX
        y = self.LeftJoystickY
        a = self.A
        b = self.X # b=1, x=2
        rb = self.RightBumper
        return [x, y, a, b, rb]


    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.X = event.state
                elif event.code == 'BTN_WEST':
                    self.Y = event.state
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY1':
                    self.LeftDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY2':
                    self.RightDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY3':
                    self.UpDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY4':
                    self.DownDPad = event.state
