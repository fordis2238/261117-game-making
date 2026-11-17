"""Distinct picture subjects with a woven 7x7 branching motif, fully revalidated."""
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw
import expand_puzzles as verify

ROOT = Path(__file__).resolve().parent
THEMES = ['거북이', '로봇', '물고기', '열기구', '선물', '집', '성', '카메라', '텔레비전',
          '배낭', '여행가방', '고래', '버스', '기차', '파인애플', '사과', '배', '도토리',
          '주전자', '컵케이크', '화분', '버섯', '꿀벌', '나비', '알람시계']


def draw_subject(name):
    im = Image.new('1', (25, 25)); d = ImageDraw.Draw(im)
    patch = (8, 11)
    if name == '거북이':
        d.ellipse((3, 5, 21, 22), fill=1); d.ellipse((20, 8, 24, 13), fill=1)
        for rect in [(3, 3, 7, 7), (3, 20, 7, 24), (17, 3, 21, 7), (17, 20, 21, 24)]: d.ellipse(rect, fill=1)
        d.point((23, 10), fill=0)
    elif name == '로봇':
        d.rectangle((5, 2, 19, 9), fill=1); d.line((12, 0, 12, 2), fill=1)
        d.rectangle((7, 4, 9, 6), fill=0); d.rectangle((15, 4, 17, 6), fill=0)
        d.rectangle((5, 11, 19, 22), fill=1); d.rectangle((1, 12, 3, 20), fill=1)
        d.rectangle((21, 12, 23, 20), fill=1); d.rectangle((6, 23, 9, 24), fill=1)
        d.rectangle((15, 23, 18, 24), fill=1); patch = (8, 12)
    elif name == '물고기':
        d.ellipse((3, 3, 24, 22), fill=1); d.polygon([(5, 12), (0, 5), (0, 20)], fill=1)
        d.ellipse((20, 8, 21, 9), fill=0); patch = (9, 8)
    elif name == '열기구':
        d.ellipse((2, 0, 22, 18), fill=1); d.line((7, 16, 9, 21), fill=1)
        d.line((17, 16, 15, 21), fill=1); d.rectangle((8, 21, 16, 24), fill=1); patch = (8, 5)
    elif name == '선물':
        d.rectangle((2, 8, 22, 24), fill=1); d.rectangle((0, 6, 24, 9), fill=1)
        d.ellipse((4, 0, 11, 5), fill=1); d.ellipse((13, 0, 20, 5), fill=1)
        d.point((7, 2), fill=0); d.point((17, 2), fill=0)
    elif name in ('집', '성'):
        d.rectangle((3, 10, 21, 24), fill=1)
        if name == '집': d.polygon([(1, 10), (12, 0), (23, 10)], fill=1)
        else:
            for x in (3, 10, 17): d.rectangle((x, 1, x + 4, 12), fill=1)
            d.rectangle((4, 4, 5, 6), fill=0); d.rectangle((18, 4, 19, 6), fill=0)
        d.rectangle((4, 19, 6, 24), fill=0); patch = (10, 12)
    elif name in ('카메라', '텔레비전', '여행가방'):
        d.rounded_rectangle((1, 6, 23, 22), radius=3, fill=1)
        if name == '카메라':
            d.rectangle((4, 3, 10, 7), fill=1); d.rectangle((3, 9, 5, 10), fill=0)
        elif name == '텔레비전':
            d.line((5, 0, 12, 6), fill=1); d.line((19, 0, 12, 6), fill=1)
            d.line((5, 22, 3, 24), fill=1); d.line((19, 22, 21, 24), fill=1)
        else:
            d.rectangle((8, 1, 16, 6), outline=1, width=2); d.rectangle((3, 23, 6, 24), fill=1)
            d.rectangle((18, 23, 21, 24), fill=1)
        patch = (8, 10)
    elif name == '배낭':
        d.rounded_rectangle((4, 4, 20, 24), radius=5, fill=1)
        d.arc((9, 0, 15, 6), 180, 360, fill=1, width=2); d.line((6, 9, 18, 9), fill=0)
        patch = (8, 12)
    elif name == '고래':
        d.ellipse((3, 7, 24, 23), fill=1); d.polygon([(6, 14), (0, 6), (0, 17)], fill=1)
        d.ellipse((20, 11, 21, 12), fill=0); d.line((15, 7, 15, 1), fill=1)
        d.arc((10, 0, 15, 4), 180, 360, fill=1); d.arc((15, 0, 20, 4), 180, 360, fill=1)
        patch = (9, 11)
    elif name in ('버스', '기차'):
        d.rectangle((1, 7, 23, 20), fill=1)
        for x in (3, 7, 11, 15, 19): d.rectangle((x, 8, x + 2, 10), fill=0)
        d.ellipse((3, 19, 8, 24), fill=1); d.ellipse((17, 19, 22, 24), fill=1)
        if name == '기차': d.rectangle((4, 1, 8, 7), fill=1); d.line((2, 1, 10, 1), fill=1)
        else: d.rectangle((3, 4, 21, 7), fill=1)
        patch = (9, 11)
    elif name in ('파인애플', '사과', '배', '도토리'):
        d.ellipse((3, 6, 22, 24), fill=1)
        if name == '파인애플': d.polygon([(12, 7), (5, 0), (11, 3), (12, 0), (15, 4), (20, 0), (17, 8)], fill=1)
        elif name == '도토리': d.ellipse((1, 3, 24, 12), fill=1); d.line((12, 0, 12, 4), fill=1)
        else:
            d.line((12, 2, 11, 7), fill=1, width=2); d.ellipse((13, 0, 20, 4), fill=1)
            if name == '배': d.ellipse((8, 3, 18, 13), fill=1)
        patch = (8, 12)
    elif name == '주전자':
        d.ellipse((4, 6, 21, 24), fill=1); d.arc((17, 7, 24, 20), 270, 90, fill=1, width=2)
        d.polygon([(5, 14), (0, 8), (0, 16), (6, 21)], fill=1)
        d.rectangle((6, 4, 20, 6), fill=1); d.rectangle((11, 2, 14, 4), fill=1)
    elif name == '컵케이크':
        d.polygon([(3, 12), (21, 12), (19, 24), (5, 24)], fill=1)
        d.ellipse((3, 2, 21, 15), fill=1); d.ellipse((10, 0, 14, 4), fill=1)
        patch = (8, 12)
    elif name == '화분':
        d.polygon([(3, 13), (22, 13), (19, 24), (6, 24)], fill=1)
        d.line((12, 3, 12, 13), fill=1, width=2)
        d.ellipse((3, 2, 11, 8), fill=1); d.ellipse((14, 0, 22, 6), fill=1)
        patch = (8, 14)
    elif name == '버섯':
        d.ellipse((0, 0, 24, 18), fill=1); d.rectangle((0, 15, 24, 24), fill=0)
        d.rectangle((9, 15, 15, 24), fill=1); patch = (8, 5)
    elif name in ('꿀벌', '나비'):
        d.ellipse((7, 4, 17, 24), fill=1); d.line((8, 0, 11, 5), fill=1); d.line((16, 0, 13, 5), fill=1)
        d.ellipse((0, 5, 8, 15), fill=1); d.ellipse((16, 5, 24, 15), fill=1)
        if name == '나비': d.ellipse((1, 15, 8, 23), fill=1); d.ellipse((16, 15, 23, 23), fill=1)
        else: d.line((2, 20, 22, 20), fill=1)
        patch = (8, 10)
    elif name == '알람시계':
        d.ellipse((2, 4, 22, 23), fill=1); d.ellipse((1, 0, 8, 5), fill=1)
        d.ellipse((16, 0, 23, 5), fill=1); d.line((5, 21, 3, 24), fill=1)
        d.line((19, 21, 21, 24), fill=1); patch = (8, 10)
    return [[int(bool(im.getpixel((c, r)))) for c in range(25)] for r in range(25)], patch


