// iNiKKi reel runtime: deterministic canvas animation (same plan + same time = same frame).
// Everything is drawn from the time t, never from state, so any frame can be rendered on its own.
export const W = 1080, H = 1920;
export const SAFE = { top: 250, bottom: 1540, left: 60, right: 960 }; // keep words inside (AGENT.md brand safe zones)

// ---------------------------------------------------------------- maths and easing
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, p) => a + (b - a) * p;
export const prog = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : clamp((t - a) / (b - a)));
export const E = {
  linear: p => p,
  inQuad: p => p * p,
  outQuad: p => 1 - (1 - p) * (1 - p),
  inOutQuad: p => (p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2),
  inCubic: p => p * p * p,
  outCubic: p => 1 - Math.pow(1 - p, 3),
  inOutCubic: p => (p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  outQuart: p => 1 - Math.pow(1 - p, 4),
  outExpo: p => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
  inExpo: p => (p <= 0 ? 0 : Math.pow(2, 10 * p - 10)),
  inOutExpo: p => (p <= 0 ? 0 : p >= 1 ? 1 : p < .5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2),
  outBack: p => { const s = 1.70158; return 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2); },
  outBackBig: p => { const s = 3.2; return 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2); },
  inBack: p => { const s = 1.70158; return (s + 1) * p * p * p - s * p * p; },
  outElastic: p => (p <= 0 ? 0 : p >= 1 ? 1 : Math.pow(2, -10 * p) * Math.sin((p * 10 - .75) * (2 * Math.PI) / 3) + 1),
};
export const ep = (t, a, b, e = E.outCubic) => e(prog(t, a, b));
// enter / hold / leave: returns 0..1 visibility with eased edges
export function life(t, a, b, din = .35, dout = .3, ein = E.outCubic, eout = E.inCubic) {
  if (t < a || t > b) return 0;
  const i = ein(prog(t, a, a + din));
  const o = 1 - eout(prog(t, b - dout, b));
  return Math.min(i, o);
}
export function hash(str) { let h = 2166136261; for (const c of String(str)) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
export function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s + 0x6D2B79F5) | 0; let x = Math.imul(s ^ (s >>> 15), 1 | s); x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x; return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
}
// smooth noise in -1..1 from a few sines (deterministic)
export function wobble(t, seed = 1, speed = 1) {
  const r = rng(seed); let v = 0;
  for (let k = 0; k < 3; k++) v += Math.sin(t * speed * (0.7 + r() * 2.3) + r() * 6.28) / 3;
  return v;
}

// ---------------------------------------------------------------- environment
const FONT_LOADS = [
  ['400 100px "Anton"', 'A'], ['400 100px "Bebas Neue"', 'A'], ['900 100px "Inter"', 'A'], ['800 100px "Inter"', 'A'],
  ['700 100px "Inter"', 'A'], ['600 100px "Inter"', 'A'], ['900 60px "Noto Sans Tamil"', 'தமிழ்'],
  ['700 60px "Noto Sans Tamil"', 'தமிழ்'], ['500 60px "Noto Sans Tamil"', 'தமிழ்'], ['italic 800 100px "Playfair Display"', 'A'],
];

export function makeCanvas(w = W, h = H) { const c = new OffscreenCanvas(w, h); return c; }

async function loadImage(src) {
  const im = new Image(); im.src = src; await im.decode(); return im;
}

// crop: [x, y, w, h] in 0..1 of the source; removes baked-in text from trailer frames
function prepare(im, crop) {
  const [cx, cy, cw, ch] = crop || [0, 0, 1, 1];
  const sw = Math.round(im.naturalWidth * cw), sh = Math.round(im.naturalHeight * ch);
  const c = makeCanvas(sw, sh);
  c.getContext('2d').drawImage(im, im.naturalWidth * cx, im.naturalHeight * cy, sw, sh, 0, 0, sw, sh);
  return c;
}

export function filtered(src, filter, scale = 1) {
  const c = makeCanvas(Math.round(src.width * scale), Math.round(src.height * scale));
  const x = c.getContext('2d'); x.filter = filter; x.drawImage(src, 0, 0, c.width, c.height); return c;
}

