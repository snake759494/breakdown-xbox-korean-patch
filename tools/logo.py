import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import img
FONT = T + '/../fonts/NanumSquareNeo-eHv.ttf'
TEXT = '브레이크다운'
def draw(im, y=150, size=30, x0=128):
    SS = 4; f = ImageFont.truetype(FONT, size * SS)
    b = f.getbbox(TEXT); w = b[2] - b[0] + 16 * SS; h = b[3] - b[1] + 16 * SS
    L = Image.new('L', (w, h), 0); ImageDraw.Draw(L).text((8 * SS - b[0], 8 * SS - b[1]), TEXT, font=f, fill=255)
    fill = np.asarray(L.resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
    ol = np.asarray(L.filter(ImageFilter.MaxFilter(3 * SS + 1)).resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
    gl = np.asarray(L.filter(ImageFilter.MaxFilter(5 * SS + 1)).filter(ImageFilter.GaussianBlur(4 * SS)).resize((w // SS, h // SS), Image.LANCZOS), np.float32) / 255
    hh, ww = fill.shape; x = x0 - ww // 2
    reg = im[y:y + hh, x:x + ww].astype(np.float32)
    # chrome-like vertical gradient fill
    g = np.linspace(255, 150, hh)[:, None, None] * np.ones((1, ww, 3))
    g[..., 2] *= 0.95
    def over(reg, col, a):
        a = a[..., None]
        reg[..., :3] = reg[..., :3] * (1 - a) + col * a
        reg[..., 3:] = np.maximum(reg[..., 3:], a * 255)
    over(reg, np.array([255, 90, 20], np.float32), gl * 0.8)
    over(reg, np.array([10, 5, 5], np.float32), ol)
    over(reg, g, fill)
    im[y:y + hh, x:x + ww] = np.clip(reg, 0, 255).astype(np.uint8)
def patch(d, y=150, size=30, x0=128):
    return img.patch_tex(d, 11, lambda im: draw(im, y, size, x0))
