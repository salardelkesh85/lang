"""خطاهای کامپایلر نوا.

همهٔ خطاها از NovaError ارث می‌برند و موقعیت (سطر/ستون) دارند تا
بتوانیم پیام خطا را همراه با نمایش خط کد و یک نشانگر ^ چاپ کنیم.
"""


class NovaError(Exception):
    kind = "error"

    def __init__(self, message, line=0, col=0):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col

    def format(self, source=None, filename="<input>"):
        out = f"{filename}:{self.line}:{self.col}: {self.kind}: {self.message}"
        if source and self.line > 0:
            lines = source.splitlines()
            if self.line <= len(lines):
                text = lines[self.line - 1]
                out += f"\n    {text}\n    {' ' * max(self.col - 1, 0)}^"
        return out

    def __str__(self):
        return self.format()


class LexError(NovaError):
    kind = "lexical error"


class ParseError(NovaError):
    kind = "syntax error"


class NovaTypeError(NovaError):
    kind = "type error"


class NovaRuntimeError(NovaError):
    kind = "runtime error"
