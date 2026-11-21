import sys, os, json, struct, numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import nutall, tex, nut
W=T+'/..'
MAP=None
def load_map():
    global MAP
    if MAP is None:
        m=json.load(open(W+'/view/sh/map.json')); MAP={v['id']:v['refs'] for v in m.values()}
    return MAP
def get(tid):
    f,k=load_map()[tid][0]; d=open(f,'rb').read()
    for kk,p,i in nutall.items(d):
        if kk==k: return nutall.decode(d,i), i
def grid(tid, out, scale=2):
    from PIL import Image, ImageDraw
    im,i=get(tid); a=im[...,3:]/255.; rgb=(im[...,:3]*a+50*(1-a)).astype(np.uint8)
    I=Image.fromarray(rgb).resize((im.shape[1]*scale,im.shape[0]*scale),Image.NEAREST); d=ImageDraw.Draw(I)
    for x in range(0,im.shape[1],16): d.line((x*scale,0,x*scale,I.height),fill=(0,255,255) if x%64==0 else (0,90,90))
    for y in range(0,im.shape[0],16): d.line((0,y*scale,I.width,y*scale),fill=(0,255,255) if y%64==0 else (0,90,90))
    for x in range(0,im.shape[1],64): d.text((x*scale+2,2),str(x),fill=(255,255,0))
    for y in range(64,im.shape[0],64): d.text((2,y*scale+2),str(y),fill=(255,255,0))
    I.save(out); return I.size
if __name__=='__main__':
    for t in sys.argv[2:]:
        print(t, get(int(t))[1]['w'], get(int(t))[1]['h'], grid(int(t), W+'/view/tx/%s.png'%t, int(sys.argv[1])))

from PIL import Image, ImageDraw, ImageFont
FONTS={'b':W+'/fonts/NanumSquareNeo-cBd.ttf','h':W+'/fonts/NanumSquareNeo-eHv.ttf','r':W+'/fonts/NanumSquareNeo-bRg.ttf'}
def inpaint(img,x0,y0,x1,y1,mode='h'):
    r=img.astype(np.float32)
    if mode=='h':
        Ls=r[y0:y1,max(0,x0-2):x0]; Rs=r[y0:y1,x1:x1+2]
        if Ls.shape[1]==0: Ls=Rs
        if Rs.shape[1]==0: Rs=Ls
        L=Ls.mean(1); R=Rs.mean(1)
        t=np.linspace(0,1,x1-x0)[None,:,None]
        r[y0:y1,x0:x1]=L[:,None]*(1-t)+R[:,None]*t
    elif mode=='v':
        Ts=r[max(0,y0-2):y0,x0:x1]; Bs=r[y1:y1+2,x0:x1]
        if Ts.shape[0]==0: Ts=Bs
        if Bs.shape[0]==0: Bs=Ts
        T_=Ts.mean(0); B=Bs.mean(0)
        t=np.linspace(0,1,y1-y0)[:,None,None]
        r[y0:y1,x0:x1]=T_[None]*(1-t)+B[None]*t
    else:
        c=np.array(mode,np.float32); r[y0:y1,x0:x1,:len(c)]=c
    img[:]=np.clip(r,0,255).astype(np.uint8)
def text(img,x0,y0,x1,y1,s,color,font='b',size=None,align='c',outline=None):
    SS=4; lines=s.split('|'); bw=x1-x0; bh=y1-y0
    pl=bh/len(lines)
    if size is None and pl<=10: font='g'
    if font=='g':
        SS=1; size=12 if pl>=12 else 10 if pl>=10 else 8
        f=ImageFont.truetype(W+'/fonts/Galmuri%d.ttf'%{12:11,10:9,8:7}[size],size); lh=size
    else:
        if size is None: size=max(6,int(pl*0.82))
        f=ImageFont.truetype(FONTS[font],size*SS); lh=int(size*1.15)*SS
    ws=[f.getbbox(l)[2] for l in lines]; asc=f.getbbox('한')[1]; hh=f.getbbox('한')[3]-asc
    tw=max(ws)+2*SS; th=lh*(len(lines)-1)+hh+2*SS
    L=Image.new('L',(tw,th),0); dr=ImageDraw.Draw(L)
    for k,l in enumerate(lines):
        x=(tw-ws[k])//2 if align=='c' else SS
        dr.text((x,SS+k*lh-asc),l,font=f,fill=255)
    w=max(1,round(tw/SS)); h=max(1,round(th/SS))
    if w>bw: w=bw
    if h>bh: h=bh
    a=np.asarray(L if L.size==(w,h) else L.resize((w,h),Image.LANCZOS),np.float32)/255
    if outline:
        from PIL import ImageFilter
        o=np.asarray(L.filter(ImageFilter.MaxFilter(2*SS+1)).resize((w,h),Image.LANCZOS),np.float32)/255
    x=x0+(bw-w)//2 if align=='c' else x0; y=y0+(bh-h)//2
    reg=img[y:y+h,x:x+w].astype(np.float32)
    if outline:
        reg[...,:3]=reg[...,:3]*(1-o[...,None])+np.array(outline,np.float32)*o[...,None]
    reg[...,:3]=reg[...,:3]*(1-a[...,None])+np.array(color,np.float32)*a[...,None]
    img[y:y+h,x:x+w]=np.clip(reg,0,255).astype(np.uint8)
