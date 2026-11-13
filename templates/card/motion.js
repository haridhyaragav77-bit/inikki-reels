// The Card template's motion-graphics library (rules/motion.md, AGENT.md 5.14).
// Every graphic shows what the voice is saying. Each one has:
//   build(el, m, c)  draw the parts once per screen
//   draw(el, m, c)   place the parts for this instant (pure function of time)
//   cues(m, c)       small sounds that land with the moves, as seconds from the screen start
// c = { s, lt, vt, say, p, isNew, enter, raw(frac, d), brand }   vt = time since the voice line began, p = how far through the line
window.MOTIONS = (() => {
  const { clamp, lerp, easeOut, easeInOut, back, esc, mark } = T;
  const LEAD = 0.08;                                     // the voice starts this long after the screen
  const cueAt = (c, frac) => LEAD + frac * c.say;
  const svg = (w, h, inner, extra = "") => `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" ${extra}>${inner}</svg>`;
  const spread = (i, n, lead = 0.06, span = 0.8) => lead + span * (n > 1 ? i / n : 0);   // where in the line part i of n appears
  const pop = k => Math.max(0.01, back(k));
  const fade = (el, c) => { el.firstElementChild.style.opacity = c.enter; };
  function smooth(p) {                                    // a smooth curve through points
    let d = `M${p[0][0]},${p[0][1]}`;
    for (let i = 0; i < p.length - 1; i++) { const a = p[i - 1] || p[i], b = p[i], e = p[i + 1], f = p[i + 2] || e;
      d += ` C${(b[0] + (e[0] - a[0]) / 6).toFixed(1)},${(b[1] + (e[1] - a[1]) / 6).toFixed(1)} ${(e[0] - (f[0] - b[0]) / 6).toFixed(1)},${(e[1] - (f[1] - b[1]) / 6).toFixed(1)} ${e[0].toFixed(1)},${e[1].toFixed(1)}`; }
    return d;
  }
  const popsFor = (c, n, from, lead, span) => { const out = []; for (let i = from; i < n; i++) out.push({ at: cueAt(c, spread(i - from, n - from, lead, span)), kind: "pop" }); return out; };

  function pointsBuild(el, m, cast) {
    const items = ((cast ? m.names : m.items) || []).slice(0, 4);
    el.innerHTML = `<div class="points${cast ? " cast" : ""}">` + items.map((x, i) => `<div class="pt panel">` +
      (cast ? (m.roles && m.roles[i] ? `<small>${esc(m.roles[i])}</small>` : "") : (m.numbered === false ? "" : `<small>${String(i + 1).padStart(2, "0")}</small>`)) +
      `<b>${esc(x)}</b><i class="tick">✓</i></div>`).join("") + `</div>`;
  }
  function pointsDraw(el, m, c, cast) {
    const pts = el.querySelectorAll(".pt"), n = pts.length, act = m.active ? m.active - 1 : -1, build = cast ? m.build !== false && c.isNew : !!m.build;
    pts.forEach((p, i) => {
      const r = build ? c.raw(spread(i, n), 0.3) : (c.isNew ? clamp(c.lt / 0.35) : 1), pulse = i === act ? 1 + 0.022 * Math.sin(c.lt * 5) : 1;
      p.style.opacity = r > 0 ? 1 : 0; p.style.transform = `scale(${(pop(r) * pulse).toFixed(3)})`;
      p.classList.toggle("on", i === act && r >= 1); p.classList.toggle("done", act >= 0 && i < act);
    });
  }
  const ICON = {
    yes: `<circle cx="20" cy="20" r="18" fill="var(--c-teal)"/><path class="dr" d="M11 21l6 6 12-13" fill="none" stroke="var(--c-navy)" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1"/>`,
    wait: `<circle cx="20" cy="20" r="17" fill="none" stroke="var(--c-gold)" stroke-width="3"/><circle class="d0" cx="12" cy="20" r="3" fill="var(--c-gold)"/><circle class="d1" cx="20" cy="20" r="3" fill="var(--c-gold)"/><circle class="d2" cx="28" cy="20" r="3" fill="var(--c-gold)"/>`,
    no: `<circle cx="20" cy="20" r="18" fill="var(--c-alert)"/><path class="dr" d="M13 13l14 14M27 13l-14 14" fill="none" stroke="var(--c-text)" stroke-width="4.5" stroke-linecap="round" pathLength="1" stroke-dasharray="1"/>` };

  const M = {
    // one or two big words under the clip: the hook question, one key word
    punch: {
      sig: m => [m.text],
      build(el, m) { const n = String(m.text || "").replace(/\*/g, "").length, fs = n <= 8 ? 108 : n <= 14 ? 80 : n <= 22 ? 56 : 42;
        el.innerHTML = `<div><div class="punch${m.color === "gold" ? " gold" : ""}" style="font-size:${fs}px"><span>${mark(m.text)}</span><i class="swipe"></i></div></div>`; },
      draw(el, m, c) { const n = el.querySelector(".punch"), k = c.isNew ? back((c.lt - 0.12) / 0.42) : 1;
        n.style.opacity = c.isNew && c.lt < 0.12 ? 0 : 1; n.style.transform = `scale(${Math.max(0.01, k).toFixed(3)}) rotate(${((1 - Math.min(1, k)) * -3).toFixed(2)}deg)`;
        n.querySelector(".swipe").style.width = (84 * (c.isNew ? easeOut((c.lt - 0.4) / 0.45) : 1)).toFixed(1) + "%"; },
      cues: (m, c) => c.isNew ? [{ at: 0.12, kind: "pop" }] : [] },

    // numbered boxes: "three things", then the one being discussed lights up
    points: { sig: m => [m.items], build: (el, m) => pointsBuild(el, m, false), draw: (el, m, c) => pointsDraw(el, m, c, false),
      cues: (m, c) => m.build ? popsFor(c, Math.min(4, (m.items || []).length), 0) : (m.active ? [{ at: 0.1, kind: "pop" }] : []) },
    // name chips: who is in it
    cast: { sig: m => [m.names], build: (el, m) => pointsBuild(el, m, true), draw: (el, m, c) => pointsDraw(el, m, c, true),
      cues: (m, c) => c.isNew && m.build !== false ? popsFor(c, Math.min(4, (m.names || []).length), 0) : [] },

    // a clock draining: a deadline, time running out; a second bar can climb
    timer: { tall: true, sig: m => ["timer", m.labels, !!m.rise],
      build(el, m) { const L = m.labels || ["TIME LEFT", "TENSION"];
        const ticks = Array.from({ length: 12 }, (_, i) => `<line x1="66" y1="16" x2="66" y2="${i % 3 ? 21 : 26}" stroke="var(--c-muted)" stroke-width="2" opacity="0.55" transform="rotate(${i * 30} 66 66)"/>`).join("");
        el.innerHTML = `<div class="timer">` + svg(132, 132, `<circle cx="66" cy="66" r="58" fill="color-mix(in srgb, var(--c-navy) 60%, transparent)" stroke="rgba(255,255,255,0.08)" stroke-width="8"/><circle class="arc" cx="66" cy="66" r="58" fill="none" stroke="var(--c-gold)" stroke-width="8" stroke-linecap="round" transform="rotate(-90 66 66)" stroke-dasharray="364.4"/>${ticks}<line class="hand" x1="66" y1="66" x2="66" y2="30" stroke="var(--c-text)" stroke-width="5" stroke-linecap="round"/><circle cx="66" cy="66" r="6" fill="var(--c-text)"/>`, `style="transform-origin:50% 50%;width:164px;height:164px"`) +
          `<div class="rows"><div class="row"><span class="lbl">${esc(L[0])}</span><div class="track"><i class="a"></i></div><em class="va"></em></div>` +
          (m.rise ? `<div class="row"><span class="lbl">${esc(L[1])}</span><div class="track"><i class="b" style="background:var(--c-alert)"></i></div><em class="vb" style="color:var(--c-alert)"></em></div>` : "") + `</div></div>`; },
      draw(el, m, c) { const tm = m.time || [1, 0], tv = lerp(tm[0], tm[1], easeInOut(c.p)), low = tv < 0.3, col = low ? "var(--c-alert)" : "var(--c-gold)";
        const arc = el.querySelector(".arc"); arc.style.strokeDashoffset = (364.4 * (1 - tv)).toFixed(1); arc.setAttribute("stroke", col);
        el.querySelector(".hand").setAttribute("transform", `rotate(${(360 * (1 - tv)).toFixed(1)} 66 66)`);
        el.querySelector("svg").style.transform = `scale(${(low ? 1 + 0.05 * Math.abs(Math.sin(c.lt * 7)) : 1).toFixed(3)})`;
        const a = el.querySelector(".a"); a.style.width = (100 * tv).toFixed(1) + "%"; a.style.background = col; const va = el.querySelector(".va"); va.textContent = Math.round(100 * tv) + "%"; va.style.color = col;
        if (m.rise) { const rv = lerp(m.rise[0], m.rise[1], easeInOut(c.p)); el.querySelector(".b").style.width = (100 * rv).toFixed(1) + "%"; el.querySelector(".vb").textContent = Math.round(100 * rv) + "%"; }
        fade(el, c); },
      cues(m, c) { const out = [], n = Math.min(8, Math.max(2, Math.round(c.say / 0.5))); for (let i = 0; i < n; i++) out.push({ at: cueAt(c, i / n), kind: "tick" }); return out; } },

    // a line climbing: suspense building, stakes rising
    tension: { tall: true, sig: m => ["tension", m.points, m.label],
      build(el, m) { const W = 840, H = 270, l = 26, r = 30, t = 46, b = 30, pts = m.points && m.points.length > 1 ? m.points : [0.15, 0.45, 0.9];
        const xy = pts.map((v, i) => [l + (W - l - r) * i / (pts.length - 1), H - b - (H - t - b) * clamp(v)]); el._xy = xy; const d = smooth(xy);
        const grid = [0.33, 0.66, 1].map(g => { const y = H - b - (H - t - b) * g; return `<line x1="${l}" x2="${W - r}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,0.07)" stroke-dasharray="4 8"/>`; }).join("");
        el.innerHTML = `<div style="position:relative;height:${H}px">` + svg(W, H, `<defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c_alert()}" stop-opacity="0.38"/><stop offset="1" stop-color="${c_alert()}" stop-opacity="0"/></linearGradient><clipPath id="tc"><rect class="clip" x="0" y="0" width="0" height="${H}"/></clipPath></defs>${grid}<line x1="${l}" x2="${W - r}" y1="${H - b}" y2="${H - b}" stroke="rgba(255,255,255,0.22)" stroke-width="2"/><path d="${d} L${xy[xy.length - 1][0]},${H - b} L${xy[0][0]},${H - b} Z" fill="url(#tg)" clip-path="url(#tc)"/><path class="ln" d="${d}" fill="none" stroke="var(--c-alert)" stroke-width="8" stroke-linecap="round"/><circle class="hd" r="13" fill="var(--c-text)" stroke="var(--c-alert)" stroke-width="5"/>`, `style="position:absolute;left:0;top:0;overflow:visible"`) +
          `<span class="lbl" style="position:absolute;left:${l}px;top:4px">${esc(m.label || "TENSION")}</span>` +
          (m.peaks || []).map(pk => `<span class="pk callout-label" style="height:46px;font-size:22px;padding:0 18px;background:var(--c-alert);color:var(--c-text)">${esc(pk.text)}</span>`).join("") + `</div>`;
        const ln = el.querySelector(".ln"); el._len = ln.getTotalLength(); ln.style.strokeDasharray = el._len; },
      draw(el, m, c) { const pp = lerp(m.from || 0, m.to != null ? m.to : 1, easeInOut(c.p)), ln = el.querySelector(".ln"); ln.style.strokeDashoffset = (el._len * (1 - pp)).toFixed(1);
        const pt = ln.getPointAtLength(el._len * pp), hd = el.querySelector(".hd"); hd.setAttribute("cx", pt.x.toFixed(1)); hd.setAttribute("cy", pt.y.toFixed(1)); hd.setAttribute("r", (13 + 3 * Math.sin(c.lt * 9)).toFixed(1));
        el.querySelector(".clip").setAttribute("width", pt.x.toFixed(1));
        el.querySelectorAll(".pk").forEach((e, i) => { const pk = m.peaks[i], q = el._xy[Math.min(el._xy.length - 1, pk.at || 0)], k = clamp((pt.x - q[0] + 4) / 46), w = e.offsetWidth;
          e.style.left = clamp(q[0] - w / 2, 0, 840 - w) + "px"; e.style.top = Math.max(0, q[1] - 70) + "px"; e.style.opacity = k > 0 ? 1 : 0; e.style.transform = `scale(${pop(k).toFixed(3)})`; });
        fade(el, c); },
      cues(m, c) { const n = (m.points || [0, 0, 0]).length; return (m.peaks || []).map(pk => ({ at: cueAt(c, 0.5 - 0.5 * Math.cos(Math.PI * clamp((pk.at || 0) / (n - 1)))), kind: "pop" })); } },

    // place tabs and a "cut" streak: the film jumps between places and leaves one hanging
    switch: { sig: m => ["switch", m.places],
      build(el, m) { el.innerHTML = `<div class="switch">` + (m.places || []).slice(0, 3).map(x => `<div class="pl panel"><b>${esc(x)}</b><small></small></div>`).join("") + `<i class="streak"></i><span class="cut">${esc(m.label || "CUT")}</span></div>`; },
      draw(el, m, c) { const pls = el.querySelectorAll(".pl"), to = (m.to || 1) - 1, from = m.from ? m.from - 1 : -1, cutF = 0.36, cutD = 0.22;
        const moving = from >= 0 && from !== to, cp = moving ? clamp((c.p - cutF) / cutD) : 1;
        pls.forEach((p, i) => { const on = cp >= 1 ? i === to : i === from; p.classList.toggle("on", on);
          const land = moving ? clamp((c.vt - (cutF + cutD) * c.say) / 0.32) : (c.isNew ? clamp(c.lt / 0.35) : 1);
          p.style.transform = `scale(${(i === to && on ? 0.92 + 0.08 * back(land) : 1).toFixed(3)})`;
          const held = m.pending && (moving ? (i === from && cp >= 1) : (i !== to && m.pending_at === i + 1));
          p.querySelector("small").innerHTML = held ? `<i style="opacity:${(0.3 + 0.7 * Math.abs(Math.sin(c.lt * 5))).toFixed(2)}"></i>${esc(m.pending)}` : ""; });
        const st = el.querySelector(".streak"), ct = el.querySelector(".cut");
        if (moving && cp > 0 && cp < 1) { const a = pls[from], b = pls[to], ax = a.offsetLeft + a.offsetWidth / 2, bx = b.offsetLeft + b.offsetWidth / 2, x = lerp(ax, bx, easeInOut(cp)), tail = 170 * Math.sin(cp * Math.PI), dir = bx > ax ? 1 : -1;
          st.style.display = ""; st.style.left = (dir > 0 ? x - tail : x) + "px"; st.style.width = tail + "px"; st.style.transform = dir > 0 ? "none" : "scaleX(-1)";
          ct.style.display = ""; ct.style.left = x + "px"; ct.style.opacity = Math.sin(cp * Math.PI).toFixed(2); }
        else { st.style.display = "none"; ct.style.display = "none"; }
        fade(el, c); },
      cues: (m, c) => (m.from && m.from !== m.to) ? [{ at: cueAt(c, 0.36), kind: "whoosh" }, { at: cueAt(c, 0.58), kind: "pop" }] : [] },

    // a person, a goal, and barriers dropping between them: one want, delayed again and again
    goal: { tall: true, sig: m => ["goal", m.who, m.goal],
      build(el, m) { const W = 840, H = 250, y = 122, x0 = 90, x1 = W - 90, blocks = Array.isArray(m.blocks) ? m.blocks : Array.from({ length: m.blocks || 3 }, () => ""), n = blocks.length;
        const st = clamp(m.start || 0, 0, 0.8); el._x0 = x0 + (x1 - x0) * st;
        const bars = blocks.map((b, i) => { const x = x0 + (x1 - x0) * (st + (1 - st) * (i + 1) / (n + 1)); return `<g class="bk" data-x="${x}"><rect x="${x - 9}" y="${y - 46}" width="18" height="92" rx="6" fill="var(--c-alert)"/><text x="${x}" y="${y - 58}" text-anchor="middle" fill="var(--c-alert)" font-size="23" font-weight="800" letter-spacing="1">${esc(String(b).toUpperCase())}</text></g>`; }).join("");
        el.innerHTML = `<div style="position:relative;height:${H}px">` + svg(W, H, `<line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,0.24)" stroke-width="4" stroke-dasharray="3 12" stroke-linecap="round"/><line class="reach" x1="${x0}" x2="${x0}" y1="${y}" y2="${y}" stroke="var(--c-teal)" stroke-width="6" stroke-linecap="round"/>${bars}` +
          `<circle cx="${x0}" cy="${y}" r="32" fill="var(--c-navy)" stroke="var(--c-teal)" stroke-width="4"/><circle cx="${x0}" cy="${y - 8}" r="8" fill="var(--c-teal)"/><path d="M${x0 - 14},${y + 17} a14,13 0 0 1 28,0z" fill="var(--c-teal)"/>` +
          `<g class="gl"><circle cx="${x1}" cy="${y}" r="34" fill="var(--c-navy)" stroke="var(--c-gold)" stroke-width="4"/><path transform="translate(${x1 - 16.2},${y - 17}) scale(1.35)" d="M12 21s-7.5-4.6-10-9.2C.3 8.4 2 4.5 5.6 4.5c2 0 3.4 1.1 4.4 2.5 1-1.4 2.4-2.5 4.4-2.5 3.6 0 5.3 3.9 3.6 7.3C19.5 16.4 12 21 12 21z" fill="var(--c-gold)"/></g>` +
          `<circle class="me" cx="${x0}" cy="${y}" r="9" fill="var(--c-text)"/><text x="${x0}" y="${y + 70}" text-anchor="middle" fill="var(--c-teal)" font-size="27" font-weight="800" letter-spacing="1">${esc(String(m.who || "").toUpperCase())}</text><text x="${x1}" y="${y + 70}" text-anchor="middle" fill="var(--c-gold)" font-size="27" font-weight="800" letter-spacing="1">${esc(String(m.goal || "").toUpperCase())}</text>`, `style="overflow:visible"`) + `</div>`; },
      draw(el, m, c) { const bks = el.querySelectorAll(".bk"), n = bks.length, from = m.from || 0; let stop = 750, shake = 0;
        bks.forEach((b, i) => { const r = i < from ? 1 : c.raw(spread(i - from, n - from, 0.14, 0.7), 0.3), x = +b.dataset.x;
          b.style.opacity = r > 0 ? 1 : 0; b.setAttribute("transform", `translate(0 ${(-(1 - Math.min(1, back(r))) * 50).toFixed(1)})`);
          if (r > 0 && x < stop) stop = x; if (r > 0 && r < 1) shake = Math.sin(r * Math.PI * 4) * 6 * (1 - r); });
        const end = m.reach != null ? 90 + 660 * clamp(m.reach) : 700;                      // how far the person gets if nothing stops them
        const free = lerp(el._x0, end, easeInOut(clamp(c.p * (from ? 99 : 2.4)))), me = Math.min(free, stop - 28) + (stop < 750 ? shake * 0.5 : 0);
        el.querySelector(".me").setAttribute("cx", me.toFixed(1)); el.querySelector(".reach").setAttribute("x2", me.toFixed(1));
        el.querySelector(".gl").setAttribute("transform", `translate(${shake.toFixed(1)} 0) scale(${(1 + 0.03 * Math.sin(c.lt * 4)).toFixed(3)})`); el.querySelector(".gl").style.transformOrigin = "750px 122px";
        fade(el, c); },
      cues(m, c) { const n = Array.isArray(m.blocks) ? m.blocks.length : (m.blocks || 3), from = m.from || 0, out = []; for (let i = from; i < n; i++) out.push({ at: cueAt(c, spread(i - from, n - from, 0.14, 0.7)), kind: "thud" }); return out; } },

    // stacked bars: the recap
    list: { tall: m => (m.items || []).length >= 3, sig: m => ["list", m.items],
      build(el, m) { el.innerHTML = `<div class="list">` + (m.items || []).slice(0, 4).map((x, i) => `<div class="li panel"><i>${i + 1}</i><b>${esc(x)}</b></div>`).join("") + `</div>`; },
      draw(el, m, c) { const its = el.querySelectorAll(".li"), from = m.from || 0, nNew = its.length - from; let last = -1;
        its.forEach((r, i) => { const k = i < from ? 1 : c.raw(spread(i - from, nNew, 0.04, 0.82), 0.3); if (k > 0 && i >= from) last = i;
          r.style.opacity = k > 0 ? easeOut(k).toFixed(3) : 0; r.style.transform = `translateX(${((1 - easeOut(k)) * -30).toFixed(1)}px)`; });
        its.forEach((r, i) => r.classList.toggle("new", i === last)); },
      cues: (m, c) => popsFor(c, Math.min(4, (m.items || []).length), m.from || 0, 0.04, 0.82) },

    // a number counting up: money, days, views, years
    count: { sig: m => ["count", m.to, m.label],
      build(el, m) { el.innerHTML = `<div class="count"><div class="num">${m.prefix ? `<span class="pre">${esc(m.prefix)}</span>` : ""}<span class="val"></span>${m.suffix ? `<span class="suf">${esc(m.suffix)}</span>` : ""}</div>${m.label ? `<div class="lbl">${esc(m.label)}</div>` : ""}</div>`; },
      draw(el, m, c) { const span = 0.7, k = easeOut(clamp(c.p / span)), dec = m.decimals || 0, v = lerp(m.from || 0, m.to || 0, k);
        el.querySelector(".val").textContent = Number(v.toFixed(dec)).toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec, useGrouping: m.grouping !== false });
        const land = clamp((c.vt - span * c.say) / 0.35); el.querySelector(".num").style.transform = `scale(${(c.p >= span ? 1.12 - 0.12 * easeOut(land) : 1).toFixed(3)})`;
        fade(el, c); },
      cues(m, c) { const out = []; for (let i = 0; i < 5; i++) out.push({ at: cueAt(c, 0.7 * i / 5), kind: "tick" }); out.push({ at: cueAt(c, 0.7), kind: "ding" }); return out; } },

    // dated stops on a line: announced, shoot, release
    timeline: { sig: m => ["timeline", m.stops],
      build(el, m) { const st = (m.stops || []).slice(0, 4), n = st.length, W = 840, x0 = 90, x1 = W - 90, y = 88; el._x = st.map((_, i) => n > 1 ? x0 + (x1 - x0) * i / (n - 1) : W / 2);
        el.innerHTML = `<div style="position:relative;height:190px">` + svg(W, 190, `<line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,0.18)" stroke-width="4" stroke-linecap="round"/><line class="fill" x1="${el._x[0]}" x2="${el._x[0]}" y1="${y}" y2="${y}" stroke="var(--c-teal)" stroke-width="4" stroke-linecap="round"/>` +
          st.map((s, i) => `<circle class="nd" cx="${el._x[i]}" cy="${y}" r="13" fill="var(--c-navy)" stroke="var(--c-muted)" stroke-width="4"/><text x="${el._x[i]}" y="${y - 36}" text-anchor="middle" fill="var(--c-text)" font-size="30" font-weight="800">${esc(s.label)}</text><text x="${el._x[i]}" y="${y + 54}" text-anchor="middle" fill="var(--c-muted)" font-size="22" font-weight="700" letter-spacing="1">${esc(String(s.sub || "").toUpperCase())}</text>`).join("") +
          `<circle class="mk" cy="${y}" r="9" fill="var(--c-gold)"/>`, `style="overflow:visible"`) + `</div>`; },
      draw(el, m, c) { const X = el._x, at = clamp((m.at || 1) - 1, 0, X.length - 1), from = m.from ? m.from - 1 : Math.max(0, at - 1), k = easeInOut(clamp((c.p - 0.08) / 0.68)), x = lerp(X[from], X[at], k);
        el.querySelector(".mk").setAttribute("cx", x.toFixed(1)); el.querySelector(".fill").setAttribute("x2", x.toFixed(1));
        el.querySelectorAll(".nd").forEach((n, i) => { const reached = X[i] <= x + 1, cur = i === at && k >= 1;
          n.setAttribute("stroke", cur ? "var(--c-gold)" : reached ? "var(--c-teal)" : "var(--c-muted)"); n.setAttribute("fill", reached ? (cur ? "var(--c-gold)" : "var(--c-teal)") : "var(--c-navy)"); n.setAttribute("r", (cur ? 15 + 2.5 * Math.sin(c.lt * 6) : 13).toFixed(1)); });
        fade(el, c); },
      cues: (m, c) => [{ at: cueAt(c, 0.76), kind: "pop" }] },

    // fact rows: confirmed, awaited, not true
    status: { tall: m => (m.rows || []).length >= 3, sig: m => ["status", (m.rows || []).map(r => r.label)],
      build(el, m) { el.innerHTML = `<div class="status">` + (m.rows || []).slice(0, 4).map(r => { const st = ICON[r.state] ? r.state : "wait"; return `<div class="st panel ${st}">${svg(40, 40, ICON[st])}<b>${esc(r.label)}</b>${r.value ? `<em>${esc(r.value)}</em>` : ""}</div>`; }).join("") + `</div>`; },
      draw(el, m, c) { const rows = el.querySelectorAll(".st"), from = m.from || 0, nNew = rows.length - from;
        rows.forEach((r, i) => { const f = spread(i - from, nNew, 0.05, 0.8), k = i < from ? 1 : c.raw(f, 0.3);
          r.style.opacity = k > 0 ? easeOut(k).toFixed(3) : 0; r.style.transform = `translateY(${((1 - easeOut(k)) * 16).toFixed(1)}px)`;
          const dr = r.querySelector(".dr"); if (dr) dr.style.strokeDashoffset = i < from ? 0 : (1 - clamp((c.vt - f * c.say - 0.15) / 0.3)).toFixed(3);
          [0, 1, 2].forEach(j => { const d = r.querySelector(".d" + j); if (d) d.setAttribute("opacity", (0.3 + 0.7 * Math.abs(Math.sin(c.lt * 4 - j * 0.7))).toFixed(2)); }); }); },
      cues: (m, c) => popsFor(c, Math.min(4, (m.rows || []).length), m.from || 0, 0.05, 0.8) },

    // two names and a balance that tilts: comparing two craft choices
    versus: { sig: m => ["versus", m.left, m.right],
      build(el, m) { el.innerHTML = `<div class="versus"><div class="side l panel">${esc(m.left)}</div><div class="vs">VS</div><div class="side r panel">${esc(m.right)}</div>` +
        svg(840, 62, `<g class="beam"><line x1="165" x2="675" y1="22" y2="22" stroke="var(--c-muted)" stroke-width="5" stroke-linecap="round"/><circle cx="165" cy="22" r="10" fill="var(--c-teal)"/><circle cx="675" cy="22" r="10" fill="var(--c-teal)"/></g><path d="M420 28l-16 28h32z" fill="var(--c-muted)"/>`) + `</div>`; },
      draw(el, m, c) { const tilt = m.tilt || 0, k = easeInOut(clamp((c.p - 0.25) / 0.45)), ang = tilt * 7 * k + (1 - k) * 2.2 * Math.sin(c.lt * 6);
        el.querySelector(".beam").setAttribute("transform", `rotate(${ang.toFixed(2)} 420 22)`);
        const L = el.querySelector(".side.l"), R = el.querySelector(".side.r"), e = easeOut(c.isNew ? clamp(c.lt / 0.35) : 1);
        L.classList.toggle("win", tilt < 0 && k >= 1); R.classList.toggle("win", tilt > 0 && k >= 1);
        L.style.transform = `translateX(${((1 - e) * -60).toFixed(1)}px)`; R.style.transform = `translateX(${((1 - e) * 60).toFixed(1)}px)`;
        el.querySelector(".vs").style.transform = `scale(${pop(c.isNew ? clamp((c.lt - 0.2) / 0.35) : 1).toFixed(3)})`; fade(el, c); },
      cues: (m, c) => c.isNew ? [{ at: 0.2, kind: "pop" }] : [] },

    // quote marks, the line, who said it
    quote: { sig: m => ["quote", m.text],
      build(el, m) { el.innerHTML = `<div class="quote panel"><span class="q">“</span><p>${String(m.text || "").split(/\s+/).map(w => `<span class="qw">${esc(w)}</span>`).join(" ")}</p>${m.by ? `<small>— ${esc(m.by)}</small>` : ""}</div>`; },
      draw(el, m, c) { const ws = el.querySelectorAll(".qw"), n = ws.length; ws.forEach((w, i) => { w.style.opacity = (0.25 + 0.75 * easeOut(c.raw(spread(i, n, 0.02, 0.85), 0.25))).toFixed(2); });
        fade(el, c); el.firstElementChild.style.transform = `translateY(${((1 - c.enter) * 16).toFixed(1)}px)`; },
      cues: () => [] },

    // a ring around a detail inside the clip, with a label (drawn over the picture)
    callout: { overlay: true, sig: m => ["callout", m.at, m.label],
      build(el, m) { const W = 840, H = el.clientHeight || 460, x = (m.at ? m.at[0] : 0.5) * W, y = (m.at ? m.at[1] : 0.5) * H, r = m.r || 64, left = x > W / 2, down = y < H / 2;
        const lx = left ? x - r - 34 : x + r + 34, ly = down ? y + r * 0.7 + 24 : y - r * 0.7 - 24; el._c = { r, lx, ly, left };
        el.innerHTML = svg(W, H, `<circle class="rg" cx="${x}" cy="${y}" r="${r}" fill="none" stroke="var(--c-teal)" stroke-width="5" pathLength="1" stroke-dasharray="1" transform="rotate(-90 ${x} ${y})"/><circle class="pu" cx="${x}" cy="${y}" r="${r}" fill="none" stroke="var(--c-teal)" stroke-width="2"/><line class="ld" x1="${x + (left ? -r : r) * 0.72}" y1="${y + (down ? r : -r) * 0.72}" x2="${lx}" y2="${ly}" stroke="var(--c-teal)" stroke-width="3" pathLength="1" stroke-dasharray="1"/>`, `style="position:absolute;left:0;top:0"`) + `<span class="callout-label">${esc(m.label || "")}</span>`; },
      draw(el, m, c) { const g = el._c, t0 = (m.when != null ? m.when : 0.18) * c.say, k = clamp((c.vt - t0) / 0.4), k2 = clamp((c.vt - t0 - 0.3) / 0.3);
        el.querySelector(".rg").style.strokeDashoffset = (1 - easeOut(k)).toFixed(3); el.querySelector(".ld").style.strokeDashoffset = (1 - easeOut(k2)).toFixed(3);
        const pu = el.querySelector(".pu"), ph = (((c.vt - t0) % 1.4) + 1.4) % 1.4 / 1.4; pu.setAttribute("r", (g.r + 26 * ph).toFixed(1)); pu.setAttribute("opacity", k >= 1 ? (0.6 * (1 - ph)).toFixed(2) : 0);
        const lb = el.querySelector(".callout-label"), w = lb.offsetWidth; lb.style.left = clamp(g.left ? g.lx - w : g.lx, 8, 832 - w) + "px"; lb.style.top = (g.ly - 25) + "px"; lb.style.opacity = k2 > 0 ? 1 : 0; lb.style.transform = `scale(${pop(k2).toFixed(3)})`; },
      cues: (m, c) => [{ at: cueAt(c, m.when != null ? m.when : 0.18), kind: "pop" }] },

    // the last screen: mascot and the send pill
    cta: { sig: m => ["cta", m.text],
      build(el, m, c) { el.innerHTML = `<div class="cta"><span class="ms" style="display:inline-block">${T.mascotHTML(c.brand, 120)}</span><span class="pill">${esc(m.text || c.brand.sign_off.pill)}<i></i></span></div>`; },
      draw(el, m, c) { const k = c.isNew ? clamp((c.lt - 0.15) / 0.45) : 1, n = el.firstElementChild; n.style.opacity = k > 0 ? 1 : 0; n.style.transform = `scale(${pop(k).toFixed(3)})`;
        el.querySelector(".ms").style.transform = `translateY(${(-7 * Math.abs(Math.sin(c.lt * 3.2))).toFixed(1)}px) rotate(${(4 * Math.sin(c.lt * 3.2)).toFixed(1)}deg)`;
        const ph = (c.lt % 1.7) / 0.7; el.querySelector(".pill i").style.left = (ph <= 1 ? -80 + ph * 600 : 700) + "px"; },
      cues: (m, c) => c.isNew ? [{ at: 0.15, kind: "pop" }] : [] }
  };
  function c_alert() { return getComputedStyle(document.documentElement).getPropertyValue("--c-alert").trim() || "red"; }

  // older short names from series files → library names
  const ALIAS = { chips_in: "points", timer_dial: "timer", tension_bar: "tension", list_reveal: "list", split_compare: "versus", meme_end: "cta", send_to_friend: "cta" };
  function normalize(s) {
    let m = s.motion; if (!m) return s.cta ? [{ type: "cta", text: s.cta === true ? undefined : s.cta }] : [];
    if (typeof m === "string") m = { type: m };
    return (Array.isArray(m) ? m : [m]).map(x => Object.assign({}, x, { type: ALIAS[x.type] || x.type })).filter(x => M[x.type]).slice(0, 2);
  }
  return { M, normalize, LEAD, names: Object.keys(M) };
})();
