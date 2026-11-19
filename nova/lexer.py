"""تحلیلگر واژگانی (Lexer / Scanner).

متن برنامه را کاراکتر به کاراکتر می‌خواند و فهرستی از توکن‌ها تولید می‌کند.
ویژگی‌های خاص:
  * شناسه‌ها می‌توانند فارسی باشند (هر حرف یونیکد).
  * ارقام فارسی در اعداد مجازند: ۱۲۳ == 123
  * رشته‌ها می‌توانند درون‌یابی داشته باشند: "سلام {name}"
  * توضیحات: // تا آخر خط و /* ... */
"""

import unicodedata

from .errors import LexError
from .tokens import KEYWORDS, T, Token


class InterpPart:
    """بخش کد درون یک رشته، مثل {count + 1}."""

    def __init__(self, source, line, col):
        self.source = source
        self.line = line
        self.col = col

    def __repr__(self):
        return f"{{{self.source}}}"


# عملگرهای چندکاراکتری باید قبل از تک‌کاراکتری‌ها امتحان شوند (longest match)
OPERATORS = [
    ("..=", T.DOTDOTEQ), ("..", T.DOTDOT),
    ("==", T.EQ), ("!=", T.NE), ("<=", T.LE), (">=", T.GE),
    ("+=", T.PLUS_ASSIGN), ("-=", T.MINUS_ASSIGN),
    ("*=", T.STAR_ASSIGN), ("/=", T.SLASH_ASSIGN),
    ("+", T.PLUS), ("-", T.MINUS), ("*", T.STAR), ("/", T.SLASH), ("%", T.PERCENT),
    ("=", T.ASSIGN), ("<", T.LT), (">", T.GT),
    ("(", T.LPAREN), (")", T.RPAREN), ("{", T.LBRACE), ("}", T.RBRACE),
    ("[", T.LBRACKET), ("]", T.RBRACKET), (",", T.COMMA), (":", T.COLON), (";", T.SEMI),
]

ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "{": "{", "}": "}"}


def is_digit(c):
    """رقم دهدهی (لاتین، فارسی یا عربی)."""
    return c != "" and unicodedata.decimal(c, None) is not None


def is_ident_start(c):
    return c != "" and (c.isalpha() or c == "_")


def is_ident_part(c):
    return is_ident_start(c) or is_digit(c)


def digits_to_ascii(s):
    return "".join(str(unicodedata.decimal(c)) if is_digit(c) else c for c in s)


