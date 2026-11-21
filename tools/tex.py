import struct, numpy as np, re
import nut
def c565(c):
    r=((c>>11)&31)*255//31; g=((c>>5)&63)*255//63; b=(c&31)*255//31
    return np.stack([r,g,b],-1)
def dxt_decode(buf,w,h,fmt):
    bw,bh=max(1,w//4),max(1,h//4); bs=8 if fmt==0x0c else 16
    out=np.zeros((bh*4,bw*4,4),np.uint8)
    a=np.frombuffer(buf,np.uint8,count=bw*bh*bs).reshape(bh,bw,bs)
    cb=a[...,bs-8:]
    c0=cb[...,0].astype(np.uint32)|(cb[...,1].astype(np.uint32)<<8); c1=cb[...,2].astype(np.uint32)|(cb[...,3].astype(np.uint32)<<8)
    C0=c565(c0).astype(np.int32); C1=c565(c1).astype(np.int32)
    idx=(cb[...,4].astype(np.uint32)|(cb[...,5].astype(np.uint32)<<8)|(cb[...,6].astype(np.uint32)<<16)|(cb[...,7].astype(np.uint32)<<24))
    pal=np.zeros((bh,bw,4,4),np.int32); pal[...,0,:3]=C0; pal[...,1,:3]=C1; pal[...,:,3]=255
    gt=(c0>c1)|(fmt!=0x0c)
    pal[...,2,:3]=np.where(gt[...,None],(2*C0+C1)//3,(C0+C1)//2)
    pal[...,3,:3]=np.where(gt[...,None],(C0+2*C1)//3,0)
    pal[...,3,3]=np.where(gt,255,0) if fmt==0x0c else 255
    for py in range(4):
        for px in range(4):
            k=(idx>>(2*(py*4+px)))&3
            col=np.take_along_axis(pal,k[...,None,None].repeat(4,-1).astype(np.int64),2)[...,0,:]
            out[py::4,px::4][:bh,:bw]=col
    if fmt in (0x0e,):
        al=a[...,:8]
        for i in range(16):
            v=(al[...,i//2]>>(4*(i%2)))&15
            out[i//4::4,i%4::4][:bh,:bw,3]=v*17
    if fmt==0x0f:
        al=a[...,:8].astype(np.uint32); a0=al[...,0].astype(np.int32); a1=al[...,1].astype(np.int32)
        bits=np.zeros(al.shape[:2],np.uint64)
        for i in range(6): bits|=al[...,2+i].astype(np.uint64)<<np.uint64(8*i)
        for i in range(16):
            k=((bits>>np.uint64(3*i))&np.uint64(7)).astype(np.int32)
            av=np.where(k==0,a0,np.where(k==1,a1,np.where(a0>a1,((8-k)*a0+(k-1)*a1)//7,np.where(k==6,0,np.where(k==7,255,((6-k)*a0+(k-1)*a1)//5)))))
            out[i//4::4,i%4::4][:bh,:bw,3]=av
    return out[:h,:w]
def find_tims(d):
    return [m.start() for m in re.finditer(b'TIM2',d)]
def tim_at(d,t):
    p=t+0x80
    tot,cl,im,hs,cc=struct.unpack_from('<IIIHH',d,p); fmt=d[p+0x11]; w,h=struct.unpack_from('<HH',d,p+0x14)
    return dict(t=t,tot=tot,cl=cl,im=im,hs=hs,cc=cc,fmt=fmt,w=w,h=h,pix=p+hs,pal=p+hs+im,raw=d[p+0x10:p+0x14].hex())
def decode(d,info):
    w,h,f=info['w'],info['h'],info['fmt']
    if f in (0x0c,0x0e,0x0f): return dxt_decode(d[info['pix']:info['pix']+info['im']],w,h,f)
    if f==0x0b:  # P8 swizzled
        px=np.frombuffer(d,np.uint8,count=w*h,offset=info['pix'])[nut.morton(w,h)]
        pal=np.frombuffer(d,np.uint8,count=info['cc']*4,offset=info['pal']).reshape(-1,4)
        a=pal[px]; return a[...,[2,1,0,3]]
    if f==0x06:  # A8R8G8B8 swizzled
        px=np.frombuffer(d,np.uint8,count=w*h*4,offset=info['pix']).reshape(-1,4)[nut.morton(w,h)]
        return px[...,[2,1,0,3]]
    return None
def _enc_color(blk):
    # blk (16,3) int ; returns 8 bytes (DXT1-style 4-color block)
    pts=blk.astype(np.float64); mean=pts.mean(0); c=pts-mean
    if np.allclose(c,0): axis=np.array([1.,1,1])
    else:
        u,s,vt=np.linalg.svd(c,full_matrices=False); axis=vt[0]
    proj=c@axis; lo=mean+axis*proj.min(); hi=mean+axis*proj.max()
    def to565(v):
        v=np.clip(np.round(v),0,255).astype(int); return ((v[0]*31+127)//255<<11)|((v[1]*63+127)//255<<5)|((v[2]*31+127)//255)
    a,b=to565(hi),to565(lo)
    if a<b: a,b=b,a
    if a==b:
        if a>0: b=a-1
        else: a=1
    ca=c565(np.array(a)).astype(float); cb=c565(np.array(b)).astype(float)
    pal=np.array([ca,cb,(2*ca+cb)/3,(ca+2*cb)/3])
    d=((pts[:,None,:]-pal[None])**2).sum(-1); idx=d.argmin(1)
    bits=0
    for i in range(16): bits|=int(idx[i])<<(2*i)
    return struct.pack('<HHI',a,b,bits)
def _enc_alpha(al):
    al=al.astype(int); a0,a1=al.max(),al.min()
    if a0==a1:
        return struct.pack('<BB',a0,a1)+b'\0'*6
    pal=[a0,a1]+[((7-k)*a0+k*a1)//7 for k in range(1,7)]
    pal=np.array(pal); idx=np.abs(al[:,None]-pal[None]).argmin(1)
    bits=0
    for i in range(16): bits|=int(idx[i])<<(3*i)
    return struct.pack('<BB',a0,a1)+bits.to_bytes(6,'little')
def dxt5_encode_blocks(buf,img,w,h,changed):
    """buf: bytearray of dxt5 data; img: (h,w,4) RGBA; changed: (h//4,w//4) bool"""
    bw=w//4
    for by,bx in zip(*np.nonzero(changed)):
        blk=img[by*4:by*4+4,bx*4:bx*4+4].reshape(16,4)
        o=(by*bw+bx)*16
        buf[o:o+8]=_enc_alpha(blk[:,3]); buf[o+8:o+16]=_enc_color(blk[:,:3])
    return buf
