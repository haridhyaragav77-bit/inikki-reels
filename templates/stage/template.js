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

  // ------------------------------------------------------------ end: question, send prompt, mascot, echo of screen 1
  end(env, s, i, T) {
    const bg = s.bg ? env.memo('blur:' + s.bg, () => filtered(env.img[s.bg], 'blur(14px) brightness(.55) saturate(.8)', .5)) : null;
    return (ctx, lt, t) => {
      stage(env, ctx, t);
      if (bg) { ctx.save(); ctx.globalAlpha = .38 * ep(lt, 0, .8); cover(ctx, bg, 0, 0, W, H, { zoom: 1.15 + .05 * Math.sin(lt * .5), fy: .4 }); ctx.restore(); ctx.globalAlpha = 1; grad(ctx, 0, 0, 0, H, [[0, 'rgba(5,6,8,.75)'], [.5, 'rgba(5,6,8,.35)'], [1, 'rgba(5,6,8,.85)']]); }
      if (s.recap) pill(ctx, s.recap, CX, 505, lt - .15, { size: 38, bg: GOLD, color: INK, ls: .1, glow: rgba(GOLD, .6) });
      endCard(env, ctx, lt, t, { echo: s.echo, question: s.question, cta: s.cta, sub: env.plan.subtitles === false ? s.sub : null, subFamily: s.subFamily, accent: GOLD,
        cx: CX, echoY: 330, qy: 690, ctaY: 990, handleY: 1100, mascot: [170, 1235, .7], echoSize: 30 });
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
