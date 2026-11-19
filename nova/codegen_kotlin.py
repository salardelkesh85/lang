"""تولید کد Kotlin (و Jetpack Compose) از AST نوع‌دار.

نگاشت انواع:  Int->Int  Float->Double  Bool->Boolean  String->String
             List<T>->List<T>  Void->Unit

برای خوانایی، عبارت‌ها با رعایت اولویت عملگرهای Kotlin تولید می‌شوند
و فقط جایی که لازم است پرانتز گذاشته می‌شود.
"""

from . import ast as A
from .types import BOOL, FLOAT, INT, STRING, UNKNOWN, VOID, ListType

KOTLIN_HARD_KEYWORDS = {
    "as", "break", "class", "continue", "do", "else", "false", "for", "fun", "if",
    "in", "interface", "is", "null", "object", "package", "return", "super", "this",
    "throw", "true", "try", "typealias", "typeof", "val", "var", "when", "while",
}

# نام‌هایی که در کد تولیدی استفاده می‌شوند؛ شناسه‌های کاربر با این نام‌ها تغییر نام می‌دهند
GENERATED_NAMES = {
    "Text", "Button", "Column", "Row", "Spacer", "Checkbox", "OutlinedTextField",
    "HorizontalDivider", "MaterialTheme", "Surface", "Modifier", "Alignment",
    "Arrangement", "Toast", "MainActivity", "NovaApp", "Math", "println", "listOf",
    "emptyList", "run", "context", "navigate", "back", "it", "stack", "holder",
    "remember", "rememberSaveable", "mutableStateOf", "Unit", "Int", "Double",
    "Boolean", "String", "List", "Regex", "Bundle",
}

# اولویت عملگرها در Kotlin (عدد بزرگ‌تر = اولویت بالاتر)
P_OR, P_AND, P_EQ, P_CMP, P_ADD, P_MUL, P_PREFIX, P_POSTFIX, P_ATOM = 1, 2, 3, 4, 6, 7, 8, 9, 10
BIN_PREC = {
    "or": P_OR, "and": P_AND, "==": P_EQ, "!=": P_EQ,
    "<": P_CMP, "<=": P_CMP, ">": P_CMP, ">=": P_CMP,
    "+": P_ADD, "-": P_ADD, "*": P_MUL, "/": P_MUL, "%": P_MUL,
}
KOTLIN_OP = {"and": "&&", "or": "||"}


def kotlin_type(t):
    if t == INT:
        return "Int"
    if t == FLOAT:
        return "Double"
    if t == BOOL:
        return "Boolean"
    if t == STRING:
        return "String"
    if t == VOID:
        return "Unit"
    if isinstance(t, ListType):
        return f"List<{kotlin_type(t.elem)}>"
    if t == UNKNOWN:
        return "Nothing"
    raise ValueError(t)


def kotlin_string(s):
    out = []
    for c in s:
        if c == "\\":
            out.append("\\\\")
        elif c == '"':
            out.append('\\"')
        elif c == "$":
            out.append("\\$")
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        else:
            out.append(c)
    return "".join(out)


def float_literal(v):
    s = repr(float(v))
    if "e" in s and "." not in s.split("e")[0]:
        s = s.replace("e", ".0e")
    return s


