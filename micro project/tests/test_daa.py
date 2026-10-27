"""
DAA Module Unit Tests
Tests Complexity Analyzer, Master Theorem solver, and Divide-and-Conquer algorithms.
"""

import unittest
from src.flat.lexer import Lexer
from src.flat.parser import Parser
from src.daa.complexity_analyzer import ComplexityAnalyzer
from src.daa.master_theorem import MasterTheoremSolver
from src.daa.divide_and_conquer import DivideAndConquerEngine


class TestDaaModule(unittest.TestCase):
    def test_master_theorem_cases(self):
        # Case 1: Karatsuba T(n) = 3T(n/2) + O(n) => log2(3) ~ 1.585 > 1
        res1 = MasterTheoremSolver.solve(3, 2, 1, 0)
        self.assertEqual(res1["case"], 1)
        self.assertEqual(res1["bound"], "Θ(n^1.585)")

        # Case 2: Merge Sort T(n) = 2T(n/2) + O(n) => log2(2) = 1 == 1
        res2 = MasterTheoremSolver.solve(2, 2, 1, 0)
        self.assertEqual(res2["case"], 2)
        self.assertEqual(res2["bound"], "Θ(n^1 * log(n))")

        # Case 3: Root heavy T(n) = T(n/2) + O(n)
        res3 = MasterTheoremSolver.solve(1, 2, 1, 0)
        self.assertEqual(res3["case"], 3)
        self.assertEqual(res3["bound"], "Θ(n^1)")

    def test_complexity_analyzer(self):
        code_linear = """
        let sum = 0;
        let i = 0;
        while (i < 10) {
            sum = sum + i;
            i = i + 1;
        }
        """
        ast = Parser(Lexer(code_linear).tokenize()).parse()
        res = ComplexityAnalyzer().analyze(ast)
        self.assertEqual(res["time_complexity"], "O(n)")
        self.assertEqual(res["max_loop_depth"], 1)

    def test_fastpow_dnc(self):
        res = DivideAndConquerEngine.run_fast_pow(2, 8)
        self.assertEqual(res["result"], 256)
        self.assertEqual(res["asymptotic_time"], "O(log n)")
        self.assertIn("benchmark", res)
        self.assertGreater(res["benchmark"]["divide_and_conquer"]["clock_cycles"], 0)

    def test_karatsuba_dnc(self):
        res = DivideAndConquerEngine.run_karatsuba(42, 18)
        self.assertEqual(res["result"], 42 * 18)
        self.assertEqual(res["asymptotic_time"], "O(n^1.585)")

    def test_binary_search_dnc(self):
        arr = [1, 3, 5, 7, 9, 11, 13, 15]
        res = DivideAndConquerEngine.run_binary_search(arr, 7)
        self.assertEqual(res["result"], 3)
        self.assertEqual(res["asymptotic_time"], "O(log n)")


if __name__ == "__main__":
    unittest.main()
