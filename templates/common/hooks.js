// Visual hooks (AGENT.md 5.8): one event in the first second that stops the scroll. Picked to fit the film.
//   Hooks.make(type, host, rand, brand) → { dur, cues, draw(t) → { x, y, s, flash } }
// x, y, s move the whole frame (shake, punch); flash (0..1) lets 3D scenes light up with the strike.
window.Hooks = (() => {
  const { clamp, easeOut, easeIn, lerp } = T, W = 1080, H = 1920;
  const decay = (t, at, peak, life) => t < at ? 0 : peak * Math.exp(-(t - at) / life);
  const shake = (t, amp) => ({ x: amp * (Math.sin(t * 97.3) + Math.sin(t * 61.7)) * 0.5, y: amp * (Math.sin(t * 83.1 + 1.3) + Math.sin(t * 47.9)) * 0.5 });
  const still = { x: 0, y: 0, s: 1, flash: 0 };
  function bolt(rand, x0, y1) {            // a jagged path from the top of the frame, with branches
    const pts = [[x0, -30]]; let x = x0, y = -30; const segs = 16;
    for (let i = 1; i <= segs; i++) { y = -30 + (y1 + 30) * i / segs; x += (rand() - 0.5) * 150; pts.push([x, y]); }
    const br = []; for (let k = 0; k < 3; k++) { const i = 4 + Math.floor(rand() * 9), b = [pts[i]]; let bx = pts[i][0], by = pts[i][1], dir = rand() < 0.5 ? -1 : 1;
      for (let j = 0; j < 5; j++) { bx += dir * (30 + rand() * 60); by += 40 + rand() * 60; b.push([bx, by]); } br.push(b); }
    return { pts, br };
  }
  const M = {
    none: () => ({ dur: 0, cues: [], draw: () => still }),

    // lightning: two strikes, the frame lights up cold and shakes
    thunder(host, rand, brand) {
      host.innerHTML = `<canvas width="${W}" height="${H}" style="position:absolute;inset:0"></canvas><div class="hk-f" style="position:absolute;inset:0;background:#cfe0ff;opacity:0"></div>`;
      const cv = host.firstElementChild, c = cv.getContext("2d"), f = host.lastElementChild, b1 = bolt(rand, 300 + rand() * 480, 760 + rand() * 260), b2 = bolt(rand, 200 + rand() * 680, 620 + rand() * 300);
      const stroke = (b, a) => { if (a <= 0.01) return; c.globalAlpha = Math.min(1, a); c.lineJoin = "round"; c.lineCap = "round"; c.shadowColor = brand.colors.glow || "#9db8ff"; c.shadowBlur = 38;
        for (const [w, col] of [[14, "rgba(160,190,255,0.55)"], [5, "#ffffff"]]) { c.strokeStyle = col; c.lineWidth = w; c.beginPath(); b.pts.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.stroke();
          c.lineWidth = w * 0.45; for (const q of b.br) { c.beginPath(); q.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.stroke(); } } };
      return { dur: 1.0, cues: [{ t: 0.0, kind: "thunder" }, { t: 0.24, kind: "hit" }], draw(t) {
        const a1 = decay(t, 0.0, 1.0, 0.09), a2 = decay(t, 0.24, 0.85, 0.11), fl = Math.max(a1, a2) + decay(t, 0.4, 0.22, 0.25);
        c.clearRect(0, 0, W, H); stroke(b1, a1 * 1.4); stroke(b2, a2 * 1.4); c.globalAlpha = 1; f.style.opacity = (0.42 * Math.max(a1, a2)).toFixed(3);
        const sh = shake(t, 15 * clamp(fl)); return { x: sh.x, y: sh.y, s: 1 + 0.02 * clamp(fl), flash: clamp(fl) }; } };
    },

    // a headlight sweep: a bright streak crosses the frame
    flare(host, rand, brand) {
      const col = brand.colors.gold || "#ffd27a";
      host.innerHTML = `<div class="hk-s" style="position:absolute;left:0;top:35%;width:${W}px;height:26px;margin-top:-13px;background:linear-gradient(90deg,transparent,${col} 35%,#fff 50%,${col} 65%,transparent);filter:blur(5px);transform-origin:50% 50%"></div>
        <div class="hk-o" style="position:absolute;top:35%;width:520px;height:520px;margin:-260px 0 0 -260px;border-radius:50%;background:radial-gradient(circle,#fff 0%,${T.rgba(col, 0.75)} 16%,${T.rgba(col, 0.22)} 42%,transparent 68%)"></div><div class="hk-f" style="position:absolute;inset:0;background:${col};opacity:0"></div>`;
      const [s, o, f] = host.children;
      return { dur: 0.85, cues: [{ t: 0.0, kind: "whoosh" }, { t: 0.26, kind: "ding" }], draw(t) {
        const k = clamp(t / 0.6), x = lerp(-300, W + 300, easeOut(k)), a = Math.sin(Math.PI * clamp(t / 0.7));
        o.style.left = x + "px"; o.style.opacity = a.toFixed(3); s.style.opacity = (a * 0.95).toFixed(3); s.style.transform = `scaleX(${(0.4 + 1.2 * a).toFixed(3)}) translateX(${((k - 0.5) * 300).toFixed(1)}px)`;
        const fl = decay(t, 0.22, 0.5, 0.12); f.style.opacity = (fl * 0.5).toFixed(3); return { x: 0, y: 0, s: 1 + 0.03 * fl, flash: fl }; } };
    },

    // a hard punch-in with a shock ring
    impact(host, rand, brand) {
      host.innerHTML = `<div class="hk-r" style="position:absolute;left:50%;top:44%;border-radius:50%;border:10px solid ${brand.colors.primary};box-shadow:0 0 60px ${brand.colors.primary}"></div><div class="hk-f" style="position:absolute;inset:0;background:#fff;opacity:0"></div>`;
      const [r, f] = host.children;
      return { dur: 0.75, cues: [{ t: 0.0, kind: "hit" }, { t: 0.05, kind: "whoosh" }], draw(t) {
        const k = clamp(t / 0.55), d = 80 + 1900 * easeOut(k); r.style.width = r.style.height = d + "px"; r.style.margin = `${-d / 2}px 0 0 ${-d / 2}px`; r.style.opacity = (1 - k).toFixed(3); r.style.borderWidth = (12 * (1 - k) + 2) + "px";
        const fl = decay(t, 0, 0.8, 0.06); f.style.opacity = (fl * 0.6).toFixed(3); const sh = shake(t, 12 * decay(t, 0, 1, 0.16));
        return { x: sh.x, y: sh.y, s: 1 + 0.30 * (1 - easeOut(clamp(t / 0.34))), flash: fl }; } };
    },

    // darkness, then a spotlight snaps on
    spotlight(host, rand, brand) {
      host.innerHTML = `<div style="position:absolute;inset:0"></div><div class="hk-f" style="position:absolute;inset:0;background:${brand.colors.gold};opacity:0"></div>`;
      const [d, f] = host.children;
      return { dur: 0.9, cues: [{ t: 0.07, kind: "clack" }, { t: 0.1, kind: "whoosh" }], draw(t) {
        const on = t >= 0.07, k = easeOut(clamp((t - 0.07) / 0.62)), flick = (t > 0.13 && t < 0.17) ? 0.5 : 1, rad = on ? 60 + 2300 * k : 0;
        d.style.background = `radial-gradient(ellipse ${rad * 0.8}px ${rad}px at 50% 40%, rgba(0,0,0,${(1 - flick) * 0.85}) 0%, rgba(0,0,0,${(1 - flick) * 0.85 + 0.0}) 55%, rgba(0,0,0,${(0.97 * (1 - k * k)).toFixed(3)}) 100%)`;
        if (!on) d.style.background = "#000"; const fl = decay(t, 0.07, 0.5, 0.1); f.style.opacity = (fl * 0.22).toFixed(3);
        return { x: 0, y: 0, s: 1 + 0.04 * (1 - k), flash: fl }; } };
    },

    // a clapperboard snaps shut and flies off
    clap(host, rand, brand) {
      const y = brand.colors.primary, n = brand.colors.navy, stripes = Array.from({ length: 7 }, (_, i) => `<polygon points="${i * 120 - 40},0 ${i * 120 + 30},0 ${i * 120 - 10},84 ${i * 120 - 80},84" fill="${n}"/>`).join("");
      host.innerHTML = `<div class="hk-b" style="position:absolute;left:160px;top:560px;width:760px;height:560px;transform-origin:50% 50%">
        <svg width="760" height="560" viewBox="0 0 760 560" style="overflow:visible"><defs><clipPath id="hkc"><rect x="0" y="0" width="760" height="84" rx="10"/></clipPath></defs>
        <rect x="0" y="130" width="760" height="420" rx="22" fill="${n}" stroke="${y}" stroke-width="8"/><g clip-path="url(#hkc)" transform="translate(0,104)"><rect width="760" height="84" fill="${y}"/>${stripes}</g>
        <g class="arm" style="transform-origin:14px 96px"><g clip-path="url(#hkc)"><rect width="760" height="84" fill="${y}"/>${stripes}</g></g>
        <text x="380" y="330" text-anchor="middle" fill="${y}" font-family="BrandCinematic" font-size="112" letter-spacing="3">${T.esc(String(brand.name || "").toUpperCase())}</text>
        <text x="380" y="430" text-anchor="middle" fill="#fff" font-family="BrandCard" font-weight="800" font-size="40" letter-spacing="6">${T.esc(brand.handle || "")}</text></svg></div><div class="hk-f" style="position:absolute;inset:0;background:#fff;opacity:0"></div>`;
      const b = host.firstElementChild, arm = host.querySelector(".arm"), f = host.lastElementChild;
      return { dur: 0.8, cues: [{ t: 0.16, kind: "clack" }, { t: 0.3, kind: "whoosh" }], draw(t) {
        const a = -26 * (1 - easeIn(clamp((t - 0.05) / 0.11))); arm.style.transform = `rotate(${a.toFixed(2)}deg)`;
        const out = clamp((t - 0.30) / 0.32), fl = decay(t, 0.16, 0.9, 0.06); b.style.opacity = (1 - out).toFixed(3); b.style.transform = `scale(${(1 + 2.4 * easeIn(out)).toFixed(3)}) rotate(${(-6 * out).toFixed(2)}deg)`;
        f.style.opacity = (fl * 0.5).toFixed(3); const sh = shake(t, 10 * decay(t, 0.16, 1, 0.1)); return { x: sh.x, y: sh.y, s: 1 + 0.05 * decay(t, 0.16, 1, 0.12), flash: fl }; } };
    }
  };
  return { names: Object.keys(M), make(type, host, rand, brand) { host.innerHTML = ""; return (M[type] || M.impact)(host, rand, brand); },
    // put the result of draw() on the frame
    apply(stage, k) { stage.style.transform = (k.x || k.y || k.s !== 1) ? `translate(${k.x.toFixed(1)}px, ${k.y.toFixed(1)}px) scale(${k.s.toFixed(4)})` : "none"; } };
})();