class Lexer:
    def __init__(self, source, line=1, col=1):
        self.src = source
        self.pos = 0
        self.line = line
        self.col = col
        self.tokens = []
        self.nl_before = False

    # ---------- ابزارهای کمکی ----------
    def peek(self, k=0):
        i = self.pos + k
        return self.src[i] if i < len(self.src) else ""

    def advance(self):
        c = self.src[self.pos]
        self.pos += 1
        if c == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return c

    def add(self, type_, lexeme, value, line, col):
        self.tokens.append(Token(type_, lexeme, value, line, col, self.nl_before))
        self.nl_before = False

    # ---------- حلقهٔ اصلی ----------
    def tokenize(self):
        while self.pos < len(self.src):
            c = self.peek()
            if c == "\n":
                self.nl_before = True
                self.advance()
            elif c in " \t\r﻿":
                self.advance()
            elif c == "/" and self.peek(1) == "/":
                while self.pos < len(self.src) and self.peek() != "\n":
                    self.advance()
            elif c == "/" and self.peek(1) == "*":
                self.block_comment()
            elif is_digit(c):
                self.number()
            elif is_ident_start(c):
                self.identifier()
            elif c == '"':
                self.string()
            else:
                self.operator()
        self.add(T.EOF, "", None, self.line, self.col)
        return self.tokens

    def block_comment(self):
        line, col = self.line, self.col
        self.advance()
        self.advance()
        while not (self.peek() == "*" and self.peek(1) == "/"):
            if self.pos >= len(self.src):
                raise LexError("unterminated comment", line, col)
            if self.peek() == "\n":
                self.nl_before = True
            self.advance()
        self.advance()
        self.advance()

    def number(self):
        line, col, start = self.line, self.col, self.pos
        while is_digit(self.peek()) or self.peek() == "_":
            self.advance()
        is_float = False
        # «1..5» یک بازه است، نه عدد اعشاری؛ پس بعد از نقطه باید رقم باشد
        if self.peek() == "." and is_digit(self.peek(1)):
            is_float = True
            self.advance()
            while is_digit(self.peek()) or self.peek() == "_":
                self.advance()
        if self.peek() in ("e", "E") and (
            is_digit(self.peek(1)) or (self.peek(1) in "+-" and is_digit(self.peek(2)))
        ):
            is_float = True
            self.advance()
            if self.peek() in "+-":
                self.advance()
            while is_digit(self.peek()):
                self.advance()
        lexeme = self.src[start:self.pos]
        text = digits_to_ascii(lexeme).replace("_", "")
        if is_float:
            self.add(T.FLOAT, lexeme, float(text), line, col)
        else:
            value = int(text)
            if value > 2**31 - 1:
                raise LexError(f"integer literal {lexeme} is too large for Int (32-bit)", line, col)
            self.add(T.INT, lexeme, value, line, col)
        if is_ident_start(self.peek()):
            raise LexError(f"invalid character {self.peek()!r} after number", self.line, self.col)

    def identifier(self):
        line, col, start = self.line, self.col, self.pos
        while is_ident_part(self.peek()):
            self.advance()
        word = self.src[start:self.pos]
        if word.startswith("nv_"):
            raise LexError("identifiers starting with 'nv_' are reserved for the runtime", line, col)
        type_ = KEYWORDS.get(word, T.IDENT)
        self.add(type_, word, word if type_ == T.IDENT else None, line, col)

    def string(self):
        line, col, start = self.line, self.col, self.pos
        self.advance()  # "
        parts, buf = [], []
        while True:
            c = self.peek()
            if c == "" or c == "\n":
                raise LexError("unterminated string", line, col)
            if c == '"':
                self.advance()
                break
            if c == "\\":
                eline, ecol = self.line, self.col
                self.advance()
                e = self.peek()
                if e not in ESCAPES:
                    raise LexError(f"unknown escape sequence \\{e}", eline, ecol)
                buf.append(ESCAPES[e])
                self.advance()
            elif c == "{":
                if buf:
                    parts.append("".join(buf))
                    buf = []
                parts.append(self.interpolation())
            elif c == "}":
                raise LexError("unmatched '}' in string (use \\} for a literal brace)", self.line, self.col)
            else:
                buf.append(self.advance())
        if buf or not parts:
            parts.append("".join(buf))
        self.add(T.STRING, self.src[start:self.pos], parts, line, col)

    def interpolation(self):
        """کد داخل {...} را جدا می‌کند؛ بعداً پارسر آن را جداگانه تجزیه می‌کند."""
        self.advance()  # {
        line, col, start = self.line, self.col, self.pos
        depth = 1
        while True:
            c = self.peek()
            if c == "" or c == "\n":
                raise LexError("unterminated interpolation in string", line, col)
            if c == '"':  # رشتهٔ تودرتو داخل درون‌یابی
                self.advance()
                while self.peek() not in ('"', "", "\n"):
                    if self.peek() == "\\":
                        self.advance()
                    self.advance()
                if self.peek() != '"':
                    raise LexError("unterminated string", line, col)
                self.advance()
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    code = self.src[start:self.pos]
                    self.advance()
                    if not code.strip():
                        raise LexError("empty interpolation {}", line, col)
                    return InterpPart(code, line, col)
            self.advance()

    def operator(self):
        line, col = self.line, self.col
        for text, type_ in OPERATORS:
            if self.src.startswith(text, self.pos):
                for _ in text:
                    self.advance()
                self.add(type_, text, None, line, col)
                return
        raise LexError(f"unexpected character {self.peek()!r}", line, col)


def tokenize(source):
    return Lexer(source).tokenize()
