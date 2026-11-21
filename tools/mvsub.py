# render Korean subtitles over clean video (A) following subtitled video (B) timeline, encode WMV2 frames
import av, numpy as np, sys, json, pickle
from PIL import Image, ImageDraw, ImageFont
W = __import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/..'
FONT = W + '/fonts/NanumSquareNeo-cBd.ttf'
A, B, segf, textf, out = sys.argv[1:6]
BR = int(sys.argv[6]); FS = int(sys.argv[7])
segs = json.load(open(segf)); texts = json.load(open(textf, encoding='utf8'))  # {segidx: text or null}

def frames(fn):
    c = av.open(fn); last = None
    for p in c.demux(c.streams.video[0]):
        if not p.size: continue
        fs = p.decode()
        if fs: last = fs[-1].to_ndarray(format='rgb24')
        yield p.pts, last
def pairs():
    ga = frames(A); cur = next(ga); nxt = next(ga, None)
    for t, img in frames(B):
        while nxt is not None and nxt[0] <= t:
            cur = nxt; nxt = next(ga, None)
        yield t, img, cur[1]
core = {}
for k, s in enumerate(segs):
    for f in range(s['f0'], s['f1'] + 1): core[f] = k
def win(f):
    r = []
    for k, s in enumerate(segs):
        if texts.get(str(k)) is None: continue
        if s['f0'] - 15 <= f <= s['f1'] + 15 and (core.get(f, k) == k or s['f0'] == s['f1'] or segs[core[f]]['f0'] == segs[core[f]]['f1']):
            r.append(k)
    return r
def count(k, img, ref):
    y0, y1, x0, x1 = segs[k]['bb']; y0 = max(0, y0 - 4); x0 = max(0, x0 - 4)
    a = img[y0:y1 + 5, x0:x1 + 5].astype(np.int16); b = ref[y0:y1 + 5, x0:x1 + 5].astype(np.int16)
    return int(((np.abs(a - b).max(-1) > 40) & (a.max(-1) > 110)).sum())
# pass 1
cnt = []
pi_, pr_ = None, None
for f, (t, img, ref) in enumerate(pairs()):
    if img is pi_ and ref is pr_ and set(cnt[-1]) == set(win(f)): cnt.append(dict(cnt[-1]))
    else: cnt.append({k: count(k, img, ref) for k in win(f)})
    pi_, pr_ = img, ref
ref = {}
for k, s in enumerate(segs):
    v = [cnt[f].get(k, 0) for f in range(s['f0'], s['f1'] + 1)]
    ref[k] = max(1, float(np.median(v)) * 0.85)
