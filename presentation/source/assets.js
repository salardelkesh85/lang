// Generates all visual assets (backgrounds, glow orbs, logo, custom neon icons) as PNG.
const sharp = require("sharp");
const fs = require("fs");
fs.mkdirSync("assets/icons", { recursive: true });

const W = 2666, H = 1500;

// deterministic pseudo random
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function stars(n, w, h, maxR) {
  let s = "";
  for (let i = 0; i < n; i++) {
    const x = rnd() * w, y = rnd() * h, r = rnd() * maxR + 0.4, o = (rnd() * 0.7 + 0.2).toFixed(2);
    s += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(2)}" fill="#fff" opacity="${o}"/>`;
  }
  return s;
}

function grid() {
  // perspective floor grid fading out
  let g = "";
  const horizon = 1050, vx = W / 2;
  for (let i = -24; i <= 24; i++) {
    g += `<line x1="${vx + i * 18}" y1="${horizon}" x2="${vx + i * 260}" y2="${H}" stroke="#8B5CF6" stroke-width="1.4"/>`;
  }
  for (let k = 0; k < 12; k++) {
    const t = Math.pow(k / 11, 2.2);
    const y = horizon + t * (H - horizon);
    g += `<line x1="0" y1="${y.toFixed(1)}" x2="${W}" y2="${y.toFixed(1)}" stroke="#22D3EE" stroke-width="1.2"/>`;
  }
  return g;
}

function background(variant) {
  const neb = variant === "hero"
    ? `<ellipse cx="1333" cy="700" rx="1100" ry="620" fill="url(#n1)"/>
       <ellipse cx="2150" cy="250" rx="800" ry="500" fill="url(#n2)"/>
       <ellipse cx="350" cy="1200" rx="900" ry="520" fill="url(#n3)"/>`
    : `<ellipse cx="2300" cy="120" rx="1000" ry="620" fill="url(#n1)" opacity="0.65"/>
       <ellipse cx="200" cy="1350" rx="900" ry="520" fill="url(#n2)" opacity="0.55"/>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
  <defs>
    <linearGradient id="base" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0B0A24"/><stop offset="0.55" stop-color="#070618"/><stop offset="1" stop-color="#040311"/>
    </linearGradient>
    <radialGradient id="n1"><stop offset="0" stop-color="#6D28D9" stop-opacity="0.55"/><stop offset="1" stop-color="#6D28D9" stop-opacity="0"/></radialGradient>
    <radialGradient id="n2"><stop offset="0" stop-color="#0891B2" stop-opacity="0.45"/><stop offset="1" stop-color="#0891B2" stop-opacity="0"/></radialGradient>
    <radialGradient id="n3"><stop offset="0" stop-color="#DB2777" stop-opacity="0.35"/><stop offset="1" stop-color="#DB2777" stop-opacity="0"/></radialGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
    <mask id="gm"><rect x="0" y="1050" width="${W}" height="450" fill="url(#fade)"/></mask>
  </defs>
  <rect width="${W}" height="${H}" fill="url(#base)"/>
  ${neb}
  ${stars(variant === "hero" ? 520 : 300, W, H, variant === "hero" ? 2.2 : 1.6)}
  <g mask="url(#gm)" opacity="${variant === "hero" ? 0.35 : 0.16}">${grid()}</g>
</svg>`;
  return sharp(Buffer.from(svg)).jpeg({ quality: 90 }).toFile(`assets/bg_${variant}.jpg`);
}

