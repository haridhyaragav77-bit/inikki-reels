// BULLETIN — Movie Updates look (AGENT.md 6.6): the film's still edge to edge, big numbers, bold type,
// no small floating card. Often music-only: numbers and stills tell the story. Teal series colour, yellow numbers.
import { W, H, clamp, lerp, prog, ep, E, rng, cue, beatPulse, nearestBeat, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, rgba, filtered } from '../_shared/runtime.js';
import { endCard, chipsRow } from '../_shared/motion.js';

const TEAL = '#78E0D0', YEL = '#F8C028', NAVY = '#0A0F18';

// edge-to-edge still with a moving colour wash and diagonal light bands
function fullStill(env, ctx, img, lt, o = {}) {
  fill(ctx, NAVY);
  cover(ctx, img, 0, 0, W, H, { zoom: (o.zoom || 1.08) + .07 * ep(lt, 0, o.dur || 5, E.linear), fx: o.fx ?? .5, fy: o.fy ?? .5, px: Math.sin(lt * .5) * .01 });
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = o.wash || 'rgba(20,60,72,.55)'; ctx.fillRect(0, 0, W, H); ctx.restore();
  grad(ctx, 0, 0, 0, H, [[0, 'rgba(10,15,24,.85)'], [.28, 'rgba(10,15,24,0)'], [.55, 'rgba(10,15,24,.15)'], [1, 'rgba(10,15,24,.96)']]);
  bands(ctx, lt);
}
function bands(ctx, lt) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.rotate(-.5);
  for (let k = 0; k < 5; k++) {
    const x = ((k * 520 + lt * 160) % 2600) - 900;
    ctx.fillStyle = `rgba(120,224,208,${.035 + .02 * (k % 2)})`; ctx.fillRect(x, -400, 70 + 40 * (k % 3), 3200);
  }
  ctx.restore();
}
// still on the top part, a slanted edge, a solid panel below for big type
function splitStill(env, ctx, img, lt, o = {}) {
  fill(ctx, NAVY);
  radial(ctx, W / 2, H * .82, 900, [[0, 'rgba(120,224,208,.14)'], [1, 'rgba(10,15,24,0)']]);
  const edge = o.edge ?? 1060, slant = 120, rise = (1 - ep(lt, 0, .55, E.outCubic)) * 260;
  ctx.save(); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W, 0); ctx.lineTo(W, edge - slant + rise); ctx.lineTo(0, edge + slant + rise); ctx.closePath(); ctx.clip();
  cover(ctx, img, 0, 0, W, edge + slant + 40, { zoom: 1.06 + .08 * ep(lt, 0, o.dur || 5, E.linear), fx: o.fx ?? .5, fy: o.fy ?? .45, px: Math.sin(lt * .6) * .012 });
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = 'rgba(30,70,80,.35)'; ctx.fillRect(0, 0, W, H); ctx.restore();
  grad(ctx, 0, 0, 0, 520, [[0, 'rgba(10,15,24,.85)'], [1, 'rgba(10,15,24,0)']], [0, 0, W, 520]);
  ctx.restore();
  ctx.save(); ctx.strokeStyle = TEAL; ctx.lineWidth = 8; ctx.shadowColor = TEAL; ctx.shadowBlur = 25;
  ctx.beginPath(); ctx.moveTo(0, edge + slant + rise); ctx.lineTo(W, edge - slant + rise); ctx.stroke(); ctx.restore();
  bands(ctx, lt);
  dust(env, ctx, lt + 3, { n: 26, color: TEAL, alpha: .25, min: 2, max: 6, seed: 4 });
}
function money(ctx, value, lt, d, x, y, o = {}) {
  const p = E.outExpo(prog(lt, 0, d)), v = value * p, dec = o.decimals || 0;
  const num = v.toFixed(dec), big = o.size || 300;
  // the ₹ sign only for money (Harish, 19 Nov: a date showed "₹20 NOV"): crore, lakh, thousand, million, or money: true
  const unit = o.unit ?? ' CR', isMoney = o.money ?? /^\s*(CR|CRORE|CRORES|L|LAKH|LAKHS|K|M|MN|B|BN)\b\+?/i.test(unit);
  const parts = [...(isMoney ? [['₹', big * .62, YEL]] : []), [num, big, o.color || '#fff'], [unit, big * .42, YEL]];
  let total = 0; const ws = parts.map(([s, z]) => { setFont(ctx, z, 'Anton', 400, 0); const w = ctx.measureText(s).width; total += w; return w; });
  let cx = x - total / 2;
  parts.forEach(([s, z, c], k) => { txt(ctx, s, cx + ws[k] / 2, y, { size: z, family: 'Anton', weight: 400, color: c, glow: k === 1 ? rgba(YEL, .35 + .3 * (lt > d ? 1 : 0)) : null, glowBlur: 50 }); cx += ws[k]; });
  return p;
}

