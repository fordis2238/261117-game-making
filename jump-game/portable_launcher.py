"""Self-contained Windows launcher for the game, rankings and optional public sharing."""
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

RESOURCE = Path(__file__).resolve().parent
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'NemoGarden'


def prepare(data_directory=DATA):
    data_directory.mkdir(parents=True, exist_ok=True)
    os.environ['NEMO_DB'] = str(data_directory / 'shared-rankings.sqlite3')
    import server
    import ai_coach
    server.DB = Path(os.environ['NEMO_DB'])
    ai_coach.ROOT = data_directory
    server.initialize()
    return server


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('8.8.8.8', 80))
            return probe.getsockname()[0]
    except OSError:
        return '127.0.0.1'


def run_test(path):
    """Exercise the *built* app with no dependence on an installed Python runtime."""
    with tempfile.TemporaryDirectory(prefix='nemo-portable-test-') as directory:
        server = prepare(Path(directory))
        class QuietHandler(server.Handler):
            def log_message(self, *_):
                pass
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        threading.Thread(target=http.serve_forever, daemon=True).start()
        address = 'http://127.0.0.1:' + str(http.server_port)
        try:
            with urllib.request.urlopen(address + '/api/health') as response:
                assert json.load(response)['ok']
            with urllib.request.urlopen(address) as response:
                page = response.read().decode('utf-8')
                assert 'aiHint' in page and 'choosePuzzle' in page
            with urllib.request.urlopen(address + '/api/records') as response:
                assert json.load(response)['records'] == []
            rows = server.BANKS['5'][0]['rows']
            def post(route, data):
                request = urllib.request.Request(address + route,
                    data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(request) as response:
                    return json.load(response)
            run = post('/api/runs', {'nickname': 'portable-test', 'rows': rows})
            answer = post('/api/runs/' + run['id'] + '/finish',
                          {'grid': [[int(c) for c in row] for row in rows], 'ms': 0})
            assert answer['record']['nickname'] == 'portable-test'
            server.initialize()
            assert len(server.records()) == 1
            gui = tk.Tk()
            gui.withdraw()
            app = Launcher(gui, data_directory=Path(directory), open_browser=False)
            gui.update()
            assert app.http.server_port and app.local_url.startswith('http://127.0.0.1:')
            app.close()
            tunnel = RESOURCE / 'tools/cloudflared.exe'
            assert tunnel.is_file()
            result = subprocess.run([str(tunnel), '--version'], capture_output=True,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            assert result.returncode == 0
            counts = {size: len(bank) for size, bank in server.BANKS.items()}
            assert all(count >= 103 for count in counts.values())
            report = {'ok': True, 'frozen': bool(getattr(sys, 'frozen', False)),
                      'counts': counts, 'total': sum(counts.values()),
                      'tests': ['embedded page', 'HTTP server', 'SQLite rankings persistence',
                                'Tk window', 'bundled public tunnel', '516 picture puzzles']}
        finally:
            http.shutdown()
            http.server_close()
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


class Launcher:
    def __init__(self, root, data_directory=DATA, open_browser=True):
        self.root = root
        self.stopping = False
        self.tunnel = None
        self.public_url = ''
        self.server = prepare(data_directory)
        class QuietHandler(self.server.Handler):
            def log_message(self, *_):
                pass
        for port in range(8765, 8796):
            try:
                self.http = self.server.ThreadingHTTPServer(('0.0.0.0', port), QuietHandler)
                break
            except OSError:
                continue
        else:
            raise RuntimeError('8765~8795 포트를 사용할 수 없습니다.')
        self.port = port
        self.local_url = f'http://127.0.0.1:{port}/'
        self.wifi_url = f'http://{local_ip()}:{port}/'
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        root.title('네모정원 · 실행 및 공유')
        root.geometry('620x550')
        root.minsize(560, 520)
        root.configure(bg='#eeeee7')
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = tk.Frame(root, bg='#eeeee7', padx=28, pady=20)
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='네모정원', bg='#eeeee7', fg='#315b46',
                 font=('Malgun Gothic', 24, 'bold')).pack(anchor='w')
        tk.Label(frame, text='516개 퍼즐 · Python 설치 없이 실행되는 게임과 공유 랭킹',
                 bg='#eeeee7', fg='#65795c', font=('Malgun Gothic', 10)).pack(anchor='w', pady=(3, 14))
        tk.Label(frame, text='내 PC에서 플레이', bg='#eeeee7', fg='#315b46',
                 font=('Malgun Gothic', 10, 'bold')).pack(anchor='w')
        self.address(frame, self.local_url)
        self.button(frame, '게임 열기', lambda: webbrowser.open(self.local_url), primary=True)
        tk.Label(frame, text='같은 와이파이의 다른 기기에서 접속', bg='#eeeee7', fg='#315b46',
                 font=('Malgun Gothic', 10, 'bold')).pack(anchor='w', pady=(13, 0))
        self.address(frame, self.wifi_url)
        self.button(frame, '와이파이 접속 주소 복사', lambda: self.copy(self.wifi_url))
        self.share_button = self.button(frame, '인터넷 공개 공유 시작', self.share)
        self.status = tk.StringVar(value='공개 공유를 시작하면 와이파이 밖에서도 링크로 접속할 수 있습니다.')
        tk.Label(frame, textvariable=self.status, wraplength=550, justify='left',
                 bg='#eeeee7', fg='#65795c', font=('Malgun Gothic', 9)).pack(anchor='w', pady=(8, 3))
        self.public_entry = tk.Entry(frame, readonlybackground='#fcfcf8', fg='#315b46',
                                    relief='flat', font=('Consolas', 10))
        self.public_entry.pack(fill='x', ipady=5)
        self.public_entry.configure(state='readonly')
        self.copy_public = self.button(frame, '공개 주소 복사', lambda: self.copy(self.public_url))
        self.copy_public.configure(state='disabled')
        tk.Label(frame, text='이 창을 닫으면 서버와 공개 공유도 종료됩니다.\n'
                            'AI 해설만 Codex CLI 설치·로그인과 인터넷 연결이 필요합니다.\n'
                            '랭킹은 이 PC에 저장되며, 다른 서버의 랭킹과는 별개입니다.',
                 bg='#eeeee7', fg='#7d8c72', justify='left', font=('Malgun Gothic', 9)).pack(anchor='w', pady=(13, 0))
        if open_browser:
            root.after(600, lambda: webbrowser.open(self.local_url))

    def address(self, parent, value):
        entry = tk.Entry(parent, readonlybackground='#fcfcf8', fg='#315b46',
                         relief='flat', font=('Consolas', 11))
        entry.insert(0, value)
        entry.configure(state='readonly')
        entry.pack(fill='x', ipady=5, pady=(3, 6))

    def button(self, parent, text, command, primary=False):
        button = tk.Button(parent, text=text, command=command, relief='flat', cursor='hand2',
                           bg='#315b46' if primary else '#dfe8d6',
                           fg='white' if primary else '#315b46',
                           activebackground='#afc5a3', font=('Malgun Gothic', 10), pady=5)
        button.pack(fill='x', pady=3)
        return button

    def copy(self, text):
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            self.status.set('접속 주소를 복사했습니다.')

    def share(self):
        if self.tunnel and self.tunnel.poll() is None:
            self.copy(self.public_url)
            return
        self.share_button.configure(state='disabled')
        self.status.set('공개 주소를 만드는 중입니다. 잠시 기다려 주세요…')
        threading.Thread(target=self.create_tunnel, daemon=True).start()

    def create_tunnel(self):
        try:
            log = DATA / 'public-tunnel.log'
            executable = RESOURCE / 'tools/cloudflared.exe'
            # Avoid passing the frozen Python DLL search path to external executables.
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(None)
            with log.open('w', encoding='utf-8') as err, (DATA / 'public-output.log').open('w') as out:
                self.tunnel = subprocess.Popen([str(executable), 'tunnel', '--url', self.local_url,
                                               '--no-autoupdate'], stdout=out, stderr=err,
                                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            for _ in range(120):
                if self.stopping:
                    return
                if self.tunnel.poll() is not None:
                    raise RuntimeError('공유 프로그램이 종료됐습니다. 인터넷 연결을 확인해 주세요.')
                content = log.read_text(encoding='utf-8', errors='replace')
                match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', content)
                if match:
                    try:
                        with urllib.request.urlopen(match[0] + '/api/health', timeout=4) as response:
                            if json.load(response).get('ok'):
                                self.public_url = match[0] + '/'
                                self.root.after(0, self.shared)
                                return
                    except Exception:
                        pass
                time.sleep(.5)
            raise RuntimeError('공개 주소 연결 시간이 초과됐습니다. 다시 시도해 주세요.')
        except Exception as error:
            self.stop_tunnel()
            if not self.stopping:
                self.root.after(0, lambda text=str(error): self.share_failed(text))

    def shared(self):
        self.public_entry.configure(state='normal')
        self.public_entry.delete(0, 'end')
        self.public_entry.insert(0, self.public_url)
        self.public_entry.configure(state='readonly')
        self.copy_public.configure(state='normal')
        self.share_button.configure(state='normal', text='공개 주소 다시 복사')
        self.status.set('공개 공유 중입니다. 이 창을 켜 두세요. 재시작하면 주소가 바뀔 수 있습니다.')

    def share_failed(self, text):
        self.status.set(text)
        self.share_button.configure(state='normal', text='인터넷 공개 공유 다시 시도')

    def stop_tunnel(self):
        if self.tunnel and self.tunnel.poll() is None:
            self.tunnel.terminate()
            try:
                self.tunnel.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.tunnel.kill()

    def close(self):
        self.stopping = True
        self.stop_tunnel()
        self.http.shutdown()
        self.http.server_close()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', metavar='RESULT_JSON')
    args = parser.parse_args()
    if args.self_test:
        run_test(args.self_test)
        return
    root = tk.Tk()
    try:
        Launcher(root)
        root.mainloop()
    except Exception as error:
        DATA.mkdir(parents=True, exist_ok=True)
        import traceback
        (DATA / 'launcher-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        messagebox.showerror('네모정원 실행 오류', str(error), parent=root)
        root.destroy()


if __name__ == '__main__':
    main()
