"""
FLAT Module: Context-Free Grammar (CFG) Parser
Recursive-descent syntax analyzer validating programming statements
and constructing an Abstract Syntax Tree (AST).
"""

from typing import List, Optional
from .lexer import Token
from .ast_nodes import (
    Program, VarDecl, Assignment, BinaryOp, UnaryOp,
    Literal, Identifier, IfStatement, WhileStatement,
    PrintStatement, DncStatement, ASTNode
)


class ParserError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"Syntax Error at line {token.line}, col {token.column}: {message} (found '{token.value}')")
        self.message = message
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _match(self, *expected_values: str) -> bool:
        curr = self._current()
        return curr.value in expected_values or curr.type in expected_values

    def _consume(self, expected_value: Optional[str] = None, expected_type: Optional[str] = None) -> Token:
        curr = self._current()
        if expected_value and curr.value != expected_value:
            raise ParserError(f"Expected '{expected_value}', got '{curr.value}'", curr)
        if expected_type and curr.type != expected_type:
            raise ParserError(f"Expected token type '{expected_type}', got '{curr.type}'", curr)
        self.pos += 1
        return curr

    def parse(self) -> Program:
        statements: List[ASTNode] = []
        while not self._match("EOF"):
            statements.append(self._parse_statement())
        return Program(statements=statements)

    def _parse_statement(self) -> ASTNode:
        curr = self._current()
        if curr.value == "let":
            return self._parse_var_decl()
        elif curr.value == "if":
            return self._parse_if_statement()
        elif curr.value == "while":
            return self._parse_while_statement()
        elif curr.value == "print":
            return self._parse_print_statement()
        elif curr.type == "IDENTIFIER":
            return self._parse_assignment()
        else:
            raise ParserError(f"Unexpected statement beginning with '{curr.value}'", curr)

    def _parse_var_decl(self) -> VarDecl:
        let_tok = self._consume("let")
        id_tok = self._consume(expected_type="IDENTIFIER")
        self._consume("=")

        if self._match("dnc"):
            dnc_node = self._parse_dnc_call(id_tok.value, let_tok.line)
            self._consume(";")
            return dnc_node

        expr = self._parse_expression()
        self._consume(";")
        return VarDecl(name=id_tok.value, expr=expr, line=let_tok.line)

    def _parse_assignment(self) -> Assignment:
        id_tok = self._consume(expected_type="IDENTIFIER")
        self._consume("=")

        if self._match("dnc"):
            dnc_node = self._parse_dnc_call(id_tok.value, id_tok.line)
            self._consume(";")
            return dnc_node

        expr = self._parse_expression()
        self._consume(";")
        return Assignment(name=id_tok.value, expr=expr, line=id_tok.line)

    def _parse_if_statement(self) -> IfStatement:
        if_tok = self._consume("if")
        self._consume("(")
        cond = self._parse_expression()
        self._consume(")")
        self._consume("{")
        then_body = []
        while not self._match("}") and not self._match("EOF"):
            then_body.append(self._parse_statement())
        self._consume("}")

        else_body = []
        if self._match("else"):
            self._consume("else")
            self._consume("{")
            while not self._match("}") and not self._match("EOF"):
                else_body.append(self._parse_statement())
            self._consume("}")

        return IfStatement(condition=cond, then_branch=then_body, else_branch=else_body, line=if_tok.line)

    def _parse_while_statement(self) -> WhileStatement:
        while_tok = self._consume("while")
        self._consume("(")
        cond = self._parse_expression()
        self._consume(")")
        self._consume("{")
        body = []
        while not self._match("}") and not self._match("EOF"):
            body.append(self._parse_statement())
        self._consume("}")
        return WhileStatement(condition=cond, body=body, line=while_tok.line)

    def _parse_print_statement(self) -> PrintStatement:
        p_tok = self._consume("print")
        self._consume("(")
        expr = self._parse_expression()
        self._consume(")")
        self._consume(";")
        return PrintStatement(expr=expr, line=p_tok.line)

    def _parse_dnc_call(self, target_var: str, line: int) -> DncStatement:
        self._consume("dnc")
        algo_tok = self._consume()
        if algo_tok.value not in {"karatsuba", "fastpow", "binsearch", "minmax"}:
            raise ParserError(f"Unknown divide-and-conquer operation '{algo_tok.value}'. Choose from karatsuba, fastpow, binsearch, minmax.", algo_tok)
        self._consume("(")
        args = []
        if not self._match(")"):
            args.append(self._parse_expression())
            while self._match(","):
                self._consume(",")
                args.append(self._parse_expression())
        self._consume(")")
        return DncStatement(target=target_var, algorithm=algo_tok.value, args=args, line=line)

    def _parse_expression(self) -> ASTNode:
        return self._parse_relational()

    def _parse_relational(self) -> ASTNode:
        node = self._parse_additive()
        while self._current().value in ("==", "!=", "<", "<=", ">", ">="):
            op = self._consume().value
            right = self._parse_additive()
            node = BinaryOp(left=node, op=op, right=right, line=self._current().line)
        return node

    def _parse_additive(self) -> ASTNode:
        node = self._parse_multiplicative()
        while self._current().value in ("+", "-"):
            op = self._consume().value
            right = self._parse_multiplicative()
            node = BinaryOp(left=node, op=op, right=right, line=self._current().line)
        return node

    def _parse_multiplicative(self) -> ASTNode:
        node = self._parse_power()
        while self._current().value in ("*", "/", "%"):
            op = self._consume().value
            right = self._parse_power()
            node = BinaryOp(left=node, op=op, right=right, line=self._current().line)
        return node

    def _parse_power(self) -> ASTNode:
        node = self._parse_unary()
        while self._current().value == "^":
            op = self._consume().value
            right = self._parse_unary()
            node = BinaryOp(left=node, op=op, right=right, line=self._current().line)
        return node

    def _parse_unary(self) -> ASTNode:
        if self._current().value in ("-", "!"):
            op = self._consume().value
            expr = self._parse_unary()
            return UnaryOp(op=op, expr=expr, line=self._current().line)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        curr = self._current()
        if curr.type == "INTEGER":
            self._consume()
            return Literal(value=int(curr.value), val_type="INTEGER", line=curr.line)
        elif curr.type == "FLOAT":
            self._consume()
            return Literal(value=float(curr.value), val_type="FLOAT", line=curr.line)
        elif curr.type == "BOOLEAN":
            self._consume()
            return Literal(value=curr.value == "true", val_type="BOOLEAN", line=curr.line)
        elif curr.type == "IDENTIFIER":
            self._consume()
            return Identifier(name=curr.value, line=curr.line)
        elif curr.value == "(":
            self._consume("(")
            expr = self._parse_expression()
            self._consume(")")
            return expr
        else:
            raise ParserError(f"Expected expression, found '{curr.value}'", curr)
