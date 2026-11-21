"""시작 경고 동영상(warning.xmv)의 일본어 경고문을 한글로 바꿔 WMV2 프레임(pickle)을 만듭니다.
사용법: python tools/mvwarn.py orig/romdata/movie/warning.xmv build/warn.pkl
이 영상은 한 장의 그림이 검은 화면에서 밝아졌다가 어두워지는 구성이라, 가장 밝은 프레임을
한글로 고친 뒤 각 프레임의 밝기 비율만큼 곱해 다시 만듭니다."""
import av, numpy as np, sys, os, struct, pickle, fractions, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W = os.path.dirname(os.path.abspath(__file__)) + '/..'
FONT = W + '/fonts/NanumSquareNeo-dEb.ttf'
LINES = ['이 게임에는', '폭력·호러 등', '그로테스크한 표현이', '포함되어 있습니다.']
src, out = sys.argv[1:3]
c = av.open(src); frs = []; ts = []
for p in c.demux(c.streams.video[0]):
    for f in p.decode(): frs.append(f.to_ndarray(format='rgb24')); ts.append(p.pts)
m = np.array([a.astype(np.float32).mean() for a in frs]); k = int(m.argmax()); peak = frs[k].astype(np.float32)
# 글자(흰색) 영역을 지우고 주변 그림으로 메우기
x0, y0, x1, y1 = 192, 138, 450, 326
mask = np.zeros(peak.shape[:2], np.uint8)
reg = peak[y0:y1, x0:x1]; mask[y0:y1, x0:x1] = ((reg.min(-1) > 120)).astype(np.uint8) * 255
mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
ko = cv2.inpaint(peak.astype(np.uint8), mask, 5, cv2.INPAINT_TELEA).astype(np.float32)
# 한글 경고문
SS = 4; fs = 25; f = ImageFont.truetype(FONT, fs * SS); lh = 46 * SS
w = (x1 - x0 - 16) * SS; h = lh * len(LINES)
L = Image.new('L', (w, h), 0); d = ImageDraw.Draw(L)
for i, l in enumerate(LINES):
    b = f.getbbox(l); d.text(((w - (b[2] - b[0])) // 2 - b[0], i * lh + (lh - (b[3] - b[1])) // 2 - b[1]), l, font=f, fill=255)
fill = np.asarray(L.resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
sh = np.asarray(L.filter(ImageFilter.MaxFilter(2 * SS + 1)).resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
ty = (y0 + y1) // 2 - fill.shape[0] // 2; tx = x0 + 8
r = ko[ty:ty + fill.shape[0], tx:tx + fill.shape[1]]
r *= (1 - 0.5 * sh[..., None]); r[:] = r * (1 - fill[..., None]) + 255 * fill[..., None]
os.makedirs(W + '/view', exist_ok=True); Image.fromarray(ko.clip(0, 255).astype(np.uint8)).save(W + '/view/warn_ko.png')
new = [(ko * (mi / m[k])).clip(0, 255).astype(np.uint8) for mi in m]
# 원본 XMV 패킷 구조에 맞춰 패킷별로 인코딩 (mvsub.py와 같은 방식)
Ld = open(src, 'rb').read()
nau = struct.unpack_from('<H', Ld, 0x20)[0]; hl = 0x24 + 12 * nau
plan = []; o = 0; size = struct.unpack_from('<I', Ld, 4)[0]
while o < len(Ld) and size:
    po = o + (hl if o == 0 else 0)
    nxt, v = struct.unpack_from('<2I', Ld, po); asz = struct.unpack_from('<%dI' % nau, Ld, po + 12)
    bud = 0x64000 - (hl if o == 0 else 0) - 12 - 4 * nau - sum(a & 0x7FFFFF for a in asz) - 4
    plan.append(((v >> 23) & 0xFF, bud)); o += size; size = nxt
def enc(fr, br):
    vs = av.CodecContext.create('wmv2', 'w'); vs.width, vs.height = 640, 480; vs.pix_fmt = 'yuv420p'
    vs.time_base = fractions.Fraction(1, 30); vs.framerate = 30; vs.gop_size = 600
    br = max(br, 20000); vs.bit_rate = br; vs.options = {'maxrate': str(br), 'bufsize': str(br * 2)}
    r = []
    for i, a in enumerate(fr):
        vf = av.VideoFrame.from_ndarray(a, format='rgb24'); vf.pts = i; r += [bytes(p) for p in vs.encode(vf)]
    r += [bytes(p) for p in vs.encode(None)]; assert len(r) == len(fr); return r, bytes(vs.extradata)
SKIP = bytes.fromhex('8affffff fe500000'.replace(' ', ''))
pk = []; ext = None; i = 0; prev = None
for fc, bud in plan:
    buf = new[i:i + fc]; i += fc
    sk = []
    for a in buf: sk.append(prev is not None and np.array_equal(prev, a)); prev = a
    real = [a for a, s in zip(buf, sk) if not s]; bud -= 12 * (len(buf) - len(real)); r = []
    if real:
        br = int(max(bud, 8000) * 8 * 30 / len(real) * 0.9)
        for _ in range(14):
            r, ext = enc(real, br); n = sum(len(x) + 7 for x in r)
            if n <= bud: break
            br = int(br * bud / n * 0.92)
    it = iter(r); pk += [SKIP if s else next(it) for s in sk]
assert i == len(new) == len(pk)
pickle.dump(dict(ext=ext, frames=pk, ts=ts), open(out, 'wb')); print('warning frames', len(pk))
