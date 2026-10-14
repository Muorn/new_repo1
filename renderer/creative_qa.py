#!/usr/bin/env python3
import json
import sys
from collections import Counter
from pathlib import Path


def crop_area(scene):
    box = scene.get('crop_box') or [0, 0, 1, 1]
    try:
        x0, y0, x1, y1 = [float(v) for v in box]
        return max(0.0, x1 - x0) * max(0.0, y1 - y0)
    except Exception:
        return 1.0


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: creative_qa.py projects/<id>/project.json')
    p = Path(sys.argv[1])
    cfg = json.loads(p.read_text(encoding='utf-8'))
    scenes = cfg.get('scenes', [])
    if not scenes:
        raise SystemExit('FAIL: no scenes')

    durations = [float(s.get('duration', 0)) for s in scenes]
    assets = [s.get('asset_id') for s in scenes]
    total = sum(durations)
    avg = total / len(scenes)
    unique_assets = len(set(assets))
    max_reuse = max(Counter(assets).values()) if assets else 0
    callout_ratio = sum(bool(s.get('emphasis')) for s in scenes) / len(scenes)
    fill_ratio = sum(s.get('layout', 'fill') == 'fill' for s in scenes) / len(scenes)
    crop_areas = [crop_area(s) for s in scenes]

    checks = {
        'all_scenes_have_fact': all(str(s.get('fact', '')).strip() for s in scenes),
        'all_scenes_have_evidence_ref': all(str(s.get('evidence_ref', '')).strip() for s in scenes),
        'all_scenes_have_viewer_intent': all(str(s.get('viewer_should_see', '')).strip() for s in scenes),
        'all_scenes_have_story_role': all(str(s.get('story_role', '')).strip() for s in scenes),
        'all_scenes_have_semantic_crop': all(isinstance(s.get('crop_box'), list) and len(s.get('crop_box')) == 4 for s in scenes),
        'no_whole_webtoon_slice_used': all(a <= 0.80 for a in crop_areas),
        'intro_is_visual_not_blank': bool(scenes[0].get('emphasis')) and scenes[0].get('layout', 'fill') == 'fill',
        'authored_avg_between_2_1_and_3_1s': 2.1 <= avg <= 3.1,
        'no_authored_scene_over_3_4s': all(d <= 3.4 for d in durations),
        'enough_visual_beats': len(scenes) >= 14 if total >= 35 else len(scenes) >= 5,
        'no_single_asset_dominates': max_reuse <= max(3, int(len(scenes) * 0.25 + 0.999)),
        'callouts_not_overused': callout_ratio <= 0.32,
        'mostly_full_screen': fill_ratio >= 0.85,
    }
    result = {
        'renderer_version': cfg.get('renderer_version'),
        'scene_count': len(scenes),
        'authored_total_duration': round(total, 2),
        'authored_average_scene_duration': round(avg, 2),
        'unique_assets': unique_assets,
        'max_asset_reuse': max_reuse,
        'callout_ratio': round(callout_ratio, 2),
        'fill_ratio': round(fill_ratio, 2),
        'average_crop_area': round(sum(crop_areas) / len(crop_areas), 3),
        'checks': checks,
    }
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit('FAIL: V4 creative QA gate')
    print('PASS: V4 creative QA')


if __name__ == '__main__':
    main()
