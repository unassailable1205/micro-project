"""
CLI Module: Command-Line Interface for Smart Code Analyzer and Execution Simulator
Allows analyzing source files, compiling, and running CPU simulations directly in terminal.
"""

import argparse
import sys
import os
import json

from src.flat.lexer import Lexer
from src.flat.parser import Parser
from src.compiler.compiler import Compiler
from src.coa.assembler import Assembler
from src.coa.cpu import CPU
from src.daa.complexity_analyzer import ComplexityAnalyzer
from src.daa.master_theorem import MasterTheoremSolver
from src.daa.divide_and_conquer import DivideAndConquerEngine


def analyze_and_run(code: str, verbose: bool = False, step_interactive: bool = False):
    print("=" * 60)
    print("🔍 SMART CODE ANALYZER & CPU SIMULATOR (CLI)")
    print("=" * 60)

    # 1. FLAT Lexer
    print("\n[1] FLAT: Lexical Analysis (DFA Tokenizer)...")
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    print(f"  ✓ Recognized {len(tokens)-1} tokens via DFA state transitions.")
    if verbose:
        for t in tokens:
            if t.type != "EOF":
                print(f"    - {t.type:<12} '{t.value}' (line {t.line}, col {t.column})")

    # 2. FLAT Parser (AST)
    print("\n[2] FLAT: Syntax Analysis (Context-Free Grammar & AST)...")
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"  ✓ Syntax Validated. AST generated with {len(ast.statements)} statements.")

    # 3. DAA Complexity Analyzer
    print("\n[3] DAA: Algorithmic Complexity Derivation...")
    analyzer = ComplexityAnalyzer()
    complexity = analyzer.analyze(ast)
    print(f"  ✓ Time Complexity:  {complexity['time_complexity']}")
    print(f"    Reasoning:        {complexity['time_explanation']}")
    print(f"  ✓ Space Complexity: {complexity['space_complexity']}")
    print(f"    Reasoning:        {complexity['space_explanation']}")
    print(f"  ✓ Max Loop Depth:   {complexity['max_loop_depth']}")

    # 4. COA Compiler & Assembler
    print("\n[4] COA: Code Generation & Assembly Translation...")
    cpu = CPU()
    compiler = Compiler(cpu.memory)
    asm_code = compiler.compile(ast)
    print("  ✓ Assembly Generated:")
    for line in asm_code.strip().split("\n"):
        print(f"      {line}")

    assembler = Assembler(cpu.memory)
    instructions = assembler.assemble(asm_code)
    print(f"  ✓ Assembled {len(instructions)} machine words into RAM.")

    # 5. COA CPU Simulation
    print("\n[5] COA: Multi-Cycle CPU Instruction Execution...")
    if step_interactive:
        print("  Entering Interactive Cycle Stepper (press ENTER for next micro-op, 'q' to finish)...")
        while not cpu.halted:
            res = cpu.step_micro_op()
            print(f"    Cycle {res['clock_cycle']:<3} [{res['t_state']}]: {res['rtl']}")
            print(f"      Regs: {cpu.registers} | PC: 0x{cpu.pc:02X} | Flags: {cpu.flags}")
            user_in = input("    [Enter=Next, c=continue, q=quit]: ").strip().lower()
            if user_in == 'q':
                break
            elif user_in == 'c':
                step_interactive = False
    
    sim_res = cpu.run()
    print("\n" + "=" * 60)
    print("📊 EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  • CPU Status:           {'HALTED' if sim_res['halted'] else 'RUNNING'}")
    print(f"  • Instructions Executed: {sim_res['total_instructions']}")
    print(f"  • Clock Cycles:         {sim_res['total_clock_cycles']}")
    print(f"  • General Registers:    {sim_res['final_state']['registers']}")
    print(f"  • Status Flags:         {sim_res['final_state']['flags']}")
    print(f"  • Output Stream:")
    if sim_res['stdout']:
        for out in sim_res['stdout']:
            print(f"      {out}")
    else:
        print("      (No print output produced)")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Smart Code Analyzer and Execution Simulator CLI")
    parser.add_argument("--file", "-f", type=str, help="Path to source code file")
    parser.add_argument("--eval", "-e", type=str, help="Evaluate source code string inline")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose token and instruction details")
    parser.add_argument("--step", "-s", action="store_true", help="Interactive T-state micro-op stepping")
    parser.add_argument("--solve-master", action="store_true", help="Solve Master Theorem recurrence")
    parser.add_argument("-a", type=float, default=3, help="Master Theorem: number of subproblems")
    parser.add_argument("-b", type=float, default=2, help="Master Theorem: reduction factor")
    parser.add_argument("-k", type=float, default=1, help="Master Theorem: polynomial work exponent")
    parser.add_argument("-p", type=float, default=0, help="Master Theorem: log factor exponent")
    parser.add_argument("--dnc", choices=["fastpow", "karatsuba", "binsearch"], help="Run divide-and-conquer algorithm benchmark")

    args = parser.parse_args()

    if args.solve_master:
        res = MasterTheoremSolver.solve(args.a, args.b, args.k, args.p)
        print("\n" + "=" * 50)
        print("MASTER THEOREM RECURRENCE SOLVER")
        print("=" * 50)
        print(f"Formula: T(n) = {args.a} * T(n/{args.b}) + Θ(n^{args.k} log^{args.p} n)")
        print(f"Critical Exponent log_b(a): {res['critical_exponent']}")
        print(f"Applicable Case: Case {res['case']}")
        print(f"Asymptotic Bound: {res['bound']}")
        print(f"Explanation:\n  {res['explanation']}")
        print("=" * 50)
        return

    if args.dnc:
        print("\n" + "=" * 50)
        print(f"DIVIDE & CONQUER ENGINE: {args.dnc.upper()}")
        print("=" * 50)
        if args.dnc == "fastpow":
            res = DivideAndConquerEngine.run_fast_pow(2, 10)
        elif args.dnc == "karatsuba":
            res = DivideAndConquerEngine.run_karatsuba(42, 18)
        elif args.dnc == "binsearch":
            res = DivideAndConquerEngine.run_binary_search([2, 5, 8, 12, 16, 23, 38, 45, 56], 23)

        print(f"Algorithm:       {res['algorithm']}")
        print(f"Recurrence:      {res['recurrence']}")
        print(f"Time Complexity: {res['asymptotic_time']}")
        print(f"Result:          {res['result']}")
        bm = res['benchmark']
        print("\nHARDWARE CPU BENCHMARK:")
        print(f"  Naive: {bm['naive']['algorithm']} -> {bm['naive']['clock_cycles']} cycles")
        print(f"  D&C:   {bm['divide_and_conquer']['algorithm']} -> {bm['divide_and_conquer']['clock_cycles']} cycles")
        print(f"  Speedup Factor: {bm['speedup_factor']} ({bm['cycle_reduction_percent']} cycle reduction)")
        print("=" * 50)
        return

    code = None
    if args.file:
        with open(args.file, "r") as f:
            code = f.read()
    elif args.eval:
        code = args.eval
    else:
        # Default sample code
        code = """// Default Sample: While Loop Sum
let sum = 0;
let i = 1;
while (i <= 5) {
    sum = sum + i;
    i = i + 1;
}
print(sum);
"""

    analyze_and_run(code, verbose=args.verbose, step_interactive=args.step)


if __name__ == "__main__":
    main()
