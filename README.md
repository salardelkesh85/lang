# Nova ✦ زبان برنامه‌نویسی برای اندروید

**Nova** یک زبان برنامه‌نویسی با تایپ ایستاست که برای ساخت اپلیکیشن‌های اندروید طراحی شده است. کامپایلر Nova برنامه را به **Kotlin + Jetpack Compose** ترجمه می‌کند و یک پروژهٔ کامل **Android Studio** تحویل می‌دهد.

> پروژهٔ درس **طراحی زبان‌های برنامه‌نویسی**

```nova
app "شمارنده" {
    screen Main {
        state count: Int = 0

        title("شمارنده")
        text("مقدار فعلی: {count}", 28)
        row {
            button("−") { count -= 1 }
            button("+") { count += 1 }
        }
        button("صفر کن") {
            count = 0
            toast("شمارنده صفر شد")
        }
    }
}
```

## ویژگی‌ها
- **تایپ ایستا با استنتاج نوع:** `let x = 5` یعنی x از نوع `Int` است؛ خطاها قبل از اجرا گرفته می‌شوند
- **ساختارهای ویژهٔ اندروید در خود زبان:** `app`، `screen`، `state`، `button`، `input`، `navigate` و ...
- **شناسه و ارقام فارسی:** `let قیمت = ۲۵۰۰۰`
- **درون‌یابی رشته:** `"سلام {name}، شما {age} سال دارید"`
- **لیست‌های تغییرناپذیر** که با مدل واکنشی Compose هماهنگ‌اند
- **پیام‌های خطای دقیق** با شمارهٔ سطر و ستون
- **شبیه‌ساز ترمینال** برای اجرای اپ بدون گوشی
- **تست تفاضلی:** خروجی مفسر با خروجی Kotlin واقعی مقایسه می‌شود

## شروع سریع
پیش‌نیاز: Python 3.9 یا بالاتر (بدون هیچ کتابخانهٔ اضافه)

```bash
python -m nova run examples/hello.nova
```
```bash
python -m nova sim examples/todo.nova
```
```bash
python -m nova build examples/bmi.nova -o build/bmi --package com.example.bmi
```
سپس پوشهٔ `build/bmi` را در Android Studio باز کنید و دکمهٔ Run را بزنید.

### همهٔ دستورها
| دستور | کار |
|---|---|
| `python -m nova tokens FILE` | نمایش توکن‌ها (خروجی فاز تحلیل واژگانی) |
| `python -m nova ast FILE` | نمایش درخت نحو انتزاعی |
| `python -m nova check FILE` | فقط بررسی خطاها |
| `python -m nova run FILE` | اجرای `main()` با مفسر |
| `python -m nova sim FILE` | اجرای اپ در شبیه‌ساز (`--do 2 --do "1=متن"` برای اجرای خودکار) |
| `python -m nova kotlin FILE` | نمایش کد Kotlin تولیدشده |
| `python -m nova build FILE -o DIR` | ساخت پروژهٔ Android Studio |

## مثال‌ها
| فایل | چه چیزی را نشان می‌دهد |
|---|---|
| [`examples/hello.nova`](examples/hello.nova) | مبانی زبان: توابع، بازگشت، حلقه‌ها، لیست‌ها، اعداد |
| [`examples/counter.nova`](examples/counter.nova) | ساده‌ترین اپ: state و دکمه |
| [`examples/todo.nova`](examples/todo.nova) | ورودی متن، لیست، حلقه داخل UI، چک‌باکس |
| [`examples/bmi.nova`](examples/bmi.nova) | دو صفحه و ناوبری، توابع محاسباتی |
| [`examples/dice.nova`](examples/dice.nova) | اعداد تصادفی و متغیر سراسری |

## مستندات
- [مرجع کامل زبان](docs/language-reference.md)
- [گرامر (EBNF)](docs/grammar.md)
- [معماری کامپایلر](docs/compiler-architecture.md)
- [مطالب ارائه (اسلاید به اسلاید)](docs/presentation-outline.md)

## ساختار پروژه
```
nova/                  کامپایلر (پایتون، بدون وابستگی)
  lexer.py             فاز ۱: تحلیل واژگانی
  parser.py            فاز ۲: تحلیل نحوی (نزولی بازگشتی)
  checker.py           فاز ۳: تحلیل معنایی و بررسی نوع
  interpreter.py       مفسر درخت‌پیما
  simulator.py         شبیه‌ساز اپ در ترمینال
  codegen_kotlin.py    فاز ۴: تولید کد Kotlin / Jetpack Compose
  android_project.py   ساخت پروژهٔ Gradle
examples/              برنامه‌های نمونه
tests/                 تست‌های واحد و تست تفاضلی
docs/                  مستندات فارسی
```

## اجرای تست‌ها
```bash
python -m unittest discover tests
```
```bash
python tests/kotlin_diff.py
```
دومی به Gradle و JDK 17 یا بالاتر نیاز دارد. برنامه‌های `tests/programs/` را با Kotlin واقعی کامپایل و اجرا می‌کند و خروجی را با مفسر مقایسه می‌کند.
