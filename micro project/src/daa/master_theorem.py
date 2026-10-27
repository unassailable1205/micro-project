"""
DAA Module: Master Theorem Recurrence Solver
Solves recurrences of the form:
    T(n) = a * T(n / b) + f(n)
where f(n) = Theta(n^k * log^p(n))
"""

import math
from typing import Dict, Any


class MasterTheoremSolver:
    @staticmethod
    def solve(a: float, b: float, k: float = 0.0, p: float = 0.0) -> Dict[str, Any]:
        """
        Solves T(n) = a*T(n/b) + Theta(n^k * log^p n)
        Returns detailed case analysis, critical exponent, and asymptotic bound.
        """
        if a < 1:
            return {"error": "Parameter 'a' must be >= 1 (number of subproblems)."}
        if b <= 1:
            return {"error": "Parameter 'b' must be > 1 (subproblem reduction factor)."}
        if k < 0:
            return {"error": "Parameter 'k' must be >= 0."}

        # Calculate critical exponent: c_crit = log_b(a)
        c_crit = math.log(a) / math.log(b)
        c_crit_rounded = round(c_crit, 4)

        diff = k - c_crit
        tolerance = 1e-6

        steps = [
            f"Given Recurrence: T(n) = {a} * T(n / {b}) + Θ(n^{k} * log^{p}(n))",
            f"Parameters: a = {a}, b = {b}, k = {k}, p = {p}",
            f"Critical Exponent: log_{b}({a}) = {c_crit_rounded}",
            f"Comparison: k = {k} vs log_b(a) = {c_crit_rounded}"
        ]

        if diff < -tolerance:
            # Case 1: k < log_b(a)
            case = 1
            bound = f"Θ(n^{c_crit_rounded})"
            explanation = (
                f"Since k ({k}) < log_{b}({a}) ({c_crit_rounded}), the work is dominated by leaves of the recursion tree. "
                f"By Master Theorem Case 1: T(n) = Θ(n^(log_{b} {a})) = {bound}."
            )
            steps.append("Result: Case 1 applies (leaf-heavy recurrence).")

        elif abs(diff) <= tolerance:
            # Case 2: k == log_b(a)
            case = 2
            if p > -1:
                p_next = p + 1
                p_str = f" * log^{p_next}(n)" if p_next != 1 else " * log(n)"
                p_str = "" if p_next == 0 else p_str
                bound = f"Θ(n^{k}{p_str})"
                explanation = (
                    f"Since k ({k}) = log_{b}({a}) ({c_crit_rounded}) and p ({p}) > -1, work is evenly balanced across levels. "
                    f"By Master Theorem Case 2a: T(n) = Θ(n^k * log^(p+1)(n)) = {bound}."
                )
            elif abs(p - (-1)) <= tolerance:
                bound = f"Θ(n^{k} * log(log(n)))"
                explanation = (
                    f"Since k = log_{b}({a}) and p = -1, by Master Theorem Case 2b: "
                    f"T(n) = Θ(n^k * log(log(n))) = {bound}."
                )
            else:
                bound = f"Θ(n^{k})"
                explanation = (
                    f"Since k = log_{b}({a}) and p ({p}) < -1, by Master Theorem Case 2c: "
                    f"T(n) = Θ(n^{k}) = {bound}."
                )
            steps.append("Result: Case 2 applies (balanced recurrence across all tree levels).")

        else:
            # Case 3: k > log_b(a)
            case = 3
            p_str = f" * log^{p}(n)" if p > 0 else ""
            bound = f"Θ(n^{k}{p_str})"
            explanation = (
                f"Since k ({k}) > log_{b}({a}) ({c_crit_rounded}), the work is dominated by the root split/combine step. "
                f"Assuming regularity condition a*f(n/b) <= c*f(n) holds for c < 1. "
                f"By Master Theorem Case 3: T(n) = Θ(f(n)) = {bound}."
            )
            steps.append("Result: Case 3 applies (root-heavy recurrence).")

        return {
            "a": a,
            "b": b,
            "k": k,
            "p": p,
            "critical_exponent": c_crit_rounded,
            "case": case,
            "bound": bound,
            "explanation": explanation,
            "steps": steps
        }
