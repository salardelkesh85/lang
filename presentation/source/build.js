// Nova presentation builder
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "Nova — زبان برنامه‌نویسی برای اندروید";
pres.author = "Nova";
pres.theme = { headFontFace: "Vazirmatn Black", bodyFontFace: "Vazirmatn" };

const SW = 13.333, SH = 7.5, M = 0.6;
const COL = {
  text: "F5F3FF", muted: "B4B0D9", dim: "7C78A8",
  violet: "A78BFA", violetD: "7C3AED", cyan: "22D3EE", pink: "F472B6",
  amber: "FBBF24", green: "34D399", red: "FB7185",
  card: "1A1640", cardLine: "4C4594", codeBg: "0C0A22",
};
const FA = "Vazirmatn", FA_B = "Vazirmatn ExtraBold", FA_BL = "Vazirmatn Black", FA_M = "Vazirmatn Medium";
const ORB = "Orbitron Black", ORB_B = "Orbitron", ORB_M = "Orbitron Medium";
const MONO = "JetBrains Mono";
const A = "assets/";
const TOTAL = 19;

// ---------------- layouts ----------------
pres.defineSlideMaster({
  title: "NOVA_HERO",
  background: { path: A + "bg_hero.jpg" },
});
pres.defineSlideMaster({
  title: "NOVA_MAIN",
  background: { path: A + "bg_main.jpg" },
  slideNumber: { x: 0.6, y: 6.98, w: 1.2, h: 0.3, fontFace: MONO, fontSize: 10, color: COL.dim, align: "left" },
});

// ---------------- animation tagging ----------------
let animSeq = 0;
function anim(effect, delay, dur = 700) {
  return `anim|${effect}|${delay}|${dur}|${animSeq++}`;
}

// ---------------- helpers ----------------
function fa(slide, text, o) {
  const opts = {
    fontFace: FA, color: COL.text, fontSize: 16, rtlMode: true, align: "right", lang: "fa-IR",
    isTextBox: true, margin: 0, valign: "top", ...o,
  };
  slide.addText(text, opts);
}

function en(slide, text, o) {
  slide.addText(text, { fontFace: ORB_B, color: COL.cyan, fontSize: 12, align: "left", isTextBox: true, margin: 0, lang: "en-US", ...o });
}

function chrome(slide, n, kicker, title, orbs) {
  // morphing background glows + logo (same names on every slide -> Morph animates them)
  const [a, b] = orbs;
  slide.addImage({ path: A + "orb_violet.png", x: a[0], y: a[1], w: a[2], h: a[2], transparency: 20, objectName: "!!orbA" });
  slide.addImage({ path: A + "orb_cyan.png", x: b[0], y: b[1], w: b[2], h: b[2], transparency: 35, objectName: "!!orbB" });
  slide.addImage({ path: A + "nova_star.png", x: 0.45, y: 0.32, w: 0.75, h: 0.75, objectName: "!!logo" });
  en(slide, "NOVA", { x: 1.15, y: 0.55, w: 1.5, h: 0.3, fontFace: ORB, fontSize: 13, color: COL.text, charSpacing: 6, objectName: "!!wordmark" });
  if (kicker) {
    en(slide, kicker, { x: SW - M - 6, y: 0.42, w: 6, h: 0.3, align: "right", fontSize: 11, charSpacing: 5, color: COL.cyan,
      objectName: anim("fade", 0, 500) });
  }
  if (title) {
    fa(slide, title, { x: M + 2.3, y: 0.72, w: SW - 2 * M - 2.3, h: 0.85, fontFace: FA_BL, fontSize: 34, color: COL.text,
      objectName: anim("rise", 150, 700) });
  }
}

function card(slide, x, y, w, h, o = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: o.r ?? 0.14,
    fill: { color: o.fill ?? COL.card, transparency: o.t ?? 35 },
    line: { color: o.line ?? COL.cardLine, width: o.lw ?? 1, transparency: o.lt ?? 20 },
    shadow: o.glow === false ? undefined : { type: "outer", color: o.glowColor ?? "7C3AED", blur: o.blur ?? 18, offset: 0, angle: 90, opacity: o.glowOp ?? 0.35 },
    objectName: o.name,
  });
}

function icon(slide, name, x, y, s, animName) {
  slide.addImage({ path: `${A}icons/${name}.png`, x, y, w: s, h: s, objectName: animName });
}

// ---- syntax highlighting ----
const NOVA_KW = new Set("let var fun return if else while for in break continue true false and or not app screen state".split(" "));
const NOVA_FN = new Set("column row text title button input checkbox spacer divider print len toast navigate back remove str int float format random sqrt abs contains".split(" "));
const KT_KW = new Set("val var fun return if else while for in until true false class override when by import package private".split(" "));
const KT_FN = new Set("Text Button Column Row OutlinedTextField Checkbox Spacer Modifier remember rememberSaveable mutableStateOf println listOf emptyList".split(" "));
const TYPES = new Set("Int Float Bool String Void List Double Boolean Unit".split(" "));

function highlight(code, lang = "nova", size = 13) {
  const kw = lang === "kotlin" ? KT_KW : NOVA_KW;
  const fn = lang === "kotlin" ? KT_FN : NOVA_FN;
  const runs = [];
  const lines = code.split("\n");
  const re = /(\/\/.*$)|("(?:[^"\\]|\\.)*")|([0-9]+(?:\.[0-9]+)?|[۰-۹]+)|([A-Za-z_؀-ۿ][\w؀-ۿ‌]*)|(\s+)|(.)/gu;
  lines.forEach((line, li) => {
    const parts = [];
    let m;
    re.lastIndex = 0;
    while ((m = re.exec(line)) !== null) {
      if (m[0] === "") { re.lastIndex++; continue; }
      let color = "E4E2F5", italic = false, bold = false;
      if (m[1]) { color = "6E6A99"; italic = true; }
      else if (m[2]) color = "86EFAC";
      else if (m[3]) color = COL.amber;
      else if (m[4]) {
        if (kw.has(m[4])) { color = "C084FC"; bold = true; }
        else if (fn.has(m[4])) color = "67E8F9";
        else if (TYPES.has(m[4])) color = COL.pink;
      } else if (m[6] && "{}()[]".includes(m[6])) color = "9CA3AF";
      else if (m[6]) color = "F9A8D4";
      parts.push({ text: m[0], options: { color, italic, bold } });
    }
    if (parts.length === 0) parts.push({ text: " ", options: {} });
    parts[parts.length - 1].options.breakLine = li < lines.length - 1;
    runs.push(...parts);
  });
  return runs;
}

function codeWindow(slide, x, y, w, h, code, o = {}) {
  card(slide, x, y, w, h, { fill: COL.codeBg, t: 8, r: 0.12, glowColor: o.glow ?? "22D3EE", glowOp: 0.3, name: o.anim });
  const dots = ["FF5F57", "FEBC2E", "28C840"];
  dots.forEach((c, i) => slide.addShape(pres.shapes.OVAL, { x: x + 0.22 + i * 0.22, y: y + 0.18, w: 0.12, h: 0.12, fill: { color: c }, line: { color: c, width: 0 }, objectName: o.anim ? o.anim + "_d" + i : undefined }));
  if (o.file) slide.addText(o.file, { x: x + 1.0, y: y + 0.1, w: w - 1.2, h: 0.28, fontFace: MONO, fontSize: 10, color: COL.dim, align: "right", margin: 0, isTextBox: true });
  slide.addText(highlight(code, o.lang, o.size ?? 13), {
    x: x + 0.3, y: y + 0.5, w: w - 0.5, h: h - 0.62, fontFace: MONO, fontSize: o.size ?? 13, valign: "top",
    align: "left", margin: 0, isTextBox: true, lineSpacingMultiple: 1.12, lang: "en-US",
  });
}

function stat(slide, x, y, w, big, label, color, delay, o = {}) {
  slide.addText(big, { x, y, w, h: o.bh ?? 1.0, fontFace: ORB, fontSize: o.size ?? 54, color, align: "center", margin: 0, isTextBox: true,
    glow: { size: 14, opacity: 0.45, color }, objectName: anim("zoom", delay, 700) });
  fa(slide, label, { x, y: y + (o.bh ?? 1.0) + 0.05, w, h: 0.5, align: "center", fontSize: 14, color: COL.muted, objectName: anim("fade", delay + 250, 600) });
}

