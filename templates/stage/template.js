// STAGE — Film Breakdown look (AGENT.md 6.6): deep black stage, spotlight, haze and dust;
// motion graphics lead and can take the whole screen. Gold accents, Anton titles, Tamil voice.
import { W, H, clamp, lerp, prog, ep, E, life, rng, cue, beatPulse, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, rgba, filtered } from '../_shared/runtime.js';
import { endCard, labelPin, shapePoints, assemble, subtitles } from '../_shared/motion.js';

const GOLD = '#F8C868', TEAL = '#78E0D0', INK = '#050608';
// Instagram-safe layout for breakdowns: the action buttons sit on the right and the profile, caption and
// message bar at the bottom. Words and key visuals stay in the safe column; subtitles get their own band.
const CX = 490, MAXW = 840, SUB_Y = 1415;

function stage(env, ctx, t) {
  fill(ctx, INK);
  const sx = W / 2 + Math.sin(t * .35) * 150;
  radial(ctx, sx, -260, 1750, [[0, 'rgba(248,200,104,.24)'], [.5, 'rgba(248,200,104,.05)'], [1, 'rgba(0,0,0,0)']]);
  radial(ctx, W / 2, H + 260, 1000, [[0, 'rgba(120,224,208,.10)'], [1, 'rgba(0,0,0,0)']]);
  const hz = tint(env, '#F8C868');
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let k = 0; k < 4; k++) {
    const x = W / 2 + Math.sin(t * .21 + k * 1.7) * 430, y = 420 + k * 360 + Math.cos(t * .17 + k) * 90, s = 720;
    ctx.globalAlpha = .045; ctx.drawImage(hz, x - s, y - s, s * 2, s * 2);
  }
  ctx.restore(); ctx.globalAlpha = 1;
  dust(env, ctx, t, { n: 38, color: '#FFE2A8', alpha: .32, min: 2, max: 7, rise: 24, seed: 21 });
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
      slam(ctx, s.film, CX, 1140, lt - hit, { size, family: 'Anton', weight: 400, color: GOLD, glow: 'rgba(248,200,104,.6)', glowBlur: 55, ls: .01 });
      ring(ctx, CX, 1080, lt - hit, { color: GOLD, r1: 760, w: 16 });
      streak(ctx, CX, 1077, lt - hit - .04, { len: 1050, h: 3 });
      const ts = fitSize(env, ctx, s.type, 'Inter', 900, MAXW - 20, 58, 34, .16);
      wordsIn(ctx, s.type, CX, 1236, lt - hit - .3, { size: ts, weight: 900, ls: .16, color: '#fff', stagger: .1 });
      const rl = ep(lt, hit + .65, hit + 1.15, E.inOutCubic);
      ctx.fillStyle = GOLD; ctx.fillRect(CX - 230 * rl, 1274, 460 * rl, 5);
      ctx.restore();
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
      slam(ctx, s.slam_text, CX, 1255, lt - cs - .35, { size: fitSize(env, ctx, s.slam_text, 'Anton', 400, MAXW, 120, 60), family: 'Anton', weight: 400, color: '#fff', glow: 'rgba(248,200,104,.6)', glowBlur: 40 });
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
      endCard(env, ctx, lt, t, { echo: s.echo, question: s.question, cta: s.cta, sub: env.plan.subtitles === false ? s.sub : null, subFamily: s.subFamily, accent: GOLD,
        cx: CX, echoY: 330, qy: 690, ctaY: 1065, mascot: [180, 1230, .72], echoSize: 30 });
    };
  },
};

export async function build(env, plan, tl) {
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
