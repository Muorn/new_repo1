#!/usr/bin/env python3
import json
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
DEFAULT_VOICE = "am_puck"
DEFAULT_SPEED = 1.0


def ensure(url: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print(f"Downloading {path.name}...")
        urllib.request.urlretrieve(url, path)


def sentence_chunks(text: str):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def load_project_settings(script_path: Path):
    project_json = script_path.parent / "project.json"
    if not project_json.exists():
        return DEFAULT_VOICE, DEFAULT_SPEED
    cfg = json.loads(project_json.read_text(encoding="utf-8"))
    return str(cfg.get("tts_voice", DEFAULT_VOICE)), float(cfg.get("tts_speed", DEFAULT_SPEED))


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: tts.py script.txt narration.wav")

    script_path = Path(sys.argv[1])
    script = script_path.read_text(encoding="utf-8").strip()
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    if not script:
        raise SystemExit("Script is empty")

    voice, base_speed = load_project_settings(script_path)
    print(f"TTS voice={voice}; base_speed={base_speed:.2f}")

    ensure(MODEL_URL, MODEL)
    ensure(VOICES_URL, VOICES)

    kokoro = Kokoro(str(MODEL), str(VOICES))
    rendered = []
    sample_rate = None
    try:
        chunks = sentence_chunks(script)
        for i, chunk in enumerate(chunks):
            # Keep the delivery energetic without racing. Hooks/reveals get a
            # little more momentum; questions slow down slightly for emphasis.
            if chunk.endswith('!'):
                speed = base_speed * 1.035
            elif chunk.endswith('?'):
                speed = base_speed * 0.97
            elif i == 0:
                speed = base_speed * 1.02
            elif any(token in chunk.lower() for token in ["then the clock", "people start screaming", "here's the crazy part"]):
                speed = base_speed * 1.015
            else:
                speed = base_speed

            samples, sr = kokoro.create(
                chunk,
                voice=voice,
                speed=speed,
                lang="en-us",
            )
            sample_rate = sr
            rendered.append(np.asarray(samples, dtype=np.float32))

            if chunk.endswith('?'):
                pause_ms = 180
            elif i == 0:
                pause_ms = 115
            else:
                pause_ms = 105
            rendered.append(np.zeros(int(sr * pause_ms / 1000.0), dtype=np.float32))

        audio = np.concatenate(rendered) if rendered else np.array([], dtype=np.float32)
        if audio.size == 0:
            raise SystemExit("TTS produced no audio")
        peak = float(np.max(np.abs(audio))) or 1.0
        audio = np.clip(audio * min(0.95 / peak, 1.30), -1.0, 1.0)
        sf.write(str(out), audio, sample_rate, subtype="PCM_16")
    finally:
        try:
            kokoro.voices.close()
        except Exception:
            pass
    print(out)


if __name__ == "__main__":
    main()
