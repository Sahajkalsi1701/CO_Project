# Instruction Type Mappings
I_TYPE = {
    "addi": {"opcode": "0010011", "funct3": "000"},
    "lw":   {"opcode": "0000011", "funct3": "010"},
    "jalr": {"opcode": "1100111", "funct3": "000"}
}

R_TYPE = {
    "add":  {"opcode": "0110011", "funct3": "000", "funct7": "0000000"},
    "sub":  {"opcode": "0110011", "funct3": "000", "funct7": "0100000"},
    "slt":  {"opcode": "0110011", "funct3": "010", "funct7": "0000000"},
    "srl":  {"opcode": "0110011", "funct3": "101", "funct7": "0000000"},
    "or":   {"opcode": "0110011", "funct3": "110", "funct7": "0000000"},
    "and":  {"opcode": "0110011", "funct3": "111", "funct7": "0000000"}
}

S_TYPE = {
    "sw": {"opcode": "0100011", "funct3": "010"}
}

B_TYPE = {
    "beq": {"opcode": "1100011", "funct3": "000"},
    "bne": {"opcode": "1100011", "funct3": "001"}
}

J_TYPE = {
    "jal": {"opcode": "1101111"}
}

def initialize_registers():
    return {f'x{i}': 0 for i in range(32)}

def initialize_memory(size=32):
    return [0] * size

def load_program(file_path, memory):
    def validate_instruction(line):
        if len(line) != 32:
            return False
        return all(c in '01' for c in line)

    try:
        with open(file_path, 'r') as file:
            instructions = []
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                if not validate_instruction(line):
                    raise ValueError(f"Invalid instruction format at line {line_num}")
                instructions.append(line)
            
            if len(instructions) > len(memory):
                raise ValueError("Program exceeds memory capacity")
            
            for i, instr in enumerate(instructions):
                memory[i] = int(instr, 2)
            return True
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return False
    except Exception as e:
        print(f"Error loading program: {str(e)}")
        return False

def binary_to_decimal(binary_str, bits=32):
    if len(binary_str) > bits:
        binary_str = binary_str[-bits:]  # Truncate to required bits
    
    if binary_str[0] == '1':  # Negative number
        inverted = ''.join('1' if bit == '0' else '0' for bit in binary_str)
        return -1 * (int(inverted, 2) + 1)
    return int(binary_str, 2)

def execute_r_type(instr, pc, registers, memory):
    funct7 = instr[:7]
    rs2 = int(instr[7:12], 2)
    rs1 = int(instr[12:17], 2)
    funct3 = instr[17:20]
    rd = int(instr[20:25], 2)
    opcode = instr[25:]

    rs1_val = registers[f'x{rs1}']
    rs2_val = registers[f'x{rs2}']

    if funct3 == R_TYPE["add"]["funct3"]:
        if funct7 == R_TYPE["add"]["funct7"]:
            result = rs1_val + rs2_val
        elif funct7 == R_TYPE["sub"]["funct7"]:
            result = rs1_val - rs2_val
        else:
            raise ValueError(f"Unknown R-type funct7: {funct7}")
    elif funct3 == R_TYPE["slt"]["funct3"]:
        result = 1 if rs1_val < rs2_val else 0
    elif funct3 == R_TYPE["srl"]["funct3"]:
        result = rs1_val >> (rs2_val % 32)
    elif funct3 == R_TYPE["or"]["funct3"]:
        result = rs1_val | rs2_val
    elif funct3 == R_TYPE["and"]["funct3"]:
        result = rs1_val & rs2_val
    else:
        raise ValueError(f"Unknown R-type funct3: {funct3}")

    write_register(registers, rd, result)
    return pc + 4

