import av, numpy as np, sys, json
from PIL import Image
A, B, out = sys.argv[1], sys.argv[2], sys.argv[3]
idx = [int(x) for x in sys.argv[4].split(',')]
def get(fn, want_ts):
    c = av.open(fn); res = {}; prev = None
    ws = sorted(want_ts); k = 0
    for f in c.decode(c.streams.video[0]):
        while k < len(ws) and f.pts > ws[k]:
            res[ws[k]] = prev; k += 1
        prev = f.to_ndarray(format='rgb24')
        if k >= len(ws): break
    while k < len(ws): res[ws[k]] = prev; k += 1
    return res
c = av.open(B); ts = [f.pts for f in c.demux(c.streams.video[0]) if f.size]
want = [ts[i] for i in idx]
rb = get(B, want); ra = get(A, want)
rows = []
for t in want:
    rows.append(np.concatenate([rb[t], ra[t]], 1))
im = Image.fromarray(np.concatenate(rows, 0)); im = im.resize((im.width // 2, im.height // 2))
im.save(out)