// ===================================================================
// SLIDE 1 — Cover
// ===================================================================
pres.addSection({ title: "شروع" });
{
  const s = pres.addSlide({ masterName: "NOVA_HERO", sectionTitle: "شروع" });
  s.addImage({ path: A + "orb_violet.png", x: 3.2, y: -1.4, w: 7, h: 7, transparency: 30, objectName: "!!orbA" });
  s.addImage({ path: A + "orb_cyan.png", x: 9.5, y: -1.5, w: 5, h: 5, transparency: 45, objectName: "!!orbB" });
  s.addImage({ path: A + "nova_star.png", x: SW / 2 - 1.9, y: 0.05, w: 3.8, h: 3.8, objectName: "!!logo" });
  en(s, "NOVA", { x: 0, y: 3.55, w: SW, h: 1.3, fontFace: ORB, fontSize: 96, color: "FFFFFF", align: "center", charSpacing: 40,
    glow: { size: 22, opacity: 0.55, color: "A78BFA" }, objectName: "!!wordmark" });
  fa(s, "زبان برنامه‌نویسی نسل آینده برای اندروید", { x: 1, y: 4.95, w: SW - 2, h: 0.6, align: "center", fontFace: FA_B, fontSize: 26,
    color: "E9E5FF", objectName: anim("rise", 900, 800) });
  en(s, "STATICALLY TYPED  ·  KOTLIN + COMPOSE  ·  PERSIAN-FRIENDLY", { x: 1, y: 5.65, w: SW - 2, h: 0.3, align: "center",
    fontSize: 10.5, charSpacing: 4, color: COL.cyan, objectName: anim("fade", 1400, 800) });
  card(s, SW / 2 - 3.6, 6.25, 7.2, 0.62, { r: 0.31, t: 45, glowOp: 0.25, name: anim("fade", 1800, 800) });
  fa(s, "درس طراحی زبان‌های برنامه‌نویسی   |   ارائه‌دهنده: نام شما   |   استاد: نام استاد", { x: SW / 2 - 3.4, y: 6.36, w: 6.8, h: 0.4,
    align: "center", fontSize: 13, color: COL.muted, objectName: anim("fade", 1900, 800) });
  s.addNotes("سلام. امروز Nova را معرفی می‌کنم؛ یک زبان برنامه‌نویسی که برای ساخت اپلیکیشن‌های اندروید طراحی کرده‌ام. Nova یعنی ستارهٔ نو: ستاره‌ای که ناگهان درخشان می‌شود. هدف: اپ اندروید را با یک دهم کد بسازیم، بدون از دست دادن ایمنی نوع.");
}

// ===================================================================
// SLIDE 2 — Problem
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "شروع" });
  chrome(s, 2, "01 · THE PROBLEM", "ساختن یک اپ ساده، چرا این‌قدر سخت است؟", [[-1.5, 3.2, 6], [9.6, -1.8, 5.5]]);
  const pains = [
    ["layers", "چندین فایل پیکربندی", "Gradle، Manifest، Activity و Theme، فقط برای یک دکمه"],
    ["bolt", "ده‌ها خط کد تکراری", "Boilerplate: کدی که هر بار باید از نو نوشته شود"],
    ["stairs", "منحنی یادگیری سنگین", "State، Recomposition، Lambda و Delegate برای یک مبتدی"],
  ];
  pains.forEach(([ic, t, d], i) => {
    const y = 2.05 + i * 1.55;
    card(s, 6.55, y, 6.2, 1.3, { name: anim("slideL", 400 + i * 250, 700) });
    icon(s, ic, 11.6, y + 0.22, 0.86, anim("zoom", 550 + i * 250, 600));
    fa(s, t, { x: 6.85, y: y + 0.22, w: 4.6, h: 0.45, fontFace: FA_B, fontSize: 19, objectName: anim("fade", 600 + i * 250, 600) });
    fa(s, d, { x: 6.85, y: y + 0.7, w: 4.6, h: 0.45, fontSize: 13.5, color: COL.muted, objectName: anim("fade", 650 + i * 250, 600) });
  });
  // big comparison
  card(s, M, 2.05, 5.55, 4.4, { t: 55, name: anim("fade", 300, 700) });
  fa(s, "یک اپ «شمارنده» با یک دکمه", { x: M + 0.3, y: 2.3, w: 4.95, h: 0.45, align: "center", fontSize: 15, color: COL.muted, objectName: anim("fade", 400, 600) });
  stat(s, M + 0.25, 2.95, 2.4, "50+", "خط در Kotlin", COL.red, 1300);
  stat(s, M + 2.9, 2.95, 2.4, "10", "خط در Nova", COL.green, 1900, { size: 66 });
  s.addImage({ path: A + "beam.png", x: M + 0.5, y: 5.05, w: 4.55, h: 0.3, objectName: anim("wipe", 2300, 900) });
  fa(s, "۸۰٪ کد کمتر، همان خروجی بومی اندروید", { x: M + 0.3, y: 5.5, w: 4.95, h: 0.5, align: "center", fontFace: FA_B, fontSize: 17, color: COL.text, objectName: anim("rise", 2500, 700) });
  s.addNotes("برای یک اپ ساده با یک عدد و یک دکمه، در Kotlin حدود ۵۰ خط کد و چند فایل پیکربندی لازم است. مبتدی باید State، Recomposition و Lambda را یاد بگیرد. Nova همین را در ۱۰ خط انجام می‌دهد.");
}

// ===================================================================
// SLIDE 3 — Design goals
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "شروع" });
  chrome(s, 3, "02 · DESIGN GOALS", "پنج اصل طراحی Nova", [[8.5, 3.5, 6.5], [-1.2, -1.5, 5]]);
  const goals = [
    ["wand", "سادگی", "نحو کوتاه و خوانا؛ بدون ; و بدون پرانتز دور شرط"],
    ["shield", "ایمنی", "تایپ ایستا؛ خطاها قبل از اجرا گرفته می‌شوند"],
    ["phone", "اندروید‌محور", "صفحه، state و UI جزو خودِ زبان‌اند"],
    ["bridge", "سازگاری", "خروجی: Kotlin + Jetpack Compose، فناوری رسمی گوگل"],
    ["persian", "فارسی‌دوست", "شناسه، رشته و ارقام فارسی: let قیمت = ۲۵۰۰۰"],
  ];
  const w = 2.25, gap = 0.22, total = goals.length * w + (goals.length - 1) * gap;
  goals.forEach(([ic, t, d], i) => {
    const x = SW - M - w - i * (w + gap) - (SW - 2 * M - total) / 2;
    const y = 2.25;
    const d0 = 400 + i * 220;
    card(s, x, y, w, 4.2, { name: anim("rise", d0, 750), glowColor: ["22D3EE", "A78BFA", "34D399", "FBBF24", "F472B6"][i] });
    icon(s, ic, x + w / 2 - 0.6, y + 0.4, 1.2, anim("zoom", d0 + 200, 600));
    en(s, `0${i + 1}`, { x: x + 0.2, y: y + 0.2, w: 0.6, h: 0.3, fontFace: ORB_M, fontSize: 11, color: COL.dim });
    fa(s, t, { x: x + 0.15, y: y + 1.85, w: w - 0.3, h: 0.5, align: "center", fontFace: FA_BL, fontSize: 21, objectName: anim("fade", d0 + 300, 600) });
    fa(s, d, { x: x + 0.2, y: y + 2.5, w: w - 0.4, h: 1.5, align: "center", fontSize: 13.5, color: COL.muted, objectName: anim("fade", d0 + 350, 600) });
  });
  s.addNotes("پنج هدف اصلی: سادگی، ایمنی با تایپ ایستا، اندروید‌محور بودن یعنی صفحه و state در خود زبان، سازگاری چون خروجی کد Kotlin و Compose است، و فارسی‌دوست بودن.");
}

