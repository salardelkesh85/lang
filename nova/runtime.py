"""کتابخانهٔ زمان اجرا برای مفسر.

این توابع رفتار Kotlin را دقیقاً تقلید می‌کنند تا خروجی مفسر و خروجی
برنامهٔ اندروید یکسان باشد (مثلاً Int سی‌ودو بیتی است و سرریز دارد،
و 1.0E7 به همان شکلی چاپ می‌شود که Kotlin چاپ می‌کند).
"""

import math
import re
from decimal import Decimal

from .errors import NovaRuntimeError

INT_MIN, INT_MAX = -(2**31), 2**31 - 1


def wrap32(v):
    """سرریز عدد صحیح ۳۲ بیتی مانند JVM."""
    v &= 0xFFFFFFFF
    return v - 2**32 if v > INT_MAX else v


def fmt_float(x):
    """قالب Double.toString() در Kotlin/Java."""
    if math.isnan(x):
        return "NaN"
    if math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    if x == 0:
        return "-0.0" if math.copysign(1, x) < 0 else "0.0"
    a = abs(x)
    if 1e-3 <= a < 1e7:
        s = repr(x)
        if "e" in s or "E" in s:  # repr ممکن است نماد علمی بدهد
            s = format(Decimal(s), "f")
        if "." not in s:
            s += ".0"
        return s
    sign, digits, exp = Decimal(repr(x)).as_tuple()
    e = exp + len(digits) - 1
    digits = "".join(map(str, digits)).rstrip("0") or "0"
    mant = digits[0] + "." + (digits[1:] or "0")
    return ("-" if sign else "") + f"{mant}E{e}"


def to_str(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return fmt_float(v)
    if isinstance(v, tuple):
        return "[" + ", ".join(to_str(x) for x in v) + "]"
    return str(v)


_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?$")


def to_int(v):
    if isinstance(v, bool):
        raise TypeError("bool")
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if math.isnan(v):
            return 0
        return max(INT_MIN, min(INT_MAX, int(v)))
    s = v.strip()
    if not _INT_RE.match(s):
        return 0
    n = int(s)
    return n if INT_MIN <= n <= INT_MAX else 0


def to_float(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = v.strip()
    if not _FLOAT_RE.match(s):
        return 0.0
    return float(s)


def int_div(a, b, line, col):
    if b == 0:
        raise NovaRuntimeError("division by zero", line, col)
    q = abs(a) // abs(b)
    return wrap32(q if (a >= 0) == (b >= 0) else -q)


def int_rem(a, b, line, col):
    if b == 0:
        raise NovaRuntimeError("division by zero", line, col)
    r = abs(a) % abs(b)
    return r if a >= 0 else -r


def float_div(a, b):
    if b == 0:
        if a == 0 or math.isnan(a):
            return math.nan
        return math.copysign(math.inf, a) * math.copysign(1, b)
    return a / b


def float_rem(a, b):
    if b == 0:
        return math.nan
    return math.fmod(a, b)


def format_fixed(x, digits):
    if math.isnan(x) or math.isinf(x):
        return fmt_float(x)
    return f"{x:.{digits}f}"
