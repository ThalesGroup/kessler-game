# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import re
import os
import shutil

from setuptools import setup, find_packages
from mypyc.build import mypycify

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

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
    "src/kesslergame/math_utils.py",
    "src/kesslergame/mines.py",
    "src/kesslergame/collisions.py",
#    "src/kesslergame/controller.py", DO NOT compile the controller.py, because adding the ship_id attribute from the derived class gets really messy and buggy
#    "src/kesslergame/controller_gamepad.py",
    "src/kesslergame/kessler_game.py",
    "src/kesslergame/scenario.py",
    "src/kesslergame/score.py",
    "src/kesslergame/settings_dicts.py",
    "src/kesslergame/ship.py",
    "src/kesslergame/state_models.py",
    "src/kesslergame/team.py",
    "src/kesslergame/graphics/graphics_base.py",
    "src/kesslergame/graphics/graphics_handler.py",
    "src/kesslergame/graphics/graphics_plt.py",
    "src/kesslergame/graphics/graphics_tk.py",
    "src/kesslergame/graphics/graphics_ue.py",
    "src/kesslergame/__init__.py",
    "src/kesslergame/graphics/__init__.py",
]

# Workaround: Temporarily remove src/__init__.py before compilation, and restore afterwards
init_file = "src/__init__.py"

try:
    if os.path.exists(init_file):
        print(f"Found {init_file}, deleting it for compilation.")
        os.remove(init_file)
    else:
        print(f"{init_file} does not exist, skipping deletion.")
    
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
except Exception as e:
    print(f"Error during setup: {e}")
    raise
finally:
    pass
    '''
    try:
        if not os.path.exists(init_file):
            print(f"Recreating {init_file} as an empty file.")
            with open(init_file, 'w'):
                pass
    except Exception as e:
        print(f"Error while recreating {init_file}: {e}")
        raise
    '''