SS = 3; font = ImageFont.truetype(FONT, FS * SS)
cache = {}
def layer(k):
    if k in cache: return cache[k]
    lines = texts[str(k)].split('\n'); lh = int(FS * 1.25) * SS
    ws = [font.getbbox(l)[2] for l in lines]; w = max(ws) + 8 * SS; h = lh * len(lines) + 8 * SS
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text(((w - ws[i]) // 2, 4 * SS + i * lh), l, font=font, fill=255)
    fill = np.asarray(im.resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
    from PIL import ImageFilter
    sh = np.asarray(im.filter(ImageFilter.MaxFilter(2 * SS + 1)).filter(ImageFilter.GaussianBlur(SS)).resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
    cache[k] = (fill, sh); return cache[k]
def draw(img, k, al):
    fill, sh = layer(k); h, w = fill.shape
    y0, y1, x0, x1 = segs[k]['bb']
    cx = (x0 + x1) // 2; x = max(0, min(640 - w, cx - w // 2)); y = max(0, min(480 - h, y1 + 6 - h))
    r = img[y:y + h, x:x + w].astype(np.float32)
    s = (sh * 0.75 * al)[..., None]; r = r * (1 - s)
    a = (fill * al)[..., None]; r = r * (1 - a) + 255 * a
    img[y:y + h, x:x + w] = np.clip(r, 0, 255).astype(np.uint8)
import struct
L = open(sys.argv[9] if len(sys.argv) > 9 else B, 'rb').read()
nau = struct.unpack_from('<H', L, 0x20)[0]; hl = 0x24 + 12 * nau
plan = []; o = 0; size = struct.unpack_from('<I', L, 4)[0]
while o < len(L) and size:
    po = o + (hl if o == 0 else 0)
    nxt, v = struct.unpack_from('<2I', L, po)
    asz = struct.unpack_from('<%dI' % nau, L, po + 12)
    fc = (v >> 23) & 0xFF
    bud = 0x64000 - (hl if o == 0 else 0) - 12 - 4 * nau - sum(a & 0x7FFFFF for a in asz) - 4
    plan.append((fc, bud)); o += size; size = nxt
def enc(frs, br):
    vs = av.CodecContext.create('wmv2', 'w'); vs.width, vs.height = 640, 480; vs.pix_fmt = 'yuv420p'
    vs.time_base = __import__('fractions').Fraction(1, 30); vs.framerate = 30
    vs.bit_rate = br; vs.gop_size = 600
    br = max(br, 20000); vs.bit_rate = br; vs.options = {'maxrate': str(br), 'bufsize': str(br * 2)}
    r = []
    for k, fr in enumerate(frs):
        vf = av.VideoFrame.from_ndarray(fr, format='rgb24'); vf.pts = k
        r += [bytes(p) for p in vs.encode(vf)]
    r += [bytes(p) for p in vs.encode(None)]
    assert len(r) == len(frs)
    return r, bytes(vs.extradata)
pk = []; ts = []; buf = []; pi = 0; ext = None; previmg = [None]; allbuf = []
SKIP = bytes.fromhex('8affffff fe500000'.replace(' ',''))
def flush():
    global pi, ext
    fc, bud = plan[pi]; pi += 1
    real = [k for k, (fr, sk) in enumerate(buf) if not sk]
    nsk = len(buf) - len(real); bud -= nsk * 12
    r = []; n = 0; br = 0
    if real:
        frs = [buf[k][0] for k in real]
        br = int(max(bud, 8000) * 8 * 30 / len(frs) * 0.9)
        for tr in range(14):
            r, ext = enc(frs, br)
            n = sum(len(x) + 7 for x in r)
            if n <= bud: break
            br = int(br * bud / n * 0.92)
    it = iter(r)
    for fr, sk in buf: pk.append(SKIP if sk else next(it))
    print(pi - 1, len(buf), len(real), bud, n, br, 'OVER' if n > bud else '', flush=True)
    buf.clear()
for f, (t, img, base) in enumerate(pairs()):
    o = base.copy()
    for k in cnt[f]:
        al = min(1.0, cnt[f][k] / ref[k])
        if al > 0.03: draw(o, k, al)
    if f in (json.loads(sys.argv[8]) if len(sys.argv) > 8 else []): Image.fromarray(o).save(W + '/view/mv/r_%04d.png' % f)
    sk = previmg[0] is not None and np.array_equal(previmg[0], o)
    previmg[0] = o
    buf.append((o, sk)); ts.append(t)
    if len(buf) == plan[pi][0]:
        if BR > 0: allbuf.append(list(buf)); buf.clear(); pi += 1
        else: flush()
if BR > 0:
    real = [fr for b in allbuf for fr, sk in b if not sk]
    br = BR
    for tr in range(20):
        r, ext = enc(real, br); it = iter(r); pk = []; worst = 0
        for (fc, bud), b in zip(plan, allbuf):
            n = 0
            for fr, sk in b:
                x = SKIP if sk else next(it); pk.append(x); n += len(x) + 4 + (-len(x) % 4)
            worst = max(worst, n / max(bud, 1))
        print('br', br, 'worst', round(worst, 3), flush=True)
        if worst <= 1: break
        br = int(br / worst * 0.95)
assert not buf and len(pk) == len(ts)
pickle.dump(dict(ext=ext, frames=pk, ts=ts), open(out, 'wb'))
print('frames', len(pk), 'bytes', sum(map(len, pk)), 'ext', ext.hex())
