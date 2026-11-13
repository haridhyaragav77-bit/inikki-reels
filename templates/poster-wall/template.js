// POSTER WALL — Watch This Next (movie recommendations) look (AGENT.md 6.6): one film per screen as a tall poster,
// its own still blurred behind it (never an empty background), big number, title, year / language / country, a short reason.
import { W, H, clamp, lerp, prog, ep, E, rng, cue, beatPulse, nearestBeat, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, rgba, filtered } from '../_shared/runtime.js';
import { endCard, chipsRow, mascot } from '../_shared/motion.js';

const SKY = '#7CC4FA', INK = '#0B1220', CREAM = '#F4EFE6';

function blurBg(env, ctx, key, lt, o = {}) {
  const bg = env.memo('blur:' + key, () => filtered(env.img[key], 'blur(18px) brightness(.5) saturate(1.25)', .45));
  fill(ctx, INK); cover(ctx, bg, 0, 0, W, H, { zoom: 1.35 + .06 * Math.sin(lt * .4), fx: o.fx ?? .5 });
  grad(ctx, 0, 0, 0, H, [[0, 'rgba(11,18,32,.65)'], [.5, 'rgba(11,18,32,.2)'], [1, 'rgba(11,18,32,.85)']]);
}
function poster(env, ctx, key, cx, cy, w, h, lt, o = {}) {
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(o.rot || 0); ctx.scale(o.scale || 1, o.scale || 1);
  ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = 70; ctx.shadowOffsetY = 35;
  rrect(ctx, -w / 2, -h / 2, w, h, 26); ctx.fillStyle = '#000'; ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.save(); rrect(ctx, -w / 2, -h / 2, w, h, 26); ctx.clip();
  cover(ctx, env.img[key], -w / 2, -h / 2, w, h, { zoom: (o.zoom || 1.05) + .08 * ep(lt, 0, 6, E.linear), fx: o.fx ?? .5, fy: o.fy ?? .45, px: Math.sin(lt * .5) * .01 });
  grad(ctx, 0, -h / 2, 0, h / 2, [[0, 'rgba(0,0,0,0)'], [.5, 'rgba(0,0,0,.05)'], [1, 'rgba(0,0,0,.88)']], [-w / 2, -h / 2, w, h]);
  ctx.restore();
  rrect(ctx, -w / 2, -h / 2, w, h, 26); ctx.lineWidth = 3; ctx.strokeStyle = rgba(CREAM, .35); ctx.stroke();
  ctx.restore();
}