function orb(name, color, size = 900) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
  <defs><radialGradient id="g"><stop offset="0" stop-color="${color}" stop-opacity="0.85"/>
  <stop offset="0.35" stop-color="${color}" stop-opacity="0.35"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient></defs>
  <circle cx="${size / 2}" cy="${size / 2}" r="${size / 2}" fill="url(#g)"/></svg>`;
  return sharp(Buffer.from(svg)).png().toFile(`assets/orb_${name}.png`);
}

function novaStar() {
  const s = 1200, c = s / 2;
  // 4-point star with long spikes + thin rings
  const star = (R, r) => {
    let p = "";
    for (let i = 0; i < 8; i++) {
      const a = (Math.PI / 4) * i - Math.PI / 2;
      const rad = i % 2 === 0 ? R : r;
      p += `${(c + rad * Math.cos(a)).toFixed(1)},${(c + rad * Math.sin(a)).toFixed(1)} `;
    }
    return p;
  };
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}">
  <defs>
    <radialGradient id="core"><stop offset="0" stop-color="#FFFFFF"/><stop offset="0.25" stop-color="#E9D5FF"/><stop offset="0.6" stop-color="#A78BFA" stop-opacity="0.6"/><stop offset="1" stop-color="#7C3AED" stop-opacity="0"/></radialGradient>
    <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22D3EE"/><stop offset="0.5" stop-color="#FFFFFF"/><stop offset="1" stop-color="#C084FC"/></linearGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22D3EE"/><stop offset="1" stop-color="#C084FC"/></linearGradient>
    <filter id="blur"><feGaussianBlur stdDeviation="18"/></filter>
    <filter id="blur2"><feGaussianBlur stdDeviation="6"/></filter>
  </defs>
  <circle cx="${c}" cy="${c}" r="520" fill="url(#core)" opacity="0.55"/>
  <ellipse cx="${c}" cy="${c}" rx="430" ry="150" fill="none" stroke="url(#ring)" stroke-width="5" opacity="0.8" transform="rotate(-18 ${c} ${c})"/>
  <ellipse cx="${c}" cy="${c}" rx="330" ry="330" fill="none" stroke="url(#ring)" stroke-width="2" opacity="0.45" stroke-dasharray="6 18"/>
  <polygon points="${star(500, 46)}" fill="#C4B5FD" filter="url(#blur)" opacity="0.9"/>
  <polygon points="${star(500, 46)}" fill="url(#sg)" filter="url(#blur2)"/>
  <polygon points="${star(300, 40)}" fill="#FFFFFF" transform="rotate(45 ${c} ${c})" opacity="0.55"/>
  <circle cx="${c}" cy="${c}" r="70" fill="#FFFFFF" filter="url(#blur2)"/>
  <circle cx="${c}" cy="${c}" r="44" fill="#FFFFFF"/>
</svg>`;
  return sharp(Buffer.from(svg)).png().toFile("assets/nova_star.png");
}

