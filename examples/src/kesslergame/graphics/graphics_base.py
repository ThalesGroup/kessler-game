# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import os
from tkinter import *
from PIL import Image, ImageTk


class KesslerGraphics:

    def start(self, scenario):
        raise NotImplementedError('Your derived KesslerController must include a start() method.')

    def update(self, score, ships, asteroids, bullets, mines):
        raise NotImplementedError('Your derived KesslerController must include an update() method.')

    def close(self):
        raise NotImplementedError('Your derived KesslerController must include a close() method.')