class KotlinGen:
    def __init__(self, prog):
        self.prog = prog
        self.lines = []
        self.level = 0
        self.reserved = set(GENERATED_NAMES)
        if prog.app:
            self.reserved |= {f"{s.name}Screen" for s in prog.app.screens}

    # ---------------- ابزارها ----------------
    def emit(self, line=""):
        self.lines.append(("    " * self.level + line) if line else "")

    def name(self, n):
        if n in KOTLIN_HARD_KEYWORDS:
            return f"`{n}`"
        if n in self.reserved:
            return n + "_"
        return n

    def text(self):
        return "\n".join(self.lines) + "\n"

    # ---------------- عبارت‌ها ----------------
    def expr(self, e):
        """کد Kotlin عبارت را همراه با تبدیل ضمنی برمی‌گرداند."""
        code, prec = self.raw(e)
        if e.coerce_to == FLOAT and e.ty == INT:
            if isinstance(e, A.IntLit):
                return f"{e.value}.0", P_ATOM if e.value >= 0 else P_PREFIX
            return f"{self.wrap(code, prec, P_POSTFIX)}.toDouble()", P_POSTFIX
        return code, prec

    def code(self, e):
        return self.expr(e)[0]

    @staticmethod
    def wrap(code, prec, need):
        return f"({code})" if prec < need else code

    def sub(self, e, need):
        code, prec = self.expr(e)
        return self.wrap(code, prec, need)

    def raw(self, e):
        if isinstance(e, A.IntLit):
            return str(e.value), (P_ATOM if e.value >= 0 else P_PREFIX)
        if isinstance(e, A.FloatLit):
            return float_literal(e.value), (P_ATOM if e.value >= 0 else P_PREFIX)
        if isinstance(e, A.BoolLit):
            return ("true" if e.value else "false"), P_ATOM
        if isinstance(e, A.StringLit):
            return self.string(e), P_ATOM
        if isinstance(e, A.ListLit):
            t = e.ty.elem
            if not e.elements:
                return f"emptyList<{kotlin_type(t)}>()", P_POSTFIX
            items = ", ".join(self.code(x) for x in e.elements)
            return f"listOf<{kotlin_type(t)}>({items})", P_POSTFIX
        if isinstance(e, A.Name):
            return self.name(e.id), P_ATOM
        if isinstance(e, A.Unary):
            op = "!" if e.op == "not" else "-"
            operand = self.sub(e.operand, P_PREFIX)
            if op == "-" and operand.startswith("-"):
                operand = f"({operand})"
            return f"{op}{operand}", P_PREFIX
        if isinstance(e, A.Binary):
            return self.binary(e)
        if isinstance(e, A.Index):
            target = self.sub(e.target, P_POSTFIX)
            code = f"{target}[{self.code(e.index)}]"
            if e.target.ty == STRING:
                return f"{code}.toString()", P_POSTFIX
            return code, P_POSTFIX
        if isinstance(e, A.Call):
            return self.call(e)
        raise ValueError(f"cannot generate {type(e).__name__}")

    def string(self, e):
        out = []
        for p in e.parts:
            if isinstance(p, str):
                out.append(kotlin_string(p))
            else:
                out.append("${" + self.code(p) + "}")
        return '"' + "".join(out) + '"'

    def binary(self, e):
        op = e.op
        prec = BIN_PREC[op]
        if op == "+" and e.ty == STRING:
            left = self.sub(e.left, prec)
            if e.left.ty != STRING:
                left = f"nv_str({self.code(e.left)})"
            return f"{left} + {self.sub(e.right, prec + 1)}", prec
        kop = KOTLIN_OP.get(op, op)
        left = self.sub(e.left, prec)
        right = self.sub(e.right, prec + 1)
        if prec in (P_EQ, P_CMP):  # مقایسه‌ها در Nova زنجیره نمی‌شوند
            left = self.sub(e.left, P_ADD)
            right = self.sub(e.right, P_ADD)
        return f"{left} {kop} {right}", prec

    def call(self, e):
        n, args = e.callee, e.args
        if n == "print":
            return f"println({self.code(args[0])})", P_POSTFIX
        if n == "str":
            return f"nv_str({self.code(args[0])})", P_POSTFIX
        if n == "len":
            prop = "length" if args[0].ty == STRING else "size"
            return f"{self.sub(args[0], P_POSTFIX)}.{prop}", P_POSTFIX
        if n == "int":
            t = args[0].ty
            if t == INT:
                return self.expr(args[0])
            if t == FLOAT:
                return f"{self.sub(args[0], P_POSTFIX)}.toInt()", P_POSTFIX
            return f"nv_parseInt({self.code(args[0])})", P_POSTFIX
        if n == "float":
            t = args[0].ty
            if t == FLOAT:
                return self.expr(args[0])
            if t == INT:
                if isinstance(args[0], A.IntLit):
                    return f"{args[0].value}.0", P_ATOM
                return f"{self.sub(args[0], P_POSTFIX)}.toDouble()", P_POSTFIX
            return f"nv_parseFloat({self.code(args[0])})", P_POSTFIX
        if n == "remove":
            return f"nv_remove({self.code(args[0])}, {self.code(args[1])})", P_POSTFIX
        if n == "contains":
            return f"{self.sub(args[0], P_POSTFIX)}.contains({self.code(args[1])})", P_POSTFIX
        if n == "random":
            return f"nv_random({self.code(args[0])}, {self.code(args[1])})", P_POSTFIX
        if n == "sqrt":
            return f"Math.sqrt({self.code(args[0])})", P_POSTFIX
        if n == "abs":
            return f"Math.abs({self.code(args[0])})", P_POSTFIX
        if n == "format":
            return f"nv_format({self.code(args[0])}, {self.code(args[1])})", P_POSTFIX
        if n == "toast":
            msg = self.code(args[0]) if args[0].ty == STRING else f"nv_str({self.code(args[0])})"
            return f"Toast.makeText(context, {msg}, Toast.LENGTH_SHORT).show()", P_POSTFIX
        if n == "navigate":
            return f'navigate("{args[0].id}")', P_POSTFIX
        if n == "back":
            return "back()", P_POSTFIX
        params = ", ".join(self.code(a) for a in args)
        return f"{self.name(n)}({params})", P_POSTFIX

    # ---------------- دستورها ----------------
    def block_body(self, block):
        self.level += 1
        for s in block.stmts:
            self.stmt(s)
        self.level -= 1

    def stmt(self, s):
        if isinstance(s, A.VarDecl):
            kw = "var" if s.mutable else "val"
            self.emit(f"{kw} {self.name(s.name)}: {kotlin_type(s.type)} = {self.code(s.init)}")
        elif isinstance(s, A.Assign):
            target = self.name(s.name)
            if s.op == "=":
                self.emit(f"{target} = {self.code(s.expanded)}")
            else:
                self.emit(f"{target} {s.op} {self.code(s.value)}")
        elif isinstance(s, A.ExprStmt):
            self.emit(self.code(s.expr))
        elif isinstance(s, A.If):
            self.if_chain(s)
        elif isinstance(s, A.While):
            self.emit(f"while ({self.code(s.cond)}) {{")
            self.block_body(s.body)
            self.emit("}")
        elif isinstance(s, A.For):
            self.emit(f"for ({self.name(s.var)} in {self.iterable(s.iterable)}) {{")
            self.block_body(s.body)
            self.emit("}")
        elif isinstance(s, A.Return):
            self.emit("return" if s.value is None else f"return {self.code(s.value)}")
        elif isinstance(s, A.Break):
            self.emit("break")
        elif isinstance(s, A.Continue):
            self.emit("continue")
        elif isinstance(s, A.Block):
            self.emit("run {")
            self.block_body(s)
            self.emit("}")
        else:
            raise ValueError(f"cannot generate {type(s).__name__}")

    def if_chain(self, s, prefix=""):
        self.emit(f"{prefix}if ({self.code(s.cond)}) {{")
        self.block_body(s.then)
        if isinstance(s.orelse, A.If):
            self.if_chain(s.orelse, prefix="} else ")
            return
        if s.orelse is not None:
            self.emit("} else {")
            self.block_body(s.orelse)
        self.emit("}")

    def iterable(self, it):
        if isinstance(it, A.Range):
            op = ".." if it.inclusive else " until "
            return f"{self.sub(it.start, P_ADD)}{op}{self.sub(it.end, P_ADD)}"
        if it.ty == STRING:
            return f"{self.sub(it, P_POSTFIX)}.map {{ it.toString() }}"
        return self.code(it)

    # ---------------- اعلان‌ها ----------------
    def program_decls(self):
        for g in self.prog.globals:
            kw = "var" if g.mutable else "val"
            self.emit(f"{kw} {self.name(g.name)}: {kotlin_type(g.type)} = {self.code(g.init)}")
        if self.prog.globals:
            self.emit()
        for f in self.prog.functions:
            params = ", ".join(f"{self.name(p.name)}: {kotlin_type(p.type)}" for p in f.params)
            ret = "" if f.ret == VOID else f": {kotlin_type(f.ret)}"
            self.emit(f"fun {self.name(f.name)}({params}){ret} {{")
            self.block_body(f.body)
            self.emit("}")
            self.emit()

    # ---------------- رابط کاربری (Jetpack Compose) ----------------
    def screen(self, s):
        self.emit("@Composable")
        self.emit(f"fun {s.name}Screen(navigate: (String) -> Unit, back: () -> Unit) {{")
        self.level += 1
        self.emit("val context = LocalContext.current")
        for st in s.states:
            t = kotlin_type(st.type)
            self.emit(f"var {self.name(st.name)} by rememberSaveable {{ mutableStateOf<{t}>({self.code(st.init)}) }}")
        self.emit("Column(")
        self.emit("    modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),")
        self.emit("    verticalArrangement = Arrangement.spacedBy(8.dp),")
        self.emit(") {")
        self.ui_nodes(s.body, in_row=False)
        self.emit("}")
        self.level -= 1
        self.emit("}")
        self.emit()

    def ui_nodes(self, nodes, in_row=None):
        saved = getattr(self, "in_row", False)
        if in_row is not None:
            self.in_row = in_row
        self.level += 1
        for n in nodes:
            self.ui_node(n)
        self.level -= 1
        self.in_row = saved

    def text_arg(self, e):
        return self.code(e) if e.ty == STRING else f"nv_str({self.code(e)})"

    def ui_node(self, n):
        if isinstance(n, A.UIIf):
            self.ui_if(n)
            return
        if isinstance(n, A.UIFor):
            self.emit(f"for ({self.name(n.var)} in {self.iterable(n.iterable)}) {{")
            self.ui_nodes(n.body)
            self.emit("}")
            return
        k, args = n.kind, n.args
        if k == "column":
            self.emit("Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {")
            self.ui_nodes(n.children, in_row=False)
            self.emit("}")
        elif k == "row":
            self.emit("Row(horizontalArrangement = Arrangement.spacedBy(8.dp), "
                      "verticalAlignment = Alignment.CenterVertically) {")
            self.ui_nodes(n.children, in_row=True)
            self.emit("}")
        elif k == "text":
            extra = f", fontSize = {self.sub(args[1], P_POSTFIX)}.sp" if len(args) > 1 else ""
            self.emit(f"Text(text = {self.text_arg(args[0])}{extra})")
        elif k == "title":
            self.emit(f"Text(text = {self.text_arg(args[0])}, style = MaterialTheme.typography.headlineMedium)")
        elif k == "button":
            self.emit("Button(onClick = {")
            self.block_body(n.action)
            self.emit(f"}}) {{ Text(text = {self.text_arg(args[0])}) }}")
        elif k == "input":
            v = self.name(args[0].id)
            label = f", label = {{ Text(text = {self.text_arg(args[1])}) }}" if len(args) > 1 else ""
            # داخل Row فضای باقی‌مانده را می‌گیرد، داخل Column کل عرض را
            mod = "Modifier.weight(1f)" if getattr(self, "in_row", False) else "Modifier.fillMaxWidth()"
            self.emit(f"OutlinedTextField(value = {v}, onValueChange = {{ {v} = it }}{label}, "
                      f"modifier = {mod})")
        elif k == "checkbox":
            v = self.name(args[0].id)
            self.emit("Row(verticalAlignment = Alignment.CenterVertically) {")
            self.emit(f"    Checkbox(checked = {v}, onCheckedChange = {{ {v} = it }})")
            if len(args) > 1:
                self.emit(f"    Text(text = {self.text_arg(args[1])})")
            self.emit("}")
        elif k == "spacer":
            size = self.sub(args[0], P_POSTFIX) if args else "16"
            self.emit(f"Spacer(modifier = Modifier.size({size}.dp))")
        elif k == "divider":
            self.emit("HorizontalDivider()")

    def ui_if(self, n, prefix=""):
        self.emit(f"{prefix}if ({self.code(n.cond)}) {{")
        self.ui_nodes(n.then)
        if n.orelse and len(n.orelse) == 1 and isinstance(n.orelse[0], A.UIIf):
            self.ui_if(n.orelse[0], prefix="} else ")
            return
        if n.orelse is not None:
            self.emit("} else {")
            self.ui_nodes(n.orelse)
        self.emit("}")


