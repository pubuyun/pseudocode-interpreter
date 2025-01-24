from dataclasses import dataclass, field

from cambridgeScript.parser.lexer import Value
from cambridgeScript.syntax_tree import FunctionDecl, ProcedureDecl
from cambridgeScript.syntax_tree.types import Type

@dataclass
class VariableState:
    variables: dict[str, (list[Value] | Value | None, Type)] = field(default_factory=dict)
    constants: dict[str, Value] = field(default_factory=dict)
    functions: dict[str, FunctionDecl] = field(default_factory=dict)
    procedures: dict[str, ProcedureDecl] = field(default_factory=dict)
