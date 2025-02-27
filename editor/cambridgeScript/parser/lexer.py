__all__ = [
    "Value",
    "EOF",
    "TokenComparable",
    "Token",
    "KeywordToken",
    "SymbolToken",
    "LiteralToken",
    "IdentifierToken",
    "EOFToken",
    "parse_tokens",
]

import re
from dataclasses import dataclass

from cambridgeScript.constants import Keyword, Symbol


# char type
class char(str):
    def __new__(cls, value):
        if len(value) != 1:
            raise ValueError("char instances must contain exactly one character.")
        return super().__new__(cls, value)


Value = str | int | float | bool | char


class _EOFSentinel:
    pass


EOF = _EOFSentinel()


class InvalidTokenError(ValueError):
    def parse_traceback(self, origin, line):
        if line >= 2 and line <= len(origin) - 1:
            return (
                f"{line-1} {origin[line-2]}\n{line} {origin[line-1]}\n"
                + "^^"
                + "^" * len(origin[line - 1])
                + f"\n{line+1} {origin[line]}"
            )
        else:
            return f"{line} {origin[line-1]}\n" + "^^" + "^" * len(origin[line - 1])

    def __init__(self, prompt, origin, line) -> None:
        self.prompt = prompt
        self.origin = origin
        self.line = line

    def __str__(self) -> str:
        return self.prompt + "\n" + self.parse_traceback(self.origin, self.line)


@dataclass(frozen=True)
class Token:
    line: int | None
    column: int | None

    @property
    def location(self) -> str:
        return f"Line {self.line} Column {self.column}"


TokenComparable = Token | Keyword | Symbol | str | Value | _EOFSentinel


@dataclass(frozen=True)
class KeywordToken(Token):
    keyword: Keyword

    def __eq__(self, other):
        if isinstance(other, Keyword):
            return self.keyword == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.keyword)


@dataclass(frozen=True)
class SymbolToken(Token):
    symbol: Symbol

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.symbol == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.symbol)


@dataclass(frozen=True)
class LiteralToken(Token):
    value: Value

    @property
    def type(self):
        return type(self.value)


@dataclass(frozen=True)
class IdentifierToken(Token):
    value: str

    def __eq__(self, other):
        return self.value == other or super().__eq__(other)


@dataclass(frozen=True)
class EOFToken(Token):
    def __eq__(self, other):
        if other is EOF:
            return True
        return super().__eq__(other)


_TOKENS = [
    ("IGNORE", r"/\*.*\*/|(?://|#).*$|[ \t]+"),
    ("NEWLINE", r"\n"),
    ("KEYWORD", "|".join(Keyword)),
    ("LITERAL", r'-?[0-9]+(?:\.[0-9]+)?|".*?"|TRUE|FALSE'),
    ("SYMBOL", r"(" + "|".join(map(re.escape, Symbol)) + ")"),
    ("IDENTIFIER", r"[A-Za-z0-9]+"),
    ("INVALID", r"."),
    ("EOF", r"$"),
]
_TOKEN_REGEX = "|".join(f"(?P<{name}>{regex})" for name, regex in _TOKENS)


def _parse_literal(literal: str) -> Value:
    if literal.startswith('"') and literal.endswith('"'):
        return literal[1:-1]
    if literal == "TRUE":
        return True
    if literal == "FALSE":
        return False
    try:
        if "." in literal:
            return float(literal)
        else:
            return int(literal)
    except ValueError:
        raise ValueError("Invalid literal")


def _parse_token(token_string: str, token_type: str, **token_kwargs) -> Token:
    if token_type == "KEYWORD":
        return KeywordToken(keyword=Keyword(token_string), **token_kwargs)
    elif token_type == "IDENTIFIER":
        return IdentifierToken(value=token_string, **token_kwargs)
    elif token_type == "SYMBOL":
        return SymbolToken(symbol=Symbol(token_string), **token_kwargs)
    elif token_type == "EOF":
        return EOFToken(**token_kwargs)
    else:
        value = _parse_literal(token_string)
        return LiteralToken(value=value, **token_kwargs)


def parse_tokens(code: str) -> list[Token]:
    """
    Parse tokens from a program.
    :param code: program to parse.
    :type code: str
    :return: a list containing the tokens in the program.
    :rtype: list[Token]
    """
    origin = code.splitlines()
    origin_no_space = code.replace(" ", "").splitlines()
    res: list[Token] = []
    line_number: int = 1
    line_start: int = 0
    last_token = None  # record last valid token
    jump = False  # jump to next token, for minus sign
    for match in re.finditer(_TOKEN_REGEX, code, re.M):
        if jump:
            jump = False
            continue
        token_type = match.lastgroup
        if token_type is None:
            raise ValueError("An error occurred")
        token_value = str(match.group())
        token_start = match.start()
        if token_type == "IGNORE":
            continue
        elif token_type == "NEWLINE":
            line_number += 1
            line_start = token_start
            continue
        elif token_type == "INVALID":
            raise InvalidTokenError(
                f"Invalid token {origin_no_space[line_number - 1][token_start - line_start - 1]} at line {line_number}, column {token_start - line_start}",
                origin,
                line_number,
            )

        try:
            token = _parse_token(
                token_value,
                token_type,
                line=line_number,
                column=token_start - line_start,
            )
        except ValueError:
            raise InvalidTokenError(
                f"Invalid literal {token_value}", origin, line_number
            )

        res.append(token)
    return res
