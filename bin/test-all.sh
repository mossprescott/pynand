#! /usr/bin/env bash

# Run tests to verify the platform, including doctest examples and type annotations.
#
# Users/solvers are not expected to run all these tests. They only need to run the
# tests for each project, found at the root of the project: `pytest test_*.py`.

cd $(dirname $0)/..

pytest --doctest-modules nand project_*.py test_*.py
