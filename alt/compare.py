from nand import gate_count
import project_05, project_06, project_08
import test_optimal_08
import alt.lazy
import alt.shift
import alt.sp
import alt.threaded

def main():
    std = measure(
        project_05.Computer, project_06.assemble, project_08.Translator)
    print_result("project_08.py", std)

    print_relative_result("alt/shift.py", std, measure(alt.shift.ShiftComputer, alt.shift.assemble, alt.shift.Translator))
    print_relative_result("alt/lazy.py", std, measure(project_05.Computer, project_06.assemble, alt.lazy.Translator))
    print_relative_result("alt/sp.py", std, measure(alt.sp.SPComputer, alt.sp.assemble, alt.sp.Translator))
    print_relative_result("alt/threaded.py", std, measure(alt.threaded.ThreadedComputer, alt.threaded.assemble, alt.threaded.Translator))


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


def measure(chip, assemble, translator):
    return (
        gate_count(chip)['nands'],
        test_optimal_08.count_pong_instructions(translator),
        test_optimal_08.count_pong_cycles_first_iteration(chip, assemble, translator),
        test_optimal_08.count_cycles_to_init(chip, assemble, translator)
    )


if __name__ == "__main__":
    main()
