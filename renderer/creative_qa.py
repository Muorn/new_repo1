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

    checks = {
        'all_scenes_have_fact': facts_ok,
        'all_scenes_have_evidence_ref': evidence_ok,
        'avg_scene_le_3s': avg <= 3.0,
        'no_scene_over_3_5s': all(d <= 3.5 for d in durations),
        'enough_visual_beats': len(scenes) >= 10 if total >= 30 else len(scenes) >= 4,
        'no_single_asset_dominates': max_reuse <= max(4, int(len(scenes) * 0.35 + 0.999)),
        'callouts_not_overused': callout_ratio <= 0.45,
    }
    result = {
        'renderer_version': cfg.get('renderer_version'),
        'scene_count': len(scenes),
        'total_duration': round(total, 2),
        'average_scene_duration': round(avg, 2),
        'unique_assets': unique_assets,
        'max_asset_reuse': max_reuse,
        'callout_ratio': round(callout_ratio, 2),
        'checks': checks,
    }
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit('FAIL: V2 creative QA gate')
    print('PASS: V2 creative QA')


if __name__ == '__main__':
    main()
