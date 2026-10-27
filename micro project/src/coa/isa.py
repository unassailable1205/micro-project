"""
COA Module: Instruction Set Architecture (ISA)
Defines registers, opcodes, instruction formats, and binary/hex encodings.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


# Register Mapping
REGISTERS = {
    "R0": 0,  # Accumulator / General Purpose 0
    "R1": 1,  # General Purpose 1
    "R2": 2,  # General Purpose 2
    "R3": 3,  # General Purpose 3
}

REG_INV = {v: k for k, v in REGISTERS.items()}

# Special Registers
SPECIAL_REGISTERS = ["PC", "IR", "MAR", "MDR", "SP"]

# Opcode Mapping (6-bit opcode: 0-63)
OPCODES = {
    "NOP": 0,
    "LDI": 1,     # LDI Rd, imm
    "LOAD": 2,    # LOAD Rd, [addr]
    "STORE": 3,   # STORE Rs, [addr]
    "MOV": 4,     # MOV Rd, Rs
    "ADD": 5,     # ADD Rd, Rs1, Rs2
    "ADDI": 6,    # ADDI Rd, Rs, imm
    "SUB": 7,     # SUB Rd, Rs1, Rs2
    "SUBI": 8,    # SUBI Rd, Rs, imm
    "MUL": 9,     # MUL Rd, Rs1, Rs2
    "DIV": 10,    # DIV Rd, Rs1, Rs2
    "MOD": 11,    # MOD Rd, Rs1, Rs2
    "AND": 12,    # AND Rd, Rs1, Rs2
    "OR": 13,     # OR Rd, Rs1, Rs2
    "XOR": 14,    # XOR Rd, Rs1, Rs2
    "CMP": 15,    # CMP Rs1, Rs2
    "CMPI": 16,   # CMPI Rs, imm
    "JMP": 17,    # JMP addr
    "JZ": 18,     # JZ addr
    "JNZ": 19,    # JNZ addr
    "JGT": 20,    # JGT addr
    "JLT": 21,    # JLT addr
    "PRINT": 22,  # PRINT Rs
    "HALT": 31,   # HALT
}

OPCODE_INV = {v: k for k, v in OPCODES.items()}


@dataclass
class Instruction:
    """
    Represents an encoded COA machine instruction.
    Format (32-bit logical word):
      [Opcode: 6 bits][Rd: 2 bits][Rs1: 2 bits][Rs2: 2 bits][Unused: 4 bits][Immediate/Addr: 16 bits]
    """
    mnemonic: str
    rd: Optional[str] = None
    rs1: Optional[str] = None
    rs2: Optional[str] = None
    imm: int = 0
    raw_assembly: str = ""
    address: int = 0

    def encode(self) -> int:
        opcode_num = OPCODES.get(self.mnemonic.upper(), 0) & 0x3F
        rd_num = REGISTERS.get(self.rd, 0) & 0x03 if self.rd else 0
        rs1_num = REGISTERS.get(self.rs1, 0) & 0x03 if self.rs1 else 0
        rs2_num = REGISTERS.get(self.rs2, 0) & 0x03 if self.rs2 else 0
        imm_num = self.imm & 0xFFFF

        word = (opcode_num << 26) | (rd_num << 24) | (rs1_num << 22) | (rs2_num << 20) | imm_num
        return word

    @staticmethod
    def decode(word: int, address: int = 0) -> "Instruction":
        opcode_num = (word >> 26) & 0x3F
        rd_num = (word >> 24) & 0x03
        rs1_num = (word >> 22) & 0x03
        rs2_num = (word >> 20) & 0x03
        imm_num = word & 0xFFFF
        # Sign-extend 16-bit immediate if needed
        if imm_num & 0x8000:
            imm_num -= 0x10000

        mnemonic = OPCODE_INV.get(opcode_num, "UNKNOWN")
        rd = REG_INV.get(rd_num, "R0")
        rs1 = REG_INV.get(rs1_num, "R0")
        rs2 = REG_INV.get(rs2_num, "R0")

        return Instruction(
            mnemonic=mnemonic,
            rd=rd,
            rs1=rs1,
            rs2=rs2,
            imm=imm_num,
            raw_assembly=f"{mnemonic} {rd}, {rs1}, {rs2}, {imm_num}",
            address=address
        )

    def to_hex(self) -> str:
        return f"0x{self.encode():08X}"

    def to_binary(self) -> str:
        val = self.encode()
        b = f"{val:032b}"
        return f"{b[0:6]} {b[6:8]} {b[8:10]} {b[10:12]} {b[12:16]} {b[16:32]}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "mnemonic": self.mnemonic,
            "rd": self.rd,
            "rs1": self.rs1,
            "rs2": self.rs2,
            "imm": self.imm,
            "hex": self.to_hex(),
            "binary": self.to_binary(),
            "assembly": self.raw_assembly
        }
