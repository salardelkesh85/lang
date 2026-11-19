"""تست‌های واحد کامپایلر Nova.   اجرا:  python -m unittest discover tests"""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from nova import ast as A  # noqa: E402
from nova.android_project import generate  # noqa: E402
from nova.checker import check  # noqa: E402
from nova.codegen_kotlin import activity_file, plain_kotlin  # noqa: E402
from nova.errors import LexError, NovaRuntimeError, NovaTypeError, ParseError  # noqa: E402
from nova.interpreter import Interpreter  # noqa: E402
from nova.lexer import tokenize  # noqa: E402
from nova.parser import parse  # noqa: E402
from nova.simulator import Simulator  # noqa: E402
from nova.tokens import T  # noqa: E402


def run(src):
    prog = check(parse(src))
    buf = io.StringIO()
    with redirect_stdout(buf):
        Interpreter(prog).run_main()
    return buf.getvalue().splitlines()


def run_expr(expr):
    return run(f"fun main() {{ print({expr}) }}")[0]


class LexerTests(unittest.TestCase):
    def types(self, src):
        return [t.type for t in tokenize(src)][:-1]

    def test_operators_longest_match(self):
        self.assertEqual(self.types("a += 1 ..= .. == ="),
                         [T.IDENT, T.PLUS_ASSIGN, T.INT, T.DOTDOTEQ, T.DOTDOT, T.EQ, T.ASSIGN])

    def test_range_is_not_float(self):
        self.assertEqual(self.types("0..10"), [T.INT, T.DOTDOT, T.INT])

    def test_persian_digits_and_identifiers(self):
        toks = tokenize("let عدد = ۱۴۰۳")
        self.assertEqual(toks[1].value, "عدد")
        self.assertEqual(toks[3].value, 1403)

    def test_comments(self):
        self.assertEqual(self.types("1 // x\n/* y\n z */ 2"), [T.INT, T.INT])

    def test_newline_flag(self):
        toks = tokenize("a\nb")
        self.assertFalse(toks[0].nl_before)
        self.assertTrue(toks[1].nl_before)

    def test_string_interpolation_parts(self):
        tok = tokenize('"x={x + 1}!"')[0]
        self.assertEqual(tok.value[0], "x=")
        self.assertEqual(tok.value[1].source, "x + 1")
        self.assertEqual(tok.value[2], "!")

    def test_errors(self):
        for src in ['"abc', "@", "/* x", "2147483648", "nv_x", '"\\q"', "12abc"]:
            with self.assertRaises(LexError, msg=src):
                tokenize(src)


class ParserTests(unittest.TestCase):
    def expr(self, s):
        prog = parse(f"let x = {s}")
        return prog.globals[0].init

    def test_precedence(self):
        e = self.expr("1 + 2 * 3")
        self.assertIsInstance(e, A.Binary)
        self.assertEqual(e.op, "+")
        self.assertEqual(e.right.op, "*")

    def test_left_associativity(self):
        e = self.expr("10 - 4 - 3")
        self.assertEqual(e.left.op, "-")

    def test_not_binds_looser_than_comparison(self):
        e = self.expr("not a == b")
        self.assertIsInstance(e, A.Unary)
        self.assertEqual(e.operand.op, "==")

    def test_negative_literal_folding(self):
        self.assertEqual(self.expr("-5").value, -5)

    def test_chained_comparison_rejected(self):
        with self.assertRaises(ParseError):
            parse("let x = 1 < 2 < 3")

    def test_newline_ends_statement(self):
        # «(1)» در خط بعد، فراخوانی g(1) نیست بلکه دستور جدید است
        with self.assertRaises(ParseError):
            parse("fun f() { let a = g\n (1) }")
        prog = parse("fun f() { let a = g(1)\n let b = 2; let c = 3 }")
        self.assertEqual(len(prog.functions[0].body.stmts), 3)

    def test_statement_errors(self):
        bad = [
            "fun f() { 1 + 2 }",
            "fun f() { let a = 1 let b = 2 }",
            "fun f( { }",
            "let x",
            "app \"a\" { }",
            "app \"a\" { screen S { text(\"x\") state y = 1 } }",
            "app \"a\" { screen S { blink(\"x\") } }",
            "app \"a\" { screen S { button(\"x\") } }",
            "while true { }",
        ]
        for src in bad:
            with self.assertRaises(ParseError, msg=src):
                parse(src)

    def test_app_structure(self):
        prog = parse('app "T" { screen A { state n = 0\n text("{n}")\n row { button("+") { n += 1 } } } screen B { } }')
        self.assertEqual(prog.app.title, "T")
        self.assertEqual([s.name for s in prog.app.screens], ["A", "B"])
        self.assertEqual(prog.app.screens[0].states[0].name, "n")
        self.assertEqual(prog.app.screens[0].body[1].kind, "row")


