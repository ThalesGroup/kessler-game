# Kessler

## Getting started

Kessler is a simulation environment loosely modeled after our internal project PsiBee and the external project [Fuzzy Asteroids](https://github.com/xfuzzycomp/FuzzyAsteroids).
The game has ships that shoot bullets at asteroids to gain score. Ships can collide with asteroids and lose lives.
If the ship runs out of lives, the game terminates. In multi-ship scenarios, ships can collide with each other as well, 
but cannot shoot each other.

Kessler can be built as python extension for install using pip, or used as a local package by copying the
`src/kessler_game` directory to your project. Wheels are provided in
[releases](https://github.com/ThalesGroup/kessler-game/releases) for install using
``` 
pip install <path to kessler_game-#.#.#-py3-none-any.whl>
```

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

## Documentation

Documentation is not yet available for Kessler. If you would like to contribute to documentation, check out 
[CONTRIBUTING.md](CONTRIBUTING.md) for info on how to get started

## Contributing

If you are interested in contributing to the Kessler project, start by reading the [Contributing guide](/CONTRIBUTING.md).

## License

Kessler is licensed under the Apache 2.0 license. Please read [LICENSE](LICENSE) for more information.
