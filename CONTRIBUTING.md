# Contributing guidelines

## Contributing

### Create an Issue
- Use the standard GitHub issue tracker in this repository and outline a well-defined bug, feature request, or 
improvement.
- Utilize tags to assign appropriate labels to the issue
- Wait for the repository Administrators to respond to or approve your issue

### Fork the Repository
- Click on the fork button at the upper-right of the repository
- Make sure your fork from the appropriate branch that your desired changes apply to
- Once you have created a fork in your own account, clone it to your development environment

### Make Your Changes
- Add the desired feature, or fix a bug!
- Commit and push your changes to your fork

### Open a Pull Request
- Navigate the main Kessler repository and create a pull request against the branch you forked from
- Wait for approval and your changes to be merged

## License
- All contributions should be made under the requirements of the Apache 2.0 License outlined in [LICENSE](LICENSE)

## Coding style
- No explicit coding style is required for contributing to Kessler, however unorganized or messy code will not be
considered for contributions. Well-commented, concise, and clean code is required.

### MyPy Type Checking and MyPyC Compilation
- MyPy is used to statically type check the codebase. This catches a lot of bugs during development, and also speeds up the game with MyPyC compilation.
- After making changes, please run `mypy --strict path/to/kessler_game.py` to type check your changes, and make sure there are no errors.
- Once there are no errors, please also try compiling wheels with MyPyC, which use these static type hints to generate compiled extension modules which allow this game to run much more efficiently.
- To compile the game, type `python setup_mypyc.py bdist_wheel` within the root of the repo, where setup_mypyc.py lives. If all is successful, a platform-specific wheel will be placed in dist/
- Please then do `pip install wheelname.whl` to install and test the wheel. MyPyC wheels will do runtime type checking, so this can reveal more issues that need to be fixed.
