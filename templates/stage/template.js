// STAGE — Film Breakdown look (AGENT.md 6.6): deep black stage, spotlight, haze and dust;
// motion graphics lead and can take the whole screen. Gold accents, Anton titles, Tamil voice.
import { W, H, clamp, lerp, prog, ep, E, life, rng, cue, beatPulse, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, rgba, filtered } from '../_shared/runtime.js';
import { endCard, labelPin, shapePoints, assemble, subtitles, soundOn, handle } from '../_shared/motion.js';

// DESIGN KITS: every breakdown gets its own design, so no two reels in a row look alike (AGENT.md 5.8). A plan names
// one in "design"; without a name the reel id picks one. GOLD is the kit's main accent, TEAL its second colour.
const KITS = {
  spotlight: { a: '#F8C868', b: '#78E0D0', back: 'haze' },
  blueprint: { a: '#8FD3FF', b: '#F4F1E8', back: 'grid' },
  noir:      { a: '#FF6B5E', b: '#F2E6D0', back: 'blinds' },
  neon:      { a: '#FF5FD2', b: '#5CF2FF', back: 'scan' },
  paper:     { a: '#FFB04A', b: '#FFF3DC', back: 'dots' },
  forest:    { a: '#8BE38F', b: '#F8C868', back: 'shafts' },
  royal:     { a: '#B79CFF', b: '#FFD98A', back: 'rings' },
};
let GOLD = '#F8C868', TEAL = '#78E0D0', BACK = 'haze';
const INK = '#050608';
function useKit(plan) {
  const names = Object.keys(KITS);
  let h = 0; for (const c of String(plan.id || plan.reel_id || '')) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const k = KITS[plan.design] || KITS[names[h % names.length]];
  GOLD = k.a; TEAL = k.b; BACK = k.back;
}
// Instagram-safe layout for breakdowns: the action buttons sit on the right and the profile, caption and
// message bar at the bottom. Words and key visuals stay in the safe column; subtitles get their own band.
const CX = 490, MAXW = 840, SUB_Y = 1415;

