# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    install_requires=requirements,
)

