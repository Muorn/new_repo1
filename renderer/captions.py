#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,56,&H00FFFFFF,&H000000FF,&H00000000,&H70000000,-1,0,0,0,100,100,0,0,1,5,0,2,145,145,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

MIN_WORDS = 3
TARGET_WORDS = 5
MAX_WORDS = 6
MAX_LINE_CHARS = 24
HIGHLIGHT = "&H0000D7FF&"


def duration_seconds(audio: Path) -> float:
    out = subprocess.check_output([
        'ffprobe','-v','error','-show_entries','format=duration',
        '-of','default=noprint_wrappers=1:nokey=1',str(audio)
    ], text=True).strip()
    return float(out)


def ass_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def phrase_chunks(text: str):
    words = text.replace('\n', ' ').split()
    out, buf = [], []
    for w in words:
        buf.append(w)
        terminal = bool(re.search(r'[.!?]$', w))
        soft_break = bool(re.search(r'[,;:]$', w))
        if terminal and len(buf) >= MIN_WORDS:
            out.append(' '.join(buf))
            buf = []
        elif len(buf) >= MAX_WORDS:
            out.append(' '.join(buf))
            buf = []
        elif soft_break and len(buf) >= TARGET_WORDS:
            out.append(' '.join(buf))
            buf = []
    if buf:
        if out and len(buf) < MIN_WORDS:
            out[-1] += ' ' + ' '.join(buf)
        else:
            out.append(' '.join(buf))
    return out


def split_lines(words):
    text = ' '.join(words)
    if len(text) <= MAX_LINE_CHARS:
        return text
    best = None
    for i in range(1, len(words)):
        left = ' '.join(words[:i])
        right = ' '.join(words[i:])
        score = max(len(left), len(right))
        if len(left) <= MAX_LINE_CHARS and len(right) <= MAX_LINE_CHARS:
            if best is None or score < best[0]:
                best = (score, left, right)
    if best:
        return best[1] + r'\N' + best[2]
    midpoint = max(1, len(words)//2)
    return ' '.join(words[:midpoint]) + r'\N' + ' '.join(words[midpoint:])


def style_caption(text: str) -> str:
    cleaned = text.upper().replace('{', '(').replace('}', ')')
    words = cleaned.split()
    if not words:
        return ''
    # Highlight one anchor word, not every two words.
    candidates = [i for i,w in enumerate(words) if len(re.sub(r'\W','',w)) >= 5]
    idx = candidates[-1] if candidates else len(words)-1
    words[idx] = r'{\c' + HIGHLIGHT + '}' + words[idx] + r'{\c&H00FFFFFF&}'
    return split_lines(words)


def main():
    if len(sys.argv) != 4:
        raise SystemExit('Usage: captions.py script.txt narration.wav subtitles.ass')
    script_path, audio_path, out_path = map(Path, sys.argv[1:])
    text = script_path.read_text(encoding='utf-8').strip()
    total = duration_seconds(audio_path)
    parts = phrase_chunks(text)
    if not parts:
        raise SystemExit('No caption text')

    weights = [max(1, len(p.split())) for p in parts]
    unit = total / sum(weights)
    t = 0.0
    lines = [ASS_HEADER]
    for part, weight in zip(parts, weights):
        dur = unit * weight
        start, end = t, min(total, t + dur)
        shown = style_caption(part)
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{shown}\n")
        t = end
    out_path.write_text(''.join(lines), encoding='utf-8')
    print(out_path)


if __name__ == '__main__':
    main()
