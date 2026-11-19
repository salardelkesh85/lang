"""تحلیلگر معنایی (Semantic Analyzer / Type Checker).

وظایف:
  1. ساخت جدول نمادها (Symbol Table) با حوزه‌های تودرتو (Lexical Scoping)
  2. بررسی نوع همهٔ عبارت‌ها و دستورها و نوشتن نوع روی گره‌ها (expr.ty)
  3. درج تبدیل‌های ضمنی (Int -> Float) با علامت‌گذاری expr.coerce_to
  4. بررسی‌های وابسته به متن: break بیرون حلقه، return در همهٔ مسیرها،
     toast/navigate فقط داخل رویداد دکمه، و ...
"""

from . import ast as A
from .errors import NovaTypeError
from .types import (BOOL, FLOAT, INT, STRING, UNKNOWN, VOID, ListType,
                    has_unknown, is_numeric, join)

# توابع داخلی (Built-in). امضای آن‌ها به‌صورت ویژه در check_builtin بررسی می‌شود.
BUILTINS = {
    "print", "len", "str", "int", "float", "remove", "contains",
    "random", "sqrt", "abs", "format", "toast", "navigate", "back",
}
ACTION_ONLY = {"toast", "navigate", "back"}


class Symbol:
    def __init__(self, name, type_, mutable, kind):
        self.name = name
        self.type = type_
        self.mutable = mutable
        self.kind = kind  # global | local | param | loop | state


