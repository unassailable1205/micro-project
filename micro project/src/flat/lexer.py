"""
FLAT Module: Lexical Analyzer (Tokenizer)
Uses DFA state machines and regex rules to recognize tokens and validate input.
Each token records its DFA transition trajectory for educational visualization.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .dfa import build_identifier_dfa, build_number_dfa, build_operator_dfa


KEYWORDS = {"let", "if", "else", "while", "for", "print", "dnc", "return"}
BOOLEANS = {"true", "false"}
DNC_OPS = {"karatsuba", "fastpow", "binsearch", "minmax"}


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int
    dfa_trace: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "dfa_trace": self.dfa_trace or []
        }


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexical Error at line {line}, col {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """
    State machine based lexer validating tokens via DFAs.
    """
    def __init__(self, source_code: str):
        self.source = source_code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source_code)
        
        # Instantiate DFA recognizers
        self.id_dfa = build_identifier_dfa()
        self.num_dfa = build_number_dfa()
        self.op_dfa = build_operator_dfa()

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def _advance(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # Skip whitespace
            if ch in ' \t\r\n':
                self._advance()
                continue

            # Skip single-line comments: // ...
            if ch == '/' and self._peek(1) == '/':
                while self.pos < self.length and self._peek() != '\n':
                    self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # 1. Identifier or Keyword (via DFA)
            if ch.isalpha() or ch == '_':
                token = self._lex_identifier()
                tokens.append(token)
                continue

            # 2. Number (Integer / Float via DFA)
            if ch.isdigit():
                token = self._lex_number()
                tokens.append(token)
                continue

            # 3. Operators (Multi-char and single-char via Operator DFA)
            if ch in "=!+-*/%^<>":
                token = self._lex_operator()
                tokens.append(token)
                continue

            # 4. Delimiters
            if ch in "(){}[];,:":
                val = self._advance()
                tokens.append(Token(
                    type="DELIMITER",
                    value=val,
                    line=start_line,
                    column=start_col,
                    dfa_trace=[{
                        "step": 1,
                        "char": val,
                        "from_state": "q_start",
                        "to_state": "q_delimiter",
                        "is_accept": True
                    }]
                ))
                continue

            # If unrecognized character
            bad_char = self._advance()
            raise LexerError(f"Unexpected character '{bad_char}'", start_line, start_col)

        tokens.append(Token(type="EOF", value="", line=self.line, column=self.column))
        return tokens

    def _lex_identifier(self) -> Token:
        start_line = self.line
        start_col = self.column
        chars = []
        state = self.id_dfa.start_state
        trace = []
        step = 1

        while self.pos < self.length:
            ch = self._peek()
            next_state = self.id_dfa.get_next_state(state, ch)
            if next_state and next_state != "q_dead":
                self._advance()
                chars.append(ch)
                trace.append({
                    "step": step,
                    "char": ch,
                    "from_state": state,
                    "to_state": next_state,
                    "is_accept": next_state in self.id_dfa.accept_states
                })
                state = next_state
                step += 1
            else:
                break

        val = "".join(chars)
        # Classify keywords vs identifiers
        if val in KEYWORDS:
            tok_type = "KEYWORD"
        elif val in DNC_OPS:
            tok_type = "DNC_OP"
        elif val in BOOLEANS:
            tok_type = "BOOLEAN"
        else:
            tok_type = "IDENTIFIER"

        return Token(tok_type, val, start_line, start_col, trace)

    def _lex_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        chars = []
        state = self.num_dfa.start_state
        trace = []
        step = 1

        while self.pos < self.length:
            ch = self._peek()
            next_state = self.num_dfa.get_next_state(state, ch)
            if next_state and next_state != "q_dead":
                self._advance()
                chars.append(ch)
                trace.append({
                    "step": step,
                    "char": ch,
                    "from_state": state,
                    "to_state": next_state,
                    "is_accept": next_state in self.num_dfa.accept_states
                })
                state = next_state
                step += 1
            else:
                break

        val = "".join(chars)
        tok_type = "FLOAT" if "." in val else "INTEGER"
        return Token(tok_type, val, start_line, start_col, trace)

    def _lex_operator(self) -> Token:
        start_line = self.line
        start_col = self.column
        chars = []
        state = self.op_dfa.start_state
        trace = []
        step = 1

        # Check up to 2 operator characters (e.g., ==, !=, <=, >=)
        for _ in range(2):
            ch = self._peek()
            if not ch:
                break
            next_state = self.op_dfa.get_next_state(state, ch)
            if next_state and next_state != "q_dead":
                self._advance()
                chars.append(ch)
                trace.append({
                    "step": step,
                    "char": ch,
                    "from_state": state,
                    "to_state": next_state,
                    "is_accept": next_state in self.op_dfa.accept_states
                })
                state = next_state
                step += 1
            else:
                break

        val = "".join(chars)
        if val == "=":
            tok_type = "ASSIGN_OP"
        elif val in ("==", "!=", "<", "<=", ">", ">="):
            tok_type = "COMP_OP"
        else:
            tok_type = "ARITH_OP"

        return Token(tok_type, val, start_line, start_col, trace)
