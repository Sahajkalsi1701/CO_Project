import sys

# Register mappings
regs = {
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011", "tp": "00100",
    "t0": "00101", "t1": "00110", "t2": "00111", "s0": "01000", "s1": "01001",
    "a0": "01010", "a1": "01011", "a2": "01100", "a3": "01101", "a4": "01110",
    "a5": "01111", "a6": "10000", "a7": "10001", "s2": "10010", "s3": "10011",
    "s4": "10100", "s5": "10101", "s6": "10110", "s7": "10111", "s8": "11000",
    "s9": "11001", "s10": "11010", "s11": "11011", "t3": "11100", "t4": "11101",
    "t5": "11110", "t6": "11111"
}

# Instruction formats
insts = {
    "add": {"op": "0110011", "f3": "000", "f7": "0000000"},
    "sub": {"op": "0110011", "f3": "000", "f7": "0100000"},
    "slt": {"op": "0110011", "f3": "010", "f7": "0000000"},
    "or":  {"op": "0110011", "f3": "110", "f7": "0000000"},
    "srl": {"op": "0110011", "f3": "101", "f7": "0000000"},
    "lw":  {"op": "0000011", "f3": "010"},
    "addi": {"op": "0010011", "f3": "000"},
    "jalr": {"op": "1100111", "f3": "000"},
    "sw":   {"op": "0100011", "f3": "010"},
    "beq":  {"op": "1100011", "f3": "000"},
    "bne":  {"op": "1100011", "f3": "001"},
    "blt":  {"op": "1100011", "f3": "100"},
    "jal":  {"op": "1101111"}
}

def make_binary(num, size):
    """Convert a number to a binary string of specified size, handling negatives."""
    if num < 0:
        num = (2 ** size) + num
    return bin(num)[2:].zfill(size)

def parse_immediate(imm_str, labels, pc, inst, line_num, size):
    """Parse an immediate value or label, returning the binary representation."""
    if imm_str in labels:
        if inst in ["beq", "bne", "blt"]:
            imm = (labels[imm_str] - pc) // 4  # Branch offset in words
        elif inst == "jal":
            imm = (labels[imm_str] - pc) // 4  # JAL offset in words
        else:
            imm = labels[imm_str]  # Absolute address or offset
    else:
        try:
            imm = int(imm_str)
        except ValueError:
            print(f"Error at line {line_num}: invalid immediate or undefined label '{imm_str}'")
            sys.exit(1)
    if not (-(2 ** (size - 1)) <= imm <= (2 ** (size - 1) - 1)):
        print(f"Error at line {line_num}: immediate {imm} out of range for {size}-bit field")
        sys.exit(1)
    return make_binary(imm, size)

def do_instruction(line, num, labels, pc):
    """Convert a single assembly instruction to binary."""
    parts = line.replace(",", " ").replace("(", " ").replace(")", "").split()
    if not parts or parts[0].endswith(":"):
        return None
    inst = parts[0]
    if inst not in insts:
        print(f"Error at line {num}: unknown instruction '{inst}'")
        sys.exit(1)
    op = insts[inst]["op"]

    # R-type instructions
    if inst in ["add", "sub", "slt", "or", "srl"]:
        if len(parts) != 4:
            print(f"Error at line {num}: {inst} expects 3 registers (rd, rs1, rs2)")
            sys.exit(1)
        rd, rs1, rs2 = map(regs.get, parts[1:4])
        if None in (rd, rs1, rs2):
            print(f"Error at line {num}: invalid register in {inst}")
            sys.exit(1)
        return insts[inst]["f7"] + rs2 + rs1 + insts[inst]["f3"] + rd + op

    # I-type instructions (lw, addi, jalr)
    elif inst in ["lw", "addi", "jalr"]:
        if len(parts) != 4:
            print(f"Error at line {num}: {inst} expects rd, rs1, and immediate")
            sys.exit(1)
        rd = regs.get(parts[1])
        rs1 = regs.get(parts[3] if inst == "lw" else parts[2])
        imm_str = parts[2] if inst == "lw" else parts[3]
        if None in (rd, rs1):
            print(f"Error at line {num}: invalid register in {inst}")
            sys.exit(1)
        imm_bin = parse_immediate(imm_str, labels, pc, inst, num, 12)
        return imm_bin + rs1 + insts[inst]["f3"] + rd + op

    # S-type instruction (sw)
    elif inst == "sw":
        if len(parts) != 4:
            print(f"Error at line {num}: sw expects rs2, imm(rs1)")
            sys.exit(1)
        rs2, imm_str, rs1 = regs.get(parts[1]), parts[2], regs.get(parts[3])
        if None in (rs1, rs2):
            print(f"Error at line {num}: invalid register in sw")
            sys.exit(1)
        imm_bin = parse_immediate(imm_str, labels, pc, inst, num, 12)
        return imm_bin[:7] + rs2 + rs1 + insts[inst]["f3"] + imm_bin[7:] + op

    # B-type instructions (beq, bne, blt)
    elif inst in ["beq", "bne", "blt"]:
        if len(parts) != 4:
            print(f"Error at line {num}: {inst} expects rs1, rs2, and offset")
            sys.exit(1)
        rs1, rs2 = map(regs.get, parts[1:3])
        if None in (rs1, rs2):
            print(f"Error at line {num}: invalid register in {inst}")
            sys.exit(1)
        imm_bin = parse_immediate(parts[3], labels, pc, inst, num, 13)
        return imm_bin[0] + imm_bin[2:8] + rs2 + rs1 + insts[inst]["f3"] + imm_bin[8:12] + imm_bin[1] + op

    # J-type instruction (jal)
    elif inst == "jal":
        if len(parts) != 3:
            print(f"Error at line {num}: jal expects rd and offset")
            sys.exit(1)
        rd = regs.get(parts[1])
        if rd is None:
            print(f"Error at line {num}: invalid register in jal")
            sys.exit(1)
        imm_bin = parse_immediate(parts[2], labels, pc, inst, num, 21)
        return imm_bin[0] + imm_bin[10:20] + imm_bin[9] + imm_bin[1:9] + rd + op

def assemble(infile, outfile):
    """Assemble the input file into binary and write to output file."""
    try:
        with open(infile, "r") as f:
            lines = [line.strip().split('#')[0].strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: Input file '{infile}' not found")
        sys.exit(1)

    lines = [line for line in lines if line]  # Remove empty lines

    # First pass: collect labels
    labels = {}
    pc = 0
    for i, line in enumerate(lines, 1):
        if line.endswith(":"):
            label = line[:-1]
            if label in labels:
                print(f"Error at line {i}: duplicate label '{label}'")
                sys.exit(1)
            labels[label] = pc
        else:
            pc += 4

    # Check for halt instruction
    if lines and "beq" in lines[-1] and "zero" in lines[-1] and "0" in lines[-1]:
        pass  # Halt detected
    else:
        print("Warning: No halt instruction (e.g., 'beq zero, zero, 0') at end")

    # Second pass: generate binary
    binary, pc = [], 0
    for i, line in enumerate(lines, 1):
        if line and not line.endswith(":"):
            result = do_instruction(line, i, labels, pc)
            if result:
                binary.append(result)
            pc += 4

    try:
        with open(outfile, "w") as f:
            f.writelines(b + "\n" for b in binary)
        print(f"Successfully assembled {infile} to {outfile}")
    except IOError:
        print(f"Error: Failed to write to output file '{outfile}'")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python assembler.py <input_file> <output_file>")
        sys.exit(1)
    assemble(sys.argv[1], sys.argv[2])