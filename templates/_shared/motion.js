// Shared motion graphics (motion library: niches/tamil-cinema/motion_library.md).
// Every function draws from time only. lt = seconds since the graphic's screen started.
import { W, H, clamp, lerp, prog, ep, E, life, rng, txt, setFont, pill, wordsIn, slam, ring, makeCanvas, rgba, beatPulse, tint, rrect } from './runtime.js';

// ---------------------------------------------------------------- the ticket mascot (brand sign-off)
export function mascot(ctx, x, y, s, t, enter = 1) {
  if (enter <= 0) return;
  ctx.save();
  ctx.translate(x, y + Math.sin(t * 3) * 8 * s + (1 - enter) * 300);
  ctx.rotate(-.14 + Math.sin(t * 2.2) * .06); ctx.scale(s * enter, s * enter);
  const w = 230, h = 146, r = 24, n = 22;
  ctx.beginPath();
  ctx.moveTo(-w / 2 + r, -h / 2); ctx.lineTo(w / 2 - r, -h / 2); ctx.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
  ctx.lineTo(w / 2, -n); ctx.arc(w / 2, 0, n, -Math.PI / 2, Math.PI / 2, true); ctx.lineTo(w / 2, h / 2 - r);
  ctx.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); ctx.lineTo(-w / 2 + r, h / 2); ctx.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r);
  ctx.lineTo(-w / 2, n); ctx.arc(-w / 2, 0, n, Math.PI / 2, -Math.PI / 2, true); ctx.lineTo(-w / 2, -h / 2 + r);
  ctx.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2); ctx.closePath();
  ctx.shadowColor = 'rgba(248,192,40,.65)'; ctx.shadowBlur = 50; ctx.fillStyle = '#F8C028'; ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
  ctx.setLineDash([10, 10]); ctx.strokeStyle = 'rgba(10,15,24,.35)'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(w / 2 - 58, -h / 2 + 14); ctx.lineTo(w / 2 - 58, h / 2 - 14); ctx.stroke(); ctx.setLineDash([]);
  const blink = (t % 3.3) > 3.12 ? .15 : 1;
  ctx.fillStyle = '#0A0F18';
  ctx.beginPath(); ctx.ellipse(-52, -16, 11, 15 * blink, 0, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.ellipse(6, -16, 11, 15 * blink, 0, 0, 7); ctx.fill();
  ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.strokeStyle = '#0A0F18';
  ctx.beginPath(); ctx.arc(-23, 6, 32, .18 * Math.PI, .82 * Math.PI); ctx.stroke();
  ctx.restore();
}

// ---------------------------------------------------------------- end card: question + send prompt + mascot + echo of the title
export function endCard(env, ctx, lt, t, o) {
  const acc = o.accent || '#F8C028', cx = o.cx ?? W / 2;
  const ey = o.echoY ?? 330, qy = o.qy ?? 760, cy = o.ctaY ?? 1180, sy = o.subY ?? 1320, [mx, my, ms] = o.mascot || [860, 1420, .9];
  if (o.echo) {
    const a = ep(lt, .05, .5);
    txt(ctx, o.echo, cx, ey - (1 - a) * 30, { size: o.echoSize || 34, weight: 800, ls: .14, color: rgba('#ffffff', .75 * a) });
    ctx.fillStyle = rgba(acc, .9 * a); ctx.fillRect(cx - 60 * a, ey + 30, 120 * a, 5);
  }
  (o.question || []).forEach((line, k) => {
    wordsIn(ctx, line.text, cx, qy + k * 132, lt - .25 - k * .22, { size: line.size || 112, family: 'Anton', weight: 400, color: line.color || '#fff', stagger: .07, rise: 70, glow: line.glow });
  });
  const pt = .95 + (o.question || []).length * .2, bp = beatPulse(env, t, 5);
  if (lt > pt) {
    ctx.save(); ctx.translate(cx, cy); const s = 1 + bp * .06; ctx.scale(s, s);
    pill(ctx, o.cta || 'SEND TO THAT FRIEND', 0, 0, lt - pt, { size: 44, bg: acc, color: '#0A0F18', glow: rgba(acc, .8), ls: .08 });
    ctx.restore();
    ring(ctx, cx, cy, lt - pt - .05, { color: acc, r0: 60, r1: 460, w: 10, alpha: .6 });
  }
  if (o.sub) wordsIn(ctx, o.sub, cx, sy, lt - pt - .3, { size: o.subSize || 44, weight: 700, family: o.subFamily || 'Inter', color: rgba('#ffffff', .88), stagger: .05, rise: 30 });
  mascot(ctx, mx, my, ms, t, ep(lt, pt + .2, pt + .8, E.outBack));
}

