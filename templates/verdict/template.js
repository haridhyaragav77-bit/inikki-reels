// VERDICT — Movie Review (First Verdict) look (AGENT.md 6.6): the film's still in a dark violet tint,
// a verdict stamp that slams down, a works-vs-not balance scale, named critic cards, the star rating (22 Nov). Music-only.
import { W, H, clamp, lerp, prog, ep, E, rng, cue, beatPulse, nearestBeat, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, rgba, filtered, duotone } from '../_shared/runtime.js';
import { endCard, chipsRow, mascot } from '../_shared/motion.js';

const VIO = '#A78BFA', DEEP = '#160F26', TICKET = '#F8C028', CREAM = '#F3EEFF', GOOD = '#78E0D0', BAD = '#E5484D';

function violetBg(env, ctx, key, lt, o = {}) {
  const im = env.memo('duo:' + key, () => duotone(env.img[key], '#120a22', '#B9A4FF', 1.2));
  fill(ctx, DEEP);
  cover(ctx, im, 0, 0, W, H, { zoom: (o.zoom || 1.15) + .06 * ep(lt, 0, 6, E.linear), fx: o.fx ?? .5, fy: o.fy ?? .45 });
  ctx.save(); ctx.globalAlpha = o.dim ?? .55; fill(ctx, DEEP); ctx.restore(); ctx.globalAlpha = 1;
  radial(ctx, W / 2 + Math.sin(lt * .5) * 120, 620, 1100, [[0, 'rgba(167,139,250,.22)'], [1, 'rgba(22,15,38,0)']]);
  dust(env, ctx, lt + 2, { n: 26, color: '#CDBBFF', alpha: .28, min: 2, max: 7, seed: 31 });
}
// rubber stamp with ink texture, slams with a shake and splatter
function stamp(env, ctx, lines, x, y, lt, o = {}) {
  if (lt < 0) return;
  const tex = env.memo('ink', () => { const c = new OffscreenCanvas(900, 600), g = c.getContext('2d'), r = rng(42); for (let k = 0; k < 1400; k++) { g.fillStyle = `rgba(0,0,0,${r() * .5})`; g.beginPath(); g.arc(r() * 900, r() * 600, r() * 4 + .5, 0, 7); g.fill(); } return c; });
  const p = prog(lt, 0, .2), sc = lerp(2.4, 1, E.inQuad(p)), col = o.color || TICKET;
  const lay = env.memo('stamp:' + lines.join('|'), () => {
    const c = new OffscreenCanvas(900, 600), g = c.getContext('2d');
    g.strokeStyle = col; g.lineWidth = 14; g.beginPath(); g.roundRect(30, 60, 840, 480, 40); g.stroke();
    g.lineWidth = 5; g.beginPath(); g.roundRect(58, 88, 784, 424, 28); g.stroke();
    g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle';
    lines.forEach((ln, k) => { g.font = `400 ${k === lines.length - 1 ? 190 : 120}px "Anton"`; g.fillText(ln, 450, 210 + k * (lines.length === 2 ? 190 : 140)); });
    g.globalCompositeOperation = 'destination-out'; g.drawImage(tex, 0, 0); return c;
  });
  ctx.save(); ctx.translate(x, y); ctx.rotate(-.13); ctx.scale(sc, sc); ctx.globalAlpha = clamp(p * 3);
  ctx.shadowColor = rgba(col, .6); ctx.shadowBlur = 30 * (lt > .2 ? 1 : 0);
  ctx.drawImage(lay, -450, -300); ctx.restore(); ctx.globalAlpha = 1;
  if (lt > .2) {
    const r = rng(7), d = lt - .2;
    ctx.save(); ctx.fillStyle = col;
    for (let k = 0; k < 26; k++) { const a = r() * 6.28, sp = 300 + r() * 700, dist = sp * E.outExpo(clamp(d / .5)), s = (2 + r() * 9) * (1 - clamp(d / 1.2)); if (s <= 0) continue; ctx.globalAlpha = .85; ctx.beginPath(); ctx.arc(x + Math.cos(a) * (360 + dist * .4), y + Math.sin(a) * (240 + dist * .3), s, 0, 7); ctx.fill(); }
    ctx.restore(); ctx.globalAlpha = 1;
  }
}

