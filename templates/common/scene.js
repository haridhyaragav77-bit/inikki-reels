// A still picture with depth. Near and far parts of the picture move at different speeds as the camera
// pushes in, pulls out or drifts, with fog, dust and a slow moving light (AGENT.md 5.7; archive 13.3).
// The layers are cut by engine/depth.py. With no layers it falls back to one picture with a slow move.
window.Scene = class {
  constructor(host, rand, opt = {}) {
    this.host = host; this.rand = rand; this.opt = Object.assign({ amount: 40, fog: true, dust: true, light: true, dof: true }, opt);
    host.style.overflow = "hidden"; host.innerHTML = `<div class="sc-l" style="position:absolute;inset:0"></div>`;
    this.L = host.firstElementChild; this.key = null; this.imgs = [];
    const W = host.clientWidth || 1080, H = host.clientHeight || 1920; this.W = W; this.H = H;
    if (this.opt.fog) this.fogs = [0, 1, 2].map(i => { const f = document.createElement("div");
      f.style.cssText = `position:absolute;left:-40%;width:180%;height:${34 + i * 8}%;top:${28 + i * 22}%;pointer-events:none;opacity:${0.15 - i * 0.03};background:radial-gradient(ellipse 46% 48% at ${30 + i * 20}% 50%, ${this.opt.fogColor || "rgba(200,220,235,0.9)"} 0%, transparent 100%)`;
      host.appendChild(f); return { el: f, sp: (i % 2 ? -1 : 1) * (10 + rand() * 12), off: rand() * 400 }; });
    if (this.opt.light) { this.light = document.createElement("div"); this.light.style.cssText = `position:absolute;top:-10%;bottom:-10%;left:-30%;width:160%;pointer-events:none;background:linear-gradient(105deg, transparent 42%, ${this.opt.lightColor || "rgba(255,236,190,0.13)"} 50%, transparent 58%)`; host.appendChild(this.light); }
    if (this.opt.dust) { this.cv = document.createElement("canvas"); this.cv.width = W; this.cv.height = H; this.cv.style.cssText = "position:absolute;inset:0;pointer-events:none"; host.appendChild(this.cv);
      this.dust = Array.from({ length: this.opt.dustCount || 70 }, () => ({ x: rand() * W, y: rand() * H, r: 0.8 + rand() * 2.2, vx: -6 + rand() * 12, vy: -(4 + rand() * 14), p: rand() * 6.28, d: rand() })); }
  }
  async set(image, key) {
    if (this.key === key) return; this.key = key; this.L.innerHTML = ""; this.imgs = [];
    const layers = image && image.layers && image.layers.length ? image.layers : (image && image.src ? [{ src: image.src, depth: 0.5 }] : []);
    const fx = image && image.focus ? image.focus[0] : 0.5, fy = image && image.focus ? image.focus[1] : 0.5;
    for (let i = 0; i < layers.length; i++) { const im = document.createElement("img");
      im.style.cssText = `position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:${fx * 100}% ${fy * 100}%;transform-origin:${fx * 100}% ${fy * 100}%;will-change:transform`;
      this.L.appendChild(im); await T.setSrc(im, layers[i].src); this.imgs.push({ el: im, d: layers.length > 1 ? layers[i].depth : 0.5 }); }
  }
  // p: how far through this picture's time (0..1, may run a little past 1 during a crossfade); t: seconds, for the ambient motion
  render(p, t, move) {
    let cx = 0, cy = 0, z = 0; const q = Math.min(1.2, Math.max(0, p));
    if (move === "pull") { z = 1 - q; cx = -0.22 * (q - 0.5); }
    else if (move === "left") { cx = 0.62 - 1.24 * q; z = 0.35; }
    else if (move === "right") { cx = -0.62 + 1.24 * q; z = 0.35; }
    else if (move === "orbit") { cx = 0.7 * Math.sin((q - 0.5) * 2.6); cy = 0.2 * Math.cos((q - 0.5) * 2.6) - 0.2; z = 0.25 + 0.35 * q; }
    else { z = q; cx = 0.3 * (q - 0.5); cy = -0.16 * (q - 0.5); }                                   // push (default)
    const A = this.opt.amount;
    for (const l of this.imgs) { const k = 0.22 + l.d;
      l.el.style.transform = `translate(${(-cx * A * k).toFixed(2)}px, ${(-cy * A * 0.6 * k).toFixed(2)}px) scale(${(1.1 + z * (0.022 + 0.085 * l.d)).toFixed(4)})`; }
    if (this.fogs) for (const f of this.fogs) f.el.style.transform = `translateX(${(((t * f.sp + f.off) % 500 + 500) % 500 - 250).toFixed(1)}px)`;
    if (this.light) this.light.style.transform = `translateX(${(-37.5 + 75 * Math.min(1, q)).toFixed(2)}%)`;
    if (this.cv) { const c = this.cv.getContext("2d"); c.clearRect(0, 0, this.W, this.H); c.globalCompositeOperation = "lighter";
      for (const d of this.dust) { const x = ((d.x + d.vx * t) % this.W + this.W) % this.W, y = ((d.y + d.vy * t) % this.H + this.H) % this.H;
        c.globalAlpha = (0.12 + 0.4 * d.d) * (0.5 + 0.5 * Math.sin(t * (0.8 + d.d) + d.p)); c.fillStyle = this.opt.dustColor || "#ffe9c4"; c.beginPath(); c.arc(x, y, d.r * (0.6 + d.d), 0, 6.283); c.fill(); }
      c.globalAlpha = 1; c.globalCompositeOperation = "source-over"; }
  }
};
