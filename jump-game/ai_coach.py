"""Verified puzzle advice explained by a real, bounded Codex CLI invocation."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def runs(values):
    return [len(part) for part in ''.join(map(str, values)).split('0') if part] or [0]


def patterns(clues, n):
    if clues == [0]:
        return [[0] * n]
    result = []

    def place(i, position, row):
        if i == len(clues):
            result.append(row + [0] * (n - len(row)))
            return
        remaining = sum(clues[i:]) + len(clues) - i - 1
        for start in range(position, n - remaining + 1):
            following = row + [0] * (start - len(row)) + [1] * clues[i]
            if i < len(clues) - 1:
                following += [0]
            place(i + 1, len(following), following)

    place(0, 0, [])
    return result


def advise(solution, grid):
    n = len(solution)
    for r in range(n):
        for c in range(n):
            if grid[r][c] and (grid[r][c] == 1) != bool(solution[r][c]):
                return dict(row=r, col=c, value=1 if solution[r][c] else 2,
                            kind='correction', basis='정답 대조로 확인한 잘못된 표시 수정',
                            evidence={'current': grid[r][c]})
    for axis in ('row', 'column'):
        for i in range(n):
            line = solution[i] if axis == 'row' else [solution[r][i] for r in range(n)]
            marks = grid[i] if axis == 'row' else [grid[r][i] for r in range(n)]
            clues = runs(line)
            possible = [p for p in patterns(clues, n)
                        if all(v == 0 or p[j] == (1 if v == 1 else 0)
                               for j, v in enumerate(marks))]
            for j, v in enumerate(marks):
                if v == 0 and possible and len({p[j] for p in possible}) == 1:
                    r, c = (i, j) if axis == 'row' else (j, i)
                    value = possible[0][j]
                    if value != solution[r][c]:
                        raise ValueError('검증된 후보가 정답과 다릅니다.')
                    return dict(row=r, col=c, value=1 if value else 2, kind='deduction',
                                basis='이 줄의 가능한 모든 배치에서 같은 값인 칸',
                                evidence={'axis': axis, 'lineNumber': i + 1, 'clues': clues,
                                          'marks': marks, 'possibleCount': len(possible),
                                          'samplePatterns': possible[:8]})
    # No immediate line deduction: make a clearly labelled trial, not a fake certainty.
    for r in range(n):
        for c in range(n):
            if grid[r][c] == 0:
                return dict(row=r, col=c, value=1, kind='assumption',
                            basis='현재 줄 단위 검사에서는 확정 수를 찾지 못함. 채움을 가정해 모순을 확인할 후보이며 정답 보장은 없음.',
                            evidence={'rowClues': runs(solution[r]),
                                      'colClues': runs([solution[i][c] for i in range(n)])})
    raise ValueError('이미 완성된 보드입니다.')


SCHEMA = {'type': 'object', 'additionalProperties': False,
          'properties': {'title': {'type': 'string'}, 'explanation': {'type': 'string'}},
          'required': ['title', 'explanation']}


def explain(candidate, grid, timeout=110):
    native = shutil.which('codex.exe')
    node = shutil.which('node')
    entry = Path(os.environ.get('APPDATA', '')) / 'npm/node_modules/@openai/codex/bin/codex.js'
    prefix = [native] if native else [node, str(entry)] if node and entry.is_file() else None
    if not prefix:
        raise RuntimeError('서버 PC에서 Codex CLI 또는 Node.js를 찾지 못했습니다.')
    prompt = ('너는 네모로직 게임의 한국어 코치다. 도구, 셸, 파일, 웹 검색을 사용하지 말고 아래 JSON만 읽어라. '
              'candidate는 서버의 검사 결과다. 좌표는 0부터 시작하므로 사용자에게는 1을 더해 말하라. '
              'value 1은 채우기, 2는 X 표시다. grid에서 0은 미정, 1은 채움, 2는 X다. '
              '서버가 정한 좌표와 값을 바꾸지 마라. kind deduction은 줄의 모든 가능한 배치에 공통인 결과이고, '
              'correction은 정답 대조 결과이므로 논리적으로 유도했다는 거짓 설명을 하지 마라. '
              'assumption은 반드시 가정이며 확정 아님을 밝히고, 더 강한 전역 추론으로 풀릴 가능성을 부정하지 마라. '
              '숫자 힌트와 주어진 증거만 이용해 간결한 제목과 한국어 2~4문장의 설명을 작성하라. '
              '정답 그림이나 다른 칸의 답은 공개하지 마라. JSON 스키마로만 답하라.\n' +
              json.dumps({'candidate': candidate, 'grid': grid}, ensure_ascii=False))
    with tempfile.TemporaryDirectory(prefix='nemo-ai-') as directory:
        work = Path(directory)
        schema = work / 'schema.json'
        output = work / 'answer.json'
        schema.write_text(json.dumps(SCHEMA), encoding='utf-8')
        command = prefix + ['exec', '--sandbox', 'read-only', '--ignore-user-config',
                   '--ephemeral', '--skip-git-repo-check', '--cd', directory,
                   '--output-schema', str(schema), '--output-last-message', str(output), '-']
        if os.name == 'nt' and getattr(__import__('sys'), 'frozen', False):
            import ctypes
            ctypes.windll.kernel32.SetDllDirectoryW(None)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding='utf-8',
                                   errors='replace',
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            stdout, stderr = process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               capture_output=True,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            else:
                process.kill()
            process.communicate()
            raise RuntimeError('Codex 응답 시간이 초과됐습니다. 잠시 후 다시 요청해 주세요.') from error
        if process.returncode or not output.is_file():
            # Logs can contain account details; only expose a bounded operational error.
            (ROOT / 'ai-last-error.log').write_text(stderr[-6000:], encoding='utf-8')
            raise RuntimeError('Codex CLI 실행에 실패했습니다. 서버 PC의 로그인과 사용 가능량을 확인해 주세요.')
        try:
            answer = json.loads(output.read_text(encoding='utf-8'))
        except (ValueError, OSError) as error:
            raise RuntimeError('Codex가 올바른 JSON 해설을 반환하지 않았습니다.') from error
        if not isinstance(answer.get('title'), str) or not isinstance(answer.get('explanation'), str):
            raise RuntimeError('AI 응답 형식을 확인하지 못했습니다.')
        return {'title': answer['title'][:120], 'explanation': answer['explanation'][:1600]}