// ---------- custom neon icons (viewBox 128) ----------
const ICONS = {
  wand: `<path d="M24 104 L78 50"/><path d="M70 42 l16 16"/><path d="M92 18 v14 M85 25 h14"/><path d="M104 52 v10 M99 57 h10"/><path d="M58 18 v8 M54 22 h8"/><circle cx="96" cy="88" r="3" class="f"/>`,
  shield: `<path d="M64 14 L104 28 V62 C104 88 86 106 64 116 C42 106 24 88 24 62 V28 Z"/><path d="M46 64 l12 12 l26 -28"/>`,
  phone: `<rect x="36" y="12" width="56" height="104" rx="12"/><path d="M56 22 h16"/><path d="M64 50 l5 11 l11 3 l-11 3 l-5 11 l-5 -11 l-11 -3 l11 -3 Z" class="f"/><circle cx="64" cy="102" r="3" class="f"/>`,
  bridge: `<path d="M14 92 C34 40 94 40 114 92"/><path d="M14 92 h100"/><path d="M38 92 v-26 M64 92 v-36 M90 92 v-26"/><path d="M30 30 l-12 10 l12 10 M98 30 l12 10 l-12 10"/>`,
  persian: `<path d="M20 28 h88 a8 8 0 0 1 8 8 v50 a8 8 0 0 1 -8 8 h-46 l-22 18 v-18 h-20 a8 8 0 0 1 -8 -8 v-50 a8 8 0 0 1 8 -8 Z"/><text x="64" y="80" font-family="Vazirmatn" font-weight="900" font-size="52" text-anchor="middle" class="t">ف</text>`,
  scan: `<rect x="14" y="44" width="26" height="40" rx="5"/><rect x="51" y="44" width="26" height="40" rx="5"/><rect x="88" y="44" width="26" height="40" rx="5"/><path d="M64 16 v96" class="hot"/><path d="M58 16 h12 M58 112 h12" class="hot"/>`,
  tree: `<circle cx="64" cy="24" r="10"/><circle cx="32" cy="70" r="10"/><circle cx="96" cy="70" r="10"/><circle cx="74" cy="108" r="8"/><circle cx="114" cy="108" r="8"/><path d="M57 32 L38 62 M71 32 L90 62 M92 79 L78 100 M100 79 L110 100"/>`,
  lens: `<circle cx="54" cy="54" r="34"/><path d="M80 80 L112 112"/><path d="M38 54 l11 11 l20 -22"/>`,
  gear: `<path d="M64 20 l8 0 l3 12 l10 4 l10 -7 l6 6 l-7 10 l4 10 l12 3 l0 8 l-12 3 l-4 10 l7 10 l-6 6 l-10 -7 l-10 4 l-3 12 l-8 0 l-3 -12 l-10 -4 l-10 7 l-6 -6 l7 -10 l-4 -10 l-12 -3 l0 -8 l12 -3 l4 -10 l-7 -10 l6 -6 l10 7 l10 -4 Z"/><path d="M58 56 l-8 8 l8 8 M70 56 l8 8 l-8 8"/>`,
  terminal: `<rect x="12" y="22" width="104" height="84" rx="10"/><path d="M12 40 h104"/><circle cx="24" cy="31" r="2.5" class="f"/><circle cx="33" cy="31" r="2.5" class="f"/><circle cx="42" cy="31" r="2.5" class="f"/><path d="M30 60 l14 12 l-14 12"/><path d="M54 86 h28" class="hot"/>`,
  layers: `<path d="M64 16 L114 42 L64 68 L14 42 Z"/><path d="M14 64 L64 90 L114 64"/><path d="M14 86 L64 112 L114 86"/>`,
  bolt: `<path d="M72 10 L28 72 H60 L52 118 L100 52 H66 Z"/>`,
  rocket: `<path d="M64 12 C86 28 94 54 86 84 H42 C34 54 42 28 64 12 Z"/><circle cx="64" cy="48" r="10"/><path d="M42 70 L24 90 L42 88 M86 70 L104 90 L86 88"/><path d="M54 96 C54 106 64 116 64 116 C64 116 74 106 74 96" class="hot"/>`,
  orbit: `<ellipse cx="64" cy="64" rx="52" ry="20"/><ellipse cx="64" cy="64" rx="52" ry="20" transform="rotate(60 64 64)"/><ellipse cx="64" cy="64" rx="52" ry="20" transform="rotate(-60 64 64)"/><circle cx="64" cy="64" r="7" class="f"/>`,
  flask: `<path d="M50 14 h28 M56 14 v34 L24 104 a8 8 0 0 0 7 12 h66 a8 8 0 0 0 7 -12 L72 48 V14"/><path d="M38 84 h52" class="hot"/><path d="M54 98 l8 8 l14 -16"/>`,
  stairs: `<path d="M14 112 H40 V86 H66 V60 H92 V34 H114"/><path d="M98 14 l16 20 l-22 4"/><circle cx="27" cy="100" r="3" class="f"/>`,
  scales: `<path d="M64 18 V110 M40 110 h48"/><path d="M24 38 H104"/><path d="M24 38 L10 76 a14 10 0 0 0 28 0 Z M104 38 L90 76 a14 10 0 0 0 28 0 Z"/><circle cx="64" cy="18" r="5" class="f"/>`,
  flag: `<path d="M20 116 C44 92 40 72 66 66 C90 60 92 44 104 30"/><path d="M98 32 V8 L120 16 L98 24"/><circle cx="20" cy="116" r="5" class="f"/><circle cx="66" cy="66" r="4" class="f"/>`,
  chat: `<path d="M16 22 h64 a8 8 0 0 1 8 8 v34 a8 8 0 0 1 -8 8 h-38 l-18 14 v-14 h-8 a8 8 0 0 1 -8 -8 v-34 a8 8 0 0 1 8 -8 Z"/><path d="M96 46 h10 a8 8 0 0 1 8 8 v30 a8 8 0 0 1 -8 8 h-4 v14 l-18 -14 h-30 a8 8 0 0 1 -8 -8 v-4"/><circle cx="34" cy="47" r="3" class="f"/><circle cx="48" cy="47" r="3" class="f"/><circle cx="62" cy="47" r="3" class="f"/>`,
  cube: `<path d="M64 12 L110 38 V90 L64 116 L18 90 V38 Z"/><path d="M18 38 L64 64 L110 38 M64 64 V116"/>`,
  compass: `<circle cx="64" cy="64" r="50"/><path d="M84 44 L70 70 L44 84 L58 58 Z"/><circle cx="64" cy="64" r="3" class="f"/>`,
  pulse: `<path d="M8 70 H34 L44 44 L58 96 L72 30 L84 70 H120"/><circle cx="120" cy="70" r="4" class="f"/>`,
  braces: `<path d="M44 16 C30 16 32 30 32 46 C32 56 26 62 18 64 C26 66 32 72 32 82 C32 98 30 112 44 112"/><path d="M84 16 C98 16 96 30 96 46 C96 56 102 62 110 64 C102 66 96 72 96 82 C96 98 98 112 84 112"/><circle cx="64" cy="64" r="6" class="f"/>`,
  target: `<circle cx="64" cy="64" r="48"/><circle cx="64" cy="64" r="28"/><circle cx="64" cy="64" r="8" class="f"/><path d="M64 4 v20 M64 104 v20 M4 64 h20 M104 64 h20"/>`,
  eye: `<path d="M10 64 C30 30 98 30 118 64 C98 98 30 98 10 64 Z"/><circle cx="64" cy="64" r="18"/><circle cx="64" cy="64" r="6" class="f"/>`,
  error: `<path d="M64 14 L118 108 H10 Z"/><path d="M64 48 V78"/><circle cx="64" cy="92" r="4" class="f"/>`,
  infinity: `<path d="M64 64 C50 40 18 40 18 64 C18 88 50 88 64 64 C78 40 110 40 110 64 C110 88 78 88 64 64 Z"/>`,
};

