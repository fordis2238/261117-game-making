import importlib.util,json,random,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('gen','jump-game/generate_harder.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class Budget(Exception):pass
def analyze(grid):
 n=len(grid);full=(1<<n)-1;rs=[g.options(g.runs(r),n) for r in grid];cs=[g.options(g.runs(c),n) for c in zip(*grid)];nodes=0;guesses=0;deadline=time.monotonic()+1.5
 def propagate(rs,cs):
  while True:
   previous=sum(map(len,rs))+sum(map(len,cs));rows=[];cols=[]
   for domains,result in [(rs,rows),(cs,cols)]:
    for dom in domains:
     if not dom:return None
     one=full;either=0
     for p in dom:one&=p;either|=p
     result.append((one,full^either))
   nr=[];nc=[]
   for r in range(n):
    one=rows[r][0];zero=rows[r][1]
    for c in range(n):
     if cols[c][0]>>r&1:one|=1<<c
     if cols[c][1]>>r&1:zero|=1<<c
    domain=[p for p in rs[r] if p&one==one and p&zero==0]
    if not domain:return None
    nr.append(domain)
   for c in range(n):
    one=cols[c][0];zero=cols[c][1]
    for r in range(n):
     if rows[r][0]>>c&1:one|=1<<r
     if rows[r][1]>>c&1:zero|=1<<r
    domain=[p for p in cs[c] if p&one==one and p&zero==0]
    if not domain:return None
    nc.append(domain)
   rs,cs=nr,nc
   if previous==sum(map(len,rs))+sum(map(len,cs)):return rs,cs
 def solve(rs,cs,depth=0):
  nonlocal nodes,guesses
  nodes+=1
  if nodes>400 or time.monotonic()>deadline:raise Budget()
  state=propagate(rs,cs)
  if state is None:return 0
  rs,cs=state
  if all(len(d)==1 for d in rs):return 1
  guesses=max(guesses,depth+1)
  # Split the smallest remaining row domain; count a second solution as ambiguous.
  i=min((i for i in range(n) if len(rs[i])>1),key=lambda i:len(rs[i]));total=0
  for p in rs[i]:
   branch=rs.copy();branch[i]=[p];total+=solve(branch,cs,depth+1)
   if total>=2:return 2
  return total
 try:return solve(rs,cs),guesses,nodes
 except Budget:return None,0,nodes
found=[];rng=random.Random(20261117)
for attempt in range(1500):
 kind=['부엉이','우주선','범선','로봇'][attempt%4];grid=g.picture(kind,25,attempt%30)
 # A patterned chest/engine introduces an interdependent region inside the silhouette.
 for r in range(11,20):
  for c in range(7,16):
   grid[r][c]=int(rng.random()<.58)
 if g.solve(grid) is not None:continue
 count,depth,nodes=analyze(grid)
 if count==1 and depth>=1:
  found.append(dict(name=kind,rows=[''.join(map(str,r)) for r in grid],validation=dict(unique=True,requiresBranching=True,maxBranchDepth=depth,nodes=nodes)))
  print('FOUND',attempt,depth,nodes,flush=True)
  if len(found)==3:break
assert found,'No unique branching puzzle found'
Path('jump-game/expert-puzzles.json').write_text(json.dumps(found,ensure_ascii=False),encoding='utf-8')
print('EXPERT PASS:',len(found),'unique puzzles; line propagation stalls, branching resolves')
