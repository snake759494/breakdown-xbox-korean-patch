# rebuild XMV using layout/audio of original, with new WMV2 frames (pickle from mvsub)
import struct, sys, pickle
src, pk, out = sys.argv[1:4]
COMPACT = len(sys.argv) > 4
d = open(src, 'rb').read(); P = pickle.load(open(pk, 'rb'))
nau = struct.unpack_from('<H', d, 0x20)[0]; hl = 0x24 + 12 * nau
e = int.from_bytes(P['ext'], 'big') >> 7
code = e & 7; rl = (e >> 3) & 1; tl = (e >> 4) & 1; j = (e >> 5) & 1; abt = (e >> 6) & 1; lf = (e >> 7) & 1; ms = (e >> 8) & 1
xext = struct.pack('<I', ms | lf << 1 | abt << 2 | j << 3 | tl << 4 | rl << 5 | code << 6)
# walk original packets
pk_l = []; o = 0; size = struct.unpack_from('<I', d, 4)[0]; first = True
while o < len(d) and size:
    po = hl if first else o
    nxt, v, unk = struct.unpack_from('<3I', d, po)
    asz = struct.unpack_from('<%dI' % nau, d, po + 12)
    fc = (v >> 23) & 0xFF; ext = v >> 31; vsz = (v & 0x7FFFFF) - 4 * nau
    p = po + 12 + 4 * nau; ap = p + vsz
    auds = []
    for a in asz: auds.append(d[ap:ap + (a & 0x7FFFFF)]); ap += a & 0x7FFFFF
    pk_l.append(dict(size=size, fc=fc, ext=ext, unk=unk, asz=asz, aud=auds, start=o))
    o += size; size = nxt; first = False
fr = P['frames']; ts = P['ts']; fi = 0; prev = 0
assert sum(p['fc'] for p in pk_l) == len(fr), (sum(p['fc'] for p in pk_l), len(fr))
bodies = []
for p in pk_l:
    vd = bytearray(xext if p['ext'] else b'')
    for k in range(p['fc']):
        b = fr[fi]; b = b + b'\0' * (-len(b) % 4)
        if len(b) == 0: b = b'\0' * 4
        sw = bytearray(len(b))
        for q in range(0, len(b), 4): sw[q:q + 4] = b[q:q + 4][::-1]
        dt = ts[fi] - prev; prev = ts[fi]; fi += 1
        vd += struct.pack('<I', (len(b) // 4 - 1) | (dt << 17)) + sw
    bodies.append(vd)
outb = bytearray(); hdr = bytearray(d[:hl]); sizes = []
for i, p in enumerate(pk_l):
    base = hl if i == 0 else 0
    need = base + 12 + 4 * nau + len(bodies[i]) + sum(map(len, p['aud']))
    sz = (need + 2047) // 2048 * 2048 if COMPACT else max(p['size'], (need + 2047) // 2048 * 2048)
    sizes.append(sz)
for i, p in enumerate(pk_l):
    base = hl if i == 0 else 0
    sz = sizes[i]; nxt = sizes[i + 1] if i + 1 < len(sizes) else 0
    alen = sum(map(len, p['aud']))
    vlen = sz - base - 12 - 4 * nau - alen
    vd = bodies[i] + b'\0' * (vlen - len(bodies[i]))
    pkt = bytearray(hdr if i == 0 else b'')
    pkt += struct.pack('<3I', nxt, (vlen + 4 * nau) | p['fc'] << 23 | p['ext'] << 31, p['unk'])
    pkt += struct.pack('<%dI' % nau, *p['asz']) + vd + b''.join(p['aud'])
    assert len(pkt) == sz
    outb += pkt
struct.pack_into('<I', outb, 0, sizes[1] if len(sizes) > 1 else 0)
struct.pack_into('<I', outb, 4, sizes[0]); struct.pack_into('<I', outb, 8, max(sizes))
outb += d[sum(p['size'] for p in pk_l):]  # trailing
open(out, 'wb').write(outb)
print('orig', len(d), 'new', len(outb), 'grown packets', sum(1 for a, p in zip(sizes, pk_l) if a != p['size']), 'max', hex(max(sizes)))
