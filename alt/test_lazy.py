#! /usr/bin/env pytest

import pytest

import test_07
import test_08
import test_optimal_08

from alt.lazy import *


#
# VM translator:
#

def test_vm_simple_add():
    test_07.test_simple_add(translator=Translator)

def test_vm_stack_ops():
    test_07.test_stack_ops(translator=Translator)

def test_vm_memory_access_basic():
    test_07.test_memory_access_basic(translator=Translator)

def test_vm_memory_access_pointer():
    test_07.test_memory_access_pointer(translator=Translator)

def test_vm_memory_access_static():
    test_07.test_memory_access_static(translator=Translator)


def test_vm_basic_loop():
    test_08.test_basic_loop(translator=Translator)

def test_vm_fibonacci_series():
    test_08.test_fibonacci_series(translator=Translator)

def test_vm_simple_function():
    test_08.test_simple_function(translator=Translator)

def test_vm_nested_call():
    test_08.test_nested_call(translator=Translator)

def test_vm_fibonacci_element():
    test_08.test_fibonacci_element(translator=Translator)

def test_vm_statics_multiple_files():
    test_08.test_statics_multiple_files(translator=Translator)


def test_vm_pong_instructions():
    instruction_count = test_optimal_08.count_pong_instructions(platform=LAZY_PLATFORM)

    assert instruction_count < 24_000


def test_pong_first_iteration():
    cycles = test_optimal_08.count_pong_cycles_first_iteration(platform=LAZY_PLATFORM)

    assert cycles < 37_500


def test_vm_cycles_to_init():
    cycles = test_optimal_08.count_cycles_to_init(platform=LAZY_PLATFORM)

    assert cycles < 112_000