def main():
    kernels = json.loads((ROOT / 'branch-kernels.json').read_text())
    rng = random.Random(17112026)
    selected = []; statistics = {}; start = time.monotonic(); seen = set()
    for name in THEMES:
        image, (left, top) = draw_subject(name)
        choices = list(range(len(kernels) * 8)); rng.shuffle(choices)
        for choice in choices:
            grid = [row[:] for row in image]
            kernel = [[int(c) for c in row] for row in kernels[choice // 8]]
            kernel = verify.transform(kernel, choice % 8)
            for r in range(top, top + 9):
                for c in range(left, left + 9):
                    grid[r][c] = kernel[r - top - 1][c - left - 1] if top < r < top + 8 and left < c < left + 8 else 0
            key = '/'.join(verify.rows_of(grid))
            if key in seen or verify.normal['solve'](grid) is not None: continue
            count, depth, nodes = verify.expert['analyze'](grid)
            if count != 1 or depth < 1: continue
            seen.add(key)
            selected.append({'name': name, 'rows': verify.rows_of(grid),
                             'id': hashlib.sha256(key.encode()).hexdigest()[:16]})
            statistics[name] = statistics.get(name, 0) + 1
            if statistics[name] >= 6: break
        print(name, statistics.get(name, 0), 'total', len(selected), flush=True)
    (ROOT / 'diverse-expert-candidates.json').write_text(json.dumps(selected, ensure_ascii=False), encoding='utf-8')
    print('DONE', len(selected), len(statistics), round(time.monotonic() - start, 1), flush=True)


if __name__ == '__main__': main()
