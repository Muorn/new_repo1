#!/usr/bin/env python3
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_RIGHTS = {"owned", "licensed", "official_promotional", "official_public_excerpt", "creator_authorized", "open_license", "public_domain"}
ALLOWED_SCHEMES = {"https"}
MAX_ASSET_BYTES = 20 * 1024 * 1024
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".ppm"}
ALLOWED_MOTIONS = {
    "static", "micro_zoom_in", "micro_zoom_out", "zoom_in", "zoom_out",
    "punch_in", "pan_left", "pan_right", "pan_up", "pan_down", "shake"
}
ALLOWED_LAYOUTS = {"fill", "framed"}


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "short"


def download(url: str, dest: Path):
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Only HTTPS assets are permitted: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "GPT-Manhwa-Shorts/4.0", "Referer": "https://www.webtoons.com/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        length = int(r.headers.get("Content-Length") or 0)
        if length and length > MAX_ASSET_BYTES:
            raise ValueError(f"Asset too large: {url}")
        data = r.read(MAX_ASSET_BYTES + 1)
    if len(data) > MAX_ASSET_BYTES:
        raise ValueError(f"Asset too large: {url}")
    dest.write_bytes(data)


def clamp01(value, default=0.5):
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def validate_crop_box(value, scene_no: int):
    if not isinstance(value, list) or len(value) != 4:
        raise SystemExit(f"Scene {scene_no} must include crop_box=[x0,y0,x1,y1] in V4")
    try:
        x0, y0, x1, y1 = [float(v) for v in value]
    except (TypeError, ValueError):
        raise SystemExit(f"Scene {scene_no} crop_box values must be numeric")
    vals = [x0, y0, x1, y1]
    if any(v < 0 or v > 1 for v in vals):
        raise SystemExit(f"Scene {scene_no} crop_box must use normalized 0..1 coordinates")
    if x1 - x0 < 0.12 or y1 - y0 < 0.12:
        raise SystemExit(f"Scene {scene_no} crop_box is too small")
    return [x0, y0, x1, y1]


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
    asset_meta = {}
    for idx, asset in enumerate(job.get("assets", []), 1):
        rights = asset.get("rights_basis")
        if rights not in ALLOWED_RIGHTS:
            raise SystemExit(f"Asset {idx} rejected: invalid rights_basis={rights!r}")

        url = asset.get("url")
        local_path = asset.get("local_path")
        if bool(url) == bool(local_path):
            raise SystemExit(f"Asset {idx} must provide exactly one of url or local_path")

        if local_path:
            src = Path(local_path).resolve()
            repo = Path.cwd().resolve()
            if repo not in src.parents and src != repo:
                raise SystemExit(f"Asset {idx} local_path escapes repository")
            if not src.exists():
                raise SystemExit(f"Asset {idx} local_path not found: {local_path}")
            ext = src.suffix.lower()
            if ext not in ALLOWED_EXTS:
                raise SystemExit(f"Asset {idx} extension not allowed: {ext}")
            local = source / f"{idx:03d}{ext}"
            shutil.copyfile(src, local)
        else:
            ext = Path(urlparse(url).path).suffix.lower()
            if ext not in ALLOWED_EXTS:
                ext = ".jpg"
            local = source / f"{idx:03d}{ext}"
            download(url, local)

        aid = asset.get("id", f"asset-{idx}")
        asset_map[aid] = local.relative_to(project).as_posix()
        asset_meta[aid] = {
            "rights_basis": rights,
            "source_label": asset.get("source_label", ""),
            "source_url": asset.get("source_url", url or ""),
        }

    scenes = []
    for i, scene in enumerate(job["scenes"], 1):
        asset_id = scene.get("asset_id")
        if asset_id not in asset_map:
            raise SystemExit(f"Scene {i} references unavailable asset_id {asset_id!r}")
        motion = scene.get("motion", "micro_zoom_in")
        if motion not in ALLOWED_MOTIONS:
            raise SystemExit(f"Scene {i} rejected: unsupported motion {motion!r}")
        layout = scene.get("layout", "fill")
        if layout not in ALLOWED_LAYOUTS:
            raise SystemExit(f"Scene {i} rejected: unsupported layout {layout!r}")
        duration = float(scene.get("duration", 2.6))
        if duration <= 0 or duration > 8:
            raise SystemExit(f"Scene {i} rejected: duration must be >0 and <=8s")
        fact = str(scene.get("fact", "")).strip()
        evidence_ref = str(scene.get("evidence_ref", "")).strip()
        viewer_should_see = str(scene.get("viewer_should_see", "")).strip()
        story_role = str(scene.get("story_role", "")).strip()
        if not fact or not evidence_ref:
            raise SystemExit(f"Scene {i} must include fact and evidence_ref in V4")
        if not viewer_should_see:
            raise SystemExit(f"Scene {i} must state viewer_should_see in V4")
        if not story_role:
            raise SystemExit(f"Scene {i} must state story_role in V4")
        crop_box = validate_crop_box(scene.get("crop_box"), i)

        scenes.append({
            "source": asset_map[asset_id],
            "asset_id": asset_id,
            "duration": duration,
            "motion": motion,
            "layout": layout,
            "crop_box": crop_box,
            "caption": scene.get("caption", ""),
            "fact": fact,
            "evidence_ref": evidence_ref,
            "viewer_should_see": viewer_should_see,
            "story_role": story_role,
            "focus_x": clamp01(scene.get("focus_x", 0.5)),
            "focus_y": clamp01(scene.get("focus_y", 0.5)),
            "emphasis": str(scene.get("emphasis", "")).strip()[:40],
            "impact": bool(scene.get("impact", False)),
            "asset_meta": asset_meta[asset_id],
        })

    total = sum(s["duration"] for s in scenes)
    avg = total / len(scenes)
    if total >= 35 and len(scenes) < 14:
        raise SystemExit("V4 quality gate: >=35s videos require at least 14 meaningful visual beats")
    if avg > 3.1:
        raise SystemExit(f"V4 quality gate: average authored scene duration {avg:.2f}s exceeds 3.1s")

    project_json = {
        "video_id": video_id,
        "series": job["series"],
        "youtube_title": job.get("youtube_title", ""),
        "description": job.get("description", ""),
        "narration_file": "narration.wav",
        "subtitles_file": "subtitles.ass",
        "output_file": "final.mp4",
        "renderer_version": 4,
        "tts_voice": job.get("tts_voice", "am_puck"),
        "tts_speed": float(job.get("tts_speed", 1.0)),
        "scenes": scenes,
    }
    (project / "script.txt").write_text(job["script"].strip() + "\n", encoding="utf-8")
    (project / "project.json").write_text(json.dumps(project_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (project / "job.snapshot.json").write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(project.as_posix())


if __name__ == "__main__":
    main()