class CheckerTests(unittest.TestCase):
    def bad(self, src, fragment):
        with self.assertRaises(NovaTypeError) as cm:
            check(parse(src))
        self.assertIn(fragment, cm.exception.message)

    def test_type_errors(self):
        self.bad('let x: Int = "a"', "expected Int, got String")
        self.bad("fun f() { y = 1 }", "undefined variable 'y'")
        self.bad("fun f() { let a = 1\n a = 2 }", "cannot assign to 'a'")
        self.bad("fun f() { let a = 1\n let a = 2 }", "already declared")
        self.bad("fun f(): Int { if true { return 1 } }", "every path")
        self.bad("fun f() { break }", "outside of a loop")
        self.bad("fun f(a: Int) { } fun g() { f(1, 2) }", "expects 1 argument")
        self.bad('fun f(a: Int) { } fun g() { f("x") }', "parameter 'a'")
        self.bad("fun f() { if 1 { } }", "condition")
        self.bad("let x = []", "cannot infer")
        self.bad("fun f() { } let x = f()", "Void")
        self.bad('fun f() { toast("x") }', "inside a button action")
        self.bad("let x = [1, \"a\"]", "same type")
        self.bad("let x = 1 + true", "cannot be applied")
        self.bad("fun print(x: Int) { }", "built-in")
        self.bad("fun f(x: Int) { x = 2 }", "parameter")
        self.bad("fun f() { for i in 0..3 { i = 1 } }", "loop variable")
        self.bad("let x: Int = 2.5", "expected Int, got Float")

    def test_ui_errors(self):
        self.bad('app "a" { screen S { button("x") { navigate(Nope) } } }', "screen name")
        self.bad('app "a" { screen S { state n = 0\n input(n) } }', "needs a String state")
        self.bad('var g = ""\napp "a" { screen S { input(g) } }', "must be a state")
        self.bad('app "a" { screen S { text() } }', "expects 1 to 2")

    def test_coercion_marked(self):
        prog = check(parse("let x: Float = 1"))
        self.assertEqual(str(prog.globals[0].init.coerce_to), "Float")

    def test_types_annotated(self):
        prog = check(parse('let x = [1, 2.5]\nlet s = "a" + 1'))
        self.assertEqual(str(prog.globals[0].type), "List<Float>")
        self.assertEqual(str(prog.globals[1].type), "String")


