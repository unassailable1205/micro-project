"""
FLAT Module: Deterministic Finite Automata (DFA) Engine
Provides generic DFA simulation, transition table generation, and specialized
DFAs for lexical token recognition (identifiers, numbers, operators, keywords).
"""

from typing import Dict, Set, Tuple, List, Optional, Any


class DFA:
    """
    Represents a Deterministic Finite Automaton:
    M = (Q, Sigma, delta, q0, F)
    where:
      - Q: Finite set of states
      - Sigma: Input alphabet
      - delta: Transition function Q x Sigma -> Q
      - q0: Initial/Start state
      - F: Set of accepting/final states
    """
    def __init__(
        self,
        name: str,
        states: Set[str],
        alphabet: Set[str],
        transitions: Dict[Tuple[str, str], str],
        start_state: str,
        accept_states: Set[str],
        token_type: Optional[str] = None,
        default_transition: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions  # (state, char_or_class) -> next_state
        self.start_state = start_state
        self.accept_states = accept_states
        self.token_type = token_type
        self.default_transition = default_transition or {}

    def get_next_state(self, current_state: str, char: str) -> Optional[str]:
        # 1. Exact character transition
        if (current_state, char) in self.transitions:
            return self.transitions[(current_state, char)]
        
        # 2. Character class transitions
        char_class = None
        if char.isalpha():
            char_class = 'LETTER'
        elif char.isdigit():
            char_class = 'DIGIT'
        elif char in ' \t\r\n':
            char_class = 'WHITESPACE'
            
        if char_class and (current_state, char_class) in self.transitions:
            return self.transitions[(current_state, char_class)]

        # 3. Wildcard or default
        if (current_state, 'OTHER') in self.transitions:
            return self.transitions[(current_state, 'OTHER')]
            
        if current_state in self.default_transition:
            return self.default_transition[current_state]

        return None

    def simulate(self, text: str) -> Dict[str, Any]:
        """
        Simulates the DFA on the input string text.
        Returns a trace of transitions, final state, and acceptance status.
        """
        current_state = self.start_state
        trace: List[Dict[str, Any]] = []

        for idx, ch in enumerate(text):
            next_state = self.get_next_state(current_state, ch)
            trace.append({
                "step": idx + 1,
                "char": ch,
                "from_state": current_state,
                "to_state": next_state,
                "is_accept": next_state in self.accept_states if next_state else False
            })
            if next_state is None:
                return {
                    "accepted": False,
                    "final_state": current_state,
                    "consumed": text[:idx],
                    "remaining": text[idx:],
                    "token_type": None,
                    "trace": trace
                }
            current_state = next_state

        is_accepted = current_state in self.accept_states
        return {
            "accepted": is_accepted,
            "final_state": current_state,
            "consumed": text,
            "remaining": "",
            "token_type": self.token_type if is_accepted else None,
            "trace": trace
        }

    def get_transition_table(self) -> Dict[str, Any]:
        """
        Returns a structured matrix representing the state transition table.
        """
        alphabet_symbols = sorted(list(self.alphabet))
        rows = []
        for state in sorted(list(self.states)):
            row = {
                "state": state,
                "is_start": state == self.start_state,
                "is_accept": state in self.accept_states,
                "transitions": {}
            }
            for sym in alphabet_symbols:
                next_st = self.transitions.get((state, sym), "-")
                row["transitions"][sym] = next_st
            rows.append(row)

        return {
            "name": self.name,
            "alphabet": alphabet_symbols,
            "states": sorted(list(self.states)),
            "start_state": self.start_state,
            "accept_states": sorted(list(self.accept_states)),
            "rows": rows
        }


def build_identifier_dfa() -> DFA:
    """
    DFA recognizing Identifier tokens: [a-zA-Z_][a-zA-Z0-9_]*
    States: {q0 (start), q1 (accept), q_dead}
    """
    states = {"q0", "q1", "q_dead"}
    alphabet = {"LETTER", "_", "DIGIT", "OTHER"}
    transitions = {
        ("q0", "LETTER"): "q1",
        ("q0", "_"): "q1",
        ("q0", "DIGIT"): "q_dead",
        ("q0", "OTHER"): "q_dead",
        ("q1", "LETTER"): "q1",
        ("q1", "_"): "q1",
        ("q1", "DIGIT"): "q1",
        ("q1", "OTHER"): "q_dead",
        ("q_dead", "LETTER"): "q_dead",
        ("q_dead", "_"): "q_dead",
        ("q_dead", "DIGIT"): "q_dead",
        ("q_dead", "OTHER"): "q_dead",
    }
    return DFA("Identifier_DFA", states, alphabet, transitions, "q0", {"q1"}, "IDENTIFIER")


def build_number_dfa() -> DFA:
    """
    DFA recognizing Integer and Float numbers: [0-9]+(\.[0-9]+)?
    States: {q0 (start), q1 (int accept), q2 (dot seen), q3 (float accept), q_dead}
    """
    states = {"q0", "q1", "q2", "q3", "q_dead"}
    alphabet = {"DIGIT", ".", "OTHER"}
    transitions = {
        ("q0", "DIGIT"): "q1",
        ("q0", "."): "q_dead",
        ("q0", "OTHER"): "q_dead",
        ("q1", "DIGIT"): "q1",
        ("q1", "."): "q2",
        ("q1", "OTHER"): "q_dead",
        ("q2", "DIGIT"): "q3",
        ("q2", "."): "q_dead",
        ("q2", "OTHER"): "q_dead",
        ("q3", "DIGIT"): "q3",
        ("q3", "."): "q_dead",
        ("q3", "OTHER"): "q_dead",
        ("q_dead", "DIGIT"): "q_dead",
        ("q_dead", "."): "q_dead",
        ("q_dead", "OTHER"): "q_dead",
    }
    return DFA("Number_DFA", states, alphabet, transitions, "q0", {"q1", "q3"}, "NUMBER")


def build_operator_dfa() -> DFA:
    """
    DFA recognizing 1- and 2-character operators:
    +, -, *, /, %, ^, =, ==, !, !=, <, <=, >, >=
    """
    states = {"q0", "q_add", "q_sub", "q_mul", "q_div", "q_mod", "q_pow",
              "q_assign", "q_eq", "q_not", "q_neq", "q_lt", "q_lte", "q_gt", "q_gte", "q_dead"}
    alphabet = {"+", "-", "*", "/", "%", "^", "=", "!", "<", ">", "OTHER"}
    transitions = {
        ("q0", "+"): "q_add",
        ("q0", "-"): "q_sub",
        ("q0", "*"): "q_mul",
        ("q0", "/"): "q_div",
        ("q0", "%"): "q_mod",
        ("q0", "^"): "q_pow",
        ("q0", "="): "q_assign",
        ("q_assign", "="): "q_eq",
        ("q0", "!"): "q_not",
        ("q_not", "="): "q_neq",
        ("q0", "<"): "q_lt",
        ("q_lt", "="): "q_lte",
        ("q0", ">"): "q_gt",
        ("q_gt", "="): "q_gte",
    }
    accept_states = {"q_add", "q_sub", "q_mul", "q_div", "q_mod", "q_pow",
                     "q_assign", "q_eq", "q_neq", "q_lt", "q_lte", "q_gt", "q_gte"}
    return DFA("Operator_DFA", states, alphabet, transitions, "q0", accept_states, "OPERATOR")
