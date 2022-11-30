# Thales Open Source Template Project

Template for creating a new project in the [Thales GitHub organization](https://github.com/ThalesGroup).

Each Thales OSS project repository **MUST** contain the following files at the root:

- a `LICENSE` which has been chosen in accordance with legal department depending on your needs

- a `README.md` outlining the project goals, sponsoring sig, and community contact information, [GitHub tips about README.md](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/about-readmes)

- a `CONTRIBUTING.md` outlining how to contribute to the project, how to submit a pull request and an issue

- a `SECURITY.md` outlining how the security concerns are handled, [GitHub tips about SECURITY.md](https://docs.github.com/en/github/managing-security-vulnerabilities/adding-a-security-policy-to-your-repository)

Below is an example of the common structure and information expected in a README.

**Please keep this structure as is and only fill the content for each section according to your project.**

If you need assistance or have question, please contact oss@thalesgroup.com

## Get started

**Please also add the description into the About section (Description field)**

Kessler is a simulation environment loosely modeled after our internal project PsiBee and the external project [Fuzzy Asteroids](https://github.com/xfuzzycomp/FuzzyAsteroids). The game has ships that shoot bullets at asteroids to gain score. Ships can collide with asteroids and lose lives. If the ship runs out of lives, the game terminates. In multi-ship scenarios, ships can collide with each other as well, but cannot shoot each other.

# Using the UE5 graphics engine
Under kessler_graphics is an Unreal Engine 5 project for receiving simulation data from the Kessler Python process and displaying it in a 3d environment. To contribute to the UE5 project, do the following.
- Install Visual Studio 2019 v16.11.5 or later with "Game Development with C++" selected on install
- Install the .NET Core 3.1 Runtime from https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-3.1.30-windows-x64-installer?cid=getdotnetcore
- Install Unreal Engine 5.0.x from the Epic Games Launcher
- Grab the latest release of the UDP-Unreal plugin from https://github.com/getnamo/UDP-Unreal/releases
- Follow installation instructions for UDP-Unreal from its included README
- Right click kessler_graphics.uproject and select "Generate Visual Studio Project Files"
- Launch the project, and select "Yes" if prompted to rebuild engine modules

## Documentation

Documentation is available at [xxx/docs](https://xxx/docs/).

You can use [GitHub pages](https://guides.github.com/features/pages/) to create your documentation.

See an example here : https://github.com/ThalesGroup/ThalesGroup.github.io

**Please also add the documentation URL into the About section (Website field)**

## Contributing

If you are interested in contributing to the XXX project, start by reading the [Contributing guide](/CONTRIBUTING.md).

## License

The chosen license in accordance with legal department must be defined into an explicit [LICENSE](https://github.com/ThalesGroup/template-project/blob/master/LICENSE) file at the root of the repository
You can also link this file in this README section.
