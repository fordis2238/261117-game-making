import json,re,random
from pathlib import Path
from PIL import Image,ImageDraw
random.seed(42)
def runs(row):return tuple(len(g) for g in ''.join(map(str,row)).split('0') if g) or (0,)
def options(clue,n):
 if clue==(0,):return [0]
 out=[]
 def go(i,pos,mask):
  if i==len(clue):out.append(mask);return
  reserve=sum(clue[i:])+len(clue)-i-1
  for start in range(pos,n-reserve+1):go(i+1,start+clue[i]+1,mask|((1<<clue[i])-1)<<start)
 go(0,0,0);return out
cache={}
def solve(grid):
 n=len(grid);full=(1<<n)-1;known1=[0]*n;known0=[0]*n;rounds=0;first=0
 rs=[options(runs(r),n) for r in grid];cs=[options(runs(c),n) for c in zip(*grid)]
 for loops in range(n*n):
  updates=[]
  for typ,domains in enumerate((rs,cs)):
   for i,domain in enumerate(domains):
    one=known1[i] if typ==0 else sum(((known1[r]>>i)&1)<<r for r in range(n));zero=known0[i] if typ==0 else sum(((known0[r]>>i)&1)<<r for r in range(n))
    domain=[m for m in domain if m&one==one and m&zero==0];domains[i]=domain
    if not domain:return None
    all1=full;any1=0
    for m in domain:all1&=m;any1|=m
    zeros=full^any1
    if typ==0:updates.append((i,all1,zeros))
    else:
     for r in range(n):updates.append((r,((all1>>r)&1)<<i,((zeros>>r)&1)<<i))
  before=sum((known1[r]|known0[r]).bit_count() for r in range(n))
  for r,o,z in updates:known1[r]|=o;known0[r]|=z
  after=sum((known1[r]|known0[r]).bit_count() for r in range(n))
  if loops==0:first=after
  rounds+=1
  if after==n*n:return dict(rounds=rounds,initial=round(first/(n*n),3))
  if after==before:return None
 return None

def picture(kind,n,variant):
 im=Image.new('1',(20,20));d=ImageDraw.Draw(im)
 if kind=='부엉이':
  d.polygon([(3,2),(7,4),(12,4),(16,2),(16,8),(18,12),(17,17),(14,19),(5,19),(2,17),(1,12),(3,8)],fill=1)
  d.ellipse((4,5,9,10),fill=0);d.ellipse((10,5,15,10),fill=0);d.rectangle((6,7,7,8),fill=1);d.rectangle((12,7,13,8),fill=1)
  d.polygon([(8,10),(11,10),(10,12)],fill=0);d.line((4,12,6,16),fill=0);d.line((15,12,13,16),fill=0)
  for x,y in [(8,14),(11,14),(9,17)]:d.point((x,y),fill=0)
 elif kind=='로봇':
  d.line((9,0,9,3),fill=1,width=2);d.rectangle((4,3,15,10),fill=1);d.rectangle((2,5,3,8),fill=1);d.rectangle((16,5,17,8),fill=1)
  d.rectangle((6,5,8,7),fill=0);d.rectangle((11,5,13,7),fill=0);d.line((7,9,12,9),fill=0)
  d.rectangle((5,12,14,17),fill=1);d.rectangle((2,12,3,16),fill=1);d.rectangle((16,12,17,16),fill=1);d.rectangle((6,18,8,19),fill=1);d.rectangle((11,18,13,19),fill=1)
  d.rectangle((7,13,12,15),fill=0);d.point((8,14),fill=1);d.point((11,14),fill=1)
 elif kind=='우주선':
  d.polygon([(9,0),(13,5),(13,12),(17,16),(17,18),(12,16),(11,18),(7,18),(6,16),(2,18),(2,16),(6,12),(6,5)],fill=1)
  d.ellipse((7,5,12,10),fill=0);d.rectangle((9,7,10,8),fill=1);d.line((7,13,12,13),fill=0);d.line((7,15,12,15),fill=0)
  d.point((7,19),fill=1);d.point((11,19),fill=1)
 elif kind=='범선':
  d.line((10,0,10,15),fill=1);d.polygon([(8,2),(1,12),(8,12)],fill=1);d.polygon([(12,4),(17,12),(12,12)],fill=1)
  d.polygon([(1,14),(18,14),(15,18),(5,18)],fill=1);d.line((5,16,14,16),fill=0)
  d.line((0,19,6,19),fill=1);d.line((11,19,18,19),fill=1)
 elif kind=='꽃병':
  for x,y in [(5,4),(13,3),(10,8)]:
   d.ellipse((x-3,y-2,x+3,y+2),fill=1);d.ellipse((x-2,y-3,x+2,y+3),fill=1);d.point((x,y),fill=0)
  d.line((5,7,9,14),fill=1);d.line((13,6,11,14),fill=1);d.line((10,11,10,14),fill=1)
  d.polygon([(5,13),(15,13),(14,18),(12,19),(8,19),(6,18)],fill=1);d.line((7,16,13,16),fill=0)
 # Slight decorative changes remain inside the drawing, rather than scattering random pixels.
 rng=random.Random(variant*100+len(kind))
 for _ in range(variant%6):
  x=rng.randrange(5,15);y=rng.randrange(11,18)
  if im.getpixel((x,y)) and all(im.getpixel((xx,yy)) for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]):d.point((x,y),fill=0)
 im=im.resize((n,n),Image.Resampling.NEAREST)
 return [[int(im.getpixel((c,r))!=0) for c in range(n)] for r in range(n)]
html=Path('index.html').read_text(encoding='utf-8');old=json.loads(re.search(r'const puzzleBanks=(.*?);\nlet n=',html).group(1));bank={'5':old['5']};report=[]
for n in [10,15,20]:
 candidates=[];seen=set()
 for kind in ['부엉이','로봇','우주선','범선','꽃병']:
  best=None
  for v in range(30):
   grid=picture(kind,n,v);rows=[''.join(map(str,r)) for r in grid];key='/'.join(rows)
   if key in seen:continue
   seen.add(key);metrics=solve(grid)
   if metrics and (best is None or (metrics['rounds'],-metrics['initial'])>(best[1]['rounds'],-best[1]['initial'])):best=({'name':kind,'rows':rows},metrics)
  if best:candidates.append(best)
 candidates.sort(key=lambda x:(x[1]['rounds'],-x[1]['initial']),reverse=True)
 bank[str(n)]=[x[0] for x in candidates[:3]]
 for p,m in candidates[:3]:report.append({'size':n,'name':p['name'],**m})
 assert len(bank[str(n)])>=2,(n,len(candidates))
Path('jump-game/harder-puzzles.json').write_text(json.dumps(bank,ensure_ascii=False),encoding='utf-8')
Path('jump-game/difficulty-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
