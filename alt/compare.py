#! /usr/bin/env python3

"""Run performance tests on all the implementations and summarize the results.

Note: this takes a couple of minutes to run.
"""

from nand import gate_count
import test_optimal_08

from nand.platform import BUNDLED_PLATFORM, USER_PLATFORM
from alt.eight import EIGHT_PLATFORM
from alt.lazy import LAZY_PLATFORM
from alt.reg import REG_PLATFORM
from alt.reduce import REDUCE_PLATFORM
from alt.shift import SHIFT_PLATFORM
from alt.sp import SP_PLATFORM
from alt.threaded import THREADED_PLATFORM
from alt.risc.main import RiSC_PLATFORM
from alt.risc.reg import RiSC_REG_PLATFORM

from alt.reduce import REDUCE_REG_PLATFORM
from alt.reduce import REDUCE_RiSC_REG_PLATFORM

def main():
    std = measure(BUNDLED_PLATFORM)
    print_result("solutions", std)

    print_relative_result("project_0x.py", std, measure(USER_PLATFORM))
    print_relative_result("alt/lazy.py", std, measure(LAZY_PLATFORM))
    print_relative_result("alt/sp.py", std, measure(SP_PLATFORM))
    print_relative_result("alt/threaded.py", std, measure(THREADED_PLATFORM))
    print_relative_result("alt/shift.py", std, measure(SHIFT_PLATFORM))
    print_relative_result("alt/reg.py", std, measure(REG_PLATFORM))
    print_relative_result("alt/reduce.py", std, measure(REDUCE_PLATFORM))

    # print_relative_result("alt/eight.py", std, measure(EIGHT_PLATFORM, "vector"))
    print_relative_result("alt/eight.py", std, (gate_count(EIGHT_PLATFORM.chip)['nands'], std[1], std[2]*2, std[3]*2))  # Cheeky
    # Note: currently the eight-bit CPU doesn't run correctly in the "codegen" simulator, so it's
    # a little painful to measure its performance directly. However, by design it takes exactly
    # two cycles per instruction, so we can just report that with a relatively clear conscience.

    print_relative_result("alt/risc/vm.py", std, measure(RiSC_PLATFORM))
    print_relative_result("alt/risc/reg.py", std, measure(RiSC_REG_PLATFORM))

    # Finally, the really impressive stuff (not shown in the table):
    print_relative_result("alt/reg.py (+reduce)", std, measure(REDUCE_REG_PLATFORM))
    print_relative_result("alt/risc/reg.py (+reduce)", std, measure(REDUCE_RiSC_REG_PLATFORM))


def print_result(name, t):
    nands, pong, frame, init = t
    print(f"{name}:")
    print(f"  Nands:               {nands:0,d}")
    print(f"  ROM size (Pong):     {pong:0,d}")
    print(f"  Cycles/frame (Pong): {frame:0,d}")
    print(f"  Cycles for init.:    {init:0,d}")


def print_relative_result(name, std, t):
    std_nands, std_pong, std_frame, std_init = std
    nands, pong, frame, init = t
    def fmt_pct(new, old):
        return f"{100*(new - old)/old:+0.1f}%"
    print(f"{name}:")
    print(f"  Nands:               {nands:0,d} ({fmt_pct(nands, std_nands)})")
    print(f"  ROM size (Pong):     {pong:0,d} ({fmt_pct(pong, std_pong)})")
    print(f"  Cycles/frame (Pong): {frame:0,d} ({fmt_pct(frame, std_frame)})")
    print(f"  Cycles for init.:    {init:0,d} ({fmt_pct(init, std_init)})")


def measure(platform, simulator="codegen"):
    return (
        gate_count(platform.chip)['nands'],
        test_optimal_08.count_pong_instructions(platform),
        test_optimal_08.count_pong_cycles_first_iteration(platform, simulator),
        test_optimal_08.count_cycles_to_init(platform, simulator)
    )


if __name__ == "__main__":
    main()
