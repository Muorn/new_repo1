#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def probe(path: Path):
    cmd = [
        'ffprobe', '-v', 'error', '-print_format', 'json',
        '-show_format', '-show_streams', str(path)
    ]
    return json.loads(subprocess.check_output(cmd, text=True))


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: qa.py path/to/final.mp4')
    p = Path(sys.argv[1])
    if not p.exists() or p.stat().st_size < 10000:
        raise SystemExit('FAIL: output missing or too small')

    info = probe(p)
    streams = info.get('streams', [])
    video = next((s for s in streams if s.get('codec_type') == 'video'), None)
    if not video:
        raise SystemExit('FAIL: no video stream')

    width, height = int(video.get('width', 0)), int(video.get('height', 0))
    duration = float(info.get('format', {}).get('duration', 0) or 0)
    checks = {
        'exists': True,
        'vertical_1080x1920': width == 1080 and height == 1920,
        'duration_gt_1s': duration > 1,
        'duration_le_60s': duration <= 60,
        'h264_video': video.get('codec_name') == 'h264',
    }
    print(json.dumps({'file': str(p), 'duration': duration, 'width': width, 'height': height, 'checks': checks}, indent=2))
    if not all(checks.values()):
        raise SystemExit('FAIL: one or more QA checks failed')
    print('PASS: technical QA')


if __name__ == '__main__':
    main()
