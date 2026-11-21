import struct
def entries(d):
    n=struct.unpack_from('<I',d,4)[0]; out=[]
    for i in range(n):
        o=0x40+i*0x80
        t=d[o+2]; gid,size,z,off=struct.unpack_from('<IIII',d,o+4)
        name=d[o+0x14:o+0x80].split(b'\0')[0].decode('latin1')
        out.append(dict(i=i,eo=o,type=t,id=gid,size=size,off=off,name=name))
    return out
