# Contributing to sigman

First of all, cheers for the interest in making sigman smooth :fireworks::tada::sparkler:

Sigman is, above all, built with cooperation in mind. In this spirit there are a few guidelines to follow when contributing to avoid spaghettification of our code, written below.

Do you want to help out, but don't know what to do? Check out [open issues](https://github.com/k-cybulski/sigman-project/issues) and see if anything catches your eye.

## Code standards
All code ought to follow the [PEP-8](https://www.python.org/dev/peps/pep-0008/) standard, especially:
* **All indentation must be 4 spaces**
* Keep code line length below 80 characters and documentation below 73
* All names must be in English

Naming conventions differ between **sigman** and **QtSigman**:
* **sigman** should follow `lowercase_with_underscores`
* **QtSigman** should follow `CamelCase` to be consistent with PyQt5

Docstrings should also follow [PEP-257](https://www.python.org/dev/peps/pep-0257/).

## Git workflow
If you wish to make an addition to sigman, please follow this scheme:
1. Choose an issue from the GitHub repository you wish to work on. If no issue describes the feature you need, make one and describe the wanted feature in detail.
2. Fork or create a new branch locally
  * If you're not a confirmed contributor, [make your own fork](https://guides.github.com/activities/forking/#fork) and [clone it](https://guides.github.com/activities/forking/#clone)
  * If you are, make a branch and name it one of these for clarity:
    * If you wish to add an analysis procedure - `procedure/<issue number>-<short name>` 
    * If you wish to add a new feature to sigman or QtSigman - `feature/<issue number>-<short name>` 
    * If you wish to fix a bug - `bug/<issue number>-<short name>`
    * If none of the above apply, and only then, simply `<issue number>-<short name>`
  * A quick way to make a branch is `git checkout -b <name of new branch>`
3. Perform the changes and test to see if they work
4. Commit changes while:
  * Referencing the issue in the commit message by writing `#<issue number>` at the beginning
  * Following [this guide](chris.beams.io/posts/git-commit) for writing commit messages
5. Upload the branch or fork
  * Fork (if you haven't made any new branches) - `git push origin master`
  * Branch - `git push origin <name of branch>`
6. Create a pull request to the master branch
  * [From a fork](https://help.github.com/articles/creating-a-pull-request-from-a-fork/)
  * [From a branch](https://help.github.com/articles/creating-a-pull-request/)
  * Your code will be reviewed by a core developer and will either be accepted or commented upon for further changes

And that's it! Your code is now an internal part of sigman.

## Code structure
The code is divided into designated files and creating new files is discouraged. The current structure is as follows:
* sigman
  * `sigman/__init__.py` - main data types and their operations
  * `sigman/file_manager.py` - file import and export
  * `sigman/analyzer.py` - external procedure import and analysis
  * `sigman/visualizer.py` - quick and dirty visualization, mainly for testing
* QtSigman
  * `QtSigman/__init__.py` - sigman data type extensions and main window
    * All QtSigman functionality is centered around `QtSigmanWindow`
  * `QtSigman/MplWidgets.py` - data visualization widgets
  * `QtSigman/DefaultColors.py` - colour to data assignment
  * `QtSigman/DataActions.py` - functions that perform actions on data (importing files into QtSigman, analysis)
    * Low level file operations should be performed in `sigman/file_manager.py`. `DataActions` should only interact with files at a high level via `file_manager`
  * `QtSigman/DataActionWidgets.py` - widgets that retrieve information regarding data actions from the user, like file names and data types
  * `QtSigman/ListWidgets.py` - widgets that list data (on the right of the main window)

Procedures are kept in `procedures/` and supposed to comply with specifications set out in `sigman/analyzer.py`
