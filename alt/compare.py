#! /usr/bin/env python3

"""Run performance tests on all the implementations and summarize the results.

Note: this takes a couple of minutes to run."""

from nand import gate_count
import test_optimal_08

from computer import HACK_PLATFORM, STANDARD_PLATFORM
from alt.lazy import LAZY_PLATFORM
from alt.shift import SHIFT_PLATFORM
from alt.sp import SP_PLATFORM
from alt.threaded import THREADED_PLATFORM

def main():
    std = measure(STANDARD_PLATFORM)
    print_result("solutions", std)

    print_relative_result("alt/shift.py", std, measure(SHIFT_PLATFORM))
    print_relative_result("alt/lazy.py", std, measure(LAZY_PLATFORM))
    print_relative_result("alt/sp.py", std, measure(SP_PLATFORM))
    print_relative_result("alt/threaded.py", std, measure(THREADED_PLATFORM))

    print_relative_result("project_0x.py", std, measure(HACK_PLATFORM))


def print_result(name, t):
    nands, pong, frame, init = t
    print(f"{name}:")
    print(f"  Nands: {nands:0,d}")
    print(f"  ROM size (Pong): {pong:0,d}")
    print(f"  Cycles for one frame (Pong): {frame:0,d}")
    print(f"  Cycles for initialization: {init:0,d}")


def print_relative_result(name, std, t):
    std_nands, std_pong, std_frame, std_init = std
    nands, pong, frame, init = t
    def fmt_pct(new, old):
        return f"{100*(new - old)/old:+0.1f}%"
    print(f"{name}:")
    print(f"  Nands: {nands:0,d} ({fmt_pct(nands, std_nands)})")
    print(f"  ROM size (Pong): {pong:0,d} ({fmt_pct(pong, std_pong)})")
    print(f"  Cycles for one frame (Pong): {frame:0,d} ({fmt_pct(frame, std_frame)})")
    print(f"  Cycles for initialization: {init:0,d} ({fmt_pct(init, std_init)})")


def measure(platform):
    return (
        gate_count(platform.chip)['nands'],
        test_optimal_08.count_pong_instructions(platform.translator),
        test_optimal_08.count_pong_cycles_first_iteration(platform.chip, platform.assemble, platform.translator),
        test_optimal_08.count_cycles_to_init(platform.chip, platform.assemble, platform.translator)
    )


if __name__ == "__main__":
    main()
