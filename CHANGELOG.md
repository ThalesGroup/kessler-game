# Changelog

## [2.X.X] NEXT VERSION
- Fixed building mypyc compiled wheels, so compiled modules are now actually being run to provide a 4X+ speed benefit
- Use cibuildwheel to automate building mypyc compiled wheels, and upload to pypi and the Github release
- Wait until all asteroid collision checks are finished before appending new asteroids
- Optimize culling of asteroids and other game objects from O(n) to O(1)
- Fix rare bug where the asteroid would wrap every frame and oscillate along the map border

## [2.3.0] - 15 July 2025

- Fixed issues with automated building of mypyc compiled wheels
- Fixed issues with uploading compiled mypyc wheels to pypi

## [2.2.0] - 9 July 2025

- Added better collision detection based on geometry of bullet over timesteps - now framerate independent
- Fixed docstrings and error messages
- Added Scott Dick's example controller and getting started guide
- Fixed bug with mine momentum direction given to asteroids
- Added more information to `game_state` dictionary for agents to access.
- Added more information to ship state and ownship state
- Improved bullet culling by considering head and tail, and deferring it until after the collision check in each frame. This makes it easier to hit asteroids on the edge.
- Switched from using immutabledict to recreating a fresh dict for each ship, to properly fix gamestate tampering issue 
- Resolved respawn time tracking off-by-two. At 30 FPS, the respawn invincibility is now the correct 90 frames instead of 92 frames. 
- Tkinter: Fixed ship sprite handling so multiple ships using the same sprite will render correctly 
- Set DPI awareness to PROCESS_PER_MONITOR_DPI_AWARE on Windows for proper high-DPI support, without blurriness 
- Changed ship shield color transition to fade gradually from red to blue over 3 seconds instead of just the final second 
- Added a scale configuration value to UI_settings, now definable in the game settings. For 1440p, 1.5 is recommended. For 4K, 2.0 is recommended.

## [2.1.9] - 4 July 2024

- Added missing package in `requirements.txt`

## [2.1.8] - 4 July 2024

- Changed the `game_state` dictionary that is passed to controllers to be type `immutabledict`. This prevents 
  changing of `game_state` values by controllers to prevent tampering/affecting controllers later in the loop where 
  it is passed. This is faster than passing copies of the dict and is still passed by reference.

## [2.1.7] - 3 July 2024

- Added optional Boolean setting `random_ast_splits` for game object instantiation. If `True`, left and right asteroid 
  child asteroid vectors will be be random within a bounded range about the main child asteroid vector. By default 
  is set to `False`.

## [2.1.6] - 2 July 2024

- Changed `stop_if_no_ammo` condition to also check mines. Also changed condition such that sum of mines and bullets 
  remaining has to be > 0 since negative values are considered true.

## [2.1.5] - 18 April 2024

- Added `Mines left` to TK graphics
- Added `mines_remaining` to team and score classes to get updated
- Added conditions for `no_ship` stop condition to wait until there aren't bullets or mines left - previously this 
  wasn't the case and gave a slight advantage to a ship if it died first because its bullets and mines would persist 
  and accumulate score but the ship that died second would not get the same persistence/score accumulation

## [2.1.4] - 16 April 2024

- Fixed issue with ship sprite indexing

## [2.1.3] - 16 April 2024
- Added `custom_sprite_path` property to `KesslerController` to automatically grab and load custom ship sprites from 
  the `graphics/images` directory

## [2.1.2] - 12 April 2024
- Added mypyc compilation for performance increases. Credit to Jie Fan for the code + testing

## [2.1.1] - 12 March 2024

- Fixed bug with only a single ship getting mine blast damage within the blast radius
- Fixed error in mine cooldown
- Added invincibility for mines during respawn

## [2.1.0] - 7 March 2024

- Multiple changes to enhance/optimize calculations
  - Reduction in calls to transcendental functions in math/numpy
  - Reduced numpy calls for non-vector/less inefficient implementations
  - Refined collision checks
  - Changed destruct order to asteroids before ships
- Added `time_limit` to game state info passed to controller
- Fixed bug in mine detonation where coincidence with asteroids/ships caused undesired destruct behavior
  - Changed such that if coincident with asteroid with 0 speed, momentum is imparted and split angles are uniform

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
