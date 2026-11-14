// POSTER WALL — Watch This Next (movie recommendations) look (AGENT.md 6.6): one film per screen as a tall poster,
// its own still blurred behind it (never an empty background), big number, title, year / language / country, a short reason.
import { W, H, clamp, lerp, prog, ep, E, rng, cue, beatPulse, nearestBeat, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, rgba, filtered } from '../_shared/runtime.js';
import { endCard, chipsRow, mascot, handle } from '../_shared/motion.js';

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

// The plot in 2-3 short beats: the plan's own `plot_beats`, else the plot sentence cut at its commas and colons.
function beatsOf(s) {
  if (Array.isArray(s.plot_beats) && s.plot_beats.length) return s.plot_beats.slice(0, 3).map(x => String(x).toUpperCase());
  const raw = String(s.plot || '').replace(/[.!]+$/, '');
  if (!raw) return [];
  let parts = raw.split(/\s*[:;,—–]\s+|\s+(?:but|until|when|who|and then)\s+/i).map(x => x.trim()).filter(Boolean);
  if (parts.length < 2) { const w = raw.split(' '), h = Math.ceil(w.length / 2); parts = [w.slice(0, h).join(' '), w.slice(h).join(' ')].filter(Boolean); }
  return parts.slice(0, 3).map(x => x.toUpperCase());
}
// One line of words wrapped to a width; returns the lines.
function wrap(ctx, text, size, maxW, family = 'Inter', weight = 900) {
  setFont(ctx, size, family, weight, 0);
  const out = []; let cur = '';
  for (const w of String(text).split(' ')) {
    const t = cur ? cur + ' ' + w : w;
    if (ctx.measureText(t).width > maxW && cur) { out.push(cur); cur = w; } else cur = t;
  }
  if (cur) out.push(cur);
  return out;
}