// ---------------------------------------------------------------- subtitles: Tamil + Tanglish, synced to the voice
// Two lines on a soft plate; the word being spoken lights up. Chunks break at sentence marks or every 4 words.
function chunks(words, ta, tg) {
  const out = []; let cur = null;
  words.forEach((w, k) => {
    if (!cur) cur = { idx: [], start: w.t };
    cur.idx.push(k);
    const raw = (ta[k] || w.w), endMark = /[.?!]$/.test(raw) || (/,$/.test(raw) && cur.idx.length >= 2);
    if (endMark || cur.idx.length >= 4 || k === words.length - 1) {
      const last = words[cur.idx[cur.idx.length - 1]];
      out.push({ ...cur, end: last.t + last.d });
      cur = null;
    }
  });
  const clean = x => (x || '').replace(/[.,]+$/, '');
  return out.map(c => ({ ...c, ta: c.idx.map(k => clean(ta[k] || words[k].w)), tg: c.idx.map(k => clean(tg[k] || '')) }));
}
export function subtitles(env, ctx, t, o) {
  const S = env.tl.screens;
  for (let si = 0; si < S.length; si++) {
    const sc = S[si], words = sc.words || [];
    if (!words.length || t < words[0].t - .1 || t > (sc.voice_end ?? sc.end) + .3) continue;
    const ps = env.plan.screens[si];
    const list = env.memo('subs:' + si, () => chunks(words, (ps.voice || '').split(/\s+/), (ps.voice_tg || '').split(/\s+/)));
    let c = null; for (const ch of list) if (t >= ch.start - .08) c = ch;
    if (!c) return;
    const cx = o.cx ?? W / 2, y = o.y ?? 1415, maxW = o.maxW ?? 840;
    const p = ep(t, c.start - .08, c.start + .12, E.outCubic);
    let taS = o.taSize || 50, tgS = o.tgSize || 39;
    const measure = (arr, size, fam, wt, ls) => { setFont(ctx, size, fam, wt, ls); const sp = size * .42; return { ws: arr.map(w => ctx.measureText(w).width), sp }; };
    let A = measure(c.ta, taS, 'Noto Sans Tamil', 700, 0), B = measure(c.tg, tgS, 'Inter', 800, .01);
    const total = m => m.ws.reduce((a, b) => a + b, 0) + m.sp * (m.ws.length - 1);
    const scale = Math.min(1, (maxW - 64) / Math.max(total(A), total(B)));
    if (scale < 1) { taS *= scale; tgS *= scale; A = measure(c.ta, taS, 'Noto Sans Tamil', 700, 0); B = measure(c.tg, tgS, 'Inter', 800, .01); }
    const pw = Math.max(total(A), total(B)) + 70, ph = taS + tgS + 70;
    ctx.save(); ctx.translate(0, (1 - p) * 18); ctx.globalAlpha = p;
    ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 30;
    rrect(ctx, cx - pw / 2, y - ph / 2, pw, ph, 24); ctx.fillStyle = 'rgba(6,7,10,.72)'; ctx.fill();
    ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
    ctx.lineWidth = 2; ctx.strokeStyle = rgba(o.accent || '#F8C868', .35); ctx.stroke();
    const lineY = [y - ph / 2 + 32 + taS * .78, y + ph / 2 - 30];
    [[c.ta, A, taS, 'Noto Sans Tamil', 700, 0], [c.tg, B, tgS, 'Inter', 800, .01]].forEach(([arr, m, size, fam, wt, ls], li) => {
      let x = cx - total(m) / 2;
      arr.forEach((w, k) => {
        const wd = words[c.idx[k]], on = t >= wd.t - .03 && t < wd.t + wd.d + .06, done = t >= wd.t + wd.d;
        const col = on ? (o.accent || '#F8C868') : (done || li === 1 ? '#FFFFFF' : 'rgba(255,255,255,.72)');
        const bump = on ? 1 + .035 * Math.exp(-(t - wd.t) * 9) : 1;
        ctx.save(); ctx.translate(x + m.ws[k] / 2, lineY[li]); ctx.scale(bump, bump);
        txt(ctx, w, 0, 0, { size, family: fam, weight: wt, ls, color: col, alpha: li === 1 && !on ? .9 : 1 });
        ctx.restore();
        x += m.ws[k] + m.sp;
      });
    });
    ctx.restore(); ctx.globalAlpha = 1;
    return;
  }
}

