# From Nand to Tetris in Python

An alternative language and test harness for doing the exercises from the amazing book/course
[Nand To Tetris](https://www.nand2tetris.org). My goal is to provide a better experience
as compared to the tools provided by the authors:

* No need to install Java
* No clunky UI
* You only need python, a text editor, and basic command-line skills.

## Requirements

You need to have Python installed, at least version 3.6.

Pytest is required to run the tests: `pip install pytest`.

## Doing exercises

_NOTE: for the time being, solved versions of each component are included. When everything's working as intended,
we'll come back and clean it up so the exercises are ready to solve._

First clone the repo and run `pytest`. If your environment is set up, you should see a lot of errors,
because none of the components are implemented yet (except `Nand`, which you get for free).

Now open `project01.py` in a text editor and replace the `___`s in the body of the `mkNot` function
with references to the input so that it computes the expected result.

Run `pytest test_01.py`. If `test_not` passes, you can move on to the next component.

When all those tests pass, you're done with the first chapter.
