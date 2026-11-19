"""تحلیلگر نحوی (Parser) به روش «نزولی بازگشتی» (Recursive Descent).

برای هر قاعدهٔ گرامر یک تابع وجود دارد. گرامر LL(1) است: در هر لحظه
فقط با نگاه به توکن بعدی تصمیم می‌گیریم کدام قاعده را دنبال کنیم.
(تنها استثنا: تشخیص انتساب `x = ...` از عبارت، که دو توکن جلو را می‌بیند.)

گرامر کامل در docs/grammar.md آمده است.
"""

from . import ast as A
from .errors import ParseError
from .lexer import InterpPart, Lexer
from .tokens import T
from .types import PRIMITIVES, ListType

UI_CONTAINERS = {"column", "row"}
UI_LEAVES = {"text", "title", "button", "input", "checkbox", "spacer", "divider"}
UI_ELEMENTS = UI_CONTAINERS | UI_LEAVES

ASSIGN_OPS = {
    T.ASSIGN: "=", T.PLUS_ASSIGN: "+=", T.MINUS_ASSIGN: "-=",
    T.STAR_ASSIGN: "*=", T.SLASH_ASSIGN: "/=",
}
COMPARISON_OPS = {T.EQ: "==", T.NE: "!=", T.LT: "<", T.LE: "<=", T.GT: ">", T.GE: ">="}

DESCRIBE = {
    T.LPAREN: "'('", T.RPAREN: "')'", T.LBRACE: "'{'", T.RBRACE: "'}'",
    T.LBRACKET: "'['", T.RBRACKET: "']'", T.COMMA: "','", T.COLON: "':'",
    T.ASSIGN: "'='", T.IDENT: "identifier", T.STRING: "string", T.EOF: "end of file",
    T.GT: "'>'", T.LT: "'<'", T.IN: "'in'",
}