// ---------------------------------------------------------------- label pin: a dot on the picture + a drawn line + a label
export function labelPin(ctx, lt, px, py, lx, ly, text, o = {}) {
  if (lt < 0) return;
  const acc = o.color || '#F8C868';
  const pd = ep(lt, 0, .25, E.outBack), pl = ep(lt, .1, .55, E.inOutCubic), pt = ep(lt, .45, .8, E.outBack);
  const pulse = .5 + .5 * Math.sin(lt * 6);
  ctx.save();
  ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = .5 * pulse * pd;
  ctx.fillStyle = acc; ctx.beginPath(); ctx.arc(px, py, 26 + 10 * pulse, 0, 7); ctx.fill();
  ctx.restore();
  ctx.fillStyle = acc; ctx.beginPath(); ctx.arc(px, py, 12 * pd, 0, 7); ctx.fill();
  ctx.strokeStyle = acc; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(px, py);
  const mx = lerp(px, lx, .0), my = ly; ctx.lineTo(lerp(px, mx, pl), lerp(py, my, pl));
  if (pl >= 1) ctx.lineTo(lerp(mx, lx, ep(lt, .55, .7)), my);
  ctx.stroke();
  if (pt > 0) {
    setFont(ctx, o.size || 44, 'Inter', 900, .06); const tw = ctx.measureText(text).width, bw = tw + 48, bh = (o.size || 44) * 1.6;
    const bx = o.align === 'right' ? lx - bw : lx;
    ctx.save(); ctx.translate(bx + bw / 2, ly); ctx.scale(pt, pt);
    ctx.fillStyle = o.bg || 'rgba(8,9,12,.82)'; ctx.beginPath(); ctx.roundRect(-bw / 2, -bh / 2, bw, bh, 12); ctx.fill();
    ctx.strokeStyle = acc; ctx.lineWidth = 3; ctx.stroke();
    txt(ctx, text, 0, (o.size || 44) * .36, { size: o.size || 44, weight: 900, ls: .06, color: '#fff' });
    ctx.restore();
  }
}

// ---------------------------------------------------------------- particles that gather into a shape (text or symbol)
export function shapePoints(env, key, text, size, family = 'Anton', step = 12) {
  return env.memo('pts:' + key, () => {
    const c = makeCanvas(W, H), x = c.getContext('2d');
    x.fillStyle = '#fff'; x.font = `400 ${size}px "${family}"`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(text, W / 2, H / 2);
    const d = x.getImageData(0, 0, W, H).data, pts = [];
    for (let y = 0; y < H; y += step) for (let xx = 0; xx < W; xx += step) if (d[(y * W + xx) * 4 + 3] > 140) pts.push([xx - W / 2, y - H / 2]);
    return pts;
  });
}
export function assemble(env, ctx, lt, pts, cx, cy, o = {}) {
  if (lt < 0) return;
  const r = rng(o.seed || 5), col = o.color || '#F8C868', spr = tint(env, col);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const flip = o.flip ? Math.cos(Math.PI * ep(lt, o.flip, o.flip + .6, E.inOutCubic) * 2) : 1;
  for (const [tx, ty] of pts) {
    const sx = (o.from ? o.from[0] : cx) + (r() - .5) * (o.spread || 1600), sy = (o.from ? o.from[1] : cy) + (r() - .5) * (o.spread || 1600) * .8;
    const delay = r() * (o.stagger ?? .6), p = E.outExpo(prog(lt, delay, delay + (o.d || 1.1)));
    const jit = Math.sin(lt * 3 + tx * .05) * 2;
    const x = lerp(sx, cx + tx * flip, p) + jit, y = lerp(sy, cy + ty, p);
    const s = (o.size || 9) * (0.7 + .6 * r());
    ctx.globalAlpha = clamp(p * 1.5) * (o.alpha ?? .9);
    ctx.drawImage(spr, x - s, y - s, s * 2, s * 2);
  }
  ctx.restore(); ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- number that rolls up (counter_rollup)
export function rollNumber(ctx, value, lt, d, x, y, o = {}) {
  const p = E.outExpo(prog(lt, 0, d)), v = value * p;
  const dec = o.decimals || 0, s = (o.prefix || '') + v.toFixed(dec) + (o.suffix || '');
  txt(ctx, s, x, y, { size: o.size || 220, family: o.family || 'Anton', weight: 400, color: o.color || '#fff', glow: o.glow, glowBlur: 40, align: o.align || 'center', ls: o.ls || 0 });
  return p;
}

// ---------------------------------------------------------------- chips that pop in one after another
export function chipsRow(ctx, items, x, y, lt, o = {}) {
  setFont(ctx, o.size || 36, 'Inter', 800, .06);
  const gap = o.gap || 20, ws = items.map(s => ctx.measureText(s).width + (o.size || 36) * 1.4);
  const total = ws.reduce((a, b) => a + b, 0) + gap * (items.length - 1);
  let cx = x - total / 2;
  items.forEach((s, k) => { pill(ctx, s, cx + ws[k] / 2, y, lt - k * (o.stagger ?? .12), o); cx += ws[k] + gap; });
}