// ===================================================================
// SLIDE 4 — Nova at a glance (code -> phone)
// ===================================================================
const COUNTER = `app "شمارنده" {
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
}`;
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "شروع" });
  chrome(s, 4, "03 · NOVA AT A GLANCE", "۱۶ خط کد، یک اپ اندروید کامل", [[3.8, 1.2, 6], [-1.5, 3.8, 5]]);
  codeWindow(s, 5.55, 1.95, 7.2, 5.0, COUNTER, { file: "counter.nova", anim: anim("slideL", 300, 800), size: 13.5 });
  // arrow
  s.addImage({ path: A + "beam.png", x: 3.55, y: 4.25, w: 1.9, h: 0.22, objectName: anim("wipeR", 1300, 700) });
  en(s, "COMPILE", { x: 3.6, y: 3.85, w: 1.8, h: 0.3, align: "center", fontSize: 10, charSpacing: 4, color: COL.cyan, objectName: anim("fade", 1400, 500) });
  // phone
  const px = 0.75, py = 1.65, pw = 2.75, ph = 5.5;
  s.addImage({ path: A + "phone.png", x: px, y: py, w: pw, h: ph, objectName: anim("zoom", 1700, 800) });
  const sx = px + pw * 70 / 600, sw = pw * 460 / 600;
  const t0 = 2200;
  fa(s, "شمارنده", { x: sx, y: py + 0.75, w: sw, h: 0.5, fontFace: FA_BL, fontSize: 20, objectName: anim("fade", t0, 500) });
  fa(s, "مقدار فعلی: ۷", { x: sx, y: py + 1.35, w: sw, h: 0.6, fontFace: FA_B, fontSize: 22, color: COL.violet, objectName: anim("fade", t0 + 150, 500) });
  const btn = (label, x, y, w, d, fill = "8B5CF6") => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.48, rectRadius: 0.24, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: anim("zoom", d, 400) });
    fa(s, label, { x, y: y + 0.07, w, h: 0.36, align: "center", fontFace: FA_B, fontSize: 14, color: "FFFFFF", objectName: anim("fade", d + 50, 400) });
  };
  btn("+", sx + sw - 0.85, py + 2.2, 0.85, t0 + 300);
  btn("−", sx + sw - 1.85, py + 2.2, 0.85, t0 + 400);
  btn("صفر کن", sx + sw - 1.4, py + 2.9, 1.4, t0 + 500);
  // toast
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: sx + 0.2, y: py + ph - 1.15, w: sw - 0.4, h: 0.45, rectRadius: 0.22, fill: { color: "2E2A55" }, line: { color: "4C4594", width: 0.75 }, objectName: anim("rise", t0 + 900, 500) });
  fa(s, "شمارنده صفر شد", { x: sx + 0.2, y: py + ph - 1.08, w: sw - 0.4, h: 0.32, align: "center", fontSize: 11.5, color: COL.text, objectName: anim("fade", t0 + 950, 400) });
  s.addNotes("این کل کد یک اپ شمارنده است. app عنوان اپ است، screen یک صفحه، و state یک متغیر واکنش‌گرا: هر بار تغییر کند، صفحه خودکار دوباره رسم می‌شود. خروجی کامپایلر یک پروژهٔ کامل Android Studio است که روی گوشی اجرا می‌شود.");
}

// ===================================================================
// SLIDE 5 — Language identity
// ===================================================================
pres.addSection({ title: "زبان" });
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "زبان" });
  chrome(s, 5, "04 · LANGUAGE DNA", "شناسنامهٔ زبان", [[9.2, 3.2, 6], [1.5, -2, 5.5]]);
  const items = [
    ["orbit", "پارادایم", "امری (Imperative) + اعلانی برای UI"],
    ["cube", "سیستم نوع", "ایستا و قوی؛ تبدیل ضمنی فقط Int به Float"],
    ["target", "استنتاج نوع", "let x = 5 یعنی x از نوع Int است"],
    ["layers", "حوزهٔ نام‌ها", "ایستا (Lexical) با بلوک‌های تودرتو"],
    ["infinity", "مدیریت حافظه", "خودکار با Garbage Collector در ART"],
    ["gear", "پیاده‌سازی", "Transpiler به Kotlin + مفسر درخت‌پیما"],
  ];
  const cw = 3.85, chh = 2.15;
  items.forEach(([ic, t, d], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = SW - M - cw - col * (cw + 0.3), y = 1.95 + row * (chh + 0.3);
    const d0 = 350 + i * 170;
    card(s, x, y, cw, chh, { name: anim("zoom", d0, 650), glowColor: row ? "22D3EE" : "A78BFA" });
    icon(s, ic, x + cw - 1.15, y + 0.3, 0.85, anim("fade", d0 + 200, 500));
    fa(s, t, { x: x + 0.25, y: y + 0.42, w: cw - 1.5, h: 0.5, fontFace: FA_BL, fontSize: 20, objectName: anim("fade", d0 + 250, 500) });
    fa(s, d, { x: x + 0.25, y: y + 1.25, w: cw - 0.5, h: 0.75, fontSize: 14, color: COL.muted, objectName: anim("fade", d0 + 300, 500) });
  });
  s.addNotes("از نظر دسته‌بندی زبان‌ها: Nova امری است و برای رابط کاربری یک زیرزبان اعلانی دارد. تایپ ایستا و قوی با استنتاج نوع محلی، حوزهٔ ایستا، و حافظهٔ خودکار. پیاده‌سازی به دو روش است: ترجمه به Kotlin و مفسر برای اجرای فوری.");
}

// ===================================================================
// SLIDE 6 — Type system
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "زبان" });
  chrome(s, 6, "05 · TYPE SYSTEM", "انواع داده و نگاشت به Kotlin", [[-1.8, 2.5, 6], [8.8, 3.6, 5]]);
  const types = [
    ["Int", "Int", "42 · ۱۴۰۳", COL.cyan],
    ["Float", "Double", "3.14 · 2.5e-3", COL.violet],
    ["Bool", "Boolean", "true · false", COL.green],
    ["String", "String", "\"سلام {name}\"", COL.amber],
    ["List<T>", "List<T>", "[1, 2, 3]", COL.pink],
    ["Void", "Unit", "تابع بدون خروجی", COL.dim],
  ];
  fa(s, "Nova", { x: 10.35, y: 1.9, w: 2.4, h: 0.35, align: "center", fontFace: ORB_B, fontSize: 12, color: COL.dim, rtlMode: false });
  fa(s, "Kotlin", { x: 7.35, y: 1.9, w: 2.2, h: 0.35, align: "center", fontFace: ORB_B, fontSize: 12, color: COL.dim, rtlMode: false });
  types.forEach(([n, k, ex, c], i) => {
    const y = 2.35 + i * 0.73, d0 = 300 + i * 160;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.35, y, w: 2.4, h: 0.55, rectRadius: 0.27, fill: { color: c, transparency: 82 }, line: { color: c, width: 1.25 }, objectName: anim("slideL", d0, 500) });
    s.addText(n, { x: 10.35, y, w: 2.4, h: 0.55, align: "center", valign: "middle", fontFace: MONO, fontSize: 15, bold: true, color: c, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 50, 400) });
    s.addImage({ path: A + "beam.png", x: 9.6, y: y + 0.17, w: 0.7, h: 0.2, objectName: anim("wipeR", d0 + 200, 400) });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.35, y, w: 2.2, h: 0.55, rectRadius: 0.27, fill: { color: COL.card, transparency: 30 }, line: { color: COL.cardLine, width: 1 }, objectName: anim("fade", d0 + 300, 400) });
    s.addText(k, { x: 7.35, y, w: 2.2, h: 0.55, align: "center", valign: "middle", fontFace: MONO, fontSize: 14, color: COL.text, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 320, 400) });
    s.addText(ex, { x: 4.9, y, w: 2.3, h: 0.55, align: "center", valign: "middle", fontFace: MONO, fontSize: 12, color: COL.muted, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 350, 400) });
  });
  // callout
  card(s, M, 2.35, 4.0, 4.3, { glowColor: "F472B6", name: anim("rise", 1500, 800) });
  icon(s, "shield", M + 3.0, 2.6, 0.75, anim("zoom", 1700, 500));
  fa(s, "چرا لیست‌ها تغییرناپذیرند؟", { x: M + 0.25, y: 2.7, w: 2.7, h: 0.8, fontFace: FA_BL, fontSize: 17, objectName: anim("fade", 1750, 500) });
  fa(s, "Compose فقط وقتی صفحه را دوباره رسم می‌کند که «مقدار» state عوض شود. تغییر درجای لیست، باگ رایج اندروید است.", { x: M + 0.25, y: 3.6, w: 3.5, h: 1.6, fontSize: 13.5, color: COL.muted, objectName: anim("fade", 1850, 500) });
  s.addText("tasks = tasks + [x]", { x: M + 0.25, y: 5.35, w: 3.5, h: 0.45, fontFace: MONO, fontSize: 13, color: COL.green, align: "left", margin: 0, isTextBox: true, objectName: anim("fade", 2000, 500) });
  fa(s, "یک دستهٔ کامل از باگ‌ها، در سطح طراحی زبان حذف شد", { x: M + 0.25, y: 5.85, w: 3.5, h: 0.65, fontFace: FA_B, fontSize: 12.5, color: COL.pink, objectName: anim("fade", 2100, 500) });
  s.addNotes("شش نوع داده داریم و هر کدام مستقیماً به یک نوع Kotlin نگاشت می‌شود. Int سی‌ودو بیتی است، دقیقاً مثل Kotlin. نکتهٔ مهم: لیست‌ها تغییرناپذیرند. در Compose اگر لیست را درجا تغییر دهید صفحه به‌روز نمی‌شود؛ در Nova هر تغییر یک لیست جدید می‌سازد، پس این باگ اصلاً ممکن نیست.");
}