# ======================= فایل‌های خروجی =======================

RUNTIME_KT = '''\
// کتابخانهٔ زمان اجرای Nova (تولید خودکار؛ ویرایش نکنید)
{package}
fun nv_str(x: Any?): String = x.toString()

fun nv_parseInt(s: String): Int = s.trim().toIntOrNull() ?: 0

private val NV_FLOAT_RE = Regex("^[+-]?([0-9]+\\\\.?[0-9]*|\\\\.[0-9]+)([eE][+-]?[0-9]+)?$")

fun nv_parseFloat(s: String): Double {{
    val t = s.trim()
    return if (NV_FLOAT_RE.matches(t)) t.toDouble() else 0.0
}}

fun <T> nv_remove(xs: List<T>, i: Int): List<T> {{
    if (i < 0 || i >= xs.size) throw IndexOutOfBoundsException("index $i out of bounds for length ${{xs.size}}")
    return xs.filterIndexed {{ j, _ -> j != i }}
}}

fun nv_random(lo: Int, hi: Int): Int = (lo..hi).random()

fun nv_format(x: Double, digits: Int): String =
    if (x.isNaN() || x.isInfinite()) x.toString()
    else String.format(java.util.Locale.US, "%.${{digits}}f", x)
'''


def runtime_file(package=None):
    return RUNTIME_KT.format(package=f"package {package}\n" if package else "")


