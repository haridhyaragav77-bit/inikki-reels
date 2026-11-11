// Shared by every template. Every frame is a pure function of time t (seconds): same plan, same reel.
window.QC = [];   // flags the template raises (text that had to shrink a lot, overflow) — read by the renderer
window.T = (() => {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const easeOut = k => 1 - Math.pow(1 - clamp(k), 3);
  const easeIn = k => Math.pow(clamp(k), 3);
  const easeInOut = k => { k = clamp(k); return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
  const back = k => { k = clamp(k); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); };
  function seed(str) {  // repeatable "random" per reel id
    let h = 1779033703 ^ str.length;
    for (let i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
    return function () { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; };
  }
  function timeline(screens) { let t = 0; return screens.map((s, i) => { const o = Object.assign({}, s, { i, start: t, end: t + s.dur }); t += s.dur; return o; }); }
  function active(tl, t) { for (const s of tl) if (t < s.end) return s; return tl[tl.length - 1]; }
  const el = (tag, cls, parent) => { const e = document.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; };
  const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const mark = s => esc(s).replace(/\*(.+?)\*/g, "<em>$1</em>");      // *word* → accent colour
  function rgba(hex, a) { const h = String(hex || "#000").replace("#", ""); const n = parseInt(h.length === 3 ? h.split("").map(c => c + c).join("") : h, 16); return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`; }

  // Brand kit → CSS variables. brand = {colors, fonts, safe_zones, tokens:{type_scale_px, layout, motion, color, gradient}}
  function applyBrand(b) {
    const r = document.documentElement.style, c = b.colors || {}, tk = b.tokens || {}, tc = tk.color || {}, ts = tk.type_scale_px || {}, lay = tk.layout || {};
    const set = (k, v) => { if (v != null) r.setProperty(k, String(v)); };
    set("--c-primary", c.primary); set("--c-gold", c.gold); set("--c-teal", c.teal); set("--c-navy", c.navy); set("--c-violet", c.violet);
    set("--c-alert", c.alert); set("--c-text", c.text); set("--c-muted", c.muted);
    set("--c-surface", tc.card_surface || c.navy); set("--c-border", tc.card_border || c.muted);
    set("--fs-kicker", (ts.kicker || 22) + "px"); set("--fs-card-headline", (ts.card_headline || 64) + "px"); set("--fs-cine-line", (ts.cinematic_line || 54) + "px");
    set("--fs-cine-headline", (ts.cinematic_headline || 96) + "px"); set("--fs-tamil", (ts.tamil_line || 40) + "px"); set("--fs-chip", (ts.chip || 26) + "px"); set("--fs-caption", (ts.caption_box || 38) + "px");
    set("--r-card", (lay.radius_card || 24) + "px"); set("--r-chip", (lay.radius_chip || 12) + "px");
    const scrim = (tk.gradient || {}).cinematic_bottom_scrim; if (scrim) { set("--scrim-a", scrim[0]); set("--scrim-b", scrim[1]); }
    const sz = b.safe_zones || {};
    window.SAFE = { top: sz.top || 250, bottom: sz.bottom || 380, right: sz.right || 120 };
    window.MOTION = Object.assign({ push_in_pct: [3, 5], chip_pop_ms: 200, beat_swap_ms: 350 }, tk.motion || {});
    const g = document.getElementById("safeguide");
    if (g) { g.innerHTML = `<div style="left:0;top:0;width:1080px;height:${SAFE.top}px"></div><div style="left:0;bottom:0;width:1080px;height:${SAFE.bottom}px"></div><div style="right:0;top:0;width:${SAFE.right}px;height:1920px"></div>`; g.style.display = window.DEBUG_SAFE ? "block" : "none"; }
  }

  // Badge colour names from series.yaml → brand colours (names only; the colours live in the brand kit)
  function badgeColor(name, b) {
    const c = b.colors || {}, tb = ((b.tokens || {}).color || {}).badge || {};
    const m = { gold: c.gold, teal: c.teal, ticket_yellow: c.primary, primary: c.primary, yellow: c.primary, red: c.alert, alert: c.alert, navy: c.navy, violet: tb["movie-review"], amber: tb["viral-story"], soft_gold: tb["artwork-quote"] };
    return m[name] || tb[name] || (/^#/.test(name || "") ? name : c.teal);
  }

  // Fit one block of text. The block is a fixed box; the text sits in its first child (a span).
  // Tries one line from maxPx down to minPx; if it still does not fit and wrapMin is given, wraps onto up to maxLines.
  function fit(box, maxPx, minPx, opt = {}) {
    const inner = box.firstElementChild || box, wrapMin = opt.wrapMin, maxLines = opt.maxLines || 2;
    const wide = () => inner.scrollWidth > box.clientWidth + 1;
    box.style.whiteSpace = "nowrap"; let s = maxPx; box.style.fontSize = s + "px";
    while (s > minPx && wide()) { s -= 2; box.style.fontSize = s + "px"; }
    if (wide() && wrapMin) {
      box.style.whiteSpace = "normal"; s = Math.min(maxPx, Math.max(minPx, opt.wrapMax || minPx + 8)); box.style.fontSize = s + "px";
      const lines = () => Math.round(inner.getBoundingClientRect().height / (parseFloat(getComputedStyle(inner).lineHeight) || s * 1.2));
      while (s > wrapMin && (lines() > maxLines || wide())) { s -= 2; box.style.fontSize = s + "px"; }
      if (lines() > maxLines || wide()) window.QC.push({ flag: "text does not fit even at the smallest size", text: inner.textContent.slice(0, 60) });
    } else if (wide()) window.QC.push({ flag: "text does not fit on one line", text: inner.textContent.slice(0, 60) });
    return s;
  }

  // Safe-zone check, called by the renderer once per screen: every visible [data-safe] element must sit inside the safe area
  function safeCheck(screenIdx) {
    const out = [], S = window.SAFE || { top: 250, bottom: 380, right: 120 };
    document.querySelectorAll("[data-safe]").forEach(e => {
      const cs = getComputedStyle(e); if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) < 0.05) return;
      const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return;
      const tr = (e.firstElementChild && e.hasAttribute("data-text")) ? e.firstElementChild.getBoundingClientRect() : r;
      if (tr.top < S.top - 4) out.push({ screen: screenIdx, flag: `${e.id || e.className} is above the top safe line`, by: Math.round(S.top - tr.top) });
      if (tr.bottom > 1920 - S.bottom + 4) out.push({ screen: screenIdx, flag: `${e.id || e.className} is below the bottom safe line`, by: Math.round(tr.bottom - (1920 - S.bottom)) });
      if (tr.right > 1080 - S.right + 4) out.push({ screen: screenIdx, flag: `${e.id || e.className} runs under Instagram's buttons on the right`, by: Math.round(tr.right - (1080 - S.right)) });
      if (tr.left < 30) out.push({ screen: screenIdx, flag: `${e.id || e.className} touches the left edge`, by: Math.round(30 - tr.left) });
    });
    return out;
  }

  // Frame-sequence visuals: {frames:{dir,count,fps,ext}} → the file for local time lt (holds the last frame when the clip is short)
  function frameSrc(v, lt) {
    const f = v.frames; if (!f || !f.count) return null;
    const i = Math.min(f.count - 1, Math.max(0, Math.floor(lt * (f.fps || 30))));
    return f.dir + "/f" + String(i + 1).padStart(4, "0") + "." + (f.ext || "jpg");
  }
  async function setSrc(img, src) {
    if (!src) return; if (img.dataset.src === src) return;
    img.dataset.src = src; img.src = src.startsWith("/") ? "file://" + src : src;
    try { await img.decode(); } catch (e) { /* missing file: keep the previous frame */ }
  }

  // Noise tiles for film grain, made once from the seed
  function grainTiles(rand, n = 4, size = 256) {
    const out = [];
    for (let k = 0; k < n; k++) {
      const c = document.createElement("canvas"); c.width = c.height = size; const ctx = c.getContext("2d");
      const im = ctx.createImageData(size, size), d = im.data;
      for (let i = 0; i < d.length; i += 4) { const v = 90 + Math.floor(rand() * 120); d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; }
      ctx.putImageData(im, 0, 0); out.push("url(" + c.toDataURL() + ")");
    }
    return out;
  }

  // Mascot: the brand's image if the kit has one, else a drawn ticket with a smile in the brand colour
  function mascotHTML(b, size = 140) {
    if (b.mascot_src) return `<img src="${b.mascot_src}" style="width:${size}px;height:${size}px;object-fit:contain">`;
    const y = (b.colors || {}).primary, n = (b.colors || {}).navy;
    return `<svg width="${size}" height="${size}" viewBox="0 0 140 140"><g transform="rotate(-12 70 70)"><path d="M18 42 h104 a10 10 0 0 1 10 10 v12 a8 8 0 0 0 0 16 v12 a10 10 0 0 1 -10 10 h-104 a10 10 0 0 1 -10 -10 v-12 a8 8 0 0 0 0 -16 v-12 a10 10 0 0 1 10 -10z" fill="${y}" stroke="${n}" stroke-width="4"/><line x1="38" y1="46" x2="38" y2="98" stroke="${n}" stroke-width="4" stroke-dasharray="6 6"/><circle cx="68" cy="62" r="5" fill="${n}"/><circle cx="98" cy="62" r="5" fill="${n}"/><path d="M62 80 q21 18 42 0" stroke="${n}" stroke-width="5" fill="none" stroke-linecap="round"/></g></svg>`;
  }

  async function fontsReady() {
    await Promise.all(['800 64px "BrandCard"', '500 40px "BrandCard"', '700 40px "BrandTamil"', '500 40px "BrandTamil"', '96px "BrandCinematic"'].map(f => document.fonts.load(f, "Aaஅ")));
    await document.fonts.ready;
  }

  return { clamp, lerp, easeOut, easeIn, easeInOut, back, seed, timeline, active, el, esc, mark, rgba, applyBrand, badgeColor, fit, safeCheck, frameSrc, setSrc, grainTiles, mascotHTML, fontsReady };
})();