// ===================================================================
// SLIDE 7 — Syntax
// ===================================================================
const SYNTAX = `let pi = 3.14           // ثابت
var total: Int = 0      // متغیر

fun fact(n: Int): Int {
    if n <= 1 { return 1 }
    return n * fact(n - 1)
}

for i in 0..10 { total += i }   // 0, 1, …, 9
for i in 1..=5 { print(i) }     // 1, 2, …, 5
while total > 0 { total -= 7 }
print("نتیجه: {fact(5)}")`;
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "زبان" });
  chrome(s, 7, "06 · SYNTAX", "نحوی تمیز و بدون ابهام", [[7.8, 3.6, 6], [-1.5, -1.0, 4.5]]);
  codeWindow(s, M, 1.95, 7.0, 4.95, SYNTAX, { file: "basics.nova", anim: anim("slideR", 300, 800), size: 13.5, glow: "A78BFA" });
  const feats = [
    ["pulse", "بدون ; اجباری", "پایان دستور با خط جدید تشخیص داده می‌شود"],
    ["braces", "شرط بی‌پرانتز، بدنه با { }", "ابهام معروف dangling-else وجود ندارد"],
    ["compass", "بازه‌های صریح", "..  انتهای باز و  ..=  انتهای بسته"],
    ["chat", "درون‌یابی رشته", "\"سلام {name}\": هر عبارتی داخل { }"],
  ];
  feats.forEach(([ic, t, d], i) => {
    const y = 1.95 + i * 1.27, d0 = 900 + i * 230;
    icon(s, ic, 11.95, y + 0.08, 0.8, anim("zoom", d0, 500));
    fa(s, t, { x: 7.9, y: y + 0.05, w: 3.9, h: 0.45, fontFace: FA_B, fontSize: 18, objectName: anim("slideL", d0 + 80, 600) });
    fa(s, d, { x: 7.9, y: y + 0.55, w: 3.9, h: 0.5, fontSize: 13.5, color: COL.muted, objectName: anim("fade", d0 + 150, 600) });
  });
  s.addNotes("نحو Nova به Kotlin و Swift نزدیک است ولی ساده‌تر. نقطه‌ویرگول لازم نیست، شرط پرانتز نمی‌خواهد ولی بدنه حتماً آکولاد دارد؛ برای همین ابهام dangling-else پیش نمی‌آید. بازه‌ها صریح‌اند و رشته‌ها درون‌یابی دارند.");
}

// ===================================================================
// SLIDE 8 — Android constructs
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "زبان" });
  chrome(s, 8, "07 · ANDROID-NATIVE", "اندروید، جزئی از خودِ زبان", [[9.5, -1.5, 5.5], [-1.2, 3.8, 5.5]]);
  const rows = [
    ["app \"عنوان\" { }", "کل اپلیکیشن", "MainActivity"],
    ["screen Name { }", "یک صفحه", "@Composable fun"],
    ["state x = 0", "وضعیت واکنش‌گرا", "rememberSaveable { mutableStateOf }"],
    ["column / row", "چیدمان عمودی / افقی", "Column / Row"],
    ["button(\"..\") { }", "دکمه + رویداد", "Button(onClick = { })"],
    ["input(name, \"..\")", "ورودی متن دوطرفه", "OutlinedTextField"],
    ["navigate(S) / back()", "ناوبری بین صفحه‌ها", "پشتهٔ صفحات + BackHandler"],
    ["toast(\"..\")", "پیام کوتاه", "Toast.makeText"],
  ];
  const y0 = 1.95, rh = 0.6;
  card(s, M, y0 - 0.05, SW - 2 * M, rows.length * rh + 0.55, { t: 50, name: anim("fade", 200, 600) });
  en(s, "NOVA", { x: 8.6, y: y0 + 0.08, w: 3.8, h: 0.3, align: "right", fontSize: 10, charSpacing: 4, color: COL.dim });
  en(s, "MEANING", { x: 5.1, y: y0 + 0.08, w: 3.2, h: 0.3, align: "right", fontSize: 10, charSpacing: 4, color: COL.dim });
  en(s, "JETPACK COMPOSE", { x: 0.9, y: y0 + 0.08, w: 4.0, h: 0.3, align: "left", fontSize: 10, charSpacing: 4, color: COL.dim });
  rows.forEach(([n, m, k], i) => {
    const y = y0 + 0.5 + i * rh, d0 = 400 + i * 140;
    if (i % 2 === 0) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M + 0.15, y: y - 0.04, w: SW - 2 * M - 0.3, h: rh - 0.04, rectRadius: 0.1, fill: { color: "FFFFFF", transparency: 95 }, line: { color: "FFFFFF", width: 0, transparency: 100 } });
    s.addText(n, { x: 8.3, y, w: 4.1, h: rh - 0.12, align: "right", valign: "middle", fontFace: MONO, fontSize: 14, color: COL.cyan, margin: 0, isTextBox: true, rtlMode: false, objectName: anim("slideL", d0, 500) });
    fa(s, m, { x: 5.1, y: y + 0.04, w: 3.0, h: rh - 0.12, fontSize: 14.5, color: COL.text, objectName: anim("fade", d0 + 100, 500) });
    s.addText(k, { x: 0.9, y, w: 4.1, h: rh - 0.12, align: "left", valign: "middle", fontFace: MONO, fontSize: 12.5, color: COL.pink, margin: 0, isTextBox: true, objectName: anim("slideR", d0 + 150, 500) });
  });
  s.addNotes("این‌ها ساختارهای ویژهٔ اندروید هستند که در خود زبان تعبیه شده‌اند. سمت راست کد Nova، وسط معنا، و سمت چپ چیزی که کامپایلر در Jetpack Compose تولید می‌کند. برنامه‌نویس Nova لازم نیست هیچ‌کدام از مفاهیم سمت چپ را بداند.");
}

// ===================================================================
// SLIDE 9 — Section divider
// ===================================================================
pres.addSection({ title: "کامپایلر" });
{
  const s = pres.addSlide({ masterName: "NOVA_HERO", sectionTitle: "کامپایلر" });
  s.addImage({ path: A + "orb_violet.png", x: 4.2, y: 0.2, w: 5, h: 5, transparency: 25, objectName: "!!orbA" });
  s.addImage({ path: A + "orb_cyan.png", x: 0.5, y: 3.5, w: 4, h: 4, transparency: 40, objectName: "!!orbB" });
  s.addImage({ path: A + "nova_star.png", x: SW / 2 - 1.3, y: 0.55, w: 2.6, h: 2.6, objectName: "!!logo" });
  en(s, "UNDER THE HOOD", { x: 0, y: 3.35, w: SW, h: 0.5, align: "center", fontFace: ORB, fontSize: 20, charSpacing: 14, color: COL.cyan, objectName: "!!wordmark" });
  fa(s, "زیر کاپوت: کامپایلر Nova", { x: 0, y: 3.95, w: SW, h: 1.2, align: "center", fontFace: FA_BL, fontSize: 54, color: "FFFFFF",
    glow: { size: 18, opacity: 0.4, color: "7C3AED" }, objectName: anim("zoom", 300, 900) });
  fa(s, "۴ فاز · ۳٬۱۷۶ خط پایتون · بدون هیچ وابستگی خارجی", { x: 0, y: 5.3, w: SW, h: 0.5, align: "center", fontSize: 18, color: COL.muted, objectName: anim("fade", 1000, 800) });
  s.addNotes("حالا برویم سراغ قلب پروژه: کامپایلر. حدود سه هزار خط پایتون، بدون هیچ کتابخانهٔ خارجی، در چهار فاز.");
}

