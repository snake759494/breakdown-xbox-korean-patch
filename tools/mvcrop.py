import av, numpy as np, sys, json
from PIL import Image, ImageDraw
B, segf, out = sys.argv[1], sys.argv[2], sys.argv[3]
Y0, Y1 = int(sys.argv[4]), int(sys.argv[5])
segs = json.load(open(segf)); want = {(s['f0'] + s['f1']) // 2: k for k, s in enumerate(segs)}
c = av.open(B); rows = {}
for i, f in enumerate(c.decode(c.streams.video[0])):
    if i in want: rows[want[i]] = f.to_ndarray(format='rgb24')[Y0:Y1]
    if len(rows) == len(want): break
ims = []
for k in range(len(segs)):
    im = Image.fromarray(rows[k]); ImageDraw.Draw(im).text((4, 2), str(k), fill=(255, 0, 0)); ims.append(np.asarray(im))
    ims.append(np.full((3, ims[-1].shape[1], 3), (255, 0, 255), np.uint8))
Image.fromarray(np.concatenate(ims, 0)).save(out)
