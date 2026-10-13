# GPT Manhwa Shorts Renderer

V1 of a free, GPT-directed manhwa/manga Shorts production pipeline.

## Goal

Input a structured project (`project.json`, source images, narration script) and automatically produce a vertical 1080x1920 MP4 using Kokoro TTS + FFmpeg.

GPT is the creative director. FFmpeg is the deterministic editor. The user only reviews the finished video and returns PASS or FAIL.

## Pipeline

1. GPT creates `project.json` + `script.txt`.
2. Kokoro TTS generates `narration.wav` when one is not supplied.
3. `renderer/render.py` creates animated vertical scene clips.
4. FFmpeg concatenates scenes, mixes narration, and optionally burns ASS captions.
5. `renderer/qa.py` validates the output.
6. GitHub Actions uploads the MP4 as an Actions artifact.
7. Optional Drive upload is enabled when Drive credentials are configured.

## Project layout

```text
projects/<video-id>/
├── project.json
├── script.txt
├── subtitles.ass        # optional
├── narration.wav        # generated automatically if absent
├── source/
│   ├── 001.jpg
│   └── 002.jpg
└── output/
    └── final.mp4
```

## Supported motion presets

- `static`
- `zoom_in`
- `zoom_out`
- `pan_left`
- `pan_right`

## Local render

Requirements: Python 3.11/3.12 and FFmpeg.

```bash
python renderer/render.py projects/demo/project.json
python renderer/qa.py projects/demo/output/final.mp4
```

If `narration.wav` is missing, generate it first:

```bash
kokoro-tts projects/demo/script.txt projects/demo/narration.wav --speed 1.08 --lang en-us --voice am_michael
```

## GitHub Actions

Run **Actions → Render Short → Run workflow** and supply the project path, such as `projects/demo`.

The workflow installs FFmpeg and Kokoro TTS, generates narration when needed, renders the Short, runs QA, and uploads the finished MP4 as an Actions artifact.

## Google Drive

The user's Drive workspace is named `Manhwa YouTube`. The intended output destination is `03_Ready for Review`.

Direct GitHub Actions → Drive upload is scaffolded but deliberately disabled until a Drive credential is stored as a GitHub secret. No credential is committed to this repository.

## V1 principle

No manual editing. The only human gate is the final PASS/FAIL review.
