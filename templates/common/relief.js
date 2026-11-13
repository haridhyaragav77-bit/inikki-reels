// A 3D scene from one picture (AGENT.md 5.14: "Guess the Movie is 3D").
// The picture and its depth map become a real surface in space, and a camera travels through it:
// push, pull, crane, orbit, track. Near things pass faster than far things, focus falls off with distance,
// light can sweep or strike (lightning), and rain, dust and fog live inside the scene, behind and in front of objects.
// Drawn with WebGL2 (software on the cloud runner). If WebGL or the depth map is missing, use Scene (layers) instead.
window.Relief = class {
  static supported() { try { return !!document.createElement("canvas").getContext("webgl2"); } catch (e) { return false; } }

  constructor(host, rand, opt = {}) {
    this.host = host; this.rand = rand; this.key = null; this.ready = false;
    this.opt = Object.assign({ fovImage: 46, zoom: 0.78, zNear: 4.2, zFar: 13, grid: 5, scale: 0.75, fog: [0.10, 0.16, 0.24], rainCount: 900, dustCount: 220 }, opt);
    const W = host.clientWidth || 1080, H = host.clientHeight || 1620; this.W = W; this.H = H;
    host.style.overflow = "hidden";
    const sc = this.opt.scale || 0.75, c = document.createElement("canvas"); c.width = Math.round(W * sc); c.height = Math.round(H * sc); c.style.cssText = "position:absolute;inset:0;width:100%;height:100%"; host.appendChild(c);
    const gl = this.gl = c.getContext("webgl2", { preserveDrawingBuffer: true, antialias: false, alpha: false });
    this.canvas = c;
    this._programs(); this._mesh(); this._particles();
  }

  _sh(type, src) { const gl = this.gl, s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
  _prog(vs, fs) { const gl = this.gl, p = gl.createProgram(); gl.attachShader(p, this._sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, this._sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); return p; }

  _programs() {
    const common = `#version 300 es
      precision highp float;
      uniform sampler2D uDepth; uniform float uNear, uFar, uTanY, uAspect, uBg, uBgMax;
      float nearness(vec2 uv) { float d = uBg > 0.5 ? min(textureLod(uDepth, uv, 5.0).r, uBgMax) : textureLod(uDepth, uv, 1.0).r; return d; }
      vec3 world(vec2 uv, float d) { float z = 1.0 / mix(1.0 / uFar, 1.0 / uNear, d); return vec3((2.0 * uv.x - 1.0) * uAspect * uTanY, (1.0 - 2.0 * uv.y) * uTanY, -1.0) * z; }`;
    // the picture as a surface
    this.pScene = this._prog(common + `
      in vec2 aUv; uniform mat4 uVP; uniform vec2 uTexel; out vec2 vUv; out float vD; out float vTear;
      void main() { float d = nearness(aUv); vUv = aUv; vD = d; vTear = 0.0;
        if (uBg < 0.5) { vec2 e = uTexel * 5.0;      // how sharply depth jumps here: where it jumps, the surface opens to show what is behind
          vTear = max(abs(textureLod(uDepth, aUv + vec2(e.x, 0.0), 0.0).r - textureLod(uDepth, aUv - vec2(e.x, 0.0), 0.0).r), abs(textureLod(uDepth, aUv + vec2(0.0, e.y), 0.0).r - textureLod(uDepth, aUv - vec2(0.0, e.y), 0.0).r)); }
        gl_Position = uVP * vec4(world(aUv, d), 1.0); }`, `#version 300 es
      precision highp float;
      uniform sampler2D uColor; uniform float uBg, uFocus, uBlur, uFog, uTime, uFlash, uGain, uSat, uTear; uniform vec3 uFogCol, uLightDir, uLightCol;
      in vec2 vUv; in float vD; in float vTear; out vec4 o;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
      void main() {
        float a = uBg > 0.5 ? 1.0 : 1.0 - smoothstep(uTear, uTear * 2.4, max(fwidth(vD), vTear * 0.12)); if (a < 0.02) discard;
        float dd = uBg > 0.5 ? min(vD, 0.2) : vD;
        float lod = clamp(abs(dd - uFocus) * uBlur + (uBg > 0.5 ? 1.2 : 0.0), 0.0, 4.5);            // out of focus = softer
        vec3 col = textureLod(uColor, vUv, lod).rgb;
        if (uBg < 0.5) {   // light: the surface's own slope, a slow key light and the lightning strike
          vec3 n = normalize(vec3(-dFdx(vD) * 60.0, dFdy(vD) * 60.0, 1.0));
          float lit = max(dot(n, normalize(uLightDir)), 0.0);
          col *= 0.92 + 0.30 * lit; col += uLightCol * pow(lit, 3.0) * 0.08 * (0.4 + dd);
          float rim = pow(max(dot(n, normalize(vec3(-0.5, 0.75, 0.42))), 0.0), 2.0);
          col = col * (1.0 + uFlash * (0.9 + 2.2 * rim)) * mix(vec3(1.0), vec3(0.80, 0.90, 1.12), uFlash) + vec3(0.30, 0.40, 0.62) * uFlash * rim * (0.3 + 0.7 * dd);
        } else col = col * (1.0 + 1.3 * uFlash) * mix(vec3(1.0), vec3(0.80, 0.90, 1.12), uFlash) + vec3(0.10, 0.14, 0.24) * uFlash;
        float fz = pow(1.0 - dd, 1.6), fn = 0.55 + 0.45 * noise(vUv * vec2(3.0, 5.0) + vec2(uTime * 0.05, uTime * 0.02));   // fog thickens with distance and drifts
        col = mix(col, uFogCol * (1.0 + 2.2 * uFlash), clamp(uFog * fz * fn, 0.0, 0.85));
        float l = dot(col, vec3(0.299, 0.587, 0.114)); col = mix(vec3(l), col, uSat) * uGain;        // grade: brighter and richer
        float out_ = max(max(-vUv.x, vUv.x - 1.0), max(-vUv.y, vUv.y - 1.0));                        // far beyond the picture's edge: fade down
        o = vec4(col * (1.0 - smoothstep(0.05, 0.16, out_)), a);
      }`);
    // rain, dust, embers: small quads that live inside the scene (hidden behind near objects, in front of far ones)
    this.pFx = this._prog(`#version 300 es
      precision highp float;
      in vec4 aBase; in vec2 aCorner; uniform mat4 uVP; uniform float uTime, uKind; uniform vec3 uBox; out float vA; out vec2 vC;
      void main() { vec3 p = aBase.xyz; float s = aBase.w;
        if (uKind < 0.5) { float sp = 9.0 + 5.0 * s; p.z = min(p.z, -3.2); p.y = mod(p.y - uTime * sp, uBox.y) - uBox.y * 0.5; p.x += -0.16 * (p.y + uBox.y * 0.5); p += vec3(aCorner.x * 0.007 - aCorner.y * 0.045, aCorner.y * 0.30, 0.0); vA = (0.10 + 0.16 * s) * smoothstep(3.0, 5.0, -p.z); }
        else { float t = uTime * (0.25 + 0.5 * s); p += vec3(sin(t + s * 40.0) * 0.5, mod(t * (uKind > 1.5 ? 1.6 : 0.35) + s * 9.0, uBox.y) - uBox.y * 0.5 - p.y, cos(t * 0.7 + s * 20.0) * 0.4); float r = (uKind > 1.5 ? 0.035 : 0.022) * (0.5 + s); p += vec3((aCorner.x - 0.0) * r, (aCorner.y - 0.5) * 2.0 * r, 0.0); vA = (uKind > 1.5 ? 0.9 : 0.35) * (0.4 + 0.6 * abs(sin(t * 3.0 + s * 12.0))); }
        vC = aCorner; gl_Position = uVP * vec4(p, 1.0); }`, `#version 300 es
      precision highp float; in float vA; in vec2 vC; uniform vec3 uCol; uniform float uKind, uFlash; out vec4 o;
      void main() { float m = uKind < 0.5 ? 1.0 : smoothstep(1.0, 0.2, length(vec2(vC.x, vC.y * 2.0 - 1.0))); o = vec4(uCol * (1.0 + 2.0 * uFlash), vA * m); }`);
  }

  _mesh() {   // a grid a little larger than the picture, so camera moves never show a hard edge
    const gl = this.gl, g = this.opt.grid, over = 0.16, nx = Math.ceil(this.W * (1 + 2 * over) / g / 2), ny = Math.ceil(this.H * (1 + 2 * over) / g / 2);
    const v = new Float32Array((nx + 1) * (ny + 1) * 2); let k = 0;
    for (let y = 0; y <= ny; y++) for (let x = 0; x <= nx; x++) { v[k++] = -over + (1 + 2 * over) * x / nx; v[k++] = -over + (1 + 2 * over) * y / ny; }
    const idx = new Uint32Array(nx * ny * 6); k = 0;
    for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) { const a = y * (nx + 1) + x, b = a + 1, c = a + nx + 1, d = c + 1; idx[k++] = a; idx[k++] = c; idx[k++] = b; idx[k++] = b; idx[k++] = c; idx[k++] = d; }
    this.vao = gl.createVertexArray(); gl.bindVertexArray(this.vao);
    const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(this.pScene, "aUv"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
    this.nIdx = idx.length; gl.bindVertexArray(null);
  }

  _particles() {
    const gl = this.gl, r = this.rand, box = [16, 15, this.opt.zFar]; this.box = box;
    const make = n => { const b = new Float32Array(n * 6 * 6); let k = 0; const cs = [[-1, 0], [1, 0], [-1, 1], [1, 0], [1, 1], [-1, 1]];
      for (let i = 0; i < n; i++) { const x = (r() - 0.5) * box[0], y = r() * box[1], z = -(1.2 + r() * (box[2] - 1.2)), s = r(); for (const c of cs) { b[k++] = x; b[k++] = y; b[k++] = z; b[k++] = s; b[k++] = c[0]; b[k++] = c[1]; } }
      const vao = gl.createVertexArray(); gl.bindVertexArray(vao); const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, b, gl.STATIC_DRAW);
      const a = gl.getAttribLocation(this.pFx, "aBase"), c = gl.getAttribLocation(this.pFx, "aCorner"); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 4, gl.FLOAT, false, 24, 0); gl.enableVertexAttribArray(c); gl.vertexAttribPointer(c, 2, gl.FLOAT, false, 24, 16); gl.bindVertexArray(null);
      return { vao, n: n * 6 }; };
    this.rain = make(this.opt.rainCount); this.dust = make(this.opt.dustCount);
  }

  async _tex(src, mip) {
    const gl = this.gl, im = new Image(); im.src = src.startsWith("/") ? "file://" + src : src; await im.decode();
    const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im); gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.MIRRORED_REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.MIRRORED_REPEAT);
    return { t, w: im.naturalWidth, h: im.naturalHeight };
  }
  async set(image, key) {
    if (this.key === key) return; this.key = key; this.ready = false;
    this.tColor = await this._tex(image.src); this.tDepth = await this._tex(image.depth); this.tFar = await this._tex(image.far || image.src);
    this.focusAt = image.focus_depth != null ? image.focus_depth : 0.62; this.weather = image.weather || this.opt.weather || "dust"; this.ready = true;
  }

  // ---- small matrix helpers (column-major)
  static persp(fovy, aspect, n, f) { const t = 1 / Math.tan(fovy / 2), m = new Float32Array(16); m[0] = t / aspect; m[5] = t; m[10] = (f + n) / (n - f); m[11] = -1; m[14] = 2 * f * n / (n - f); return m; }
  static look(e, c, u) { const z = Relief.norm([e[0] - c[0], e[1] - c[1], e[2] - c[2]]), x = Relief.norm(Relief.cross(u, z)), y = Relief.cross(z, x), m = new Float32Array(16);
    m[0] = x[0]; m[1] = y[0]; m[2] = z[0]; m[4] = x[1]; m[5] = y[1]; m[6] = z[1]; m[8] = x[2]; m[9] = y[2]; m[10] = z[2];
    m[12] = -(x[0] * e[0] + x[1] * e[1] + x[2] * e[2]); m[13] = -(y[0] * e[0] + y[1] * e[1] + y[2] * e[2]); m[14] = -(z[0] * e[0] + z[1] * e[1] + z[2] * e[2]); m[15] = 1; return m; }
  static mul(a, b) { const o = new Float32Array(16); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3]; return o; }
  static cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  static norm(a) { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }

  // where the camera is at progress q (0..1) for each move; target is the point it looks at
  camera(q, t, move) {
    const e = T.easeInOut(Math.min(1, Math.max(0, q))), s = Math.min(1.15, Math.max(0, q)), zf = (this.opt.zNear + this.opt.zFar) * 0.5;
    let pos = [0, 0, 0], tgt = [0, 0, -zf];
    if (move === "orbit") { const a = (-0.5 + s) * 0.34; pos = [Math.sin(a) * zf, 0.25 - 0.3 * s, -zf + Math.cos(a) * zf - 0.9 * s]; }
    else if (move === "crane") { pos = [0.25 - 0.5 * s, 1.5 - 1.5 * e, 0.4 - 1.5 * e]; tgt = [0, -0.2 + 0.2 * e, -zf]; }
    else if (move === "track" || move === "right") { pos = [-1.25 + 2.5 * s, 0.05, -0.5 - 0.5 * s]; tgt = [pos[0] * 0.55, 0, -zf]; }
    else if (move === "left") { pos = [1.25 - 2.5 * s, 0.05, -0.5 - 0.5 * s]; tgt = [pos[0] * 0.55, 0, -zf]; }
    else if (move === "pull") { pos = [0.3 * (s - 0.5), -0.1 + 0.25 * s, -2.1 + 2.1 * s]; }
    else { pos = [-0.35 + 0.7 * s, 0.3 - 0.35 * s, -2.4 * s]; }                                    // push (default): travel into the scene
    pos[0] += 0.025 * Math.sin(t * 1.7) + 0.015 * Math.sin(t * 3.1); pos[1] += 0.02 * Math.sin(t * 2.3 + 1.0);   // a hand-held breath
    return { pos, tgt };
  }

  // q: how far through this scene; t: seconds; fx: { flash 0..1, shake px }
  render(q, t, move, fx = {}) {
    if (!this.ready) return; const gl = this.gl, o = this.opt, W = this.W, H = this.H;
    const tanImg = Math.tan(o.fovImage * Math.PI / 360), fovCam = 2 * Math.atan(tanImg * o.zoom), cam = this.camera(q, t, move);
    const VP = Relief.mul(Relief.persp(fovCam, W / H, 0.3, 60), Relief.look(cam.pos, cam.tgt, [0, 1, 0]));
    gl.viewport(0, 0, this.canvas.width, this.canvas.height); gl.clearColor(0.02, 0.03, 0.06, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL);
    const P = this.pScene, U = n => gl.getUniformLocation(P, n); gl.useProgram(P); gl.bindVertexArray(this.vao);
    gl.uniformMatrix4fv(U("uVP"), false, VP); gl.uniform1f(U("uNear"), o.zNear); gl.uniform1f(U("uFar"), o.zFar); gl.uniform1f(U("uTanY"), tanImg); gl.uniform1f(U("uAspect"), W / H);
    gl.uniform1f(U("uFocus"), this.focusAt); gl.uniform1f(U("uBlur"), fx.blur != null ? fx.blur : 5.0); gl.uniform1f(U("uFog"), fx.fog != null ? fx.fog : 0.5); gl.uniform3fv(U("uFogCol"), o.fog);
    gl.uniform1f(U("uTime"), t); gl.uniform1f(U("uFlash"), fx.flash || 0); gl.uniform1f(U("uGain"), fx.gain || 1.12); gl.uniform1f(U("uSat"), fx.sat || 1.18); gl.uniform1f(U("uTear"), 0.014);
    gl.uniform3fv(U("uLightDir"), [Math.sin(t * 0.45) * 0.7, 0.55, 0.6]); gl.uniform3fv(U("uLightCol"), [1.0, 0.86, 0.6]); gl.uniform2f(U("uTexel"), 1 / this.tDepth.w, 1 / this.tDepth.h);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, this.tDepth.t); gl.uniform1i(U("uDepth"), 1); gl.activeTexture(gl.TEXTURE0); gl.uniform1i(U("uColor"), 0);
    gl.disable(gl.BLEND); gl.bindTexture(gl.TEXTURE_2D, this.tFar.t); gl.uniform1f(U("uBg"), 1); gl.uniform1f(U("uBgMax"), 0.22); gl.drawElements(gl.TRIANGLES, this.nIdx, gl.UNSIGNED_INT, 0);   // what is behind
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.bindTexture(gl.TEXTURE_2D, this.tColor.t); gl.uniform1f(U("uBg"), 0); gl.drawElements(gl.TRIANGLES, this.nIdx, gl.UNSIGNED_INT, 0);   // the scene itself
    // weather, inside the scene
    const F = this.pFx, V = n => gl.getUniformLocation(F, n), w = this.weather; gl.useProgram(F); gl.depthMask(false); gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.uniformMatrix4fv(V("uVP"), false, VP); gl.uniform1f(V("uTime"), t); gl.uniform3fv(V("uBox"), this.box); gl.uniform1f(V("uFlash"), fx.flash || 0);
    if (w === "rain" || w === "storm") { gl.uniform1f(V("uKind"), 0); gl.uniform3fv(V("uCol"), [0.75, 0.85, 1.0]); gl.bindVertexArray(this.rain.vao); gl.drawArrays(gl.TRIANGLES, 0, this.rain.n); }
    gl.uniform1f(V("uKind"), w === "embers" ? 2 : 1); gl.uniform3fv(V("uCol"), w === "embers" ? [1.0, 0.55, 0.18] : [1.0, 0.92, 0.75]); gl.bindVertexArray(this.dust.vao); gl.drawArrays(gl.TRIANGLES, 0, this.dust.n);
    gl.depthMask(true); gl.bindVertexArray(null); gl.flush();
  }
};
