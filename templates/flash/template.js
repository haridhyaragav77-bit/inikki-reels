// FLASH — Breaking News look (AGENT.md 6.6): full-bleed still in a red wash, scan lines, a pulsing live dot,
// headline slams, fact blocks that snap in, a running ticker. Music-only, short.
import { W, H, clamp, lerp, prog, ep, E, rng, cue, beatPulse, nearestBeat, shake, fill, grad, radial, cover, framed, rrect,
  txt, setFont, fitSize, slam, wordsIn, pill, dust, tint, sweep, ring, streak, flash, vignette, grain, scanlines, rgba, filtered, duotone } from '../_shared/runtime.js';
import { endCard } from '../_shared/motion.js';

const RED = '#E5484D', BLACK = '#070708', WHITE = '#FFFFFF';

function redStill(env, ctx, key, lt, o = {}) {
  const im = env.memo('red:' + key, () => duotone(env.img[key], '#0b0203', '#ff6b6f', 1.25));
  fill(ctx, BLACK);
  cover(ctx, im, 0, 0, W, H, { zoom: (o.zoom || 1.12) + .08 * ep(lt, 0, 5, E.linear), fx: o.fx ?? .5, fy: o.fy ?? .45, px: Math.sin(lt * 9) * .002 });
  ctx.save(); ctx.globalAlpha = o.dim ?? .35; fill(ctx, BLACK); ctx.restore(); ctx.globalAlpha = 1;
  grad(ctx, 0, 0, 0, H, [[0, 'rgba(7,7,8,.8)'], [.3, 'rgba(7,7,8,0)'], [.62, 'rgba(7,7,8,.25)'], [1, 'rgba(7,7,8,.95)']]);
}
function jitter(env, lt, amt = 1) { const r = rng(env.frame * 13 + 1); return (r() < .12 ? (r() - .5) * 18 * amt : 0); }
function block(ctx, text, x, y, lt, o = {}) {
  if (lt < 0) return;
  const p = ep(lt, 0, .28, E.outExpo), side = o.side || -1, size = o.size || 90;
  setFont(ctx, size, 'Anton', 400, .02); const w = ctx.measureText(text).width + size * .7, h = size * 1.32;
  const bx = x + (1 - p) * side * 1200;
  ctx.save(); ctx.translate(bx, y);
  ctx.fillStyle = o.bg || RED; ctx.fillRect(-w / 2, -h / 2, w, h);
  txt(ctx, text, 0, size * .37, { size, family: 'Anton', weight: 400, color: o.color || WHITE, ls: .02 });
  if (o.sub) txt(ctx, o.sub, -w / 2 + 6, -h / 2 - 16, { size: 30, weight: 900, ls: .16, color: rgba(WHITE, .85 * clamp(p * 2)), align: 'left' });
  ctx.restore();
}

