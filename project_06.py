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

def asm_op(line):
    line = line.strip()
    
    m = re.match(r"@(\d+)", line)
    if m:
        return int(m.group(1))
    else:
        m = re.match(r"(?:([ADM]+)=)?([^;]+)(?:;J(..))?", line)
        if m:
            dest = 0
            if m.group(1):
                if 'A' in m.group(1):
                    dest |= 0b100
                if 'D' in m.group(1):
                    dest |= 0b010
                if 'M' in m.group(1):
                    dest |= 0b001
            
            alu_str = m.group(2).replace('M', 'A')
            if alu_str in ALU_CONTROL:
                alu = ALU_CONTROL[alu_str]
                m_for_a = int('M' in m.group(2))
            else:
                raise Exception(f"unrecognized alu op: {m.group(2)}")
                
            if m.group(3) is None:
                jmp = 0
            elif m.group(3) in JMP_CONTROL:
                jmp = JMP_CONTROL[m.group(3)]
            else:
                raise Exception(f"unrecognized jump: J{m.group(3)}")
            
            return (0b111 << 13) | (m_for_a << 12) | (alu << 6) | (dest << 3) | jmp
        else:
            raise Exception(f"unrecognized: {line}")
