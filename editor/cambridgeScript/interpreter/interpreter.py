from cambridgeScript.interpreter.variables import VariableState
from cambridgeScript.parser.lexer import LiteralToken, Value
from cambridgeScript.syntax_tree.expression import Expression
from cambridgeScript.syntax_tree.types import PrimitiveType, ArrayType
from cambridgeScript.exceptions import (
    InterpreterError,
    InvalidNode,
    PseudoAssignmentError,
    PseudoIndexError,
    PseudoSubroutineError,
    PseudoUndefinedError,
    PseudoOpError,
    PseudoInputError,
    ReturnException,
)

from cambridgeScript.syntax_tree import (
    Expression,
    Identifier,
    Literal,
    ArrayIndex,
    FunctionCall,
    UnaryOp,
    BinaryOp,
    Statement,
    AssignmentStmt,
    ProcedureCallStmt,
    FileCloseStmt,
    FileWriteStmt,
    FileReadStmt,
    FileOpenStmt,
    ReturnStmt,
    OutputStmt,
    InputStmt,
    ConstantDecl,
    VariableDecl,
    WhileStmt,
    RepeatUntilStmt,
    ForStmt,
    CaseStmt,
    IfStmt,
    FunctionDecl,
    ProcedureDecl,
    Program,
)
from cambridgeScript.syntax_tree.visitors import ExpressionVisitor, StatementVisitor
from cambridgeScript.interpreter.builtin_function import create_builtins
import random


