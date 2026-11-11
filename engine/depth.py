"""Depth layers for a still picture, so near and far parts can move at different speeds
(AGENT.md 5.7; archive 13.3). Free: a small depth model on the runner's CPU, no keys.

    layers(image, outdir) → ([{"src": file, "depth": 0..1}, ...] far → near, source)

source is "model" when the depth model ran, "simple" when it was not available and a simpler split was
used (the reel still renders: fail soft)."""
import os

import numpy as np
from PIL import Image, ImageFilter

from .settings import ENGINE

CACHE = os.path.expanduser("~/.cache/inikki")
_SESSION = {"tried": False, "s": None}


def _model():
    if _SESSION["tried"]:
        return _SESSION["s"]
    _SESSION["tried"] = True
    cfg = ENGINE.get("depth", {})
    try:
        import onnxruntime as ort
        import requests
    except ImportError:
        return None
    path = os.path.join(CACHE, cfg.get("file", "depth_model.onnx"))
    if not os.path.exists(path) or os.path.getsize(path) < 5_000_000:
        os.makedirs(CACHE, exist_ok=True)
        for url in cfg.get("model_urls", []):
            try:
                with requests.get(url, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(path + ".part", "wb") as f:
                        for chunk in r.iter_content(1 << 20):
                            f.write(chunk)
                os.replace(path + ".part", path)
                break
            except Exception as e:
                print("depth model download failed:", url.split("/")[-1], str(e)[:120])
    if not os.path.exists(path):
        return None
    try:
        o = ort.SessionOptions()
        o.intra_op_num_threads = int(cfg.get("threads", 2))
        _SESSION["s"] = ort.InferenceSession(path, o, providers=["CPUExecutionProvider"])
    except Exception as e:
        print("depth model could not start:", str(e)[:160])
    return _SESSION["s"]


def _box(a, r, axis):
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    return ((np.take(c, range(2 * r + 1, 2 * r + 1 + n), axis=axis) - np.take(c, range(0, n), axis=axis)) / (2 * r + 1)).astype(np.float32)


def _blur(a, radius):
    """Soft blur of a float picture (three box passes, close to a Gaussian)."""
    r = max(1, int(round(radius * 0.87)))
    a = a.astype(np.float32)
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a


def depth_map(img, local=False):
    """Float array HxW in 0..1, 1 = nearest. Returns (depth, source)."""
    W, H = img.size
    sess = None if local else _model()
    if sess is not None:
        try:
            inp = sess.get_inputs()[0]
            shp = inp.shape
            h = shp[2] if isinstance(shp[2], int) else int(round(518 * H / W / 14)) * 14
            w = shp[3] if isinstance(shp[3], int) else 518
            x = np.asarray(img.convert("RGB").resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0
            x = (x - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
            y = sess.run(None, {inp.name: x.transpose(2, 0, 1)[None]})[0]
            d = np.squeeze(y).astype(np.float32)
            d = (d - d.min()) / max(1e-6, float(d.max() - d.min()))          # the model gives nearness: larger = nearer
            d = np.asarray(Image.fromarray((d * 65535).astype(np.uint16)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 65535.0
            return np.clip(d, 0, 1), "model"
        except Exception as e:
            print("depth model failed on this picture:", str(e)[:160])
    # simple stand-in: the ground rises toward the viewer, the middle of the frame holds the subject
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    blob = np.exp(-((xx / 0.55) ** 2 + ((yy - 0.6) / 0.28) ** 2))
    d = 0.62 * yy ** 1.3 + 0.38 * blob
    d = (d - d.min()) / max(1e-6, float(d.max() - d.min()))
    return d.astype(np.float32), "simple"


def _cuts(d):
    """Two thresholds that split depth into far / middle / near (three-class Otsu), with a guard against tiny layers."""
    hist, edges = np.histogram(d, bins=48, range=(0, 1))
    p = hist / max(1, hist.sum())
    mids = (edges[:-1] + edges[1:]) / 2
    cp, cm = np.cumsum(p), np.cumsum(p * mids)
    best, pick = -1.0, (16, 34)
    for a in range(4, 40):
        for b in range(a + 4, 46):
            w0, w1, w2 = cp[a], cp[b] - cp[a], 1 - cp[b]
            if min(w0, w1, w2) < 0.1:
                continue
            m0, m1, m2 = cm[a] / w0, (cm[b] - cm[a]) / w1, (cm[-1] - cm[b]) / w2
            var = w0 * m0 * m0 + w1 * m1 * m1 + w2 * m2 * m2
            if var > best:
                best, pick = var, (a, b)
    if best < 0:
        q = np.quantile(d, [0.45, 0.78])
        return float(q[0]), float(q[1])
    return float(edges[pick[0] + 1]), float(edges[pick[1] + 1])


def _fill(rgb, hole):
    """Paint over a hole with the colours around it (so nothing shows when a nearer layer slides aside)."""
    H, W = hole.shape
    sw = 320
    sh = max(8, int(round(H * sw / W)))
    small = np.asarray(Image.fromarray(rgb).resize((sw, sh), Image.BILINEAR), dtype=np.float32)
    keep = 1.0 - np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).resize((sw, sh), Image.BILINEAR), dtype=np.float32) / 255.0
    keep = (keep > 0.98).astype(np.float32)
    out = small.copy()
    left = keep.copy()
    for radius in (4, 10, 24, 60):
        den = _blur(left, radius)
        est = np.stack([_blur(out[..., c] * left, radius) / np.maximum(den, 1e-4) for c in range(3)], axis=-1)
        take = (left < 0.5) & (den > 0.02)
        out[take] = est[take]
        left = np.where(take, 1.0, left)
    out = np.stack([_blur(out[..., c], 2.0) for c in range(3)], axis=-1)
    up = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC))
    grow = np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(4)), dtype=np.float32)[..., None] / 255.0
    return (rgb * (1 - grow) + up * grow).astype(np.uint8)


def layers(image_path, outdir, local=False):
    os.makedirs(outdir, exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    if img.width > 1080:
        img = img.resize((1080, round(img.height * 1080 / img.width)), Image.LANCZOS)
    rgb = np.asarray(img)
    d, source = depth_map(img, local)
    if source == "simple" and not local:
        # no depth model: do not guess a split (it would show seams); the picture moves as one piece instead
        return [{"src": image_path, "depth": 0.5}], source
    d = _blur(d, max(2.0, img.width / 300))
    t1, t2 = _cuts(d)

    def alpha(mask):
        a = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.5))
        return np.asarray(a)

    near, mid = d > t2, d > t1
    far_rgb = _fill(rgb, mid)                       # everything nearer than the background is painted over
    mid_rgb = _fill(rgb, near)                      # the nearest part is painted over in the middle layer
    out = []
    p = os.path.join(outdir, "far.jpg")
    Image.fromarray(far_rgb).filter(ImageFilter.GaussianBlur(1.3)).save(p, quality=92)     # the far layer is a touch soft (depth of field)
    out.append({"src": p, "depth": 0.0})
    p = os.path.join(outdir, "mid.png")
    Image.fromarray(np.dstack([mid_rgb, alpha(mid)])).save(p, compress_level=1)
    out.append({"src": p, "depth": 0.5})
    p = os.path.join(outdir, "near.png")
    Image.fromarray(np.dstack([rgb, alpha(near)])).save(p, compress_level=1)
    out.append({"src": p, "depth": 1.0})
    return out, source
