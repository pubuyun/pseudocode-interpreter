# import click
#
# from .interpreter.programs import Program
#
#
# @click.group(invoke_without_command=True)
# @click.pass_context
# def cli(ctx: click.Context):
#     if ctx.invoked_subcommand:
#         return
#
#     click.echo("REPL is under construction")
#
#
# @cli.command()
# @click.argument("file", type=click.File())
# def run(file):
#     code = file.read()
#     code += "\n"
#     program = Program.from_code(code)
#     program.execute()


import sys, os


class SimpleInputStream:
    """A simple input stream"""

    def readline(self):
        try:
            return input() + "\n"
        except EOFError:
            return ""


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if __name__ == "__main__":
    from cambridgeScript.parser.lexer import parse_tokens
    from cambridgeScript.parser.parser import Parser
    from cambridgeScript.interpreter.variables import VariableState
    from cambridgeScript.interpreter.interpreter import Interpreter

    # Read source code
    with open(sys.argv[1], "r") as file:
        code = file.read()

    # Parse code
    tokens = parse_tokens(code)
    parsed = Parser.parse_program(tokens, code)

    # Create interpreter with simple input stream
    interpreter = Interpreter(VariableState(), code, SimpleInputStream())
    interpreter.visit(parsed)