// ===================================================================
// SLIDE 10 — Pipeline
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 10, "08 · ARCHITECTURE", "معماری کامپایلر: از متن تا اپ", [[4.5, 1.5, 5], [-1.5, 4.5, 4.5]]);
  const stages = [
    ["scan", "تحلیل واژگانی", "Lexer", "متن ← توکن"],
    ["tree", "تحلیل نحوی", "Parser", "توکن ← AST"],
    ["lens", "تحلیل معنایی", "Type Checker", "AST ← AST نوع‌دار"],
    ["gear", "تولید کد", "Code Generator", "AST ← Kotlin"],
  ];
  const w = 2.55, gap = 0.55, y = 2.15;
  stages.forEach(([ic, t, e, d], i) => {
    const x = SW - M - w - i * (w + gap), d0 = 300 + i * 450;
    card(s, x, y, w, 2.85, { name: anim("zoom", d0, 600), glowColor: ["22D3EE", "A78BFA", "F472B6", "FBBF24"][i] });
    en(s, `0${i + 1}`, { x: x + 0.2, y: y + 0.18, w: 0.6, h: 0.3, fontFace: ORB, fontSize: 14, color: COL.dim });
    icon(s, ic, x + w / 2 - 0.5, y + 0.35, 1.0, anim("fade", d0 + 150, 400));
    fa(s, t, { x: x + 0.1, y: y + 1.45, w: w - 0.2, h: 0.45, align: "center", fontFace: FA_BL, fontSize: 18, objectName: anim("fade", d0 + 200, 400) });
    en(s, e, { x: x + 0.1, y: y + 1.92, w: w - 0.2, h: 0.3, align: "center", fontFace: ORB_M, fontSize: 10.5, charSpacing: 2, color: COL.cyan, objectName: anim("fade", d0 + 220, 400) });
    fa(s, d, { x: x + 0.1, y: y + 2.3, w: w - 0.2, h: 0.4, align: "center", fontSize: 13, color: COL.muted, objectName: anim("fade", d0 + 250, 400) });
    if (i < 3) s.addImage({ path: A + "beam.png", x: x - gap - 0.05, y: y + 1.3, w: gap + 0.1, h: 0.22, objectName: anim("wipeR", d0 + 380, 300) });
  });
  // outputs
  const outs = [
    ["terminal", "مفسر و شبیه‌ساز", "اجرای فوری در ترمینال، بدون گوشی"],
    ["phone", "پروژهٔ Android Studio", "MainActivity.kt + Gradle، آمادهٔ Run"],
  ];
  outs.forEach(([ic, t, d], i) => {
    const x = i === 0 ? 6.85 : M, d0 = 2300 + i * 300;
    card(s, x, 5.35, 5.85, 1.35, { t: 45, name: anim("rise", d0, 600), glowColor: i ? "34D399" : "22D3EE" });
    icon(s, ic, x + 4.85, 5.52, 0.95, anim("zoom", d0 + 100, 400));
    fa(s, t, { x: x + 0.3, y: 5.55, w: 4.4, h: 0.45, fontFace: FA_B, fontSize: 17, objectName: anim("fade", d0 + 150, 400) });
    fa(s, d, { x: x + 0.3, y: 6.02, w: 4.4, h: 0.45, fontSize: 13, color: COL.muted, objectName: anim("fade", d0 + 200, 400) });
  });
  s.addNotes("کامپایلر چهار فاز دارد. متن وارد Lexer می‌شود و توکن بیرون می‌آید. Parser از توکن‌ها درخت نحو می‌سازد. تحلیلگر معنایی نوع‌ها را بررسی و روی درخت می‌نویسد. در پایان دو مسیر داریم: مفسر برای اجرای فوری در ترمینال، یا تولید کد Kotlin و ساخت پروژهٔ کامل اندروید.");
}

// ===================================================================
// SLIDE 11 — Lexer
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 11, "09 · PHASE 1 · LEXER", "تحلیل واژگانی: شکستن متن به توکن", [[-1.5, 1.8, 5.5], [9.0, 4.0, 5]]);
  card(s, 2.4, 2.05, 8.5, 1.15, { fill: COL.codeBg, t: 10, glowColor: "22D3EE", name: anim("zoom", 300, 600) });
  s.addText(highlight("count += 1"), { x: 2.4, y: 2.05, w: 8.5, h: 1.15, fontFace: MONO, fontSize: 32, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: anim("fade", 400, 500) });
  s.addImage({ path: A + "icons/scan.png", x: 1.3, y: 2.12, w: 1.0, h: 1.0, objectName: anim("slideR", 700, 800) });
  const toks = [["IDENT", "count", COL.cyan], ["PLUS_ASSIGN", "+=", COL.pink], ["INT", "1", COL.amber]];
  toks.forEach(([t, v, c], i) => {
    const x = 2.4 + i * 2.95, d0 = 1100 + i * 250;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.6, w: 2.6, h: 1.05, rectRadius: 0.16, fill: { color: c, transparency: 85 }, line: { color: c, width: 1.5 },
      shadow: { type: "outer", color: c, blur: 16, offset: 0, angle: 90, opacity: 0.45 }, objectName: anim("rise", d0, 600) });
    s.addText(t, { x, y: 3.68, w: 2.6, h: 0.45, align: "center", fontFace: ORB_B, fontSize: 12.5, color: c, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 100, 400) });
    s.addText(v, { x, y: 4.1, w: 2.6, h: 0.45, align: "center", fontFace: MONO, fontSize: 18, color: COL.text, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 150, 400) });
  });
  const feats = [
    ["ارقام فارسی", "۱۲ = 12"], ["شناسهٔ فارسی", "let قیمت"], ["بلندترین تطابق", "..=  before  .."], ["درون‌یابی تودرتو", "\"{a + b}\""],
  ];
  feats.forEach(([t, ex], i) => {
    const w = 2.85, x = SW - M - w - i * (w + 0.22), d0 = 2000 + i * 180;
    card(s, x, 5.15, w, 1.55, { t: 45, name: anim("rise", d0, 500), glowColor: "A78BFA" });
    fa(s, t, { x: x + 0.2, y: 5.32, w: w - 0.4, h: 0.45, align: "center", fontFace: FA_B, fontSize: 16, objectName: anim("fade", d0 + 100, 400) });
    s.addText(ex, { x: x + 0.15, y: 5.9, w: w - 0.3, h: 0.5, align: "center", fontFace: MONO, fontSize: 15, color: COL.cyan, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 150, 400) });
  });
  s.addNotes("فاز اول، تحلیل واژگانی است. اسکنر دستی، مثل یک ماشین حالت، کاراکتر به کاراکتر جلو می‌رود و توکن می‌سازد. نکات خاص: ارقام فارسی، شناسهٔ فارسی، قاعدهٔ بلندترین تطابق برای عملگرها، و درون‌یابی رشته که با یک Lexer تودرتو تجزیه می‌شود. دستور نمایش: python -m nova tokens");
}

