import struct,sys,os
iso=sys.argv[1]; mode=sys.argv[2]
f=open(iso,'rb')
f.seek(0x10000); h=f.read(0x20)
rs,rz=struct.unpack_from('<II',h,0x14)
entries=[]
def walk(sec,size,path):
    f.seek(sec*2048); d=f.read(size)
    stack=[0]; seen=set()
    while stack:
        o=stack.pop()
        if o in seen or o*4+14>len(d): continue
        seen.add(o); p=o*4
        l,r,s,z,a,n=struct.unpack_from('<HHIIBB',d,p)
        if l==0xffff: continue
        name=d[p+14:p+14+n].decode('latin1')
        if l: stack.append(l)
        if r: stack.append(r)
        full=path+'/'+name
        if a&0x10:
            if z: walk(s,z,full)
        else: entries.append((full,s,z))
walk(rs,rz,'')
if mode=='list':
    for e in sorted(entries,key=lambda x:x[1]): print(e[1],e[2],e[0])
else:
    out=sys.argv[3]
    for p,s,z in entries:
        fp=out+p; os.makedirs(os.path.dirname(fp),exist_ok=True)
        f.seek(s*2048); open(fp,'wb').write(f.read(z))
