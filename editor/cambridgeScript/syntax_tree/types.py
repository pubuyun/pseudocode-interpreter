__all__ = [
    "PrimitiveType",
    "ArrayType",
    "Type",
]


from dataclasses import dataclass
from enum import Enum

from cambridgeScript.syntax_tree import Expression
from cambridgeScript.parser.lexer import char


class PseudoInputError(Exception):
    # only parse 1 line
    def __init__(self, prompt, origin, line):
        self.prompt = prompt
        self.origin = origin
        self.line = line

    def __str__(self):
        return (
            self.prompt
            + "\n"
            + self.origin[self.line - 1]
            + "\n"
            + " " * (len(self.origin[self.line - 1]) - 1)
            + "^"  # under the variable
        )


class PrimitiveType(Enum):
    INTEGER = int
    REAL = float
    CHAR = char
    STRING = str
    BOOLEAN = bool

    @staticmethod
    def parse_to_type(vartype, value, name, origin, line):
        if vartype == PrimitiveType.INTEGER:
            try:
                value = float(value)
            except:
                raise PseudoInputError(
                    f"Non number value entered for integer variable {name}",
                    origin,
                    line,
                )
            if value % 1:
                raise PseudoInputError(
                    f"Entered real number for integer variable {name}",
                    origin,
                    line,
                )
            val = int(value)
        elif vartype == PrimitiveType.BOOLEAN:
            if not value.upper() in ["TRUE", "FALSE"]:
                raise PseudoInputError(
                    f"invalid valueut {value} for boolean variable {name}",
                    origin,
                    line,
                )
            val = True if value.upper() == "TRUE" else False
        elif vartype == PrimitiveType.CHAR:
            val = value[0]
        elif vartype == PrimitiveType.STRING:
            val = value
        elif vartype == PrimitiveType.REAL:
            try:
                value = float(value)
            except:
                raise PseudoInputError(
                    f"Non number value entered for integer variable {name}",
                    origin,
                    line,
                )
            val = value
        return val


@dataclass(frozen=True)
class ArrayType:
    type: PrimitiveType
    ranges: list[tuple[Expression, Expression]]


Type = PrimitiveType | ArrayType
