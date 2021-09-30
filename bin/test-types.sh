#! /usr/bin/env bash

# Check type annotations, which can be helpful but may include some spurious errors.
#
# Requires mypy; run `pip install -r bin/test-requirements.txt`.

cd $(dirname $0)/..

PYTHONPATH=. mypy nand/ *.py
