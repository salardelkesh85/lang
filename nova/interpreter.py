"""مفسر درخت‌پیما (Tree-Walking Interpreter).

AST نوع‌دار را مستقیماً اجرا می‌کند. از این مفسر برای دو کار استفاده می‌شود:
  * اجرای برنامه‌های متنی (دستور `run`) که تابع main دارند
  * شبیه‌ساز اپلیکیشن در ترمینال (دستور `sim`)

مقادیر زمان اجرا: int, float, bool, str و tuple (برای List؛ چون لیست‌ها تغییرناپذیرند).
"""

import math
import random
import sys

from . import ast as A
from . import runtime as R
from .errors import NovaRuntimeError
from .types import FLOAT, INT, STRING


class Env:
    """محیط (Environment): نگاشت نام به مقدار، با اشاره‌گر به محیط بیرونی."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        self.vars[name] = value

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise KeyError(name)

    def set(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        raise KeyError(name)


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class UIHooks:
    """رابط بین مفسر و شبیه‌ساز برای toast / navigate / back."""

    def toast(self, msg):
        print(f"[toast] {msg}")

    def navigate(self, screen):
        pass

    def back(self):
        pass


class Interpreter:
    def __init__(self, prog, out=None, ui=None, seed=None):
        self.prog = prog
        self.funcs = {f.name: f for f in prog.functions}
        self.globals = Env()
        self.out = out or (lambda s: print(s))
        self.ui = ui or UIHooks()
        self.rng = random.Random(seed)
        self.depth = 0

    def error(self, node, msg):
        return NovaRuntimeError(msg, node.line, node.col)

    def init_globals(self):
        for g in self.prog.globals:
            self.globals.define(g.name, self.value(g.init, self.globals))

    def run_main(self):
        self.init_globals()
        main = self.funcs.get("main")
        if main is None:
            raise NovaRuntimeError("program has no main() function", 1, 1)
        self.call_function(main, [], main)

    # ---------------- دستورها ----------------
    def exec_block(self, block, env):
        for s in block.stmts:
            self.exec(s, env)

    def exec(self, s, env):
        if isinstance(s, A.VarDecl):
            env.define(s.name, self.value(s.init, env))
        elif isinstance(s, A.Assign):
            env.set(s.name, self.value(s.expanded, env))
        elif isinstance(s, A.ExprStmt):
            self.eval(s.expr, env)
        elif isinstance(s, A.If):
            if self.eval(s.cond, env):
                self.exec_block(s.then, Env(env))
            elif isinstance(s.orelse, A.If):
                self.exec(s.orelse, env)
            elif s.orelse is not None:
                self.exec_block(s.orelse, Env(env))
        elif isinstance(s, A.While):
            while self.eval(s.cond, env):
                try:
                    self.exec_block(s.body, Env(env))
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif isinstance(s, A.For):
            for item in self.iterate(s.iterable, env):
                loop_env = Env(env)
                loop_env.define(s.var, item)
                try:
                    self.exec_block(s.body, loop_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif isinstance(s, A.Return):
            raise ReturnSignal(None if s.value is None else self.value(s.value, env))
        elif isinstance(s, A.Break):
            raise BreakSignal()
        elif isinstance(s, A.Continue):
            raise ContinueSignal()
        elif isinstance(s, A.Block):
            self.exec_block(s, Env(env))
        else:
            raise self.error(s, f"cannot execute {type(s).__name__}")

    def iterate(self, it, env):
        if isinstance(it, A.Range):
            start = self.eval(it.start, env)
            end = self.eval(it.end, env)
            return range(start, end + 1 if it.inclusive else end)
        v = self.eval(it, env)
        return list(v)  # tuple یا str (هر کاراکتر یک رشته)

    # ---------------- عبارت‌ها ----------------
    def value(self, e, env):
        """ارزیابی عبارت به‌همراه تبدیل ضمنی (Int -> Float) که checker تعیین کرده است."""
        v = self.eval(e, env)
        if e.coerce_to == FLOAT and isinstance(v, int) and not isinstance(v, bool):
            return float(v)
        return v

    def eval(self, e, env):
        if isinstance(e, (A.IntLit, A.FloatLit, A.BoolLit)):
            return e.value
        if isinstance(e, A.StringLit):
            return "".join(p if isinstance(p, str) else R.to_str(self.value(p, env)) for p in e.parts)
        if isinstance(e, A.ListLit):
            return tuple(self.value(x, env) for x in e.elements)
        if isinstance(e, A.Name):
            return env.get(e.id)
        if isinstance(e, A.Unary):
            v = self.value(e.operand, env)
            if e.op == "not":
                return not v
            return R.wrap32(-v) if e.ty == INT else -v
        if isinstance(e, A.Binary):
            return self.binary(e, env)
        if isinstance(e, A.Index):
            target = self.value(e.target, env)
            i = self.value(e.index, env)
            if not 0 <= i < len(target):
                raise self.error(e, f"index {i} out of bounds for length {len(target)}")
            return target[i]
        if isinstance(e, A.Call):
            return self.call(e, env)
        raise self.error(e, f"cannot evaluate {type(e).__name__}")

    def binary(self, e, env):
        op = e.op
        if op == "and":
            return bool(self.value(e.left, env)) and bool(self.value(e.right, env))
        if op == "or":
            return bool(self.value(e.left, env)) or bool(self.value(e.right, env))
        a = self.value(e.left, env)
        b = self.value(e.right, env)
        if op == "+" and e.ty == STRING:
            return R.to_str(a) + R.to_str(b)
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        if e.ty == INT:
            if op == "+":
                return R.wrap32(a + b)
            if op == "-":
                return R.wrap32(a - b)
            if op == "*":
                return R.wrap32(a * b)
            if op == "/":
                return R.int_div(a, b, e.line, e.col)
            if op == "%":
                return R.int_rem(a, b, e.line, e.col)
        if e.ty == FLOAT:
            a, b = float(a), float(b)
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                return R.float_div(a, b)
            if op == "%":
                return R.float_rem(a, b)
        if op == "+":  # لیست + لیست
            return a + b
        raise self.error(e, f"bad operator {op}")

    def call(self, e, env):
        f = self.funcs.get(e.callee)
        if f is not None:
            args = [self.value(a, env) for a in e.args]
            return self.call_function(f, args, e)
        return self.builtin(e, env)

    def call_function(self, f, args, site):
        env = Env(self.globals)
        for p, v in zip(f.params, args):
            env.define(p.name, v)
        self.depth += 1
        if self.depth > 2000:
            self.depth = 0
            raise self.error(site, "stack overflow (too much recursion)")
        try:
            self.exec_block(f.body, env)
        except ReturnSignal as r:
            return r.value
        finally:
            self.depth -= 1
        return None

    def builtin(self, e, env):
        name = e.callee
        if name == "navigate":
            self.ui.navigate(e.args[0].id)
            return None
        if name == "back":
            self.ui.back()
            return None
        args = [self.value(a, env) for a in e.args]
        if name == "print":
            self.out(R.to_str(args[0]))
            return None
        if name == "toast":
            self.ui.toast(R.to_str(args[0]))
            return None
        if name == "str":
            return R.to_str(args[0])
        if name == "len":
            return len(args[0])
        if name == "int":
            return R.to_int(args[0])
        if name == "float":
            return R.to_float(args[0])
        if name == "remove":
            xs, i = args
            if not 0 <= i < len(xs):
                raise self.error(e, f"index {i} out of bounds for length {len(xs)}")
            return xs[:i] + xs[i + 1:]
        if name == "contains":
            return args[1] in args[0]
        if name == "random":
            lo, hi = args
            if lo > hi:
                raise self.error(e, f"random(): empty range {lo}..{hi}")
            return self.rng.randint(lo, hi)
        if name == "sqrt":
            x = args[0]
            return math.sqrt(x) if x >= 0 else math.nan
        if name == "abs":
            x = args[0]
            return R.wrap32(abs(x)) if e.ty == INT else abs(x)
        if name == "format":
            x, d = args
            if d < 0:
                raise self.error(e, "format(): digits must be >= 0")
            return R.format_fixed(x, d)
        raise self.error(e, f"unknown builtin {name}")


sys.setrecursionlimit(max(sys.getrecursionlimit(), 60000))
