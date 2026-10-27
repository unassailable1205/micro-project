"""
COA Module: Two-Pass Assembler
Translates assembly instructions with labels, symbolic memory addresses,
and immediate operands into machine instructions.
"""

from typing import List, Dict, Tuple, Optional
import re
from .isa import Instruction, OPCODES, REGISTERS
from .memory import Memory


class AssemblerError(Exception):
    def __init__(self, message: str, line_no: int, line_text: str):
        super().__init__(f"Assembler Error at line {line_no}: {message} -> '{line_text}'")
        self.message = message
        self.line_no = line_no
        self.line_text = line_text


class Assembler:
    def __init__(self, memory: Optional[Memory] = None):
        self.memory = memory if memory is not None else Memory()
        self.symbol_table: Dict[str, int] = {}  # label -> memory_address
        self.data_symbols: Dict[str, int] = {}   # var_name -> memory_address

    def assemble(self, source_text: str, start_address: int = 0) -> List[Instruction]:
        lines = source_text.strip().split("\n")
        
        # Pass 1: Collect labels and determine instruction addresses
        cleaned_lines: List[Tuple[int, str]] = []  # (original_line_num, text)
        current_addr = start_address
        
        for idx, line in enumerate(lines, start=1):
            # Strip comments (// or ;)
            line_no_comment = re.sub(r"(//|;).*", "", line).strip()
            if not line_no_comment:
                continue

            # Check for label (e.g., LOOP_START:)
            label_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):(.*)$", line_no_comment)
            if label_match:
                lbl = label_match.group(1)
                self.symbol_table[lbl] = current_addr
                rest = label_match.group(2).strip()
                if rest:
                    cleaned_lines.append((idx, rest))
                    current_addr += 1
            else:
                cleaned_lines.append((idx, line_no_comment))
                current_addr += 1

        # Pass 2: Translate instructions into Instruction objects
        instructions: List[Instruction] = []
        for line_num, (orig_line, text) in enumerate(cleaned_lines):
            addr = start_address + line_num
            instr = self._parse_instruction(text, addr, orig_line)
            instructions.append(instr)
            self.memory.write_instruction(addr, instr)

        return instructions

    def _parse_instruction(self, text: str, address: int, orig_line_no: int) -> Instruction:
        # Tokenize line: MNEMONIC [arg1, arg2, ...]
        parts = re.split(r"[\s,]+", text.strip())
        mnemonic = parts[0].upper()

        if mnemonic not in OPCODES:
            raise AssemblerError(f"Unknown instruction mnemonic '{mnemonic}'", orig_line_no, text)

        rd = None
        rs1 = None
        rs2 = None
        imm = 0

        try:
            if mnemonic in ("NOP", "HALT"):
                pass

            elif mnemonic == "LDI":
                # LDI Rd, imm
                rd = parts[1].upper()
                imm = self._resolve_val(parts[2])

            elif mnemonic in ("LOAD", "STORE"):
                # LOAD Rd, [addr] or STORE Rs, [addr]
                reg = parts[1].upper()
                raw_addr = parts[2].strip("[]")
                resolved_addr = self._resolve_val(raw_addr)
                if mnemonic == "LOAD":
                    rd = reg
                    imm = resolved_addr
                else:
                    rs1 = reg
                    imm = resolved_addr

            elif mnemonic == "MOV":
                # MOV Rd, Rs
                rd = parts[1].upper()
                rs1 = parts[2].upper()

            elif mnemonic in ("ADD", "SUB", "MUL", "DIV", "MOD", "AND", "OR", "XOR"):
                # ADD Rd, Rs1, Rs2
                rd = parts[1].upper()
                rs1 = parts[2].upper()
                rs2 = parts[3].upper()

            elif mnemonic in ("ADDI", "SUBI"):
                # ADDI Rd, Rs, imm
                rd = parts[1].upper()
                rs1 = parts[2].upper()
                imm = self._resolve_val(parts[3])

            elif mnemonic == "CMP":
                # CMP Rs1, Rs2
                rs1 = parts[1].upper()
                rs2 = parts[2].upper()

            elif mnemonic == "CMPI":
                # CMPI Rs, imm
                rs1 = parts[1].upper()
                imm = self._resolve_val(parts[2])

            elif mnemonic in ("JMP", "JZ", "JNZ", "JGT", "JLT"):
                # JMP label / addr
                target = parts[1]
                imm = self._resolve_val(target)

            elif mnemonic == "PRINT":
                # PRINT Rs
                rs1 = parts[1].upper()

        except Exception as e:
            raise AssemblerError(str(e), orig_line_no, text)

        return Instruction(
            mnemonic=mnemonic,
            rd=rd,
            rs1=rs1,
            rs2=rs2,
            imm=imm,
            raw_assembly=text,
            address=address
        )

    def _resolve_val(self, token: str) -> int:
        # Check if symbol/label
        if token in self.symbol_table:
            return self.symbol_table[token]
        if token in self.memory.symbol_table:
            return self.memory.symbol_table[token]
        # Check if hex
        if token.startswith("0x") or token.startswith("0X"):
            return int(token, 16)
        # Check if integer
        return int(token)
