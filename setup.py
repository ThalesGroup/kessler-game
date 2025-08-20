# -*- coding: utf-8 -*-
# Copyright © 2025 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import os
import re
from setuptools import setup, find_packages

# Optional import: only needed if we do a compiled build
try:
    from mypyc.build import mypycify
except ImportError:
    mypycify = None

# --- Requirements ---
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# --- Version parsing ---
VERSIONFILE = "src/kesslergame/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError(f"Unable to find version string in {VERSIONFILE}.")

# --- Decide whether to use MyPyC ---
use_mypyc = os.environ.get("USE_MYPYC") == "1"

mypyc_modules = [
    "src/kesslergame/asteroid.py",
    "src/kesslergame/bullet.py",
    "src/kesslergame/math_utils.py",
    "src/kesslergame/mines.py",
    "src/kesslergame/collisions.py",
    "src/kesslergame/collision_event.py",
    # "src/kesslergame/controller.py",  # DO NOT compile the controller.py, because adding the ship_id attribute from the derived class gets really messy and buggy
    # "src/kesslergame/controller_gamepad.py",
    "src/kesslergame/kessler_game.py",
    "src/kesslergame/heapq_mypyc.py",
    "src/kesslergame/scenario.py",
    "src/kesslergame/score.py",
    "src/kesslergame/settings_dicts.py",
    "src/kesslergame/ship.py",
    "src/kesslergame/state_models.py",
    "src/kesslergame/team.py",
    "src/kesslergame/validate.py",
    "src/kesslergame/graphics/graphics_base.py",
    "src/kesslergame/graphics/graphics_handler.py",
    "src/kesslergame/graphics/graphics_plt.py",
    "src/kesslergame/graphics/graphics_tk.py",
    "src/kesslergame/graphics/graphics_ue.py",
    "src/kesslergame/__init__.py",
    "src/kesslergame/graphics/__init__.py",
]

ext_modules = []

if use_mypyc:
    if not mypycify:
        raise RuntimeError("mypy[mypyc] must be installed to build compiled wheels")
    print("Building with MyPyC")

    # --- Workaround: Temporarily remove src/__init__.py before compilation ---
    init_file = "src/__init__.py"
    init_removed = False
    try:
        if os.path.exists(init_file):
            print(f"Found {init_file}, deleting it for compilation.")
            os.remove(init_file)
            init_removed = True
        else:
            print(f"{init_file} does not exist, skipping deletion.")
        ext_modules = mypycify(mypyc_modules, strip_asserts=True, strict_dunder_typing=True)
    finally:
        # Restore src/__init__.py if we removed it
        if init_removed:
            try:
                print(f"Recreating {init_file} as an empty file.")
                with open(init_file, 'w'):
                    pass
            except Exception as e:
                print(f"Error while recreating {init_file}: {e}")
                raise
else:
    print("Building pure Python wheel")

# --- Setup call ---
setup(
    name="KesslerGame",
    version=verstr,
    packages=find_packages(
        where="src",
        exclude=["examples", "src.examples", "*.examples.*", "examples.*"],
    ),
    install_requires=requirements,
    package_dir={"": "src"},
    package_data={"": ["*.png"]},
    ext_modules=ext_modules,
)