def describe(tok):
    if tok.type == T.EOF:
        return "end of file"
    return f"'{tok.lexeme}'"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------------- ابزارها ----------------
    @property
    def tok(self):
        return self.tokens[self.pos]

    def peek(self, k=1):
        i = min(self.pos + k, len(self.tokens) - 1)
        return self.tokens[i]

    def check(self, *types):
        return self.tok.type in types

    def match(self, *types):
        if self.tok.type in types:
            t = self.tok
            self.pos += 1
            return t
        return None

    def expect(self, type_, what=None):
        if self.tok.type == type_:
            t = self.tok
            self.pos += 1
            return t
        what = what or DESCRIBE.get(type_, type_.name)
        raise self.error(f"expected {what}, found {describe(self.tok)}")

    def error(self, msg, tok=None):
        tok = tok or self.tok
        return ParseError(msg, tok.line, tok.col)

    def end_statement(self):
        """هر دستور با ';' یا خط جدید یا '}' تمام می‌شود."""
        if self.match(T.SEMI):
            return
        if self.check(T.RBRACE, T.EOF) or self.tok.nl_before:
            return
        raise self.error(f"expected end of statement (newline or ';'), found {describe(self.tok)}")

    # ---------------- برنامه ----------------
    def parse_program(self):
        prog = A.Program(1, 1)
        seen_funs = set()
        while not self.check(T.EOF):
            if self.check(T.FUN):
                f = self.fun_decl()
                if f.name in seen_funs:
                    raise ParseError(f"function '{f.name}' is already defined", f.line, f.col)
                seen_funs.add(f.name)
                prog.functions.append(f)
            elif self.check(T.LET, T.VAR):
                prog.globals.append(self.var_decl())
                self.end_statement()
            elif self.check(T.APP):
                if prog.app is not None:
                    raise self.error("only one 'app' block is allowed")
                prog.app = self.app_decl()
            else:
                raise self.error(
                    f"expected 'fun', 'let', 'var' or 'app' at top level, found {describe(self.tok)}")
        return prog

    # ---------------- انواع ----------------
    def parse_type(self):
        t = self.expect(T.IDENT, "type name")
        if t.value == "List":
            self.expect(T.LT, "'<' after List")
            elem = self.parse_type()
            self.expect(T.GT, "'>'")
            return ListType(elem)
        if t.value in PRIMITIVES:
            return PRIMITIVES[t.value]
        raise ParseError(f"unknown type '{t.value}'", t.line, t.col)

    # ---------------- اعلان‌ها ----------------
    def fun_decl(self):
        start = self.expect(T.FUN)
        name = self.expect(T.IDENT, "function name")
        self.expect(T.LPAREN)
        params = []
        if not self.check(T.RPAREN):
            while True:
                p = self.expect(T.IDENT, "parameter name")
                self.expect(T.COLON, "':' and parameter type")
                params.append(A.Param(p.line, p.col, p.value, self.parse_type()))
                if not self.match(T.COMMA):
                    break
        self.expect(T.RPAREN)
        ret = PRIMITIVES["Void"]
        if self.match(T.COLON):
            ret = self.parse_type()
        body = self.block()
        return A.FunDecl(start.line, start.col, name.value, params, ret, body)

    def var_decl(self):
        kw = self.match(T.LET, T.VAR)
        name = self.expect(T.IDENT, "variable name")
        type_ann = self.parse_type() if self.match(T.COLON) else None
        self.expect(T.ASSIGN, "'=' (variables must be initialized)")
        init = self.expression()
        return A.VarDecl(kw.line, kw.col, kw.type == T.VAR, name.value, type_ann, init)

    def app_decl(self):
        start = self.expect(T.APP)
        title = self.expect(T.STRING, "app title string")
        if any(not isinstance(p, str) for p in title.value):
            raise ParseError("app title cannot contain interpolation", title.line, title.col)
        self.expect(T.LBRACE)
        screens = []
        while not self.check(T.RBRACE):
            if not self.check(T.SCREEN):
                raise self.error(f"expected 'screen' inside app, found {describe(self.tok)}")
            screens.append(self.screen_decl())
        self.expect(T.RBRACE)
        if not screens:
            raise ParseError("app must contain at least one screen", start.line, start.col)
        return A.AppDecl(start.line, start.col, "".join(title.value), screens)

    def screen_decl(self):
        start = self.expect(T.SCREEN)
        name = self.expect(T.IDENT, "screen name")
        self.expect(T.LBRACE)
        states = []
        while self.check(T.STATE):
            kw = self.expect(T.STATE)
            sname = self.expect(T.IDENT, "state name")
            type_ann = self.parse_type() if self.match(T.COLON) else None
            self.expect(T.ASSIGN, "'=' (state must have an initial value)")
            states.append(A.StateDecl(kw.line, kw.col, sname.value, type_ann, self.expression()))
            self.end_statement()
        body = self.ui_nodes()
        self.expect(T.RBRACE)
        return A.ScreenDecl(start.line, start.col, name.value, states, body)

    # ---------------- رابط کاربری ----------------
    def ui_nodes(self):
        nodes = []
        while not self.check(T.RBRACE, T.EOF):
            if self.check(T.STATE):
                raise self.error("state declarations must come at the start of the screen")
            nodes.append(self.ui_node())
            self.match(T.SEMI)
        return nodes

    def ui_block(self):
        self.expect(T.LBRACE)
        nodes = self.ui_nodes()
        self.expect(T.RBRACE)
        return nodes

    def ui_node(self):
        if self.check(T.IF):
            return self.ui_if()
        if self.check(T.FOR):
            start = self.expect(T.FOR)
            var = self.expect(T.IDENT, "loop variable")
            self.expect(T.IN)
            iterable = self.iterable()
            return A.UIFor(start.line, start.col, var.value, iterable, self.ui_block())
        t = self.expect(T.IDENT, "UI element (column, row, text, button, ...)")
        kind = t.value
        if kind not in UI_ELEMENTS:
            raise ParseError(
                f"unknown UI element '{kind}' (expected one of: {', '.join(sorted(UI_ELEMENTS))})",
                t.line, t.col)
        args = []
        if self.match(T.LPAREN):
            args = self.arguments()
        elif kind not in UI_CONTAINERS:
            raise self.error(f"expected '(' after '{kind}'")
        node = A.UIElement(t.line, t.col, kind, args)
        if kind in UI_CONTAINERS:
            node.children = self.ui_block()
        elif kind == "button":
            if not self.check(T.LBRACE):
                raise self.error("button needs an action block: button(\"label\") { ... }")
            node.action = self.block()
        return node

    def ui_if(self):
        start = self.expect(T.IF)
        cond = self.expression()
        then = self.ui_block()
        orelse = None
        if self.match(T.ELSE):
            orelse = [self.ui_if()] if self.check(T.IF) else self.ui_block()
        return A.UIIf(start.line, start.col, cond, then, orelse)

    # ---------------- دستورها ----------------
    def block(self):
        start = self.expect(T.LBRACE)
        stmts = []
        while not self.check(T.RBRACE):
            if self.check(T.EOF):
                raise ParseError("unclosed '{'", start.line, start.col)
            stmts.append(self.statement())
        self.expect(T.RBRACE)
        return A.Block(start.line, start.col, stmts)

    def statement(self):
        t = self.tok
        if t.type in (T.LET, T.VAR):
            s = self.var_decl()
        elif t.type == T.IF:
            return self.if_stmt()
        elif t.type == T.WHILE:
            self.pos += 1
            cond = self.expression()
            return A.While(t.line, t.col, cond, self.block())
        elif t.type == T.FOR:
            self.pos += 1
            var = self.expect(T.IDENT, "loop variable")
            self.expect(T.IN)
            iterable = self.iterable()
            return A.For(t.line, t.col, var.value, iterable, self.block())
        elif t.type == T.RETURN:
            self.pos += 1
            value = None
            if not (self.check(T.RBRACE, T.SEMI, T.EOF) or self.tok.nl_before):
                value = self.expression()
            s = A.Return(t.line, t.col, value)
        elif t.type == T.BREAK:
            self.pos += 1
            s = A.Break(t.line, t.col)
        elif t.type == T.CONTINUE:
            self.pos += 1
            s = A.Continue(t.line, t.col)
        elif t.type == T.IDENT and self.peek().type in ASSIGN_OPS:
            self.pos += 1
            op = ASSIGN_OPS[self.tok.type]
            self.pos += 1
            s = A.Assign(t.line, t.col, t.value, op, self.expression())
        elif t.type == T.LBRACE:
            return self.block()
        else:
            e = self.expression()
            if not isinstance(e, A.Call):
                if self.check(T.ASSIGN, *ASSIGN_OPS):
                    raise self.error("only variables can be assigned (lists are immutable)")
                raise ParseError("only function calls can be used as statements", e.line, e.col)
            s = A.ExprStmt(e.line, e.col, e)
        self.end_statement()
        return s

    def if_stmt(self):
        start = self.expect(T.IF)
        cond = self.expression()
        then = self.block()
        orelse = None
        if self.match(T.ELSE):
            orelse = self.if_stmt() if self.check(T.IF) else self.block()
        return A.If(start.line, start.col, cond, then, orelse)

    def iterable(self):
        start = self.expression()
        op = self.match(T.DOTDOT, T.DOTDOTEQ)
        if op:
            end = self.expression()
            return A.Range(start.line, start.col, start, end, op.type == T.DOTDOTEQ)
        return start

    # ---------------- عبارت‌ها (به ترتیب اولویت) ----------------
    def expression(self):
        return self.or_expr()

    def or_expr(self):
        left = self.and_expr()
        while self.check(T.OR):
            op = self.match(T.OR)
            left = A.Binary(op.line, op.col, "or", left, self.and_expr())
        return left

    def and_expr(self):
        left = self.not_expr()
        while self.check(T.AND):
            op = self.match(T.AND)
            left = A.Binary(op.line, op.col, "and", left, self.not_expr())
        return left

    def not_expr(self):
        if self.check(T.NOT):
            op = self.match(T.NOT)
            return A.Unary(op.line, op.col, "not", self.not_expr())
        return self.comparison()

    def comparison(self):
        left = self.additive()
        if self.tok.type in COMPARISON_OPS:
            op = self.tok
            self.pos += 1
            left = A.Binary(op.line, op.col, COMPARISON_OPS[op.type], left, self.additive())
            if self.tok.type in COMPARISON_OPS:
                raise self.error("comparisons cannot be chained; use 'and' (a < b and b < c)")
        return left

    def additive(self):
        left = self.multiplicative()
        while self.check(T.PLUS, T.MINUS):
            op = self.tok
            self.pos += 1
            left = A.Binary(op.line, op.col, op.lexeme, left, self.multiplicative())
        return left

    def multiplicative(self):
        left = self.unary()
        while self.check(T.STAR, T.SLASH, T.PERCENT):
            op = self.tok
            self.pos += 1
            left = A.Binary(op.line, op.col, op.lexeme, left, self.unary())
        return left

    def unary(self):
        if self.check(T.MINUS):
            op = self.match(T.MINUS)
            operand = self.unary()
            # ثابت‌های منفی را همین‌جا تا می‌کنیم (constant folding)
            if isinstance(operand, A.IntLit):
                return A.IntLit(op.line, op.col, -operand.value)
            if isinstance(operand, A.FloatLit):
                return A.FloatLit(op.line, op.col, -operand.value)
            return A.Unary(op.line, op.col, "-", operand)
        return self.postfix()

    def postfix(self):
        expr = self.primary()
        while True:
            # '(' یا '[' در خط بعد، شروع دستور جدید است نه فراخوانی/اندیس
            if self.check(T.LPAREN) and not self.tok.nl_before:
                if not isinstance(expr, A.Name):
                    raise self.error("only named functions can be called")
                self.pos += 1
                expr = A.Call(expr.line, expr.col, expr.id, self.arguments())
            elif self.check(T.LBRACKET) and not self.tok.nl_before:
                lb = self.match(T.LBRACKET)
                index = self.expression()
                self.expect(T.RBRACKET)
                expr = A.Index(lb.line, lb.col, expr, index)
            else:
                return expr

    def arguments(self):
        """پس از '(' فراخوانی می‌شود و تا ')' را می‌خواند."""
        args = []
        if not self.check(T.RPAREN):
            while True:
                args.append(self.expression())
                if not self.match(T.COMMA):
                    break
        self.expect(T.RPAREN)
        return args

    def primary(self):
        t = self.tok
        if t.type == T.INT:
            self.pos += 1
            return A.IntLit(t.line, t.col, t.value)
        if t.type == T.FLOAT:
            self.pos += 1
            return A.FloatLit(t.line, t.col, t.value)
        if t.type in (T.TRUE, T.FALSE):
            self.pos += 1
            return A.BoolLit(t.line, t.col, t.type == T.TRUE)
        if t.type == T.STRING:
            self.pos += 1
            return A.StringLit(t.line, t.col, [self.interp(p) for p in t.value])
        if t.type == T.IDENT:
            self.pos += 1
            return A.Name(t.line, t.col, t.value)
        if t.type == T.LPAREN:
            self.pos += 1
            e = self.expression()
            self.expect(T.RPAREN)
            return e
        if t.type == T.LBRACKET:
            self.pos += 1
            elems = []
            if not self.check(T.RBRACKET):
                while True:
                    elems.append(self.expression())
                    if not self.match(T.COMMA) or self.check(T.RBRACKET):
                        break
            self.expect(T.RBRACKET)
            return A.ListLit(t.line, t.col, elems)
        raise self.error(f"expected an expression, found {describe(t)}")

    def interp(self, part):
        """بخش {...} داخل رشته را با یک Lexer/Parser جدا تجزیه می‌کند."""
        if isinstance(part, str):
            return part
        assert isinstance(part, InterpPart)
        tokens = Lexer(part.source, part.line, part.col).tokenize()
        sub = Parser(tokens)
        e = sub.expression()
        if not sub.check(T.EOF):
            raise sub.error("unexpected token in string interpolation")
        return e


def parse(source):
    return Parser(Lexer(source).tokenize()).parse_program()
