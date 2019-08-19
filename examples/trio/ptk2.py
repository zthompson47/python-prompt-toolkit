import ast
import sys
import traceback
from functools import partial

import trio
from pygments.styles import get_style_by_name
from pygments.lexers.python import PythonLexer
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit import prompt, HTML, PromptSession

PS1 = HTML("<yellow>>>></yellow> ")
PS2 = HTML("<yellow>...</yellow> ")
STYLE = style_from_pygments_cls(get_style_by_name("monokai"))

_wrap_eval = """async def __wrap(nursery):
    result = {}
    _locals = locals()
    del _locals["nursery"]
    return (_locals, result)
"""

_wrap_exec = """async def __wrap(nursery):
    {}
    _locals = locals()
    del _locals["nursery"]
    return (_locals, None)
"""

class Wrap(object):
    async def main(self):
        session = PromptSession()
        import trio
        async with trio.open_nursery() as nursery:
            try:
                while True:
                    with patch_stdout():
                        code = await trio.to_thread.run_sync(
                            partial(
                                session.prompt, PS1, style=STYLE,
                                lexer=PygmentsLexer(PythonLexer),
                                include_default_pygments_style=False,
                                vi_mode=True
                            )
                        )
                        try:
                            ast_code = ast.parse(code)
                        except SyntaxError as err:
                            if "unexpected EOF" in str(err):
                                while True:
                                    nextline = await trio.to_thread.run_sync(
                                        partial(
                                            session.prompt, PS2, style=STYLE,
                                            lexer=PygmentsLexer(PythonLexer),
                                            include_default_pygments_style=False,
                                            vi_mode=True
                                        )
                                    )
                                    if not nextline:
                                        break
                                    code += "\n    " + nextline
                                try:
                                    ast_code = ast.parse(code)
                                except SyntaxError:
                                    traceback.print_exc()
                                    continue
                            else:
                                traceback.print_exc()
                                continue

                        if not ast_code.body:
                            continue
                        if isinstance(ast_code.body[0], ast.Expr):
                            exec(_wrap_eval.format(code))
                        else:
                            exec(_wrap_exec.format(code))

                        __wrap = locals()['__wrap']
                        try:
                            inner_locals, result = await __wrap(nursery)
                            if result is not None:
                                print(result)
                        except:
                            traceback.print_exc()
                        else:
                            for var, val in inner_locals.items():
                                sys.modules[__name__].__dict__[var] = val

            except (KeyboardInterrupt, EOFError):
                nursery.cancel_scope.cancel()

trio.run(Wrap().main)
