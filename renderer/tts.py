#!/usr/bin/env python3
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin"
MODEL = Path(".models/kokoro-v1.0.onnx")
VOICES = Path(".models/voices-v1.0.bin")
VOICE = "am_fenrir"
BASE_SPEED = 1.03


def ensure(url: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print(f"Downloading {path.name}...")
        urllib.request.urlretrieve(url, path)


def sentence_chunks(text: str):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: tts.py script.txt narration.wav")

    script = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    if not script:
        raise SystemExit("Script is empty")

    ensure(MODEL_URL, MODEL)
    ensure(VOICES_URL, VOICES)

    kokoro = Kokoro(str(MODEL), str(VOICES))
    rendered = []
    sample_rate = None
    try:
        chunks = sentence_chunks(script)
        for i, chunk in enumerate(chunks):
            # Slightly vary pace so the delivery feels spoken rather than read.
            if chunk.endswith('!'):
                speed = 1.07
            elif chunk.endswith('?'):
                speed = 1.01
            elif i == 0:
                speed = 1.05
            else:
                speed = BASE_SPEED
            samples, sr = kokoro.create(
                chunk,
                voice=VOICE,
                speed=speed,
                lang="en-us",
            )
            sample_rate = sr
            rendered.append(np.asarray(samples, dtype=np.float32))
            # Natural micro-pause between sentences; longer after questions.
            pause_ms = 130 if chunk.endswith('?') else 85
            rendered.append(np.zeros(int(sr * pause_ms / 1000.0), dtype=np.float32))

        audio = np.concatenate(rendered) if rendered else np.array([], dtype=np.float32)
        if audio.size == 0:
            raise SystemExit("TTS produced no audio")
        peak = float(np.max(np.abs(audio))) or 1.0
        audio = np.clip(audio * min(0.95 / peak, 1.35), -1.0, 1.0)
        sf.write(str(out), audio, sample_rate, subtype="PCM_16")
    finally:
        try:
            kokoro.voices.close()
        except Exception:
            pass
    print(out)


if __name__ == "__main__":
    main()