class InterpreterTests(unittest.TestCase):
    def test_arithmetic_matches_kotlin(self):
        self.assertEqual(run_expr("7 / 2"), "3")
        self.assertEqual(run_expr("-7 / 2"), "-3")
        self.assertEqual(run_expr("-7 % 3"), "-1")
        self.assertEqual(run_expr("2147483647 + 1"), "-2147483648")
        self.assertEqual(run_expr("7 / 2.0"), "3.5")
        self.assertEqual(run_expr("1e7"), "1.0E7")
        self.assertEqual(run_expr("1.0 / 0"), "Infinity")

    def test_strings_and_lists(self):
        self.assertEqual(run_expr('"a" + 1 + 2'), "a12")
        self.assertEqual(run_expr('1 + 2 + "a"'), "3a")
        self.assertEqual(run_expr("[1, 2] + [3]"), "[1, 2, 3]")
        self.assertEqual(run_expr("remove([1, 2, 3], 0)"), "[2, 3]")
        self.assertEqual(run_expr('"{1 + 1} و {true}"'), "2 و true")
        self.assertEqual(run_expr('len("سلام")'), "4")

    def test_control_flow(self):
        out = run("""
            fun f(n: Int): Int { if n < 2 { return n } return f(n - 1) + f(n - 2) }
            fun main() {
                var s = 0
                for i in 0..10 { if i == 5 { break } s += i }
                print(s)
                print(f(15))
                for i in 1..=3 { if i == 2 { continue } print(i) }
            }""")
        self.assertEqual(out, ["10", "610", "1", "3"])

    def test_runtime_errors(self):
        for src in ["print(1 / 0)", "print([1][5])", "print(remove([1], 3))", "print(random(5, 1))"]:
            with self.assertRaises(NovaRuntimeError, msg=src):
                run(f"fun main() {{ {src} }}")

    def test_stack_overflow(self):
        with self.assertRaises(NovaRuntimeError):
            run("fun f(n: Int): Int { return f(n + 1) }\nfun main() { print(f(0)) }")


APP = """
app "Test" {
    screen Main {
        state n: Int = 0
        state name: String = ""
        text("n={n} name={name}")
        button("inc") { n += 1 }
        input(name, "name")
        button("go") { navigate(Other) }
    }
    screen Other {
        state ok: Bool = false
        checkbox(ok, "ok")
        if ok { text("checked") }
        button("back") { toast("bye")
            back() }
    }
}
"""


class SimulatorTests(unittest.TestCase):
    def test_events_and_navigation(self):
        lines = []
        sim = Simulator(check(parse(APP)), out=lines.append)
        sim.run_script(["1", "1", "2=Ali", "3", "1", "2"])
        screen = lines[-1]
        self.assertIn("n=2 name=Ali", screen)       # state حفظ شده است
        self.assertIn("[toast] bye", screen)
        self.assertTrue(any("checked" in l for l in lines))


class CodegenTests(unittest.TestCase):
    def test_plain_kotlin(self):
        kt = plain_kotlin(check(parse("fun main() { var x: Float = 1\n x += 2\n print(\"v={x}\") }")))
        self.assertIn("var x: Double = 1.0", kt)
        self.assertIn('println("v=${x}")', kt)

    def test_precedence_parentheses(self):
        kt = plain_kotlin(check(parse("fun main() { print((1 + 2) * 3)\n print(not (1 < 2))\n print(10 - (4 - 3)) }")))
        self.assertIn("println((1 + 2) * 3)", kt)
        self.assertIn("println(!(1 < 2))", kt)
        self.assertIn("println(10 - (4 - 3))", kt)

    def test_keyword_mangling(self):
        kt = plain_kotlin(check(parse("fun main() { let val = 1\n let Text = 2\n print(val + Text) }")))
        self.assertIn("val `val`: Int = 1", kt)
        self.assertIn("val Text_: Int = 2", kt)

    def test_compose_output(self):
        kt = activity_file(check(parse(APP)), "com.example.t")
        self.assertIn("var n by rememberSaveable { mutableStateOf<Int>(0) }", kt)
        self.assertIn('navigate("Other")', kt)
        self.assertIn("Checkbox(checked = ok, onCheckedChange = { ok = it })", kt)
        self.assertIn('"Other" -> OtherScreen(navigate, back)', kt)

    def test_android_project_files(self):
        with tempfile.TemporaryDirectory() as d:
            generate(check(parse(APP)), d, "com.example.t")
            for rel in ["settings.gradle.kts", "app/build.gradle.kts", "app/src/main/AndroidManifest.xml",
                        "app/src/main/java/com/example/t/MainActivity.kt",
                        "app/src/main/res/values/strings.xml"]:
                self.assertTrue(os.path.exists(os.path.join(d, rel)), rel)


class ExamplesTests(unittest.TestCase):
    def test_all_examples_check(self):
        folder = os.path.join(ROOT, "examples")
        for name in os.listdir(folder):
            if name.endswith(".nova"):
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    check(parse(f.read()))


if __name__ == "__main__":
    unittest.main()
