"""سیستم نوع (Type System) زبان نوا.

انواع پایه: Int, Float, Bool, String, Void
نوع مرکب: List<T>
نوع ویژه: Unknown (فقط برای عناصر لیست خالی [] قبل از استنتاج نوع)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Type:
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class ListType(Type):
    elem: Type = None

    def __init__(self, elem):
        object.__setattr__(self, "name", "List")
        object.__setattr__(self, "elem", elem)

    def __str__(self):
        return f"List<{self.elem}>"


INT = Type("Int")
FLOAT = Type("Float")
BOOL = Type("Bool")
STRING = Type("String")
VOID = Type("Void")
UNKNOWN = Type("?")

PRIMITIVES = {"Int": INT, "Float": FLOAT, "Bool": BOOL, "String": STRING, "Void": VOID}


def is_numeric(t):
    return t in (INT, FLOAT)


def has_unknown(t):
    if t == UNKNOWN:
        return True
    if isinstance(t, ListType):
        return has_unknown(t.elem)
    return False


def join(a, b):
    """کوچک‌ترین نوعی که هر دو نوع a و b را در بر می‌گیرد (یا None)."""
    if a == b:
        return a
    if a == UNKNOWN:
        return b
    if b == UNKNOWN:
        return a
    if is_numeric(a) and is_numeric(b):
        return FLOAT
    if isinstance(a, ListType) and isinstance(b, ListType):
        e = join(a.elem, b.elem)
        return ListType(e) if e is not None else None
    return None