// two-tone image: shadows -> dark colour, highlights -> light colour
export function duotone(src, dark, light, contrast = 1.15) {
  const c = makeCanvas(src.width, src.height), x = c.getContext('2d');
  x.filter = `grayscale(1) contrast(${contrast})`; x.drawImage(src, 0, 0); x.filter = 'none';
  const d = x.getImageData(0, 0, c.width, c.height), p = d.data;
  const a = hexRgb(dark), b = hexRgb(light);
  for (let i = 0; i < p.length; i += 4) { const v = p[i] / 255; p[i] = a[0] + (b[0] - a[0]) * v; p[i + 1] = a[1] + (b[1] - a[1]) * v; p[i + 2] = a[2] + (b[2] - a[2]) * v; }
  x.putImageData(d, 0, 0); return c;
}
export function hexRgb(h) { const n = parseInt(h.replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
export function rgba(h, a) { const [r, g, b] = hexRgb(h); return `rgba(${r},${g},${b},${a})`; }

function makeGrain(seed, n = 4) {
  const tiles = []; const r = rng(seed);
  for (let k = 0; k < n; k++) {
    const c = makeCanvas(540, 960), x = c.getContext('2d'), d = x.createImageData(540, 960);
    for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (r() - .5) * 150; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
    x.putImageData(d, 0, 0); tiles.push(c);
  }
  return tiles;
}
function makeSoftDot() {
  const c = makeCanvas(128, 128), x = c.getContext('2d'), g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(.35, 'rgba(255,255,255,.45)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 128, 128); return c;
}

export async function createEnv(canvas, plan, timeline) {
  const ctx = canvas.getContext('2d', { alpha: false });
  await Promise.all(FONT_LOADS.map(([f, s]) => document.fonts.load(f, s).catch(() => null)));
  const env = { canvas, ctx, plan, tl: timeline, W, H, warnings: [], img: {}, seed: hash(plan.id), fps: timeline.fps || 30 };
  for (const [k, a] of Object.entries(plan.assets || {})) {
    try { const im = await loadImage('/' + a.src); env.img[k] = prepare(im, a.crop); }
    catch (e) { env.warnings.push(`image missing: ${k} (${a.src})`); env.img[k] = makeCanvas(16, 9); }
  }
  env.grain = makeGrain(env.seed); env.dot = makeSoftDot();
  env.bufA = makeCanvas(); env.bufB = makeCanvas();
  env.beats = timeline.beats || [];
  env.cache = new Map();
  env.memo = (key, fn) => { if (!env.cache.has(key)) env.cache.set(key, fn()); return env.cache.get(key); };
  return env;
}

// ---------------------------------------------------------------- timing helpers
// time of a word inside a screen (graphics land on the word the voice says)
export function cue(env, si, spec, fallback = 0) {
  const s = env.tl.screens[si];
  if (spec == null) return s.start + fallback;
  if (typeof spec === 'number') return s.start + spec;
  if (spec.at != null) return s.start + spec.at;
  if (spec.frac != null) return s.start + (s.end - s.start) * spec.frac;
  if (spec.word) {
    const k = spec.word.toLowerCase();
    const w = (s.words || []).find(w => w.w.toLowerCase().includes(k) || (k.includes(w.w.toLowerCase()) && w.w.length > 2));
    if (w) return w.t + (spec.off || 0);
    env.warnings.push(`cue word not found: "${spec.word}" in screen ${si}`);
    return s.start + (spec.fallback ?? fallback);
  }
  return s.start + fallback;
}
// a soft pulse that peaks on each music beat
export function beatPulse(env, t, decay = 7) {
  let v = 0;
  for (const b of env.beats) { if (b > t) break; const d = t - b; if (d < 1) v = Math.max(v, Math.exp(-d * decay)); }
  return v;
}
export function nearestBeat(env, t, win = .25) {
  let best = t, bd = win;
  for (const b of env.beats) { const d = Math.abs(b - t); if (d < bd) { bd = d; best = b; } }
  return best;
}
// camera shake from hit times
export function shake(t, hits, amp = 14, seed = 3) {
  let x = 0, y = 0;
  for (const h of hits) { const d = t - h; if (d < 0 || d > .6) continue; const k = Math.exp(-d * 9) * amp; x += Math.sin(d * 70 + seed) * k; y += Math.cos(d * 63 + seed * 2) * k; }
  return [x, y];
}

// ---------------------------------------------------------------- drawing helpers
export function fill(ctx, c) { ctx.fillStyle = c; ctx.fillRect(0, 0, W, H); }
export function grad(ctx, x0, y0, x1, y1, stops, rect = [0, 0, W, H]) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of stops) g.addColorStop(o, c);
  ctx.fillStyle = g; ctx.fillRect(...rect);
}
export function radial(ctx, x, y, r, stops, rect = [0, 0, W, H]) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r); for (const [o, c] of stops) g.addColorStop(o, c);
  ctx.fillStyle = g; ctx.fillRect(...rect);
}
// image covering a box, with focus point, zoom and pan (Ken Burns)
export function cover(ctx, img, x, y, w, h, o = {}) {
  if (!img) return;
  const iw = img.width, ih = img.height, s = Math.max(w / iw, h / ih) * (o.zoom || 1);
  const dw = iw * s, dh = ih * s, fx = o.fx ?? .5, fy = o.fy ?? .5;
  let dx = x + w / 2 - fx * dw + (o.px || 0) * w, dy = y + h / 2 - fy * dh + (o.py || 0) * h;
  dx = Math.min(x, Math.max(x + w - dw, dx)); dy = Math.min(y, Math.max(y + h - dh, dy));
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.drawImage(img, dx, dy, dw, dh);
  ctx.restore();
}
export function rrect(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

// floating cinematic frame with shadow, glow edge and slow drift
export function framed(ctx, img, cx, cy, w, h, o = {}) {
  const r = o.r ?? 28;
  ctx.save();
  ctx.translate(cx, cy); ctx.rotate(o.rot || 0); ctx.scale(o.scale || 1, o.scale || 1);
  ctx.shadowColor = 'rgba(0,0,0,.65)'; ctx.shadowBlur = 60; ctx.shadowOffsetY = 30;
  rrect(ctx, -w / 2, -h / 2, w, h, r); ctx.fillStyle = '#000'; ctx.fill();
  ctx.shadowColor = 'transparent';
  ctx.save(); rrect(ctx, -w / 2, -h / 2, w, h, r); ctx.clip();
  cover(ctx, img, -w / 2, -h / 2, w, h, o);
  if (o.tint) { ctx.fillStyle = o.tint; ctx.fillRect(-w / 2, -h / 2, w, h); }
  ctx.restore();
  if (o.edge) { rrect(ctx, -w / 2, -h / 2, w, h, r); ctx.lineWidth = o.edgeW || 3; ctx.strokeStyle = o.edge; ctx.stroke(); }
  ctx.restore();
}

// ---------------------------------------------------------------- text
export function font(size, family = 'Inter', weight = 800, italic = false) { return `${italic ? 'italic ' : ''}${weight} ${size}px "${family}"`; }
export function setFont(ctx, size, family, weight, ls = 0, italic = false) { ctx.font = font(size, family, weight, italic); ctx.letterSpacing = `${Math.round(ls * size)}px`; }
export function fitSize(env, ctx, text, family, weight, maxW, size, min = 24, ls = 0) {
  let s = size;
  for (; s > min; s -= 2) { setFont(ctx, s, family, weight, ls); if (ctx.measureText(text).width <= maxW) return s; }
  env && env.warnings.push(`text squeezed to minimum: "${text}"`); return min;
}
// text with optional glow / stroke; returns width
export function txt(ctx, str, x, y, o = {}) {
  const size = o.size || 60;
  setFont(ctx, size, o.family || 'Inter', o.weight ?? 800, o.ls || 0, o.italic);
  ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'alphabetic';
  ctx.globalAlpha = (o.alpha ?? 1);
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.glowBlur || 30; }
  if (o.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = o.strokeW || 8; ctx.strokeStyle = o.stroke; ctx.strokeText(str, x, y); }
  ctx.fillStyle = o.color || '#fff'; ctx.fillText(str, x, y);
  ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.globalAlpha = 1;
  return ctx.measureText(str).width;
}
// slam in: big -> settle with overshoot, ghost trails, flash
export function slam(ctx, str, x, y, lt, o = {}) {
  if (lt < 0) return;
  const d = o.d || .32, p = prog(lt, 0, d);
  const sc = lerp(o.from || 1.9, 1, E.outExpo(p));
  const wob = 1 + (o.punch ?? .035) * Math.exp(-lt * 7) * Math.sin(lt * 28);
  if (p < 1) {
    for (let k = 1; k <= 3; k++) {
      ctx.save(); ctx.translate(x, y); const g = sc * (1 + k * .07 * (1 - p)); ctx.scale(g, g);
      txt(ctx, str, 0, 0, { ...o, alpha: (1 - p) * .16, glow: null, stroke: null }); ctx.restore();
    }
  }
  ctx.save(); ctx.translate(x, y); ctx.scale(sc * wob, sc * wob);
  txt(ctx, str, 0, 0, { ...o, alpha: (o.alpha ?? 1) * clamp(p * 4) });
  ctx.restore();
}
// words arrive one after another (rise + fade + slight blur feel)
export function wordsIn(ctx, words, x, y, lt, o = {}) {
  const list = Array.isArray(words) ? words : words.split(' ');
  const size = o.size || 60; setFont(ctx, size, o.family || 'Inter', o.weight ?? 800, o.ls || 0);
  const gap = size * (o.gap ?? .28);
  const widths = list.map(w => ctx.measureText(w).width);
  const total = widths.reduce((a, b) => a + b, 0) + gap * (list.length - 1);
  let cx = (o.align === 'left') ? x : x - total / 2;
  list.forEach((w, i) => {
    const st = (o.stagger ?? .08) * i, p = ep(lt, st, st + (o.d || .45), E.outBack);
    if (p <= 0) { cx += widths[i] + gap; return; }
    const yy = y + (1 - p) * (o.rise ?? 50);
    txt(ctx, w, cx + widths[i] / 2, yy, { ...o, align: 'center', alpha: clamp(p * 1.4) * (o.alpha ?? 1) });
    cx += widths[i] + gap;
  });
  return total;
}
// pill label with pop
export function pill(ctx, str, x, y, lt, o = {}) {
  if (lt < 0) return;
  const p = ep(lt, 0, o.d || .35, E.outBack), size = o.size || 34;
  setFont(ctx, size, o.family || 'Inter', o.weight ?? 800, o.ls ?? .06);
  const w = ctx.measureText(str).width + size * 1.4, h = size * 1.75;
  ctx.save(); ctx.translate(x, y); ctx.scale(p, p); ctx.globalAlpha = clamp(p * 2) * (o.alpha ?? 1);
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = 30; }
  rrect(ctx, -w / 2, -h / 2, w, h, h / 2); ctx.fillStyle = o.bg || '#F8C028'; ctx.fill();
  ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
  if (o.border) { ctx.lineWidth = 3; ctx.strokeStyle = o.border; ctx.stroke(); }
  ctx.fillStyle = o.color || '#0A0F18'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(str, 0, size * .05);
  ctx.restore(); ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- living layers
