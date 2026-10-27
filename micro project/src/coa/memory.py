"""
COA Module: Main Memory (RAM) Model
Represents a 256-word addressable memory system divided into
Code Segment (0-127) and Data Segment (128-255).
"""

from typing import List, Dict, Any, Optional
from .isa import Instruction


class Memory:
    SIZE = 256
    DATA_SEGMENT_START = 128

    def __init__(self):
        # Memory array storing 32-bit values or instructions
        self.raw_cells: List[int] = [0] * self.SIZE
        self.instruction_cells: List[Optional[Instruction]] = [None] * self.SIZE
        self.labels: Dict[int, str] = {}
        self.symbol_table: Dict[str, int] = {}  # var_name -> memory_address
        self.read_count = 0
        self.write_count = 0

    def reset(self):
        self.raw_cells = [0] * self.SIZE
        self.instruction_cells = [None] * self.SIZE
        self.labels.clear()
        self.symbol_table.clear()
        self.read_count = 0
        self.write_count = 0

    def read(self, address: int) -> int:
        if not (0 <= address < self.SIZE):
            raise IndexError(f"Memory Access Violation: Address {address} out of bounds (0-{self.SIZE-1})")
        self.read_count += 1
        return self.raw_cells[address]

    def read_instruction(self, address: int) -> Optional[Instruction]:
        if not (0 <= address < self.SIZE):
            raise IndexError(f"Instruction Fetch Error: Address {address} out of bounds")
        self.read_count += 1
        return self.instruction_cells[address]

    def write(self, address: int, value: int):
        if not (0 <= address < self.SIZE):
            raise IndexError(f"Memory Write Violation: Address {address} out of bounds")
        self.write_count += 1
        self.raw_cells[address] = int(value)

    def write_instruction(self, address: int, instr: Instruction):
        if not (0 <= address < self.SIZE):
            raise IndexError(f"Instruction Store Error: Address {address} out of bounds")
        self.instruction_cells[address] = instr
        self.raw_cells[address] = instr.encode()

    def allocate_variable(self, name: str, initial_value: int = 0) -> int:
        if name in self.symbol_table:
            addr = self.symbol_table[name]
            self.write(addr, initial_value)
            return addr
        
        # Find next available data slot
        used_addrs = set(self.symbol_table.values())
        for addr in range(self.DATA_SEGMENT_START, self.SIZE):
            if addr not in used_addrs:
                self.symbol_table[name] = addr
                self.labels[addr] = name
                self.write(addr, initial_value)
                return addr
        raise MemoryError("Out of Data Memory space (Data Segment Full)")

    def get_dump(self, limit: int = 64) -> List[Dict[str, Any]]:
        """
        Returns a structured snapshot of memory cells for the UI.
        """
        snapshot = []
        for addr in range(self.SIZE):
            val = self.raw_cells[addr]
            instr = self.instruction_cells[addr]
            label = self.labels.get(addr, "")
            is_code = addr < self.DATA_SEGMENT_START
            if val != 0 or instr is not None or label != "" or addr < 16 or (128 <= addr < 136):
                snapshot.append({
                    "address": addr,
                    "hex_addr": f"0x{addr:02X}",
                    "value": val,
                    "hex_val": f"0x{val & 0xFFFFFFFF:08X}",
                    "label": label,
                    "segment": "CODE" if is_code else "DATA",
                    "instruction": instr.raw_assembly if instr else None
                })
        return snapshot