const KINDS = {
  title(env, s, i, T) {
    const hit = s.slam_at ?? .1;
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [hit, hit + .4], 14);
      ctx.save(); ctx.translate(sx + jitter(env, lt), sy);
      redStill(env, ctx, s.image, lt, { fx: s.fx, fy: s.fy, zoom: 1.0, dim: .2 });
      scanlines(env, ctx, .16, lt);
      flash(ctx, lt, hit, { alpha: .6, color: RED });
      const f = fitSize(env, ctx, s.film, 'Anton', 400, 980, 210, 90);
      slam(ctx, s.film, W / 2, 1230, lt - hit, { size: f, family: 'Anton', weight: 400, color: WHITE, from: 2.6, glow: 'rgba(229,72,77,.8)', glowBlur: 40 });
      block(ctx, s.what, W / 2, 1380, lt - hit - .4, { size: 100, side: 1 });
      ring(ctx, W / 2, 1230, lt - hit, { color: RED, r1: 900, w: 20 });
      ctx.restore();
    };
  },
  date(env, s, i, T) {
    const land = nearestBeat(env, T.start + (s.land ?? .9)) - T.start;
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [land], 16);
      ctx.save(); ctx.translate(sx, sy);
      redStill(env, ctx, s.image, lt, { fx: s.fx, dim: .6, zoom: 1.2 });
      scanlines(env, ctx, .12, lt);
      const cx = W / 2, cy = 830, cw = 640, ch = 720, p = ep(lt, .1, .5, E.outBack);
      ctx.save(); ctx.translate(cx, cy); ctx.scale(p, p);
      ctx.shadowColor = 'rgba(229,72,77,.7)'; ctx.shadowBlur = 60 + 30 * beatPulse(env, t);
      rrect(ctx, -cw / 2, -ch / 2, cw, ch, 36); ctx.fillStyle = '#FAF7F5'; ctx.fill(); ctx.shadowBlur = 0; ctx.shadowColor = 'transparent';
      ctx.save(); rrect(ctx, -cw / 2, -ch / 2, cw, 170, 36); ctx.clip(); ctx.fillStyle = RED; ctx.fillRect(-cw / 2, -ch / 2, cw, 170); ctx.restore();
      txt(ctx, s.month, 0, -ch / 2 + 120, { size: 96, family: 'Anton', weight: 400, color: WHITE, ls: .08 });
      for (const rx of [-200, 200]) { ctx.fillStyle = '#2a2a2a'; rrect(ctx, rx - 14, -ch / 2 - 30, 28, 70, 14); ctx.fill(); }
      const fp = prog(lt, .35, land);
      const shown = lt < land ? String(Math.max(1, Math.floor(lerp(1, s.day, E.inQuad(fp))))) : String(s.day);
      const flip = lt < land ? Math.abs(Math.cos((lt * 22))) : 1;
      ctx.save(); ctx.translate(0, 90); ctx.scale(1, lt < land ? flip : 1 + .08 * Math.exp(-(lt - land) * 7));
      txt(ctx, shown, 0, 140, { size: 400, family: 'Anton', weight: 400, color: BLACK });
      ctx.restore();
      txt(ctx, s.year, 0, ch / 2 - 40, { size: 64, family: 'Anton', weight: 400, color: RED, alpha: ep(lt, land, land + .3) });
      ctx.restore();
      ring(ctx, cx, cy, lt - land, { color: RED, r1: 800, w: 18 });
      block(ctx, s.line, W / 2, 1360, lt - land - .25, { size: 84, side: -1 });
      ctx.restore();
    };
  },
  team(env, s, i, T) {
    return (ctx, lt, t) => {
      redStill(env, ctx, s.image, lt, { fx: s.fx, dim: .62, zoom: 1.15 });
      scanlines(env, ctx, .12, lt);
      wordsIn(ctx, s.heading, W / 2, 470, lt - .05, { size: 60, weight: 900, ls: .2, color: WHITE, stagger: .1 });
      s.people.forEach((p, k) => {
        const y = 690 + k * 215, st = .3 + k * (s.gap ?? .5);
        block(ctx, p.name, W / 2, y, lt - st, { size: 92, side: k % 2 ? 1 : -1, bg: k % 2 ? WHITE : RED, color: k % 2 ? BLACK : WHITE, sub: p.role });
        if (lt > st && lt < st + .12) { ctx.save(); ctx.globalAlpha = .35; ctx.fillStyle = RED; ctx.fillRect(0, y - 80, W, 160); ctx.restore(); ctx.globalAlpha = 1; }
      });
    };
  },
  fact(env, s, i, T) {
    return (ctx, lt, t) => {
      const [sx, sy] = shake(lt, [.5], 10);
      ctx.save(); ctx.translate(sx, sy);
      redStill(env, ctx, s.image, lt, { fx: s.fx, fy: s.fy, dim: .25, zoom: s.zoom || 1.6 });
      scanlines(env, ctx, .14, lt);
      sweep(ctx, lt, .2, 1.0, { alpha: .2 });
      s.lines.forEach((ln, k) => block(ctx, ln, W / 2, 1150 + k * 150, lt - .3 - k * .25, { size: k ? 110 : 84, side: k % 2 ? 1 : -1, bg: k ? RED : WHITE, color: k ? WHITE : BLACK }));
      if (s.source) txt(ctx, s.source, W / 2, 1510, { size: 26, weight: 700, color: rgba(WHITE, .6 * ep(lt, 1, 1.5)) });
      ctx.restore();
    };
  },
  end(env, s, i, T) {
    return (ctx, lt, t) => {
      redStill(env, ctx, s.bg, lt, { dim: .8, zoom: 1.3 });
      scanlines(env, ctx, .1, lt);
      endCard(env, ctx, lt, t, { echo: s.echo, question: s.question, cta: s.cta, sub: s.sub, accent: RED });
    };
  },
};

export async function build(env, plan, tl) {
  const screens = plan.screens.map((s, i) => {
    const T = tl.screens[i];
    return { start: T.start, end: T.end, tin: s.in ? { type: s.in, d: s.in_d || .3 } : null, draw: KINDS[s.kind](env, s, i, T) };
  });
  const lastStart = tl.screens[tl.screens.length - 1].start;
  const tick = (plan.ticker || '') + '   •   ';
  return {
    screens,
    overlay: (ctx, t) => {
      if (t >= lastStart) return;
      // live bar
      const a = ep(t, 0, .25);
      ctx.save(); ctx.globalAlpha = a;
      setFont(ctx, 36, 'Inter', 900, .16); const bw = ctx.measureText(plan.badge || 'BREAKING').width + 110;
      ctx.fillStyle = RED; ctx.fillRect(60, 268, bw, 64);
      const pulse = .5 + .5 * Math.sin(t * 7);
      ctx.fillStyle = WHITE; ctx.beginPath(); ctx.arc(96, 300, 11, 0, 7); ctx.fill();
      ctx.globalAlpha = a * (1 - pulse) * .8; ctx.strokeStyle = WHITE; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(96, 300, 11 + pulse * 22, 0, 7); ctx.stroke(); ctx.globalAlpha = a;
      txt(ctx, plan.badge || 'BREAKING', 122, 313, { size: 36, weight: 900, ls: .16, color: WHITE, align: 'left' });
      if (plan.when) txt(ctx, plan.when, 60 + bw + 24, 313, { size: 32, weight: 800, ls: .1, color: rgba(WHITE, .85), align: 'left' });
      // ticker
      ctx.fillStyle = 'rgba(229,72,77,.95)'; ctx.fillRect(0, 1478, W, 62);
      setFont(ctx, 34, 'Inter', 900, .1); const tw = ctx.measureText(tick).width;
      const off = (t * 220) % tw;
      ctx.save(); ctx.beginPath(); ctx.rect(0, 1478, W, 62); ctx.clip();
      for (let x = -off; x < W; x += tw) txt(ctx, tick, x, 1521, { size: 34, weight: 900, ls: .1, color: WHITE, align: 'left' });
      ctx.restore();
      ctx.restore(); ctx.globalAlpha = 1;
    },
    post: (ctx) => { vignette(env, ctx, .7); grain(env, ctx, .08); },
  };
}
