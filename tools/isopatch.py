# write bytes at file-relative offset inside ISO (in place)
import struct
FILES={}
for l in open(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','files.txt')):
    s,z,p=l.rstrip('\n').split(' ',2); FILES[p]=(int(s)*2048,int(z))
def write(iso,path,off,data):
    base,size=FILES[path]; assert off+len(data)<=size,(path,off,len(data),size)
    with open(iso,'r+b') as f: f.seek(base+off); f.write(data)
def read(iso,path):
    base,size=FILES[path]
    with open(iso,'rb') as f: f.seek(base); return f.read(size)