function stage(env, ctx, t) {
  fill(ctx, INK);
  const sx = W / 2 + Math.sin(t * .35) * 150;
  radial(ctx, sx, -260, 1750, [[0, rgba(GOLD, .24)], [.5, rgba(GOLD, .05)], [1, 'rgba(0,0,0,0)']]);
  radial(ctx, W / 2, H + 260, 1000, [[0, rgba(TEAL, .10)], [1, 'rgba(0,0,0,0)']]);
  ctx.save();
  if (BACK === 'haze') {
    const hz = tint(env, GOLD); ctx.globalCompositeOperation = 'lighter';
    for (let k = 0; k < 4; k++) {
      const x = W / 2 + Math.sin(t * .21 + k * 1.7) * 430, y = 420 + k * 360 + Math.cos(t * .17 + k) * 90, z = 720;
      ctx.globalAlpha = .045; ctx.drawImage(hz, x - z, y - z, z * 2, z * 2);
    }
  } else if (BACK === 'grid') {                       // a drifting technical grid with a bright crosshair row
    const g = 90, off = (t * 14) % g; ctx.lineWidth = 1.5;
    for (let x = -g + off; x < W + g; x += g) { ctx.strokeStyle = rgba(GOLD, .07); ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = -g + off; y < H + g; y += g) { ctx.strokeStyle = rgba(GOLD, (Math.round((y - off) / g) % 4 === 0) ? .16 : .07); ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  } else if (BACK === 'blinds') {                     // light through window blinds, slowly sliding
    ctx.globalCompositeOperation = 'lighter'; ctx.translate(W / 2, H / 2); ctx.rotate(-.32);
    for (let k = -12; k < 12; k++) { const y = k * 150 + ((t * 18) % 150); ctx.fillStyle = rgba(GOLD, .035 + .02 * Math.sin(t * .6 + k)); ctx.fillRect(-W * 1.2, y, W * 2.4, 58); }
  } else if (BACK === 'scan') {                       // two neon beams crossing
    ctx.globalCompositeOperation = 'lighter';
    [[GOLD, .5, 1], [TEAL, -.42, -1]].forEach(([c, ang, dir], k) => {
      ctx.save(); ctx.translate(W / 2 + Math.sin(t * .3 + k * 2) * 380 * dir, H / 2); ctx.rotate(ang);
      const g = ctx.createLinearGradient(-220, 0, 220, 0); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.5, rgba(c, .1)); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(-220, -H * 1.2, 440, H * 2.4); ctx.restore();
    });
  } else if (BACK === 'dots') {                       // print dots that breathe from one corner
    for (let y = 40; y < H; y += 54) for (let x = 40 + ((y / 54) % 2) * 27; x < W; x += 54) {
      const d = Math.hypot(x - W, y) / 1900, r = Math.max(0, 9 * (1 - d) + 2 * Math.sin(t * .8 + x * .01 + y * .012));
      if (r > .6) { ctx.fillStyle = rgba(GOLD, .09); ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
    }
  } else if (BACK === 'shafts') {                     // tall shafts of light, like sun through trees
    ctx.globalCompositeOperation = 'lighter';
    for (let k = 0; k < 6; k++) {
      const x = 90 + k * 190 + Math.sin(t * .25 + k * 1.3) * 60, w = 70 + 40 * Math.sin(k * 2.1);
      const g = ctx.createLinearGradient(0, 0, 0, H * .85); g.addColorStop(0, rgba(k % 2 ? TEAL : GOLD, .1)); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.save(); ctx.transform(1, 0, -.18, 1, 0, 0); ctx.fillStyle = g; ctx.fillRect(x, 0, w, H * .85); ctx.restore();
    }
  } else if (BACK === 'rings') {                      // slow rings opening from below, like a stage floor
    ctx.lineWidth = 2;
    for (let k = 0; k < 7; k++) { const r = 180 + k * 190 + ((t * 26) % 190); ctx.strokeStyle = rgba(k % 2 ? GOLD : TEAL, .1 * (1 - r / 1600)); ctx.beginPath(); ctx.ellipse(W / 2, H * .82, r, r * .42, 0, 0, 7); ctx.stroke(); }
  }
  ctx.restore(); ctx.globalAlpha = 1;
  dust(env, ctx, t, { n: 38, color: rgba(GOLD, 1), alpha: .3, min: 2, max: 7, rise: 24, seed: 21 });
}
function fadeBand(ctx, y0, h, bottom = 320) {
  grad(ctx, 0, y0, 0, y0 + 280, [[0, INK], [1, 'rgba(5,6,8,0)']], [0, y0 - 2, W, 282]);
  grad(ctx, 0, y0 + h - bottom, 0, y0 + h, [[0, 'rgba(5,6,8,0)'], [1, INK]], [0, y0 + h - bottom, W, bottom + 2]);
}

// PART n/of: a film week's badge (plan.part = [n, of], AGENT.md 5.7), on the title and end screens
function partBadge(env, ctx, lt, y) {
  const pt = env.plan.part; if (!Array.isArray(pt) || lt < 0) return;
  pill(ctx, `PART ${pt[0]}/${pt[1]}`, CX, y, lt, { size: 34, bg: INK, color: GOLD, border: GOLD, ls: .18, family: 'Anton', weight: 400, glow: rgba(GOLD, .5) });
}

// ---------------------------------------------------------------- icons for the story loop
function icon(ctx, kind, s, col) {
  ctx.save(); ctx.scale(s, s); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 5; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  if (kind === 'story') {
    ctx.beginPath(); ctx.moveTo(-34, -18); ctx.quadraticCurveTo(-17, -26, 0, -16); ctx.lineTo(0, 24); ctx.quadraticCurveTo(-17, 15, -34, 22); ctx.closePath(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(34, -18); ctx.quadraticCurveTo(17, -26, 0, -16); ctx.lineTo(0, 24); ctx.quadraticCurveTo(17, 15, 34, 22); ctx.closePath(); ctx.stroke();
  } else if (kind === 'question') {
    txt(ctx, '?', 0, 26, { size: 76, family: 'Anton', weight: 400, color: col });
  } else if (kind === 'answer') {
    ctx.beginPath(); ctx.roundRect(-34, -26, 68, 44, 12); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-12, 18); ctx.lineTo(-20, 32); ctx.lineTo(2, 18); ctx.stroke();
    for (let k = -1; k <= 1; k++) { ctx.beginPath(); ctx.arc(k * 14, -4, 4.5, 0, 7); ctx.fill(); }
  } else if (kind === 'escape') {
    ctx.beginPath(); ctx.arc(0, -8, 26, Math.PI, 0); ctx.lineTo(26, 26);
    for (let k = 0; k < 4; k++) ctx.quadraticCurveTo(26 - 13 * k - 6.5, 16, 26 - 13 * (k + 1), 26);
    ctx.closePath(); ctx.stroke();
    ctx.beginPath(); ctx.arc(-9, -8, 4.5, 0, 7); ctx.arc(9, -8, 4.5, 0, 7); ctx.fill();
  }
  ctx.restore();
}

const KINDS = {
  // ------------------------------------------------------------ title screen: the film and what the reel is
  title(env, s, i, T) {
    const img = env.img[s.image], hit = s.slam_at ?? .12;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const [sx, sy] = shake(lt, [hit], 9);
      ctx.save(); ctx.translate(sx, sy);
      const bandY = 170, bandH = 830;
      ctx.globalAlpha = ep(lt, 0, .35);
      cover(ctx, img, 0, bandY, W, bandH, { zoom: 1.08 - .06 * ep(lt, 0, 5, E.outQuad), fx: s.fx ?? .5, fy: s.fy ?? .5, px: Math.sin(lt * .4) * .015 });
      ctx.globalAlpha = 1;
      fadeBand(ctx, bandY, bandH, 200);
      sweep(ctx, lt, .25, 1.3, { alpha: .16 });
      const size = fitSize(env, ctx, s.film, 'Anton', 400, MAXW, s.size || 180, 90, .01);
      slam(ctx, s.film, CX, 1140, lt - hit, { size, family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .6), glowBlur: 55, ls: .01 });
      ring(ctx, CX, 1080, lt - hit, { color: GOLD, r1: 760, w: 16 });
      streak(ctx, CX, 1077, lt - hit - .04, { len: 1050, h: 3 });
      const ts = fitSize(env, ctx, s.type, 'Inter', 900, MAXW - 20, 58, 34, .16);
      wordsIn(ctx, s.type, CX, 1236, lt - hit - .3, { size: ts, weight: 900, ls: .16, color: '#fff', stagger: .1 });
      const rl = ep(lt, hit + .65, hit + 1.15, E.inOutCubic);
      partBadge(env, ctx, lt - hit - .5, 945);
      ctx.fillStyle = GOLD; ctx.fillRect(CX - 230 * rl, 1274, 460 * rl, 5);
      ctx.restore();
      if (env.plan.voice && env.plan.voice.on) soundOn(ctx, lt, CX, 300, { until: T.end - T.start + .2, accent: GOLD });
    };
  },

  // ------------------------------------------------------------ a still with "who's who" pins and a big line
  pins(env, s, i, T) {
    const img = env.img[s.image];
    const cues = s.pins.map(p => cue(env, i, p.cue) - T.start), slamT = cue(env, i, s.slam.cue) - T.start;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const fw = 880, fh = 520, cx = CX, cy = 640, ent = ep(lt, 0, .7, E.outBack);
      const [sx, sy] = shake(lt, [slamT], 10);
      ctx.save(); ctx.translate(sx, sy);
      framed(ctx, img, cx, cy + (1 - ent) * 160, fw, fh, { scale: .88 + .12 * ent, rot: Math.sin(lt * .6) * .012, zoom: 1.05 + .07 * ep(lt, 0, 7, E.linear), fx: s.fx ?? .5, fy: s.fy ?? .5, edge: rgba(GOLD, .55) });
      s.pins.forEach((p, k) => labelPin(ctx, lt - cues[k], cx - fw / 2 + p.x * fw, cy - fh / 2 + p.y * fh, p.lx, p.ly, p.text, { color: k % 2 ? TEAL : GOLD, align: p.align, size: p.size || 38 }));
      if (s.extra) {
        const xt = cue(env, i, s.extra.cue) - T.start, inn = ep(lt, xt, xt + .35, E.outBack), out = ep(lt, slamT - .25, slamT + .15, E.inCubic);
        if (inn > 0 && out < 1) {
          ctx.save(); ctx.globalAlpha = 1 - out;
          framed(ctx, env.img[s.extra.image], CX + 70 + (1 - inn) * 260, 1135 + out * 240, 620, 350, { rot: .045 + Math.sin(lt) * .01, zoom: 1.08 + .06 * ep(lt, xt, xt + 4, E.linear), fx: s.extra.fx ?? .5, edge: rgba(TEAL, .6) });
          pill(ctx, s.extra.label, 280, 975, lt - xt - .25, { size: 36, bg: TEAL, color: '#0A0F18', ls: .08 });
          ctx.restore(); ctx.globalAlpha = 1;
        }
      }
      s.slam.lines.forEach((ln, k) => slam(ctx, ln.text, CX, 1105 + k * 158, lt - slamT - k * .2, { size: Math.min(ln.size || 150, fitSize(env, ctx, ln.text, 'Anton', 400, MAXW, ln.size || 150, 60)), family: 'Anton', weight: 400, color: ln.color || '#fff', glow: ln.glow, glowBlur: 45 }));
      ring(ctx, CX, 1150, lt - slamT - .2, { color: GOLD, r1: 640 });
      ctx.restore();
    };
  },

  // ------------------------------------------------------------ THE TECHNIQUE: name it, define it, show it (the pin)
  technique(env, s, i, T) {
    const cn = cue(env, i, s.cues.name) - T.start, co = cue(env, i, s.cues.outer) - T.start, ci = cue(env, i, s.cues.inner) - T.start;
    const per = (s.frame_w || 780) + 0 ;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const [sx, sy] = shake(lt, [cn], 12);
      ctx.save(); ctx.translate(sx, sy);
      wordsIn(ctx, s.kicker || 'THE TECHNIQUE', CX, 330, lt - .05, { size: 40, weight: 900, ls: .22, color: GOLD, stagger: .1 });
      const nsz = fitSize(env, ctx, s.name, 'Anton', 400, MAXW, 170, 80);
      if (lt < cn) {
        // before the word: the name scrambles, building up to the reveal
        const r = rng(env.frame * 7 + 3), AZ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ?';
        const scr = [...s.name].map(ch => ch === ' ' ? ' ' : AZ[Math.floor(r() * AZ.length)]).join('');
        txt(ctx, scr, CX, 500, { size: nsz, family: 'Anton', weight: 400, color: rgba('#ffffff', .18 + .12 * Math.sin(lt * 9)), alpha: ep(lt, .1, .5) });
        ctx.save(); ctx.globalAlpha = .5 * ep(lt, .1, .5); ctx.strokeStyle = GOLD; ctx.lineWidth = 3;
        const bw = MAXW * .9, ph = (lt * .7) % 1; ctx.beginPath(); ctx.moveTo(CX - bw / 2 + bw * ph, 520); ctx.lineTo(CX - bw / 2 + bw * Math.min(1, ph + .25), 520); ctx.stroke(); ctx.restore();
      }
      slam(ctx, s.name, CX, 500, lt - cn, { size: nsz, family: 'Anton', weight: 400, color: '#fff', glow: 'rgba(248,200,104,.7)', glowBlur: 50 });
      ring(ctx, CX, 450, lt - cn, { color: GOLD, r1: 720, w: 16 });
      streak(ctx, CX, 452, lt - cn - .05, { len: 950 });
      if (s.definition) pill(ctx, s.definition, CX, 590, lt - cn - .55, { size: 36, bg: 'rgba(248,232,200,.95)', color: INK, ls: .06 });
      // the diagram: one big story holding small stories
      const fw = s.frame_w || 800, fh = 520, fx = CX - fw / 2, fy = 690;
      const po = ep(lt, co, co + .9, E.inOutCubic);
      if (po > 0) {
        ctx.save(); ctx.lineWidth = 5; ctx.strokeStyle = GOLD; ctx.shadowColor = GOLD; ctx.shadowBlur = 18 + 14 * beatPulse(env, t);
        const perim = 2 * (fw + fh), L = perim * po;
        ctx.setLineDash([L, perim]); rrect(ctx, fx, fy, fw, fh, 30); ctx.stroke(); ctx.setLineDash([]);
        ctx.restore();
        ctx.globalAlpha = .9 * po; rrect(ctx, fx, fy, fw, fh, 30); ctx.fillStyle = 'rgba(16,14,10,.55)'; ctx.fill(); ctx.globalAlpha = 1;
        pill(ctx, s.outer_label, fx + 190, fy, lt - co - .3, { size: 32, bg: GOLD, color: INK, ls: .08 });
      }
      (s.inner || []).forEach((lab, k) => {
        const st = ci + k * .3, p = ep(lt, st, st + .45, E.outBack); if (p <= 0) return;
        const bw = 210, bh = 300, bx = CX + (k - 1) * 250, by = fy + fh / 2 + 25;
        const lit = Math.floor(((lt - ci) * 1.2)) % 3 === k && lt > ci + 1.2;
        ctx.save(); ctx.translate(bx, by + (1 - p) * 60); ctx.scale(p, p);
        if (lit) { ctx.shadowColor = rgba(TEAL, .8); ctx.shadowBlur = 30; }
        rrect(ctx, -bw / 2, -bh / 2, bw, bh, 20); ctx.fillStyle = 'rgba(12,16,20,.95)'; ctx.fill();
        ctx.lineWidth = 4; ctx.strokeStyle = lit ? '#fff' : TEAL; ctx.stroke(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
        icon(ctx, 'story', 1.1, TEAL);
        txt(ctx, lab, 0, 100, { size: 34, family: 'Anton', weight: 400, color: '#fff' });
        const qp = ep(lt, st + .35, st + .65, E.outBack);
        if (qp > 0) { ctx.save(); ctx.translate(bw / 2 - 12, -bh / 2 + 12); ctx.scale(qp, qp); ctx.beginPath(); ctx.arc(0, 0, 30, 0, 7); ctx.fillStyle = GOLD; ctx.fill(); txt(ctx, '?', 0, 14, { size: 40, family: 'Anton', weight: 400, color: INK }); ctx.restore(); }
        ctx.restore();
      });
      ctx.restore();
    };
  },

  // ------------------------------------------------------------ the story loop (STORY -> QUESTION -> ANSWER -> ESCAPES)
  loop(env, s, i, T) {
    const cues = s.nodes.map(n => cue(env, i, n.cue) - T.start), icons = ['story', 'question', 'answer', 'escape'];
    const angleAt = lt => {
      const top = -Math.PI / 2;
      if (lt < cues[0]) return top - 1.2 + 1.2 * ep(lt, .2, cues[0], E.inOutCubic);
      for (let k = 0; k < cues.length - 1; k++) if (lt < cues[k + 1]) return top + k * Math.PI / 2 + Math.PI / 2 * ep(lt, cues[k], cues[k + 1], E.inOutCubic);
      return top + (cues.length - 1) * Math.PI / 2 + (lt - cues[cues.length - 1]) * 2.6;
    };
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const cx = CX, cy = 810, R = 320, pr = ep(lt, .05, .9, E.inOutCubic);
      ctx.save();
      ctx.lineWidth = 7; ctx.strokeStyle = rgba(GOLD, .4); ctx.beginPath(); ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + pr * Math.PI * 2); ctx.stroke();
      ctx.setLineDash([3, 24]); ctx.lineDashOffset = -lt * 50; ctx.strokeStyle = rgba(GOLD, .55 * pr); ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(cx, cy, R + 46, 0, 7); ctx.stroke();
      ctx.lineDashOffset = lt * 35; ctx.beginPath(); ctx.arc(cx, cy, R - 46, 0, 7); ctx.stroke(); ctx.setLineDash([]);
      ctx.restore();
      const a = angleAt(lt), spr = tint(env, '#FFE6B0');
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let k = 0; k < 28; k++) { const aa = a - k * .03, x = cx + Math.cos(aa) * R, y = cy + Math.sin(aa) * R, z = 46 - k * 1.4; ctx.globalAlpha = (1 - k / 28) * .9 * pr; ctx.drawImage(spr, x - z / 2, y - z / 2, z, z); }
      ctx.restore(); ctx.globalAlpha = 1;
      s.nodes.forEach((n, k) => {
        const aa = -Math.PI / 2 + k * Math.PI / 2, x = cx + Math.cos(aa) * R, y = cy + Math.sin(aa) * R, d = lt - cues[k], on = d >= 0;
        const pop = on ? 1 + .35 * Math.exp(-d * 6) * Math.cos(d * 18) : .85;
        ctx.save(); ctx.translate(x, y); ctx.scale(pop, pop);
        if (on) { ctx.shadowColor = rgba(GOLD, .9); ctx.shadowBlur = 40 + 25 * beatPulse(env, t); }
        ctx.beginPath(); ctx.arc(0, 0, 70, 0, 7); ctx.fillStyle = on ? '#1a140a' : '#0d0e12'; ctx.fill();
        ctx.lineWidth = 5; ctx.strokeStyle = on ? GOLD : 'rgba(255,255,255,.25)'; ctx.stroke(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
        icon(ctx, icons[k], 1, on ? GOLD : 'rgba(255,255,255,.4)');
        ctx.restore();
        ring(ctx, x, y, d, { color: GOLD, r0: 70, r1: 220, w: 8, d: .6 });
        const ly = k === 0 ? y - 128 : y + 130;
        pill(ctx, n.label, x, ly, d - .08, { size: 40, bg: GOLD, color: '#0A0F18', ls: .1 });
      });
      const ca = ep(lt, .3, .9);
      txt(ctx, s.center, cx, cy + 8, { size: 76, family: 'Anton', weight: 400, color: rgba('#ffffff', ca) });
      if (s.center_ta) txt(ctx, s.center_ta, cx, cy + 74, { size: 34, family: 'Noto Sans Tamil', weight: 700, color: rgba(GOLD, ca) });
      if (s.footer) wordsIn(ctx, s.footer, CX, 1290, lt - (cue(env, i, s.footer_cue) - T.start), { size: 56, family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
    };
  },

  // ------------------------------------------------------------ TIMELINE: a playhead scrubs to each moment on its word;
  // "links" draw an arc from a setup to its payoff (events: [{label, sub, cue}], links: [[0, 3]])
  timeline(env, s, i, T) {
    const ev = s.events, n = ev.length, cues = ev.map(e => cue(env, i, e.cue) - T.start);
    const x0 = 110, x1 = 870, y = 800, xs = ev.map((e, k) => n === 1 ? CX : lerp(x0, x1, k / (n - 1)));
    const headAt = lt => { if (lt < cues[0]) return lerp(x0 - 60, xs[0], ep(lt, .15, cues[0], E.inOutCubic)); for (let k = n - 1; k >= 0; k--) if (lt >= cues[k]) return k === n - 1 ? xs[k] : lerp(xs[k], xs[k] + (xs[k + 1] - xs[k]) * .12, ep(lt, cues[k], cues[k] + 2)); return xs[0]; };
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      wordsIn(ctx, s.heading, CX, 380, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 84, 48), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      if (s.heading_ta) txt(ctx, s.heading_ta, CX, 446, { size: 36, family: 'Noto Sans Tamil', weight: 700, color: rgba(GOLD, ep(lt, .4, .9)) });
      const hx = headAt(lt), dr = ep(lt, .05, .7, E.inOutCubic);
      ctx.save(); ctx.lineCap = 'round';
      ctx.lineWidth = 6; ctx.strokeStyle = 'rgba(255,255,255,.14)'; ctx.beginPath(); ctx.moveTo(x0 - 50, y); ctx.lineTo(lerp(x0 - 50, x1 + 50, dr), y); ctx.stroke();
      for (let k = 0; k < 40; k++) { const tx = x0 - 50 + k * 22; if (tx > lerp(x0 - 50, x1 + 50, dr)) break; ctx.fillStyle = 'rgba(255,255,255,.16)'; ctx.fillRect(tx, y + 16, 2, k % 5 ? 10 : 22); }
      ctx.strokeStyle = GOLD; ctx.shadowColor = GOLD; ctx.shadowBlur = 24; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(x0 - 50, y); ctx.lineTo(Math.max(x0 - 50, hx), y); ctx.stroke(); ctx.restore();
      (s.links || []).forEach(([a, b]) => {                    // the thread from a setup to its payoff
        const p = ep(lt, cues[b], cues[b] + .7, E.inOutCubic); if (p <= 0) return;
        const mx = (xs[a] + xs[b]) / 2, r = Math.abs(xs[b] - xs[a]) / 2;
        ctx.save(); ctx.lineWidth = 6; ctx.strokeStyle = TEAL; ctx.shadowColor = TEAL; ctx.shadowBlur = 26; ctx.setLineDash([18, 12]); ctx.lineDashOffset = -lt * 60;
        ctx.beginPath(); ctx.ellipse(mx, y, r, Math.min(260, r * .8), 0, Math.PI, Math.PI + Math.PI * p); ctx.stroke(); ctx.restore();
      });
      ev.forEach((e, k) => {
        const d = lt - cues[k], on = d >= 0, cur = on && (k === n - 1 || lt < cues[k + 1]);
        const pop = on ? 1 + .4 * Math.exp(-d * 6) * Math.cos(d * 18) : .8, up = k % 2 === 0;
        ctx.save(); ctx.translate(xs[k], y); ctx.scale(pop, pop);
        if (on) { ctx.shadowColor = GOLD; ctx.shadowBlur = 30 + 20 * beatPulse(env, t); }
        ctx.beginPath(); ctx.arc(0, 0, cur ? 30 : 22, 0, 7); ctx.fillStyle = on ? GOLD : '#14161c'; ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = on ? '#fff' : 'rgba(255,255,255,.3)'; ctx.stroke();
        ctx.restore();
        ring(ctx, xs[k], y, d, { color: GOLD, r0: 30, r1: 200, w: 8, d: .6 });
        if (!on) return;
        const ly = up ? y - 150 : y + 170, a = cur ? 1 : .55, lx = clamp(xs[k], 190, 790);
        ctx.save(); ctx.strokeStyle = rgba(GOLD, .6 * a); ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(xs[k], y + (up ? -34 : 34)); ctx.lineTo(xs[k], y + (up ? -34 : 34) + (up ? -1 : 1) * 62 * ep(d, 0, .3)); ctx.stroke(); ctx.restore();
        pill(ctx, e.label, lx, ly, d - .1, { size: cur ? 42 : 34, bg: cur ? GOLD : 'rgba(22,24,30,.95)', color: cur ? INK : '#fff', border: cur ? null : rgba(GOLD, .5), ls: .08, alpha: a });
        if (e.sub) txt(ctx, e.sub, lx, ly + (up ? -58 : 70), { size: 32, weight: 800, ls: .1, color: rgba(TEAL, a * ep(d, .2, .5)) });
      });
      const spr = tint(env, '#ffffff'); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = .9; ctx.drawImage(spr, hx - 46, y - 46, 92, 92); ctx.restore(); ctx.globalAlpha = 1;
      if (s.footer) wordsIn(ctx, s.footer, CX, 1240, lt - (cue(env, i, s.footer_cue) - T.start), { size: fitSize(env, ctx, s.footer, 'Anton', 400, MAXW, 64, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
    };
  },

  // ------------------------------------------------------------ METER: a dial whose needle climbs level by level on the
  // voice (levels: [{label, value 0-100, cue}]); the top level shakes the frame
  meter(env, s, i, T) {
    const lv = s.levels, cues = lv.map(l => cue(env, i, l.cue) - T.start), top = Math.max(...lv.map(l => l.value));
    const valAt = lt => { let v = 0; lv.forEach((l, k) => { const d = lt - cues[k]; if (d >= 0) { const prev = k ? lv[k - 1].value : 0; v = prev + (l.value - prev) * (1 - Math.exp(-d * 5) * Math.cos(d * 11)); } }); return clamp(v, 0, 104); };
    const peak = cues[lv.findIndex(l => l.value === top)];
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const [sx, sy] = shake(lt, [peak], 14); ctx.save(); ctx.translate(sx, sy);
      wordsIn(ctx, s.heading, CX, 380, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 84, 48), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const cx = CX, cy = 940, R = 350, a0 = Math.PI * .85, a1 = Math.PI * 2.15, v = valAt(lt), ang = lerp(a0, a1, v / 100), dr = ep(lt, .1, .8, E.inOutCubic);
      ctx.save(); ctx.lineCap = 'round';
      ctx.lineWidth = 44; ctx.strokeStyle = 'rgba(255,255,255,.08)'; ctx.beginPath(); ctx.arc(cx, cy, R, a0, lerp(a0, a1, dr)); ctx.stroke();
      const g = ctx.createLinearGradient(cx - R, 0, cx + R, 0); g.addColorStop(0, TEAL); g.addColorStop(.6, GOLD); g.addColorStop(1, '#FF4D4D');
      ctx.strokeStyle = g; ctx.shadowColor = GOLD; ctx.shadowBlur = 30 + 26 * beatPulse(env, t); ctx.beginPath(); ctx.arc(cx, cy, R, a0, Math.max(a0 + .001, ang)); ctx.stroke(); ctx.shadowBlur = 0;
      for (let k = 0; k <= 20; k++) { const a = lerp(a0, a1, k / 20), r0 = R + 40, r1 = R + (k % 5 ? 56 : 74); ctx.lineWidth = k % 5 ? 3 : 5; ctx.strokeStyle = `rgba(255,255,255,${(k % 5 ? .25 : .6) * dr})`; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); ctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); ctx.stroke(); }
      ctx.translate(cx, cy); ctx.rotate(ang); ctx.shadowColor = '#fff'; ctx.shadowBlur = 20; ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(-30, -9); ctx.lineTo(R - 30, 0); ctx.lineTo(-30, 9); ctx.closePath(); ctx.fill();
      ctx.restore();
      ctx.beginPath(); ctx.arc(cx, cy, 30, 0, 7); ctx.fillStyle = GOLD; ctx.fill();
      txt(ctx, String(Math.round(Math.min(v, 100))), cx, cy + 250, { size: 180, family: 'Anton', weight: 400, color: '#fff', glow: rgba(GOLD, .5), glowBlur: 40 });
      if (s.label) txt(ctx, s.label, cx, cy + 312, { size: 36, weight: 900, ls: .22, color: rgba(GOLD, ep(lt, .3, .8)) });
      lv.forEach((l, k) => { const d = lt - cues[k], cur = d >= 0 && (k === lv.length - 1 || lt < cues[k + 1]); if (cur) { pill(ctx, l.label, cx, 560, d - .05, { size: 46, bg: l.value === top ? '#FF4D4D' : GOLD, color: l.value === top ? '#fff' : INK, ls: .08, glow: rgba(GOLD, .6) }); ring(ctx, cx, cy, d, { color: GOLD, r0: 120, r1: 620, w: 10, d: .6 }); } });
      ctx.restore();
      flash(ctx, lt, peak, { alpha: .3, d: .25 });
    };
  },

  // ------------------------------------------------------------ VERSUS: two stills cut by a moving diagonal; the cut slides
  // to one side on a word (left/right: {image, label, sub}, tilt_cue, tilt: -1 left wins | 1 right wins, slam_text, slam_cue)
  versus(env, s, i, T) {
    const ct = s.tilt_cue ? cue(env, i, s.tilt_cue) - T.start : 1e9, cs = s.slam_cue ? cue(env, i, s.slam_cue) - T.start : 1e9;
    const cl = cue(env, i, s.left.cue, .3) - T.start, cr = cue(env, i, s.right.cue, .9) - T.start;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const y0 = 300, h = 880, mid = W / 2 + (s.tilt || 0) * 250 * ep(lt, ct, ct + .7, E.inOutCubic) + Math.sin(lt * .8) * 8, sk = 120;
      const half = (img, side, o) => { ctx.save(); ctx.beginPath();
        if (side < 0) { ctx.moveTo(0, y0); ctx.lineTo(mid + sk, y0); ctx.lineTo(mid - sk, y0 + h); ctx.lineTo(0, y0 + h); } else { ctx.moveTo(mid + sk, y0); ctx.lineTo(W, y0); ctx.lineTo(W, y0 + h); ctx.lineTo(mid - sk, y0 + h); }
        ctx.closePath(); ctx.clip(); ctx.globalAlpha = o.a;
        cover(ctx, img, side < 0 ? 0 : mid - sk, y0, side < 0 ? mid + sk : W - mid + sk, h, { zoom: 1.1 + .08 * ep(lt, 0, 6, E.linear), fx: o.fx ?? .5, fy: o.fy ?? .4 });
        ctx.globalAlpha = 1; grad(ctx, 0, y0 + h - 420, 0, y0 + h, [[0, 'rgba(5,6,8,0)'], [1, 'rgba(5,6,8,.92)']], [0, y0 + h - 420, W, 422]); ctx.restore(); };
      half(env.img[s.left.image], -1, { a: ep(lt, 0, .4) * (lt > ct && s.tilt > 0 ? .55 : 1), fx: s.left.fx, fy: s.left.fy });
      half(env.img[s.right.image], 1, { a: ep(lt, .15, .55) * (lt > ct && s.tilt < 0 ? .55 : 1), fx: s.right.fx, fy: s.right.fy });
      fadeBand(ctx, y0, h, 10);
      ctx.save(); ctx.lineWidth = 8; ctx.strokeStyle = GOLD; ctx.shadowColor = GOLD; ctx.shadowBlur = 30 + 30 * beatPulse(env, t); const dp = ep(lt, .1, .6, E.inOutCubic);
      ctx.beginPath(); ctx.moveTo(mid + sk, y0); ctx.lineTo(lerp(mid + sk, mid - sk, dp), lerp(y0, y0 + h, dp)); ctx.stroke(); ctx.restore();
      [[s.left, cl, 250, 'left'], [s.right, cr, 760, 'right']].forEach(([o, c, x]) => {
        const size = fitSize(env, ctx, o.label, 'Anton', 400, 440, 92, 46);
        slam(ctx, o.label, x, y0 + h - 130, lt - c, { size, family: 'Anton', weight: 400, color: '#fff', stroke: 'rgba(5,6,8,.9)', strokeW: 10 });
        if (o.sub) pill(ctx, o.sub, x, y0 + h - 60, lt - c - .25, { size: 30, bg: GOLD, color: INK, ls: .08 });
      });
      if (s.vs !== false) pill(ctx, s.vs || 'VS', mid, y0 + h / 2, lt - .5, { size: 54, bg: INK, color: GOLD, border: GOLD, ls: .1, family: 'Anton', weight: 400 });
      if (s.slam_text) { slam(ctx, s.slam_text, CX, 1270, lt - cs, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 120, 60), family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .6), glowBlur: 50 }); ring(ctx, CX, 1230, lt - cs, { color: GOLD, r1: 700 }); }
    };
  },

  // ------------------------------------------------------------ WEB: who is tied to whom. Lines run out from the centre and
  // light a face on each word (center: {label, image}, nodes: [{label, image, link, cue}], 3 to 6)
  web(env, s, i, T) {
    const nd = s.nodes, n = nd.length, cues = nd.map(x => cue(env, i, x.cue) - T.start), cx = CX, cy = 810, RX = 335, RY = 365;
    const pos = nd.map((x, k) => { const a = -Math.PI / 2 + (k + (n % 2 ? 0 : .5)) * Math.PI * 2 / n; return [cx + Math.cos(a) * RX, cy + Math.sin(a) * RY]; });
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (s.heading) wordsIn(ctx, s.heading, CX, 330, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 76, 44), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const circle = (key, x, y, r, on, label) => {
        ctx.save(); ctx.translate(x, y);
        if (on) { ctx.shadowColor = GOLD; ctx.shadowBlur = 34 + 24 * beatPulse(env, t); }
        ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fillStyle = '#101216'; ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
        if (key && env.img[key]) { ctx.save(); ctx.beginPath(); ctx.arc(0, 0, r - 6, 0, 7); ctx.clip(); ctx.globalAlpha = on ? 1 : .35; cover(ctx, env.img[key], -r, -r, r * 2, r * 2, { zoom: 1.15, fy: .35 }); ctx.restore(); }
        else txt(ctx, String(label || '?')[0], 0, r * .36, { size: r * 1.05, family: 'Anton', weight: 400, color: rgba(GOLD, on ? 1 : .4) });
        ctx.lineWidth = 6; ctx.strokeStyle = on ? GOLD : 'rgba(255,255,255,.22)'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.stroke(); ctx.restore();
      };
      nd.forEach((x, k) => {                                     // the threads first, so the faces sit on top
        const d = lt - cues[k], p = ep(d, 0, .55, E.inOutCubic); if (p <= 0) return;
        const [px, py] = pos[k], ex = lerp(cx, px, p), ey = lerp(cy, py, p);
        ctx.save(); ctx.lineWidth = 5; ctx.strokeStyle = rgba(GOLD, .8); ctx.shadowColor = GOLD; ctx.shadowBlur = 18; ctx.setLineDash([14, 10]); ctx.lineDashOffset = -lt * 50;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke(); ctx.restore();
      });
      nd.forEach((x, k) => {
        const d = lt - cues[k], on = d >= .45, [px, py] = pos[k], pop = on ? 1 + .3 * Math.exp(-(d - .45) * 6) * Math.cos((d - .45) * 18) : ep(lt, .1 + k * .06, .5 + k * .06, E.outBack) * .85;
        ctx.save(); ctx.translate(px, py); ctx.scale(pop, pop); ctx.translate(-px, -py); circle(x.image, px, py, 96, on, x.label); ctx.restore();
        ring(ctx, px, py, d - .45, { color: GOLD, r0: 96, r1: 260, w: 8, d: .6 });
        if (on) pill(ctx, x.label, clamp(px, 170, 810), py + (py < cy - 40 ? -132 : 132), d - .5, { size: 34, bg: GOLD, color: INK, ls: .08 });
      });
      const cr = 128 + 6 * beatPulse(env, t);
      circle(s.center.image, cx, cy, cr, true, s.center.label);
      if (s.center.image && env.img[s.center.image]) {              // the name sits inside the centre, so the threads stay clear
        ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, cr - 6, 0, 7); ctx.clip();
        grad(ctx, 0, cy, 0, cy + cr, [[0, 'rgba(5,6,8,0)'], [1, 'rgba(5,6,8,.95)']], [cx - cr, cy, cr * 2, cr]); ctx.restore();
        txt(ctx, s.center.label, cx, cy + 84, { size: fitSize(env, ctx, s.center.label, 'Anton', 400, 190, 52, 28), family: 'Anton', weight: 400, color: '#fff', alpha: ep(lt, .2, .6) });
      }
      nd.forEach((x, k) => {                                     // what ties them, written on the thread, on top of everything
        const d = lt - cues[k], [px, py] = pos[k];
        if (x.link) pill(ctx, x.link, lerp(cx, px, .54), lerp(cy, py, .54), d - .55, { size: 26, bg: 'rgba(12,14,18,.96)', color: TEAL, border: rgba(TEAL, .7), ls: .08 });
      });
      if (s.footer) wordsIn(ctx, s.footer, CX, 1296, lt - (cue(env, i, s.footer_cue) - T.start), { size: fitSize(env, ctx, s.footer, 'Anton', 400, MAXW, 60, 38), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
    };
  },

  // ------------------------------------------------------------ question cards that flip in on the word
  cards(env, s, i, T) {
    const cues = s.cards.map(c => cue(env, i, c.cue) - T.start);
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      wordsIn(ctx, s.heading, CX, 360, lt - .05, { size: 70, family: 'Anton', weight: 400, color: '#fff', stagger: .09 });
      if (s.heading_ta) txt(ctx, s.heading_ta, CX, 424, { size: 36, family: 'Noto Sans Tamil', weight: 700, color: rgba(GOLD, ep(lt, .4, .9)) });
      s.cards.forEach((c, k) => {
        const p = ep(lt, cues[k], cues[k] + .5, E.outBack); if (p <= 0) return;
        const active = lt >= cues[k] && (k === s.cards.length - 1 || lt < cues[k + 1]), dim = active ? 1 : .5;
        const y = 580 + k * 250, cw = 860, ch = 220;
        ctx.save(); ctx.translate(CX + (active ? Math.sin(lt * 2) * 4 : 0), y); ctx.scale(lerp(.9, 1, p), p); ctx.globalAlpha = clamp(p * 2);
        if (active) { ctx.shadowColor = rgba(GOLD, .75); ctx.shadowBlur = 36 + 28 * beatPulse(env, t); }
        rrect(ctx, -cw / 2, -ch / 2, cw, ch, 28); ctx.fillStyle = 'rgba(16,18,24,.94)'; ctx.fill();
        ctx.lineWidth = 3; ctx.strokeStyle = active ? GOLD : 'rgba(255,255,255,.16)'; ctx.stroke(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
        ctx.save(); rrect(ctx, -cw / 2 + 14, -ch / 2 + 14, 270, ch - 28, 18); ctx.clip();
        ctx.globalAlpha = clamp(p * 2) * (active ? 1 : .55);
        cover(ctx, env.img[c.image], -cw / 2 + 14, -ch / 2 + 14, 270, ch - 28, { zoom: 1.12 + .12 * ep(lt, cues[k], cues[k] + 6, E.linear), fx: c.fx ?? .5, fy: c.fy ?? .4 });
        ctx.restore();
        ctx.globalAlpha = clamp(p * 2);
        txt(ctx, String(k + 1).padStart(2, '0'), -cw / 2 + 312, -50, { size: 40, family: 'Anton', weight: 400, color: GOLD, align: 'left', alpha: dim });
        c.lines.forEach((ln, j) => txt(ctx, ln, -cw / 2 + 312, 12 + j * 64, { size: 60, family: 'Anton', weight: 400, color: '#fff', align: 'left', alpha: dim }));
        ctx.restore(); ctx.globalAlpha = 1;
        if (active) sweep(ctx, lt - cues[k], .1, .9, { alpha: .12, width: 160 });
      });
    };
  },

  // ------------------------------------------------------------ HERO MOMENT: black and white bleed into grey
  moral(env, s, i, T) {
    const c = {}; for (const [k, v] of Object.entries(s.cues)) c[k] = cue(env, i, v) - T.start;
    const faces = env.memo('gray:' + s.image, () => filtered(env.img[s.image], 'grayscale(1) contrast(1.25) brightness(1.05)'));
    const r = rng(77), shards = Array.from({ length: 26 }, () => ({ y: r() * H, len: 60 + r() * 160, vx: (r() - .5) * 1400, vy: (r() - .3) * 900, rot: (r() - .5) * 8 }));
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [c.crack, c.slam], 16);
      ctx.save(); ctx.translate(sx, sy);
      const mid = W / 2;
      ctx.fillStyle = '#EEEAE2'; ctx.fillRect(-40, -40, mid + 40, H + 80); ctx.fillStyle = '#060709'; ctx.fillRect(mid, -40, W - mid + 40, H + 80);
      dust(env, ctx, t, { n: 22, color: '#ffffff', alpha: .25, min: 2, max: 6, seed: 9 });
      const gone = ep(lt, c.crack, c.crack + .5);
      const la = ep(lt, .05, .5, E.outBack) * (1 - gone);
      txt(ctx, s.left, 270, 600 - (1 - la) * 40, { size: 160, family: 'Anton', weight: 400, color: rgba('#060709', la) });
      txt(ctx, s.right, 760, 1150 + (1 - la) * 40, { size: 160, family: 'Anton', weight: 400, color: rgba('#EEEAE2', la) });
      if (s.left_ta) txt(ctx, s.left_ta, 270, 680, { size: 40, family: 'Noto Sans Tamil', weight: 700, color: rgba('#060709', la * .8) });
      if (s.right_ta) txt(ctx, s.right_ta, 760, 1230, { size: 40, family: 'Noto Sans Tamil', weight: 700, color: rgba('#EEEAE2', la * .8) });
      const bleed = ep(lt, c.bleed, c.crack, E.inOutQuad) * 330 + beatPulse(env, t) * 12 * (lt > c.bleed ? 1 : 0);
      if (bleed > 1 && gone < 1) {
        for (let layer = 2; layer >= 0; layer--) {
          ctx.beginPath();
          const wAt = y => bleed * (1 + layer * .16) * (1 + .24 * Math.sin(y * .008 + lt * 2.1 + layer) + .13 * Math.sin(y * .024 - lt * 3.2));
          for (let y = -40; y <= H + 40; y += 40) ctx.lineTo(mid - wAt(y), y);
          for (let y = H + 40; y >= -40; y -= 40) ctx.lineTo(mid + wAt(y), y);
          ctx.closePath(); ctx.fillStyle = layer ? `rgba(128,128,128,${.28 / layer})` : '#808080'; ctx.fill();
        }
      }
      const dl = ep(lt, c.line, c.line + .55, E.inOutCubic);
      if (dl > 0 && lt < c.crack) {
        ctx.save(); ctx.strokeStyle = GOLD; ctx.lineWidth = 7; ctx.shadowColor = GOLD; ctx.shadowBlur = 34 + 20 * beatPulse(env, t);
        ctx.beginPath();
        for (let y = 0; y <= H * dl; y += 24) { const x = mid + Math.sin(y * .011 + lt * 4) * bleed * .09; if (y === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); }
        ctx.stroke(); ctx.restore();
      }
      if (lt >= c.crack) {
        const cp = ep(lt, c.crack, c.crack + .6, E.outCubic);
        ctx.save(); ctx.globalAlpha = cp; grad(ctx, 0, 0, 0, H, [[0, '#a2a2a2'], [.5, '#7b7b7b'], [1, '#3f3f3f']], [-40, -40, W + 80, H + 80]); ctx.restore();
        ctx.save(); ctx.globalAlpha = .55 * ep(lt, c.crack + .2, c.crack + 1.4); ctx.globalCompositeOperation = 'multiply';
        cover(ctx, faces, 0, 260, W, 1360, { zoom: 1.06 + .06 * ep(lt, c.crack, c.crack + 5, E.linear), fx: s.fx ?? .5, fy: .4 }); ctx.restore();
        const d = lt - c.crack;
        if (d < 1.4) {
          ctx.save(); ctx.strokeStyle = GOLD; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.shadowColor = GOLD; ctx.shadowBlur = 20;
          for (const sh of shards) {
            const x = mid + sh.vx * d, y = sh.y + sh.vy * d + 900 * d * d, a = sh.rot * d;
            ctx.globalAlpha = clamp(1 - d / 1.4);
            ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.beginPath(); ctx.moveTo(0, -sh.len / 2); ctx.lineTo(0, sh.len / 2); ctx.stroke(); ctx.restore();
          }
          ctx.restore(); ctx.globalAlpha = 1;
        }
        flash(ctx, lt, c.crack, { alpha: .55 });
      }
      if (s.kicker) pill(ctx, s.kicker, CX, 330, lt - .1, { size: 34, bg: INK, color: GOLD, border: rgba(GOLD, .7), ls: .16, alpha: 1 - ep(lt, c.crack - .2, c.crack + .2) });
      s.slam_text.forEach((w, k) => slam(ctx, w, CX, 840 + k * 220, lt - c.slam - k * .16, { size: k ? 250 : 170, family: 'Anton', weight: 400, color: k ? '#fff' : '#111', glow: k ? 'rgba(255,255,255,.55)' : null, glowBlur: 50 }));
      ring(ctx, CX, 960, lt - c.slam - .16, { color: '#ffffff', r1: 800, w: 14, alpha: .7 });
      ctx.restore();
    };
  },

  // ------------------------------------------------------------ the last scene: the question turns to us
  standoff(env, s, i, T) {
    const img = env.img[s.image];
    const cq = cue(env, i, s.q_cue) - T.start, cs = cue(env, i, s.slam_cue) - T.start;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const bandY = 200, bandH = 820, dur = T.end - T.start;
      cover(ctx, img, 0, bandY, W, bandH, { zoom: 1.02 + .14 * ep(lt, 0, dur, E.linear), fx: s.fx ?? .5, fy: s.fy ?? .45 });
      ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = 'rgba(120,70,20,.35)'; ctx.fillRect(0, bandY, W, bandH); ctx.restore();
      fadeBand(ctx, bandY, bandH);
      const pts = shapePoints(env, 'q', '?', 620, 'Anton', 11);
      assemble(env, ctx, lt - cq, pts, CX, 905, { from: [W * .3, 560], spread: 700, color: GOLD, size: 9, stagger: .55, d: 1.05, flip: cs - cq });
      slam(ctx, s.slam_text, CX, 1255, lt - cs - .35, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 120, 60), family: 'Anton', weight: 400, color: '#fff', glow: rgba(GOLD, .6), glowBlur: 40 });
      ring(ctx, CX, 905, lt - cs, { color: GOLD, r0: 120, r1: 760 });
      streak(ctx, CX, 1215, lt - cs - .35, { len: 900 });
    };
  },

  // ------------------------------------------------------------ DETAIL (19 Nov): a lens travels to the detail most viewers
  // missed and magnifies it (image, spot: {x, y} 0-1 inside the frame, zoom, cue, label, label_cue, count: [n, of], heading)
  detail(env, s, i, T) {
    const img = env.img[s.image], cl = cue(env, i, s.cue, .9) - T.start, cb = s.label_cue ? cue(env, i, s.label_cue) - T.start : cl + .6;
    const fx0 = 70, fy0 = 360, fw = 840, fh = 820, sp = s.spot || { x: .5, y: .5 }, Z = s.zoom || 2.6;
    const tx = fx0 + sp.x * fw, ty = fy0 + sp.y * fh, cnt = s.count;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const [sx, sy] = shake(lt, [cl + .55], 9);
      ctx.save(); ctx.translate(sx, sy);
      const ent = ep(lt, 0, .6, E.outBack), push = 1.04 + .05 * ep(lt, 0, 8, E.linear);
      const still = () => cover(ctx, img, fx0, fy0, fw, fh, { zoom: push, fx: s.fx ?? .5, fy: s.fy ?? .5 });
      ctx.save(); ctx.globalAlpha = ep(lt, 0, .4); ctx.translate(CX, fy0 + fh / 2 + (1 - ent) * 140); ctx.scale(.9 + .1 * ent, .9 + .1 * ent); ctx.translate(-CX, -(fy0 + fh / 2));
      ctx.save(); rrect(ctx, fx0, fy0, fw, fh, 30); ctx.clip(); still(); ctx.restore();
      rrect(ctx, fx0, fy0, fw, fh, 30); ctx.lineWidth = 3; ctx.strokeStyle = rgba(GOLD, .5); ctx.stroke(); ctx.restore(); ctx.globalAlpha = 1;
      // the lens: searches slowly, then travels to the detail on the word and opens up
      const go = ep(lt, cl, cl + .6, E.inOutCubic), open = ep(lt, cl + .45, cl + .85, E.outBack);
      const wx = CX + Math.sin(lt * 1.3) * 230, wy = fy0 + fh * .45 + Math.cos(lt * .9) * 170;
      const lx = lerp(wx, tx, go), ly = lerp(wy, ty, go), R = lerp(95, 175, open), z = lerp(1.35, Z, open);
      if (lt > .3) {
        const dim = .62 * open;                              // the rest of the frame goes dark around the lens
        if (dim > 0) { ctx.save(); ctx.beginPath(); ctx.rect(fx0, fy0, fw, fh); ctx.arc(lx, ly, R, 0, 7, true); ctx.fillStyle = `rgba(5,6,8,${dim})`; ctx.fill(); ctx.restore(); }
        ctx.save(); ctx.beginPath(); ctx.arc(lx, ly, R - 4, 0, 7); ctx.clip();
        ctx.translate(lx, ly); ctx.scale(z, z); ctx.translate(-lx, -ly); still(); ctx.restore();
        ctx.save(); ctx.shadowColor = GOLD; ctx.shadowBlur = 30 + 24 * beatPulse(env, t); ctx.lineWidth = 9; ctx.strokeStyle = GOLD;
        ctx.beginPath(); ctx.arc(lx, ly, R, 0, 7); ctx.stroke(); ctx.shadowBlur = 0;
        ctx.lineWidth = 22; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(lx + R * .72, ly + R * .72); ctx.lineTo(lx + R * 1.25, ly + R * 1.25); ctx.stroke();
        ctx.lineWidth = 3; ctx.strokeStyle = rgba('#ffffff', .55 * open);
        for (let k = 0; k < 4; k++) { const a = k * Math.PI / 2 + lt * .6; ctx.beginPath(); ctx.moveTo(lx + Math.cos(a) * (R - 28), ly + Math.sin(a) * (R - 28)); ctx.lineTo(lx + Math.cos(a) * (R - 8), ly + Math.sin(a) * (R - 8)); ctx.stroke(); }
        ctx.restore();
        ring(ctx, lx, ly, lt - cl - .55, { color: GOLD, r0: R, r1: R + 260, w: 10 });
      }
      if (s.label) {                                          // the label hangs off the lens, on the side with room
        const below = ty < fy0 + fh * .55, py = below ? ly + R + 95 : ly - R - 70, px = clamp(lx, 250, 730);
        if (lt > cb) { ctx.save(); ctx.globalAlpha = ep(lt, cb, cb + .3); ctx.strokeStyle = TEAL; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(lx, ly + (below ? R : -R)); ctx.lineTo(px, py + (below ? -32 : 32)); ctx.stroke(); ctx.restore(); ctx.globalAlpha = 1; }
        pill(ctx, s.label, px, py, lt - cb, { size: 44, bg: TEAL, color: INK, ls: .08, glow: rgba(TEAL, .6) });
      }
      ctx.restore();
      // the counter: DETAIL 1/3, one bar per detail, this one fills on entry
      if (cnt) {
        const [n, of] = cnt, bw = 70, gap = 18, x0 = CX - ((of * bw + (of - 1) * gap) / 2);
        wordsIn(ctx, s.heading || 'DETAIL', CX - 70, 300, lt - .05, { size: 44, weight: 900, ls: .2, color: '#fff', stagger: .08 });
        slam(ctx, `${n}/${of}`, CX + 130, 304, lt - .2, { size: 64, family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .6), glowBlur: 30 });
        for (let k = 0; k < of; k++) {
          const on = k < n - 1 ? 1 : k === n - 1 ? ep(lt, .35, .75, E.outBack) : 0;
          ctx.fillStyle = 'rgba(255,255,255,.18)'; rrect(ctx, x0 + k * (bw + gap), 326, bw, 10, 5); ctx.fill();
          if (on > 0) { ctx.save(); ctx.shadowColor = GOLD; ctx.shadowBlur = 18; ctx.fillStyle = GOLD; rrect(ctx, x0 + k * (bw + gap), 326, bw * on, 10, 5); ctx.fill(); ctx.restore(); }
        }
      } else if (s.heading) wordsIn(ctx, s.heading, CX, 300, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 76, 44), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
    };
  },

  // ------------------------------------------------------------ CHAIN (19 Nov): the butterfly effect. One small choice knocks
  // down the next, each card bigger, up to the ending (heading, steps: 3-5 of {label, cue}; the last one is the payoff)
  chain(env, s, i, T) {
    const st = s.steps, n = st.length, cues = st.map((x, k) => cue(env, i, x.cue, .4 + k * 1.1) - T.start);
    const y0 = 470, y1 = 1230, gap = n > 1 ? (y1 - y0) / (n - 1) : 0;
    const pos = st.map((x, k) => { const f = n > 1 ? k / (n - 1) : 1; return { x: CX + (k % 2 ? 60 : -60) * (1 - f), y: y0 + k * gap, w: lerp(360, 800, f), h: lerp(96, 132, f) }; });
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const hits = cues.map(c => c + .38), [sx, sy] = shake(lt, hits, 7);
      ctx.save(); ctx.translate(sx, sy);
      if (s.heading) wordsIn(ctx, s.heading, CX, 330, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 76, 44), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      for (let k = 1; k < n; k++) {                        // the thread from one card to the next, drawn as the next one falls
        const p = ep(lt, cues[k] - .1, cues[k] + .3, E.inOutCubic); if (p <= 0) continue;
        const a = pos[k - 1], b = pos[k];
        ctx.save(); ctx.strokeStyle = rgba(GOLD, .8); ctx.lineWidth = 5; ctx.setLineDash([14, 12]); ctx.lineDashOffset = -lt * 60;
        ctx.beginPath(); ctx.moveTo(a.x, a.y + a.h / 2); ctx.lineTo(lerp(a.x, b.x, p), lerp(a.y + a.h / 2, b.y - b.h / 2, p)); ctx.stroke(); ctx.restore();
      }
      st.forEach((x, k) => {
        const d = lt - cues[k]; if (d < 0) return;
        const P = pos[k], last = k === n - 1, fall = ep(d, 0, .42, E.outBack);
        const pushed = k < n - 1 && lt > cues[k + 1] + .3 ? Math.exp(-(lt - cues[k + 1] - .3) * 5) * Math.sin((lt - cues[k + 1]) * 22) * .05 : 0;
        ctx.save(); ctx.translate(P.x, P.y - (1 - fall) * 170); ctx.rotate((1 - fall) * (k % 2 ? .3 : -.3) + pushed + Math.sin(lt * .9 + k) * .01);
        ctx.globalAlpha = clamp(d * 5);
        if (last) { ctx.shadowColor = GOLD; ctx.shadowBlur = 40 + 30 * beatPulse(env, t); }
        rrect(ctx, -P.w / 2, -P.h / 2, P.w, P.h, 22); ctx.fillStyle = last ? GOLD : '#12151B'; ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
        ctx.lineWidth = 4; ctx.strokeStyle = last ? '#fff' : rgba(k % 2 ? TEAL : GOLD, .8); ctx.stroke();
        const size = fitSize(env, ctx, x.label, 'Anton', 400, P.w - 150, last ? 78 : 60, 34);
        txt(ctx, x.label, 26, size * .36, { size, family: 'Anton', weight: 400, color: last ? INK : '#fff' });
        txt(ctx, String(k + 1), -P.w / 2 + 50, 22, { size: 60, family: 'Anton', weight: 400, color: last ? rgba(INK, .5) : rgba(GOLD, .6) });
        ctx.restore(); ctx.globalAlpha = 1;
        ring(ctx, P.x, P.y, d - .38, { color: last ? GOLD : TEAL, r0: 60, r1: P.w * .7, w: 8, d: .55 });
      });
      ctx.restore();
      // the butterfly on the first card: a tiny wing-beat that starts it all
      const b = pos[0], bd = lt - cues[0];
      if (bd > .2) {
        const flap = .35 + .65 * Math.abs(Math.sin(lt * 9)), bx = b.x - b.w / 2 - 30 + Math.sin(lt * 1.7) * 14, by = b.y - b.h / 2 - 22 + Math.cos(lt * 2.3) * 10;
        ctx.save(); ctx.translate(bx, by); ctx.globalAlpha = ep(bd, .2, .6); ctx.fillStyle = TEAL; ctx.shadowColor = TEAL; ctx.shadowBlur = 20;
        [-1, 1].forEach(sd => { ctx.beginPath(); ctx.ellipse(sd * 13 * flap, -6, 14 * flap, 19, sd * .5, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(sd * 9 * flap, 12, 9 * flap, 11, -sd * .4, 0, 7); ctx.fill(); });
        ctx.restore(); ctx.globalAlpha = 1;
      }
      flash(ctx, lt, cues[n - 1] + .38, { alpha: .22, d: .25 });
    };
  },

  // ------------------------------------------------------------ QUOTE (19 Nov): who said it, from where. A portrait that
  // "talks" (bars pulse round it), the name, the role, a short key phrase and the source (image, name, role, phrase,
  // source, cues: {name, phrase})
  quote(env, s, i, T) {
    const img = s.image ? env.img[s.image] : null, cs = s.cues || {};
    const cn = cue(env, i, cs.name, .5) - T.start, cp = cue(env, i, cs.phrase, 1.6) - T.start;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const [sx, sy] = shake(lt, [cp + .1], 8);
      ctx.save(); ctx.translate(sx, sy);
      const px = CX, py = 600, R = 190, ent = ep(lt, 0, .6, E.outBack);
      txt(ctx, '“', CX - 330, 470 + (1 - ep(lt, .1, .6)) * 60, { size: 360, family: 'Anton', weight: 400, color: rgba(GOLD, .22 * ep(lt, .1, .6)) });
      ctx.save(); ctx.globalCompositeOperation = 'lighter';           // the voice bars round the portrait
      for (let k = 0; k < 48; k++) {
        const a = k / 48 * Math.PI * 2 + lt * .25, amp = (.35 + .65 * Math.abs(Math.sin(lt * 7 + k * 1.9) * Math.sin(lt * 3.1 + k * .7))) * (.5 + .5 * beatPulse(env, t));
        const r0 = R + 22, r1 = r0 + 16 + 60 * amp * ent;
        ctx.strokeStyle = rgba(k % 2 ? TEAL : GOLD, .55); ctx.lineWidth = 6; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(px + Math.cos(a) * r0, py + Math.sin(a) * r0); ctx.lineTo(px + Math.cos(a) * r1, py + Math.sin(a) * r1); ctx.stroke();
      }
      ctx.restore();
      ctx.save(); ctx.translate(px, py); ctx.scale(ent, ent);
      ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.fillStyle = '#101216'; ctx.fill();
      if (img) { ctx.save(); ctx.beginPath(); ctx.arc(0, 0, R - 8, 0, 7); ctx.clip(); cover(ctx, img, -R, -R, R * 2, R * 2, { zoom: 1.12 + .05 * ep(lt, 0, 8, E.linear), fx: s.fx ?? .5, fy: s.fy ?? .35 }); ctx.restore(); }
      else txt(ctx, String(s.name || '?')[0], 0, R * .36, { size: R * 1.05, family: 'Anton', weight: 400, color: GOLD });
      ctx.lineWidth = 8; ctx.strokeStyle = GOLD; ctx.shadowColor = GOLD; ctx.shadowBlur = 26; ctx.beginPath(); ctx.arc(0, 0, R, 0, 7); ctx.stroke();
      ctx.restore(); ctx.shadowBlur = 0;
      const ns = fitSize(env, ctx, s.name, 'Anton', 400, MAXW, 104, 54);
      slam(ctx, s.name, CX, 935, lt - cn, { size: ns, family: 'Anton', weight: 400, color: '#fff', glow: rgba(GOLD, .5), glowBlur: 40 });
      if (s.role) pill(ctx, s.role, CX, 1000, lt - cn - .3, { size: 32, bg: rgba('#ffffff', .12), color: '#fff', border: rgba(GOLD, .7), ls: .12 });
      if (s.phrase) {
        const ps = fitSize(env, ctx, s.phrase, 'Anton', 400, MAXW, 92, 46);
        wordsIn(ctx, s.phrase, CX, 1150, lt - cp, { size: ps, family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .5), glowBlur: 30, stagger: .1 });
        streak(ctx, CX, 1175, lt - cp - .2, { len: 800 });
      }
      if (s.source) pill(ctx, 'SOURCE: ' + s.source, CX, 1262, lt - cp - .6, { size: 26, bg: INK, color: rgba('#ffffff', .85), border: rgba(TEAL, .8), ls: .14 });
      ctx.restore();
    };
  },

  // ------------------------------------------------------------ SOURCE (19 Nov): the source story and the film, side by
  // side; lines link the beats that match (heading, left / right: {title, beats: [{label, cue}]}, links: [{from, to, cue}])
  source(env, s, i, T) {
    const L = s.left, R = s.right, lx = CX - 235, rx = CX + 235, top = 500, bot = s.slam_text ? 1080 : 1200;
    const nb = Math.max(L.beats.length, R.beats.length), gy = nb > 1 ? (bot - top) / (nb - 1) : 0;
    const ly = k => top + k * gy, bc = (side, k, f) => cue(env, i, side.beats[k].cue, f) - T.start;
    const lc = L.beats.map((_, k) => bc(L, k, .3 + k * .25)), rc = R.beats.map((_, k) => bc(R, k, .5 + k * .25));
    const links = (s.links || []).map((x, k) => ({ ...x, c: cue(env, i, x.cue, 1.5 + k * .9) - T.start }));
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      const [sx, sy] = shake(lt, links.map(x => x.c + .45), 6);
      ctx.save(); ctx.translate(sx, sy);
      if (s.heading) wordsIn(ctx, s.heading, CX, 300, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 70, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      [[L, lx, GOLD, lc], [R, rx, TEAL, rc]].forEach(([side, x, col, cs], k) => {
        const dp = ep(lt, .1 + k * .15, .9 + k * .15, E.inOutCubic);
        ctx.save(); ctx.strokeStyle = rgba(col, .45); ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x, top - 40); ctx.lineTo(x, lerp(top - 40, bot + 40, dp)); ctx.stroke(); ctx.restore();
        const ts = fitSize(env, ctx, side.title, 'Anton', 400, 360, 64, 34);
        slam(ctx, side.title, x, 400, lt - .15 - k * .2, { size: ts, family: 'Anton', weight: 400, color: col, glow: rgba(col, .5), glowBlur: 30 });
        side.beats.forEach((b, j) => {
          const d = lt - cs[j], y = ly(j); if (d < 0) return;
          const p = ep(d, 0, .4, E.outBack), w = 340, h = 92, hit = links.some(x => (k ? x.to : x.from) === j && lt > x.c + .45);
          ctx.save(); ctx.translate(x + (1 - p) * (k ? 120 : -120), y); ctx.globalAlpha = clamp(d * 4);
          if (hit) { ctx.shadowColor = col; ctx.shadowBlur = 22 + 18 * beatPulse(env, t); }
          rrect(ctx, -w / 2, -h / 2, w, h, 20); ctx.fillStyle = hit ? rgba(col, .22) : '#12151B'; ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
          ctx.lineWidth = hit ? 5 : 3; ctx.strokeStyle = hit ? '#fff' : rgba(col, .8); ctx.stroke();
          const bs = fitSize(env, ctx, b.label, 'Inter', 900, w - 40, 40, 24);
          txt(ctx, b.label, 0, bs * .36, { size: bs, weight: 900, color: '#fff' });
          ctx.restore(); ctx.globalAlpha = 1;
        });
      });
      links.forEach(x => {                                   // a bright curve from the source beat to the film beat, a spark running along it
        const p = ep(lt, x.c, x.c + .5, E.inOutCubic); if (p <= 0) return;
        const ay = ly(x.from), by = ly(x.to), ax = lx + 170, bx = rx - 170, mx = (ax + bx) / 2;
        ctx.save(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.shadowColor = GOLD; ctx.shadowBlur = 24 + 20 * beatPulse(env, t);
        ctx.beginPath(); const N = 24;
        const pt = u => { const q = 1 - u; return [q * q * q * ax + 3 * q * q * u * mx + 3 * q * u * u * mx + u * u * u * bx, q * q * q * ay + 3 * q * q * u * ay + 3 * q * u * u * by + u * u * u * by]; };
        for (let k = 0; k <= N * p; k++) { const [px, py] = pt(k / N); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
        ctx.stroke();
        const [sx2, sy2] = pt((lt * .8) % 1); if (p >= 1) { ctx.fillStyle = GOLD; ctx.beginPath(); ctx.arc(sx2, sy2, 10, 0, 7); ctx.fill(); }
        ctx.restore();
        ring(ctx, bx, by, lt - x.c - .45, { color: TEAL, r0: 20, r1: 220, w: 8, d: .5 });
      });
      ctx.restore();
      if (s.slam_text) { const c = cue(env, i, s.slam_cue, T.end - T.start - 1.2) - T.start; slam(ctx, s.slam_text, CX, 1250, lt - c, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 100, 50), family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .6), glowBlur: 40, stroke: INK, strokeW: 10 }); }
    };
  },

  // ------------------------------------------------------------ BOARD (19 Nov): an evidence board. Clue cards are pinned one
  // by one and red string runs from each to one face in the middle (heading, center: {label, image, fx, fy}, clues: 3-5 of
  // {label, sub, image, cue}, slam_text, slam_cue). For "it all leads to one man", setup and payoff, hidden links.
  board(env, s, i, T) {
    const cl = s.clues, n = cl.length, cues = cl.map((c, k) => cue(env, i, c.cue, .5 + k * .9) - T.start);
    const cs = s.slam_cue ? cue(env, i, s.slam_cue) - T.start : cues[n - 1] + 1.4, X0 = 60, Y0 = 380, BW = 960, BH = 900;
    const cx = CX + 50, cy = 830, slots = [[-300, -300], [300, -300], [-300, 290], [300, 290], [0, -360]].slice(0, n);
    const specks = (() => { const r = rng(77), a = []; for (let k = 0; k < 420; k++) a.push([X0 + r() * BW, Y0 + r() * BH, 1 + r() * 3, r()]); return a; })();
    const card = (ctx, x, y, w, h, img, label, sub, rot, sc, col, o = {}) => {
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
      ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = 26; ctx.shadowOffsetY = 14; ctx.fillStyle = '#F4EFE4'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.shadowColor = 'transparent';
      const ih = img ? h - 74 : 0;
      if (img) { ctx.save(); ctx.beginPath(); ctx.rect(-w / 2 + 12, -h / 2 + 12, w - 24, ih - 12); ctx.clip(); cover(ctx, img, -w / 2 + 12, -h / 2 + 12, w - 24, ih - 12, { zoom: 1.1, fx: o.fx ?? .5, fy: o.fy ?? .35 }); ctx.restore(); }
      const ls = fitSize(env, ctx, label, 'Anton', 400, w - 30, img ? 40 : 52, 22);
      txt(ctx, label, 0, img ? h / 2 - 26 - (sub ? 12 : 0) : (sub ? -4 : ls * .36), { size: ls, family: 'Anton', weight: 400, color: '#1B1B1B' });
      if (sub) txt(ctx, sub, 0, img ? h / 2 - 12 : 34, { size: 22, weight: 800, color: '#7A2B22', ls: .1 });
      ctx.beginPath(); ctx.arc(0, -h / 2 + 4, 11, 0, 7); ctx.fillStyle = col; ctx.fill(); ctx.beginPath(); ctx.arc(-3, -h / 2, 4, 0, 7); ctx.fillStyle = 'rgba(255,255,255,.7)'; ctx.fill();
      ctx.restore();
    };
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (s.heading) wordsIn(ctx, s.heading, CX, 320, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 74, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const push = 1 + .05 * ep(lt, 0, T.end - T.start, E.linear) + .05 * ep(lt, cs, cs + .6, E.outBack);
      const [sx, sy] = shake(lt, cues.map(c => c + .3).concat([cs]), 7);
      ctx.save(); ctx.translate(cx + sx, cy + sy); ctx.scale(push, push); ctx.translate(-cx, -cy);
      ctx.globalAlpha = ep(lt, 0, .4);                       // the cork board in its wooden frame
      rrect(ctx, X0 - 16, Y0 - 16, BW + 32, BH + 32, 18); ctx.fillStyle = '#3A2414'; ctx.fill();
      rrect(ctx, X0, Y0, BW, BH, 8); ctx.fillStyle = '#7B5532'; ctx.fill();
      specks.forEach(([x, y, r, a]) => { ctx.fillStyle = a > .5 ? 'rgba(40,22,10,.35)' : 'rgba(200,160,110,.25)'; ctx.fillRect(x, y, r, r); });
      radial(ctx, cx, cy, 700, [[0, 'rgba(255,220,160,.18)'], [1, 'rgba(0,0,0,.35)']], [X0, Y0, BW, BH]);
      ctx.globalAlpha = 1;
      const pins = slots.map(([dx, dy]) => [cx + dx, cy + dy - 85]);
      cl.forEach((c, k) => {                                // red string first, so the cards sit on top
        const d = lt - cues[k] - .35, p = ep(d, 0, .55, E.inOutCubic); if (p <= 0) return;
        const [ax, ay] = pins[k], bx = cx, by = cy - 175, ex = lerp(ax, bx, p), ey = lerp(ay, by, p);
        ctx.save(); ctx.strokeStyle = '#E0281E'; ctx.lineWidth = 5; ctx.shadowColor = 'rgba(255,60,40,.8)'; ctx.shadowBlur = lt > cs ? 22 + 16 * beatPulse(env, t) : 8;
        ctx.beginPath(); ctx.moveTo(ax, ay); ctx.quadraticCurveTo((ax + ex) / 2, (ay + ey) / 2 + 40 * p, ex, ey); ctx.stroke(); ctx.restore();
      });
      const cimg = s.center && s.center.image ? env.img[s.center.image] : null, cin = ep(lt, .15, .7, E.outBack);
      card(ctx, cx, cy, 300, 360, cimg, (s.center || {}).label || '?', (s.center || {}).sub, -.02 + Math.sin(lt * .7) * .01, cin, '#E0281E', s.center || {});
      cl.forEach((c, k) => {
        const d = lt - cues[k]; if (d < 0) return;
        const p = ep(d, 0, .4, E.outBack), [dx, dy] = slots[k];
        card(ctx, cx + dx, cy + dy - (1 - p) * 120, 240, c.image ? 250 : 160, c.image ? env.img[c.image] : null, c.label, c.sub, (k % 2 ? .06 : -.06) + Math.sin(lt * .8 + k) * .008, lerp(1.35, 1, p), '#F2C230', c);
        ring(ctx, cx + dx, cy + dy - 85, d - .3, { color: '#F2C230', r0: 10, r1: 160, w: 6, d: .45 });
      });
      ctx.restore();
      if (s.slam_text && lt > cs) {                          // a red stamp across the face in the middle
        const p = ep(lt, cs, cs + .3, E.outBack);
        ctx.save(); ctx.translate(cx, cy + 150); ctx.rotate(-.12); ctx.scale(lerp(2.2, 1, p), lerp(2.2, 1, p)); ctx.globalAlpha = clamp(p * 2);
        const ss = fitSize(env, ctx, s.slam_text, 'Anton', 400, 620, 96, 44); setFont(ctx, ss, 'Anton', 400, .04);
        const w = ctx.measureText(s.slam_text).width + 60; ctx.lineWidth = 8; ctx.strokeStyle = '#E0281E'; rrect(ctx, -w / 2, -ss * .85, w, ss * 1.3, 12); ctx.stroke();
        txt(ctx, s.slam_text, 0, ss * .2, { size: ss, family: 'Anton', weight: 400, color: '#E0281E', ls: .04 });
        ctx.restore(); ctx.globalAlpha = 1;
      }
    };
  },

  // ------------------------------------------------------------ CLIMB (19 Nov): a staircase in the city; a figure climbs it
  // heavily (cold light, rain) or dances down it (warm light, sparks). For a character's arc told by direction (heading,
  // phases: 1-2 of {dir: up|down, label, sub, cue}, steps, slam_text, slam_cue)
  climb(env, s, i, T) {
    const ph = s.phases, pc = ph.map((p, k) => cue(env, i, p.cue, .3 + k * 3) - T.start), N = s.steps || 10;
    const cs = s.slam_cue ? cue(env, i, s.slam_cue) - T.start : 1e9, B = [130, 1190], Tp = [880, 470];
    const city = (() => { const r = rng(31), a = []; let x = 0; while (x < W) { const w = 70 + r() * 110, h = 260 + r() * 520; a.push([x, w, h, Array.from({ length: 30 }, () => r())]); x += w + 6; } return a; })();
    const rain = (() => { const r = rng(9), a = []; for (let k = 0; k < 140; k++) a.push([r() * W, r() * H, .6 + r() * .8]); return a; })();
    const stepPos = f => [lerp(B[0], Tp[0], f), lerp(B[1], Tp[1], f)];
    const figure = (ctx, x, y, mode, tt, col) => {          // a simple silhouette with a walk or dance cycle
      const up = mode === 'up', sw = Math.sin(tt * (up ? 7 : 12)), lean = up ? .38 : -.12 + .1 * Math.sin(tt * 6);
      ctx.save(); ctx.translate(x, y); ctx.scale(1.7, 1.7); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 15;
      ctx.shadowColor = up ? 'rgba(120,200,220,.5)' : 'rgba(255,90,40,.9)'; ctx.shadowBlur = up ? 10 : 30;
      const hipY = -95 - (up ? 0 : Math.abs(sw) * 12), sh = [Math.sin(lean) * 85, hipY - Math.cos(lean) * 85];
      ctx.beginPath(); ctx.moveTo(-14 * sw, 0); ctx.lineTo(0, hipY); ctx.lineTo(14 * sw, 0); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, hipY); ctx.lineTo(sh[0], sh[1]); ctx.stroke();
      ctx.beginPath(); ctx.arc(sh[0] + Math.sin(lean) * 26, sh[1] - Math.cos(lean) * 26 + (up ? 10 : 0), 22, 0, 7); ctx.fill();
      ctx.lineWidth = 12;
      if (up) { ctx.beginPath(); ctx.moveTo(sh[0], sh[1]); ctx.lineTo(sh[0] + 10 + 8 * sw, sh[1] + 70); ctx.moveTo(sh[0], sh[1]); ctx.lineTo(sh[0] - 4 - 8 * sw, sh[1] + 72); ctx.stroke(); }
      else { const a1 = -2.2 + .6 * sw, a2 = -.9 - .6 * sw; ctx.beginPath(); ctx.moveTo(sh[0], sh[1]); ctx.lineTo(sh[0] + Math.cos(a1) * 72, sh[1] + Math.sin(a1) * 72); ctx.moveTo(sh[0], sh[1]); ctx.lineTo(sh[0] + Math.cos(a2) * 72, sh[1] + Math.sin(a2) * 72); ctx.stroke(); }
      ctx.restore();
    };
    return (ctx, lt, t) => {
      const cur = ph.reduce((a, p, k) => (lt >= pc[k] ? k : a), 0), P = ph[cur], up = P.dir !== 'down';
      const warm = ep(lt, pc[cur] - .2, pc[cur] + .6) * (up ? 0 : 1) + (up ? 0 : 0);
      fill(ctx, INK);
      radial(ctx, W / 2, 300, 1500, [[0, up ? 'rgba(90,140,160,.28)' : `rgba(255,${110 - 40 * warm | 0},50,${.18 + .2 * warm})`], [1, 'rgba(0,0,0,0)']]);
      city.forEach(([x, w, h, win]) => {                    // the city behind, windows lit
        ctx.fillStyle = '#0D1117'; ctx.fillRect(x, 1250 - h, w, h);
        win.forEach((r, k) => { if (r > .62) { ctx.fillStyle = up ? `rgba(160,200,210,${.15 + .2 * r})` : `rgba(255,190,110,${.2 + .3 * r})`; ctx.fillRect(x + 12 + (k % 3) * (w - 30) / 3, 1250 - h + 24 + Math.floor(k / 3) * 46, 14, 20); } });
      });
      const steps = N, sw = (Tp[0] - B[0]) / steps, shh = (B[1] - Tp[1]) / steps;
      for (let k = 0; k < steps; k++) {                     // the stairs: treads with a lit edge, and a rail
        const x = B[0] + k * sw, y = B[1] - (k + 1) * shh;
        ctx.fillStyle = '#20262E'; ctx.fillRect(x, y, W - x + 40, shh + 2);
        ctx.fillStyle = up ? 'rgba(150,200,215,.55)' : 'rgba(255,150,80,.75)'; ctx.fillRect(x, y, sw + 4, 5);
      }
      ctx.strokeStyle = up ? 'rgba(170,210,220,.5)' : 'rgba(255,170,100,.7)'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(B[0] - 20, B[1] - 170); ctx.lineTo(Tp[0] - 20, Tp[1] - 170); ctx.stroke();
      for (let k = 0; k <= steps; k += 2) { const [x, y] = stepPos(k / steps); ctx.beginPath(); ctx.moveTo(x - 20, y - 170 + 0); ctx.lineTo(x - 20, y); ctx.stroke(); }
      // the walk: slow and heavy going up, quick and bouncing coming down
      const d0 = pc[cur], d1 = cur + 1 < ph.length ? pc[cur + 1] : T.end - T.start, dur = Math.max(1, d1 - d0 - .2);
      let f = ep(lt, d0, d0 + dur * (up ? 1 : .9), up ? E.inOutQuad : E.linear); f = up ? f : 1 - f;
      if (lt < pc[0]) f = up ? 0 : 1;
      const stepF = Math.floor(f * steps) / steps, sub = f * steps % 1, [fx, fy] = stepPos(stepF + sub / steps);
      figure(ctx, fx + 30, fy - (up ? 0 : Math.abs(Math.sin(lt * 12)) * 18), up ? 'up' : 'down', lt, up ? '#7E97A3' : '#E8432E');
      if (up && s.rain !== false) {                         // rain on the climb (rain: false to turn off)
        ctx.save(); ctx.strokeStyle = 'rgba(180,210,230,.28)'; ctx.lineWidth = 2;
        rain.forEach(([x, y, v]) => { const yy = (y + lt * 900 * v) % H; ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(x - 8, yy + 34); ctx.stroke(); }); ctx.restore();
      } else dust(env, ctx, t, { n: 60, color: 'rgba(255,170,90,1)', alpha: .55, min: 3, max: 9, rise: 60, seed: 5 });
      // the big arrow beside the stairs: which way the story goes
      const ax = 1000, ay0 = up ? 1100 : 520, ay1 = up ? 560 : 1060, ap = ep(lt, d0 + .2, d0 + 1, E.inOutCubic);
      ctx.save(); ctx.strokeStyle = up ? TEAL : '#FF5A3C'; ctx.fillStyle = ctx.strokeStyle; ctx.lineWidth = 14; ctx.lineCap = 'round'; ctx.shadowColor = ctx.strokeStyle; ctx.shadowBlur = 24;
      const ey = lerp(ay0, ay1, ap); ctx.beginPath(); ctx.moveTo(ax, ay0); ctx.lineTo(ax, ey); ctx.stroke();
      if (ap > .05) { const dir = up ? -1 : 1; ctx.beginPath(); ctx.moveTo(ax - 30, ey - dir * 34); ctx.lineTo(ax, ey + dir * 6); ctx.lineTo(ax + 30, ey - dir * 34); ctx.closePath(); ctx.fill(); }
      ctx.restore();
      if (s.heading) wordsIn(ctx, s.heading, CX, 300, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 70, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const lab = P.label, ls = fitSize(env, ctx, lab, 'Anton', 400, 560, 110, 50);
      slam(ctx, lab, 330, 420, lt - pc[cur] - .1, { size: ls, family: 'Anton', weight: 400, color: up ? '#CFE3EA' : '#FF5A3C', glow: up ? rgba(TEAL, .5) : 'rgba(255,90,60,.7)', glowBlur: 40 });
      if (P.sub) pill(ctx, P.sub, 330, 490, lt - pc[cur] - .45, { size: 30, bg: up ? 'rgba(207,227,234,.92)' : '#FF5A3C', color: INK, ls: .1 });
      if (s.slam_text) { slam(ctx, s.slam_text, CX, 1290, lt - cs, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 104, 50), family: 'Anton', weight: 400, color: '#fff', glow: 'rgba(255,90,60,.7)', glowBlur: 40, stroke: INK, strokeW: 10 }); flash(ctx, lt, cs, { alpha: .25 }); }
    };
  },

  // ------------------------------------------------------------ TRACK (19 Nov): a race circuit or a route draws itself; a car
  // laps it with a light trail while a speed counter climbs; markers pop on their word (heading, shape: circuit | route,
  // points: [[x, y] 0-1] for your own route, lap seconds, start_cue, speed: {from, to, unit, cue}, markers: [{at 0-1, label, cue}])
  track(env, s, i, T) {
    const SH = { circuit: [[.18, .82], [.1, .62], [.16, .42], [.32, .36], [.42, .2], [.6, .14], [.86, .2], [.9, .38], [.74, .48], [.82, .66], [.66, .86], [.4, .9]],
                 route: [[.12, .88], [.3, .7], [.22, .5], [.45, .42], [.58, .22], [.86, .12]] };
    const raw = s.points || SH[s.shape || 'circuit'], closed = !s.points && (s.shape || 'circuit') === 'circuit';
    const bx = 110, by = 470, bw = 760, bh = 700, pts = raw.map(([x, y]) => [bx + x * bw, by + y * bh]);
    const path = (() => {                                   // smooth the corners (Catmull-Rom), then measure the length
      const P = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]], out = [];
      for (let k = 1; k < P.length - 2; k++) for (let u = 0; u < 1; u += .05) {
        const [p0, p1, p2, p3] = [P[k - 1], P[k], P[k + 1], P[k + 2]], u2 = u * u, u3 = u2 * u;
        out.push([0, 1].map(j => .5 * (2 * p1[j] + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3)));
      }
      if (closed) out.push(out[0]);
      const L = [0]; for (let k = 1; k < out.length; k++) L.push(L[k - 1] + Math.hypot(out[k][0] - out[k - 1][0], out[k][1] - out[k - 1][1]));
      return { pts: out, L, total: L[L.length - 1] };
    })();
    const at = f => { f = ((f % 1) + 1) % 1; const d = f * path.total; let k = path.L.findIndex(v => v >= d); k = Math.max(1, k);
      const a = path.pts[k - 1], b = path.pts[k], u = (d - path.L[k - 1]) / Math.max(1e-6, path.L[k] - path.L[k - 1]);
      return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), Math.atan2(b[1] - a[1], b[0] - a[0])]; };
    const st = cue(env, i, s.start_cue, .9) - T.start, lap = s.lap || 4.5, mk = (s.markers || []).map((m, k) => ({ ...m, c: cue(env, i, m.cue, 1.5 + k) - T.start }));
    const sp = s.speed, spc = sp ? cue(env, i, sp.cue, st) - T.start : 0;
    const line = (ctx, upto, w, col) => { ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath();
      const n = Math.max(2, Math.floor(path.pts.length * upto)); path.pts.slice(0, n).forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); };
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (s.heading) wordsIn(ctx, s.heading, CX, 320, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 74, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const dr = ep(lt, .1, 1.3, E.inOutCubic);
      ctx.save(); ctx.shadowColor = GOLD; ctx.shadowBlur = 30; line(ctx, dr, 58, rgba(GOLD, .35)); ctx.restore();
      line(ctx, dr, 46, '#1A1D22'); ctx.setLineDash([18, 16]); line(ctx, dr, 3, 'rgba(255,255,255,.35)'); ctx.setLineDash([]);
      if (dr >= 1) {                                         // start line, chequered
        const [x, y, a] = at(0); ctx.save(); ctx.translate(x, y); ctx.rotate(a + Math.PI / 2);
        for (let r = 0; r < 2; r++) for (let c = -3; c < 3; c++) { ctx.fillStyle = (r + c) % 2 ? '#fff' : '#111'; ctx.fillRect(c * 8, r * 8 - 8, 8, 8); } ctx.restore();
      }
      mk.forEach(m => {
        const d = lt - m.c; if (d < 0) return; const [x, y] = at(m.at);
        ring(ctx, x, y, d, { color: TEAL, r0: 10, r1: 150, w: 7, d: .5 });
        ctx.beginPath(); ctx.arc(x, y, 14, 0, 7); ctx.fillStyle = TEAL; ctx.fill();
        pill(ctx, m.label, clamp(x, 210, 770), y + (y > by + bh / 2 ? -70 : 70), d - .1, { size: 32, bg: TEAL, color: INK, ls: .08 });
      });
      if (lt > st) {                                         // the car: a light trail, then the car itself facing its way
        const f = (lt - st) / lap, sp2 = Math.min(1, (lt - st) / 1.2);
        for (let k = 14; k >= 1; k--) { const [x, y] = at(f - k * .006 * sp2); ctx.beginPath(); ctx.arc(x, y, 18 - k * .9, 0, 7); ctx.fillStyle = rgba(GOLD, .5 * (1 - k / 15)); ctx.fill(); }
        const [x, y, a] = at(f); ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.scale(1.8, 1.8); ctx.shadowColor = GOLD; ctx.shadowBlur = 24;
        ctx.fillStyle = '#111'; [[-18, -16], [-18, 10], [16, -16], [16, 10]].forEach(([wx, wy]) => ctx.fillRect(wx, wy, 13, 7));
        ctx.fillStyle = GOLD; rrect(ctx, -28, -7, 58, 14, 7); ctx.fill(); ctx.fillRect(28, -14, 6, 28); ctx.fillRect(-32, -12, 6, 24);
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(2, 0, 5, 0, 7); ctx.fill(); ctx.restore();
      }
      if (sp) {
        const v = Math.round(lerp(sp.from || 0, sp.to, ep(lt, spc, spc + 2.2, E.outCubic))), p = ep(lt, spc - .2, spc + .2);
        if (p > 0) { txt(ctx, String(v), 700, 1300, { size: 150, family: 'Anton', weight: 400, color: '#fff', glow: rgba(GOLD, .6), glowBlur: 30, alpha: p, align: 'right' });
          txt(ctx, sp.unit || 'KM/H', 715, 1300, { size: 46, family: 'Anton', weight: 400, color: GOLD, alpha: p, align: 'left' }); }
      }
    };
  },

  // ------------------------------------------------------------ LAYERS (19 Nov): what is under the surface. Slabs drop into a
  // stack one by one, then lift apart with a label each (heading, layers: 2-4 of {label, sub, cue}, bottom first; split_cue,
  // slam_text, slam_cue). For a car under its bodywork, a set built in layers, sound layers, a story in layers.
  layers(env, s, i, T) {
    const ly = s.layers, n = ly.length, cues = ly.map((l, k) => cue(env, i, l.cue, .4 + k * .8) - T.start);
    const sp = s.split_cue ? cue(env, i, s.split_cue) - T.start : cues[n - 1] + 1, cs = s.slam_cue ? cue(env, i, s.slam_cue) - T.start : 1e9;
    const cx = 380, base = 1150, Wd = 600, Dp = 320, Th = 60;
    const slab = (ctx, y, col, a, glow) => {
      const top = [[cx, y - Dp / 2], [cx + Wd / 2, y], [cx, y + Dp / 2], [cx - Wd / 2, y]];
      ctx.save(); ctx.globalAlpha = a; if (glow) { ctx.shadowColor = col; ctx.shadowBlur = glow; }
      ctx.fillStyle = rgba(col, .22); ctx.beginPath(); ctx.moveTo(top[3][0], top[3][1]); ctx.lineTo(top[2][0], top[2][1]); ctx.lineTo(top[2][0], top[2][1] + Th); ctx.lineTo(top[3][0], top[3][1] + Th); ctx.closePath(); ctx.fill();
      ctx.fillStyle = rgba(col, .34); ctx.beginPath(); ctx.moveTo(top[2][0], top[2][1]); ctx.lineTo(top[1][0], top[1][1]); ctx.lineTo(top[1][0], top[1][1] + Th); ctx.lineTo(top[2][0], top[2][1] + Th); ctx.closePath(); ctx.fill();
      ctx.fillStyle = rgba(col, .5); ctx.beginPath(); top.forEach(([x, yy], k) => k ? ctx.lineTo(x, yy) : ctx.moveTo(x, yy)); ctx.closePath(); ctx.fill();
      ctx.lineWidth = 3; ctx.strokeStyle = col; ctx.stroke(); ctx.restore(); ctx.globalAlpha = 1;
    };
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (s.heading) wordsIn(ctx, s.heading, CX, 320, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 74, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const split = ep(lt, sp, sp + .8, E.inOutCubic), [sx, sy] = shake(lt, cues.map(c => c + .35), 6);
      ctx.save(); ctx.translate(sx, sy);
      ly.forEach((l, k) => {
        const d = lt - cues[k]; if (d < 0) return;
        const fall = ep(d, 0, .4, E.outBack), y = base - k * (Th + 6) - split * k * 210 - (1 - fall) * 500;
        const col = [GOLD, TEAL, '#FFFFFF', '#FF6B5E'][k % 4], hot = lt > cs && k === n - 1;
        slab(ctx, y, col, clamp(d * 5), hot ? 40 + 30 * beatPulse(env, t) : 14);
        const lp = ep(lt, Math.max(sp, cues[k]) + .2 + k * .12, Math.max(sp, cues[k]) + .6 + k * .12);
        if (lp > 0) {                                         // a leader line out to the label
          ctx.save(); ctx.globalAlpha = lp; ctx.strokeStyle = col; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx + Wd / 2, y); ctx.lineTo(cx + Wd / 2 + 60 * lp, y); ctx.stroke(); ctx.restore();
          const ls = fitSize(env, ctx, l.label, 'Anton', 400, 330, 56, 28);
          txt(ctx, l.label, cx + Wd / 2 + 74, y + ls * .2, { size: ls, family: 'Anton', weight: 400, color: '#fff', align: 'left', alpha: lp });
          if (l.sub) txt(ctx, l.sub, cx + Wd / 2 + 76, y + ls * .2 + 36, { size: 24, weight: 800, color: col, align: 'left', alpha: lp, ls: .08 });
        }
      });
      ctx.restore();
      if (s.slam_text) { slam(ctx, s.slam_text, CX, 1300, lt - cs, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 100, 50), family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .6), glowBlur: 40, stroke: INK, strokeW: 10 }); }
    };
  },

  // ------------------------------------------------------------ SCENE (Harish, 22 Nov): the custom visual for each film,
  // drawn from the plan, no new code. Props (drawn icons) stand in a box, move along paths, and act on the voice's words.
  // Fields: heading · ground (floor|road|rail|water|city|sky|map|grid|none) · scroll (px/s for road and rail) ·
  // props: 1-8 of {id, icon, x, y (0-1 in the box), size, count, gap, flip, color (accent|second|white|red), label (≤3 words),
  //   label_at (below|above), cue, enter (pop|drop|slide|rise|fade), path [[x, y] 2-8 points], move (s), move_cue, trail, face,
  //   loop, acts: [{do: fall|shake|blast|light|spin|grow|fade|pulse|swap, cue, to, icon, copy}]} ·
  // links: [{from, to, cue, style (line|string|beam|arrow), label}] · focus {on, to (1.1-1.6), cue, d} ·
  // counter {from, to, unit, cue, d, x, y} · slam_text, slam_cue. Same plan, same frames: everything is a function of time.
  scene(env, s, i, T) {
    const bx = 90, by = 450, bw = 800, bh = 780, X = x => bx + x * bw, Y = y => by + y * bh, RED = '#FF5A4E', U = 1.6;   // size 1 = a 160 px icon
    const COL = { accent: GOLD, second: TEAL, white: '#FFFFFF', red: RED };
    const at = (c, f) => cue(env, i, c, f) - T.start;
    const smooth = (raw, closed) => {                    // Catmull-Rom through the points, measured for even speed
      const pts = raw.map(([x, y]) => [X(x), Y(y)]);
      if (pts.length < 2) return null;
      const P = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]], out = [];
      for (let k = 1; k < P.length - 2; k++) for (let u = 0; u < 1; u += .05) {
        const [p0, p1, p2, p3] = [P[k - 1], P[k], P[k + 1], P[k + 2]], u2 = u * u, u3 = u2 * u;
        out.push([0, 1].map(j => .5 * (2 * p1[j] + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3)));
      }
      out.push(closed ? out[0] : pts[pts.length - 1]);
      const L = [0]; for (let k = 1; k < out.length; k++) L.push(L[k - 1] + Math.hypot(out[k][0] - out[k - 1][0], out[k][1] - out[k - 1][1]));
      const total = Math.max(1e-6, L[L.length - 1]);
      return { pts: out, L, total, at: f => {
        f = clamp(f); const d = f * total; let k = L.findIndex(v => v >= d); k = Math.max(1, k < 0 ? L.length - 1 : k);
        const a = out[k - 1], b = out[k], u = (d - L[k - 1]) / Math.max(1e-6, L[k] - L[k - 1]);
        return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), Math.atan2(b[1] - a[1], b[0] - a[0])]; } };
    };
    const props = (s.props || []).map((p, k) => {
      const c0 = at(p.cue, .25 + k * .3), path = Array.isArray(p.path) ? smooth(p.path, !!p.loop) : null;
      return { ...p, k, c0, path, mc: p.move_cue ? at(p.move_cue) : c0 + .35, mv: p.move || 2.6, lc: p.label_cue ? at(p.label_cue) : c0 + .35,
        acts: (p.acts || []).map(a => ({ ...a, c: at(a.cue, c0 + 1.2) })), col: COL[p.color] || (k === 0 ? GOLD : TEAL) };
    });
    const byId = Object.fromEntries(props.filter(p => p.id).map(p => [p.id, p]));
    const hits = [];
    props.forEach(p => p.acts.forEach(a => { if (a.do === 'blast' || a.do === 'shake') hits.push(a.c); }));
    const links = (s.links || []).map(l => ({ ...l, c: at(l.cue, 1.4) }));
    const fo = s.focus, fc = fo ? at(fo.cue, 1) : 1e9, cs = s.slam_cue ? at(s.slam_cue) : 1e9, ct = s.counter ? at(s.counter.cue, .6) : 0;

    // ---- the icons: drawn in a 100 px box around (0, 0), facing right; g strokes in the prop's colour with a glow
    const ICONS = {
      camera: g => { g.box(-44, -20, 60, 46, 8); g.circ(-30, -36, 13); g.circ(-2, -36, 13); g.poly([[16, -10], [46, -24], [46, 22], [16, 8]]); g.dot(-14, 3, 9); },
      film: g => { g.box(-46, -26, 92, 52, 4); for (let x = -38; x <= 34; x += 18) { g.sq(x, -21, 7); g.sq(x, 14, 7); } g.line([[-46, -10], [46, -10]]); g.line([[-46, 9], [46, 9]]); },
      clapper: g => { g.box(-40, -8, 80, 44, 4); g.poly([[-40, -10], [36, -34], [40, -22], [-36, 2]]); g.line([[-20, -15], [-8, -26]]); g.line([[2, -21], [14, -31]]); },
      mic: g => { g.box(-13, -46, 26, 48, 13); g.arc(0, -6, 24, 0, Math.PI); g.line([[0, 18], [0, 40]]); g.line([[-20, 42], [20, 42]]); },
      spotlight: g => { g.beam([[-14, -20], [14, -20], [60, 50], [-60, 50]]); g.poly([[-22, -44], [22, -44], [14, -18], [-14, -18]]); g.line([[0, -44], [0, -54]]); },
      screen: g => { g.box(-48, -34, 96, 60, 4); g.line([[-14, 26], [-20, 42]]); g.line([[14, 26], [20, 42]]); g.line([[-28, 42], [28, 42]]); },
      person: g => { g.circ(0, -36, 13); g.line([[0, -22], [0, 14]]); g.line([[-22, -6], [0, -14], [22, -6]]); g.line([[-15, 46], [0, 14], [15, 46]]); },
      runner: g => { g.circ(8, -38, 13); g.line([[4, -24], [-4, 10]]); g.line([[-24, -4], [0, -16], [20, -24]]); g.line([[-26, 30], [-4, 10], [16, 30], [10, 46]]); },
      crowd: g => { [-30, 0, 30].forEach((x, k) => { const y = k === 1 ? -6 : 4; g.circ(x, y - 26, 10); g.line([[x, y - 15], [x, y + 14]]); g.line([[x - 12, y + 40], [x, y + 14], [x + 12, y + 40]]); }); },
      car: g => { g.poly([[-48, 14], [-48, -2], [-24, -6], [-12, -24], [20, -24], [32, -6], [48, -2], [48, 14]]); g.circ(-28, 16, 10); g.circ(28, 16, 10); g.line([[-8, -22], [-8, -6]]); },
      racecar: g => { g.poly([[-48, 10], [-40, -4], [-4, -8], [8, -18], [22, -8], [44, -4], [50, 10]]); g.line([[-50, -14], [-50, 4]]); g.line([[-56, -14], [-42, -14]]); g.circ(-30, 14, 11); g.circ(32, 14, 11); },
      bike: g => { g.circ(-28, 18, 18); g.circ(28, 18, 18); g.line([[-28, 18], [-6, -12], [16, -12], [28, 18]]); g.line([[-6, -12], [2, 18], [16, -12]]); g.line([[14, -22], [22, -22]]); },
      train: g => { g.box(-48, -26, 64, 48, 4); g.box(-6, -44, 22, 20, 3); g.poly([[16, -14], [44, -6], [44, 22], [16, 22]]); g.circ(-32, 26, 9); g.circ(-4, 26, 9); g.circ(28, 26, 9); g.sq(-40, -16, 14); },
      coach: g => { g.box(-48, -26, 96, 46, 6); [-34, -10, 14].forEach(x => g.sq(x, -16, 16)); g.circ(-30, 24, 8); g.circ(30, 24, 8); },
      plane: g => { g.poly([[-50, 0], [-30, -8], [40, -6], [52, 0], [40, 6], [-30, 8]]); g.poly([[4, -6], [-14, -42], [-2, -42], [22, -6]]); g.poly([[4, 6], [-14, 42], [-2, 42], [22, 6]]); g.poly([[-44, -2], [-50, -20], [-40, -20], [-32, -6]]); },
      boat: g => { g.poly([[-48, 10], [48, 10], [34, 30], [-34, 30]]); g.line([[0, 10], [0, -46]]); g.poly([[4, -42], [36, 4], [4, 4]]); },
      bridge: g => { g.line([[-60, -6], [60, -6]]); g.line([[-60, 2], [60, 2]]); [-40, 0, 40].forEach(x => { g.line([[x, 2], [x, 44]]); }); g.arc(-20, 44, 20, Math.PI, 0); g.arc(20, 44, 20, Math.PI, 0); },
      building: g => { g.box(-30, -50, 60, 100, 2); for (let y = -40; y < 40; y += 16) for (let x = -20; x <= 10; x += 14) g.sq(x, y, 8); },
      house: g => { g.poly([[-40, -6], [0, -40], [40, -6]]); g.box(-32, -6, 64, 46, 2); g.box(-8, 14, 16, 26, 2); },
      tree: g => { g.line([[0, 46], [0, 4]]); g.circ(0, -18, 28); g.circ(-18, -4, 16); g.circ(18, -4, 16); },
      mountain: g => { g.poly([[-54, 40], [-14, -30], [10, 8], [24, -12], [56, 40]]); g.line([[-24, -12], [-14, -30], [-4, -14]]); },
      sun: g => { g.circ(0, 0, 22); for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; g.line([[Math.cos(a) * 32, Math.sin(a) * 32], [Math.cos(a) * 46, Math.sin(a) * 46]]); } },
      moon: g => { g.crescent(0, 0, 34); },
      star: g => { g.poly([...Array(10)].map((_, k) => { const a = -Math.PI / 2 + k * Math.PI / 5, r = k % 2 ? 18 : 44; return [Math.cos(a) * r, Math.sin(a) * r]; })); },
      cloud: g => { g.cloud(); },
      rain: g => { g.cloud(); [-24, -4, 16].forEach(x => g.line([[x, 30], [x - 8, 48]])); },
      fire: g => { g.flame(); },
      bomb: g => { g.circ(-6, 8, 30); g.line([[14, -14], [24, -28], [36, -30]]); g.dot(40, -32, 6); },
      blast: g => { g.poly([...Array(16)].map((_, k) => { const a = k * Math.PI / 8, r = k % 2 ? 22 : 50; return [Math.cos(a) * r, Math.sin(a) * r]; })); },
      gun: g => { g.poly([[-44, -16], [40, -16], [40, -4], [-6, -4], [-14, 30], [-32, 30], [-26, -4], [-44, -4]]); g.line([[-6, -4], [-2, 8], [-12, 8]]); },
      knife: g => { g.poly([[-8, -8], [48, -8], [24, 8], [-8, 8]]); g.box(-46, -8, 36, 16, 6); },
      phone: g => { g.box(-24, -46, 48, 92, 9); g.box(-17, -36, 34, 62, 3); g.dot(0, 36, 4); },
      clock: g => { g.circ(0, 0, 40); g.hand(0, 0, 28, g.t * 2.4); g.hand(0, 0, 18, g.t * .2); g.dot(0, 0, 4); },
      hourglass: g => { g.poly([[-26, -42], [26, -42], [0, 0]]); g.poly([[-26, 42], [26, 42], [0, 0]]); g.line([[-32, -46], [32, -46]]); g.line([[-32, 46], [32, 46]]); },
      heart: g => { g.heart(); },
      eye: g => { g.eye(); },
      crown: g => { g.poly([[-40, 24], [-44, -24], [-20, 0], [0, -32], [20, 0], [44, -24], [40, 24]]); g.dot(0, -32, 5); },
      key: g => { g.circ(-26, 0, 16); g.line([[-10, 0], [44, 0]]); g.line([[30, 0], [30, 14]]); g.line([[40, 0], [40, 12]]); },
      lock: g => { g.box(-28, -6, 56, 46, 6); g.arc(0, -6, 18, Math.PI, 0); g.line([[-18, -6], [-18, -6]]); g.dot(0, 14, 6); },
      door: g => { g.box(-26, -48, 52, 96, 3); g.dot(14, 4, 5); },
      book: g => { g.poly([[-46, -30], [0, -22], [0, 34], [-46, 26]]); g.poly([[46, -30], [0, -22], [0, 34], [46, 26]]); },
      letter: g => { g.box(-44, -28, 88, 56, 4); g.line([[-44, -28], [0, 6], [44, -28]]); },
      note: g => { g.circ(-14, 26, 13); g.line([[-2, 26], [-2, -40], [26, -28], [26, -14]]); },
      trophy: g => { g.poly([[-26, -40], [26, -40], [20, 0], [-20, 0]]); g.arc(-26, -26, 12, Math.PI / 2, Math.PI * 1.5); g.arc(26, -26, 12, -Math.PI / 2, Math.PI / 2); g.line([[0, 0], [0, 24]]); g.box(-20, 24, 40, 14, 3); },
      flag: g => { g.line([[-30, 46], [-30, -46]]); g.wave(-30, -44, 66, 40); },
      skull: g => { g.circ(0, -8, 32); g.box(-16, 18, 32, 18, 4); g.dot(-12, -8, 8); g.dot(12, -8, 8); },
      mask: g => { g.mask(); },
      throne: g => { g.poly([[-26, -48], [26, -48], [26, 10], [-26, 10]]); g.box(-34, 6, 68, 14, 3); g.line([[-30, 20], [-30, 46]]); g.line([[30, 20], [30, 46]]); },
      ball: g => { g.circ(0, 0, 36); g.poly([[0, -14], [13, -4], [8, 12], [-8, 12], [-13, -4]]); },
      ticket: g => { g.ticket(); },
      question: g => { g.circ(0, 0, 40); g.glyph('?'); },
      exclaim: g => { g.circ(0, 0, 40); g.glyph('!'); },
      check: g => { g.line([[-30, 0], [-8, 24], [32, -24]]); },
      cross: g => { g.line([[-28, -28], [28, 28]]); g.line([[28, -28], [-28, 28]]); },
      arrow: g => { g.line([[-44, 0], [36, 0]]); g.poly([[20, -18], [46, 0], [20, 18]]); },
      target: g => { g.circ(0, 0, 40); g.circ(0, 0, 24); g.dot(0, 0, 9); },
      pin: g => { g.pin(); },
      dot: g => { g.dot(0, 0, 16); },
    };
    const painter = (ctx, col, t) => {
      const st = () => { ctx.fillStyle = rgba(col, .16); ctx.fill(); ctx.stroke(); };
      return {
        t,
        box: (x, y, w, h, r) => { rrect(ctx, x, y, w, h, r); st(); },
        sq: (x, y, w) => { ctx.beginPath(); ctx.rect(x, y, w, w); ctx.fillStyle = rgba(col, .6); ctx.fill(); },
        circ: (x, y, r) => { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); st(); },
        dot: (x, y, r) => { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill(); },
        arc: (x, y, r, a0, a1) => { ctx.beginPath(); ctx.arc(x, y, r, a0, a1); ctx.stroke(); },
        line: pts => { ctx.beginPath(); pts.forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); },
        poly: pts => { ctx.beginPath(); pts.forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); st(); },
        beam: pts => { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.shadowBlur = 0; const gr = ctx.createLinearGradient(0, -20, 0, 50);
          gr.addColorStop(0, rgba(col, .45)); gr.addColorStop(1, rgba(col, 0)); ctx.fillStyle = gr; ctx.beginPath(); pts.forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.fill(); ctx.restore(); },
        hand: (x, y, r, a) => { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a - Math.PI / 2) * r, y + Math.sin(a - Math.PI / 2) * r); ctx.stroke(); },
        crescent: (x, y, r) => { ctx.beginPath(); ctx.arc(x, y, r, Math.PI * .3, Math.PI * 1.7); ctx.arc(x + r * .5, y - r * .1, r * .8, Math.PI * 1.55, Math.PI * .45, true); ctx.closePath(); st(); },
        cloud: () => { ctx.beginPath(); ctx.arc(-22, 6, 18, Math.PI * .5, Math.PI * 1.5); ctx.arc(-4, -10, 22, Math.PI, 0); ctx.arc(22, 2, 18, Math.PI * 1.4, Math.PI * .5); ctx.closePath(); st(); },
        flame: () => { const f = 4 * Math.sin(t * 9); ctx.beginPath(); ctx.moveTo(0, 46); ctx.bezierCurveTo(-40, 30, -30, -10, -8 + f, -46); ctx.bezierCurveTo(-4, -20, 14, -26, 12, -40);
          ctx.bezierCurveTo(40, -10, 40, 30, 0, 46); st(); ctx.beginPath(); ctx.moveTo(0, 40); ctx.bezierCurveTo(-16, 30, -12, 6, 0 - f, -8); ctx.bezierCurveTo(12, 8, 16, 30, 0, 40); ctx.fillStyle = rgba(col, .6); ctx.fill(); },
        heart: () => { ctx.beginPath(); ctx.moveTo(0, 40); ctx.bezierCurveTo(-60, 0, -30, -50, 0, -18); ctx.bezierCurveTo(30, -50, 60, 0, 0, 40); st(); },
        eye: () => { ctx.beginPath(); ctx.moveTo(-48, 0); ctx.quadraticCurveTo(0, -42, 48, 0); ctx.quadraticCurveTo(0, 42, -48, 0); st();
          ctx.beginPath(); ctx.arc(6 * Math.sin(t * .9), 0, 15, 0, 7); ctx.fillStyle = col; ctx.fill(); },
        mask: () => { ctx.beginPath(); ctx.moveTo(-36, -36); ctx.quadraticCurveTo(0, -46, 36, -36); ctx.quadraticCurveTo(40, 20, 0, 44); ctx.quadraticCurveTo(-40, 20, -36, -36); st();
          ctx.beginPath(); ctx.ellipse(-14, -12, 9, 6, 0, 0, 7); ctx.ellipse(14, -12, 9, 6, 0, 0, 7); ctx.fillStyle = col; ctx.fill(); ctx.beginPath(); ctx.arc(0, 14, 14, .15 * Math.PI, .85 * Math.PI); ctx.stroke(); },
        ticket: () => { ctx.beginPath(); ctx.moveTo(-46, -26); ctx.lineTo(46, -26); ctx.lineTo(46, -8); ctx.arc(46, 0, 8, -Math.PI / 2, Math.PI / 2, true); ctx.lineTo(46, 26);
          ctx.lineTo(-46, 26); ctx.lineTo(-46, 8); ctx.arc(-46, 0, 8, Math.PI / 2, -Math.PI / 2, true); ctx.closePath(); st(); ctx.setLineDash([6, 6]); ctx.beginPath(); ctx.moveTo(16, -24); ctx.lineTo(16, 24); ctx.stroke(); ctx.setLineDash([]); },
        wave: (x, y, w, h) => { ctx.beginPath(); ctx.moveTo(x, y); for (let u = 0; u <= 1.001; u += .1) ctx.lineTo(x + u * w, y + Math.sin(u * 6 + t * 5) * 5 * u);
          for (let u = 1; u >= -.001; u -= .1) ctx.lineTo(x + u * w, y + h + Math.sin(u * 6 + t * 5) * 5 * u); ctx.closePath(); st(); },
        pin: () => { ctx.beginPath(); ctx.arc(0, -16, 24, Math.PI * .8, Math.PI * .2); ctx.lineTo(0, 40); ctx.closePath(); st(); ctx.beginPath(); ctx.arc(0, -16, 9, 0, 7); ctx.fillStyle = col; ctx.fill(); },
        glyph: ch => { ctx.save(); ctx.shadowBlur = 0; txt(ctx, ch, 0, 20, { size: 58, family: 'Anton', weight: 400, color: col }); ctx.restore(); },
      };
    };
    const drawIcon = (ctx, name, x, y, sc, rot, flip, col, alpha, glow, t) => {
      const fn = ICONS[name] || ICONS.dot;
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0); ctx.scale((flip ? -1 : 1) * sc, sc); ctx.globalAlpha = clamp(alpha);
      ctx.strokeStyle = col; ctx.lineWidth = 6.5 / Math.max(.5, Math.abs(sc)) * Math.max(.85, Math.min(1.3, sc / U)); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.shadowColor = col; ctx.shadowBlur = glow; fn(painter(ctx, col, t)); ctx.restore(); ctx.globalAlpha = 1;
    };

    // ---- where a prop is and how it looks at a moment
    const state = (p, lt, copy) => {
      const n = Math.max(1, Math.min(8, p.count || 1)), gap = (p.gap || .2 * (p.size || 1)) * bw, off = (copy - (n - 1) / 2) * gap;
      let x = X(p.x ?? .5) + off, y = Y(p.y ?? .5), rot = 0, sc = (p.size || 1) * U, alpha = 1, glow = 16, icon = p.icon, col = p.col, hide = false;
      const d0 = lt - p.c0, en = p.enter || 'pop';
      if (d0 < 0) return null;
      const a = ep(d0, 0, .5, E.outBack), af = clamp(d0 * 3);
      if (en === 'pop') sc *= a; else if (en === 'drop') { y -= (1 - ep(d0, 0, .55, E.outBack)) * 420; alpha = af; }
      else if (en === 'slide') { x += (1 - ep(d0, 0, .6, E.outCubic)) * ((p.x ?? .5) < .5 ? -520 : 520); alpha = af; }
      else if (en === 'rise') { y += (1 - ep(d0, 0, .55, E.outBack)) * 220; alpha = af; } else alpha = clamp(d0 * 2);
      if (p.path) {
        const f = p.loop ? (lt > p.mc ? ((lt - p.mc) / p.mv) % 1 : 0) : ep(lt, p.mc, p.mc + p.mv, E.inOutCubic);
        const [px, py, ang] = p.path.at(f); x = px + off; y = py; if (p.face) rot = ang;
      }
      for (const ac of p.acts) {
        if (ac.copy != null && ac.copy !== copy) continue;
        const d = lt - ac.c; if (d < 0) continue;
        if (ac.do === 'fall') { y += 1300 * d * d; rot += d * 2.2 * ((p.x ?? .5) < .5 ? -1 : 1); if (y > H + 200) hide = true; }
        else if (ac.do === 'shake' && d < .7) { const k = Math.exp(-d * 6) * 16; x += Math.sin(d * 70) * k; y += Math.cos(d * 61) * k; }
        else if (ac.do === 'spin') rot += d * 4;
        else if (ac.do === 'grow') sc *= lerp(1, ac.to || 1.6, ep(d, 0, .6, E.outBack));
        else if (ac.do === 'pulse') sc *= 1 + .08 * Math.sin(d * 8);
        else if (ac.do === 'fade') alpha *= 1 - clamp(d / .4);
        else if (ac.do === 'light') { col = GOLD; glow = 34 + 26 * Math.sin(d * 6) ** 2; }
        else if (ac.do === 'swap') { if (d < .25) sc *= 1 - d / .25 * .9; else { icon = ac.icon || icon; sc *= ep(d, .25, .6, E.outBack); } }
        else if (ac.do === 'blast') { if (!ac.keep) alpha *= 1 - clamp((d - .15) / .35); sc *= 1 + .5 * ep(d, 0, .3); }
      }
      return hide ? null : { x, y, rot, sc, alpha, glow, icon, col };
    };
    const where = (p, lt) => state(p, Math.max(lt, p.c0 + .01), 0) || { x: X(p.x ?? .5), y: Y(p.y ?? .5) };

    // ---- the ground under the props
    const ground = (ctx, lt) => {
      const g = s.ground || 'floor', gy = Y(.8), sc = (s.scroll || 0) * lt, dr = ep(lt, 0, .8, E.inOutCubic);
      ctx.save(); ctx.globalAlpha = dr;
      if (g === 'floor' || g === 'road' || g === 'rail') {
        ctx.strokeStyle = rgba(GOLD, .55); ctx.lineWidth = 3; ctx.shadowColor = GOLD; ctx.shadowBlur = 18;
        ctx.beginPath(); ctx.moveTo(X(0) - 40, gy); ctx.lineTo(X(1) + 40, gy); ctx.stroke(); ctx.shadowBlur = 0;
        for (let k = -6; k <= 6; k++) { ctx.strokeStyle = rgba(TEAL, .1); ctx.beginPath(); ctx.moveTo(CX + k * 70, gy); ctx.lineTo(CX + k * 260, Y(1.08)); ctx.stroke(); }
      }
      if (g === 'road') { ctx.setLineDash([38, 30]); ctx.lineDashOffset = sc; ctx.strokeStyle = rgba('#FFFFFF', .45); ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(X(0), gy + 40); ctx.lineTo(X(1), gy + 40); ctx.stroke(); ctx.setLineDash([]); }
      if (g === 'rail') { ctx.strokeStyle = rgba('#FFFFFF', .4); ctx.lineWidth = 4; [gy + 10, gy + 26].forEach(yy => { ctx.beginPath(); ctx.moveTo(X(0) - 40, yy); ctx.lineTo(X(1) + 40, yy); ctx.stroke(); });
        for (let x = X(0) - 40 - ((sc % 46) + 46) % 46; x < X(1) + 40; x += 46) { ctx.fillStyle = rgba(GOLD, .25); ctx.fillRect(x, gy + 6, 10, 26); } }
      if (g === 'water') for (let k = 0; k < 4; k++) { ctx.strokeStyle = rgba(TEAL, .35 - k * .07); ctx.lineWidth = 3; ctx.beginPath();
        for (let x = X(0); x <= X(1); x += 20) ctx.lineTo(x, gy + k * 26 + Math.sin(x * .02 + lt * 2 + k) * 7); ctx.stroke(); }
      if (g === 'city') { const r = rng(91 + i); for (let x = X(0) - 30; x < X(1) + 30;) { const w = 50 + r() * 70, h = 90 + r() * 260; ctx.fillStyle = 'rgba(14,16,22,.95)'; ctx.fillRect(x, gy - h, w, h);
        ctx.strokeStyle = rgba(TEAL, .25); ctx.lineWidth = 2; ctx.strokeRect(x, gy - h, w, h);
        for (let wy = gy - h + 14; wy < gy - 14; wy += 26) for (let wx = x + 10; wx < x + w - 12; wx += 20) if (r() < .35) { ctx.fillStyle = rgba(GOLD, .25 + .25 * Math.sin(lt * 2 + wx)); ctx.fillRect(wx, wy, 8, 10); }
        x += w + 8; } }
      if (g === 'sky') { const r = rng(57 + i); for (let k = 0; k < 60; k++) { const x = X(r() * 1.1 - .05), y = Y(r() * .75), a = .3 + .3 * Math.sin(lt * 2 + k);
        ctx.fillStyle = rgba('#FFFFFF', a); ctx.beginPath(); ctx.arc(x, y, 1.5 + r() * 2.5, 0, 7); ctx.fill(); } }
      if (g === 'map' || g === 'grid') { ctx.lineWidth = 1.5; for (let x = X(0); x <= X(1) + 1; x += bw / 10) { ctx.strokeStyle = rgba(TEAL, .14); ctx.beginPath(); ctx.moveTo(x, Y(0)); ctx.lineTo(x, Y(1)); ctx.stroke(); }
        for (let y = Y(0); y <= Y(1) + 1; y += bh / 10) { ctx.strokeStyle = rgba(TEAL, .14); ctx.beginPath(); ctx.moveTo(X(0), y); ctx.lineTo(X(1), y); ctx.stroke(); }
        if (g === 'map') { ctx.strokeStyle = rgba(GOLD, .5); ctx.lineWidth = 3; ctx.strokeRect(X(0), Y(0), bw, bh); } }
      ctx.restore(); ctx.globalAlpha = 1;
    };

    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (s.heading) wordsIn(ctx, s.heading, CX, 330, lt - .05, { size: fitSize(env, ctx, s.heading, 'Anton', 400, MAXW, 74, 40), family: 'Anton', weight: 400, color: '#fff', stagger: .08 });
      const [sx, sy] = shake(lt, hits, 10);
      ctx.save(); ctx.translate(sx, sy);
      if (fo) {                                               // the camera pushes in on one prop (or a point) and keeps it in frame
        const z = lerp(1, clamp(fo.to || 1.3, 1, 1.8), ep(lt, fc, fc + (fo.d || 1.2), E.inOutCubic));
        const tgt = typeof fo.on === 'string' && byId[fo.on] ? where(byId[fo.on], lt) : Array.isArray(fo.on) ? { x: X(fo.on[0]), y: Y(fo.on[1]) } : { x: CX, y: Y(.5) };
        const cx = lerp(tgt.x, CX, (z - 1) / Math.max(.01, (fo.to || 1.3) - 1) * .7), cy = lerp(tgt.y, Y(.48), (z - 1) / Math.max(.01, (fo.to || 1.3) - 1) * .5);
        ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-tgt.x, -tgt.y);
      }
      ground(ctx, lt);
      props.forEach(p => {                                    // the path a prop travels, drawn on as it moves (a camera path, a route)
        if (!p.path || p.trail === false) return;
        const f = p.loop ? 1 : ep(lt, p.mc, p.mc + p.mv, E.inOutCubic); if (lt < p.mc) return;
        const n = Math.max(2, Math.floor(p.path.pts.length * f));
        ctx.save(); ctx.strokeStyle = rgba(p.col, .55); ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.shadowColor = p.col; ctx.shadowBlur = 20; ctx.setLineDash([2, 16]);
        ctx.beginPath(); p.path.pts.slice(0, n).forEach(([x, y], k) => k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); ctx.restore();
      });
      links.forEach(l => {                                    // a link between two props: a line, red string, a light beam or an arrow
        const A = byId[l.from], B = byId[l.to]; if (!A || !B) return;
        const p = ep(lt, l.c, l.c + .6, E.inOutCubic); if (p <= 0) return;
        const a = where(A, lt), b = where(B, lt), mx = lerp(a.x, b.x, p), my = lerp(a.y, b.y, p), st2 = l.style || 'line';
        ctx.save();
        if (st2 === 'beam') { ctx.globalCompositeOperation = 'lighter'; const ang = Math.atan2(b.y - a.y, b.x - a.x), w = 70 * p, nx = -Math.sin(ang) * w, ny = Math.cos(ang) * w;
          const gr = ctx.createLinearGradient(a.x, a.y, b.x, b.y); gr.addColorStop(0, rgba(GOLD, .5)); gr.addColorStop(1, rgba(GOLD, .05)); ctx.fillStyle = gr;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(mx + nx, my + ny); ctx.lineTo(mx - nx, my - ny); ctx.closePath(); ctx.fill(); }
        else { ctx.strokeStyle = st2 === 'string' ? RED : TEAL; ctx.lineWidth = st2 === 'string' ? 5 : 4; ctx.shadowColor = ctx.strokeStyle; ctx.shadowBlur = 14; if (st2 === 'line') ctx.setLineDash([14, 10]);
          ctx.beginPath(); ctx.moveTo(a.x, a.y);
          if (st2 === 'string') ctx.quadraticCurveTo((a.x + mx) / 2, (a.y + my) / 2 + 40 * p, mx, my); else ctx.lineTo(mx, my); ctx.stroke(); ctx.setLineDash([]);
          if (st2 === 'arrow' && p > .95) { const ang = Math.atan2(b.y - a.y, b.x - a.x); ctx.fillStyle = TEAL; ctx.beginPath(); ctx.moveTo(mx, my);
            ctx.lineTo(mx - Math.cos(ang - .45) * 30, my - Math.sin(ang - .45) * 30); ctx.lineTo(mx - Math.cos(ang + .45) * 30, my - Math.sin(ang + .45) * 30); ctx.closePath(); ctx.fill(); } }
        ctx.restore();
        if (l.label && p >= 1) pill(ctx, l.label, clamp((a.x + b.x) / 2, 210, 770), (a.y + b.y) / 2 - 46, lt - l.c - .6, { size: 30, bg: st2 === 'string' ? RED : TEAL, color: INK, ls: .08 });
      });
      props.forEach(p => {
        const n = Math.max(1, Math.min(8, p.count || 1));
        for (let c = 0; c < n; c++) {
          const v = state(p, lt, c); if (!v) continue;
          drawIcon(ctx, v.icon, v.x, v.y, v.sc, v.rot, p.flip, v.col, v.alpha, v.glow, t);
          p.acts.forEach(ac => {                              // a blast: ring, sparks and a flash
            if (ac.do !== 'blast' || (ac.copy != null && ac.copy !== c)) return; const d = lt - ac.c; if (d < 0 || d > 1.2) return;
            ring(ctx, v.x, v.y, d, { color: GOLD, r0: 20, r1: 340, w: 16, d: .7 });
            const r = rng(i * 131 + p.k * 17 + c); for (let q = 0; q < 22; q++) { const ang = r() * Math.PI * 2, sp = 260 + r() * 520, dd = Math.min(d, .9);
              ctx.fillStyle = rgba(q % 3 ? GOLD : '#FFFFFF', clamp(1 - d / 1.1)); ctx.beginPath(); ctx.arc(v.x + Math.cos(ang) * sp * dd, v.y + Math.sin(ang) * sp * dd + 300 * dd * dd, 3 + r() * 5, 0, 7); ctx.fill(); }
          });
        }
      });
      props.forEach(p => {                                    // labels last, so no prop covers them
        if (!p.label || lt < p.lc) return;
        const v = state(p, Math.max(lt, p.c0 + .5), 0); if (!v) return;
        const up = p.label_at === 'above', ly = v.y + (up ? -1 : 1) * (52 * (p.size || 1) * U + 30);
        pill(ctx, p.label, clamp(v.x, 210, 770), clamp(ly, 420, 1260), lt - p.lc, { size: 32, bg: p.col, color: INK, ls: .08 });
      });
      ctx.restore();
      props.forEach(p => p.acts.forEach(ac => { if (ac.do === 'blast') flash(ctx, lt, ac.c, { alpha: .35, d: .3 }); }));
      if (s.counter) {                                        // a number that counts up on its word (no currency sign unless the unit says so)
        const c = s.counter, v = Math.round(lerp(c.from || 0, c.to, ep(lt, ct, ct + (c.d || 1.8), E.outCubic))), pa = ep(lt, ct - .2, ct + .2);
        const x = X(c.x ?? .5), y = Y(c.y ?? .95);
        if (pa > 0) { const w = txt(ctx, String(v), x - 12, y, { size: 140, family: 'Anton', weight: 400, color: '#fff', glow: rgba(GOLD, .6), glowBlur: 30, alpha: pa, align: 'right' });
          if (c.unit) txt(ctx, c.unit, x, y, { size: 50, family: 'Anton', weight: 400, color: GOLD, alpha: pa, align: 'left' }); }
      }
      if (s.slam_text) slam(ctx, s.slam_text, CX, 1300, lt - cs, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 100, 50), family: 'Anton', weight: 400, color: GOLD, glow: rgba(GOLD, .6), glowBlur: 40, stroke: INK, strokeW: 10 });
    };
  },

  // ------------------------------------------------------------ end: question, send prompt, mascot, echo of screen 1
  end(env, s, i, T) {
    const bg = s.bg ? env.memo('blur:' + s.bg, () => filtered(env.img[s.bg], 'blur(14px) brightness(.55) saturate(.8)', .5)) : null;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (bg) { ctx.save(); ctx.globalAlpha = .38 * ep(lt, 0, .8); cover(ctx, bg, 0, 0, W, H, { zoom: 1.15 + .05 * Math.sin(lt * .5), fy: .4 }); ctx.restore(); ctx.globalAlpha = 1; grad(ctx, 0, 0, 0, H, [[0, 'rgba(5,6,8,.75)'], [.5, 'rgba(5,6,8,.35)'], [1, 'rgba(5,6,8,.85)']]); }
      if (s.recap) pill(ctx, s.recap, CX, 505, lt - .15, { size: 38, bg: GOLD, color: INK, ls: .1, glow: rgba(GOLD, .6) });
      partBadge(env, ctx, lt - .3, 425);
      endCard(env, ctx, lt, t, { echo: s.echo, question: s.question, cta: s.cta, sub: env.plan.subtitles === false ? s.sub : null, subFamily: s.subFamily, accent: GOLD,
        cx: CX, echoY: 330, qy: 690, ctaY: 990, handleY: 1100, mascot: [170, 1235, .7], echoSize: 30 });
      // the loop (Harish, 19 Nov): the last moments fade back to the opening frame, so the end flows into the start
      const dur = T.end - T.start, lp = env.plan.loop === false ? 0 : ep(lt, dur - .75, dur, E.inOutCubic), first = env.plan.screens[0] || {};
      if (lp > 0) {
        ctx.save(); ctx.globalAlpha = lp; fill(ctx, INK);
        if (env.img[first.image]) cover(ctx, env.img[first.image], 0, 170, W, 830, { zoom: 1.08, fx: first.fx ?? .5, fy: first.fy ?? .5 });
        fadeBand(ctx, 170, 830, 200); ctx.restore(); ctx.globalAlpha = 1;
      }
    };
  },
};

export async function build(env, plan, tl) {
  useKit(plan);
  const screens = plan.screens.map((s, i) => {
    const T = tl.screens[i];
    return { start: T.start, end: T.end, tin: s.in ? { type: s.in, d: s.in_d || .36 } : null, draw: KINDS[s.kind](env, s, i, T) };
  });
  return {
    screens,
    overlay: (ctx, t) => { if (plan.subtitles !== false) subtitles(env, ctx, t, { cx: CX, y: SUB_Y, maxW: MAXW, accent: GOLD }); },
    post: (ctx) => { vignette(env, ctx, .82); grain(env, ctx, .085); },
  };
}