// ===================================================================
// SLIDE 12 — Parser / AST
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 12, "10 · PHASE 2 · PARSER", "تحلیل نحوی: ساخت درخت نحو انتزاعی", [[2.5, 2.8, 5], [9.5, -1.5, 4.5]]);
  // tree for 1 + 2 * 3   (left side)
  card(s, M, 1.95, 6.0, 4.95, { t: 55, name: anim("fade", 200, 500) });
  s.addText(highlight("1 + 2 * 3"), { x: M, y: 2.1, w: 6.0, h: 0.6, fontFace: MONO, fontSize: 24, align: "center", margin: 0, isTextBox: true, objectName: anim("fade", 300, 500) });
  const nodes = {
    plus: [3.6, 2.95, "+", COL.pink], one: [2.0, 4.05, "1", COL.amber], mul: [5.2, 4.05, "*", COL.pink],
    two: [4.2, 5.15, "2", COL.amber], three: [6.2, 5.15, "3", COL.amber],
  };
  const edges = [["plus", "one"], ["plus", "mul"], ["mul", "two"], ["mul", "three"]];
  const R = 0.36;
  edges.forEach(([a, b], i) => {
    const [x1, y1] = nodes[a], [x2, y2] = nodes[b];
    s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: y1 + 2 * R, w: Math.abs(x2 - x1), h: y2 - y1 - 2 * R, flipH: x2 < x1,
      line: { color: COL.violet, width: 2.25, transparency: 20 }, objectName: anim("fade", 900 + i * 250, 400) });
  });
  const order = ["plus", "one", "mul", "two", "three"];
  order.forEach((k, i) => {
    const [x, y, t, c] = nodes[k];
    s.addShape(pres.shapes.OVAL, { x: x - R, y, w: 2 * R, h: 2 * R, fill: { color: c, transparency: 80 }, line: { color: c, width: 2 },
      shadow: { type: "outer", color: c, blur: 14, offset: 0, angle: 90, opacity: 0.5 }, objectName: anim("zoom", 600 + i * 250, 450) });
    s.addText(t, { x: x - R, y: y, w: 2 * R, h: 2 * R - 0.05, align: "center", valign: "middle", fontFace: MONO, fontSize: 20, bold: true, color: COL.text, margin: 0, isTextBox: true, objectName: anim("fade", 650 + i * 250, 400) });
  });
  fa(s, "ضرب پایین‌تر است، پس زودتر محاسبه می‌شود", { x: M + 0.3, y: 6.4, w: 5.4, h: 0.4, align: "center", fontSize: 13, color: COL.muted, objectName: anim("fade", 2000, 500) });
  // right side: recursive descent chain
  fa(s, "پارسر نزولی بازگشتی · LL(1)", { x: 7.0, y: 1.95, w: 5.73, h: 0.5, fontFace: FA_B, fontSize: 19, objectName: anim("fade", 600, 500) });
  fa(s, "به ازای هر قاعدهٔ گرامر یک تابع؛ اولویت عملگرها از ترتیب فراخوانی می‌آید:", { x: 7.0, y: 2.5, w: 5.73, h: 0.75, fontSize: 13.5, color: COL.muted, objectName: anim("fade", 700, 500) });
  const chain = ["expression", "or_expr", "and_expr", "not_expr", "comparison", "additive", "multiplicative", "unary", "postfix", "primary"];
  chain.forEach((c, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = col === 0 ? 9.95 : 7.0, y = 3.4 + row * 0.68, d0 = 1000 + i * 120;
    const t = 85 - i * 5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.75, h: 0.5, rectRadius: 0.25, fill: { color: "8B5CF6", transparency: t }, line: { color: "A78BFA", width: 1 }, objectName: anim("slideL", d0, 400) });
    s.addText(`${i + 1}. ${c}()`, { x: x + 0.1, y, w: 2.55, h: 0.5, valign: "middle", align: "left", fontFace: MONO, fontSize: 12.5, color: COL.text, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 50, 300) });
  });
  s.addNotes("فاز دوم پارسر است، از نوع نزولی بازگشتی. برای هر قاعدهٔ گرامر یک تابع داریم و اولویت عملگرها از ترتیب فراخوانی این توابع می‌آید: تابعی که پایین‌تر است زودتر گره می‌سازد. نتیجه درخت سمت چپ است: ضرب زیر جمع قرار می‌گیرد. گرامر LL(1) است، یعنی با دیدن فقط یک توکن جلو تصمیم می‌گیریم.");
}

// ===================================================================
// SLIDE 13 — Grammar & precedence
// ===================================================================
const EBNF = `program    = { funDecl | varDecl | appDecl } ;
appDecl    = "app" STRING "{" { screenDecl } "}" ;
screenDecl = "screen" IDENT "{" { stateDecl }
             { uiNode } "}" ;
funDecl    = "fun" IDENT "(" [ params ] ")"
             [ ":" type ] block ;
stmt       = varDecl | assign | ifStmt | whileStmt
           | forStmt | "return" [ expr ] | call ;
comparison = additive [ compOp additive ] ;
additive   = term { ("+" | "-") term } ;`;
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 13, "11 · GRAMMAR", "گرامر و اولویت عملگرها", [[-1.0, -1.2, 5], [7.5, 3.5, 6]]);
  codeWindow(s, M, 1.95, 6.25, 4.95, EBNF, { file: "grammar.ebnf", anim: anim("slideR", 300, 700), size: 12.5, glow: "F472B6", lang: "ebnf" });
  const levels = [["or", 1], ["and", 2], ["not", 3], ["== < >", 4], ["+  -", 5], ["*  /  %", 6], ["- (unary)", 7], ["f()  a[i]", 8]];
  const baseY = 6.85, stepH = 0.56, colW = 0.6;
  levels.forEach(([op, lv], i) => {
    const h = 0.4 + i * 0.38;
    const x = SW - M - colW - i * (colW + 0.04);
    const d0 = 800 + i * 160;
    const c = i < 3 ? "8B5CF6" : i < 6 ? "22D3EE" : "F472B6";
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: baseY - h, w: colW, h, rectRadius: 0.08, fill: { color: c, transparency: 55 }, line: { color: c, width: 1 },
      shadow: { type: "outer", color: c, blur: 12, offset: 0, angle: 90, opacity: 0.35 }, objectName: anim("grow", d0, 600) });
    s.addText(op, { x: x - 0.1, y: baseY - h - 0.45, w: colW + 0.2, h: 0.4, align: "center", fontFace: MONO, fontSize: 10.5, bold: true, color: COL.text, margin: 0, isTextBox: true, objectName: anim("fade", d0 + 200, 300) });
  });
  fa(s, "اولویت ← بیشتر", { x: 7.5, y: 1.95, w: 5.2, h: 0.45, fontFace: FA_B, fontSize: 17, color: COL.text, objectName: anim("fade", 700, 400) });
  fa(s, "مقایسهٔ زنجیره‌ای ممنوع است:", { x: 7.5, y: 2.4, w: 5.2, h: 0.4, fontSize: 13, color: COL.muted, objectName: anim("fade", 800, 400) });
  s.addText("1 < x < 5   →   syntax error", { x: 7.5, y: 2.8, w: 5.2, h: 0.35, align: "right", fontFace: MONO, fontSize: 12, color: COL.red, margin: 0, isTextBox: true, objectName: anim("fade", 850, 400) });
  s.addNotes("گرامر کامل به صورت EBNF نوشته شده است. ستون‌ها اولویت عملگرها را نشان می‌دهند: هرچه بلندتر، اولویت بیشتر. یک تصمیم طراحی جالب: not اولویتی کمتر از مقایسه دارد، پس not a == b یعنی not (a == b). مقایسهٔ زنجیره‌ای هم ممنوع است تا با معنای ریاضی اشتباه نشود.");
}

// ===================================================================
// SLIDE 14 — Semantic analysis
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 14, "12 · PHASE 3 · TYPE CHECKER", "تحلیل معنایی: خطا قبل از اجرا", [[8.8, -1.0, 5], [-1.6, 3.2, 5.5]]);
  // console
  card(s, M, 1.95, 7.3, 2.25, { fill: "12051A", t: 10, glowColor: "FB7185", glowOp: 0.45, name: anim("zoom", 300, 700) });
  s.addText([
    { text: "$ python -m nova check counter.nova", options: { color: COL.dim, breakLine: true } },
    { text: "counter.nova:5:17: ", options: { color: COL.text } },
    { text: "type error: ", options: { color: COL.red, bold: true } },
    { text: "expected Int, got String", options: { color: COL.text, breakLine: true } },
    { text: "    count = \"ده\"", options: { color: "86EFAC", breakLine: true } },
    { text: "            ^", options: { color: COL.red, bold: true } },
  ], { x: M + 0.3, y: 2.15, w: 6.8, h: 1.9, fontFace: MONO, fontSize: 14, align: "left", valign: "top", margin: 0, isTextBox: true, lineSpacingMultiple: 1.15, objectName: anim("fade", 700, 500) });
  icon(s, "error", M + 6.55, 3.45, 0.6, anim("zoom", 1200, 400));
  // scopes visual
  fa(s, "جدول نماد: پشته‌ای از حوزه‌ها", { x: M, y: 4.45, w: 7.3, h: 0.45, fontFace: FA_B, fontSize: 16, objectName: anim("fade", 1300, 400) });
  const scopes = [["سراسری", "8B5CF6"], ["تابع", "A78BFA"], ["بلوک if", "22D3EE"], ["حلقه", "34D399"]];
  scopes.forEach(([t, c], i) => {
    const x = M + 7.3 - (i + 1) * 1.75 - i * 0.07 + 0.07, d0 = 1400 + i * 180;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.0, w: 1.75, h: 0.75, rectRadius: 0.1, fill: { color: c, transparency: 70 }, line: { color: c, width: 1.25 }, objectName: anim("slideL", d0, 400) });
    fa(s, t, { x, y: 5.17, w: 1.75, h: 0.4, align: "center", fontFace: FA_B, fontSize: 14, objectName: anim("fade", d0 + 50, 300) });
  });
  fa(s, "push() هنگام ورود به بلوک  ·  pop() هنگام خروج", { x: M, y: 5.95, w: 7.3, h: 0.4, align: "center", fontSize: 13, color: COL.muted, objectName: anim("fade", 2200, 400) });
  // checks list
  const checks = ["ناسازگاری نوع", "متغیر تعریف‌نشده / تکراری", "تغییر ثابت let", "تعداد و نوع آرگومان", "return در همهٔ مسیرها", "break بیرون حلقه", "toast بیرون رویداد دکمه", "navigate به صفحهٔ ناموجود"];
  card(s, 8.2, 1.95, 4.53, 4.95, { t: 45, glowColor: "34D399", name: anim("rise", 500, 600) });
  checks.forEach((c, i) => {
    const y = 2.2 + i * 0.57, d0 = 900 + i * 150;
    icon(s, "lens", 12.05, y, 0.42, anim("zoom", d0, 300));
    fa(s, c, { x: 8.45, y: y + 0.04, w: 3.5, h: 0.4, fontSize: 14.5, objectName: anim("slideL", d0 + 50, 400) });
  });
  s.addNotes("فاز سوم تحلیل معنایی است. یک جدول نماد به شکل پشته‌ای از حوزه‌ها داریم. هر عبارت نوع می‌گیرد و هر ناسازگاری با شمارهٔ سطر و ستون و حتی یک نشانگر زیر کد گزارش می‌شود. سمت راست فهرست خطاهایی است که قبل از اجرا گرفته می‌شوند، حتی خطاهای وابسته به متن مثل toast بیرون از رویداد دکمه.");
}