class Checker:
    def __init__(self):
        self.scopes = []
        self.funcs = {}
        self.screens = {}
        self.fun_ret = None
        self.loop_depth = 0
        self.in_action = False
        self.current_screen = None

    def error(self, node, msg):
        return NovaTypeError(msg, node.line, node.col)

    # ---------------- جدول نمادها ----------------
    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def declare(self, node, name, type_, mutable, kind):
        scope = self.scopes[-1]
        if name in scope:
            raise self.error(node, f"'{name}' is already declared in this scope")
        if name in self.screens and self.current_screen is not None:
            raise self.error(node, f"'{name}' conflicts with a screen name")
        scope[name] = Symbol(name, type_, mutable, kind)

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # ---------------- برنامه ----------------
    def check_program(self, prog):
        # گذر اول: جمع‌آوری امضای توابع و نام صفحه‌ها (برای ارجاع پیش‌رو)
        for f in prog.functions:
            if f.name in BUILTINS:
                raise self.error(f, f"cannot redefine built-in function '{f.name}'")
            names = set()
            for p in f.params:
                if p.name in names:
                    raise self.error(p, f"duplicate parameter '{p.name}'")
                names.add(p.name)
            self.funcs[f.name] = f
        if "main" in self.funcs:
            m = self.funcs["main"]
            if m.params or m.ret != VOID:
                raise self.error(m, "main() must take no parameters and return nothing")
        if prog.app:
            for s in prog.app.screens:
                if s.name in self.screens:
                    raise self.error(s, f"screen '{s.name}' is already defined")
                self.screens[s.name] = s

        # گذر دوم: متغیرهای سراسری، بدنهٔ توابع، صفحه‌ها
        self.push()
        for g in prog.globals:
            self.var_decl(g, "global")
        for f in prog.functions:
            self.function(f)
        if prog.app:
            for s in prog.app.screens:
                self.screen(s)
        self.pop()
        return prog

    def function(self, f):
        self.push()
        for p in f.params:
            self.declare(p, p.name, p.type, False, "param")
        self.fun_ret = f.ret
        self.block(f.body, new_scope=False)
        if f.ret != VOID and not returns(f.body):
            raise self.error(f, f"function '{f.name}' must return a value of type {f.ret} on every path")
        self.fun_ret = None
        self.pop()

    # ---------------- صفحه و رابط کاربری ----------------
    def screen(self, s):
        self.current_screen = s
        self.push()
        for st in s.states:
            t = self.typed_init(st, st.type_ann, st.init, f"state '{st.name}'")
            st.type = t
            self.declare(st, st.name, t, True, "state")
        self.ui_nodes(s.body)
        self.pop()
        self.current_screen = None

    def ui_nodes(self, nodes):
        for n in nodes:
            self.ui_node(n)

    def ui_node(self, n):
        if isinstance(n, A.UIIf):
            self.condition(n.cond)
            self.push(); self.ui_nodes(n.then); self.pop()
            if n.orelse:
                self.push(); self.ui_nodes(n.orelse); self.pop()
            return
        if isinstance(n, A.UIFor):
            self.push()
            elem = self.iterable(n.iterable)
            self.declare(n, n.var, elem, False, "loop")
            self.ui_nodes(n.body)
            self.pop()
            return
        k, args = n.kind, n.args

        def arity(lo, hi):
            if not lo <= len(args) <= hi:
                exp = str(lo) if lo == hi else f"{lo} to {hi}"
                raise self.error(n, f"'{k}' expects {exp} argument(s), got {len(args)}")

        if k in ("column", "row", "divider"):
            arity(0, 0)
        elif k in ("text", "title"):
            arity(1, 2 if k == "text" else 1)
            self.expr(args[0])
            if len(args) == 2:
                self.expect_type(args[1], INT, "font size")
        elif k == "button":
            arity(1, 1)
            self.expr(args[0])
            saved = self.in_action
            self.in_action = True
            self.block(n.action)
            self.in_action = saved
        elif k in ("input", "checkbox"):
            arity(1, 2)
            want = STRING if k == "input" else BOOL
            target = args[0]
            sym = self.lookup(target.id) if isinstance(target, A.Name) else None
            if sym is None or sym.kind != "state":
                raise self.error(target, f"first argument of '{k}' must be a state variable")
            if sym.type != want:
                raise self.error(target, f"'{k}' needs a {want} state, but '{target.id}' is {sym.type}")
            target.ty = sym.type
            if len(args) == 2:
                self.expr(args[1])
        elif k == "spacer":
            arity(0, 1)
            if args:
                self.expect_type(args[0], INT, "spacer size")
        if n.children is not None:
            self.push(); self.ui_nodes(n.children); self.pop()

    # ---------------- دستورها ----------------
    def block(self, b, new_scope=True):
        if new_scope:
            self.push()
        for s in b.stmts:
            self.stmt(s)
        if new_scope:
            self.pop()

    def stmt(self, s):
        if isinstance(s, A.VarDecl):
            self.var_decl(s, "local")
        elif isinstance(s, A.Assign):
            self.assign(s)
        elif isinstance(s, A.If):
            self.condition(s.cond)
            self.block(s.then)
            if isinstance(s.orelse, A.If):
                self.stmt(s.orelse)
            elif s.orelse:
                self.block(s.orelse)
        elif isinstance(s, A.While):
            self.condition(s.cond)
            self.loop_depth += 1
            self.block(s.body)
            self.loop_depth -= 1
        elif isinstance(s, A.For):
            self.push()
            elem = self.iterable(s.iterable)
            self.declare(s, s.var, elem, False, "loop")
            self.loop_depth += 1
            self.block(s.body)
            self.loop_depth -= 1
            self.pop()
        elif isinstance(s, A.Return):
            if self.fun_ret is None:
                raise self.error(s, "'return' outside of a function")
            if s.value is None:
                if self.fun_ret != VOID:
                    raise self.error(s, f"missing return value of type {self.fun_ret}")
            else:
                if self.fun_ret == VOID:
                    raise self.error(s, "this function returns nothing (Void) but a value is returned")
                self.expr(s.value)
                self.coerce(s.value, self.fun_ret, "return value")
        elif isinstance(s, (A.Break, A.Continue)):
            if self.loop_depth == 0:
                word = "break" if isinstance(s, A.Break) else "continue"
                raise self.error(s, f"'{word}' outside of a loop")
        elif isinstance(s, A.ExprStmt):
            self.expr(s.expr, allow_void=True)
        elif isinstance(s, A.Block):
            self.block(s)
        else:
            raise self.error(s, f"unknown statement {type(s).__name__}")

    def var_decl(self, d, kind):
        t = self.typed_init(d, d.type_ann, d.init, f"variable '{d.name}'")
        d.type = t
        self.declare(d, d.name, t, d.mutable, kind)

    def typed_init(self, node, ann, init, what):
        self.expr(init)
        if ann is not None:
            self.coerce(init, ann, what)
            return ann
        if has_unknown(init.ty):
            raise self.error(init, f"cannot infer the type of {what}; add a type, e.g. ': List<Int>'")
        return init.ty

    def assign(self, s):
        sym = self.lookup(s.name)
        if sym is None:
            raise self.error(s, f"undefined variable '{s.name}'")
        if not sym.mutable:
            what = {"loop": "loop variable", "param": "parameter"}.get(sym.kind, "constant (declared with 'let')")
            raise self.error(s, f"cannot assign to '{s.name}': it is a {what}")
        if sym.kind == "state" and not self.in_action:
            raise self.error(s, f"state '{s.name}' can only be changed inside a button action")
        if s.op == "=":
            value = s.value
            self.expr(value)
        else:
            # x += v  ==>  x = x + v
            target = A.Name(s.line, s.col, s.name)
            value = A.Binary(s.line, s.col, s.op[0], target, s.value)
            self.expr(value)
        self.coerce(value, sym.type, f"variable '{s.name}'")
        s.expanded = value

    def condition(self, e):
        self.expect_type(e, BOOL, "condition")

    def iterable(self, it):
        """نوع متغیر حلقه را برمی‌گرداند."""
        if isinstance(it, A.Range):
            self.expect_type(it.start, INT, "range start")
            self.expect_type(it.end, INT, "range end")
            return INT
        t = self.expr(it)
        if isinstance(t, ListType):
            if t.elem == UNKNOWN:
                raise self.error(it, "cannot loop over an empty list literal")
            return t.elem
        if t == STRING:
            return STRING
        raise self.error(it, f"cannot loop over a value of type {t} (use a List, String or a range like 0..10)")

    # ---------------- تبدیل نوع ----------------
    def expect_type(self, e, t, what):
        self.expr(e)
        self.coerce(e, t, what)

    def coerce(self, e, target, what):
        src = e.ty
        if src == target:
            return
        if target == FLOAT and src == INT:
            e.coerce_to = FLOAT
            return
        if isinstance(target, ListType) and isinstance(e, A.ListLit):
            for el in e.elements:
                self.coerce(el, target.elem, what)
            e.ty = target
            return
        if isinstance(target, ListType) and isinstance(src, ListType) and has_unknown(src) and \
                join(src, target) == target and not isinstance(e, A.Name):
            # مثل [] + [] یا remove([], 0): نوع را از مقصد می‌گیریم
            set_list_type(e, target)
            return
        raise self.error(e, f"type mismatch for {what}: expected {target}, got {src}")

    # ---------------- عبارت‌ها ----------------
    def expr(self, e, allow_void=False):
        t = self._expr(e)
        e.ty = t
        if t == VOID and not allow_void:
            raise self.error(e, "this call returns nothing (Void) and cannot be used as a value")
        return t

    def _expr(self, e):
        if isinstance(e, A.IntLit):
            return INT
        if isinstance(e, A.FloatLit):
            return FLOAT
        if isinstance(e, A.BoolLit):
            return BOOL
        if isinstance(e, A.StringLit):
            for p in e.parts:
                if not isinstance(p, str):
                    self.expr(p)
            return STRING
        if isinstance(e, A.ListLit):
            t = UNKNOWN
            for el in e.elements:
                et = self.expr(el)
                j = join(t, et)
                if j is None:
                    raise self.error(el, f"list elements must have the same type ({t} vs {et})")
                t = j
            for el in e.elements:
                self.coerce(el, t, "list element")
            return ListType(t)
        if isinstance(e, A.Name):
            sym = self.lookup(e.id)
            if sym is None:
                if e.id in self.screens:
                    raise self.error(e, f"screen '{e.id}' can only be used with navigate()")
                if e.id in self.funcs or e.id in BUILTINS:
                    raise self.error(e, f"'{e.id}' is a function; call it with ()")
                raise self.error(e, f"undefined variable '{e.id}'")
            return sym.type
        if isinstance(e, A.Unary):
            t = self.expr(e.operand)
            if e.op == "-":
                if not is_numeric(t):
                    raise self.error(e, f"unary '-' needs a number, got {t}")
                return t
            if t != BOOL:
                raise self.error(e, f"'not' needs a Bool, got {t}")
            return BOOL
        if isinstance(e, A.Binary):
            return self.binary(e)
        if isinstance(e, A.Index):
            t = self.expr(e.target)
            self.expect_type(e.index, INT, "index")
            if isinstance(t, ListType):
                if t.elem == UNKNOWN:
                    raise self.error(e, "cannot index an empty list literal")
                return t.elem
            if t == STRING:
                return STRING
            raise self.error(e, f"cannot index a value of type {t}")
        if isinstance(e, A.Call):
            return self.call(e)
        raise self.error(e, f"unknown expression {type(e).__name__}")

    def binary(self, e):
        op = e.op
        lt = self.expr(e.left)
        rt = self.expr(e.right)
        if op in ("and", "or"):
            if lt != BOOL or rt != BOOL:
                raise self.error(e, f"'{op}' needs Bool operands, got {lt} and {rt}")
            return BOOL
        if op == "+" and (lt == STRING or rt == STRING):
            return STRING
        if op in ("+", "-", "*", "/", "%"):
            if is_numeric(lt) and is_numeric(rt):
                return join(lt, rt)
            if op == "+" and isinstance(lt, ListType) and isinstance(rt, ListType):
                j = join(lt, rt)
                if j is None or (lt != rt and not has_unknown(lt) and not has_unknown(rt)):
                    raise self.error(e, f"cannot concatenate {lt} and {rt}")
                if not has_unknown(j):
                    self.coerce(e.left, j, "list")
                    self.coerce(e.right, j, "list")
                return j
            raise self.error(e, f"operator '{op}' cannot be applied to {lt} and {rt}")
        if op in ("<", "<=", ">", ">="):
            if (is_numeric(lt) and is_numeric(rt)) or (lt == STRING and rt == STRING):
                return BOOL
            raise self.error(e, f"cannot compare {lt} and {rt} with '{op}'")
        if op in ("==", "!="):
            j = join(lt, rt)
            if j is None:
                raise self.error(e, f"cannot compare {lt} and {rt} with '{op}'")
            if j == FLOAT or (isinstance(j, ListType) and not has_unknown(j)):
                self.coerce(e.left, j, "comparison")
                self.coerce(e.right, j, "comparison")
            return BOOL
        raise self.error(e, f"unknown operator {op}")

    def call(self, e):
        if e.callee in BUILTINS:
            if e.callee in ACTION_ONLY and not self.in_action:
                raise self.error(e, f"'{e.callee}()' can only be used inside a button action")
            return self.builtin(e)
        f = self.funcs.get(e.callee)
        if f is None:
            if e.callee in self.screens:
                raise self.error(e, f"'{e.callee}' is a screen; use navigate({e.callee})")
            raise self.error(e, f"undefined function '{e.callee}'")
        if len(e.args) != len(f.params):
            raise self.error(e, f"'{f.name}' expects {len(f.params)} argument(s), got {len(e.args)}")
        for a, p in zip(e.args, f.params):
            self.expect_type(a, p.type, f"parameter '{p.name}' of '{f.name}'")
        return f.ret

    def builtin(self, e):
        name, args = e.callee, e.args

        def arity(n):
            if len(args) != n:
                raise self.error(e, f"'{name}' expects {n} argument(s), got {len(args)}")

        if name == "navigate":
            arity(1)
            a = args[0]
            if not isinstance(a, A.Name) or a.id not in self.screens:
                raise self.error(a, "navigate() needs a screen name, e.g. navigate(Settings)")
            return VOID
        if name == "back":
            arity(0)
            return VOID
        if name in ("print", "toast"):
            arity(1)
            self.expr(args[0])
            return VOID
        if name == "str":
            arity(1)
            self.expr(args[0])
            return STRING
        if name == "len":
            arity(1)
            t = self.expr(args[0])
            if not (t == STRING or isinstance(t, ListType)):
                raise self.error(args[0], f"len() needs a String or List, got {t}")
            return INT
        if name in ("int", "float"):
            arity(1)
            t = self.expr(args[0])
            if t not in (INT, FLOAT, STRING):
                raise self.error(args[0], f"{name}() needs Int, Float or String, got {t}")
            return INT if name == "int" else FLOAT
        if name == "remove":
            arity(2)
            t = self.expr(args[0])
            if not isinstance(t, ListType):
                raise self.error(args[0], f"remove() needs a List, got {t}")
            self.expect_type(args[1], INT, "index")
            return t
        if name == "contains":
            arity(2)
            t = self.expr(args[0])
            if t == STRING:
                self.expect_type(args[1], STRING, "substring")
            elif isinstance(t, ListType):
                if t.elem == UNKNOWN:
                    raise self.error(args[0], "cannot search an empty list literal")
                self.expect_type(args[1], t.elem, "element")
            else:
                raise self.error(args[0], f"contains() needs a List or String, got {t}")
            return BOOL
        if name == "random":
            arity(2)
            self.expect_type(args[0], INT, "lower bound")
            self.expect_type(args[1], INT, "upper bound")
            return INT
        if name == "sqrt":
            arity(1)
            self.expect_type(args[0], FLOAT, "sqrt argument")
            return FLOAT
        if name == "abs":
            arity(1)
            t = self.expr(args[0])
            if not is_numeric(t):
                raise self.error(args[0], f"abs() needs a number, got {t}")
            return t
        if name == "format":
            arity(2)
            self.expect_type(args[0], FLOAT, "number")
            self.expect_type(args[1], INT, "digits")
            return STRING
        raise self.error(e, f"unknown builtin {name}")


def set_list_type(e, target):
    e.ty = target
    if isinstance(e, A.ListLit):
        for el in e.elements:
            set_list_type(el, target.elem) if isinstance(target.elem, ListType) else None
    elif isinstance(e, A.Binary):
        set_list_type(e.left, target)
        set_list_type(e.right, target)
    elif isinstance(e, A.Call) and e.callee == "remove":
        set_list_type(e.args[0], target)


def returns(node):
    """آیا اجرای این دستور در همهٔ مسیرها به return می‌رسد؟ (تحلیل جریان کنترل)"""
    if isinstance(node, A.Return):
        return True
    if isinstance(node, A.Block):
        return any(returns(s) for s in node.stmts)
    if isinstance(node, A.If):
        return node.orelse is not None and returns(node.then) and returns(node.orelse)
    return False


def check(prog):
    return Checker().check_program(prog)
