# Changelog

## [1.3.6] - 18 April 2023

- Added pause functionality for gamepad controller
- Added small dead zones to joystick and trigger inputs from gamepad controller for better human playability

## [1.3.5] - 17 April 2023

- Fixed bug in ship-ship collisions where deaths were not properly counted for both ships.

## [1.3.4] - 16 April 2023

- Fixed bug in relative imports of `GamepadController` class
- Updated `__init__.py` in `src` with `GamepadController`

## [1.3.3] - 13 April 2023

- Fixed bug with `out_of_bullets` stop condition not covering all cases
- Fixed bug in `GraphicsTK` when `ui_settings` are `None`
- Added gamepad functionality for human players. To do so import `GamepadController` from `src.kesslergame.
  controller_gamepad` and use when passing to game object just like `KesslerController`. Requires a Windows 
  compatible controller such as a wired X360 controller.

## [1.3.2] - 22 February 2023

- Fixed bug where controller thrust and turn rate commands were not clamped to allowable range before being applied.
- Fixed bug where perferormance metrics were not returned after using `KesslerGame.run()`
- Added finalized controller references to `Score` object returned from `KesslerGame.run()`. Allows user to access saved characteristics of controller after simulation.

## [1.3.1] - 22 February 2023

- Fixed bug in 1.3.0 where sprites used in Tkinter graphics would not be packaged into release wheel
- Added `KesslerGraphics` class to allow for the creation of custom graphics display interfaces

## [1.3.0] - 5 January 2023

- Project name refactor for PyPI. Breaking change for imports, now named `kesslergame` instead of `kessler_game`.

## [1.2.0] - 4 January 2023

- `team_name` property added for teams
- Controller property `name` now used in graphics

## [1.1.0] - 2 December 2022

- Added name property to `KesslerController` base class. This property must be defined on any derived controller or a
  `NotImplementedError` will be raised
- Tkinter graphics now displays simulation time in the top left
- Bullets remaining metric has been added to default Tkinter UI settings

## [1.0.0] - 30 November 2022

- Initial release with support for python 3.10+
