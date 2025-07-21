# Kessler

## Getting started

Kessler is a simulation environment loosely modeled after our internal project PsiBee and the external project [Fuzzy Asteroids](https://github.com/xfuzzycomp/FuzzyAsteroids).
The game features ships that can shoot bullets, or drop mines to destroy asteroids and gain score.
Ships can also be destroyed by colliding with asteroids or getting caught in mine explosions, causing them to lose lives. When a ship runs out of lives, the game ends.
In multi-ship scenarios, they can't shoot one another, but they can drop mines or crash into the other ship to take each other's lives.

This game is used for the [Explainable Fuzzy Competition](https://xfuzzycomp.github.io/XFC/)

Kessler can be used as a local Python package by copying the `src/kessler_game` directory into your project, or installed as a Python extension via `pip`.
It is available on PyPI and can be installed with:
```
pip install KesslerGame
```

Both **pure Python** wheels (e.g. KesslerGame-1.2.3-py3-none-any.whl) and **compiled** wheels built with [mypyc](https://mypyc.readthedocs.io/en/latest/) (e.g. KesslerGame-1.2.3-cp310-cp310-win_amd64.whl) are provided on [PyPI](https://pypi.org/project/KesslerGame/#files) and on the [GitHub releases page](https://github.com/ThalesGroup/kessler-game/releases).

`pip install` will automatically select the compiled version if it is compatible with your system. You can also install a wheel manually by downloading the wheel file and running:
``` 
pip install <path to wheel file>
```

The compiled version can be 4X+ faster than the pure Python version and can simulate the game at 1000X+ real-time speed. It is especially recommended for performance-sensitive use cases, such as reinforcement learning. All releases (on PyPI and GitHub) now include:

* Pure Python wheels
* Compiled wheels (for supported platforms)
* Source distributions

If you prefer, you can compile your own `.whl` file using:

``` 
python setup_mypyc.py bdist_wheel
```

This requires a compatible Python version, `mypyc`, and a compatible C compiler (e.g., MSVC on Windows). If successful, the generated wheel will be located in the `dist/` directory.

Kessler has two primary graphics modules. The first uses Python's Tkinter UI library to display the game. The second
utilizes a separate executable process called kessler_graphics made in Unreal Engine 5. Data is sent to the
kessler_graphics instance using UDP protocol on a local machine.

## Using the UE5 graphics engine
Under kessler_graphics is an Unreal Engine 5 project for receiving simulation data from the Kessler Python process and
displaying it in a 3d environment. To contribute to the UE5 project, you will need to do the following.
- Install Visual Studio 2019 v16.11.5 or later with "Game Development with C++" selected on install
- Install the .NET Core 3.1 Runtime from [here](https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-3.1.30-windows-x64-installer?cid=getdotnetcore)
- Install Unreal Engine 5.0.x from the [Epic Games Launcher](https://store.epicgames.com/en-US/download)
- Grab the latest release of the UDP-Unreal plugin from [here](https://github.com/getnamo/UDP-Unreal/releases)
- Follow installation instructions for UDP-Unreal from its included README
- Right click `kessler_graphics.uproject` under the `kessler_graphics` directory and select "Generate Visual Studio Project Files" from the context menu
- Launch the project by double-clicking on `kessler_graphics.uproject`, and select "Yes" if prompted to rebuild engine modules
NOTE: UE5 graphics currently do not support the display of mines, and it also has other bugs. It is not currently recommended to be used.

## Documentation

See docs/ for a guide to the game's API, and how to instantiate, configure, and run Kessler!

## Contributing

If you are interested in contributing to the Kessler project, start by reading the [Contributing guide](/CONTRIBUTING.md).

## License

Kessler is licensed under the Apache 2.0 license. Please read [LICENSE](LICENSE) for more information.
