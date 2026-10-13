#!/usr/bin/env python3
import sys
import urllib.request
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin"
MODEL = Path(".models/kokoro-v1.0.onnx")
VOICES = Path(".models/voices-v1.0.bin")


def ensure(url: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print(f"Downloading {path.name}...")
        urllib.request.urlretrieve(url, path)


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
    try:
        samples, sample_rate = kokoro.create(
            script,
            voice="am_michael",
            speed=1.08,
            lang="en-us",
        )
        sf.write(str(out), samples, sample_rate, subtype="PCM_16")
    finally:
        try:
            kokoro.voices.close()
        except Exception:
            pass
    print(out)


if __name__ == "__main__":
    main()
