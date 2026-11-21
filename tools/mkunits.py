"""원본 ISO의 영어 CAP 문자열에서 번역 단위 목록(units.txt)을 만듭니다. 원문은 저장소에 넣지 않습니다."""
import sys, os, re, struct
T = os.path.dirname(os.path.abspath(__file__)); W = T + '/..'
sys.path.insert(0, T); import cap, listpak
def build(iso, out=W + '/units.txt'):
    if not os.path.exists(W + '/files.txt'):
        import subprocess
        open(W + '/files.txt', 'w').write(subprocess.check_output([sys.executable, T + '/xiso.py', iso, 'list']).decode())
    f = open(iso, 'rb'); paks = []
    for l in open(W + '/files.txt'):
        s, z, p = l.rstrip('\n').split(' ', 2)
        if not p.endswith('.pak') or 'sndroom' in p: continue
        f.seek(int(s) * 2048); d = f.read(int(z))
        es = [e for e in listpak.entries(d) if e['type'] == 5 and e['name'].endswith('_e')]
        if es: paks.append((p, d, es[0]))
    paks.sort(key=lambda x: x[0] != '/romdata/common/base.pak')
    units = {}
    for p, d, e in paks:
        c = cap.parse(d[e['off']:e['off'] + e['size']]); ch = cap.charfun(c); sysf = p == '/romdata/common/base.pak'
        for i, x, sv in c['strs']:
            t = cap.to_text(sv, ch)
            segs = [(s.replace('\n', '⏎') if sysf else s.replace('\n', ' ')).strip() for s in re.split(r'\{[^}]*\}', t)]
            segs = [s for s in segs if s]
            if segs: units.setdefault(' ¦ '.join(segs), 0)
    open(out, 'w', encoding='utf8').write('\n'.join(units))
    return len(units)
if __name__ == '__main__': print(build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else W + '/units.txt'))