// ===================================================================
// SLIDE 15 — Code generation
// ===================================================================
const NV = `state count: Int = 0
var x: Float = 1
let val = 5

button("+") {
    count += 1
}`;
const KT = `var count by rememberSaveable {
    mutableStateOf<Int>(0) }
var x: Double = 1.0
val \`val\`: Int = 5

Button(onClick = {
    count += 1
}) { Text(text = "+") }`;
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 15, "13 · PHASE 4 · CODEGEN", "تولید کد: از Nova به Kotlin", [[4.0, 3.8, 5], [9.5, -1.6, 5]]);
  codeWindow(s, 7.75, 1.95, 4.98, 3.35, NV, { file: "app.nova", anim: anim("slideL", 300, 700), size: 13.5 });
  codeWindow(s, M, 1.95, 6.2, 3.35, KT, { file: "MainActivity.kt", anim: anim("slideR", 1100, 700), size: 13, lang: "kotlin", glow: "F472B6" });
  s.addImage({ path: A + "beam.png", x: 6.85, y: 3.5, w: 0.85, h: 0.25, objectName: anim("wipeR", 800, 400) });
  const ch = [
    ["stairs", "پرانتز فقط در صورت لزوم", "(1 + 2) * 3   ·   1 + 2 * 3"],
    ["shield", "فرار از کلمات کلیدی", "val → `val`  ·  Text → Text_"],
    ["bolt", "تبدیل ضمنی صریح می‌شود", "1 → 1.0  ·  n → n.toDouble()"],
  ];
  ch.forEach(([ic, t, d], i) => {
    const w = 3.9, x = SW - M - w - i * (w + 0.22), d0 = 1700 + i * 220;
    card(s, x, 5.55, w, 1.35, { t: 45, name: anim("rise", d0, 500), glowColor: "FBBF24" });
    icon(s, ic, x + w - 0.85, 5.75, 0.62, anim("zoom", d0 + 100, 400));
    fa(s, t, { x: x + 0.2, y: 5.7, w: w - 1.15, h: 0.45, fontFace: FA_B, fontSize: 14.5, objectName: anim("fade", d0 + 150, 400) });
    s.addText(d, { x: x + 0.2, y: 6.22, w: w - 0.4, h: 0.45, fontFace: MONO, fontSize: 11.5, color: COL.cyan, align: "right", margin: 0, isTextBox: true, objectName: anim("fade", d0 + 200, 400) });
  });
  s.addNotes("فاز آخر تولید کد است. هر state به rememberSaveable تبدیل می‌شود تا حتی با چرخش گوشی هم حفظ شود. سه چالش جالب: پرانتز فقط جایی گذاشته می‌شود که لازم است؛ اگر کاربر متغیری به اسم val بسازد که در Kotlin کلمهٔ کلیدی است، نامش با بک‌تیک فرار داده می‌شود؛ و چون Kotlin تبدیل ضمنی ندارد، کامپایلر خودش toDouble درج می‌کند.");
}

// ===================================================================
// SLIDE 16 — Proof / tests
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "کامپایلر" });
  chrome(s, 16, "14 · PROOF", "اثبات درستی: تست تفاضلی", [[-1.2, -1.2, 5], [6.5, 2.5, 6]]);
  const stats = [["31", "تست واحد، همه سبز", COL.green], ["4/4", "خروجی یکسان با Kotlin واقعی", COL.cyan], ["0", "وابستگی خارجی", COL.violet], ["5", "اپ نمونهٔ آماده", COL.amber]];
  stats.forEach(([b, l, c], i) => {
    const w = 2.85, x = SW - M - w - i * (w + 0.24);
    card(s, x, 1.95, w, 2.0, { t: 45, glowColor: c, name: anim("rise", 300 + i * 200, 600) });
    stat(s, x, 2.1, w, b, l, c, 500 + i * 200, { size: 46, bh: 0.95 });
  });
  // terminal sim
  card(s, M, 4.25, 6.4, 2.65, { fill: COL.codeBg, t: 8, glowColor: "22D3EE", name: anim("slideR", 1400, 600) });
  s.addText([
    { text: "$ python -m nova sim examples/counter.nova", options: { color: COL.dim, breakLine: true } },
    { text: "+------------ شمارنده > Main ------------+", options: { color: COL.violet, breakLine: true } },
    { text: "| مقدار فعلی: 2", options: { color: COL.text, breakLine: true } },
    { text: "| [1: −]   [2: +]", options: { color: COL.cyan, breakLine: true } },
    { text: "| [3: صفر کن]", options: { color: COL.cyan, breakLine: true } },
    { text: "> 2", options: { color: COL.amber } },
  ], { x: M + 0.3, y: 4.45, w: 5.9, h: 2.3, fontFace: MONO, fontSize: 12.5, align: "left", valign: "top", margin: 0, isTextBox: true, lineSpacingMultiple: 1.1, objectName: anim("fade", 1600, 500) });
  // diff diagram
  card(s, 7.2, 4.25, 5.53, 2.65, { t: 45, name: anim("slideL", 1800, 600) });
  fa(s, "یک برنامه، دو اجرا، یک خروجی", { x: 7.45, y: 4.4, w: 5.0, h: 0.45, fontFace: FA_B, fontSize: 16, objectName: anim("fade", 1900, 400) });
  const pill = (t, x, y, c, d) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.3, h: 0.5, rectRadius: 0.25, fill: { color: c, transparency: 80 }, line: { color: c, width: 1.25 }, objectName: anim("zoom", d, 400) });
    s.addText(t, { x, y, w: 2.3, h: 0.5, align: "center", valign: "middle", fontFace: MONO, fontSize: 12, color: COL.text, margin: 0, isTextBox: true, objectName: anim("fade", d + 50, 300) });
  };
  pill("Python Interpreter", 10.2, 5.05, COL.violet, 2100);
  pill("Kotlin on JVM", 10.2, 5.75, COL.pink, 2250);
  s.addImage({ path: A + "beam.png", x: 9.55, y: 5.55, w: 0.6, h: 0.2, objectName: anim("wipeR", 2400, 300) });
  pill("diff = ∅  ✓", 7.4, 5.4, COL.green, 2600);
  s.addNotes("چطور مطمئن شویم مفسر و کد Kotlin تولیدشده یک معنا دارند؟ با تست تفاضلی: هر برنامهٔ تست یک بار با مفسر پایتون و یک بار با کامپایلر واقعی Kotlin روی JVM اجرا می‌شود و خروجی‌ها مقایسه می‌شوند. هر چهار برنامه، از جمله سرریز اعداد و قالب اعشار، خروجی کاملاً یکسان دادند. ۳۱ تست واحد هم همهٔ فازها را پوشش می‌دهند.");
}

