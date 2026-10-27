"""
FLAT Module Unit Tests
Tests DFA state transitions, tokenization, CFG parsing, and AST construction.
"""

import unittest
from src.flat.dfa import build_identifier_dfa, build_number_dfa, build_operator_dfa
from src.flat.lexer import Lexer, LexerError
from src.flat.parser import Parser, ParserError
from src.flat.ast_nodes import VarDecl, Assignment, WhileStatement, IfStatement, BinaryOp, DncStatement


class TestFlatModule(unittest.TestCase):
    def test_identifier_dfa(self):
        dfa = build_identifier_dfa()
        res_valid = dfa.simulate("my_var_123")
        self.assertTrue(res_valid["accepted"])
        self.assertEqual(res_valid["token_type"], "IDENTIFIER")

        res_invalid = dfa.simulate("123bad")
        self.assertFalse(res_invalid["accepted"])

    def test_number_dfa(self):
        dfa = build_number_dfa()
        res_int = dfa.simulate("42")
        self.assertTrue(res_int["accepted"])

        res_float = dfa.simulate("3.1415")
        self.assertTrue(res_float["accepted"])

        res_invalid = dfa.simulate("12.34.56")
        self.assertFalse(res_invalid["accepted"])

    def test_operator_dfa(self):
        dfa = build_operator_dfa()
        self.assertTrue(dfa.simulate("+")["accepted"])
        self.assertTrue(dfa.simulate("==")["accepted"])
        self.assertTrue(dfa.simulate("<=")["accepted"])
        self.assertTrue(dfa.simulate("!=")["accepted"])

    def test_lexer_token_stream(self):
        code = "let total = x + 100; // note"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        types = [t.type for t in tokens if t.type != "EOF"]
        self.assertEqual(types, ["KEYWORD", "IDENTIFIER", "ASSIGN_OP", "IDENTIFIER", "ARITH_OP", "INTEGER", "DELIMITER"])
        # Check DFA trace is present
        self.assertGreater(len(tokens[1].dfa_trace), 0)

    def test_lexer_error_on_invalid_character(self):
        code = "let x = @bad;"
        lexer = Lexer(code)
        with self.assertRaises(LexerError):
            lexer.tokenize()

    def test_parser_variable_declaration(self):
        code = "let x = 42;"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        self.assertEqual(len(ast.statements), 1)
        self.assertIsInstance(ast.statements[0], VarDecl)
        self.assertEqual(ast.statements[0].name, "x")

    def test_parser_while_and_if(self):
        code = """
        while (x < 10) {
            if (x == 5) {
                print(x);
            }
            x = x + 1;
        }
        """
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast.statements[0], WhileStatement)
        body = ast.statements[0].body
        self.assertIsInstance(body[0], IfStatement)
        self.assertIsInstance(body[1], Assignment)

    def test_parser_dnc_statement(self):
        code = "let p = dnc fastpow(2, 8);"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        self.assertIsInstance(ast.statements[0], DncStatement)
        self.assertEqual(ast.statements[0].algorithm, "fastpow")
        self.assertEqual(len(ast.statements[0].args), 2)


if __name__ == "__main__":
    unittest.main()
