"""Start or reuse a temporary public sharing URL, without changing firewall settings."""
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'public-share-state.json'
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def healthy(url):
    try:
        with urllib.request.urlopen(url.rstrip('/') + '/api/health', timeout=5) as response:
            return json.load(response).get('mode') == 'shared'
    except Exception:
        return False


def publish_info(state):
    STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')
    info = ('네모정원 공개 공유 주소\n\n' + state['url'] + '/\n\n'
            '링크를 전달하면 누구나 가입 없이 플레이할 수 있습니다.\n'
            '공유 랭킹과 Codex AI 해설이 연결됩니다.\n'
            'AI 해설은 서버 전체 시간당 30회이며 한 번에 하나씩 처리합니다.\n\n'
            '임시 공개 주소입니다. 이 PC와 서버, cloudflared가 실행 중이어야 합니다.\n'
            'PC를 재시작한 뒤에는 공개공유시작.cmd를 실행하세요.\n'
            '재실행하면 새 주소가 만들어질 수 있습니다.\n')
    (ROOT.parent / '공개공유주소.txt').write_text(info, encoding='utf-8')
    print(info, flush=True)


def main():
    if STATE.is_file():
        state = json.loads(STATE.read_text(encoding='utf-8'))
        if healthy(state['url']):
            publish_info(state)
            return
    if not healthy('http://127.0.0.1:8765'):
        with (ROOT / 'server.log').open('w') as out, (ROOT / 'server-error.log').open('w') as err:
            subprocess.Popen([sys.executable, '-u', str(ROOT / 'server.py')], cwd=ROOT,
                             stdout=out, stderr=err, creationflags=FLAGS)
        for _ in range(20):
            if healthy('http://127.0.0.1:8765'):
                break
            time.sleep(.5)
        else:
            raise RuntimeError('게임 서버 시작에 실패했습니다. server-error.log를 확인하세요.')
    executable = ROOT / 'tools/cloudflared.exe'
    if not executable.is_file():
        raise RuntimeError('공유 프로그램 tools/cloudflared.exe가 없습니다.')
    log = ROOT / 'public-tunnel-error.log'
    with (ROOT / 'public-tunnel.log').open('w') as out, log.open('w') as err:
        process = subprocess.Popen([str(executable), 'tunnel', '--url',
                                    'http://127.0.0.1:8765', '--no-autoupdate'],
                                   cwd=ROOT, stdout=out, stderr=err, creationflags=FLAGS)
    for _ in range(120):
        if process.poll() is not None:
            raise RuntimeError('공유 프로그램이 종료되었습니다. public-tunnel-error.log를 확인하세요.')
        content = log.read_text(encoding='utf-8', errors='replace')
        match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', content)
        if match and healthy(match[0]):
            publish_info({'url': match[0], 'pid': process.pid})
            return
        time.sleep(.5)
    raise RuntimeError('공개 주소 연결을 확인하지 못했습니다. 공유 로그를 확인하세요.')


if __name__ == '__main__':
    main()
