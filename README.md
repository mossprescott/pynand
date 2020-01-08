# From Nand to Tetris in Python

An alternative language and test harness for doing the exercises from the amazing book/course
[Nand To Tetris](https://www.nand2tetris.org). My goal is to provide a better experience
as compared to the tools provided by the authors:

* No need to install Java
* No clunky UI
* You only need python, a text editor, and basic command-line skills.


## Requirements

You need to have Python installed, at least version 3.6.

Pytest is required to run the tests: `pip3 install pytest`.

For the full Computer simulation including display and keyboard, `pygame` is required:
`pip3 install pygame`. On Mac OS X, you may need to install a dev version: 
`pip3 install pygame==2.0.0dev6`


## Step 1: Do the Exercises

_NOTE: for the time being, solved versions of each component are included. When everything's 
working as intended, we'll come back and clean it up so the exercises are ready to solve._

First clone the repo and run `pytest`. If your environment is set up, you should see a lot of 
errors, because none of the components are implemented yet (except `Nand`, which you get for 
free).

Now open `project01.py` in a text editor and replace the `___`s in the body of the `mkNot` 
function with references to the input so that it computes the expected result.

Run `pytest test_01.py`. If `test_not` passes, you can move on to the next component.

When all those tests pass, you're done with the first chapter. Move on to test_02.py…


## Step 2: Enjoy

Run `python computer.py examples/Pong.asm`. Bask in the glory of a CPU you built from scratch.
Note: the awesomeness starts after about 5 million cycles.


## Step 3: Go Further


### Your CPU Design

The components here can be used to implement any generally similar CPU design. Ideas:

- Make a fancier ALU. What features do you think would be useful?
- Make a better instruction encoding. How can it do more with less?
- Make an even smaller CPU. What can you take away and still get stuff done?

Note: if you want to run any programs, you'll have to figure out how to get them into
your new chip's instruction format. One way to do that is to implement a new VM-assembly 
translator, and find some VM programs to run on both chips for comparison.


### Your Language

What language do you like to write? Can you compile _that_ language, or something like it, to
the Hack VM? Or directly to assembly?