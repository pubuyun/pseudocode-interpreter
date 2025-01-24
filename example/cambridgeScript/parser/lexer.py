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



class str1(str):
    def __new__(cls, value):
        if len(value) != 1:
            raise ValueError("char instances must contain exactly one character.")
        return super().__new__(cls, value)
    
Value = str | int | float | bool | str1


class _EOFSentinel:
    pass


EOF = _EOFSentinel()

class InvalidTokenError(ValueError):
    def parse3(self, origin, line):
        if line >= 2 and line <= len(origin) - 1:
            return f"{line-1} {origin[line-2]}\n{line} {origin[line-1]}\n" + "^^" + "^"*len(origin[line-1]) + f"\n{line+1} {origin[line]}"
        else:
            return f"{line} {origin[line-1]}\n" + "^^" + "^"*len(origin[line-1])
    def __init__(self, prompt, origin, line) -> None:
        self.prompt = prompt
        self.origin = origin
        self.line = line
    def __str__(self) -> str:
        return (self.prompt + "\n" + self.parse3(self.origin, self.line))

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
    ("SYMBOL", r"-|(" + "|".join(re.escape(s) for s in Symbol if s != "-") + ")"),
    ("LITERAL", r'-?[0-9]+(?:\.[0-9]+)?|".*?"'),
    ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("INVALID", r"."),
    ("EOF", r"$"),
]




_TOKEN_REGEX = "|".join(f"(?P<{name}>{regex})" for name, regex in _TOKENS)


def _parse_literal(literal: str) -> Value:
    if literal.startswith('"') and literal.endswith('"'):
        return literal[1:-1]
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
    originNoSpace = code.replace(" ", "").splitlines()
    res: list[Token] = []
    line_number: int = 1
    line_start: int = 0
    last_token = None  # 记录最后一个有效 Token
    jump = False
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
                f"Invalid token {originNoSpace[line_number - 1][token_start - line_start - 1]} at line {line_number}, column {token_start - line_start}",
                origin,
                line_number
            )

        # 特殊处理负号
        if token_type == "SYMBOL" and token_value == "-":
            if (last_token is None or  # 行首
                isinstance(last_token, SymbolToken) or  # 紧接符号
                isinstance(last_token, KeywordToken) or  # 关键字后
                isinstance(last_token, EOFToken)):  # 文件末尾前
                # 尝试将后续的 Token 与当前符号结合
                match_next = re.match(_TOKEN_REGEX, code[match.end():])
                if match_next and match_next.lastgroup == "LITERAL":
                    literal_value = code[match.end():match.end() + len(match_next.group())]
                    token_value = f"-{literal_value}"
                    token_type = "LITERAL"
                    match = re.match(_TOKEN_REGEX, code[match.start():match.start() + len(token_value)])
                else:
                    raise InvalidTokenError(
                        f"Invalid token '-' at line {line_number}, column {token_start - line_start}",
                        origin,
                        line_number
                    )
                jump = True

        try:
            token = _parse_token(
                token_value,
                token_type,
                line=line_number,
                column=token_start - line_start,
            )
        except ValueError:
            raise InvalidTokenError(
                f"Invalid literal {token_value}",
                origin,
                line_number
            )

        res.append(token)
        last_token = token  # 更新最后一个 Token
    return res
