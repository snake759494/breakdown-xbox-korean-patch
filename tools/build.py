import sys, os, json, struct, collections, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
T = os.path.dirname(os.path.abspath(__file__)); W = T + '/..'
sys.path.insert(0, T)
import cap, listpak, nut, ko, isopatch

ISO = sys.argv[1] if len(sys.argv) > 1 else W + '/test.iso'
SRC = os.environ.get('SRC_ISO', W + '/orig.iso')
FONT_SYS = W + '/fonts/NanumSquareNeo-bRg.ttf'
FONT_CAP = W + '/fonts/NanumSquareNeo-cBd.ttf'

# ---------------- text ----------------
tr, miss = ko.load_units(); assert not miss, miss

def runs_of(tokens):
    """group tokens -> list of ('run',[codes]) / ('tok',token)"""
    out = []
    for k, v in tokens:
        if k == 'c' and (v in (1, 3) or v >= 0x100):
            if out and out[-1][0] == 'run': out[-1][1].append(v)
            else: out.append(('run', [v]))
        else: out.append(('tok', (k, v)))
    return out

def run_text(codes, chf):
    return ''.join('\n' if c == 1 else ' ' if c == 3 else chf(c) for c in codes)

def korean_strings(c, sysf):
    """c = parsed english CAP; return list of (idx,x,items) items: str (text) or token"""
    chf = cap.charfun(c); res = []
    for idx, x, s in c['strs']:
        rs = runs_of(cap.tokens(s))
        texts = [run_text(v, chf) for k, v in rs if k == 'run']
        key = [(t.replace('\n', '⏎') if sysf else t.replace('\n', ' ')).strip() for t in texts]
        segs = [t for t in key if t]
        if not segs:
            res.append((idx, x, [('tok', t) if k == 'tok' else ('txt', run_text(t, chf)) for k, t in rs])); continue
        kot = tr[' ¦ '.join(segs)].split('¦')
        assert len(kot) == len(segs), (segs, kot)
        items = []; j = 0
        for k, v in rs:
            if k == 'tok': items.append(('tok', v)); continue
            t = run_text(v, chf)
            k2 = (t.replace('\n', '⏎') if sysf else t.replace('\n', ' ')).strip()
            if not k2: items.append(('txt', t)); continue
            s2 = kot[j]
            if j == 0: s2 = s2.lstrip()
            if j == len(kot) - 1: s2 = s2.rstrip()
            # keep original surrounding whitespace for icon-adjacent segments
            items.append(('ko', s2.replace('⏎', '\n'))); j += 1
        res.append((idx, x, items))
    return res

# ---------------- glyph rendering ----------------
class Face:
    def __init__(s, path, cell, size, outline):
        s.f = ImageFont.truetype(path, size); s.cell = cell; s.outline = outline
        b = s.f.getbbox('한글홝')
        s.yoff = (cell - (b[3] - b[1])) // 2 - b[1]
    def adv(s, ch):
        if ch == ' ': return None
        return max(1, int(math.ceil(s.f.getlength(ch)))) + 2 * s.outline + (1 if s.outline else 0)
    def render(s, ch):
        w = s.adv(ch); h = s.cell; SS = 4
        im = Image.new('L', (w * SS, h * SS), 0)
        d = ImageDraw.Draw(im)
        fbig = ImageFont.truetype(s.f.path, s.f.size * SS)
        d.text(((s.outline) * SS, s.yoff * SS), ch, font=fbig, fill=255)
        fill = np.asarray(im.resize((w, h), Image.LANCZOS), dtype=np.float32) / 255
        fill = np.clip(fill, 0, 1)
        if s.outline:
            big = im.filter(ImageFilter.MaxFilter(2 * s.outline * SS + 1))
            ol = np.asarray(big.resize((w, h), Image.LANCZOS), dtype=np.float32) / 255
            ol = np.clip(ol, 0, 1)
        else: ol = None
        return fill, ol

FS = Face(FONT_SYS, 18, 16, 0)
FC = Face(FONT_CAP, 28, 24, 1)

# ---------------- textures ----------------
def tim_info(b): return nut.parse(b)

