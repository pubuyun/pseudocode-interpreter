__all__ = [
    "PrimitiveType",
    "ArrayType",
    "Type",
]


from dataclasses import dataclass
from enum import Enum

from cambridgeScript.syntax_tree import Expression
from cambridgeScript.parser.lexer import str1


class PrimitiveType(Enum):
    INTEGER = int
    REAL = float
    CHAR = str1
    STRING = str
    BOOLEAN = bool


@dataclass(frozen=True)
class ArrayType:
    type: PrimitiveType
    ranges: list[tuple[Expression, Expression]]


Type = PrimitiveType | ArrayType
