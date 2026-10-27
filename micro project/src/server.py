"""
Server Module: Built-in HTTP REST API & Static File Server
Pure Python 3 standard library implementation with zero external dependencies.
"""

import http.server
import json
import os
import sys
import urllib.parse
from typing import Dict, Any, Optional

from .flat.lexer import Lexer, LexerError
from .flat.parser import Parser, ParserError
from .flat.dfa import build_identifier_dfa, build_number_dfa, build_operator_dfa
from .flat.regex import RegexPatternMatcher
from .compiler.compiler import Compiler
from .coa.assembler import Assembler, AssemblerError
from .coa.cpu import CPU
from .daa.complexity_analyzer import ComplexityAnalyzer
from .daa.master_theorem import MasterTheoremSolver
from .daa.divide_and_conquer import DivideAndConquerEngine


# Global Simulator Session State
class SimulationSession:
    def __init__(self):
        self.cpu = CPU()
        self.assembler = Assembler(self.cpu.memory)
        self.last_assembly: str = ""
        self.last_tokens = []
        self.last_ast = None
        self.last_analysis = {}

    def reset(self):
        self.cpu.reset()
        self.cpu.memory.reset()
        self.assembler = Assembler(self.cpu.memory)
        if self.last_assembly:
            self.assembler.assemble(self.last_assembly)


session = SimulationSession()

