#!/usr/bin/env node
// Render one reel: plan -> audio + timeline -> animated frames (headless Chromium canvas) -> MP4 -> inspect.
// Usage:
//   node engine/render/render.mjs plans/<date>/<reel>.json [--out file.mp4] [--stills 0.5,3,10] [--skip-audio]
// Same plan, same reel: every frame is computed from its time, so renders repeat exactly.
import { createRequire } from 'module';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { spawn, execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const args = process.argv.slice(2);
const planPath = path.resolve(args[0]);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const flag = k => args.includes(k);
const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
// the brand kit travels with the plan (handle on every end card); nothing brand-specific is typed into templates
try { const bt = JSON.parse(fs.readFileSync(path.join(ROOT, 'brands', plan.brand_kit || 'inikki-reels', 'brand_tokens.json'), 'utf8')); plan.brand = { handle: bt.handle, name: bt.name }; } catch (e) { plan.brand = { handle: '@inikki_reels' }; }
const work = path.join(ROOT, 'engine', '.work', plan.id);
fs.mkdirSync(work, { recursive: true });
const out = path.resolve(opt('--out', path.join(ROOT, 'engine', '.work', 'out', `${plan.id}.mp4`)));
fs.mkdirSync(path.dirname(out), { recursive: true });
const log = (...a) => console.log(`[${plan.id}]`, ...a);

// 0. fonts and stills on disk (any cloud machine can render any plan)
if (!fs.existsSync(path.join(ROOT, 'engine/.cache/fonts/fonts.local.css'))) execFileSync('python3', [path.join(ROOT, 'engine/tools/fetch_fonts.py')], { stdio: 'inherit' });
execFileSync('python3', [path.join(ROOT, 'engine/render/assets.py'), planPath], { stdio: 'inherit' });

// 1. audio + timeline
if (!flag('--skip-audio') || !fs.existsSync(path.join(work, 'timeline.json'))) {
  const r = execFileSync('python3', [path.join(ROOT, 'engine/render/audio.py'), planPath, work], { encoding: 'utf8' });
  log('audio', r.trim().split('\n').pop());
}
const timeline = JSON.parse(fs.readFileSync(path.join(work, 'timeline.json'), 'utf8'));
const fps = timeline.fps || 30;

// 2. local file server (same origin, so the canvas can be read back)
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.json': 'application/json', '.webp': 'image/webp' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-lcd-text', '--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => log('PAGE ERROR', e.message));
page.on('console', m => { if (m.type() === 'error') log('console', m.text()); });
await page.goto(`http://127.0.0.1:${port}/templates/_shared/page.html`);
await page.waitForFunction(() => window.__ready === true);
const warnings = await page.evaluate(([p, t]) => window.boot(p, t), [plan, timeline]);
if (warnings.length) log('warnings:', warnings.join(' | '));

const toBuf = d => Buffer.from(d.slice(d.indexOf(',') + 1), 'base64');

if (opt('--stills')) {
  // quick look at chosen moments
  for (const f of fs.readdirSync(work)) if (f.startsWith('still_')) fs.unlinkSync(path.join(work, f));
  const ts = opt('--stills').split(',').map(Number);
  const imgs = await page.evaluate(([ts]) => window.renderBatch(ts, .9), [ts]);
  imgs.forEach((d, k) => fs.writeFileSync(path.join(work, `still_${String(ts[k]).replace('.', '_')}.jpg`), toBuf(d)));
  log('stills written to', work);
  await browser.close(); server.close(); process.exit(0);
}

// 3. frames -> ffmpeg
const total = Math.round(timeline.duration * fps);
const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  '-i', path.join(work, 'audio.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '9M', '-bufsize', '18M',
  '-pix_fmt', 'yuv420p', '-r', String(fps), '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
const write = buf => new Promise(r => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', r); else r(); });
const t0 = Date.now();
const BATCH = 6;
for (let f = 0; f < total; f += BATCH) {
  const ts = []; for (let k = f; k < Math.min(total, f + BATCH); k++) ts.push(k / fps);
  const imgs = await page.evaluate(([ts]) => window.renderBatch(ts, .93), [ts]);
  for (const d of imgs) await write(toBuf(d));
  if (f % (fps * 5) < BATCH) log(`frame ${f}/${total} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close(); server.close();
log('video', out, `${((Date.now() - t0) / 1000).toFixed(0)} s`);

// 4. inspect (AGENT.md stage 8)
const rep = execFileSync('python3', [path.join(ROOT, 'engine/render/check_reel.py'), out, path.join(work, 'timeline.json'), planPath], { encoding: 'utf8' });
fs.writeFileSync(path.join(work, 'inspect.json'), rep);
log('inspect', rep.trim());