class Atlas:
    """packs glyphs into a TIM2 texture (rows of fixed height)"""
    def __init__(s, texid, b, cell, mode, keep=None):
        s.texid = texid; s.b = bytearray(b); s.i = tim_info(b); s.cell = cell; s.mode = mode
        w, h = s.i['w'], s.i['h']; s.w, s.h = w, h
        _, px, pal = nut.decode(bytes(b))
        s.keep = keep  # list of rects to keep (x,y,w,h) from original
        if mode == 'sys':
            s.px = np.full((h, w), 255, np.uint8)
            if keep:
                for x, y, ww, hh in keep: s.px[y:y+hh, x:x+ww] = px[y:y+hh, x:x+ww]
        else:
            s.px = np.zeros((h, w), np.uint8)
        s.x = 0; s.y = 0; s.full = False
        s.blocked = keep or []
    def _overlap(s, x, y, w, h):
        for bx, by, bw, bh in s.blocked:
            if x < bx + bw and bx < x + w and y < by + bh and by < y + h: return bx + bw
        return None
    def place(s, w):
        while True:
            if s.y + s.cell > s.h: return None
            if s.x + w > s.w: s.x = 0; s.y += s.cell; continue
            o = s._overlap(s.x, s.y, w, s.cell)
            if o is not None: s.x = o; continue
            p = (s.x, s.y); s.x += w; return p
    def put(s, p, fill, ol):
        x, y = p; h, w = fill.shape
        if s.mode == 'sys':
            idx = np.where(fill < 1 / 32, 255, np.clip(np.round(fill * 16) - 1, 0, 15)).astype(np.uint8)
        else:
            f = np.clip(np.round(fill * 15), 0, 15).astype(np.int32)
            o = np.clip(np.round(ol * 15), 0, 15).astype(np.int32)
            idx = (f * 16 + o).astype(np.uint8)
        s.px[y:y+h, x:x+w] = idx
    def palette(s):
        pal = np.zeros((256, 4), np.uint8)
        if s.mode == 'sys':
            for k in range(16): pal[k] = (255, 255, 255, 16 * (k + 1) - (1 if k == 15 else 0))
            pal[255] = (0, 0, 0, 0)
        else:
            for f in range(16):
                for o in range(16):
                    fa = f / 15; oa = o / 15; A = fa + oa * (1 - fa)
                    C = 255 * fa / A if A > 0 else 0
                    pal[f * 16 + o] = (round(C), round(C), round(C), round(A * 255))
        return pal
    def bytes(s):
        i = s.i; m = nut.morton(s.w, s.h)
        buf = np.zeros(s.w * s.h, np.uint8); buf[m.ravel()] = s.px.ravel()
        b = s.b; b[i['pix']:i['pix'] + s.w * s.h] = buf.tobytes()
        b[i['pal']:i['pal'] + 1024] = s.palette().tobytes()
        return bytes(b)

def fill_glyphs(face, atlases, chars, glyph_tab):
    """glyph_tab: dict ch -> (font_index, x, y, w, h)"""
    ai = 0
    for ch in chars:
        if ch in glyph_tab: continue
        w = face.adv(ch)
        while True:
            if ai >= len(atlases): raise RuntimeError('atlas full at %r' % ch)
            p = atlases[ai].place(w)
            if p: break
            ai += 1
        fill, ol = face.render(ch)
        atlases[ai].put(p, fill, ol)
        glyph_tab[ch] = (ai, p[0], p[1], w, face.cell)

# ---------------- CAP encode ----------------
def wrap(text, face, limit):
    sp = face.space
    def wlen(t): return sum(face.adv(c) or sp for c in t)
    out = []
    for para in text.split('\n'):
        words = para.split(' ')
        if wlen(para) <= limit or len(words) == 1: out.append(para); continue
        # greedy line count
        n = 1; lw = 0
        for wd in words:
            ww = wlen(wd)
            if lw == 0: lw = ww
            elif lw + sp + ww <= limit: lw += sp + ww
            else: n += 1; lw = ww
        if n == 2:
            best = None
            for k in range(1, len(words)):
                a = ' '.join(words[:k]); b = ' '.join(words[k:])
                m = max(wlen(a), wlen(b))
                if m <= limit and (best is None or m < best[0]): best = (m, a, b)
            if best: out += [best[1], best[2]]; continue
        line = ''; lw = 0
        for wd in words:
            ww = wlen(wd)
            if line == '': line, lw = wd, ww
            elif lw + sp + ww <= limit: line, lw = line + ' ' + wd, lw + sp + ww
            else: out.append(line); line, lw = wd, ww
        out.append(line)
    return '\n'.join(out)

def encode(items, gtab, face, limit, nbase):
    codes = []
    for k, v in items:
        if k == 'tok':
            t, val = v
            if t == 't': codes += [6] + list(struct.unpack('<HH', struct.pack('<f', val)))
            elif t == 'i': codes += [0xc, len(val)] + list(val)
            else: codes.append(val)
        else:
            text = wrap(v, face, limit) if (k == 'ko' and limit) else v
            for ch in text:
                if ch == '\n': codes.append(1)
                elif ch == ' ': codes.append(3)
                else: codes.append(0x100 + gtab[ch])
    return codes

