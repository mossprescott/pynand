import re

ALU_CONTROL = {
    "0":   0b101010,
    "A":   0b110000,
    "D":   0b001100,
    "D-A": 0b010011,
    "D+A": 0b000010,
    # unconfirmed:
    "1":   0b111111,
    "-1":  0b101001,
    "D&A": 0b000000,
    "D|A": 0b010101,
    "A-D": 0b000111,
    "!D":  0b001011,
    "!A":  0b100011,
    "D+1": 0b011111,
    "A+1": 0b110111,
    "D-1": 0b001110,
    "A-1": 0b110010,
    "-D":  0b001111,
    "-A":  0b110011,
}

JMP_CONTROL = {
    "LT": 0b100,
    "LE": 0b110,
    "EQ": 0b010,
    "NE": 0b101,
    "GE": 0b011,
    "GT": 0b001,
    "MP": 0b111,
}

BUILTIN_SYMBOLS = {
    **{
        "SP":       0,
        "LCL":      1,
        "ARG":      2,
        "THIS":     3,
        "THAT":     4,
        "SCREEN":   0x4000,
        "KEYBOARD": 0x6000,
    },
    **{ f"R{i}": i for i in range(15)}
}


def parse_op(string, symbols=BUILTIN_SYMBOLS):
    m = re.match(r"@(\d+)", string)
    if m:
        return int(m.group(1))
    else:
        m = re.match(r"@(.*)", string)
        if m:
            symbol_str = m.group(1)
            if symbol_str in symbols:
                return symbols[symbol_str]
            else:
                raise Exception(f"symbol not found: {symbol_str}")
        else:
            m = re.match(r"(?:([ADM]+)=)?([^;]+)(?:;J(..))?", string)
            if m:
                dest_str = m.group(1) or ""
                dest = 0
                if 'A' in dest_str:
                    dest |= 0b100
                if 'D' in dest_str:
                    dest |= 0b010
                if 'M' in dest_str:
                    dest |= 0b001
            
                alu_str = m.group(2).replace('M', 'A')
                if alu_str in ALU_CONTROL:
                    alu = ALU_CONTROL[alu_str]
                    m_for_a = int('M' in m.group(2))
                else:
                    raise Exception(f"unrecognized alu op: {m.group(2)}")
                
                jmp_str = m.group(3)
                if jmp_str is None:
                    jmp = 0
                elif jmp_str in JMP_CONTROL:
                    jmp = JMP_CONTROL[jmp_str]
                else:
                    raise Exception(f"unrecognized jump: J{m.group(3)}")
            
                return (0b111 << 13) | (m_for_a << 12) | (alu << 6) | (dest << 3) | jmp
            else:
                raise Exception(f"unrecognized: {line}")


def load_file(f):
    code_lines = []
    for line in f:
        m = re.match(r"([^/]*)(?://.*)?", line)
        if m:
            string = m.group(1).strip()
        else:
            string = line.strip()
        
        if string:
            code_lines.append(string)
    
    symbols = BUILTIN_SYMBOLS.copy()
    loc = 0
    for line in code_lines:
        m = re.match(r"\((.*)\)", line)
        if m:
            symbols[m.group(1)] = loc
        else:
            loc += 1
        
    ops = []
    for line in code_lines:
        if "(" not in line:
            ops.append(parse_op(line, symbols))
    return ops
