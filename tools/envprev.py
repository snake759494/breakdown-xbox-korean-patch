import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'tr'); import envtex, envspec, numpy as np
from PIL import Image
def mk(ops):
    def fn(im):
        for o in ops:
            if o[0]=='e': envtex.inpaint(im,*o[1:5],*(o[5:6] or ['h']))
            else: envtex.text(im,*o[1:6],o[6],*(o[7:]))
    return fn
ids=[int(x) for x in sys.argv[2:]]; sc=int(sys.argv[1]); ims=[]
for t in ids:
    im,i=envtex.get(t); mk(envspec.S[t])(im); I=Image.fromarray(im[...,:3]); ims.append(I.resize((I.width*sc,I.height*sc),Image.NEAREST))
W_=sum(i.width for i in ims)+8*len(ims); H=max(i.height for i in ims)
s=Image.new('RGB',(W_,H),(255,0,255)); x=0
for i in ims: s.paste(i,(x,0)); x+=i.width+8
s.save('view/tx/p.png')
