"""تعریف انواع توکن‌ها (واحدهای واژگانی) زبان نوا."""

from dataclasses import dataclass, field
from enum import Enum, auto


class T(Enum):
    # لیترال‌ها و شناسه
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    IDENT = auto()

    # کلمات کلیدی
    LET = auto()
    VAR = auto()
    FUN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    BREAK = auto()
    CONTINUE = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    APP = auto()
    SCREEN = auto()
    STATE = auto()

    # عملگرها
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    PERCENT = auto()     # %
    ASSIGN = auto()      # =
    PLUS_ASSIGN = auto()   # +=
    MINUS_ASSIGN = auto()  # -=
    STAR_ASSIGN = auto()   # *=
    SLASH_ASSIGN = auto()  # /=
    EQ = auto()          # ==
    NE = auto()          # !=
    LT = auto()          # <
    LE = auto()          # <=
    GT = auto()          # >
    GE = auto()          # >=
    DOTDOT = auto()      # ..
    DOTDOTEQ = auto()    # ..=

    # جداکننده‌ها
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    SEMI = auto()

    EOF = auto()


KEYWORDS = {
    "let": T.LET, "var": T.VAR, "fun": T.FUN, "return": T.RETURN,
    "if": T.IF, "else": T.ELSE, "while": T.WHILE, "for": T.FOR, "in": T.IN,
    "break": T.BREAK, "continue": T.CONTINUE, "true": T.TRUE, "false": T.FALSE,
    "and": T.AND, "or": T.OR, "not": T.NOT,
    "app": T.APP, "screen": T.SCREEN, "state": T.STATE,
}


@dataclass
class Token:
    type: T
    lexeme: str
    value: object
    line: int
    col: int
    # آیا قبل از این توکن «خط جدید» آمده است؟ (برای تشخیص پایان دستور)
    nl_before: bool = field(default=False)

    def __repr__(self):
        v = "" if self.value is None else f" {self.value!r}"
        return f"{self.line}:{self.col} {self.type.name}{v}"
