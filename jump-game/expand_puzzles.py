"""Create 100 additional verified picture puzzles per level, deterministically."""
import ast
import hashlib
import json
import random
import time
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent


def definitions(filename):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8-sig'))
    tree.body = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom,
                                                      ast.FunctionDef, ast.ClassDef))]
    namespace = {}
    exec(compile(tree, filename, 'exec'), namespace)
    return namespace


normal = definitions('generate_harder.py')
normal['options'] = lru_cache(maxsize=2500)(normal['options'])
expert = definitions('generate_expert.py')
expert['g'] = SimpleNamespace(**{k: normal[k] for k in ('runs', 'options', 'solve', 'picture')})

GLYPHS = {
 '문자 A':'01110/10001/11111/10001/10001', '문자 B':'11110/10001/11110/10001/11110',
 '문자 C':'01111/10000/10000/10000/01111', '문자 D':'11110/10001/10001/10001/11110',
 '문자 E':'11111/10000/11110/10000/11111', '문자 F':'11111/10000/11110/10000/10000',
 '문자 G':'01111/10000/10111/10001/01111', '문자 H':'10001/10001/11111/10001/10001',
 '문자 I':'11111/00100/00100/00100/11111', '문자 J':'00111/00010/00010/10010/01100',
 '문자 K':'10001/10010/11100/10010/10001', '문자 L':'10000/10000/10000/10000/11111',
 '문자 M':'10001/11011/10101/10001/10001', '문자 N':'10001/11001/10101/10011/10001',
 '문자 O':'01110/10001/10001/10001/01110', '문자 P':'11110/10001/11110/10000/10000',
 '문자 Q':'01110/10001/10101/10010/01101', '문자 R':'11110/10001/11110/10010/10001',
 '문자 S':'01111/10000/01110/00001/11110', '문자 T':'11111/00100/00100/00100/00100',
 '문자 U':'10001/10001/10001/10001/01110', '문자 V':'10001/10001/10001/01010/00100',
 '문자 W':'10001/10001/10101/11011/10001', '문자 X':'10001/01010/00100/01010/10001',
 '문자 Y':'10001/01010/00100/00100/00100', '문자 Z':'11111/00010/00100/01000/11111',
 '숫자 0':'01110/10011/10101/11001/01110', '숫자 1':'00100/01100/00100/00100/01110',
 '숫자 2':'01110/10001/00110/01000/11111', '숫자 3':'11110/00001/01110/00001/11110',
 '숫자 4':'10010/10010/11111/00010/00010', '숫자 5':'11111/10000/11110/00001/11110',
 '숫자 6':'01110/10000/11110/10001/01110', '숫자 7':'11111/00001/00010/00100/00100',
 '숫자 8':'01110/10001/01110/10001/01110', '숫자 9':'01110/10001/01111/00001/01110',
 '깃발':'11110/10110/11110/10000/10000', '화살표':'00100/01100/11111/01100/00100',
 '우산':'01110/11111/00100/10100/01100', '왕관':'10101/11111/11111/01110/01110',
 '음표':'00111/00101/00101/11100/11100', '체크':'00001/00010/10100/01000/00000',
 '물고기':'00110/01111/11101/01111/00110', '버섯':'01110/11111/10101/00100/01110',
 '선물':'01010/11111/00100/11111/11111', '컵':'11110/10011/10011/11110/01100',
 '꽃':'00100/01110/11111/00100/01100', '열쇠':'01100/01000/01111/00010/00011',
 '강아지':'11011/11111/10101/11111/01110', '고양이':'10001/11011/10101/11111/01110',
 '번개':'00110/01100/11110/00100/01000', '자동차':'01110/11111/10101/11111/01010',
 '나비':'11011/11111/01110/11011/11011', '하트':'01010/11111/11111/01110/00100',
 '나무':'00100/01110/11111/00100/01110', '집':'00100/01110/11111/11011/11011',
}