function icon(name, body, palette) {
  const [a, b] = palette;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="-8 -8 144 144">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4.5"/></filter>
    <style>
      .s path,.s circle,.s rect,.s ellipse,.s polygon{fill:none;stroke:url(#g);stroke-width:6;stroke-linecap:round;stroke-linejoin:round}
      .s .f{fill:url(#g);stroke:none}
      .s .hot{stroke:#FFFFFF}
      .s .t{fill:url(#g);stroke:none}
    </style>
  </defs>
  <g class="s" filter="url(#glow)" opacity="0.85">${body}</g>
  <g class="s">${body}</g>
</svg>`;
  return sharp(Buffer.from(svg)).png().toFile(`assets/icons/${name}.png`);
}

function phoneFrame() {
  const w = 600, h = 1200;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22D3EE"/><stop offset="0.5" stop-color="#8B5CF6"/><stop offset="1" stop-color="#F472B6"/></linearGradient>
    <linearGradient id="scr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14112E"/><stop offset="1" stop-color="#0B0A1F"/></linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>
  </defs>
  <rect x="30" y="30" width="${w - 60}" height="${h - 60}" rx="70" fill="none" stroke="url(#edge)" stroke-width="10" filter="url(#glow)" opacity="0.8"/>
  <rect x="30" y="30" width="${w - 60}" height="${h - 60}" rx="70" fill="#05040F" stroke="url(#edge)" stroke-width="6"/>
  <rect x="50" y="50" width="${w - 100}" height="${h - 100}" rx="54" fill="url(#scr)"/>
  <rect x="${w / 2 - 60}" y="66" width="120" height="26" rx="13" fill="#05040F"/>
</svg>`;
  return sharp(Buffer.from(svg)).png().toFile("assets/phone.png");
}

function glowLine() {
  // horizontal energy beam used as pipeline connector
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="60">
  <defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#22D3EE" stop-opacity="0.1"/><stop offset="0.5" stop-color="#FFFFFF"/><stop offset="1" stop-color="#C084FC" stop-opacity="0.1"/></linearGradient>
  <filter id="b"><feGaussianBlur stdDeviation="6"/></filter></defs>
  <rect x="0" y="22" width="800" height="16" rx="8" fill="url(#g)" filter="url(#b)"/>
  <rect x="0" y="28" width="800" height="4" rx="2" fill="url(#g)"/></svg>`;
  return sharp(Buffer.from(svg)).png().toFile("assets/beam.png");
}

(async () => {
  await background("hero");
  await background("main");
  await orb("violet", "#7C3AED");
  await orb("cyan", "#06B6D4");
  await orb("pink", "#EC4899");
  await novaStar();
  await phoneFrame();
  await glowLine();
  const palettes = [["#22D3EE", "#A78BFA"], ["#A78BFA", "#F472B6"], ["#34D399", "#22D3EE"], ["#FBBF24", "#F472B6"]];
  let i = 0;
  for (const [n, body] of Object.entries(ICONS)) await icon(n, body, palettes[i++ % palettes.length]);
  console.log("assets done:", Object.keys(ICONS).length, "icons");
})();
