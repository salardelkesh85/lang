"""رابط خط فرمان Nova.

  python -m nova tokens  FILE        نمایش توکن‌ها (فاز ۱)
  python -m nova ast     FILE        نمایش درخت نحو (فاز ۲)
  python -m nova check   FILE        بررسی نوع (فاز ۳)
  python -m nova run     FILE        اجرای main() با مفسر
  python -m nova sim     FILE        اجرای اپ در شبیه‌ساز ترمینال
  python -m nova kotlin  FILE        چاپ کد Kotlin تولیدشده
  python -m nova build   FILE -o DIR ساخت پروژهٔ Android Studio
"""

import argparse
import sys

from . import ast as A
from .android_project import generate
from .checker import check
from .codegen_kotlin import activity_file, plain_kotlin, program_file
from .errors import NovaError
from .interpreter import Interpreter
from .lexer import tokenize
from .parser import Parser
from .simulator import Simulator


def load(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def front_end(source):
    prog = Parser(tokenize(source)).parse_program()
    check(prog)
    return prog


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="nova", description="Nova: a programming language for Android")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in [
        ("tokens", "show tokens (lexical analysis)"),
        ("ast", "show the abstract syntax tree"),
        ("check", "type-check the program"),
        ("run", "run main() with the interpreter"),
        ("kotlin", "print generated Kotlin code"),
    ]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("file")
    p = sub.add_parser("sim", help="run the app in the terminal simulator")
    p.add_argument("file")
    p.add_argument("--do", action="append", default=None, metavar="EVENT",
                   help="scripted event: N (click), N=text (type), back")
    p.add_argument("--seed", type=int, default=None)
    p = sub.add_parser("build", help="generate an Android Studio project")
    p.add_argument("file")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--package", default="com.example.novaapp")
    args = ap.parse_args(argv)

    source = load(args.file)
    try:
        if args.cmd == "tokens":
            for t in tokenize(source):
                print(t)
            return 0
        if args.cmd == "ast":
            prog = Parser(tokenize(source)).parse_program()
            try:
                check(prog)
            except NovaError:
                pass
            print(A.dump(prog))
            return 0
        prog = front_end(source)
        if args.cmd == "check":
            print(f"{args.file}: OK ({len(prog.functions)} function(s), "
                  f"{len(prog.app.screens) if prog.app else 0} screen(s))")
        elif args.cmd == "run":
            Interpreter(prog).run_main()
        elif args.cmd == "kotlin":
            if prog.app:
                print(program_file(prog, "com.example.novaapp"))
                print(activity_file(prog, "com.example.novaapp"))
            else:
                print(plain_kotlin(prog))
        elif args.cmd == "sim":
            if not prog.app:
                print("error: this program has no 'app' block", file=sys.stderr)
                return 1
            sim = Simulator(prog, seed=args.seed)
            if args.do is not None:
                sim.run_script(args.do)
            else:
                sim.run_interactive()
        elif args.cmd == "build":
            if not prog.app:
                print("error: this program has no 'app' block", file=sys.stderr)
                return 1
            import os
            generate(prog, args.out, args.package, os.path.basename(args.file))
            print(f"Android project written to {args.out}")
        return 0
    except NovaError as e:
        print(e.format(source, args.file), file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
