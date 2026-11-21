import struct,sys,os
iso,out=sys.argv[1],sys.argv[2]; pats=sys.argv[3:]
f=open(iso,'rb')
for l in open(os.path.join(os.path.dirname(__file__),'..','files.txt'),encoding='utf8'):
    s,z,p=l.rstrip('\n').split(' ',2)
    if any(x in p for x in pats):
        fp=out+p; os.makedirs(os.path.dirname(fp),exist_ok=True); f.seek(int(s)*2048); open(fp,'wb').write(f.read(int(z)))
