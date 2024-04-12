# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

from setuptools import setup, find_packages
from mypyc.build import mypycify

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

import re
VERSIONFILE="src/kesslergame/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

# List of all Python modules to compile with MyPyC
mypyc_modules = [
    "src/kesslergame/asteroid.py",
    "src/kesslergame/bullet.py",
    "src/kesslergame/collisions.py",
    "src/kesslergame/controller.py",
    "src/kesslergame/controller_gamepad.py",
    "src/kesslergame/kessler_game.py",
    "src/kesslergame/mines.py",
    "src/kesslergame/scenario.py",
    "src/kesslergame/score.py",
    "src/kesslergame/ship.py",
    "src/kesslergame/team.py",
    "src/kesslergame/graphics/graphics_base.py",
    "src/kesslergame/graphics/graphics_handler.py",
    "src/kesslergame/graphics/graphics_plt.py",
    "src/kesslergame/graphics/graphics_tk.py",
    "src/kesslergame/graphics/graphics_ue.py",
    # Add __init__.py if you have specific initialization code that needs compilation.
    # "src/__init__.py",
    "src/kesslergame/__init__.py",
    "src/kesslergame/graphics/__init__.py",
]

setup(
    name='KesslerGame',
    version=verstr,
    packages=find_packages(where='src', exclude=['examples', 'src.examples', '*.examples.*', 'examples.*']),
    install_requires=requirements,
    ext_modules=mypycify(mypyc_modules),
    package_data={
        '': ['*.png'],
    },
    package_dir={'': 'src'},
)





