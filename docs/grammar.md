# گرامر زبان Nova (EBNF)

نمادگذاری: `{ x }` یعنی صفر یا چند بار، `[ x ]` یعنی اختیاری، `|` یعنی «یا»، و رشته‌های داخل `"..."` توکن‌های ثابت‌اند.

## ۱. واژگان (Lexical Grammar)

```ebnf
letter      = ? هر حرف یونیکد (لاتین، فارسی، ...) ? | "_" ;
digit       = ? هر رقم دهدهی یونیکد: 0-9 یا ۰-۹ یا ٠-٩ ? ;

IDENT       = letter { letter | digit } ;          (* نباید با nv_ شروع شود *)
INT         = digit { digit | "_" } ;              (* حداکثر 2147483647 *)
FLOAT       = digit { digit } "." digit { digit } [ exponent ]
            | digit { digit } exponent ;
exponent    = ( "e" | "E" ) [ "+" | "-" ] digit { digit } ;
STRING      = '"' { char | escape | "{" expr "}" } '"' ;
escape      = "\n" | "\t" | '\"' | "\\" | "\{" | "\}" ;

comment     = "//" { ? هر کاراکتر جز خط جدید ? }
            | "/*" { ? هر کاراکتر ? } "*/" ;
```

**کلمات کلیدی (۱۹ کلمه):**
`let var fun return if else while for in break continue true false and or not app screen state`

**عملگرها و جداکننده‌ها:**
`+ - * / % = += -= *= /= == != < <= > >= .. ..= ( ) { } [ ] , : ;`

## ۲. نحو (Syntactic Grammar)

```ebnf
(* ---------- برنامه ---------- *)
program      = { topDecl } EOF ;
topDecl      = funDecl | varDecl end | appDecl ;

(* ---------- انواع ---------- *)
type         = "Int" | "Float" | "Bool" | "String" | "Void"
             | "List" "<" type ">" ;

(* ---------- اعلان‌ها ---------- *)
funDecl      = "fun" IDENT "(" [ param { "," param } ] ")" [ ":" type ] block ;
param        = IDENT ":" type ;
varDecl      = ( "let" | "var" ) IDENT [ ":" type ] "=" expr ;

appDecl      = "app" STRING "{" screenDecl { screenDecl } "}" ;
screenDecl   = "screen" IDENT "{" { stateDecl } { uiNode } "}" ;
stateDecl    = "state" IDENT [ ":" type ] "=" expr end ;

(* ---------- رابط کاربری ---------- *)
uiNode       = uiIf | uiFor | uiElement ;
uiIf         = "if" expr uiBlock [ "else" ( uiIf | uiBlock ) ] ;
uiFor        = "for" IDENT "in" iterable uiBlock ;
uiBlock      = "{" { uiNode } "}" ;
uiElement    = ( "column" | "row" ) [ "(" ")" ] uiBlock
             | "button" "(" args ")" block
             | ( "text" | "title" | "input" | "checkbox"
               | "spacer" | "divider" ) "(" [ args ] ")" ;

(* ---------- دستورها ---------- *)
block        = "{" { stmt } "}" ;
stmt         = varDecl end
             | IDENT assignOp expr end
             | "if" expr block [ "else" ( ifStmt | block ) ]
             | "while" expr block
             | "for" IDENT "in" iterable block
             | "return" [ expr ] end
             | "break" end
             | "continue" end
             | call end
             | block ;
assignOp     = "=" | "+=" | "-=" | "*=" | "/=" ;
iterable     = expr [ ( ".." | "..=" ) expr ] ;
end          = ";" | NEWLINE | ? قبل از "}" ? ;

(* ---------- عبارت‌ها (از کم‌اولویت به پراولویت) ---------- *)
expr         = orExpr ;
orExpr       = andExpr { "or" andExpr } ;
andExpr      = notExpr { "and" notExpr } ;
notExpr      = "not" notExpr | comparison ;
comparison   = additive [ compOp additive ] ;          (* زنجیره ممنوع است *)
compOp       = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
additive     = multiplicative { ( "+" | "-" ) multiplicative } ;
multiplicative = unary { ( "*" | "/" | "%" ) unary } ;
unary        = "-" unary | postfix ;
postfix      = primary { call_suffix | index_suffix } ;   (* فقط اگر در همان خط باشد *)
call_suffix  = "(" [ args ] ")" ;
index_suffix = "[" expr "]" ;
args         = expr { "," expr } ;
primary      = INT | FLOAT | STRING | "true" | "false" | IDENT
             | "(" expr ")"
             | "[" [ expr { "," expr } [ "," ] ] "]" ;
```

## ۳. نکات طراحی گرامر

1. **LL(1):** در هر نقطه، توکن بعدی مشخص می‌کند کدام قاعده اعمال شود. تنها استثنا تشخیص انتساب (`x = …`) از فراخوانی (`x(…)`) است که با دیدن توکن دوم حل می‌شود (LL(2) محلی).
2. **بدون ابهام dangling-else:** چون بدنهٔ `if` همیشه داخل `{ }` است، `else` همیشه به نزدیک‌ترین `if` تعلق دارد و ابهامی وجود ندارد.
3. **شرط بدون پرانتز:** چون بدنه با `{` شروع می‌شود، پایان شرط مشخص است: `if x > 0 { ... }`.
4. **حساسیت به خط جدید فقط در یک جا:** `(` و `[` اگر در خط جدید باشند، فراخوانی/اندیس محسوب نمی‌شوند. بنابراین `;` لازم نیست.
5. **اولویت `not` کمتر از مقایسه است:** `not a == b` یعنی `not (a == b)`، که طبیعی‌تر از رفتار `!` در C/Kotlin است.
6. **مقایسهٔ زنجیره‌ای ممنوع است:** `1 < x < 5` خطای نحوی می‌دهد تا با معنای ریاضی آن اشتباه نشود.
