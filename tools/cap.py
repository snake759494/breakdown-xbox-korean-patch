import struct
ENG1=['0123456789ABCDEFGH','IJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqr','stuvwxyz%\',.!?-"#(',')/:;αβ']
def parse(b):
    mag,nstr,nf,u1,u2,u3,ofd,ogl,ost,otx=struct.unpack_from('<4sIHHHHIIII',b,0)
    fonts=[struct.unpack_from('<HHBBBB',b,ofd+i*8) for i in range(nf)]
    ng=sum(f[0] for f in fonts)
    gl=[struct.unpack_from('<HHBBH',b,ogl+i*8) for i in range(ng)]
    st=[struct.unpack_from('<IHH',b,ost+i*8) for i in range(nstr)]
    txt=b[otx:]
    strs=[]
    for off,idx,x in st:
        p=off*2; s=[]
        while p+1<len(txt):
            c=struct.unpack_from('<H',txt,p)[0]; p+=2; s.append(c)
            if c==2: break
        strs.append((idx,x,s))
    return dict(hdr=(nstr,nf,u1,u2,u3),fonts=fonts,glyphs=gl,strs=strs,raw=st)
def eng_map(c,gl,fonts):
    # map code to char for single-font E caps using eng1 grid (28px)
    return None
def tokens(s):
    i=0; out=[]
    while i<len(s):
        c=s[i]
        if c==6: out.append(('t',struct.unpack('<f',struct.pack('<HH',s[i+1],s[i+2]))[0])); i+=3; continue
        if c==0xc:
            n=s[i+1]; out.append(('i',s[i+2:i+2+n])); i+=2+n; continue
        out.append(('c',c)); i+=1
    return out
def to_text(s,chf):
    r=''
    for k,v in tokens(s):
        if k=='t': r+='{%g}'%round(v,3)
        elif k=='i': r+='{i:'+b''.join(__import__('struct').pack('<H',x) for x in v).decode('latin1')+'}'
        elif v==1: r+='\n'
        elif v==2: pass
        elif v==3: r+=' '
        elif v==0: r+='{p}'
        elif v<0x100: r+='{%x}'%v
        else: r+=chf(v)
    return r
SYSR=['0123456789ABCD','EFGHIJKLMNOPQR','STUVWXYZabcdef','ghijklmnopqrst','uvwxyz']
SYSX={(8,15):"'",(9,15):'(',(10,15):')',(11,15):'α',(12,15):'β',(0,16):'。',(1,16):',',(2,16):'.',(3,16):'・',(4,16):':',(5,16):'?',(6,16):'!',(7,16):'%',(8,16):'+',(9,16):'-',(10,16):'×',(11,16):'~',(12,16):'/',(13,16):'ー',(0,17):'#'}
def charfun(c):
    f=c['fonts'][0]
    if f[1]==2931:
        return lambda code:(lambda g:ENG1[g[1]//28][g[0]//28])(c['glyphs'][code-0x100])
    def h(code):
        g=c['glyphs'][code-0x100]; col=g[0]//18; row=g[1]//18
        if row<5 and col<len(SYSR[row]): return SYSR[row][col]
        return SYSX[(col,row)]
    return h
def build(nstr_hdr,fonts,glyphs,strs):
    """hdr: (u1,u2,u3) ; fonts: list (count,texid,cw,ch,sp,lh); glyphs: (x,y,w,h); strs: list (idx,x,codes list incl terminating 2)"""
    u1,u2,u3=nstr_hdr
    nf=len(fonts); ofd=0x20; ogl=ofd+8*nf; ost=ogl+8*len(glyphs); otx=ost+8*len(strs)
    tx=[]; pos={}; tbl=b''
    for idx,x,codes in strs:
        k=tuple(codes)
        if k not in pos: pos[k]=len(tx); tx.extend(codes)
        tbl+=struct.pack('<IHH',pos[k],idx,x)
    out=struct.pack('<4sIHHHHIIII','CAP\0'.encode(),len(strs),nf,u1,u2,u3,ofd,ogl,ost,otx)
    out+=b''.join(struct.pack('<HHBBBB',*f) for f in fonts)
    out+=b''.join(struct.pack('<HHBBH',x,y,w,h,0) for x,y,w,h in glyphs)
    out+=tbl+b''.join(struct.pack('<H',c) for c in tx)
    return out
