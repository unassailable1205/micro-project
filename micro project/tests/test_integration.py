"""
Integration Unit Tests
Tests the full pipeline: Source Code -> FLAT Lexer/Parser -> DAA Complexity -> COA Compiler -> Assembler -> CPU Execution.
"""

import unittest
from src.flat.lexer import Lexer
from src.flat.parser import Parser
from src.compiler.compiler import Compiler
from src.coa.assembler import Assembler
from src.coa.cpu import CPU
from src.daa.complexity_analyzer import ComplexityAnalyzer


class TestIntegrationPipeline(unittest.TestCase):
    def test_full_pipeline_arithmetic(self):
        source = """
        let a = 10;
        let b = 25;
        let c = a + b * 2;
        print(c);
        """
        # 1. FLAT
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()

        # 2. DAA
        comp = ComplexityAnalyzer().analyze(ast)
        self.assertEqual(comp["time_complexity"], "O(1)")

        # 3. COA
        cpu = CPU()
        compiler = Compiler(cpu.memory)
        asm_code = compiler.compile(ast)

        assembler = Assembler(cpu.memory)
        assembler.assemble(asm_code)
        sim_res = cpu.run()

        self.assertTrue(sim_res["halted"])
        # c = 10 + 25 * 2 = 60
        self.assertEqual(sim_res["stdout"], ["[OUT]: 60"])

    def test_full_pipeline_loop(self):
        source = """
        let n = 5;
        let fact = 1;
        let i = 1;
        while (i <= n) {
            fact = fact * i;
            i = i + 1;
        }
        print(fact);
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()

        cpu = CPU()
        compiler = Compiler(cpu.memory)
        asm_code = compiler.compile(ast)

        assembler = Assembler(cpu.memory)
        assembler.assemble(asm_code)
        sim_res = cpu.run()

        self.assertTrue(sim_res["halted"])
        # 5! = 120
        self.assertEqual(sim_res["stdout"], ["[OUT]: 120"])


if __name__ == "__main__":
    unittest.main()
