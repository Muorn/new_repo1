#!/usr/bin/env python3
"""Collect a limited visual research pack from a public official WEBTOON episode.

This is intentionally constrained: official webtoons.com episode URLs only, a bounded
number of images, and a contact sheet for GPT review. The output is a research/source
pack; it is not automatically published or treated as licensed material.
"""
import html
import json
import math
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw

ALLOWED_HOSTS = {"www.webtoons.com", "m.webtoons.com"}
MAX_IMAGES = 20
MAX_FILE_BYTES = 8 * 1024 * 1024


def fetch(url: str, referer: str | None = None) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GPT-Manhwa-Research/2.0)",
        "Accept": "text/html,image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"asset too large: {url}")
    return data


def extract_image_urls(page_html: str):
    candidates = []
    patterns = [r'data-url=["\']([^"\']+)["\']', r'src=["\']([^"\']+)["\']']
    for pat in patterns:
        for raw in re.findall(pat, page_html, flags=re.I):
            u = html.unescape(raw).replace('\\u0026', '&')
            if u.startswith('//'):
                u = 'https:' + u
            if u.startswith('https://') and 'webtoon-phinf.pstatic.net' in urlparse(u).netloc:
                candidates.append(u)
    out, seen = [], set()
    for u in candidates:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def choose_indices(n: int, count: int, start_frac: float, end_frac: float):
    if n <= 0:
        return []
    start = max(0, min(n - 1, int(math.floor(n * start_frac))))
    end = max(start + 1, min(n, int(math.ceil(n * end_frac))))
    span = end - start
    count = max(1, min(count, span, MAX_IMAGES))
    if count == 1:
        return [start]
    return sorted(set(round(start + i * (span - 1) / (count - 1)) for i in range(count)))


def make_contact_sheet(paths, out: Path):
    thumbs = []
    for p in paths:
        im = Image.open(p).convert('RGB')
        im.thumbnail((260, 360))
        thumbs.append((p, im.copy()))
    cols = 4
    cell_w, cell_h = 280, 400
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new('RGB', (cols * cell_w, rows * cell_h), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (p, im) in enumerate(thumbs):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        px = x + (cell_w - im.width) // 2
        py = y + 24
        sheet.paste(im, (px, py))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline='black', width=2)
        draw.text((x + 10, y + 6), f"{i+1:02d}  {p.name}", fill='black')
    sheet.save(out, quality=88)


def main():
    if len(sys.argv) != 3:
        raise SystemExit('Usage: collect_webtoon.py source_requests/<id>.json output_dir')
    req_path = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    req = json.loads(req_path.read_text(encoding='utf-8'))
    episode_url = req.get('episode_url', '')
    parsed = urlparse(episode_url)
    if parsed.scheme != 'https' or parsed.netloc not in ALLOWED_HOSTS:
        raise SystemExit('Only public official webtoons.com episode URLs are accepted')

    outdir.mkdir(parents=True, exist_ok=True)
    page = fetch(episode_url).decode('utf-8', errors='ignore')
    urls = extract_image_urls(page)
    if not urls:
        raise SystemExit('No official episode images discovered')

    count = min(int(req.get('max_images', 16)), MAX_IMAGES)
    start_frac = float(req.get('start_fraction', 0.0))
    end_frac = float(req.get('end_fraction', 0.45))
    indices = choose_indices(len(urls), count, start_frac, end_frac)

    files = []
    selected = []
    for seq, idx in enumerate(indices, 1):
        u = urls[idx]
        ext = Path(urlparse(u).path).suffix.lower()
        if ext not in {'.jpg','.jpeg','.png','.webp'}:
            ext = '.jpg'
        p = outdir / f'{seq:02d}-panel-{idx+1:03d}{ext}'
        p.write_bytes(fetch(u, referer=episode_url))
        files.append(p)
        selected.append({
            'sequence': seq,
            'episode_image_index_1_based': idx + 1,
            'file': p.name,
            'url': u,
        })

    make_contact_sheet(files, outdir / 'contact-sheet.jpg')
    manifest = {
        'source_id': req.get('source_id', req_path.stem),
        'episode_url': episode_url,
        'discovered_image_count': len(urls),
        'sample_window': [start_frac, end_frac],
        'selected': selected,
        'notice': 'Public official WEBTOON excerpts collected for transformative review/editing. This does not grant a license; final use remains subject to copyright/platform rules.'
    }
    (outdir / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(outdir)


if __name__ == '__main__':
    main()