# ---------------- main ----------------
def main():
    en = {}
    src = open(SRC, 'rb')
    paks = {}
    for l in open(W + '/files.txt'):
        s, z, p = l.rstrip('\n').split(' ', 2)
        if not p.endswith('.pak') or 'sndroom' in p: continue
        src.seek(int(s) * 2048); d = src.read(int(z))
        es = listpak.entries(d); cs = [e for e in es if e['type'] == 5]
        if not cs: continue
        paks[p] = (bytearray(d), es, cs)
    base_p = '/romdata/common/base.pak'
    bd, bes, _ = paks[base_p]
    def tex(d, es, texid):
        e = [e for e in es if e['type'] == 2 and e['id'] == texid][0]
        return e, d[e['off']:e['off'] + e['size']]

    # --- korean text per pak
    kos = {}; chars = {}
    for p, (d, es, cs) in paks.items():
        jp = [e for e in cs if not e['name'].endswith('_e')][0]
        e = [e for e in cs if e['name'].endswith('_e')][0]
        cj = cap.parse(bytes(d[jp['off']:jp['off'] + jp['size']]))
        c = cap.parse(bytes(d[e['off']:e['off'] + e['size']]))
        ks = korean_strings(c, p == base_p)
        kos[p] = (cj, ks, jp, e)
        cc = collections.Counter()
        for _, _, items in ks:
            for k, v in items:
                if k in ('ko', 'txt'):
                    cc.update(ch for ch in v if ch not in ' \n')
        chars[p] = cc

    FS.space = 7; FC.space = 12
    # --- system atlases
    e845, t845 = tex(bd, bes, 845); e846, t846 = tex(bd, bes, 846); e3342, t3342 = tex(bd, bes, 3342)
    keep = [(0, 0, 252, 72), (0, 72, 108, 18), (144, 270, 108, 18), (0, 288, 252, 18), (0, 306, 18, 18)]
    A_sys = [Atlas(845, t845, 18, 'sys', keep), Atlas(846, t846, 18, 'sys'), Atlas(3342, t3342, 18, 'sys')]
    # original Latin glyphs reused
    SYS_KEEP = {}
    for r, row in enumerate(cap.SYSR):
        for col, ch in enumerate(row): SYS_KEEP[ch] = (0, col * 18, r * 18)
    for (col, r), ch in cap.SYSX.items(): SYS_KEEP.setdefault(ch, (0, col * 18, r * 18))
    # widths of kept glyphs from original E/JP cap glyph tables
    ce = kos[base_p][0]; ce_e = cap.parse(bytes(bd[kos[base_p][3]['off']:kos[base_p][3]['off'] + kos[base_p][3]['size']]))
    wmap = {}
    for g in ce_e['glyphs']: wmap[(g[0], g[1])] = g[2]
    for g in ce['glyphs'][:0x188]: wmap.setdefault((g[0], g[1]), g[2])
    gsys = {}
    syschars = [ch for ch, _ in chars[base_p].most_common()]
    for ch in syschars:
        if ch in SYS_KEEP and (SYS_KEEP[ch][1], SYS_KEEP[ch][2]) in wmap and ch.isascii() and ch.isalnum():
            a, x, y = SYS_KEEP[ch]; gsys[ch] = (0, x, y, wmap[(x, y)], 18)
    fill_glyphs(FS, A_sys, syschars, gsys)
    print('sys glyphs', len(gsys), [ (a.x, a.y) for a in A_sys])

    # --- caption shared atlases
    e849, t849 = tex(bd, bes, 849); e2931, t2931 = tex(bd, bes, 2931); e850, t850 = tex(bd, bes, 850)
    A_sh = [Atlas(849, t849, 28, 'cap'), Atlas(2931, t2931, 28, 'cap'), Atlas(850, t850, 28, 'cap')]
    areas = [p for p in paks if p != base_p]
    # choose shared set: greedy by number of areas using the char, then total freq
    nareas = collections.Counter(); tot = collections.Counter()
    for p in areas:
        for ch, n in chars[p].items(): nareas[ch] += 1; tot[ch] += n
    order = sorted(nareas, key=lambda ch: (-nareas[ch], -tot[ch]))
    gsh = {}
    for ch in order:
        try: fill_glyphs(FC, A_sh, [ch], gsh)
        except RuntimeError: break
    print('shared caption glyphs', len(gsh))

    out_paks = {}
    # --- per area
    for p in areas:
        d, es, cs = paks[p]
        cj, ks, jp, ee = kos[p]
        own = cj['fonts'][-1][1] if p.split('/')[-1] not in ('hill2.pak', 'park2.pak', 'silo2.pak') else {'hill2.pak': 2303, 'park2.pak': 3677, 'silo2.pak': 2305}[p.split('/')[-1]]
        eo, to = tex(d, es, own)
        A_own = Atlas(own, to, 28, 'cap')
        g = dict(gsh)
        need = [ch for ch, _ in chars[p].most_common() if ch not in g]
        loc = {}
        fill_glyphs(FC, [A_own], need, loc)
        for ch, v in loc.items(): g[ch] = (3,) + v[1:]
        d[eo['off']:eo['off'] + eo['size']] = A_own.bytes()
        # glyph table
        fonts_tex = [849, 2931, 850, own]
        used = sorted(set(chars[p]), key=lambda ch: (g[ch][0], g[ch][2], g[ch][1]))
        glyphs = []; gidx = {}; counts = [0, 0, 0, 0]
        for fi in range(4):
            for ch in used:
                if g[ch][0] == fi:
                    gidx[ch] = len(glyphs); glyphs.append(g[ch][1:]); counts[fi] += 1
        fonts = [(counts[i], fonts_tex[i], 28, 28, 12, 28) for i in range(4)]
        strs = [(idx, x, encode(items, gidx, FC, 390, 0)) for idx, x, items in ks]
        blob = cap.build(cj['hdr'][2:5], fonts, glyphs, strs)
        write_cap(d, es, jp, ee, blob, p)
        print(p.split('/')[-1], 'chars', len(chars[p]), 'own', len(loc), 'cap', len(blob))
        out_paks[p] = d

    # --- base system cap
    cj, ks, jp, ee = kos[base_p]
    used = sorted(set(chars[base_p]), key=lambda ch: (gsys[ch][0], gsys[ch][2], gsys[ch][1]))
    glyphs = []; gidx = {}; counts = [0, 0, 0]
    for fi in range(3):
        for ch in used:
            if gsys[ch][0] == fi: gidx[ch] = len(glyphs); glyphs.append(gsys[ch][1:]); counts[fi] += 1
    fonts = [(counts[0], 845, 18, 18, 7, 18), (counts[1], 846, 18, 18, 7, 18), (counts[2], 3342, 18, 18, 7, 18)]
    strs = [(idx, x, encode(items, gidx, FS, 470, 0)) for idx, x, items in ks]
    blob = cap.build(cj['hdr'][2:5], fonts, glyphs, strs)
    write_cap(bd, bes, jp, ee, blob, base_p)
    for a in A_sys + A_sh:
        e = [e for e in bes if e['type'] == 2 and e['id'] == a.texid][0]
        bd[e['off']:e['off'] + e['size']] = a.bytes()
    out_paks[base_p] = bd
    print('base cap', len(blob))
    for p, d in out_paks.items():
        isopatch.write(ISO, p, 0, bytes(d))
    import img
    for p, d in img.build(W + '/orig/romdata/common').items():
        isopatch.write(ISO, p, 0, d)
    # previews
    os.makedirs(W + '/view', exist_ok=True)
    for a in A_sys + A_sh:
        Image.fromarray(np.where(a.px == 255, 0, a.px.astype(np.int32) * 16).clip(0, 255).astype(np.uint8) if a.mode == 'sys' else ((a.px >> 4) * 17).astype(np.uint8)).save(W + '/view/atlas_%d.png' % a.texid)

def write_cap(d, es, jp, ee, blob, p):
    nxt = min(e['off'] for e in es if e['off'] > ee['off'])
    region = nxt - jp['off']
    assert len(blob) <= region, (p, len(blob), region)
    d[jp['off']:nxt] = blob + b'\0' * (region - len(blob))
    for e in (jp, ee):
        struct.pack_into('<I', d, e['eo'] + 8, len(blob))
        struct.pack_into('<I', d, e['eo'] + 0x10, jp['off'])

if __name__ == '__main__':
    main()

def patch_movies(iso):
    import isopatch
    for n in ('opening_bt', 'opening_bt51', 'ED_02J', 'warning'):
        fp = W + '/mv/%s.xmv' % n
        if not os.path.exists(fp): continue
        p = '/romdata/movie/%s.xmv' % n
        sz = isopatch.FILES[p][1] if isinstance(isopatch.FILES[p], tuple) else None
        d = open(fp, 'rb').read()
        isopatch.write(iso, p, 0, d + b'\0' * ((sz or len(d)) - len(d)))
        print('movie', n, len(d), sz)

if __name__ == '__main__':
    patch_movies(ISO)
    import envtex; envtex.build(SRC, ISO)