def execute_i_type(instr, pc, registers, memory):
    imm = binary_to_decimal(instr[:12], 12)
    rs1 = int(instr[12:17], 2)
    funct3 = instr[17:20]
    rd = int(instr[20:25], 2)
    opcode = instr[25:]

    rs1_val = registers[f'x{rs1}']

    if opcode == I_TYPE["addi"]["opcode"] and funct3 == I_TYPE["addi"]["funct3"]:
        result = rs1_val + imm
    elif opcode == I_TYPE["lw"]["opcode"] and funct3 == I_TYPE["lw"]["funct3"]:
        addr = rs1_val + imm
        if 0 <= addr < len(memory) * 4:
            result = memory[addr // 4]
        else:
            raise ValueError(f"Invalid memory address: {addr:08x}")
    elif opcode == I_TYPE["jalr"]["opcode"] and funct3 == I_TYPE["jalr"]["funct3"]:
        write_register(registers, rd, pc + 4)
        return rs1_val + imm
    else:
        raise ValueError(f"Unknown I-type opcode/funct3: {opcode}/{funct3}")

    write_register(registers, rd, result)
    return pc + 4

def execute_s_type(instr, pc, registers, memory):
    imm_high = instr[:7]
    rs2 = int(instr[7:12], 2)
    rs1 = int(instr[12:17], 2)
    funct3 = instr[17:20]
    imm_low = instr[20:25]
    opcode = instr[25:]

    imm = binary_to_decimal(imm_high + imm_low, 12)
    rs1_val = registers[f'x{rs1}']
    rs2_val = registers[f'x{rs2}']

    if opcode == S_TYPE["sw"]["opcode"] and funct3 == S_TYPE["sw"]["funct3"]:
        addr = rs1_val + imm
        if 0 <= addr < len(memory) * 4:
            memory[addr // 4] = rs2_val
        else:
            raise ValueError(f"Invalid memory address: {addr:08x}")
    else:
        raise ValueError(f"Unknown S-type opcode/funct3: {opcode}/{funct3}")

    return pc + 4

def execute_b_type(instr, pc, registers, memory):
    imm_12 = instr[0]
    imm_10_5 = instr[1:7]
    rs2 = int(instr[7:12], 2)
    rs1 = int(instr[12:17], 2)
    funct3 = instr[17:20]
    imm_4_1 = instr[20:24]
    imm_11 = instr[24]
    opcode = instr[25:]

    imm = binary_to_decimal(imm_12 + imm_11 + imm_10_5 + imm_4_1 + '0', 13)
    rs1_val = registers[f'x{rs1}']
    rs2_val = registers[f'x{rs2}']

    # Special case for halt (beq x0, x0, 0)
    if rs1 == 0 and rs2 == 0 and imm == 0 and opcode == B_TYPE["beq"]["opcode"]:
        return -1  # Halt signal

    branch_taken = False
    if funct3 == B_TYPE["beq"]["funct3"]:
        branch_taken = (rs1_val == rs2_val)
    elif funct3 == B_TYPE["bne"]["funct3"]:
        branch_taken = (rs1_val != rs2_val)
    else:
        raise ValueError(f"Unknown B-type funct3: {funct3}")

    return pc + (imm if branch_taken else 4)

def execute_j_type(instr, pc, registers, memory):
    imm_20 = instr[0]
    imm_10_1 = instr[1:11]
    imm_11 = instr[11]
    imm_19_12 = instr[12:20]
    rd = int(instr[20:25], 2)
    opcode = instr[25:]

    imm = binary_to_decimal(imm_20 + imm_19_12 + imm_11 + imm_10_1 + '0', 21)

    if opcode == J_TYPE["jal"]["opcode"]:
        write_register(registers, rd, pc + 4)
        return pc + imm
    else:
        raise ValueError(f"Unknown J-type opcode: {opcode}")

def write_register(registers, reg_num, value):
    if reg_num != 0:  # x0 is hardwired to zero
        registers[f'x{reg_num}'] = value & 0xFFFFFFFF  # 32-bit mask

def execute_instruction(instruction, pc, registers, memory):
    opcode = instruction[25:]

    try:
        if opcode == R_TYPE["add"]["opcode"]:
            return execute_r_type(instruction, pc, registers, memory)
        elif opcode in {I_TYPE[op]["opcode"] for op in ["addi", "lw", "jalr"]}:
            return execute_i_type(instruction, pc, registers, memory)
        elif opcode == S_TYPE["sw"]["opcode"]:
            return execute_s_type(instruction, pc, registers, memory)
        elif opcode == B_TYPE["beq"]["opcode"]:
            return execute_b_type(instruction, pc, registers, memory)
        elif opcode == J_TYPE["jal"]["opcode"]:
            return execute_j_type(instruction, pc, registers, memory)
        elif opcode == "1110011":  # ECALL/EBREAK
            return -1
        else:
            raise ValueError(f"Unknown opcode: {opcode}")
    except Exception as e:
        print(f"Error executing instruction at PC {pc:08x}: {str(e)}")
        return -2

def format_registers(pc, registers):
    pc_hex = f"{pc:08x}"
    reg_lines = []
    for i in range(32):
        reg_val = registers[f'x{i}'] & 0xFFFFFFFF
        reg_lines.append(f"x{i}:0b{reg_val:032b}")
    return pc_hex + " " + " ".join(reg_lines)

def format_memory(memory):
    memory_dump = []
    for i in range(len(memory)):
        addr = 0x00010000 + i * 4
        value = memory[i]
        memory_dump.append(f"0x{addr:08X}:0b{value:032b}")
    return memory_dump

def run_simulation(input_path, output_path):
    registers = initialize_registers()
    memory = initialize_memory()
    
    if not load_program(input_path, memory):
        print("Failed to load program")
        return False
    
    pc = 0
    halted = False
    last_pc = -1
    max_steps = 10000
    step_count = 0

    with open(output_path, 'w') as f:
        while not halted and 0 <= pc < len(memory)*4:
            if pc == last_pc:
                print(f"Warning: Infinite loop detected at PC {pc:08x}")
                break
            if step_count > max_steps:
                print(f"Stopped after {max_steps} steps (possible infinite loop)")
                break

            last_pc = pc
            step_count += 1
            
            # Ensure x0 is always zero
            registers['x0'] = 0
            
            try:
                instr = memory[pc // 4]
                instr_bin = bin(instr)[2:].zfill(32)
                new_pc = execute_instruction(instr_bin, pc, registers, memory)
                
                f.write(format_registers(pc, registers) + "\n")
                
                if new_pc == -1:  # Halt
                    halted = True
                elif new_pc == -2:  # Error
                    break
                else:
                    pc = new_pc
            except Exception as e:
                print(f"Error at PC {pc:08x}: {str(e)}")
                break

        f.write("\nMemory:\n")
        for line in format_memory(memory):
            f.write(line + "\n")

    return halted

def main():
    input_path = input("Enter the input file path: ")
    output_path = input("Enter the output file path: ")
    
    success = run_simulation(input_path, output_path)
    if success:
        print("Simulation completed successfully")
    else:
        print("Simulation has issues")

if __name__ == "__main__":
    main()