// floating dust / bokeh (stateless, so every frame can be drawn on its own)
export function dust(env, ctx, t, o = {}) {
  const r = rng(o.seed ?? 11), n = o.n ?? 40, col = o.color || '#fff';
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const x0 = r() * W, y0 = r() * H, vx = (r() - .5) * (o.speed ?? 30), vy = -(r() * (o.rise ?? 40) + 8), s = lerp(o.min ?? 4, o.max ?? 26, r() ** 2), ph = r() * 6.28;
    const x = ((x0 + vx * t) % W + W) % W, y = ((y0 + vy * t) % H + H) % H;
    const a = (o.alpha ?? .35) * (.5 + .5 * Math.sin(t * (1 + r() * 2) + ph));
    ctx.globalAlpha = a; ctx.drawImage(tint(env, col), x - s, y - s, s * 2, s * 2);
  }
  ctx.restore(); ctx.globalAlpha = 1;
}
export function tint(env, col) {
  return env.memo('dot' + col, () => { const c = makeCanvas(128, 128), x = c.getContext('2d'); x.drawImage(env.dot, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = col; x.fillRect(0, 0, 128, 128); return c; });
}
// soft band of light passing across
export function sweep(ctx, t, t0, d = 1.1, o = {}) {
  const p = prog(t, t0, t0 + d); if (p <= 0 || p >= 1) return;
  const x = lerp(-W * .6, W * 1.6, E.inOutQuad(p)), ang = o.angle ?? -.35, wdt = o.width ?? 260;
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(x, H / 2); ctx.rotate(ang);
  const g = ctx.createLinearGradient(-wdt, 0, wdt, 0);
  g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(.5, `rgba(255,255,255,${o.alpha ?? .22})`); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(-wdt, -H * 1.5, wdt * 2, H * 3); ctx.restore();
}
// expanding ring of light (a hit)
export function ring(ctx, x, y, lt, o = {}) {
  if (lt < 0 || lt > (o.d || .7)) return;
  const p = lt / (o.d || .7), r = lerp(o.r0 || 40, o.r1 || 520, E.outCubic(p));
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = (1 - p) * (o.alpha ?? .8);
  ctx.lineWidth = lerp(o.w || 18, 1, p); ctx.strokeStyle = o.color || '#F8C868';
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); ctx.globalAlpha = 1;
}
// horizontal light streaks (anamorphic flare)
export function streak(ctx, x, y, lt, o = {}) {
  const a = (o.alpha ?? .8) * life(lt, 0, o.d || 1.2, .15, .8);
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a;
  const len = (o.len || 900) * (0.6 + .4 * ep(lt, 0, .5));
  const g = ctx.createLinearGradient(x - len, 0, x + len, 0);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.5, o.color || 'rgba(255,214,140,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(x - len, y - (o.h || 4), len * 2, (o.h || 4) * 2);
  ctx.globalAlpha = a * .35; ctx.fillRect(x - len * .6, y - (o.h || 4) * 6, len * 1.2, (o.h || 4) * 12);
  ctx.restore(); ctx.globalAlpha = 1;
}
export function flash(ctx, t, t0, o = {}) {
  const d = t - t0; if (d < 0 || d > (o.d || .35)) return;
  ctx.save(); ctx.globalAlpha = (1 - d / (o.d || .35)) * (o.alpha ?? .55); ctx.fillStyle = o.color || '#fff'; ctx.fillRect(0, 0, W, H); ctx.restore(); ctx.globalAlpha = 1;
}
export function vignette(env, ctx, strength = .75) {
  const v = env.memo('vig' + strength, () => { const c = makeCanvas(), x = c.getContext('2d'); const g = x.createRadialGradient(W / 2, H * .45, H * .22, W / 2, H * .5, H * .78); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${strength})`); x.fillStyle = g; x.fillRect(0, 0, W, H); return c; });
  ctx.drawImage(v, 0, 0);
}
export function grain(env, ctx, amount = .07) {
  const tile = env.grain[env.frame % env.grain.length];
  ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = amount * 3.2; ctx.drawImage(tile, 0, 0, W, H); ctx.restore(); ctx.globalAlpha = 1;
}
export function scanlines(env, ctx, alpha = .12, t = 0) {
  const s = env.memo('scan', () => { const c = makeCanvas(W, 8), x = c.getContext('2d'); x.fillStyle = 'rgba(0,0,0,1)'; x.fillRect(0, 0, W, 3); return c; });
  ctx.save(); ctx.globalAlpha = alpha; const off = (t * 60) % 8;
  for (let y = -8 + off; y < H; y += 8) ctx.drawImage(s, 0, y); ctx.restore(); ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- transitions between screens
function transition(env, type, p, drawA, drawB) {
  const { ctx, bufA, bufB } = env;
  const a = bufA.getContext('2d'), b = bufB.getContext('2d');
  a.setTransform(1, 0, 0, 1, 0, 0); b.setTransform(1, 0, 0, 1, 0, 0);
  drawA(a); drawB(b);
  const e = E.inOutCubic(clamp(p));
  ctx.save();
  if (type === 'whip' || type === 'push') {
    const vert = type === 'push', dist = vert ? H : W;
    const off = e * dist, blur = Math.sin(Math.PI * clamp(p)) * 70;
    for (let k = 0; k < 4; k++) {
      ctx.globalAlpha = k === 0 ? 1 : .22;
      const d = k * blur * .5;
      if (vert) { ctx.drawImage(bufA, 0, -off - d); ctx.drawImage(bufB, 0, dist - off - d); }
      else { ctx.drawImage(bufA, -off - d, 0); ctx.drawImage(bufB, dist - off - d, 0); }
    }
  } else if (type === 'zoom') {
    const sa = 1 + e * .45, sb = .82 + .18 * e;
    ctx.globalAlpha = 1; ctx.drawImage(bufB, W / 2 - W * sb / 2, H / 2 - H * sb / 2, W * sb, H * sb);
    ctx.globalAlpha = 1 - e; ctx.drawImage(bufA, W / 2 - W * sa / 2, H / 2 - H * sa / 2, W * sa, H * sa);
    ctx.globalAlpha = Math.sin(Math.PI * clamp(p)) * .5; ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
  } else if (type === 'flash') {
    ctx.drawImage(p < .5 ? bufA : bufB, 0, 0);
    ctx.globalAlpha = (1 - Math.abs(p - .5) * 2) * .9; ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
  } else if (type === 'glitch') {
    const src = p < .5 ? bufA : bufB, amt = 1 - Math.abs(p - .5) * 2, r = rng(env.frame * 31 + 7);
    ctx.drawImage(src, 0, 0);
    for (let k = 0; k < 14; k++) {
      const y = r() * H, h = 20 + r() * 140, dx = (r() - .5) * 260 * amt;
      ctx.drawImage(src, 0, y, W, h, dx, y, W, h);
      if (r() < .5) { ctx.globalAlpha = .35 * amt; ctx.fillStyle = r() < .5 ? '#E5484D' : '#78E0D0'; ctx.fillRect(0, y, W, h * .3); ctx.globalAlpha = 1; }
    }
  } else if (type === 'wipe') {
    ctx.drawImage(bufA, 0, 0);
    ctx.save(); ctx.beginPath(); const x = lerp(-400, W + 400, e);
    ctx.moveTo(-10, 0); ctx.lineTo(x + 400, 0); ctx.lineTo(x - 400, H); ctx.lineTo(-10, H); ctx.closePath(); ctx.clip();
    ctx.drawImage(bufB, 0, 0); ctx.restore();
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = Math.sin(Math.PI * e) * .6;
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(x + 400, 0); ctx.lineTo(x - 400, H); ctx.stroke(); ctx.restore();
  } else {
    ctx.drawImage(p < .5 ? bufA : bufB, 0, 0);
  }
  ctx.restore(); ctx.globalAlpha = 1;
}

export function renderFrame(env, reel, t) {
  const { ctx } = env;
  env.t = t; env.frame = Math.round(t * env.fps);
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  const S = reel.screens;
  let i = S.findIndex(s => t >= s.start && t < s.end); if (i < 0) i = t < S[0].start ? 0 : S.length - 1;
  const cur = S[i], nxt = S[i + 1];
  const half = s => (s && s.tin && s.tin.d ? s.tin.d : .36) / 2;
  let A = null, B = null, p = 0, type = null;
  if (i > 0 && t - cur.start < half(cur) && cur.tin && cur.tin.type !== 'cut') { A = S[i - 1]; B = cur; const h = half(cur); p = (t - (cur.start - h)) / (2 * h); type = cur.tin.type; }
  else if (nxt && nxt.start - t < half(nxt) && nxt.tin && nxt.tin.type !== 'cut') { A = cur; B = nxt; const h = half(nxt); p = (t - (nxt.start - h)) / (2 * h); type = nxt.tin.type; }
  const draw = (s, c) => { c.save(); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; s.draw(c, t - s.start, t); c.restore(); };
  if (A) transition(env, type, p, c => draw(A, c), c => draw(B, c));
  else draw(cur, ctx);
  if (reel.overlay) { ctx.save(); reel.overlay(ctx, t); ctx.restore(); }
  if (reel.post) reel.post(ctx, t); else { vignette(env, ctx); grain(env, ctx); }
}
