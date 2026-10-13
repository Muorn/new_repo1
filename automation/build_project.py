#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_RIGHTS = {"owned", "licensed", "official_promotional", "creator_authorized"}
ALLOWED_SCHEMES = {"https"}
MAX_ASSET_BYTES = 20 * 1024 * 1024


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "short"


def download(url: str, dest: Path):
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Only HTTPS assets are permitted: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "GPT-Manhwa-Shorts/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        length = int(r.headers.get("Content-Length") or 0)
        if length and length > MAX_ASSET_BYTES:
            raise ValueError(f"Asset too large: {url}")
        data = r.read(MAX_ASSET_BYTES + 1)
    if len(data) > MAX_ASSET_BYTES:
        raise ValueError(f"Asset too large: {url}")
    dest.write_bytes(data)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_project.py jobs/<job>.json")

    job_path = Path(sys.argv[1]).resolve()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    required = ["video_id", "series", "script", "scenes"]
    missing = [k for k in required if not job.get(k)]
    if missing:
        raise SystemExit(f"Missing required job fields: {', '.join(missing)}")

    video_id = slugify(str(job["video_id"]))
    project = Path("projects") / video_id
    source = project / "source"
    source.mkdir(parents=True, exist_ok=True)

    asset_map = {}
    for idx, asset in enumerate(job.get("assets", []), 1):
        rights = asset.get("rights_basis")
        if rights not in ALLOWED_RIGHTS:
            raise SystemExit(f"Asset {idx} rejected: invalid rights_basis={rights!r}")
        url = asset.get("url")
        if not url:
            raise SystemExit(f"Asset {idx} has no URL")
        ext = Path(urlparse(url).path).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        local = source / f"{idx:03d}{ext}"
        download(url, local)
        asset_map[asset.get("id", f"asset-{idx}")] = local.relative_to(project).as_posix()

    scenes = []
    for i, scene in enumerate(job["scenes"], 1):
        asset_id = scene.get("asset_id")
        if asset_id not in asset_map:
            raise SystemExit(f"Scene {i} references unavailable asset_id {asset_id!r}")
        scenes.append({
            "source": asset_map[asset_id],
            "duration": float(scene.get("duration", 2.5)),
            "motion": scene.get("motion", "zoom_in"),
            "caption": scene.get("caption", ""),
        })

    project_json = {
        "video_id": video_id,
        "series": job["series"],
        "youtube_title": job.get("youtube_title", ""),
        "description": job.get("description", ""),
        "narration_file": "narration.wav",
        "subtitles_file": "subtitles.ass",
        "output_file": "final.mp4",
        "scenes": scenes,
    }
    (project / "script.txt").write_text(job["script"].strip() + "\n", encoding="utf-8")
    (project / "project.json").write_text(json.dumps(project_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (project / "job.snapshot.json").write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(project.as_posix())


if __name__ == "__main__":
    main()
