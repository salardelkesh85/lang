"""شبیه‌ساز اپلیکیشن در ترمینال.

همان مدل Jetpack Compose را تقلید می‌کند:
  * هر صفحه state خودش را دارد
  * بعد از هر رویداد (کلیک، تایپ) کل صفحه دوباره «ترسیم» (recompose) می‌شود
  * navigate صفحهٔ جدیدی روی پشته می‌گذارد و back آن را برمی‌دارد

عناصر تعاملی شماره می‌گیرند؛ کاربر با وارد کردن شماره روی آن‌ها «کلیک» می‌کند.
"""

from . import ast as A
from . import runtime as R
from .errors import NovaRuntimeError
from .interpreter import Env, Interpreter, UIHooks


class ScreenInstance:
    def __init__(self, decl, env):
        self.decl = decl
        self.env = env


class Widget:
    def __init__(self, kind, text="", children=None, action=None, env=None, state=None, value=None):
        self.kind = kind
        self.text = text
        self.children = children or []
        self.action = action
        self.env = env
        self.state = state
        self.value = value
        self.index = None


class Simulator(UIHooks):
    def __init__(self, prog, out=print, seed=None):
        self.prog = prog
        self.app = prog.app
        self.screens = {s.name: s for s in self.app.screens}
        self.out = out
        self.interp = Interpreter(prog, out=lambda s: out(f"[print] {s}"), ui=self, seed=seed)
        self.interp.init_globals()
        self.stack = []
        self.pending = []
        self.messages = []
        self.finished = False
        self.push_screen(self.app.screens[0].name)

    # ---------- رابط UIHooks ----------
    def toast(self, msg):
        self.messages.append(f"[toast] {msg}")

    def navigate(self, name):
        self.pending.append(("push", name))

    def back(self):
        self.pending.append(("pop", None))

    # ---------- مدیریت صفحه‌ها ----------
    def push_screen(self, name):
        decl = self.screens[name]
        env = Env(self.interp.globals)
        for st in decl.states:
            env.define(st.name, self.interp.value(st.init, env))
        self.stack.append(ScreenInstance(decl, env))

    def apply_navigation(self):
        for kind, name in self.pending:
            if kind == "push":
                self.push_screen(name)
            elif len(self.stack) > 1:
                self.stack.pop()
            else:
                self.finished = True
        self.pending = []

    @property
    def current(self):
        return self.stack[-1]

    # ---------- ساخت درخت ویجت‌ها (composition) ----------
    def compose(self):
        root = Widget("column", children=self.build(self.current.decl.body, self.current.env))
        interactive = []

        def number(w):
            if w.kind in ("button", "input", "checkbox"):
                interactive.append(w)
                w.index = len(interactive)
            for c in w.children:
                number(c)

        number(root)
        return root, interactive

    def build(self, nodes, env):
        out = []
        it = self.interp
        for n in nodes:
            if isinstance(n, A.UIIf):
                branch = n.then if it.value(n.cond, env) else (n.orelse or [])
                out.extend(self.build(branch, Env(env)))
            elif isinstance(n, A.UIFor):
                for item in it.iterate(n.iterable, env):
                    e = Env(env)
                    e.define(n.var, item)
                    out.extend(self.build(n.body, e))
            else:
                k = n.kind
                if k in ("column", "row"):
                    out.append(Widget(k, children=self.build(n.children, Env(env))))
                elif k in ("text", "title"):
                    out.append(Widget(k, R.to_str(it.value(n.args[0], env))))
                elif k == "button":
                    out.append(Widget(k, R.to_str(it.value(n.args[0], env)), action=n.action, env=env))
                elif k == "input":
                    hint = R.to_str(it.value(n.args[1], env)) if len(n.args) > 1 else ""
                    name = n.args[0].id
                    out.append(Widget(k, hint, env=env, state=name, value=env.get(name)))
                elif k == "checkbox":
                    label = R.to_str(it.value(n.args[1], env)) if len(n.args) > 1 else ""
                    name = n.args[0].id
                    out.append(Widget(k, label, env=env, state=name, value=env.get(name)))
                elif k == "spacer":
                    out.append(Widget(k))
                elif k == "divider":
                    out.append(Widget(k))
        return out

    # ---------- نمایش ----------
    def render_lines(self, w, indent=0):
        pad = "  " * indent
        k = w.kind
        if k == "column":
            lines = []
            for c in w.children:
                lines.extend(self.render_lines(c, indent))
            return lines
        if k == "row":
            parts = [" ".join(l.strip() for l in self.render_lines(c)) for c in w.children]
            return [pad + "   ".join(p for p in parts if p)]
        if k == "title":
            return [pad + f"== {w.text} =="]
        if k == "text":
            return [pad + w.text]
        if k == "button":
            return [pad + f"[{w.index}: {w.text}]"]
        if k == "input":
            hint = f" ({w.text})" if w.text else ""
            return [pad + f"[{w.index}: input{hint}] \"{w.value}\""]
        if k == "checkbox":
            mark = "x" if w.value else " "
            return [pad + f"[{w.index}: ({mark}) {w.text}]"]
        if k == "spacer":
            return [""]
        if k == "divider":
            return [pad + "-" * 30]
        return []

    def render(self):
        root, interactive = self.compose()
        title = f" {self.app.title} > {self.current.decl.name} "
        width = 40
        lines = ["+" + title.center(width, "-") + "+"]
        for l in self.render_lines(root):
            lines.append("| " + l)
        lines.append("+" + "-" * width + "+")
        for m in self.messages:
            lines.append(m)
        self.messages = []
        self.out("\n".join(lines))
        return interactive

    # ---------- رویدادها ----------
    def handle(self, command, interactive, ask_text=None):
        """یک رویداد را اجرا می‌کند. فرمت: '2' برای کلیک، '3=متن' برای ورودی، 'back'."""
        command = command.strip()
        if command in ("q", "quit", "exit"):
            self.finished = True
            return
        if command == "back":
            self.back()
            self.apply_navigation()
            return
        text = None
        if "=" in command:
            command, text = command.split("=", 1)
        try:
            idx = int(command)
            if idx < 1:
                raise IndexError
            w = interactive[idx - 1]
        except (ValueError, IndexError):
            self.out(f"? unknown command '{command}' (enter a number, 'back' or 'q')")
            return
        self.out(f">>> {w.kind} {idx}" + (f" = {text!r}" if text is not None else ""))
        if w.kind == "button":
            try:
                self.interp.exec_block(w.action, Env(w.env))
            except NovaRuntimeError as err:
                self.out(f"!!! {err}")
        elif w.kind == "input":
            if text is None:
                text = ask_text(f"{w.text or w.state}: ") if ask_text else ""
            w.env.set(w.state, text)
        elif w.kind == "checkbox":
            w.env.set(w.state, not w.value)
        self.apply_navigation()

    def run_script(self, events):
        interactive = self.render()
        for ev in events:
            self.handle(ev, interactive)
            if self.finished:
                break
            interactive = self.render()

    def run_interactive(self):
        self.out("Nova simulator: enter an element number to click it, 'back' to go back, 'q' to quit")
        while not self.finished:
            interactive = self.render()
            try:
                cmd = input("> ")
            except EOFError:
                break
            self.handle(cmd, interactive, ask_text=input)