const KINDS = {
  // THE HOOK FRAME. The eye rests on the middle of the screen, so the title lives there: a moving wall of the films'
  // posters above and below, a dark stage in the middle, a timely kicker, and two slammed lines that fill the width.
  title(env, s, i, T) {
    const keys = s.posters, hit = s.slam_at ?? .12, n = keys.length;
    const wall = [...keys, ...keys, ...keys, ...keys].slice(0, Math.max(8, n * 2));
    const hits = [hit, hit + .42];
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, hits, 16, 5);
      ctx.save(); ctx.translate(sx, sy);
      blurBg(env, ctx, keys[0], lt);
      // the poster wall: two tilted rows that drift against each other, so the frame is alive from the first frame
      const pw = 330, ph = 480, gap = 28, span = (pw + gap) * wall.length;
      [[430, -1, 0], [1500, 1, 2]].forEach(([y, dir, off], row) => {
        ctx.save(); ctx.translate(W / 2, y); ctx.rotate(-.07);
        const drift = (lt * 46 * dir + row * 190) % span;
        wall.forEach((k, j) => {
          const key = wall[(j + off) % wall.length];
          let x = ((j * (pw + gap) + drift) % span + span) % span - span / 2 + pw / 2;
          if (x < -W * .85 || x > W * .85) return;
          const p = ep(lt, .02 + (j % 5) * .05, .5 + (j % 5) * .05, E.outBack);
          poster(env, ctx, key, x, (1 - p) * (row ? 500 : -500), pw, ph, lt, { zoom: 1.08, fx: s.fx ? s.fx[keys.indexOf(key)] ?? .5 : .5 });
        });
        ctx.restore();
      });
      // the stage in the middle: dark, so the words carry
      grad(ctx, 0, 560, 0, 1400, [[0, 'rgba(6,10,20,0)'], [.2, 'rgba(6,10,20,.9)'], [.8, 'rgba(6,10,20,.9)'], [1, 'rgba(6,10,20,0)']], [0, 560, W, 840]);
      radial(ctx, W / 2, 980, 760, [[0, rgba(SKY, .16 + .08 * beatPulse(env, t))], [1, 'rgba(0,0,0,0)']]);
      dust(env, ctx, t, { n: 34, color: SKY, alpha: .35, min: 2, max: 9, seed: 3 });
      streak(ctx, W / 2, 778, lt - hit, { color: rgba(SKY, 1), len: 760, h: 3, d: 2.4, alpha: .7 });
      streak(ctx, W / 2, 1226, lt - hit - .42, { color: rgba(SKY, 1), len: 760, h: 3, d: 2.4, alpha: .7 });
      if (s.kicker) pill(ctx, String(s.kicker).toUpperCase(), W / 2, 716, lt - .04, { size: 40, bg: CREAM, color: INK, ls: .12, glow: rgba(CREAM, .5) });
      const s1 = fitSize(env, ctx, s.lines[0], 'Anton', 400, 990, 200, 84);
      const s2 = fitSize(env, ctx, s.lines[1], 'Anton', 400, 990, 230, 96);
      const mid = 985, y1 = mid - s2 * .1 - 22, y2 = y1 + s2 * .92 + 26;
      slam(ctx, s.lines[0], W / 2, y1, lt - hit, { size: s1, family: 'Anton', weight: 400, color: '#fff', from: 2.2, stroke: 'rgba(6,10,20,.9)', strokeW: 14 });
      slam(ctx, s.lines[1], W / 2, y2, lt - hit - .42, { size: s2, family: 'Anton', weight: 400, color: SKY, glow: rgba(SKY, .75), glowBlur: 60, from: 2.2 });
      ring(ctx, W / 2, mid, lt - hit, { color: '#fff', r0: 80, r1: 900, w: 14, alpha: .5 });
      ring(ctx, W / 2, mid, lt - hit - .42, { color: SKY, r0: 80, r1: 980, w: 22 });
      if (s.tag) pill(ctx, String(s.tag).toUpperCase(), W / 2, 1300, lt - hit - 1.0, { size: 36, bg: SKY, color: INK, ls: .1 });
      sweep(ctx, lt, .95, .9, { alpha: .2 });
      ctx.restore();
      flash(ctx, lt, hit, { alpha: .5, d: .22 }); flash(ctx, lt, hit + .42, { alpha: .35, d: .22, color: SKY });
    };
  },
  // ONE FILM: the card (poster, number, rating, title, reason, where to watch) lands fast; then, when the plan gives a
  // `plot`, the card lifts into a film strip and the story is told in 2-3 beats on a drawn thread (no spoilers).
  film(env, s, i, T) {
    const OTT = { NETFLIX: ['#E50914', '#fff'], 'PRIME VIDEO': ['#00A8E1', '#fff'], 'JIOHOTSTAR': ['#1F80E0', '#fff'], 'SONYLIV': ['#F5A623', INK], 'ZEE5': ['#8230C6', '#fff'] };
    const beats = beatsOf(s), len = T.end - T.start;
    const pa = beats.length ? (s.plot_at ?? Math.min(3.4, len * .46)) : 1e9;       // when the plot beat begins
    return (ctx, lt, t) => {
      blurBg(env, ctx, s.image, lt, { fx: s.fx });
      dust(env, ctx, t, { n: 24, color: CREAM, alpha: .22, min: 2, max: 7, seed: 8 + i });
      const m = ep(lt, pa, pa + .55, E.inOutCubic);                                // 0 = the card, 1 = the plot beat
      const ent = ep(lt, 0, .45, E.outBack), tilt = Math.sin(lt * .7) * .012 * (1 - m);
      const pw = lerp(880, 940, m), ph = lerp(940, 520, m), cx = W / 2, cy = lerp(760, 560, m);
      poster(env, ctx, s.image, cx, cy + (1 - ent) * 140, pw, ph, lt, { rot: tilt, scale: .92 + .08 * ent, fx: s.fx, fy: s.fy, zoom: (s.zoom || 1.06) + .1 * m });
      sweep(ctx, lt, .4, .9, { alpha: .16 });
      // number
      const np = ep(lt, .1, .45, E.outBack);
      ctx.save(); ctx.translate(cx - pw / 2 + 110, cy - ph / 2 + 110); ctx.scale(np, np);
      setFont(ctx, 140, 'Anton', 400, 0); ctx.lineWidth = 5; ctx.strokeStyle = SKY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.strokeText(s.num, 0, 8); ctx.fillStyle = rgba(SKY, .25 + .2 * beatPulse(env, t)); ctx.fillText(s.num, 0, 8);
      ctx.restore();
      // Letterboxd rating badge with a filling ring
      if (s.rating) {
        const bx = cx + pw / 2 - 150, by = cy - ph / 2 + 150, bp = ep(lt, .45, .8, E.outBack) * lerp(1, .78, m), fillp = E.outCubic(prog(lt, .55, 1.3));
        ctx.save(); ctx.translate(bx, by); ctx.scale(bp, bp);
        ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 30;
        ctx.beginPath(); ctx.arc(0, 0, 124, 0, 7); ctx.fillStyle = 'rgba(8,12,22,.94)'; ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
        ctx.lineWidth = 13; ctx.strokeStyle = 'rgba(255,255,255,.16)'; ctx.beginPath(); ctx.arc(0, 0, 106, 0, 7); ctx.stroke();
        ctx.strokeStyle = SKY; ctx.lineCap = 'round'; ctx.shadowColor = SKY; ctx.shadowBlur = 16 + 14 * beatPulse(env, t);
        ctx.beginPath(); ctx.arc(0, 0, 106, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (s.rating / 5) * fillp); ctx.stroke(); ctx.shadowBlur = 0;
        txt(ctx, (s.rating * fillp).toFixed(1), -14, 36, { size: 104, family: 'Anton', weight: 400, color: '#fff' });
        txt(ctx, '/5', 52, 36, { size: 36, family: 'Anton', weight: 400, color: rgba(CREAM, .85), align: 'left' });
        ctx.restore();
        if (m < .5) pill(ctx, 'LETTERBOXD', bx, by + 128, lt - .7, { size: 26, bg: SKY, color: INK, ls: .1, alpha: 1 - m * 2 });
      }
      // title + badges inside the poster (they stay with the picture when it lifts)
      const tsz = fitSize(env, ctx, s.title, 'Anton', 400, pw - 90, lerp(112, 92, m), 56);
      wordsIn(ctx, s.title, cx, cy + ph / 2 - lerp(190, 118, m), lt - .2, { size: tsz, family: 'Anton', weight: 400, color: '#fff', stagger: .05, rise: 40 });
      chipsRow(ctx, s.meta, cx, cy + ph / 2 - lerp(112, 50, m), lt - .45, { size: 30, bg: rgba(SKY, .95), color: INK, stagger: .08 });
      if (m < 1) txt(ctx, s.director, cx, cy + ph / 2 - 50, { size: 28, weight: 700, ls: .12, color: rgba(CREAM, .8 * ep(lt, .6, .9) * (1 - m)) });
      // the card's own words: proof and the reason (they give way to the plot)
      if (m < 1) {
        ctx.save(); ctx.globalAlpha = 1 - m; ctx.translate(0, -60 * m);
        if (s.proof) pill(ctx, '★ ' + s.proof, W / 2, 1290, lt - 1.05, { size: 34, bg: CREAM, color: INK, ls: .06, alpha: 1 - m });
        wordsIn(ctx, s.reason, W / 2, 1392, lt - .7, { size: fitSize(env, ctx, s.reason, 'Inter', 900, 960, 52, 34), weight: 900, color: CREAM, stagger: .06, rise: 34, alpha: 1 - m });
        ctx.restore();
      }
      // THE PLOT BEAT: a thread is drawn down the left, a node lights for each beat, the words rise beside it
      if (m > 0) {
        const pt = lt - pa - .3, x0 = 130, top = 905, step = beats.length > 2 ? 178 : 215, tw = 830;
        pill(ctx, s.plot_label || 'THE PLOT · NO SPOILERS', W / 2, 868 - 12, pt + .22, { size: 28, bg: 'rgba(8,12,22,.9)', color: SKY, border: rgba(SKY, .8), ls: .14 });
        const gap = (len - pa - .9) / Math.max(1, beats.length), yN = k => top + 90 + k * step;
        const drawn = clamp((pt) / Math.max(.4, gap * (beats.length - 1) + .3));
        ctx.save(); ctx.lineCap = 'round'; ctx.lineWidth = 6; ctx.strokeStyle = rgba(SKY, .25);
        ctx.beginPath(); ctx.moveTo(x0, yN(0)); ctx.lineTo(x0, yN(beats.length - 1)); ctx.stroke();
        ctx.strokeStyle = SKY; ctx.shadowColor = SKY; ctx.shadowBlur = 18;
        ctx.beginPath(); ctx.moveTo(x0, yN(0)); ctx.lineTo(x0, lerp(yN(0), yN(beats.length - 1), E.inOutQuad(drawn))); ctx.stroke(); ctx.restore();
        beats.forEach((b, k) => {
          const bt = pt - k * Math.min(gap, 1.05), p = ep(bt, 0, .4, E.outBack);
          if (p <= 0) return;
          const y = yN(k);
          ctx.save(); ctx.translate(x0, y); ctx.scale(p, p);
          ctx.beginPath(); ctx.arc(0, 0, 32, 0, 7); ctx.fillStyle = INK; ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = SKY; ctx.shadowColor = SKY; ctx.shadowBlur = 22; ctx.stroke();
          ctx.shadowBlur = 0; txt(ctx, String(k + 1), 0, 15, { size: 40, family: 'Anton', weight: 400, color: '#fff' });
          ctx.restore();
          ring(ctx, x0, y, bt, { color: SKY, r0: 20, r1: 150, w: 8, alpha: .7, d: .5 });
          const size = beats.length > 2 ? 58 : 66, rows = wrap(ctx, b, size, tw).slice(0, 2);
          rows.forEach((row, r) => wordsIn(ctx, row, x0 + 76, y + 20 + (r - (rows.length - 1) / 2) * (size + 8), bt - .05 - r * .12,
            { size, weight: 900, color: k === beats.length - 1 ? '#fff' : CREAM, align: 'left', stagger: .045, rise: 26, d: .32 }));
        });
      }
      if (s.watch) {
        const [bg, fg] = OTT[s.watch] || [SKY, INK], wp = 1 + beatPulse(env, t, 6) * .05 * (lt > 1.9 ? 1 : 0);
        ctx.save(); ctx.translate(W / 2, 1478); ctx.scale(wp, wp);
        pill(ctx, 'WATCH ON ' + s.watch, 0, 0, lt - 1.4, { size: 40, bg, color: fg, glow: rgba(bg, .8), ls: .08 });
        ctx.restore();
        ring(ctx, W / 2, 1478, lt - 1.45, { color: bg, r0: 50, r1: 420, w: 8, alpha: .5 });
      }
    };
  },
  recap(env, s, i, T) {
    return (ctx, lt, t) => {
      blurBg(env, ctx, s.items[0].image, lt);
      handle(env, ctx, lt - 1.3, W / 2, 1530, SKY, 40);
      wordsIn(ctx, s.heading, W / 2, 380, lt - .05, { size: 92, family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      s.items.forEach((it, k) => {
        const col = k % 2, row = Math.floor(k / 2), x = 300 + col * 480, y = 630 + row * 462;
        const p = ep(lt, .15 + k * .12, .75 + k * .12, E.outBack);
        if (p <= 0) return;
        poster(env, ctx, it.image, x, y + (1 - p) * 120, 330 * p, 330 * p, lt, { fx: it.fx, rot: (col ? .02 : -.02) + Math.sin(lt + k) * .01, zoom: 1.12 });
        txt(ctx, it.title, x, y + 210, { size: fitSize(env, ctx, it.title, 'Anton', 400, 400, 42, 26), family: 'Anton', weight: 400, color: '#fff', alpha: p });
        if (it.watch) pill(ctx, it.watch, x, y + 256, lt - .5 - k * .12, { size: 26, bg: it.watch === 'NETFLIX' ? '#E50914' : '#00A8E1', color: '#fff', ls: .08 });
      });
      const pt = 1.0, bp = 1 + beatPulse(env, t, 5) * .05;
      ctx.save(); ctx.translate(W / 2, 1432); ctx.scale(bp, bp);
      pill(ctx, s.cta, 0, 0, lt - pt, { size: 44, bg: SKY, color: INK, glow: rgba(SKY, .8), ls: .08 });
      ctx.restore();
      ring(ctx, W / 2, 1432, lt - pt, { color: SKY, r0: 60, r1: 440, w: 10, alpha: .6 });
      mascot(ctx, 135, 1405, .5, t, ep(lt, pt + .2, pt + .8, E.outBack));
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