const KINDS = {
  title(env, s, i, T) {
    const img = env.img[s.image], hit = s.slam_at ?? .1;
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [hit, hit + .35], 12);
      ctx.save(); ctx.translate(sx, sy);
      if (s.band) {
        const bg = env.memo('blur:' + s.image, () => filtered(img, 'blur(16px) brightness(.55) saturate(1.2)', .5));
        fill(ctx, NAVY); cover(ctx, bg, 0, 0, W, H, { zoom: 1.3 + .05 * Math.sin(lt * .5), fx: s.fx });
        const ent = ep(lt, 0, .5, E.outCubic);
        cover(ctx, img, 0, s.band[0] + (1 - ent) * 80, W, s.band[1], { zoom: 1.04 + .06 * ep(lt, 0, T.end - T.start, E.linear), fx: s.fx ?? .5, fy: s.fy ?? .5 });
        grad(ctx, 0, s.band[0], 0, s.band[0] + 200, [[0, 'rgba(10,15,24,.9)'], [1, 'rgba(10,15,24,0)']], [0, s.band[0], W, 200]);
        grad(ctx, 0, s.band[0] + s.band[1] - 260, 0, s.band[0] + s.band[1], [[0, 'rgba(10,15,24,0)'], [1, 'rgba(10,15,24,1)']], [0, s.band[0] + s.band[1] - 260, W, 262]);
        grad(ctx, 0, s.band[0] + s.band[1], 0, H, [[0, 'rgba(10,15,24,1)'], [1, 'rgba(10,15,24,.92)']], [0, s.band[0] + s.band[1] - 1, W, H]);
        bands(ctx, lt);
      } else fullStill(env, ctx, img, lt, { fx: s.fx, fy: s.fy, zoom: 1.12, dur: T.end - T.start });
      flash(ctx, lt, hit, { alpha: .45 });
      s.lines.forEach((ln, k) => {
        const size = fitSize(env, ctx, ln.text, 'Anton', 400, 980, ln.size, 80);
        slam(ctx, ln.text, W / 2, ln.y, lt - hit - k * .35, { size, family: 'Anton', weight: 400, color: ln.color || '#fff', glow: ln.glow, glowBlur: 45, from: 2.3 });
      });
      ring(ctx, W / 2, s.lines[0].y - 90, lt - hit, { color: TEAL, r1: 800, w: 16 });
      streak(ctx, W / 2, s.lines[s.lines.length - 1].y + 30, lt - hit - .4, { color: 'rgba(120,224,208,1)', len: 1000 });
      sweep(ctx, lt, .9, 1.1, { alpha: .2 });
      ctx.restore();
    };
  },
  number(env, s, i, T) {
    const img = env.img[s.image];
    const land = nearestBeat(env, T.start + (s.land ?? 1.6)) - T.start;
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [land], 14);
      ctx.save(); ctx.translate(sx, sy);
      splitStill(env, ctx, img, lt, { fx: s.fx, fy: s.fy, dur: T.end - T.start, edge: 980 });
      pill(ctx, s.kicker, W / 2, 1065, lt - .2, { size: 38, bg: TEAL, color: NAVY, ls: .1 });
      const bp = 1 + beatPulse(env, t, 6) * .03 * (lt > land ? 1 : 0);
      ctx.save(); ctx.translate(W / 2, 1400); ctx.scale(bp, bp);
      money(ctx, s.value, lt - .3, land - .3, 0, 0, { size: 300, unit: s.unit, money: s.money });
      ctx.restore();
      ring(ctx, W / 2, 1300, lt - land, { color: YEL, r1: 820, w: 18 });
      flash(ctx, lt, land, { alpha: .3, color: '#F8C028' });
      sweep(ctx, lt, land + .1, .9, { alpha: .28, width: 200 });
      if (s.tag) chipsRow(ctx, s.tag, W / 2, 1500, lt - land - .25, { size: 30, bg: 'rgba(255,255,255,.12)', color: '#fff', border: 'rgba(255,255,255,.35)', stagger: .12 });
      ctx.restore();
    };
  },
  bars(env, s, i, T) {
    const img = env.img[s.image], max = Math.max(...s.items.map(b => b.value));
    return (ctx, lt, t) => {
      splitStill(env, ctx, img, lt, { fx: s.fx, fy: s.fy, dur: T.end - T.start, edge: 860 });
      pill(ctx, s.kicker, W / 2, 1010, lt - .15, { size: 38, bg: TEAL, color: NAVY, ls: .1 });
      s.items.forEach((b, k) => {
        const y = 1150 + k * 190, st = .35 + k * .35, p = E.outExpo(prog(lt, st, st + 1.2)), w = 860 * b.value / max * p;
        if (lt < st) return;
        txt(ctx, b.label, 110, y - 26, { size: 40, weight: 900, ls: .12, color: rgba('#ffffff', clamp((lt - st) * 4)), align: 'left' });
        rrect(ctx, 110, y, 860, 70, 35); ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fill();
        ctx.save(); ctx.shadowColor = b.color || YEL; ctx.shadowBlur = 30 + 20 * beatPulse(env, t);
        rrect(ctx, 110, y, Math.max(70, w), 70, 35); ctx.fillStyle = b.color || YEL; ctx.fill(); ctx.restore();
        txt(ctx, '₹' + (b.value * p).toFixed(b.decimals || 0) + ' CR', 110 + Math.max(70, w) - 24, y + 52, { size: 46, family: 'Anton', weight: 400, color: NAVY, align: 'right' });
        sweep(ctx, lt, st + 1.1, .7, { alpha: .18, width: 120 });
      });
      if (s.note) txt(ctx, s.note, W / 2, 1520, { size: 28, weight: 700, color: rgba('#ffffff', .6 * ep(lt, 1.6, 2.2)) });
    };
  },
  ladder(env, s, i, T) {
    const img = env.img[s.image];
    const stops = s.stops.map(st => ({ ...st, t: nearestBeat(env, T.start + st.at) - T.start }));
    return (ctx, lt, t) => {
      fill(ctx, NAVY);
      radial(ctx, W * .3, H * .6, 1000, [[0, 'rgba(120,224,208,.16)'], [1, 'rgba(10,15,24,0)']]);
      bands(ctx, lt);
      const ent = ep(lt, 0, .6, E.outBack);
      framed(ctx, img, 760 + (1 - ent) * 400, 760, 560, 760, { rot: .05 + Math.sin(lt * .7) * .012, zoom: 1.1 + .08 * ep(lt, 0, 5, E.linear), fx: s.fx ?? .5, fy: s.fy ?? .4, edge: rgba(TEAL, .7) });
      wordsIn(ctx, s.heading, 70, 420, lt - .1, { size: 76, family: 'Anton', weight: 400, color: '#fff', align: 'left', stagger: .08 });
      const x = 290, y0 = 1460, y1 = 560, top = s.max;
      ctx.strokeStyle = 'rgba(255,255,255,.25)'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x, y0 - (y0 - y1) * ep(lt, .1, .7)); ctx.stroke();
      for (let v = s.step; v <= top; v += s.step) {
        const y = y0 - (y0 - y1) * v / top; const hitStop = stops.find(st => st.value === v), lit = hitStop && lt >= hitStop.t;
        ctx.fillStyle = lit ? YEL : 'rgba(255,255,255,.3)'; ctx.fillRect(x - 60, y - 4, 120, 8);
        txt(ctx, `₹${v} CR`, x - 80, y + 14, { size: 40, family: 'Anton', weight: 400, color: lit ? YEL : 'rgba(255,255,255,.45)', align: 'right' });
        if (hitStop) {
          ring(ctx, x, y, lt - hitStop.t, { color: YEL, r0: 30, r1: 260, w: 10 });
          pill(ctx, hitStop.label, x + 210, y, lt - hitStop.t - .05, { size: 34, bg: YEL, color: NAVY });
        }
      }
      let v = 0;
      for (let k = 0; k < stops.length; k++) { const st0 = k ? stops[k - 1].t : .35, from = k ? stops[k - 1].value : 0; if (lt >= st0) v = lerp(from, stops[k].value, E.inOutCubic(prog(lt, st0, stops[k].t))); }
      const ty = y0 - (y0 - y1) * v / top;
      ctx.save(); ctx.shadowColor = YEL; ctx.shadowBlur = 40 + 30 * beatPulse(env, t);
      ctx.beginPath(); ctx.arc(x, ty, 34, 0, 7); ctx.fillStyle = YEL; ctx.fill(); ctx.restore();
      txt(ctx, '₹', x, ty + 15, { size: 42, family: 'Anton', weight: 400, color: NAVY });
      if (s.footer) wordsIn(ctx, s.footer, W / 2, 1520, lt - (stops[stops.length - 1].t + .5), { size: 44, weight: 900, color: '#fff', stagger: .06 });
    };
  },
  end(env, s, i, T) {
    const bg = env.memo('blur:' + s.bg, () => filtered(env.img[s.bg], 'blur(12px) brightness(.5)', .5));
    return (ctx, lt, t) => {
      fill(ctx, NAVY); cover(ctx, bg, 0, 0, W, H, { zoom: 1.2 + .05 * Math.sin(lt * .6) });
      grad(ctx, 0, 0, 0, H, [[0, 'rgba(10,15,24,.85)'], [.5, 'rgba(10,15,24,.45)'], [1, 'rgba(10,15,24,.92)']]);
      bands(ctx, lt);
      endCard(env, ctx, lt, t, { echo: s.echo, question: s.question, cta: s.cta, sub: s.sub, accent: TEAL });
    };
  },
};

export async function build(env, plan, tl) {
  const screens = plan.screens.map((s, i) => {
    const T = tl.screens[i];
    return { start: T.start, end: T.end, tin: s.in ? { type: s.in, d: s.in_d || .34 } : null, draw: KINDS[s.kind](env, s, i, T) };
  });
  const lastStart = tl.screens[tl.screens.length - 1].start;
  return {
    screens,
    overlay: (ctx, t) => { if (t < lastStart && plan.dateline) pill(ctx, plan.dateline, W / 2, 300, t - .05, { size: 30, bg: 'rgba(10,15,24,.7)', color: TEAL, border: rgba(TEAL, .6), ls: .14 }); },
    post: (ctx) => { vignette(env, ctx, .6); grain(env, ctx, .07); },
  };
}