const KINDS = {
  title(env, s, i, T) {
    const keys = s.posters, hit = s.slam_at ?? .15;
    return (ctx, lt, t) => {
      blurBg(env, ctx, keys[0], lt);
      dust(env, ctx, t, { n: 30, color: SKY, alpha: .3, min: 2, max: 8, seed: 3 });
      const n = keys.length;
      keys.forEach((k, j) => {
        const st = .05 + j * .12, p = ep(lt, st, st + .7, E.outBack);
        const ang = (j - (n - 1) / 2) * .16 + Math.sin(lt * .8 + j) * .015;
        const x = W / 2 + (j - (n - 1) / 2) * 190, y = 930 + Math.abs(j - (n - 1) / 2) * 40 + (1 - p) * 900;
        poster(env, ctx, k, x, y, 420, 620, lt, { rot: ang, fx: s.fx ? s.fx[j] : .5, zoom: 1.1 });
      });
      const s1 = fitSize(env, ctx, s.lines[0], 'Anton', 400, 960, 120, 60);
      slam(ctx, s.lines[0], W / 2, 450, lt - hit, { size: s1, family: 'Anton', weight: 400, color: '#fff', from: 1.6 });
      const s2 = fitSize(env, ctx, s.lines[1], 'Anton', 400, 980, 170, 80);
      slam(ctx, s.lines[1], W / 2, 1470, lt - hit - .55, { size: s2, family: 'Anton', weight: 400, color: SKY, glow: rgba(SKY, .6), glowBlur: 45 });
      ring(ctx, W / 2, 1410, lt - hit - .55, { color: SKY, r1: 760 });
      sweep(ctx, lt, 1.1, 1.0, { alpha: .18 });
    };
  },
  film(env, s, i, T) {
    const dur = T.end - T.start;
    return (ctx, lt, t) => {
      blurBg(env, ctx, s.image, lt, { fx: s.fx });
      dust(env, ctx, t, { n: 24, color: CREAM, alpha: .22, min: 2, max: 7, seed: 8 + i });
      const ent = ep(lt, 0, .55, E.outBack), tilt = Math.sin(lt * .7) * .012;
      const pw = 900, ph = 1080, cx = W / 2, cy = 860;
      poster(env, ctx, s.image, cx, cy + (1 - ent) * 140, pw, ph, lt, { rot: tilt, scale: .92 + .08 * ent, fx: s.fx, fy: s.fy, zoom: s.zoom || 1.06 });
      sweep(ctx, lt, .5, 1.0, { alpha: .16 });
      // number
      const np = ep(lt, .15, .55, E.outBack);
      ctx.save(); ctx.translate(cx - pw / 2 + 120, cy - ph / 2 + 120); ctx.scale(np, np);
      setFont(ctx, 150, 'Anton', 400, 0); ctx.lineWidth = 5; ctx.strokeStyle = SKY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.strokeText(s.num, 0, 8); ctx.fillStyle = rgba(SKY, .25 + .2 * beatPulse(env, t)); ctx.fillText(s.num, 0, 8);
      ctx.restore();
      // title + badges inside the poster
      const tsz = fitSize(env, ctx, s.title, 'Anton', 400, pw - 90, 118, 60);
      wordsIn(ctx, s.title, cx, cy + ph / 2 - 200, lt - .3, { size: tsz, family: 'Anton', weight: 400, color: '#fff', stagger: .06, rise: 40 });
      chipsRow(ctx, s.meta, cx, cy + ph / 2 - 118, lt - .65, { size: 30, bg: rgba(SKY, .95), color: INK, stagger: .1 });
      txt(ctx, s.director, cx, cy + ph / 2 - 52, { size: 28, weight: 700, ls: .12, color: rgba(CREAM, .8 * ep(lt, .9, 1.3)) });
      // the reason, below the poster
      wordsIn(ctx, s.reason, W / 2, 1490, lt - 1.05, { size: fitSize(env, ctx, s.reason, 'Inter', 900, 960, 54, 34), weight: 900, color: CREAM, stagger: .07, rise: 34 });
      void dur;
    };
  },
  recap(env, s, i, T) {
    return (ctx, lt, t) => {
      blurBg(env, ctx, s.items[0].image, lt);
      wordsIn(ctx, s.heading, W / 2, 400, lt - .05, { size: 92, family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      s.items.forEach((it, k) => {
        const col = k % 2, row = Math.floor(k / 2), x = 300 + col * 480, y = 720 + row * 470;
        const p = ep(lt, .15 + k * .12, .75 + k * .12, E.outBack);
        if (p <= 0) return;
        poster(env, ctx, it.image, x, y + (1 - p) * 120, 420 * p, 420 * p, lt, { fx: it.fx, rot: (col ? .02 : -.02) + Math.sin(lt + k) * .01, zoom: 1.12 });
        txt(ctx, it.title, x, y + 170, { size: fitSize(env, ctx, it.title, 'Anton', 400, 390, 46, 26), family: 'Anton', weight: 400, color: '#fff', alpha: p });
      });
      const pt = 1.0, bp = 1 + beatPulse(env, t, 5) * .05;
      ctx.save(); ctx.translate(W / 2, 1430); ctx.scale(bp, bp);
      pill(ctx, s.cta, 0, 0, lt - pt, { size: 44, bg: SKY, color: INK, glow: rgba(SKY, .8), ls: .08 });
      ctx.restore();
      ring(ctx, W / 2, 1430, lt - pt, { color: SKY, r0: 60, r1: 440, w: 10, alpha: .6 });
      mascot(ctx, 900, 1530, .7, t, ep(lt, pt + .2, pt + .8, E.outBack));
    };
  },
};

export async function build(env, plan, tl) {
  const screens = plan.screens.map((s, i) => {
    const T = tl.screens[i];
    return { start: T.start, end: T.end, tin: s.in ? { type: s.in, d: s.in_d || .36 } : null, draw: KINDS[s.kind](env, s, i, T) };
  });
  return { screens, post: (ctx) => { vignette(env, ctx, .65); grain(env, ctx, .075); } };
}
