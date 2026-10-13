#!/usr/bin/env python3
import json
import sys
from collections import Counter
from pathlib import Path


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
    facts_ok = all(str(s.get('fact', '')).strip() for s in scenes)
    evidence_ok = all(str(s.get('evidence_ref', '')).strip() for s in scenes)
    total = sum(durations)
    avg = total / len(scenes)
    unique_assets = len(set(assets))
    max_reuse = max(Counter(assets).values()) if assets else 0
    callout_ratio = sum(bool(s.get('emphasis')) for s in scenes) / len(scenes)
    fill_ratio = sum(s.get('layout', 'fill') == 'fill' for s in scenes) / len(scenes)
    intro_ok = bool(scenes[0].get('emphasis')) and durations[0] <= 2.4

    checks = {
        'all_scenes_have_fact': facts_ok,
        'all_scenes_have_evidence_ref': evidence_ok,
        'intro_present': intro_ok,
        'authored_avg_between_1_7_and_2_7s': 1.7 <= avg <= 2.7,
        'no_authored_scene_over_3_2s': all(d <= 3.2 for d in durations),
        'enough_visual_beats': len(scenes) >= 16 if total >= 30 else len(scenes) >= 5,
        'no_single_asset_dominates': max_reuse <= max(3, int(len(scenes) * 0.25 + 0.999)),
        'callouts_not_overused': callout_ratio <= 0.35,
        'mostly_full_screen': fill_ratio >= 0.75,
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
        'checks': checks,
    }
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit('FAIL: V3 creative QA gate')
    print('PASS: V3 creative QA')


if __name__ == '__main__':
    main()
