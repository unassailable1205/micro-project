"""
DAA Module: Algorithmic Complexity Analyzer
Performs static analysis of Abstract Syntax Trees (AST) to derive
Time Complexity, Space Complexity, and Recurrence Relations.
"""

from typing import Dict, Any, List, Optional
from ..flat.ast_nodes import (
    Program, VarDecl, Assignment, BinaryOp, UnaryOp,
    Literal, Identifier, IfStatement, WhileStatement,
    PrintStatement, DncStatement, ASTNode
)
from .master_theorem import MasterTheoremSolver


class ComplexityAnalyzer:
    def __init__(self):
        self.max_loop_depth = 0
        self.current_loop_depth = 0
        self.loop_steps: List[str] = []
        self.dnc_operations: List[Dict[str, Any]] = []
        self.var_count = 0
        self.statement_counts: Dict[str, int] = {
            "VarDecl": 0,
            "Assignment": 0,
            "IfStatement": 0,
            "WhileStatement": 0,
            "PrintStatement": 0,
            "DncStatement": 0,
        }

    def analyze(self, program: Program) -> Dict[str, Any]:
        self.max_loop_depth = 0
        self.current_loop_depth = 0
        self.loop_steps.clear()
        self.dnc_operations.clear()
        self.var_count = 0
        for k in self.statement_counts:
            self.statement_counts[k] = 0

        for stmt in program.statements:
            self._visit(stmt)

        # Compute asymptotic time complexity
        time_complexity, time_explanation = self._derive_time_complexity()
        space_complexity, space_explanation = self._derive_space_complexity()

        return {
            "time_complexity": time_complexity,
            "time_explanation": time_explanation,
            "space_complexity": space_complexity,
            "space_explanation": space_explanation,
            "max_loop_depth": self.max_loop_depth,
            "variables_allocated": self.var_count,
            "statement_counts": self.statement_counts,
            "dnc_operations": self.dnc_operations,
        }

    def _visit(self, node: ASTNode):
        node_name = node.__class__.__name__
        if node_name in self.statement_counts:
            self.statement_counts[node_name] += 1

        if isinstance(node, VarDecl):
            self.var_count += 1

        elif isinstance(node, WhileStatement):
            self.current_loop_depth += 1
            if self.current_loop_depth > self.max_loop_depth:
                self.max_loop_depth = self.current_loop_depth
            
            # Analyze step increment (additive vs multiplicative)
            step_type = self._detect_loop_step(node)
            self.loop_steps.append(step_type)

            for s in node.body:
                self._visit(s)
            self.current_loop_depth -= 1

        elif isinstance(node, IfStatement):
            for s in node.then_branch:
                self._visit(s)
            for s in node.else_branch:
                self._visit(s)

        elif isinstance(node, DncStatement):
            meta = self._get_dnc_metadata(node.algorithm)
            self.dnc_operations.append(meta)

    def _detect_loop_step(self, while_node: WhileStatement) -> str:
        """
        Inspects body for step patterns like i = i * 2 or i = i / 2 (logarithmic)
        vs i = i + 1 (linear).
        """
        for stmt in while_node.body:
            if isinstance(stmt, Assignment) and isinstance(stmt.expr, BinaryOp):
                if stmt.expr.op in ("*", "/"):
                    return "LOGARITHMIC"
                elif stmt.expr.op in ("+", "-"):
                    return "LINEAR"
        return "LINEAR"

    def _get_dnc_metadata(self, algo: str) -> Dict[str, Any]:
        if algo == "fastpow":
            mt = MasterTheoremSolver.solve(a=1, b=2, k=0, p=0)
            return {
                "algorithm": "Fast Exponentiation (Binary Exponentiation)",
                "recurrence": "T(n) = T(n / 2) + Θ(1)",
                "a": 1, "b": 2, "k": 0, "p": 0,
                "complexity": "O(log n)",
                "master_theorem": mt
            }
        elif algo == "karatsuba":
            mt = MasterTheoremSolver.solve(a=3, b=2, k=1, p=0)
            return {
                "algorithm": "Karatsuba Integer Multiplication",
                "recurrence": "T(n) = 3 * T(n / 2) + Θ(n)",
                "a": 3, "b": 2, "k": 1, "p": 0,
                "complexity": "O(n^1.585)",
                "master_theorem": mt
            }
        elif algo == "binsearch":
            mt = MasterTheoremSolver.solve(a=1, b=2, k=0, p=0)
            return {
                "algorithm": "Divide-and-Conquer Binary Search",
                "recurrence": "T(n) = T(n / 2) + Θ(1)",
                "a": 1, "b": 2, "k": 0, "p": 0,
                "complexity": "O(log n)",
                "master_theorem": mt
            }
        elif algo == "minmax":
            mt = MasterTheoremSolver.solve(a=2, b=2, k=0, p=0)
            return {
                "algorithm": "Divide-and-Conquer Min-Max",
                "recurrence": "T(n) = 2 * T(n / 2) + 2",
                "a": 2, "b": 2, "k": 0, "p": 0,
                "complexity": "O(n) [3n/2 - 2 comparisons]",
                "master_theorem": mt
            }
        return {
            "algorithm": algo,
            "recurrence": "T(n) = a * T(n/b) + f(n)",
            "complexity": "O(n log n)"
        }

    def _derive_time_complexity(self) -> (str, str):
        if self.dnc_operations:
            dominant = self.dnc_operations[0]
            return dominant["complexity"], f"Dominated by divide-and-conquer operation '{dominant['algorithm']}' with recurrence {dominant['recurrence']}."

        if self.max_loop_depth == 0:
            return "O(1)", "Program contains sequential instructions and conditionals with constant execution paths."
        elif self.max_loop_depth == 1:
            if "LOGARITHMIC" in self.loop_steps:
                return "O(log n)", "Single loop whose loop control variable changes by multiplicative factors (halving or doubling)."
            return "O(n)", "Single linear loop iterating proportional to input scale n."
        elif self.max_loop_depth == 2:
            return "O(n^2)", "Two nested loops detected resulting in quadratic iterations."
        else:
            return f"O(n^{self.max_loop_depth})", f"{self.max_loop_depth} nested loops detected resulting in polynomial time bounds."

    def _derive_space_complexity(self) -> (str, str):
        if self.dnc_operations:
            algo = self.dnc_operations[0]["algorithm"]
            if "Karatsuba" in algo:
                return "O(n)", "Divide-and-conquer recursion stack depth O(log n) with intermediate digit buffers O(n)."
            return "O(log n)", "Call stack depth proportional to recursion tree height O(log n)."

        return "O(1)", f"Static auxiliary memory with {self.var_count} scalar variables allocated in RAM data segment."
