import sys,subprocess
from PIL import Image
sc=sys.argv[1]; ids=sys.argv[2:]
subprocess.run([sys.executable,'tools/envtex.py',sc]+ids,capture_output=True)
x=0;y=0;rowh=0;P=[]
for i in ids:
  im=Image.open('view/tx/%s.png'%i)
  if x+im.width>1600: x=0;y+=rowh+6;rowh=0
  P.append((i,im,(x,y))); x+=im.width+6; rowh=max(rowh,im.height)
s=Image.new('RGB',(1600,y+rowh))
for i,im,p in P: s.paste(im,p)
s.save('view/tx/b.png'); print([(i,p,im.size[0]//int(sc),im.size[1]//int(sc)) for i,im,p in P])