PRESET_PROGRAMS = [
    {
        "id": "arithmetic_basic",
        "title": "1. Basic Arithmetic & Variables",
        "category": "FLAT / COA Basics",
        "code": """// Basic Arithmetic and Register Operations
let a = 15;
let b = 25;
let sum = a + b;
let diff = b - a;
let product = a * 2;
print(sum);
print(diff);
print(product);
"""
    },
    {
        "id": "while_loop",
        "title": "2. While Loop & Accumulator (Sum 1 to 5)",
        "category": "Control Flow & Flags",
        "code": """// Computes sum of integers from 1 to 5
let n = 5;
let sum = 0;
let i = 1;

while (i <= n) {
    sum = sum + i;
    i = i + 1;
}

print(sum);
"""
    },
    {
        "id": "conditional_branch",
        "title": "3. If-Else Branching & Comparator",
        "category": "COA Condition Codes",
        "code": """// Evaluates condition and branches using CMP & Status Flags
let x = 40;
let threshold = 30;
let status = 0;

if (x > threshold) {
    status = 1;
    print(status);
} else {
    status = 0;
    print(status);
}
"""
    },
    {
        "id": "fast_power",
        "title": "4. Divide & Conquer: Fast Exponentiation O(log n)",
        "category": "DAA / Master Theorem",
        "code": """// Divide-and-Conquer Binary Exponentiation: 2^8
// Recurrence: T(n) = T(n/2) + O(1) => O(log n)
let base = 2;
let exp = 8;
let result = dnc fastpow(base, exp);
print(result);
"""
    },
    {
        "id": "karatsuba",
        "title": "5. Divide & Conquer: Karatsuba Multiplication O(n^1.585)",
        "category": "DAA Algorithms",
        "code": """// Divide-and-Conquer Karatsuba Multiplication: 42 * 18
// Recurrence: T(n) = 3*T(n/2) + O(n) => O(n^1.585)
let x = 42;
let y = 18;
let prod = dnc karatsuba(x, y);
print(prod);
"""
    },
    {
        "id": "bin_search",
        "title": "6. Divide & Conquer: Binary Search O(log n)",
        "category": "DAA Search",
        "code": """// Divide-and-Conquer Binary Search
// Recurrence: T(n) = T(n/2) + O(1) => O(log n)
let target = 42;
let index = dnc binsearch(target);
print(index);
"""
    }
]


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve files from the web directory
        self.web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/presets":
            self._send_json(200, {"presets": PRESET_PROGRAMS})
            return

        elif path == "/api/dfa/tables":
            tables = {
                "identifier": build_identifier_dfa().get_transition_table(),
                "number": build_number_dfa().get_transition_table(),
                "operator": build_operator_dfa().get_transition_table(),
            }
            self._send_json(200, tables)
            return

        elif path == "/api/regex/rules":
            rules = RegexPatternMatcher.get_token_rules()
            self._send_json(200, {"rules": rules})
            return

        # Serve static web frontend
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            req_json = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        try:
            if path == "/api/analyze":
                self._handle_analyze(req_json)
            elif path == "/api/cpu/step_micro":
                self._handle_cpu_step_micro()
            elif path == "/api/cpu/step_instruction":
                self._handle_cpu_step_instruction()
            elif path == "/api/cpu/run":
                self._handle_cpu_run(req_json)
            elif path == "/api/cpu/reset":
                self._handle_cpu_reset()
            elif path == "/api/daa/solve-master":
                self._handle_solve_master(req_json)
            elif path == "/api/daa/divide-and-conquer":
                self._handle_divide_and_conquer(req_json)
            else:
                self._send_json(404, {"error": f"Unknown endpoint '{path}'"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _handle_analyze(self, req: Dict[str, Any]):
        source = req.get("source_code", "")
        if not source.strip():
            self._send_json(400, {"error": "Source code cannot be empty"})
            return

        # 1. FLAT Lexer
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
        except LexerError as le:
            self._send_json(400, {"stage": "LEXER", "error": le.message, "line": le.line, "column": le.column})
            return

        # 2. FLAT Parser
        try:
            parser = Parser(tokens)
            ast = parser.parse()
        except ParserError as pe:
            self._send_json(400, {"stage": "PARSER", "error": pe.message, "line": pe.token.line, "column": pe.token.column})
            return

        # 3. DAA Complexity Analyzer
        complexity_analyzer = ComplexityAnalyzer()
        complexity_results = complexity_analyzer.analyze(ast)

        # 4. COA Compiler & Assembler
        session.reset()
        compiler = Compiler(session.cpu.memory)
        asm_code = compiler.compile(ast)
        session.last_assembly = asm_code

        try:
            instructions = session.assembler.assemble(asm_code)
        except AssemblerError as ae:
            self._send_json(400, {"stage": "ASSEMBLER", "error": ae.message, "line": ae.line_no})
            return

        session.last_tokens = tokens
        session.last_ast = ast
        session.last_analysis = complexity_results

        # Token serializable list
        token_dicts = [t.to_dict() for t in tokens if t.type != "EOF"]

        # Encoded instructions list
        encoded_instrs = [i.to_dict() for i in instructions]

        # Memory snapshot
        memory_dump = session.cpu.memory.get_dump()

        self._send_json(200, {
            "success": True,
            "flat": {
                "token_count": len(token_dicts),
                "tokens": token_dicts,
                "ast": ast.to_dict(),
            },
            "daa": complexity_results,
            "coa": {
                "assembly": asm_code,
                "instruction_count": len(instructions),
                "instructions": encoded_instrs,
                "cpu_state": session.cpu.get_state(),
                "memory_dump": memory_dump
            }
        })

    def _handle_cpu_step_micro(self):
        result = session.cpu.step_micro_op()
        result["memory_dump"] = session.cpu.memory.get_dump()
        self._send_json(200, result)

    def _handle_cpu_step_instruction(self):
        result = session.cpu.step_instruction()
        result["memory_dump"] = session.cpu.memory.get_dump()
        self._send_json(200, result)

    def _handle_cpu_run(self, req: Dict[str, Any]):
        max_instr = req.get("max_instructions", 1000)
        result = session.cpu.run(max_instructions=max_instr)
        result["memory_dump"] = session.cpu.memory.get_dump()
        self._send_json(200, result)

    def _handle_cpu_reset(self):
        session.reset()
        self._send_json(200, {
            "cpu_state": session.cpu.get_state(),
            "memory_dump": session.cpu.memory.get_dump()
        })

    def _handle_solve_master(self, req: Dict[str, Any]):
        a = float(req.get("a", 1))
        b = float(req.get("b", 2))
        k = float(req.get("k", 0))
        p = float(req.get("p", 0))
        res = MasterTheoremSolver.solve(a, b, k, p)
        self._send_json(200, res)

    def _handle_divide_and_conquer(self, req: Dict[str, Any]):
        algo = req.get("algorithm", "fastpow")
        params = req.get("params", {})

        if algo == "fastpow":
            base = int(params.get("base", 2))
            exp = int(params.get("exp", 8))
            res = DivideAndConquerEngine.run_fast_pow(base, exp)
        elif algo == "karatsuba":
            x = int(params.get("x", 42))
            y = int(params.get("y", 18))
            res = DivideAndConquerEngine.run_karatsuba(x, y)
        elif algo == "binsearch":
            arr = params.get("array", [2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91])
            target = int(params.get("target", 23))
            res = DivideAndConquerEngine.run_binary_search(arr, target)
        else:
            self._send_json(400, {"error": f"Unknown divide-and-conquer algorithm '{algo}'"})
            return

        self._send_json(200, res)


def run_server(port: int = 8000, host: str = "0.0.0.0"):
    server_address = (host, port)
    httpd = http.server.HTTPServer(server_address, RequestHandler)
    print(f"================================================================")
    print(f"🚀 Smart Code Analyzer & Execution Simulator Server Running!")
    print(f"🌐 Access Web Dashboard: http://localhost:{port}")
    print(f"📚 Modules Active: FLAT (M1/M2) | COA (M1/M2) | DAA (M1/M2)")
    print(f"================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()
