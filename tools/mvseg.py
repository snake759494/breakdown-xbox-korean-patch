import av, numpy as np, sys, json
A, B, out = sys.argv[1], sys.argv[2], sys.argv[3]
Y0, Y1 = int(sys.argv[4]), int(sys.argv[5])
def frames(fn):
    c = av.open(fn); last = None
    for p in c.demux(c.streams.video[0]):
        if not p.size: continue
        fs = p.decode()
        if fs: last = fs[-1].to_ndarray(format='rgb24')
        yield p.pts, last
ga = frames(A); cur = next(ga); nxt = next(ga, None)
segs = []; prev = None; i = -1
for t, img in frames(B):
    i += 1
    while nxt is not None and nxt[0] <= t:
        cur = nxt; nxt = next(ga, None)
    reg = img[Y0:Y1].astype(np.int16); ref = cur[1][Y0:Y1].astype(np.int16)
    m = (np.abs(reg - ref).max(-1) > 80) & (reg.min(-1) > 170)
    n = int(m.sum())
    if n < 150:
        prev = None; continue
    if prev is not None and (m & prev).sum() > 0.6 * min(n, prev.sum()):
        s = segs[-1]; s['f1'] = i; s['t1'] = t
        ys, xs = np.nonzero(m); s['bb'] = [min(s['bb'][0], int(ys.min())+Y0), max(s['bb'][1], int(ys.max())+Y0), min(s['bb'][2], int(xs.min())), max(s['bb'][3], int(xs.max()))]
    else:
        ys, xs = np.nonzero(m)
        segs.append(dict(f0=i, f1=i, t0=t, t1=t, bb=[int(ys.min())+Y0, int(ys.max())+Y0, int(xs.min()), int(xs.max())]))
    prev = m
json.dump(segs, open(out, 'w'), indent=0)
for k, s in enumerate(segs): print(k, s)
