import json,re,os,sys,glob,struct
W=os.path.dirname(os.path.abspath(__file__))+'/..'
sys.path.insert(0,W+'/text'); import loc
def load_units():
    L=open(W+'/units.txt',encoding='utf8').read().split('\n')
    tr={}
    for f in sorted(glob.glob(W+'/text/ko_*.txt')):
        for l in open(f,encoding='utf8'):
            l=l.rstrip('\n')
            if not l: continue
            n,t=l.split('|',1); tr[int(n)]=t
    out={}; miss=[]
    for n,u in enumerate(L,1):
        if n in tr: out[u]=tr[n]
        else:
            r=loc.tr(u)
            if r is None: miss.append((n,u))
            else: out[u]=r
    return out,miss
def split_tokens(t):
    # returns list of ('code',str) / ('text',str)
    out=[]; p=0
    for m in re.finditer(r'\{[^}]*\}',t):
        if m.start()>p: out.append(('text',t[p:m.start()]))
        out.append(('code',m.group())); p=m.end()
    if p<len(t): out.append(('text',t[p:]))
    return out
def unit_key(t,sysf):
    segs=[(s.replace('\n','⏎') if sysf else s.replace('\n',' ')).strip() for s in re.split(r'\{[^}]*\}',t)]
    segs=[s for s in segs if s]
    return ' ¦ '.join(segs) if segs else None
def translate(t,sysf,tr):
    """returns new text string with codes, Korean text, ⏎ as \n"""
    k=unit_key(t,sysf)
    if k is None: return t
    ko=tr[k]
    kseg=ko.split('¦')
    toks=split_tokens(t)
    ti=[i for i,(a,b) in enumerate(toks) if a=='text' and b.strip()]
    assert len(ti)==len(kseg),(t,ko)
    for j,i in enumerate(ti):
        s=kseg[j]
        if j==0: s=s.lstrip()
        if j==len(kseg)-1: s=s.rstrip()
        toks[i]=('text',s.replace('⏎','\n'))
    # drop whitespace-only text tokens (original spaces/newlines) between codes? keep them
    return ''.join(b for a,b in toks)
