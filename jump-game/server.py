"""LAN nonogram server. Python standard library only; SQLite records stay on this PC."""
from contextlib import contextmanager
import argparse, hashlib, json, os, re, socket, sqlite3, time, uuid, threading
from ai_coach import advise, explain
AI_LOCK=threading.Lock()
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent
BANKS=json.loads((ROOT/'puzzle-seeds.json').read_text(encoding='utf-8'))
PUZZLES={hashlib.sha256(('/'.join(p['rows'])).encode()).hexdigest()[:16]:(int(size),p) for size,bank in BANKS.items() for p in bank}
LEGACY_PATH=ROOT/'puzzle-legacy.json'
if LEGACY_PATH.is_file():
 for size,bank in json.loads(LEGACY_PATH.read_text(encoding='utf-8')).items():
  for p in bank:PUZZLES.setdefault(hashlib.sha256(('/'.join(p['rows'])).encode()).hexdigest()[:16],(int(size),p))
DB=Path(os.environ.get('NEMO_DB',str(ROOT/'shared-rankings.sqlite3')))
@contextmanager
def connect():
 db=sqlite3.connect(DB,timeout=10);db.row_factory=sqlite3.Row
 try:
  with db:yield db
 finally:db.close()
def initialize():
 with connect() as db:
  db.executescript('CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, name TEXT NOT NULL, puzzle TEXT NOT NULL, started REAL NOT NULL); CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY REFERENCES runs(id), nickname TEXT NOT NULL, size INTEGER NOT NULL, picture TEXT NOT NULL, ms INTEGER NOT NULL, hints INTEGER NOT NULL, checks INTEGER NOT NULL, nameRevealed INTEGER NOT NULL, date TEXT NOT NULL);')
  if 'aiUses' not in [row[1] for row in db.execute('PRAGMA table_info(records)')]:db.execute('ALTER TABLE records ADD COLUMN aiUses INTEGER NOT NULL DEFAULT 0')
  db.execute('CREATE TABLE IF NOT EXISTS ai_events(id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, state TEXT NOT NULL, response TEXT NOT NULL, created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS ai_requests(id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, created REAL NOT NULL)')

def records():
 with connect() as db:return [dict(r) for r in db.execute('SELECT * FROM records ORDER BY ms,date,id')]
