"""
COA Module Unit Tests
Tests Instruction encoding/decoding, CPU registers, ALU operations, Memory,
Micro-operation T-states, and Assembler.
"""

import unittest
from src.coa.isa import Instruction, OPCODES, REGISTERS
from src.coa.memory import Memory
from src.coa.cpu import CPU
from src.coa.assembler import Assembler


class TestCoaModule(unittest.TestCase):
    def test_instruction_encode_decode(self):
        instr = Instruction(mnemonic="ADD", rd="R0", rs1="R1", rs2="R2", raw_assembly="ADD R0, R1, R2")
        word = instr.encode()
        decoded = Instruction.decode(word)
        self.assertEqual(decoded.mnemonic, "ADD")
        self.assertEqual(decoded.rd, "R0")
        self.assertEqual(decoded.rs1, "R1")
        self.assertEqual(decoded.rs2, "R2")

    def test_memory_read_write(self):
        mem = Memory()
        addr = mem.allocate_variable("counter", 42)
        self.assertEqual(mem.read(addr), 42)
        mem.write(addr, 99)
        self.assertEqual(mem.read(addr), 99)

    def test_assembler_and_cpu_execution(self):
        cpu = CPU()
        asm = Assembler(cpu.memory)
        code = """
        LDI R0, 15
        LDI R1, 25
        ADD R2, R0, R1
        PRINT R2
        HALT
        """
        asm.assemble(code)
        res = cpu.run()
        self.assertTrue(res["halted"])
        self.assertEqual(cpu.registers["R2"], 40)
        self.assertEqual(res["stdout"], ["[OUT]: 40"])

    def test_condition_flags(self):
        cpu = CPU()
        asm = Assembler(cpu.memory)
        # Test Zero Flag
        code = """
        LDI R0, 5
        LDI R1, 5
        CMP R0, R1
        HALT
        """
        asm.assemble(code)
        cpu.run()
        self.assertEqual(cpu.flags["ZF"], 1)
        self.assertEqual(cpu.flags["SF"], 0)

    def test_micro_operations_cycle(self):
        cpu = CPU()
        asm = Assembler(cpu.memory)
        asm.assemble("LDI R0, 10\nHALT")
        
        t0 = cpu.step_micro_op()
        self.assertEqual(t0["t_state"], "T0")
        self.assertEqual(t0["phase"], "FETCH")

        t1 = cpu.step_micro_op()
        self.assertEqual(t1["t_state"], "T1")

        t2 = cpu.step_micro_op()
        self.assertEqual(t2["t_state"], "T2")

        t3 = cpu.step_micro_op()
        self.assertEqual(t3["t_state"], "T3")
        self.assertEqual(t3["phase"], "DECODE")


if __name__ == "__main__":
    unittest.main()
