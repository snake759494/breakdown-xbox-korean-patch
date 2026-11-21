import sys, os, struct, numpy as np
from PIL import Image, ImageDraw
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import tex, nut
def items(d):
    p=0x80; k=0
    while p+0x18<len(d):
        tot,cl,im,hs,cc=struct.unpack_from('<IIIHH',d,p)
        if tot==0: break
        w,h=struct.unpack_from('<HH',d,p+0x14); f=d[p+0x13]
        yield k,p,dict(tot=tot,cl=cl,im=im,hs=hs,cc=cc,w=w,h=h,f=f,pix=p+hs)
        p+=tot; k+=1
def decode(d,i):
    w,h,f=i['w'],i['h'],i['f']; raw=d[i['pix']:i['pix']+i['im']]
    if f==0x08: return tex.dxt_decode(raw,w,h,0x0c)
    if f==0x0c: return tex.dxt_decode(raw,w,h,0x0f)
    if f==0x05:
        px=np.frombuffer(raw,np.uint8,count=w*h)[nut.morton(w,h)]
        pal=np.frombuffer(d,np.uint8,count=256*4,offset=i['pix']+i['im']).reshape(-1,4)
        o=pal[px][...,[2,1,0,3]].copy(); o[...,3]=np.minimum(255,o[...,3].astype(int)*2); return o
    return None
def sheet(fn,out):
    d=open(fn,'rb').read(); tiles=[]
    for k,p,i in items(d):
        try: im=decode(d,i)
        except Exception: im=None
        if im is None: continue
        a=im[...,3:]/255.; im=Image.fromarray((im[...,:3]*a+50*(1-a)).astype(np.uint8)); im.thumbnail((192,192))
        t=Image.new('RGB',(192,204),(255,0,255)); t.paste(im,(0,12)); ImageDraw.Draw(t).text((2,0),'%d %dx%d %x'%(k,i['w'],i['h'],i['f']),fill=0); tiles.append(t)
    c=8; s=Image.new('RGB',(192*c,204*((len(tiles)+c-1)//c)))
    for k,t in enumerate(tiles): s.paste(t,((k%c)*192,(k//c)*204))
    s.save(out); return len(tiles)
if __name__=='__main__': print(sheet(sys.argv[1],sys.argv[2]))