const KINDS = {
  title(env, s, i, T) {
    const hit = s.slam_at ?? .12;
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [hit + .4], 12);
      ctx.save(); ctx.translate(sx, sy);
      violetBg(env, ctx, s.image, lt, { fx: s.fx, fy: s.fy, dim: .02, zoom: 1.08 });
      grad(ctx, 0, H * .52, 0, H, [[0, 'rgba(22,15,38,0)'], [.5, 'rgba(22,15,38,.85)'], [1, DEEP]], [0, H * .52, W, H * .48]);
      const f = fitSize(env, ctx, s.film, 'Anton', 400, 960, 260, 100);
      slam(ctx, s.film, W / 2, 1250, lt - hit, { size: f, family: 'Anton', weight: 400, color: TICKET, glow: rgba(TICKET, .5), glowBlur: 50 });
      ctx.save(); ctx.translate(W / 2, 1400); ctx.rotate(-.04);
      const p = ep(lt, hit + .4, hit + .62, E.inQuad);
      if (p > 0) { ctx.scale(lerp(2, 1, p), lerp(2, 1, p)); ctx.globalAlpha = clamp(p * 3);
        setFont(ctx, 104, 'Anton', 400, .04); const w = ctx.measureText(s.type).width + 70;
        rrect(ctx, -w / 2, -76, w, 132, 14); ctx.fillStyle = VIO; ctx.fill();
        txt(ctx, s.type, 0, 36, { size: 104, family: 'Anton', weight: 400, color: DEEP, ls: .04 }); }
      ctx.restore(); ctx.globalAlpha = 1;
      ring(ctx, W / 2, 1400, lt - hit - .62, { color: VIO, r1: 700 });
      sweep(ctx, lt, .9, 1.0, { alpha: .18 });
      ctx.restore();
    };
  },
  stamp(env, s, i, T) {
    const land = (s.land ?? .5);
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [land + .2], 22);
      ctx.save(); ctx.translate(sx, sy);
      violetBg(env, ctx, s.image, lt, { fx: s.fx, dim: .7 });
      wordsIn(ctx, s.heading, W / 2, 470, lt - .05, { size: 64, weight: 900, ls: .2, color: rgba(CREAM, .9), stagger: .1 });
      stamp(env, ctx, s.lines, W / 2, 900, lt - land, { color: TICKET });
      flash(ctx, lt, land + .2, { alpha: .25, color: TICKET });
      if (s.sub) pill(ctx, s.sub, W / 2, 1330, lt - land - .55, { size: 40, bg: CREAM, color: DEEP, ls: .08 });
      mascot(ctx, 880, 1480, .7, t, ep(lt, land + .8, land + 1.3, E.outBack));
      ctx.restore();
    };
  },
  scale(env, s, i, T) {
    const items = [...s.works.map((w, k) => ({ text: w, side: -1, k })), ...s.not.map((w, k) => ({ text: w, side: 1, k }))];
    const drop = it => .5 + (it.side < 0 ? it.k * .45 : s.works.length * .45 + it.k * .45);
    return (ctx, lt, t) => {
      violetBg(env, ctx, s.image, lt, { fx: s.fx, dim: .78 });
      const cx = W / 2, py = 760;
      let wl = 0, wr = 0; for (const it of items) { const d = lt - drop(it); if (d > .35) { if (it.side < 0) wl++; else wr++; } }
      const target = clamp((wr - wl) * .09, -.32, .32), bal = target + Math.sin(lt * 6) * .02 * Math.exp(-((lt % 1.2)) * 2);
      const ang = bal;
      ctx.save(); ctx.translate(cx, py);
      ctx.fillStyle = CREAM; ctx.beginPath(); ctx.moveTo(0, -20); ctx.lineTo(-40, 50); ctx.lineTo(40, 50); ctx.closePath(); ctx.fill();
      ctx.fillRect(-8, 50, 16, 560); ctx.fillRect(-120, 600, 240, 16);
      ctx.rotate(ang); ctx.fillStyle = CREAM; rrect(ctx, -360, -14, 720, 28, 14); ctx.fill();
      ctx.restore();
      [-1, 1].forEach(side => {
        const ex = cx + Math.cos(ang) * 330 * side, ey = py + Math.sin(ang) * 330 * side;
        ctx.strokeStyle = rgba(CREAM, .7); ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(ex, ey); ctx.lineTo(ex - 150, ey + 150); ctx.moveTo(ex, ey); ctx.lineTo(ex + 150, ey + 150); ctx.stroke();
        ctx.fillStyle = side < 0 ? rgba(GOOD, .22) : rgba(BAD, .22); ctx.strokeStyle = side < 0 ? GOOD : BAD; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(ex - 190, ey + 150); ctx.quadraticCurveTo(ex, ey + 250, ex + 190, ey + 150); ctx.closePath(); ctx.fill(); ctx.stroke();
        txt(ctx, side < 0 ? s.works_label : s.not_label, ex, ey + 320, { size: 56, family: 'Anton', weight: 400, color: side < 0 ? GOOD : BAD, alpha: ep(lt, .1, .5) });
        const mine = items.filter(it => it.side === side);
        mine.forEach((it, j) => {
          const d = lt - drop(it); if (d < 0) return;
          const fall = E.outBackBig(clamp(d / .45)), ty = ey + 120 - j * 74, y = lerp(260, ty, fall);
          pill(ctx, it.text, ex, y, d, { size: 32, bg: side < 0 ? GOOD : BAD, color: side < 0 ? DEEP : '#fff', d: .25 });
        });
      });
      if (s.footer) wordsIn(ctx, s.footer, W / 2, 1500, lt - (drop(items[items.length - 1]) + .6), { size: 50, family: 'Anton', weight: 400, color: CREAM, stagger: .07 });
    };
  },
  // STARS (Harish, 22 Nov): the rating out of 5 and the straight answer. Fields: heading, score (the plan check's number),
  // out_of (5), verdict (GO | WAIT | SKIP), line (WATCH IT IN THEATRES...), basis (e.g. "5 TRUSTED CRITICS"), land (s).
  stars(env, s, i, T) {
    const score = Number(s.score) || 0, out = s.out_of || 5, land = s.land ?? 1.9, word = String(s.verdict || ''), fillEnd = 1.5;
    const col = { GO: GOOD, WAIT: TICKET, SKIP: BAD }[word] || TICKET;
    const star = (ctx, cx, cy, r) => { ctx.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * .45 : r; ctx.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); } ctx.closePath(); };
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [land + .2], 16);
      ctx.save(); ctx.translate(sx, sy);
      violetBg(env, ctx, s.image, lt, { fx: s.fx, dim: .8 });
      wordsIn(ctx, s.heading || 'THE RATING', W / 2, 400, lt - .05, { size: 70, family: 'Anton', weight: 400, color: CREAM, stagger: .08 });
      const v = score * ep(lt, .35, fillEnd, E.inOutCubic), r = 78, gap = 178, y0 = 640;
      for (let k = 0; k < out; k++) {
        const cx = W / 2 + (k - (out - 1) / 2) * gap, pop = ep(lt, .1 + k * .07, .45 + k * .07, E.outBack);
        ctx.save(); ctx.translate(cx, y0); ctx.scale(pop, pop); ctx.translate(-cx, -y0);
        star(ctx, cx, y0, r); ctx.fillStyle = 'rgba(243,238,255,.10)'; ctx.fill(); ctx.lineWidth = 5; ctx.strokeStyle = rgba(CREAM, .55); ctx.stroke();
        const f = clamp(v - k);
        if (f > 0) { ctx.save(); ctx.beginPath(); ctx.rect(cx - r, y0 - r, 2 * r * f, 2 * r); ctx.clip(); star(ctx, cx, y0, r);
          ctx.shadowColor = rgba(TICKET, .7); ctx.shadowBlur = 30; ctx.fillStyle = TICKET; ctx.fill(); ctx.restore(); }
        ctx.restore();
      }
      const shown = (Math.round(v * 10) / 10).toFixed(1), pn = ep(lt, .3, .6);
      if (pn > 0) {
        const w = txt(ctx, shown, W / 2 - 20, 960, { size: 230, family: 'Anton', weight: 400, color: '#fff', glow: rgba(TICKET, .5), glowBlur: 40, alpha: pn, align: 'right' });
        txt(ctx, '/' + out, W / 2 - 4, 960, { size: 96, family: 'Anton', weight: 400, color: rgba(CREAM, .8), alpha: pn, align: 'left' });
      }
      if (s.basis) pill(ctx, s.basis, W / 2, 1050, lt - fillEnd, { size: 32, bg: CREAM, color: DEEP, ls: .1 });
      if (word) { ctx.save(); ctx.translate(W / 2, 1300); ctx.scale(.62, .62); stamp(env, ctx, ['VERDICT', word], 0, 0, lt - land, { color: col }); ctx.restore(); }
      flash(ctx, lt, land + .2, { alpha: .2, color: col });
      if (s.line) pill(ctx, s.line, W / 2, 1500, lt - land - .5, { size: 40, bg: col, color: DEEP, ls: .08 });
      ctx.restore();
    };
  },
  critics(env, s, i, T) {
    const n = s.cards.length, per = (T.end - T.start - .6) / n;
    return (ctx, lt, t) => {
      violetBg(env, ctx, s.image, lt, { fx: s.fx, dim: .8 });
      wordsIn(ctx, s.heading, W / 2, 400, lt - .05, { size: 76, family: 'Anton', weight: 400, color: CREAM, stagger: .08 });
      s.cards.forEach((c, k) => {
        const st = .25 + k * per, p = ep(lt, st, st + .45, E.outBack); if (p <= 0) return;
        const y = 600 + k * 235, side = k % 2 ? 1 : -1, active = lt < st + per || k === n - 1;
        ctx.save(); ctx.translate(W / 2 + (1 - p) * side * 900, y); ctx.rotate(side * .012);
        ctx.globalAlpha = active ? 1 : .6;
        rrect(ctx, -470, -95, 940, 200, 22); ctx.fillStyle = 'rgba(243,238,255,.96)'; ctx.fill();
        ctx.fillStyle = VIO; ctx.fillRect(-470, -95, 14, 200);
        txt(ctx, c.outlet, -430, -38, { size: 34, weight: 900, ls: .08, color: '#3B2A6B', align: 'left' });
        txt(ctx, c.critic, -430, -2, { size: 26, weight: 600, color: '#6B5A9B', align: 'left' });
        const qs = fitSize(env, ctx, '“' + c.quote + '”', 'Playfair Display', 800, c.rating ? 680 : 860, 54, 30, 0);
        txt(ctx, '“' + c.quote + '”', -430, 70, { size: qs, family: 'Playfair Display', weight: 800, italic: true, color: DEEP, align: 'left' });
        if (c.rating) { rrect(ctx, 300, -60, 140, 76, 38); ctx.fillStyle = TICKET; ctx.fill(); txt(ctx, c.rating, 370, -8, { size: 40, family: 'Anton', weight: 400, color: DEEP }); }
        ctx.restore(); ctx.globalAlpha = 1;
      });
    };
  },
  who(env, s, i, T) {
    return (ctx, lt, t) => {
      violetBg(env, ctx, s.image, lt, { fx: s.fx, fy: s.fy, dim: .35, zoom: 1.1 });
      grad(ctx, 0, 700, 0, H, [[0, 'rgba(22,15,38,0)'], [.45, 'rgba(22,15,38,.92)'], [1, DEEP]], [0, 700, W, H - 700]);
      wordsIn(ctx, s.heading, W / 2, 1150, lt - .05, { size: 84, family: 'Anton', weight: 400, color: CREAM, stagger: .07 });
      s.chips.forEach((row, k) => chipsRow(ctx, row, W / 2, 1290 + k * 100, lt - .5 - k * .3, { size: 40, bg: k ? VIO : TICKET, color: DEEP, stagger: .14 }));
      sweep(ctx, lt, .3, 1.1, { alpha: .14 });
    };
  },
  end(env, s, i, T) {
    return (ctx, lt, t) => {
      violetBg(env, ctx, s.bg, lt, { dim: .82 });
      endCard(env, ctx, lt, t, { echo: s.echo, question: s.question, cta: s.cta, sub: s.sub, accent: TICKET });
    };
  },
};

export async function build(env, plan, tl) {
  const screens = plan.screens.map((s, i) => {
    const T = tl.screens[i];
    return { start: T.start, end: T.end, tin: s.in ? { type: s.in, d: s.in_d || .36 } : null, draw: KINDS[s.kind](env, s, i, T) };
  });
  return { screens, post: (ctx) => { vignette(env, ctx, .7); grain(env, ctx, .075); } };
}