def program_file(prog, package=None):
    g = KotlinGen(prog)
    g.emit("// تولید خودکار توسط کامپایلر Nova")
    if package:
        g.emit(f"package {package}")
    g.emit()
    g.program_decls()
    return g.text()


ACTIVITY_IMPORTS = """\
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
"""


def activity_file(prog, package):
    app = prog.app
    g = KotlinGen(prog)
    g.emit("// تولید خودکار توسط کامپایلر Nova")
    g.emit(f"package {package}")
    g.emit()
    for line in ACTIVITY_IMPORTS.splitlines():
        g.emit(line)
    g.emit()
    g.emit("class MainActivity : ComponentActivity() {")
    g.emit("    override fun onCreate(savedInstanceState: Bundle?) {")
    g.emit("        super.onCreate(savedInstanceState)")
    g.emit("        setContent {")
    g.emit("            MaterialTheme {")
    g.emit("                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {")
    g.emit("                    NovaApp()")
    g.emit("                }")
    g.emit("            }")
    g.emit("        }")
    g.emit("    }")
    g.emit("}")
    g.emit()
    first = app.screens[0].name
    g.emit("// ناوبری: پشته‌ای از نام صفحه‌ها؛ state هر صفحه تا وقتی در پشته است حفظ می‌شود")
    g.emit("@Composable")
    g.emit("fun NovaApp() {")
    g.level += 1
    g.emit("val activity = LocalContext.current as? ComponentActivity")
    g.emit(f'val stack = remember {{ mutableStateListOf("{first}") }}')
    g.emit("val holder = rememberSaveableStateHolder()")
    g.emit('fun key(i: Int) = "$i:${stack[i]}"')
    g.emit("val navigate: (String) -> Unit = { stack.add(it) }")
    g.emit("val back: () -> Unit = {")
    g.emit("    if (stack.size > 1) {")
    g.emit("        holder.removeState(key(stack.size - 1))")
    g.emit("        stack.removeAt(stack.size - 1)")
    g.emit("    } else {")
    g.emit("        activity?.finish()")
    g.emit("    }")
    g.emit("}")
    g.emit("BackHandler(enabled = stack.size > 1) { back() }")
    g.emit("holder.SaveableStateProvider(key(stack.size - 1)) {")
    g.emit("    when (stack.last()) {")
    for s in app.screens:
        g.emit(f'        "{s.name}" -> {s.name}Screen(navigate, back)')
    g.emit("    }")
    g.emit("}")
    g.level -= 1
    g.emit("}")
    g.emit()
    for s in app.screens:
        g.screen(s)
    return g.text()


def plain_kotlin(prog):
    """یک فایل Kotlin مستقل (بدون اندروید) برای برنامه‌هایی که main دارند."""
    return runtime_file() + "\n" + program_file(prog)
