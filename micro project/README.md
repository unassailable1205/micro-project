# Smart Code Analyzer & Execution Simulator

> A comprehensive, interdisciplinary educational computer science tool bridging **FLAT (Formal Languages & Automata Theory)**, **COA (Computer Organization & Architecture)**, and **DAA (Design & Analysis of Algorithms)**.

Built with **Zero External Dependencies** (pure Python 3.11+ standard library). Runs anywhere immediately without `pip install` friction.

---

## 🌟 Core Computer Science Pillars

| Discipline | Modules Covered | Implemented Capabilities |
| :--- | :--- | :--- |
| **FLAT (M1 / M2)** | **Finite Automata & Regular Expressions** | • Custom Deterministic Finite Automata (DFA) engine.<br>• Character-by-character state transition tracking and matrix visualizer.<br>• Tokenization of Identifiers, Numbers (integers & floats), Operators, and Keywords.<br>• Context-Free Grammar (CFG) recursive-descent parser producing Abstract Syntax Trees (AST).<br>• Regular expression pattern matching for statement signatures. |
| **COA (M1 / M2)** | **CPU Architecture & Instruction Execution Cycle** | • Educational 32-bit RISC Instruction Set Architecture (ISA).<br>• Registers: General-Purpose `R0` (ACC), `R1`, `R2`, `R3`; Special-Purpose `PC`, `IR`, `MAR`, `MDR`, `SP`.<br>• Status Flags: Zero (`ZF`), Sign (`SF`), Carry (`CF`), Overflow (`OF`).<br>• 256-word addressable RAM (Code Segment `0-127`, Data Segment `128-255`).<br>• Sub-cycle **7-stage micro-operations ($T_0 - T_6$)** stepping with Register Transfer Language (RTL) and datapath bus transfer indicators (Address, Data, Control buses). |
| **DAA (M1 / M2)** | **Complexity Analysis & Divide-and-Conquer** | • Static AST analysis calculating Asymptotic Time & Space Complexities ($O(1), O(\log n), O(n), O(n^2)$).<br>• **Master Theorem Recurrence Solver**: solves $T(n) = aT(n/b) + \Theta(n^k \log^p n)$ across Cases 1, 2, and 3 with formal mathematical proofs.<br>• **Divide-and-Conquer Engines**: Fast Exponentiation $O(\log n)$, Karatsuba Integer Multiplication $O(n^{1.585})$, Binary Search $O(\log n)$, and Min-Max.<br>• Interactive collapsible recursion tree visualizer.<br>• Hardware CPU Cycle Benchmark: side-by-side clock cycle and instruction count comparison between Naive and D&C algorithms on simulated CPU. |

---

## 🚀 Quick Start

### 1. Launch the Interactive Web Dashboard
```bash
python3 main.py
```
Open your browser to: **`http://localhost:8000`**

### 2. Run the Terminal Command-Line Interface (CLI)
```bash
# Analyze a sample file
python3 cli.py --file examples/02_while_loop.txt

# Inline evaluation with micro-op stepper
python3 cli.py --eval "let a = 12; let b = 8; print(a + b);" --verbose

# Solve Master Theorem recurrence
python3 cli.py --solve-master -a 3 -b 2 -k 1 -p 0

# Benchmark Divide-and-Conquer Fast Exponentiation
python3 cli.py --dnc fastpow
```

### 3. Run the Automated Unit Test Suite
```bash
python3 main.py --test
# or
python3 -m unittest discover tests
```

---

## 📐 Project Structure

```
micro project/
├── src/
│   ├── flat/
│   │   ├── dfa.py                  # Generic DFA engine & token automata builders
│   │   ├── regex.py                # Regex rules & statement pattern signatures
│   │   ├── lexer.py                # Tokenizer recording DFA transition trajectories
│   │   ├── ast_nodes.py            # AST node dataclasses
│   │   └── parser.py               # Recursive-descent CFG syntax parser
│   ├── coa/
│   │   ├── isa.py                  # 32-bit RISC ISA, opcodes, register encodings
│   │   ├── memory.py               # 256-word addressable RAM (Code & Data)
│   │   ├── cpu.py                  # Multi-cycle CPU simulator with registers & flags
│   │   ├── micro_ops.py            # T0-T6 micro-operations & RTL descriptions
│   │   └── assembler.py            # Two-pass assembler resolving labels
│   ├── daa/
│   │   ├── complexity_analyzer.py  # Static Big-O time and space complexity derivation
│   │   ├── master_theorem.py       # Master Theorem solver for recurrence relations
│   │   └── divide_and_conquer.py   # D&C engines, recursion trees & CPU benchmarks
│   ├── compiler/
│   │   └── compiler.py             # Translates high-level AST into COA Assembly
│   └── server.py                   # Zero-dependency HTTP REST API & static server
├── web/
│   ├── index.html                  # Modern responsive dashboard
│   ├── style.css                   # Dark theme, datapath & pipeline CSS
│   └── app.js                      # Interactive UI state, simulation & tree renderer
├── tests/
│   ├── test_flat.py                # DFA, lexer, and parser test cases
│   ├── test_coa.py                 # ISA, memory, CPU, and micro-op test cases
│   ├── test_daa.py                 # Complexity, Master Theorem, and D&C tests
│   └── test_integration.py         # Full end-to-end pipeline execution tests
├── examples/
│   ├── 01_arithmetic.txt           # Basic arithmetic & register operations
│   ├── 02_while_loop.txt           # While loop accumulator O(n)
│   ├── 03_if_else.txt              # Condition codes & status flag branching
│   ├── 04_fast_exponentiation.txt  # D&C FastPow O(log n)
│   └── 05_karatsuba.txt            # D&C Karatsuba multiplication O(n^1.585)
├── cli.py                          # Terminal CLI tool
├── main.py                         # Unified launcher
└── README.md
```

---

## 💻 Language Grammar & Statements

The tool accepts simple, clean statements:
- **Variable Declaration**: `let x = 10;`
- **Variable Assignment**: `x = x + 1;`
- **Arithmetic Expressions**: `+`, `-`, `*`, `/`, `%`, `^`, parentheses `(a + b) * c`
- **Relational Expressions**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Conditionals**: `if (x > 10) { ... } else { ... }`
- **Loops**: `while (i < n) { ... }`
- **Print Output**: `print(sum);`
- **Divide-and-Conquer Statement**:
  - `let res = dnc fastpow(base, exp);`
  - `let prod = dnc karatsuba(a, b);`
  - `let idx = dnc binsearch(target);`

---

## 🔬 COA Micro-Operations ($T_0 - T_6$) Breakdown

Every instruction is executed through 7 clock cycle T-states:
- **$T_0$ (Fetch)**: `MAR ← PC` (Address Bus asserts Program Counter).
- **$T_1$ (Fetch)**: `MDR ← M[MAR], PC ← PC + 1` (RAM word loaded into MDR; PC incremented).
- **$T_2$ (Fetch)**: `IR ← MDR` (Instruction loaded into Instruction Register).
- **$T_3$ (Decode)**: Control Unit decodes Opcode and resolves register operands.
- **$T_4$ (Execute)**: ALU computes arithmetic/logic result or evaluates branch condition.
- **$T_5$ (Memory)**: RAM accessed for `LOAD` or `STORE` instructions (idle for register-register).
- **$T_6$ (Writeback)**: Result written to destination register `Rd` and status flags updated (`ZF`, `SF`, `CF`, `OF`).