def art(name, size, variation):
    if name in ('부엉이', '로봇', '우주선', '범선', '꽃병'):
        return normal['picture'](name, size, variation)
    image = Image.new('1', (20, 20))
    d = ImageDraw.Draw(image)
    if name == '열기구':
        d.ellipse((3, 0, 16, 13), fill=1); d.line((6, 3, 6, 10), fill=0)
        d.line((13, 3, 13, 10), fill=0); d.line((6, 12, 8, 16), fill=1)
        d.line((13, 12, 11, 16), fill=1); d.rectangle((7, 16, 12, 19), fill=1)
    elif name == '물고기':
        d.ellipse((3, 4, 17, 15), fill=1); d.polygon([(5, 9), (0, 4), (0, 15)], fill=1)
        d.ellipse((13, 7, 14, 8), fill=0); d.line((8, 7, 10, 11), fill=0)
    elif name == '버섯':
        d.ellipse((1, 1, 18, 15), fill=1); d.rectangle((0, 11, 19, 16), fill=0)
        d.rectangle((7, 11, 12, 18), fill=1); d.ellipse((3, 5, 5, 7), fill=0)
        d.ellipse((11, 3, 14, 6), fill=0); d.line((5, 19, 14, 19), fill=1)
    elif name == '성':
        for x in (1, 8, 15):
            d.rectangle((x, 2, x + 3, 18), fill=1); d.rectangle((x + 1, 5, x + 2, 7), fill=0)
        d.rectangle((2, 9, 17, 19), fill=1); d.ellipse((7, 13, 12, 20), fill=0)
        d.rectangle((7, 16, 12, 19), fill=0)
    elif name == '고양이':
        d.polygon([(3, 0), (7, 4), (12, 4), (16, 0), (16, 11), (14, 14), (5, 14), (3, 11)], fill=1)
        d.rectangle((6, 7, 7, 8), fill=0); d.rectangle((12, 7, 13, 8), fill=0)
        d.line((9, 11, 10, 11), fill=0); d.ellipse((5, 12, 14, 19), fill=1)
        d.arc((11, 10, 19, 19), 270, 100, fill=1, width=2)
    elif name == '눈사람':
        d.ellipse((6, 2, 13, 9), fill=1); d.ellipse((3, 9, 16, 19), fill=1)
        d.rectangle((6, 0, 13, 3), fill=1); d.line((4, 3, 15, 3), fill=1)
        for x, y in ((8, 5), (11, 5), (9, 12), (9, 16)): d.point((x, y), fill=0)
        d.line((0, 8, 4, 13), fill=1); d.line((15, 13, 19, 8), fill=1)
    elif name == '우산':
        d.ellipse((1, 0, 18, 15), fill=1); d.rectangle((0, 9, 19, 19), fill=0)
        d.line((9, 9, 9, 17), fill=1, width=2); d.arc((4, 14, 10, 19), 0, 180, fill=1, width=2)
        d.line((6, 3, 5, 7), fill=0); d.line((13, 3, 14, 7), fill=0)
    elif name == '카메라':
        d.rectangle((1, 5, 18, 16), fill=1); d.rectangle((4, 2, 9, 5), fill=1)
        d.ellipse((5, 6, 14, 15), fill=0); d.ellipse((7, 8, 12, 13), fill=1)
        d.rectangle((15, 7, 16, 8), fill=0)
    elif name == '선물':
        d.rectangle((2, 7, 17, 19), fill=1); d.rectangle((0, 5, 19, 8), fill=1)
        d.line((9, 6, 9, 19), fill=0, width=2); d.line((2, 13, 17, 13), fill=0)
        d.ellipse((3, 0, 9, 5), fill=1); d.ellipse((10, 0, 16, 5), fill=1)
        d.point((6, 2), fill=0); d.point((13, 2), fill=0)
    elif name == '체리':
        d.line((11, 0, 6, 10), fill=1); d.line((11, 0, 15, 10), fill=1)
        d.ellipse((1, 8, 10, 18), fill=1); d.ellipse((11, 8, 19, 17), fill=1)
        d.rectangle((4, 10, 5, 11), fill=0); d.rectangle((14, 10, 15, 11), fill=0)
        d.ellipse((11, 0, 17, 3), fill=1)
    else:
        glyph = GLYPHS[name].split('/')
        source = Image.new('1', (5, 5)); source.putdata([int(v) for row in glyph for v in row])
        width = 15 + variation % 4
        source = source.resize((width, width), Image.Resampling.NEAREST)
        image.paste(source, ((20 - width) // 2, (20 - width) // 2))
    image = image.resize((size, size), Image.Resampling.NEAREST)
    rng = random.Random(variation * 731 + sum(map(ord, name)))
    for _ in range(variation % 7):
        r, c = rng.randrange(1, size - 1), rng.randrange(1, size - 1)
        if image.getpixel((c, r)) and sum(bool(image.getpixel((cc, rr))) for rr, cc in
                                       ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))) >= 3:
            image.putpixel((c, r), 0)
    return [[int(bool(image.getpixel((c, r)))) for c in range(size)] for r in range(size)]


