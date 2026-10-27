"""
COA Module: Central Processing Unit (CPU) Simulator
Simulates a multi-cycle RISC processor with explicit registers, status flags,
buses, and cycle-by-cycle / micro-operation stepping.
"""

from typing import Dict, Any, List, Optional
from .isa import Instruction, REGISTERS, OPCODES
from .memory import Memory
from .micro_ops import MicroOpStage, describe_micro_op


class CPU:
    def __init__(self, memory: Optional[Memory] = None):
        self.memory = memory if memory is not None else Memory()
        
        # General Purpose Registers (32-bit signed integers)
        self.registers: Dict[str, int] = {
            "R0": 0,
            "R1": 0,
            "R2": 0,
            "R3": 0,
        }
        
        # Special Purpose Registers
        self.pc: int = 0          # Program Counter
        self.ir: Optional[Instruction] = None  # Instruction Register
        self.mar: int = 0         # Memory Address Register
        self.mdr: int = 0         # Memory Data Register
        self.sp: int = 255        # Stack Pointer
        
        # Status / Condition Flags
        self.flags: Dict[str, int] = {
            "ZF": 0,  # Zero Flag
            "SF": 0,  # Sign Flag
            "CF": 0,  # Carry Flag
            "OF": 0,  # Overflow Flag
        }

        # Internal Execution Latches
        self._alu_result: int = 0
        self._jump_target: Optional[int] = None

        # Simulation Lifecycle
        self.halted: bool = False
        self.clock_cycles: int = 0
        self.instruction_count: int = 0
        self.current_t_index: int = 0  # 0 to 6 (T0 to T6)
        
        # Output Console Buffer
        self.stdout: List[str] = []
        self.trace_log: List[Dict[str, Any]] = []

    def reset(self):
        for reg in self.registers:
            self.registers[reg] = 0
        self.pc = 0
        self.ir = None
        self.mar = 0
        self.mdr = 0
        self.sp = 255
        for f in self.flags:
            self.flags[f] = 0
        self._alu_result = 0
        self._jump_target = None
        self.halted = False
        self.clock_cycles = 0
        self.instruction_count = 0
        self.current_t_index = 0
        self.stdout.clear()
        self.trace_log.clear()

    def update_flags(self, result: int):
        val = result & 0xFFFFFFFF
        self.flags["ZF"] = 1 if (val == 0) else 0
        self.flags["SF"] = 1 if ((val & 0x80000000) != 0) else 0
        self.flags["CF"] = 1 if (result > 0xFFFFFFFF or result < 0) else 0

    def step_micro_op(self) -> Dict[str, Any]:
        """
        Executes a single T-state micro-operation (T0 -> T1 -> ... -> T6).
        Returns the micro-operation report and new CPU state.
        """
        if self.halted:
            return {"halted": True, "message": "CPU is halted"}

        stage = MicroOpStage.ORDER[self.current_t_index]
        self.clock_cycles += 1

        # Execute micro-operation based on current T-state
        if stage == MicroOpStage.T0_FETCH_MAR:
            # T0: MAR <- PC
            self.mar = self.pc

        elif stage == MicroOpStage.T1_FETCH_MDR:
            # T1: MDR <- M[MAR], PC <- PC + 1
            instr = self.memory.read_instruction(self.mar)
            self.mdr = self.memory.read(self.mar)
            self._current_fetched_instr = instr
            self.pc += 1

        elif stage == MicroOpStage.T2_FETCH_IR:
            # T2: IR <- MDR
            self.ir = getattr(self, "_current_fetched_instr", None)
            if self.ir is None and self.mdr != 0:
                self.ir = Instruction.decode(self.mdr, address=self.mar)

        elif stage == MicroOpStage.T3_DECODE:
            # T3: Control Unit Decodes Opcode
            if self.ir is None or self.ir.mnemonic == "HALT":
                self.halted = True

        elif stage == MicroOpStage.T4_EXECUTE:
            # T4: ALU Computation / Condition Evaluation
            if self.ir:
                self._execute_alu()

        elif stage == MicroOpStage.T5_MEMORY:
            # T5: Memory Read / Write
            if self.ir:
                self._execute_memory()

        elif stage == MicroOpStage.T6_WRITEBACK:
            # T6: Register Writeback & PC update if branch
            if self.ir:
                self._execute_writeback()
            self.instruction_count += 1

        # Produce micro-op log info
        state_dict = self.get_state()
        op_info = describe_micro_op(stage, self.ir, state_dict)
        op_info["clock_cycle"] = self.clock_cycles
        op_info["instruction_count"] = self.instruction_count
        op_info["cpu_state"] = state_dict

        # Advance T-state index
        self.current_t_index = (self.current_t_index + 1) % len(MicroOpStage.ORDER)
        return op_info

    def _execute_alu(self):
        instr = self.ir
        if not instr:
            return
        m = instr.mnemonic
        r1_val = self.registers.get(instr.rs1, 0)
        r2_val = self.registers.get(instr.rs2, 0)
        imm_val = instr.imm

        self._jump_target = None

        if m == "LDI":
            self._alu_result = imm_val
        elif m == "MOV":
            self._alu_result = r1_val
        elif m == "ADD":
            self._alu_result = r1_val + r2_val
        elif m == "ADDI":
            self._alu_result = r1_val + imm_val
        elif m == "SUB":
            self._alu_result = r1_val - r2_val
        elif m == "SUBI":
            self._alu_result = r1_val - imm_val
        elif m == "MUL":
            self._alu_result = r1_val * r2_val
        elif m == "DIV":
            self._alu_result = r1_val // r2_val if r2_val != 0 else 0
        elif m == "MOD":
            self._alu_result = r1_val % r2_val if r2_val != 0 else 0
        elif m == "AND":
            self._alu_result = r1_val & r2_val
        elif m == "OR":
            self._alu_result = r1_val | r2_val
        elif m == "XOR":
            self._alu_result = r1_val ^ r2_val
        elif m == "CMP":
            diff = r1_val - r2_val
            self.update_flags(diff)
            self._alu_result = diff
        elif m == "CMPI":
            diff = r1_val - imm_val
            self.update_flags(diff)
            self._alu_result = diff
        elif m == "JMP":
            self._jump_target = imm_val
        elif m == "JZ" and self.flags["ZF"] == 1:
            self._jump_target = imm_val
        elif m == "JNZ" and self.flags["ZF"] == 0:
            self._jump_target = imm_val
        elif m == "JGT" and self.flags["ZF"] == 0 and self.flags["SF"] == 0:
            self._jump_target = imm_val
        elif m == "JLT" and self.flags["SF"] == 1:
            self._jump_target = imm_val
        elif m == "PRINT":
            val = self.registers.get(instr.rs1, 0)
            self.stdout.append(f"[OUT]: {val}")

    def _execute_memory(self):
        instr = self.ir
        if not instr:
            return
        if instr.mnemonic == "LOAD":
            addr = instr.imm
            self.mar = addr
            self.mdr = self.memory.read(addr)
            self._alu_result = self.mdr
        elif instr.mnemonic == "STORE":
            addr = instr.imm
            rs_val = self.registers.get(instr.rs1, 0)
            self.mar = addr
            self.mdr = rs_val
            self.memory.write(addr, rs_val)

    def _execute_writeback(self):
        instr = self.ir
        if not instr:
            return
        m = instr.mnemonic

        # Register writeback
        if m in ("LDI", "MOV", "ADD", "ADDI", "SUB", "SUBI", "MUL", "DIV", "MOD", "AND", "OR", "XOR", "LOAD"):
            if instr.rd in self.registers:
                self.registers[instr.rd] = self._alu_result
                self.update_flags(self._alu_result)

        # Branch resolution
        if self._jump_target is not None:
            self.pc = self._jump_target

        if m == "HALT":
            self.halted = True

    def step_instruction(self) -> Dict[str, Any]:
        """
        Steps through micro-operations until the current instruction cycle completes (T6 finishes).
        """
        if self.halted:
            return {"halted": True, "message": "CPU is halted"}

        trace = []
        while True:
            micro_res = self.step_micro_op()
            trace.append(micro_res)
            # When current_t_index returns to 0, instruction is fully executed
            if self.current_t_index == 0 or self.halted:
                break

        return {
            "halted": self.halted,
            "instruction": self.ir.raw_assembly if self.ir else "NOP",
            "micro_trace": trace,
            "cpu_state": self.get_state()
        }

    def run(self, max_instructions: int = 1000) -> Dict[str, Any]:
        """
        Runs the simulation until HALT or max instructions reached.
        """
        steps = []
        while not self.halted and self.instruction_count < max_instructions:
            step_res = self.step_instruction()
            steps.append(step_res)

        return {
            "halted": self.halted,
            "total_instructions": self.instruction_count,
            "total_clock_cycles": self.clock_cycles,
            "stdout": self.stdout,
            "final_state": self.get_state(),
            "step_count": len(steps)
        }

    def get_state(self) -> Dict[str, Any]:
        return {
            "registers": dict(self.registers),
            "PC": self.pc,
            "IR": self.ir.raw_assembly if self.ir else "NOP",
            "MAR": self.mar,
            "MDR": self.mdr,
            "SP": self.sp,
            "flags": dict(self.flags),
            "current_t_state": MicroOpStage.ORDER[self.current_t_index],
            "halted": self.halted,
            "clock_cycles": self.clock_cycles,
            "instruction_count": self.instruction_count,
            "stdout": list(self.stdout),
            "memory_reads": self.memory.read_count,
            "memory_writes": self.memory.write_count,
        }
