from cambridgeScript.syntax_tree import (
    Expression,
    Statement,
)
from cambridgeScript.parser.lexer import Token, TokenComparable


class PseudoError(Exception):
    prompt: str
    origin: list[str]
    line: int

    def __init__(self, prompt, origin, line):
        self.prompt = prompt
        self.origin = origin
        self.line = line

    def message(self) -> str:
        return self.prompt

    def parse_traceback(self) -> str:
        if not hasattr(self, "origin") or not hasattr(self, "line"):
            return ""
        if self.line >= 2 and self.line <= len(self.origin) - 1:
            return (
                f"{self.line-1} {self.origin[self.line-2]}\n{self.line} {self.origin[self.line-1]}\n"
                + "  "
                + "^" * len(self.origin[self.line - 1])
                + f"\n{self.line+1} {self.origin[self.line]}"
            )
        else:
            return f"{self.line} {self.origin[self.line-1]}\n  " + "^" * len(
                self.origin[self.line - 1]
            )

    def __str__(self) -> str:
        msg = self.message()
        trace = self.parse_traceback()
        return f"{msg}{': ' + chr(10) if trace else ''}{trace}"


class ParserError(PseudoError):
    """Base exception class for errors from the parser"""


class _InvalidMatch(ParserError):
    def __init__(self):
        pass


class UnexpectedToken(ParserError):
    """Raised when the parser encounters an unexpected token"""

    expected: TokenComparable
    actual: Token

    def __init__(self, expected: TokenComparable, actual: Token, origin, line):
        self.expected = expected
        self.actual = actual
        self.origin = origin
        self.line = line

    def __str__(self):
        return (
            f"Expected '{self.expected}' at {self.actual.location}, "
            f"found '{self.actual}' instead\n"
            f"{self.parse_traceback(self.origin, self.line)}"
        )


class UnexpectedTokenType(ParserError):
    """Raised when the parser encounters an unexpected token type"""

    expected_type: type[Token]
    actual: Token

    def __init__(self, expected: type[Token], actual: Token, origin, line):
        self.expected_type = expected
        self.actual = actual
        self.origin = origin
        self.line = line

    def __str__(self):
        return (
            f"Expected {self.expected_type.__name__.lower()} at {self.actual.location}, "
            f"found '{self.actual}' instead\n"
            f"{self.parse_traceback(self.origin, self.line)}"
        )


class InterpreterError(PseudoError):
    pass


class InvalidNode(InterpreterError):
    node: Statement | Expression
    token: Token

    def __init__(self, node: Statement | Expression, token: Token, origin):
        self.node = node
        self.token = token
        self.origin = origin
        self.line = token.line

    def message(self) -> str:
        return f"Invalid node at {self.token.location}: {self.node}"


class PseudoOpError(InterpreterError, TypeError):
    op_error: TypeError
    line: int

    def __init__(self, left, right, op_error):
        self.left = left
        self.right = right
        self.op_error = op_error

    def message(self) -> str:
        return (
            f"Unsupported operation for {self.left} and {self.right}: {self.op_error}"
        )


class PseudoBuiltinError(InterpreterError, ValueError):
    def __init__(self, prompt):
        self.prompt = prompt

    def message(self) -> str:
        return self.prompt


class PseudoInputError(InterpreterError, ValueError):

    def message(self) -> str:
        return f"Input Error: {self.prompt}"


class PseudoUndefinedError(InterpreterError, RuntimeError):

    def message(self) -> str:
        return f"Undefined Identifier: {self.prompt}"


class PseudoAssignmentError(InterpreterError, RuntimeError):

    def message(self) -> str:
        return f"Assignment Error: {self.prompt}"


class PseudoIndexError(InterpreterError, ValueError):
    def __init__(self, name, indices, ranges, origin, line):
        self.name = name
        self.indices = indices
        self.ranges = ranges
        self.origin = origin
        self.line = line

    def message(self) -> str:
        return f"List index out of range, trying to access {self.name}{''.join(f'[{indice}]' for indice in self.indices)}, but {self.name} has a range of {self.ranges}"


class PseudoSubroutineError(InterpreterError, RuntimeError):

    def message(self) -> str:
        return self.prompt


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value
        super().__init__(value)
