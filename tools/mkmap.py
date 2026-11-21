"""orig/romdata/area/*/*.nut의 텍스처에 번호를 매겨 view/sh/map.json을 만듭니다(같은 그림은 한 번호).
먼저: python tools/ext.py orig.iso orig /romdata/area/"""
import sys, glob, hashlib, json, os
T = os.path.dirname(os.path.abspath(__file__)); W = T + '/..'; sys.path.insert(0, T); import nutall
seen = {}; order = []
for f in sorted(glob.glob(W + '/orig/romdata/area/*/*.nut')):
    f = os.path.relpath(f, W).replace(os.sep, '/'); d = open(W + '/' + f, 'rb').read()
    for k, p, i in nutall.items(d):
        if i['w'] < 32 or i['h'] < 16: continue
        h = hashlib.md5(d[i['pix']:i['pix'] + min(i['im'], 65536)]).hexdigest()
        if h in seen: seen[h]['refs'].append([W + '/' + f, k]); continue
        seen[h] = dict(id=len(order), refs=[[W + '/' + f, k]]); order.append(h)
os.makedirs(W + '/view/sh', exist_ok=True); json.dump(seen, open(W + '/view/sh/map.json', 'w'))
print(len(order))
