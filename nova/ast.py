"""درخت نحو انتزاعی (AST) زبان نوا.

هر گره، موقعیت (line, col) خود را در کد منبع نگه می‌دارد.
تحلیلگر معنایی روی گره‌های عبارت دو فیلد اضافه می‌نویسد:
  ty         نوع محاسبه‌شدهٔ عبارت
  coerce_to  اگر عبارت باید به نوع دیگری تبدیل ضمنی شود (مثلاً Int -> Float)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Node:
    line: int
    col: int


# ======================= عبارت‌ها (Expressions) =======================

@dataclass
class Expr(Node):
    def __post_init__(self):
        self.ty = None
        self.coerce_to = None


@dataclass
class IntLit(Expr):
    value: int


@dataclass
class FloatLit(Expr):
    value: float


@dataclass
class BoolLit(Expr):
    value: bool


@dataclass
class StringLit(Expr):
    parts: list  # هر بخش یا str است یا Expr (درون‌یابی)


@dataclass
class ListLit(Expr):
    elements: List[Expr]


@dataclass
class Name(Expr):
    id: str


@dataclass
class Unary(Expr):
    op: str  # '-' یا 'not'
    operand: Expr


@dataclass
class Binary(Expr):
    op: str  # + - * / % == != < <= > >= and or
    left: Expr
    right: Expr


@dataclass
class Call(Expr):
    callee: str
    args: List[Expr]


@dataclass
class Index(Expr):
    target: Expr
    index: Expr


# ======================= دستورها (Statements) =======================

@dataclass
class Stmt(Node):
    pass


@dataclass
class Block(Stmt):
    stmts: List[Stmt]


@dataclass
class VarDecl(Stmt):
    mutable: bool          # var=True , let=False
    name: str
    type_ann: Optional[object]
    init: Expr


@dataclass
class Assign(Stmt):
    name: str
    op: str                # '=' '+=' '-=' '*=' '/='
    value: Expr


@dataclass
class If(Stmt):
    cond: Expr
    then: Block
    orelse: Optional[Union[Block, "If"]]


@dataclass
class While(Stmt):
    cond: Expr
    body: Block


@dataclass
class Range(Node):
    start: Expr
    end: Expr
    inclusive: bool


@dataclass
class For(Stmt):
    var: str
    iterable: Union[Range, Expr]
    body: Block


@dataclass
class Return(Stmt):
    value: Optional[Expr]


@dataclass
class Break(Stmt):
    pass


@dataclass
class Continue(Stmt):
    pass


@dataclass
class ExprStmt(Stmt):
    expr: Expr


# ======================= رابط کاربری (UI) =======================

@dataclass
class UIElement(Node):
    kind: str                          # column, row, text, title, button, input, checkbox, spacer, divider
    args: List[Expr]
    children: Optional[List[Node]] = None   # برای column/row
    action: Optional[Block] = None          # برای button


@dataclass
class UIIf(Node):
    cond: Expr
    then: List[Node]
    orelse: Optional[List[Node]]


@dataclass
class UIFor(Node):
    var: str
    iterable: Union[Range, Expr]
    body: List[Node]


# ======================= اعلان‌ها (Declarations) =======================

@dataclass
class Param(Node):
    name: str
    type: object


@dataclass
class FunDecl(Node):
    name: str
    params: List[Param]
    ret: object
    body: Block


@dataclass
class StateDecl(Node):
    name: str
    type_ann: Optional[object]
    init: Expr


@dataclass
class ScreenDecl(Node):
    name: str
    states: List[StateDecl]
    body: List[Node]


@dataclass
class AppDecl(Node):
    title: str
    screens: List[ScreenDecl]


@dataclass
class Program(Node):
    globals: List[VarDecl] = field(default_factory=list)
    functions: List[FunDecl] = field(default_factory=list)
    app: Optional[AppDecl] = None


# ======================= چاپ درخت (برای نمایش در ارائه) =======================

def dump(node, indent=0):
    pad = "  " * indent
    if isinstance(node, list):
        return "\n".join(dump(n, indent) for n in node)
    if not isinstance(node, Node):
        return pad + repr(node)
    fields = [(k, v) for k, v in node.__dict__.items()
              if k not in ("line", "col", "ty", "coerce_to")]
    simple = [(k, v) for k, v in fields
              if not isinstance(v, (Node, list)) or (isinstance(v, list) and all(isinstance(x, str) for x in v))]
    complex_ = [(k, v) for k, v in fields if (k, v) not in simple]
    head = f"{pad}{type(node).__name__}"
    if simple:
        head += "(" + ", ".join(f"{k}={_short(v)}" for k, v in simple) + ")"
    ty = getattr(node, "ty", None)
    if ty is not None:
        head += f" : {ty}"
    lines = [head]
    for k, v in complex_:
        if v is None:
            continue
        if isinstance(v, list):
            if not v:
                continue
            lines.append(f"{pad}  {k}:")
            for item in v:
                if isinstance(item, Node):
                    lines.append(dump(item, indent + 2))
                else:
                    lines.append(f"{pad}    {item!r}")
        else:
            lines.append(f"{pad}  {k}:")
            lines.append(dump(v, indent + 2))
    return "\n".join(lines)


def _short(v):
    if isinstance(v, str):
        return repr(v)
    return str(v)