class Interpreter(ExpressionVisitor, StatementVisitor):
    variable_state: VariableState

    def __init__(self, variable_state: VariableState, origin: str, input_stream=None):
        self.variable_state = variable_state
        self.origin = origin.splitlines()
        self.builtins = create_builtins(self)
        self.input_stream = input_stream or __import__("sys").stdin

    def visit(self, thing: Expression | Statement):
        if isinstance(thing, Expression):
            return ExpressionVisitor.visit(self, thing)
        else:
            return StatementVisitor.visit(self, thing)

    def visit_statements(self, statements: list[Statement]):
        for stmt in statements:
            self.visit(stmt)

    def visit_binary_op(self, expr: BinaryOp) -> Value:
        left = self.visit(expr.left)
        right = self.visit(expr.right)
        try:
            return expr.operator(left, right)
        except TypeError as e:
            raise PseudoOpError(expr.left, expr.right, e)

    def visit_unary_op(self, expr: UnaryOp) -> Value:
        operand = self.visit(expr.operand)
        return expr.operator(operand)

    def visit_function_call(self, func_call):
        function_name = func_call.function.token.value
        line = func_call.function.token.line
        if function_name in self.builtins:
            return self.builtins[function_name](func_call.params)
        elif function_name in self.variable_state.functions:
            func = self.variable_state.functions[function_name]

            # Create new scope for function parameters
            self.variable_state.push_scope()
            if func.params is not None:
                # Bind function parameters to new variable state
                for param, original_param in zip(func_call.params, func.params):
                    param_value = self.visit(param)
                    self.variable_state.variables[original_param[0].value] = (
                        param_value,
                        original_param[1],
                    )

            try:
                # Execute function body and handle return value via exception
                self.visit_statements(func.body)
                # If we reach here, no return statement was encountered
                raise PseudoSubroutineError(
                    f"Function {function_name} did not return a value",
                    self.origin,
                    line,
                )
            except ReturnException as ret:
                # Restore previous scope and return value
                self.variable_state.pop_scope()
                return ret.value
        else:
            raise PseudoUndefinedError(
                f"name {function_name} is not defined", self.origin, line
            )

    def visit_array_index(self, expr: ArrayIndex) -> Value:
        name = expr.array.token.value
        array_type = self.variable_state.variables[name][1]
        if not isinstance(array_type, ArrayType):
            raise PseudoAssignmentError(
                f"{name} is not an array.", self.origin, expr.array.token.line
            )

        indices = [self.visit(indexexp) for indexexp in expr.index]
        ranges = [(self.visit(a), self.visit(b)) for a, b in array_type.ranges]

        try:
            target = self.variable_state.get_array_value(name, indices, ranges)
        except IndexError:
            raise PseudoIndexError(
                name,
                indices,
                ranges,
                self.origin,
                expr.array.token.line,
            )
        return target

    def visit_literal(self, expr: Literal) -> Value:
        if not isinstance(expr.token, LiteralToken):
            raise InvalidNode(expr.token, self.origin)
        return expr.token.value

    def visit_identifier(self, expr: Identifier) -> Value:
        name = expr.token.value
        if name in self.variable_state.variables:
            value = self.variable_state.variables[name][0]
        elif name in self.variable_state.constants:
            value = self.variable_state.constants[name]
        else:
            raise InterpreterError(f"Name {name} isn't defined")

        if value is None:
            raise InterpreterError(f"Name {name} has no value")
        return value

    def visit_proc_decl(self, stmt: ProcedureDecl) -> None:
        self.variable_state.procedures[stmt.name.value] = stmt

    def visit_func_decl(self, stmt: FunctionDecl) -> None:
        self.variable_state.functions[stmt.name.value] = stmt

    def visit_if(self, stmt: IfStmt) -> None:
        condition = self.visit(stmt.condition)
        if condition:
            self.visit_statements(stmt.then_branch)
        elif stmt.else_branch is not None:
            self.visit_statements(stmt.else_branch)

    def visit_case(self, stmt: CaseStmt):
        expr = self.visit(stmt.expr)
        for i in stmt.cases:
            if self.visit(i[0]) == expr:
                self.visit_statements(i[1])
                return
        if stmt.otherwise is not None:
            self.visit_statements(stmt.otherwise)

    def visit_for_loop(self, stmt: ForStmt) -> None:
        if isinstance(stmt, ArrayIndex):
            raise NotImplemented
        name = stmt.variable.token.value
        current_value = self.visit(stmt.start)
        end_value = self.visit(stmt.end)
        if stmt.step is not None:
            step_value = self.visit(stmt.step)
        else:
            step_value = 1
        cnt = 0
        while (
            current_value <= end_value if step_value > 0 else current_value >= end_value
        ):
            self.variable_state.variables[name] = (current_value, PrimitiveType.INTEGER)
            self.visit_statements(stmt.body)
            current_value += step_value
            cnt += 1
            if cnt > 10000:
                raise InterpreterError(
                    "Maximum iteration limit(10000) reached",
                    self.origin,
                    stmt.variable.token.line,
                )

    def visit_repeat_until(self, stmt: RepeatUntilStmt) -> None:
        self.visit_statements(stmt.body)
        cnt = 0
        while True:
            self.visit_statements(stmt.body)
            expr = self.visit(stmt.condition)
            if expr:
                break
            cnt += 1
            if cnt > 10000:
                raise InterpreterError(
                    "Maximum iteration limit(10000) reached",
                    self.origin,
                    stmt.condition.token.line,
                )

    def visit_while(self, stmt: WhileStmt) -> None:
        expr = self.visit(stmt.condition)
        cnt = 0
        while expr:
            self.visit_statements(stmt.body)
            expr = self.visit(stmt.condition)
            cnt += 1
            if cnt > 10000:
                raise InterpreterError(
                    "Maximum iteration limit(10000) reached",
                    self.origin,
                    stmt.condition.token.line,
                )

    def visit_variable_decl(self, stmt: VariableDecl) -> None:
        # for name in stmt.names:
        name = stmt.name
        if isinstance(stmt.vartype, ArrayType):
            ranges = [(self.visit(a), self.visit(b)) for a, b in stmt.vartype.ranges]
            self.variable_state.variables[name.value] = (
                self.variable_state.create_nd_array(ranges),
                stmt.vartype,
            )
        else:
            self.variable_state.variables[name.value] = (None, stmt.vartype)

    def visit_constant_decl(self, stmt: ConstantDecl) -> None:
        self.variable_state.constants[stmt.name.value] = stmt.value.value

    def visit_input(self, stmt: InputStmt) -> None:
        if isinstance(stmt.variable, ArrayIndex):
            name = stmt.variable.array.token.value
            array_type = self.variable_state.variables[name][1]
            vartype = array_type.type

        else:
            name = stmt.variable.token.value
            vartype = self.variable_state.variables[name][1]

        if name not in self.variable_state.variables:
            raise InterpreterError(f"{name} was not declared")
        if name in self.variable_state.constants:
            raise PseudoInputError(
                f"{name} is a constant, which can't be inputted",
                self.origin,
                stmt.variable.token.line,
            )

        inp = self.input_stream.readline().strip()
        val = PrimitiveType.parse_to_type(
            vartype, inp, name, self.origin, stmt.variable.token.line
        )
        if isinstance(stmt.variable, ArrayIndex):
            indices = [self.visit(indexexp) for indexexp in stmt.variable.index]
            ranges = [(self.visit(a), self.visit(b)) for a, b in vartype.ranges]
            self.variable_state.set_array_value(name, indices, val, ranges)
        else:
            self.variable_state.variables[name] = (
                val,
                self.variable_state.variables[name][1],
            )

    def visit_output(self, stmt: OutputStmt) -> None:
        values = [self.visit(expr) for expr in stmt.values]
        print("".join(map(str, values)))

    def visit_return(self, stmt: ReturnStmt) -> None:
        raise ReturnException(self.visit(stmt.value))

    def visit_f_open(self, stmt: FileOpenStmt) -> None:
        pass

    def visit_f_read(self, stmt: FileReadStmt) -> None:
        pass

    def visit_f_write(self, stmt: FileWriteStmt) -> None:
        pass

    def visit_f_close(self, stmt: FileCloseStmt) -> None:
        pass

    def visit_proc_call(self, stmt: ProcedureCallStmt) -> None:
        procedure_name = stmt.name.value
        line = stmt.name.line
        # Check if the procedure is defined
        if procedure_name not in self.variable_state.procedures:
            raise PseudoUndefinedError(
                f"Procedure {procedure_name} is not defined", self.origin, line
            )

        # Retrieve the procedure statement
        proc = self.variable_state.procedures[procedure_name]

        # Create new scope for procedure parameters
        self.variable_state.push_scope()
        if proc.params is not None:
            # Bind parameters passed to the procedure to the new scope
            for param, proc_param in zip(stmt.args, proc.params):
                param_value = self.visit(param)
                self.variable_state.variables[proc_param[0].value] = (
                    param_value,
                    proc_param[1],
                )

        try:
            # Execute the procedure's statements
            self.visit_statements(proc.body)
        except ReturnException:
            raise PseudoSubroutineError(
                f"Procedure {procedure_name} mustn't has return values",
                self.origin,
                line,
            )
        finally:
            # Restore the previous scope
            self.variable_state.pop_scope()

    def visit_assign(self, stmt: AssignmentStmt) -> None:
        if isinstance(stmt.target, ArrayIndex):
            name = stmt.target.array.token.value
            array_type = self.variable_state.variables[name][1]
            val = self.visit(stmt.value)
            if not self.check_type(val, array_type.type):
                raise PseudoAssignmentError(
                    f"Trying to assign invalid type to array {name}, expected {array_type.type.name}",
                    self.origin,
                    stmt.target.array.token.line,
                )
            indices = [self.visit(indexexp) for indexexp in stmt.target.index]
            ranges = [(self.visit(a), self.visit(b)) for a, b in array_type.ranges]
            try:
                self.variable_state.set_array_value(name, indices, val, ranges)
            except IndexError:
                raise PseudoIndexError(
                    name,
                    indices,
                    ranges,
                    self.origin,
                    stmt.target.array.token.line,
                )
        else:
            name = stmt.target.token.value
            if name not in self.variable_state.variables:
                raise InterpreterError(f"{name} was not declared")
            if name in self.variable_state.constants:
                raise PseudoAssignmentError(
                    f"{name} is a constant, which can't be assigned a value.",
                    self.origin,
                    stmt.target.token.line,
                )
            val = self.visit(stmt.value)
            if self.check_type(val, self.variable_state.variables[name][1]):
                self.variable_state.variables[name] = (
                    val,
                    self.variable_state.variables[name][1],
                )
            else:
                raise PseudoAssignmentError(
                    f"Type Error for assigning {name}, expected {self.variable_state.variables[name][1].name}",
                    self.origin,
                    stmt.target.token.line,
                )

    def visit_program(self, stmt: Program) -> None:
        self.visit_statements(stmt.statements)

    def check_type(self, val, typ):
        if typ == PrimitiveType.INTEGER:
            if type(val) != int and type(val) != float:
                return False
            try:
                val = float(val)
            except:
                return False
            if val % 1:
                return False
            return True
        if typ == PrimitiveType.REAL:
            try:
                val = float(val)
            except:
                return False
            return True
        if typ == PrimitiveType.STRING:
            if isinstance(val, str):
                return True
            else:
                return False
        if typ == PrimitiveType.CHAR:
            if isinstance(val, str) and len(val) == 1:
                return True
            else:
                return False
        if typ == PrimitiveType.BOOLEAN:
            if isinstance(val, bool) or val in [0, 1]:
                return True
            else:
                return False
