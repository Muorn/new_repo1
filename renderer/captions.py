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
Style: Default,Arial,62,&H00FFFFFF,&H000000FF,&H00000000,&H70000000,-1,0,0,0,100,100,0,0,1,5,0,2,130,130,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

MAX_WORDS_PER_CAPTION = 2
MAX_CHARS_PER_LINE = 18
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


def chunks(text: str, max_words: int = MAX_WORDS_PER_CAPTION):
    words = text.replace('\n', ' ').split()
    out, buf = [], []
    for w in words:
        buf.append(w)
        if len(buf) >= max_words or re.search(r'[.!?]$', w):
            out.append(' '.join(buf))
            buf = []
    if buf:
        out.append(' '.join(buf))
    return out


def style_caption(text: str) -> str:
    cleaned = text.upper().replace('{', '(').replace('}', ')')
    words = cleaned.split()
    if not words:
        return ''
    words[-1] = r'{\c' + HIGHLIGHT + '}' + words[-1] + r'{\c&H00FFFFFF&}'
    shown = ' '.join(words)
    if len(shown) <= MAX_CHARS_PER_LINE:
        return shown
    return r'\N'.join(words)


def main():
    if len(sys.argv) != 4:
        raise SystemExit('Usage: captions.py script.txt narration.wav subtitles.ass')
    script_path, audio_path, out_path = map(Path, sys.argv[1:])
    text = script_path.read_text(encoding='utf-8').strip()
    total = duration_seconds(audio_path)
    parts = chunks(text)
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
