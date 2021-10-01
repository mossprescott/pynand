#! /usr/bin/env pytest

import pytest

from alt.risc.asm import *

def test_simple_ops():
    assert parse_op("add r0 r0 r0", {})  == 0b000_000_000_0000_000
    assert parse_op("add r3 r5 r7", {})  == 0b000_011_101_0000_111

    assert parse_op("addi r1 r2 13", {}) == 0b001_001_010_0001101
    assert parse_op("addi r1 r2 -1", {}) == 0b001_001_010_1111111

    assert parse_op("nand r0 r0 r0", {}) == 0b010_000_000_0000_000
    assert parse_op("nand r4 r2 r1", {}) == 0b010_100_010_0000_001

    assert parse_op("lui r1 256", {})    == 0b011_001_00_0000_0100
    assert parse_op("lui r1 -64", {})    == 0b011_001_11_1111_1111

    assert parse_op("lw r1 r0 0", {})    == 0b100_001_000_0000000
    assert parse_op("sw r0 r2 0", {})    == 0b101_000_010_0000000

    assert parse_op("beq r0 r2 +1", {})  == 0b110_000_010_0000001

    assert parse_op("jalr r7 r2", {})    == 0b111_111_010_0000_000


def test_absolute_labels():
    symbols = {"main.main": 16389}  # (256 << 6) + 5

    assert parse_op("lui r2 @main.main", symbols) == 0b011_010_01_0000_0000
    assert parse_op("lli r2 @main.main", symbols) == 0b001_010_010_000_0101


def test_relative_labels():
    symbols = {"end0": 125}
    assert parse_op("beq r0 r2 @end0", symbols, location=123) == 0b110_000_010_0000001  # +1 to skip the next instr


def test_errors():
    with pytest.raises(Exception) as exc_info:
        parse_op("addi r1 r2 64", {})
    assert exc_info.value.args[0].startswith("Constant value doesn't fit")

    with pytest.raises(parsing.ParseFailure):
        parse_op("addi r1 r2 @start", {"start": 12345})
