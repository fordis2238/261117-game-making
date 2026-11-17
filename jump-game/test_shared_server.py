import importlib.util,json,tempfile,threading,urllib.request,urllib.error
from pathlib import Path
spec=importlib.util.spec_from_file_location('server',Path(__file__).with_name('server.py'));s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
with tempfile.TemporaryDirectory() as tmp:
 s.DB=Path(tmp)/'test.sqlite3';s.initialize();http=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(http.server_address[1])
 def req(path,data=None):
  request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request) as r:return r.status,json.loads(r.read())
  except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
 rows=s.BANKS['5'][0]['rows'];grid=[[int(v) for v in r] for r in rows]
 assert req('/api/runs',{'nickname':'','rows':rows})[0]==400
 ids=[]
 for name,ms in [('토끼',1200),('당근',500)]:
  status,run=req('/api/runs',{'nickname':name,'rows':rows});assert status==201;ids.append(run['id'])
  bad={'grid':[[0]*5 for _ in range(5)],'ms':ms};assert req('/api/runs/'+run['id']+'/finish',bad)[0]==400
  data={'grid':grid,'ms':ms,'hints':1,'checks':0,'nameRevealed':True}
  assert req('/api/runs/'+run['id']+'/finish',data)[0]==201
  assert req('/api/runs/'+run['id']+'/finish',data)[0]==200
 status,result=req('/api/records');assert status==200;assert len(result['records'])==2;assert [r['nickname'] for r in result['records']]==['당근','토끼'];assert all(r['size']==5 for r in result['records'])
 s.initialize();assert len(s.records())==2
 assert req('/shared-rankings.sqlite3')[0]==404
 http.shutdown();http.server_close()
print('PASS: independent players, shared ordering, duplicate protection, invalid solution rejection, persistent SQLite records, restricted file serving')