# ---- encode
def _enc_dxt1(img,w,h,changed,buf):
    for by in range(h//4):
        for bx in range(w//4):
            if not changed[by,bx]: continue
            blk=img[by*4:by*4+4,bx*4:bx*4+4,:3].reshape(16,3).astype(int)
            o=(by*(w//4)+bx)*8; buf[o:o+8]=tex._enc_color(blk)
def _enc_dxt5(img,w,h,changed,buf):
    tex.dxt5_encode_blocks(buf,img.astype(np.int32),w,h,changed)
def encode_level(d,i,lvl_off,w,h,img,orig):
    f=i['f']
    if f in (0x08,0x0c):
        bs=8 if f==0x08 else 16; n=max(1,w//4)*max(1,h//4)*bs
        buf=bytearray(d[lvl_off:lvl_off+n])
        ch=(img!=orig).any(-1).reshape(h//4,4,w//4,4).any(axis=(1,3)) if orig is not None else np.ones((h//4,w//4),bool)
        (_enc_dxt1 if f==0x08 else _enc_dxt5)(img,w,h,ch,buf); d[lvl_off:lvl_off+n]=buf; return n
    if f==0x05:
        pal=np.frombuffer(bytes(d),np.uint8,count=1024,offset=i['pix']+i['im']).reshape(-1,4)[:,[2,1,0,3]].astype(int)
        n=w*h; mi=nut.morton(w,h)
        px=np.frombuffer(bytes(d[lvl_off:lvl_off+n]),np.uint8).copy()
        cur=np.zeros(n,np.uint8); cur[mi.ravel()]=0
        ch=(img!=orig).any(-1) if orig is not None else np.ones((h,w),bool)
        ys,xs=np.nonzero(ch)
        if len(ys):
            c=img[ys,xs].astype(int); a=c[:,3:4]//2
            pc=np.concatenate([pal[:,:3],pal[:,3:4]],1)
            tgt=np.concatenate([c[:,:3],a],1)
            dist=((tgt[:,None,:]-pc[None])**2).sum(-1); idx=dist.argmin(1).astype(np.uint8)
            px[mi[ys,xs]]=idx
        d[lvl_off:lvl_off+n]=px.tobytes(); return n
def apply(d,i,fn):
    w,h=i['w'],i['h']; im=nutall.decode(bytes(d),i)
    if i['f']==0x05:
        # decode alpha raw (undo *2)
        pass
    orig=im.copy(); fn(im)
    if i['f']==0x05:
        im2=im.copy(); im2[...,3]=orig[...,3]; im=im2
        im[...,3]=np.where((im[...,:3]!=orig[...,:3]).any(-1),255,orig[...,3]) if False else orig[...,3]
    p=i['pix']; nm=d[i['pix']-i['hs']+0x11] or 1
    cur,cor=im,orig
    for lv in range(nm):
        n=encode_level(d,i,p,w,h,cur,cor if lv==0 else None); p+=n
        if w<=4 or h<=4: break
        w//=2; h//=2
        cur=np.asarray(Image.fromarray(cur).resize((w,h),Image.BOX)); cor=None
def patch_all(specs):
    """specs: {tid: fn(img)} -> writes modified nut files under W/mod/..."""
    m=load_map(); files={}
    for tid,fn in specs.items():
        for f,k in m[tid]:
            if f not in files: files[f]=bytearray(open(f,'rb').read())
            d=files[f]
            for kk,p,i in nutall.items(bytes(d)):
                if kk==k: apply(d,i,fn); break
    return files

def build(iso_src, iso_dst):
    import isopatch
    sys.path.insert(0,W+'/text'); import envspec
    mp=json.load(open(W+'/text/envmap.json'))
    def mk(ops):
        def fn(im):
            for o in ops:
                if o[0]=='e': inpaint(im,*o[1:5],*(o[5:6] or ['h']))
                else: text(im,*o[1:6],o[6],*(o[7:]))
        return fn
    files={}
    for tid,refs in mp.items():
        fn=mk(envspec.S[int(tid)])
        for p,k in refs:
            if p not in files: files[p]=bytearray(isopatch.read(iso_src,p))
            d=files[p]
            for kk,pp,i in nutall.items(bytes(d)):
                if kk==k: apply(d,i,fn); break
    for p,d in files.items(): isopatch.write(iso_dst,p,0,bytes(d))
    print('env textures',len(mp),'files',len(files))
