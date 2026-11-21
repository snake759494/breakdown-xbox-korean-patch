import struct
def parse(d):
    hdr = struct.unpack_from('<3I4sI3IHH', d, 0)
    nau = hdr[8]; o = 0x24
    aud = [d[o+12*i:o+12*i+12] for i in range(nau)]
    first = hdr[1]
    pkts = []; o = o + 12*nau; hdrlen = o; size = first - hdrlen
    while o < len(d) and size:
        nxt, v, unk = struct.unpack_from('<3I', d, o)
        asz = list(struct.unpack_from('<%dI' % nau, d, o+12))
        p = o + 12 + 4*nau
        vsize = (v & 0x7FFFFF) - 4*nau; fc = (v >> 23) & 0xFF; ext = v >> 31
        vdat = d[p:p+vsize]
        apos = p + vsize; auds = []
        for a in asz:
            a &= 0x7FFFFF; auds.append(d[apos:apos+a]); apos += a
        pkts.append(dict(off=o, size=size, nxt=nxt, v=v, unk=unk, fc=fc, ext=ext, vdat=vdat, aud=auds, asz=asz, end=apos))
        o += size; size = nxt
    return hdr, aud, pkts
def frames(p):
    vd = p['vdat']; q = 0; ext = None
    if p['ext']: ext = vd[:4]; q = 4
    out = []
    for i in range(p['fc']):
        h = struct.unpack_from('<I', vd, q)[0]
        n = (h & 0x1FFFF) * 4 + 4
        out.append((h >> 17, vd[q+4:q+n])); q += n + 0
    return ext, out, q
