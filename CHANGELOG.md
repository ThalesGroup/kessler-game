# Changelog

## [2.0.1] - 12 January 2024

- Changed `game_state` dictionary information to include an explicit `delta_time` entry representing the difference 
  in simulation time from one frame to the next as well as renaming `time_step` to a more accurate `sim_frame` which 
  represents the frame number that the sim is currently on. 
  - I.e. the default frequency is 30 Hz, and `delta_time` is constant so in this case has a value of 1/30.
  - `sim_frame` will be 0 on the first frame of the sim and then increment to 1, 2,..., etc. until the sim reaches 
    termination criteria

## [2.0.0] - 17 October 2023

- Added mine objects that can be placed by ships. Mines cannot move once placed, detonate after a fixed amount of 
  time, inflict a "hit" on any object within the blast radius (asteroids and ships), and impart momentum on 
  asteroids based on blast strength which is a function of the distance of the asteroid from the mine placement 
  point. The blast momentum imparted is a linearly decreasing amount with the maximum at the mine location and goes 
  to 0 at the edge of the blast radius.

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
