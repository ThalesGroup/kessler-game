from ..controller import KesslerController
# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import socket
from typing import List
from multiprocessing import Process

from .tts_process import run_tts_process
from .tts_controller import TTSController

from ..ship import Ship
from ..asteroid import Asteroid
from ..bullet import Bullet
from ..score import Score
from ..scenario import Scenario
from ..graphics.graphics_base import KesslerGraphics
from ..graphics.graphics_handler import GraphicsType


class GraphicsTTS(KesslerGraphics):
    def __init__(self, graphics_type: GraphicsType=GraphicsType.Tkinter, ui_settings=None):
        # Create udp senders/receivers for communicating with TTS server
        self.host = 'localhost'
        self.send_port = 5093
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_addr = (self.host, self.send_port)
        self.speaking_controller = None

        # Get primary graphics type
        match graphics_type:
            case GraphicsType.NoGraphics:
                self.graphics = None
            case GraphicsType.UnrealEngine:
                from ..graphics.graphics_ue import GraphicsUE
                self.graphics = GraphicsUE()
            case GraphicsType.Tkinter:
                from ..graphics.graphics_tk import GraphicsTK
                self.graphics = GraphicsTK(ui_settings)
            case GraphicsType.Pyplot:
                from ..graphics.graphics_plt import GraphicsPLT
                self.graphics = GraphicsPLT()
            case GraphicsType.Custom:
                raise ValueError(' Cannot use custom graphics type within graphics tts')

    def start(self, scenario: Scenario):
        # Launch tts server process
        tts_process = Process(target=run_tts_process)
        tts_process.start()

        # Call to main graphics engine start
        self.graphics.start(scenario)

    def update(self, score: Score, ships: List[Ship], asteroids: List[Asteroid], bullets: List[Bullet]):
        # Send new explanation string to tts server
        self.speaking_controller = ships[0].controller
        if issubclass(self.speaking_controller.__class__, TTSController):
            self.udp_sock.sendto(self.speaking_controller.explanation.encode(), self.udp_addr)
        else:
            raise RuntimeError("GraphicsTTS requires the first ship controller be of type TTSController")

        # Call to main graphics engine update
        self.graphics.update(score, ships, asteroids, bullets)

    def close(self):

        # Shutdown TTS server. Server will wait until last string is spoken
        self.udp_sock.sendto("!close".encode(), self.udp_addr)
        self.udp_sock.close()

        # Call to main graphics engine close
        self.graphics.close()
