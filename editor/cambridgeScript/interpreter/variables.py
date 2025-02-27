from dataclasses import dataclass, field
from typing import Any
from functools import reduce

from cambridgeScript.parser.lexer import Value
from cambridgeScript.syntax_tree import FunctionDecl, ProcedureDecl
from cambridgeScript.syntax_tree.types import Type, ArrayType


@dataclass
class VariableState:
    variables: dict[str, tuple[list[Value] | Value | None, Type]] = field(
        default_factory=dict
    )
    constants: dict[str, Value] = field(default_factory=dict)
    functions: dict[str, FunctionDecl] = field(default_factory=dict)
    procedures: dict[str, ProcedureDecl] = field(default_factory=dict)
    variable_stack: list[dict[str, tuple[list[Value] | Value | None, Type]]] = field(
        default_factory=list
    )

    def push_scope(self) -> None:
        """Push current variable scope onto stack and create new scope."""
        self.variable_stack.append(self.variables.copy())
        self.variables = self.variables.copy()

    def pop_scope(self) -> None:
        """Restore previous variable scope."""
        if self.variable_stack:
            current_scope = self.variables
            self.variables = self.variable_stack.pop()
            # Update any modified variables in the parent scope
            for var in self.variables.keys():
                if var in current_scope:
                    self.variables[var] = current_scope[var]

    def create_nd_array(
        self, ranges: list[tuple[int, int]], default: Any = None
    ) -> list:
        """Create an n-dimensional array."""
        if not ranges:
            return default
        start, end = ranges[0]
        # Create array from 0 to size-1, where size matches the range
        size = end - start + 1
        return [self.create_nd_array(ranges[1:], default) for _ in range(size)]

    def get_array_value(
        self, name: str, indices: list[int], ranges: list[tuple[int, int]]
    ) -> Value:
        """Get value from array at given indices."""
        # Convert user indices to zero-based indices for internal array access
        internal_indices = [i - start for i, (start, _) in zip(indices, ranges)]
        target = reduce(
            lambda x, i: x[i],
            internal_indices,
            self.variables[name][0].copy(),
        )
        return target

    def set_array_value(
        self, name: str, indices: list[int], value: Value, ranges: list[tuple[int, int]]
    ) -> None:
        """Set value in array at given indices."""
        # Convert user indices to zero-based indices for internal array access
        internal_indices = [i - start for i, (start, _) in zip(indices, ranges)]
        arrcpy = self.variables[name][0].copy()
        target = reduce(lambda x, i: x[i], internal_indices[:-1], arrcpy)
        target[internal_indices[-1]] = value
        self.variables[name] = (arrcpy, self.variables[name][1])