// ===================================================================
// SLIDE 17 — Comparison
// ===================================================================
pres.addSection({ title: "جمع‌بندی" });
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "جمع‌بندی" });
  chrome(s, 17, "15 · COMPARISON", "Nova در کنار غول‌ها", [[0.8, 1.5, 4.5], [9.0, 3.5, 5]]);
  const rows = [
    ["خطوط کد اپ شمارنده", "~60", "~40", "~10"],
    ["تایپ ایستا", "✓", "✓", "✓"],
    ["UI داخل خود زبان", "✗", "DSL", "✓"],
    ["state واکنش‌گرا بدون boilerplate", "✗", "✗", "✓"],
    ["شبیه‌ساز بدون گوشی", "✗", "✗", "✓"],
    ["منحنی یادگیری", "سخت", "متوسط", "آسان"],
  ];
  const cols = [{ x: 8.0, w: 4.73 }, { x: 5.75, w: 2.05 }, { x: 3.5, w: 2.05 }, { x: M, w: 2.7 }];
  // highlight nova column
  card(s, cols[3].x, 1.85, cols[3].w, 5.1, { fill: "3B1F7A", t: 30, line: "A78BFA", lw: 1.5, glowColor: "8B5CF6", glowOp: 0.6, blur: 26, name: anim("zoom", 1600, 700) });
  const heads = ["", "Java", "Kotlin + Compose", "NOVA"];
  heads.forEach((h, j) => {
    if (!h) return;
    en(s, h, { x: cols[j].x, y: 2.05, w: cols[j].w, h: 0.4, align: "center", fontFace: j === 3 ? ORB : ORB_B, fontSize: j === 3 ? 18 : 12.5, color: j === 3 ? "FFFFFF" : COL.muted,
      objectName: anim("fade", j === 3 ? 1700 : 200, 400) });
  });
  rows.forEach((r, i) => {
    const y = 2.65 + i * 0.7, d0 = 300 + i * 150;
    s.addShape(pres.shapes.LINE, { x: M, y: y - 0.06, w: SW - 2 * M, h: 0, line: { color: "FFFFFF", width: 0.5, transparency: 85 } });
    fa(s, r[0], { x: cols[0].x, y: y + 0.08, w: cols[0].w, h: 0.45, fontSize: 15, objectName: anim("slideL", d0, 400) });
    [1, 2, 3].forEach((j) => {
      const v = r[j];
      const isNova = j === 3;
      const color = v === "✓" ? COL.green : v === "✗" ? COL.red : isNova ? "FFFFFF" : COL.muted;
      const isFa = /[؀-ۿ]/.test(v);
      s.addText(v, { x: cols[j].x, y: y + 0.05, w: cols[j].w, h: 0.5, align: "center", valign: "middle", fontFace: isFa ? (isNova ? FA_BL : FA) : (isNova ? ORB_B : MONO),
        fontSize: isNova ? 17 : 15, bold: isNova && !isFa, color, margin: 0, isTextBox: true, rtlMode: isFa, lang: isFa ? "fa-IR" : "en-US",
        objectName: anim(isNova ? "zoom" : "fade", isNova ? 1900 + i * 120 : d0 + 100 + j * 60, 400) });
    });
  });
  s.addNotes("مقایسه با Java و Kotlin: هر سه تایپ ایستا دارند، ولی فقط Nova رابط کاربری و state را در خود زبان دارد و برای یک اپ ساده حدود یک ششم کد Java لازم دارد. شبیه‌ساز هم اجازه می‌دهد بدون گوشی و حتی بدون Android Studio اپ را امتحان کنید.");
}

// ===================================================================
// SLIDE 18 — Roadmap
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_MAIN", sectionTitle: "جمع‌بندی" });
  chrome(s, 18, "16 · ROADMAP", "مسیر آینده", [[7.5, 1.0, 5.5], [-1.0, 3.5, 5]]);
  const steps = [
    ["persian", "کلمات کلیدی فارسی", "اگر، تا_وقتی، برای: برنامه‌نویسی کاملاً فارسی", "v1.1"],
    ["cube", "کلاس و شیءگرایی", "class، متد و رابط برای اپ‌های بزرگ", "v1.5"],
    ["orbit", "شبکه و پایگاه داده", "fetch و storage در کتابخانهٔ استاندارد", "v2.0"],
    ["rocket", "افزونهٔ VS Code", "رنگ‌آمیزی نحو، تکمیل خودکار و پیش‌نمایش زنده", "v2.5"],
  ];
  // timeline line
  s.addImage({ path: A + "beam.png", x: M + 0.3, y: 3.62, w: SW - 2 * M - 0.6, h: 0.3, objectName: anim("wipeR", 300, 1400) });
  steps.forEach(([ic, t, d, v], i) => {
    const w = 2.85, x = SW - M - w - i * (w + 0.24), d0 = 500 + i * 350;
    s.addShape(pres.shapes.OVAL, { x: x + w / 2 - 0.17, y: 3.6, w: 0.34, h: 0.34, fill: { color: "FFFFFF" }, line: { color: COL.violet, width: 3 },
      shadow: { type: "outer", color: "A78BFA", blur: 16, offset: 0, angle: 90, opacity: 0.8 }, objectName: anim("zoom", d0, 400) });
    en(s, v, { x, y: 2.95, w, h: 0.45, align: "center", fontFace: ORB, fontSize: 18, color: COL.cyan, objectName: anim("fade", d0 + 100, 400) });
    card(s, x, 4.3, w, 2.55, { t: 45, name: anim("rise", d0 + 150, 600), glowColor: ["22D3EE", "A78BFA", "F472B6", "FBBF24"][i] });
    icon(s, ic, x + w / 2 - 0.4, 4.45, 0.8, anim("zoom", d0 + 250, 400));
    fa(s, t, { x: x + 0.15, y: 5.3, w: w - 0.3, h: 0.45, align: "center", fontFace: FA_B, fontSize: 16.5, objectName: anim("fade", d0 + 300, 400) });
    fa(s, d, { x: x + 0.2, y: 5.8, w: w - 0.4, h: 0.95, align: "center", fontSize: 12.5, color: COL.muted, objectName: anim("fade", d0 + 350, 400) });
  });
  fa(s, "Nova امروز: زبان کامل، کامپایلر ۴ فازی، شبیه‌ساز و خروجی اندروید", { x: M, y: 2.05, w: SW - 2 * M, h: 0.5, align: "center", fontSize: 16, color: COL.muted, objectName: anim("fade", 200, 500) });
  s.addNotes("محدودیت‌های فعلی: کلاس و شیءگرایی نداریم و هنوز به شبکه و پایگاه داده دسترسی نیست. نقشهٔ راه: کلمات کلیدی فارسی، شیءگرایی، کتابخانهٔ شبکه و ذخیره‌سازی، و یک افزونه برای VS Code.");
}

// ===================================================================
// SLIDE 19 — Closing
// ===================================================================
{
  const s = pres.addSlide({ masterName: "NOVA_HERO", sectionTitle: "جمع‌بندی" });
  s.addImage({ path: A + "orb_violet.png", x: 3.0, y: -1.0, w: 7.4, h: 7.4, transparency: 25, objectName: "!!orbA" });
  s.addImage({ path: A + "orb_cyan.png", x: -1.0, y: -1.5, w: 5.5, h: 5.5, transparency: 40, objectName: "!!orbB" });
  s.addImage({ path: A + "nova_star.png", x: SW / 2 - 1.6, y: 0.2, w: 3.2, h: 3.2, objectName: "!!logo" });
  fa(s, "آینده، همین‌جاست.", { x: 0, y: 3.2, w: SW, h: 1.25, align: "center", fontFace: FA_BL, fontSize: 60, color: "FFFFFF",
    glow: { size: 20, opacity: 0.45, color: "A78BFA" }, objectName: anim("zoom", 300, 900) });
  en(s, "NOVA", { x: 0, y: 4.5, w: SW, h: 0.6, align: "center", fontFace: ORB, fontSize: 26, charSpacing: 30, color: COL.cyan, objectName: "!!wordmark" });
  card(s, SW / 2 - 2.0, 5.45, 4.0, 0.85, { r: 0.42, t: 40, glowColor: "22D3EE", glowOp: 0.5, name: anim("rise", 1300, 700) });
  icon(s, "chat", SW / 2 + 1.0, 5.55, 0.65, anim("zoom", 1500, 400));
  fa(s, "پرسش و پاسخ", { x: SW / 2 - 1.8, y: 5.6, w: 2.75, h: 0.55, align: "center", fontFace: FA_B, fontSize: 22, objectName: anim("fade", 1500, 500) });
  s.addText("github.com/salardelkesh85/lang", { x: 0, y: 6.6, w: SW, h: 0.35, align: "center", fontFace: MONO, fontSize: 13, color: COL.muted, margin: 0, isTextBox: true, objectName: anim("fade", 1900, 600) });
  s.addNotes("خلاصه: یک زبان کامل با تایپ ایستا، کامپایلری در چهار فاز، شبیه‌ساز، و خروجی واقعی اندروید. ممنون از توجه شما. آمادهٔ پرسش هستم. اگر وقت باشد، دموی زنده: python -m nova sim examples/todo.nova");
}

pres.writeFile({ fileName: "nova_raw.pptx" }).then(() => console.log("written"));
