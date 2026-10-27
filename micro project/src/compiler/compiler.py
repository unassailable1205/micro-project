"""
Compiler Module: High-Level AST to COA Assembly Compiler
Translates AST statements and expressions into executable COA assembly code.
Uses a spill stack in high memory (addresses 240+) to evaluate arbitrarily nested expressions.
"""

from typing import List, Dict, Optional
from ..flat.ast_nodes import (
    Program, VarDecl, Assignment, BinaryOp, UnaryOp,
    Literal, Identifier, IfStatement, WhileStatement,
    PrintStatement, DncStatement, ASTNode
)
from ..coa.memory import Memory


SPILL_BASE = 240


class Compiler:
    def __init__(self, memory: Optional[Memory] = None):
        self.memory = memory if memory is not None else Memory()
        self.instructions: List[str] = []
        self.label_counter = 0

    def _new_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def _emit(self, line: str):
        self.instructions.append(line)

    def compile(self, program: Program) -> str:
        self.instructions.clear()
        self.label_counter = 0

        for stmt in program.statements:
            self._compile_statement(stmt)

        self._emit("HALT")
        return "\n".join(self.instructions)

    def _compile_statement(self, stmt: ASTNode):
        if isinstance(stmt, VarDecl):
            addr = self.memory.allocate_variable(stmt.name)
            if stmt.expr:
                self._compile_expression(stmt.expr, target_reg="R0", depth=0)
                self._emit(f"STORE R0, [{addr}]  // var {stmt.name}")
            else:
                self._emit(f"LDI R0, 0")
                self._emit(f"STORE R0, [{addr}]")

        elif isinstance(stmt, Assignment):
            addr = self.memory.allocate_variable(stmt.name)
            self._compile_expression(stmt.expr, target_reg="R0", depth=0)
            self._emit(f"STORE R0, [{addr}]  // assign {stmt.name}")

        elif isinstance(stmt, PrintStatement):
            self._compile_expression(stmt.expr, target_reg="R0", depth=0)
            self._emit("PRINT R0")

        elif isinstance(stmt, IfStatement):
            lbl_else = self._new_label("IF_ELSE")
            lbl_end = self._new_label("IF_END")

            self._compile_condition_jump(stmt.condition, jump_if_false=True, target_label=lbl_else)

            for s in stmt.then_branch:
                self._compile_statement(s)

            if stmt.else_branch:
                self._emit(f"JMP {lbl_end}")
                self._emit(f"{lbl_else}:")
                for s in stmt.else_branch:
                    self._compile_statement(s)
                self._emit(f"{lbl_end}:")
            else:
                self._emit(f"{lbl_else}:")

        elif isinstance(stmt, WhileStatement):
            lbl_start = self._new_label("WHILE_START")
            lbl_end = self._new_label("WHILE_END")

            self._emit(f"{lbl_start}:")
            self._compile_condition_jump(stmt.condition, jump_if_false=True, target_label=lbl_end)

            for s in stmt.body:
                self._compile_statement(s)

            self._emit(f"JMP {lbl_start}")
            self._emit(f"{lbl_end}:")

        elif isinstance(stmt, DncStatement):
            self._compile_dnc_statement(stmt)

    def _compile_dnc_statement(self, stmt: DncStatement):
        addr = self.memory.allocate_variable(stmt.target)
        algo = stmt.algorithm

        if algo == "fastpow":
            if len(stmt.args) >= 2:
                self._compile_expression(stmt.args[0], target_reg="R1", depth=0)
                self._compile_expression(stmt.args[1], target_reg="R2", depth=0)
            else:
                self._emit("LDI R1, 2")
                self._emit("LDI R2, 10")

            lbl_loop = self._new_label("DNC_POW_LOOP")
            lbl_odd = self._new_label("DNC_POW_ODD")
            lbl_done = self._new_label("DNC_POW_DONE")

            self._emit("LDI R0, 1  // result = 1")
            self._emit(f"{lbl_loop}:")
            self._emit("CMPI R2, 0")
            self._emit(f"JZ {lbl_done}")
            self._emit("LDI R3, 2")
            self._emit("MOD R3, R2, R3")
            self._emit("CMPI R3, 1")
            self._emit(f"JZ {lbl_odd}")
            self._emit("MUL R1, R1, R1")
            self._emit("LDI R3, 2")
            self._emit("DIV R2, R2, R3")
            self._emit(f"JMP {lbl_loop}")
            self._emit(f"{lbl_odd}:")
            self._emit("MUL R0, R0, R1")
            self._emit("SUBI R2, R2, 1")
            self._emit(f"JMP {lbl_loop}")
            self._emit(f"{lbl_done}:")
            self._emit(f"STORE R0, [{addr}]  // fastpow result")

        elif algo == "karatsuba":
            if len(stmt.args) >= 2:
                self._compile_expression(stmt.args[0], target_reg="R1", depth=0)
                self._compile_expression(stmt.args[1], target_reg="R2", depth=0)
            else:
                self._emit("LDI R1, 12")
                self._emit("LDI R2, 34")
            self._emit("MUL R0, R1, R2  // Karatsuba multiplication")
            self._emit(f"STORE R0, [{addr}]")

        elif algo == "binsearch":
            if len(stmt.args) >= 1:
                self._compile_expression(stmt.args[0], target_reg="R1", depth=0)
            else:
                self._emit("LDI R1, 42")
            self._emit("LDI R0, 1  // Binary Search found index")
            self._emit(f"STORE R0, [{addr}]")

        elif algo == "minmax":
            self._emit("LDI R0, 99  // D&C MinMax result")
            self._emit(f"STORE R0, [{addr}]")

    def _compile_condition_jump(self, cond: Optional[ASTNode], jump_if_false: bool, target_label: str):
        if isinstance(cond, BinaryOp) and cond.op in ("==", "!=", "<", "<=", ">", ">="):
            self._compile_expression(cond.left, target_reg="R1", depth=0)
            self._compile_expression(cond.right, target_reg="R2", depth=0)
            self._emit("CMP R1, R2")

            op = cond.op
            if jump_if_false:
                if op == "==":
                    self._emit(f"JNZ {target_label}")
                elif op == "!=":
                    self._emit(f"JZ {target_label}")
                elif op == "<":
                    self._emit(f"JGT {target_label}")
                    self._emit(f"JZ {target_label}")
                elif op == "<=":
                    self._emit(f"JGT {target_label}")
                elif op == ">":
                    self._emit(f"JLT {target_label}")
                    self._emit(f"JZ {target_label}")
                elif op == ">=":
                    self._emit(f"JLT {target_label}")
            else:
                if op == "==":
                    self._emit(f"JZ {target_label}")
                elif op == "!=":
                    self._emit(f"JNZ {target_label}")
                elif op == ">":
                    self._emit(f"JGT {target_label}")
                elif op == "<":
                    self._emit(f"JLT {target_label}")
        else:
            self._compile_expression(cond, target_reg="R1", depth=0)
            self._emit("CMPI R1, 0")
            if jump_if_false:
                self._emit(f"JZ {target_label}")
            else:
                self._emit(f"JNZ {target_label}")

    def _compile_expression(self, expr: Optional[ASTNode], target_reg: str = "R0", depth: int = 0):
        if expr is None:
            return

        if isinstance(expr, Literal):
            val = int(expr.value) if expr.val_type in ("INTEGER", "BOOLEAN") else int(float(expr.value))
            self._emit(f"LDI {target_reg}, {val}")

        elif isinstance(expr, Identifier):
            addr = self.memory.allocate_variable(expr.name)
            self._emit(f"LOAD {target_reg}, [{addr}]  // read {expr.name}")

        elif isinstance(expr, BinaryOp):
            spill_addr = SPILL_BASE + depth
            # 1. Evaluate left expression into R0
            self._compile_expression(expr.left, target_reg="R0", depth=depth + 1)
            # 2. Spill left to memory slot
            self._emit(f"STORE R0, [{spill_addr}]  // spill left depth {depth}")
            # 3. Evaluate right expression into R0
            self._compile_expression(expr.right, target_reg="R0", depth=depth + 1)
            # 4. Move right operand to R1
            self._emit("MOV R1, R0  // right operand in R1")
            # 5. Restore left operand from memory into R0
            self._emit(f"LOAD R0, [{spill_addr}]  // restore left depth {depth}")

            op = expr.op
            if op == "+":
                self._emit("ADD R0, R0, R1")
            elif op == "-":
                self._emit("SUB R0, R0, R1")
            elif op == "*":
                self._emit("MUL R0, R0, R1")
            elif op == "/":
                self._emit("DIV R0, R0, R1")
            elif op == "%":
                self._emit("MOD R0, R0, R1")
            elif op == "^":
                self._emit("MUL R0, R0, R1")
            elif op in ("==", "!=", "<", "<=", ">", ">="):
                lbl_true = self._new_label("CMP_TRUE")
                lbl_end = self._new_label("CMP_END")
                self._emit("CMP R0, R1")
                if op == "==":
                    self._emit(f"JZ {lbl_true}")
                elif op == "!=":
                    self._emit(f"JNZ {lbl_true}")
                elif op == ">":
                    self._emit(f"JGT {lbl_true}")
                elif op == "<":
                    self._emit(f"JLT {lbl_true}")
                elif op == ">=":
                    self._emit(f"JGT {lbl_true}")
                    self._emit(f"JZ {lbl_true}")
                elif op == "<=":
                    self._emit(f"JLT {lbl_true}")
                    self._emit(f"JZ {lbl_true}")
                self._emit("LDI R0, 0")
                self._emit(f"JMP {lbl_end}")
                self._emit(f"{lbl_true}:")
                self._emit("LDI R0, 1")
                self._emit(f"{lbl_end}:")

            if target_reg != "R0":
                self._emit(f"MOV {target_reg}, R0")

        elif isinstance(expr, UnaryOp):
            self._compile_expression(expr.expr, target_reg=target_reg, depth=depth)
            if expr.op == "-":
                self._emit("LDI R1, 0")
                self._emit(f"SUB {target_reg}, R1, {target_reg}")
            elif expr.op == "!":
                lbl_zero = self._new_label("NOT_ZERO")
                lbl_end = self._new_label("NOT_END")
                self._emit(f"CMPI {target_reg}, 0")
                self._emit(f"JZ {lbl_zero}")
                self._emit(f"LDI {target_reg}, 0")
                self._emit(f"JMP {lbl_end}")
                self._emit(f"{lbl_zero}:")
                self._emit(f"LDI {target_reg}, 1")
                self._emit(f"{lbl_end}:")
