"""
FLAT Module: Regular Expressions & Pattern Recognition
Defines formal regular expressions for lexical tokens and syntactic statement patterns.
"""

import re
from typing import List, Dict, Any, Tuple, Optional


# Token Regular Expression Specifications
TOKEN_REGEX_RULES = [
    ("COMMENT", r"//[^\n]*"),
    ("FLOAT", r"\d+\.\d+"),
    ("INTEGER", r"\d+"),
    ("KEYWORD", r"\b(let|if|else|while|for|print|dnc|return|func)\b"),
    ("DNC_OP", r"\b(karatsuba|fastpow|binsearch|minmax)\b"),
    ("BOOLEAN", r"\b(true|false)\b"),
    ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("COMP_OP", r"(==|!=|<=|>=|<|>)"),
    ("ASSIGN_OP", r"="),
    ("ARITH_OP", r"(\+|\-|\*|/|%|\^)"),
    ("DELIMITER", r"(\(|\)|\{|\}|\[|\]|;|,|:)"),
    ("WHITESPACE", r"[ \t\r\n]+"),
    ("UNKNOWN", r"."),
]

# High-Level Statement Pattern Signatures
STATEMENT_PATTERNS = {
    "DECLARATION": {
        "regex": r"^\s*let\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+);\s*$",
        "description": "Variable Declaration (e.g., let x = 42;)"
    },
    "ASSIGNMENT": {
        "regex": r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+);\s*$",
        "description": "Variable Assignment (e.g., x = y + 1;)"
    },
    "PRINT": {
        "regex": r"^\s*print\s*\((.+)\)\s*;\s*$",
        "description": "Print Statement (e.g., print(x);)"
    },
    "IF_BRANCH": {
        "regex": r"^\s*if\s*\((.+)\)\s*\{",
        "description": "Conditional If Block (e.g., if (x > 0) {)"
    },
    "WHILE_LOOP": {
        "regex": r"^\s*while\s*\((.+)\)\s*\{",
        "description": "While Loop Structure (e.g., while (i < n) {)"
    },
    "DNC_STATEMENT": {
        "regex": r"^\s*let\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*dnc\s+([a-zA-Z0-9_]+)\s*\((.+)\)\s*;\s*$",
        "description": "Divide-and-Conquer Invocation (e.g., let res = dnc fastpow(base, exp);)"
    }
}


class RegexPatternMatcher:
    """
    Evaluates regular expressions against tokens and statements,
    reporting match groups, validity, and pattern classification.
    """
    @staticmethod
    def identify_statement_pattern(line: str) -> Dict[str, Any]:
        stripped = line.strip()
        for name, meta in STATEMENT_PATTERNS.items():
            match = re.match(meta["regex"], stripped)
            if match:
                return {
                    "matched": True,
                    "pattern_name": name,
                    "description": meta["description"],
                    "groups": match.groups(),
                    "raw": stripped
                }
        return {
            "matched": False,
            "pattern_name": "UNKNOWN",
            "description": "Unrecognized or composite statement syntax",
            "groups": (),
            "raw": stripped
        }

    @staticmethod
    def get_token_rules() -> List[Dict[str, str]]:
        return [{"type": name, "regex": pat} for name, pat in TOKEN_REGEX_RULES]