def rows_of(grid):
    return [''.join(map(str, row)) for row in grid]


def transform(grid, value):
    grid = [row[:] for row in grid]
    if value >= 4:
        grid = [row[::-1] for row in grid]
    for _ in range(value % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def main():
    banks = json.loads((ROOT / 'puzzle-seeds-base.json').read_text(encoding='utf-8'))
    report = []
    rng = random.Random(5172026)
    start = time.monotonic()
    for size in (5, 10, 15, 20, 25):
        bank = banks[str(size)]
        initial = len(bank)
        seen = {'/'.join(p['rows']) for p in bank}
        themes = ['부엉이', '로봇', '우주선', '범선', '꽃병', '열기구', '물고기', '버섯',
                  '성', '고양이', '눈사람', '우산', '카메라', '선물', '체리'] + list(GLYPHS)
        accepted = 0
        attempts = 0
        while accepted < 100:
            attempts += 1
            if attempts > 100000:
                raise RuntimeError(f'Not enough verified puzzles at {size}: {accepted}')
            if size == 5:
                name = list(GLYPHS)[(attempts - 1) % len(GLYPHS)]
                grid = [[int(v) for v in row] for row in GLYPHS[name].split('/')]
                variant = (attempts - 1) // len(GLYPHS)
                if variant:
                    for index in rng.sample(range(25), 1 if variant <= 2 else 2):
                        r, c = divmod(index, 5)
                        grid[r][c] ^= 1
            elif size == 25:
                source = banks['25'][(attempts - 1) % initial]
                name = source['name']
                grid = [[int(v) for v in row] for row in source['rows']]
                # Different decorations and panel motifs keep a recognizable picture,
                # while retaining its already verified branching core.
                empty_rows = [r for r, row in enumerate(grid) if not any(row)]
                empty_cols = [c for c in range(size) if not any(grid[r][c] for r in range(size))]
                if empty_rows:
                    r = rng.choice(empty_rows)
                    left = rng.randrange(0, size - 4)
                    for c in range(left, min(size, left + rng.randrange(2, 9))):
                        grid[r][c] = int(rng.random() < .75)
                elif empty_cols:
                    c = rng.choice(empty_cols)
                    for r in range(rng.randrange(0, 8), rng.randrange(10, 23)):
                        grid[r][c] = int(rng.random() < .75)
                grid = transform(grid, (attempts // initial) % 8)
            else:
                name = themes[(attempts - 1) % len(themes)]
                grid = art(name, size, attempts // len(themes))
            rows = rows_of(grid)
            key = '/'.join(rows)
            if key in seen or sum(map(sum, grid)) < size:
                continue
            if size == 25:
                if normal['solve'](grid) is not None:
                    continue
                count, depth, nodes = expert['analyze'](grid)
                if count != 1 or depth < 1:
                    continue
                validation = {'unique': True, 'requiresBranching': True,
                              'branchDepth': depth, 'searchNodes': nodes}
            else:
                validation = normal['solve'](grid)
                if not validation:
                    continue
                if size in (15, 20) and validation['rounds'] < (3 if size == 15 else 4):
                    continue
                validation = {'unique': True, 'requiresBranching': False, **validation}
            seen.add(key)
            ident = hashlib.sha256(key.encode()).hexdigest()[:16]
            bank.append({'name': name, 'rows': rows, 'id': ident})
            report.append({'size': size, 'id': ident, **validation})
            accepted += 1
            if accepted % 20 == 0:
                print(f'{size}x{size}: added {accepted}/100, attempts={attempts}', flush=True)
        for puzzle in bank:
            puzzle.setdefault('id', hashlib.sha256('/'.join(puzzle['rows']).encode()).hexdigest()[:16])
        (ROOT / 'puzzle-seeds-expanded.json').write_text(json.dumps(banks, ensure_ascii=False), encoding='utf-8')
        print(f'LEVEL PASS: {size}, old={initial}, added=100, total={len(bank)}', flush=True)
    result = {'added': 500, 'counts': {k: len(v) for k, v in banks.items()},
              'seconds': round(time.monotonic() - start, 2), 'puzzles': report}
    (ROOT / 'expanded-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('ALL PASS', result['counts'], result['seconds'], flush=True)


if __name__ == '__main__':
    main()