class Handler(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def json(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/api/health':return self.json(200,{'ok':True,'mode':'shared'})
  if path=='/api/records':return self.json(200,{'records':records()})
  if path in ('/','/play','/index.html','/네모로직.html'):
   raw=(ROOT/'dist'/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-cache');self.end_headers();self.wfile.write(raw);return
  return self.json(404,{'error':'페이지를 찾을 수 없습니다.'})
 def do_POST(self):
  origin=self.headers.get('Origin')
  if origin and urlparse(origin).netloc!=self.headers.get('Host'):return self.json(403,{'error':'같은 게임 페이지에서만 기록을 보낼 수 있습니다.'})
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=65536:return self.json(413,{'error':'잘못된 요청 크기입니다.'})
   data=json.loads(self.rfile.read(length))
   if not isinstance(data,dict):raise ValueError()
   path=urlparse(self.path).path
   if path=='/api/runs':
    name=str(data.get('nickname','')).strip()
    if not 1<=len(name)<=16 or any(ord(c)<32 for c in name):return self.json(400,{'error':'닉네임을 1~16자로 입력해 주세요.'})
    rows=data.get('rows');key=hashlib.sha256(('/'.join(rows)).encode()).hexdigest()[:16]
    if key not in PUZZLES:return self.json(400,{'error':'등록되지 않은 퍼즐입니다.'})
    run_id=uuid.uuid4().hex
    with connect() as db:db.execute('INSERT INTO runs VALUES(?,?,?,?)',(run_id,name,key,time.time()))
    return self.json(201,{'id':run_id})
   if path=='/api/ai/hint':
    run_id=data.get('runId')
    with connect() as db:
     run=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
     if not run:return self.json(404,{'error':'새 퍼즐을 시작한 뒤 AI 해설을 요청해 주세요.'})
     if db.execute('SELECT 1 FROM records WHERE id=?',(run_id,)).fetchone():return self.json(409,{'error':'이미 완료된 플레이입니다.'})
     size,puzzle=PUZZLES[run['puzzle']];grid=data.get('grid')
     if not isinstance(grid,list) or len(grid)!=size or any(not isinstance(row,list) or len(row)!=size or any(type(v)!=int or v not in (0,1,2) for v in row) for row in grid):raise ValueError()
     state=json.dumps(grid,separators=(',',':'))
     cached=db.execute('SELECT response FROM ai_events WHERE run_id=? AND state=?',(run_id,state)).fetchone()
     count=db.execute('SELECT COUNT(*) FROM ai_events WHERE run_id=?',(run_id,)).fetchone()[0]
     if cached:return self.json(200,{**json.loads(cached['response']),'aiUses':count,'cached':True})
     if count>=20:return self.json(429,{'error':'이 플레이의 AI 해설 20회를 모두 사용했습니다.'})
    if not AI_LOCK.acquire(blocking=False):return self.json(429,{'error':'다른 플레이어의 AI 해설을 작성 중입니다. 잠시 후 다시 눌러 주세요.'})
    try:
     with connect() as db:
      recent=db.execute('SELECT COUNT(*) FROM ai_requests WHERE created>?',(time.time()-3600,)).fetchone()[0]
      if recent>=30:return self.json(429,{'error':'공유 서버의 시간당 AI 해설 30회를 모두 사용했습니다. 나중에 다시 이용해 주세요.'})
      db.execute('INSERT INTO ai_requests(run_id,created) VALUES(?,?)',(run_id,time.time()))
     suggestion=advise([[int(v) for v in row] for row in puzzle['rows']],grid)
     answer=explain(suggestion,grid)
     response={**answer,'suggestion':suggestion,'source':'Codex CLI'}
     with connect() as db:
      db.execute('INSERT INTO ai_events(run_id,state,response,created) VALUES(?,?,?,?)',(run_id,state,json.dumps(response,ensure_ascii=False),time.time()))
      count=db.execute('SELECT COUNT(*) FROM ai_events WHERE run_id=?',(run_id,)).fetchone()[0]
      db.execute('UPDATE records SET aiUses=? WHERE id=?',(count,run_id))
     return self.json(200,{**response,'aiUses':count,'cached':False})
    except RuntimeError as error:return self.json(503,{'error':str(error)})
    finally:AI_LOCK.release()
   match=re.fullmatch('/api/runs/([a-f0-9]{32})/finish',path)
   if match:
    run_id=match[1]
    with connect() as db:
     previous=db.execute('SELECT * FROM records WHERE id=?',(run_id,)).fetchone()
     if previous:return self.json(200,{'record':dict(previous),'records':records()})
     run=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
     if not run:return self.json(404,{'error':'플레이 세션이 없습니다. 새 퍼즐로 시작해 주세요.'})
     size,puzzle=PUZZLES[run['puzzle']];grid=data.get('grid')
     if not isinstance(grid,list) or len(grid)!=size or any(not isinstance(row,list) or len(row)!=size or any(type(v)!=int or v not in (0,1,2) for v in row) for row in grid):raise ValueError()
     if any((grid[r][c]==1)!=(puzzle['rows'][r][c]=='1') for r in range(size) for c in range(size)):return self.json(400,{'error':'완성된 퍼즐만 랭킹에 등록할 수 있습니다.'})
     ms=data.get('ms');hints=data.get('hints',0);checks=data.get('checks',0)
     if any(type(v)!=int or v<0 for v in [ms,hints,checks]) or ms>(time.time()-run['started'])*1000+2000:raise ValueError()
     date=datetime.now(timezone.utc).isoformat()
     ai_uses=db.execute('SELECT COUNT(*) FROM ai_events WHERE run_id=?',(run_id,)).fetchone()[0]
     db.execute('INSERT OR IGNORE INTO records(id,nickname,size,picture,ms,hints,checks,nameRevealed,date,aiUses) VALUES(?,?,?,?,?,?,?,?,?,?)',(run_id,run['name'],size,puzzle['name'],ms,hints,checks,int(bool(data.get('nameRevealed'))),date,ai_uses))
    return self.json(201,{'record':next(r for r in records() if r['id']==run_id),'records':records()})
   return self.json(404,{'error':'요청 주소를 찾을 수 없습니다.'})
  except (ValueError,TypeError,KeyError):return self.json(400,{'error':'기록 데이터가 올바르지 않습니다.'})
  except Exception as exc:
   print('Request failed:',type(exc).__name__,flush=True);return self.json(500,{'error':'서버 저장에 실패했습니다. 잠시 후 다시 시도해 주세요.'})
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args();initialize()
 server=ThreadingHTTPServer(('0.0.0.0',args.port),Handler)
 print(f'Nonogram shared server: http://127.0.0.1:{args.port}',flush=True)
 try:
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
   probe.connect(('8.8.8.8',80));print(f'Wi-Fi URL: http://{probe.getsockname()[0]}:{args.port}',flush=True)
 except OSError:pass
 server.serve_forever()
if __name__=='__main__':main()
