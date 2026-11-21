import struct
from PIL import Image
def swz_index(w,h):
    # morton (xbox swizzle) for power of 2 w,h
    import numpy as np
    def bits(n): return (n-1).bit_length()
    bw,bh=bits(w),bits(h)
    xs=np.arange(w); ys=np.arange(h)
    def spread(v,isx):
        out=np.zeros_like(v); o=0; i=0; bx=by=0
        # interleave: lowest bit x, then y, while both available
        res=0
        return None
    idx=np.zeros((h,w),dtype=np.int64)
    for y in range(h):
        pass
    return idx
def morton(w,h):
    import numpy as np
    X=np.zeros(w,dtype=np.int64); Y=np.zeros(h,dtype=np.int64)
    bw=(w-1).bit_length(); bh=(h-1).bit_length()
    bit=0; xi=yi=0
    while xi<bw or yi<bh:
        if xi<bw:
            X|=((np.arange(w)>>xi)&1)<<bit; bit+=1; xi+=1
        if yi<bh:
            Y|=((np.arange(h)>>yi)&1)<<bit; bit+=1; yi+=1
    return Y[:,None]+X[None,:]
def parse(b):
    assert b[:4]==b'TIM2'
    p=0x80
    tot,cl,im,hs,cc=struct.unpack_from('<IIIHH',b,p)
    w,h=struct.unpack_from('<HH',b,p+0x14)
    return dict(tot=tot,cl=cl,im=im,hs=hs,cc=cc,w=w,h=h,fmt=b[p+0x10:p+0x14].hex(),pix=p+hs,pal=p+hs+im)
def decode(b,swz=True):
    import numpy as np
    i=parse(b); w,h=i['w'],i['h']
    px=np.frombuffer(b,dtype=np.uint8,count=w*h,offset=i['pix'])
    if swz: px=px[morton(w,h)]
    else: px=px.reshape(h,w)
    pal=np.frombuffer(b,dtype=np.uint8,count=i['cc']*4,offset=i['pal']).reshape(-1,4)
    return i,px,pal
