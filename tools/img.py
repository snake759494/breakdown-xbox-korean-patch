import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
T = os.path.dirname(os.path.abspath(__file__)); W = T + '/..'
sys.path.insert(0, T)
import tex

FONT_R = W + '/fonts/NanumSquareNeo-bRg.ttf'
FONT_B = W + '/fonts/NanumSquareNeo-cBd.ttf'
LABELS = [('공격 1', '무기 전환'), ('공격 2', '가드'), ('액세스', '록온'), ('점프', '웅크리기'), ('취소', '수류탄'),
          ('후진', '전진'), ('우회전', '좌회전'), ('아래 보기', '위 보기'), ('오른쪽 이동', '왼쪽 이동')]

def text_layer(size, text, font, px, color, maxw=None):
    """render text to RGBA (supersampled), optionally squeezed horizontally to maxw"""
    SS = 4; f = ImageFont.truetype(font, px * SS)
    b = f.getbbox(text); w = b[2] - b[0] + 2 * SS; h = b[3] - b[1] + 2 * SS
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).text((SS - b[0], SS - b[1]), text, font=f, fill=255)
    tw = max(1, round(w / SS)); th = max(1, round(h / SS))
    if maxw and tw > maxw: tw = maxw
    a = np.asarray(im.resize((tw, th), Image.LANCZOS), np.float32) / 255
    return a

def blend(img, a, x, y, color):
    h, w = a.shape
    reg = img[y:y+h, x:x+w].astype(np.float32)
    al = a[..., None]
    src = np.array(color + (255,), np.float32)
    out = reg.copy()
    out[..., :3] = reg[..., :3] * (1 - al) + src[:3] * al
    out[..., 3] = np.maximum(reg[..., 3], a * 255)
    img[y:y+h, x:x+w] = np.clip(out, 0, 255).astype(np.uint8)

def patch_tex(d, k, fn):
    t = tex.find_tims(d)[k]; i = tex.tim_at(d, t)
    raw = d[i['pix']:i['pix'] + i['im']]
    img = tex.dxt_decode(raw, i['w'], i['h'], 0x0f).copy(); orig = img.copy()
    fn(img)
    ch = (img != orig).any(-1).reshape(i['h'] // 4, 4, i['w'] // 4, 4).any(axis=(1, 3))
    buf = bytearray(raw); tex.dxt5_encode_blocks(buf, img.astype(np.int32), i['w'], i['h'], ch)
    d[i['pix']:i['pix'] + i['im']] = buf
    return img

def labels(img):
    for r, pair in enumerate(LABELS):
        for c, s in enumerate(pair):
            x0 = 2 + c * 93; x1 = 88 + c * 93; y0 = r * 23 + 2; y1 = r * 23 + 18
            reg = img[y0:y1+1, x0:x1+1]
            m = reg[..., :3].max(-1) > 30
            reg[m] = (8, 8, 8, 255)
            a = text_layer(None, s, FONT_R, 13, None, maxw=x1 - x0 - 2)
            h, w = a.shape
            cx = (x0 + x1) // 2 + 1; cy = r * 23 + 10
            blend(img, a, cx - w // 2, cy - h // 2, (178, 178, 178))

def quit_lines(img):
    img[194:210, 124:256] = 0
    img[210:226, 124:217] = 0
    a = text_layer(None, '저장하지 않고 종료', FONT_B, 13, None, maxw=128)
    blend(img, a, 126, 202 - a.shape[0] // 2, (255, 255, 255))
    a = text_layer(None, '저장하고 종료', FONT_B, 13, None, maxw=88)
    blend(img, a, 126, 218 - a.shape[0] // 2, (255, 255, 255))

def build(src_dir):
    out = {}; os.makedirs(W + '/view', exist_ok=True)
    d = bytearray(open(src_dir + '/r_BD00.ast', 'rb').read())
    im1 = patch_tex(d, 46, labels)
    import logo; logo.patch(d)
    out['/romdata/common/r_BD00.ast'] = bytes(d)
    d = bytearray(open(src_dir + '/r_PauseMain.ast', 'rb').read())
    im2 = patch_tex(d, 10, labels); im3 = patch_tex(d, 4, quit_lines)
    out['/romdata/common/r_PauseMain.ast'] = bytes(d)
    for n, im in (('labels_bd', im1), ('labels_pause', im2), ('pause_moji', im3)):
        a = im.astype(float); al = a[..., 3:] / 255
        Image.fromarray((a[..., :3] * al + 80 * (1 - al)).astype('uint8')).resize((512, 512), Image.NEAREST).save(W + '/view/%s.png' % n)
    return out

if __name__ == '__main__':
    build(W + '/orig/romdata/common')
