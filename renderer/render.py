#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30


def run(cmd):
    print('+', ' '.join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def esc_filter_path(p: Path) -> str:
    return str(p).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")


def motion_filter(motion: str, duration: float) -> str:
    frames = max(1, int(round(duration * FPS)))
    base = "scale='if(gt(a,9/16),-2,1080)':'if(gt(a,9/16),1920,-2)',crop=1080:1920"
    pan_base = "scale='if(gt(a,9/16),-2,1200)':'if(gt(a,9/16),2100,-2)'"

    if motion == 'zoom_in':
        return base + f",zoompan=z='min(zoom+0.0015,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'zoom_out':
        return base + f",zoompan=z='if(eq(on,1),1.12,max(zoom-0.0015,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'pan_left':
        return pan_base + ",crop=1080:1920:x='max(0,(iw-1080)*(1-t/{d}))':y='max(0,(ih-1920)/2)',fps={fps}".format(d=max(duration, .001), fps=FPS)
    if motion == 'pan_right':
        return pan_base + ",crop=1080:1920:x='min(iw-1080,(iw-1080)*(t/{d}))':y='max(0,(ih-1920)/2)',fps={fps}".format(d=max(duration, .001), fps=FPS)
    return base + f",fps={FPS}"


def render_scene(img: Path, out: Path, duration: float, motion: str):
    vf = motion_filter(motion, duration)
    run([
        'ffmpeg', '-y', '-loop', '1', '-i', str(img),
        '-t', f'{duration:.3f}', '-vf', vf,
        '-r', str(FPS), '-pix_fmt', 'yuv420p',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
        '-an', str(out)
    ])


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: render.py projects/<id>/project.json')

    cfg_path = Path(sys.argv[1]).resolve()
    root = cfg_path.parent
    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    scenes = cfg.get('scenes', [])
    if not scenes:
        raise SystemExit('project.json must contain at least one scene')

    work = root / '.render'
    outdir = root / 'output'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    outdir.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, scene in enumerate(scenes, start=1):
        src = root / scene['source']
        if not src.exists():
            raise FileNotFoundError(src)
        duration = float(scene.get('duration', 2.5))
        motion = scene.get('motion', 'static')
        clip = work / f'{i:03d}.mp4'
        render_scene(src, clip, duration, motion)
        clips.append(clip)

    concat = work / 'concat.txt'
    concat.write_text('\n'.join(f"file '{c.as_posix()}'" for c in clips), encoding='utf-8')
    picture = work / 'picture.mp4'
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(picture)])

    narration = root / cfg.get('narration_file', 'narration.wav')
    subtitles = root / cfg.get('subtitles_file', 'subtitles.ass')
    final = outdir / cfg.get('output_file', 'final.mp4')

    vf = f"ass='{esc_filter_path(subtitles)}'" if subtitles.exists() else None

    cmd = ['ffmpeg', '-y', '-i', str(picture)]
    if narration.exists():
        cmd += ['-i', str(narration)]
    if vf:
        cmd += ['-vf', vf]
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p']
    if narration.exists():
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-shortest']
    else:
        cmd += ['-an']
    cmd += ['-movflags', '+faststart', str(final)]
    run(cmd)
    print(final)


if __name__ == '__main__':
    main()
