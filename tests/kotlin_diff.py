"""تست تفاضلی (Differential Testing).

هر برنامهٔ tests/programs/*.nova یک بار با مفسر پایتون اجرا می‌شود و یک بار
به Kotlin ترجمه، با کامپایلر واقعی Kotlin (از طریق Gradle) کامپایل و روی JVM
اجرا می‌شود. اگر خروجی‌ها یکسان باشند، یعنی معنای زبان در هر دو پیاده‌سازی
یکی است.

اجرا:  python tests/kotlin_diff.py      (به Gradle و JDK 17+ نیاز دارد)
"""

import glob
import io
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from nova.checker import check  # noqa: E402
from nova.codegen_kotlin import program_file, runtime_file  # noqa: E402
from nova.interpreter import Interpreter  # noqa: E402
from nova.parser import parse  # noqa: E402

SETTINGS = """\
pluginManagement { repositories { gradlePluginPortal(); mavenCentral() } }
rootProject.name = "novadiff"
"""
BUILD = """\
plugins { kotlin("jvm") version "2.0.21"; application }
repositories { mavenCentral() }
application {
    mainClass.set("RunnerKt")
    applicationDefaultJvmArgs = listOf("-Dstdout.encoding=UTF-8", "-Xss16m")
}
"""


def main():
    programs = sorted(glob.glob(os.path.join(ROOT, "tests", "programs", "*.nova")))
    work = tempfile.mkdtemp(prefix="novadiff-")
    src = os.path.join(work, "src", "main", "kotlin")
    os.makedirs(src)
    with open(os.path.join(work, "settings.gradle.kts"), "w") as f:
        f.write(SETTINGS)
    with open(os.path.join(work, "build.gradle.kts"), "w") as f:
        f.write(BUILD)

    expected = {}
    cases = []
    for path in programs:
        name = "p_" + os.path.splitext(os.path.basename(path))[0]
        prog = check(parse(open(path, encoding="utf-8").read()))
        buf = io.StringIO()
        with redirect_stdout(buf):
            Interpreter(prog).run_main()
        expected[name] = buf.getvalue()
        os.makedirs(os.path.join(src, name))
        with open(os.path.join(src, name, "Program.kt"), "w", encoding="utf-8") as f:
            f.write(program_file(prog, name))
        with open(os.path.join(src, name, "Runtime.kt"), "w", encoding="utf-8") as f:
            f.write(runtime_file(name))
        cases.append(name)

    runner = ["fun main(args: Array<String>) {", "    when (args[0]) {"]
    runner += [f'        "{n}" -> {n}.main()' for n in cases]
    runner += ["    }", "}"]
    with open(os.path.join(src, "Runner.kt"), "w") as f:
        f.write("\n".join(runner) + "\n")

    build = subprocess.run(["gradle", "-q", "--console=plain", "installDist"], cwd=work,
                           capture_output=True, text=True)
    if build.returncode != 0:
        print(build.stdout, build.stderr)
        print("FAILED: generated Kotlin did not compile")
        return 1
    exe = os.path.join(work, "build", "install", "novadiff", "bin", "novadiff")
    failed = 0
    for n in cases:
        out = subprocess.run([exe, n], capture_output=True, text=True, encoding="utf-8").stdout
        if out == expected[n]:
            print(f"PASS {n}")
        else:
            failed += 1
            print(f"FAIL {n}")
            import difflib
            for line in difflib.unified_diff(expected[n].splitlines(), out.splitlines(),
                                             "interpreter", "kotlin", lineterm=""):
                print("   ", line)
    shutil.rmtree(work, ignore_errors=True)
    print(f"{len(cases) - failed}/{len(cases)} programs produce identical output")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
