#!/usr/bin/env python3
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    print('+', ' '.join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def esc_filter_path(p: Path) -> str:
    return str(p).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")


def esc_drawtext(s: str) -> str:
    return (s.replace('\\', '\\\\')
             .replace(':', '\\:')
             .replace("'", "\\'")
             .replace('%', '\\%'))


def focus_expr(axis: str, focus: float) -> str:
    dim = 'iw' if axis == 'x' else 'ih'
    return f"max(0,min({dim}-{dim}/zoom,{dim}*{focus:.4f}-{dim}/(2*zoom)))"


def motion_filter(motion: str, duration: float, focus_x=0.5, focus_y=0.5) -> str:
    frames = max(1, int(round(duration * FPS)))
    fill = "scale='if(gt(a,9/16),-2,1080)':'if(gt(a,9/16),1920,-2)',crop=1080:1920"
    large = "scale='if(gt(a,9/16),-2,1240)':'if(gt(a,9/16),2180,-2)'"
    x = focus_expr('x', focus_x)
    y = focus_expr('y', focus_y)

    if motion == 'micro_zoom_in':
        return fill + f",zoompan=z='min(zoom+0.0007,1.055)':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'micro_zoom_out':
        return fill + f",zoompan=z='if(eq(on,1),1.055,max(zoom-0.0007,1.0))':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'zoom_in':
        return fill + f",zoompan=z='min(zoom+0.0018,1.13)':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'zoom_out':
        return fill + f",zoompan=z='if(eq(on,1),1.13,max(zoom-0.0018,1.0))':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'punch_in':
        return fill + f",zoompan=z='min(1+on/{max(frames,1)}*0.18,1.18)':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'pan_left':
        return large + ",crop=1080:1920:x='max(0,(iw-1080)*(1-t/{d}))':y='max(0,(ih-1920)*{fy})',fps={fps}".format(d=max(duration,.001), fy=focus_y, fps=FPS)
    if motion == 'pan_right':
        return large + ",crop=1080:1920:x='min(iw-1080,(iw-1080)*(t/{d}))':y='max(0,(ih-1920)*{fy})',fps={fps}".format(d=max(duration,.001), fy=focus_y, fps=FPS)
    if motion == 'pan_up':
        return large + ",crop=1080:1920:x='max(0,(iw-1080)*{fx})':y='max(0,(ih-1920)*(1-t/{d}))',fps={fps}".format(d=max(duration,.001), fx=focus_x, fps=FPS)
    if motion == 'pan_down':
        return large + ",crop=1080:1920:x='max(0,(iw-1080)*{fx})':y='min(ih-1920,(ih-1920)*(t/{d}))',fps={fps}".format(d=max(duration,.001), fx=focus_x, fps=FPS)
    if motion == 'shake':
        # Intentionally subtle: roughly +/- 12 px for a brief impact feel.
        return large + ",crop=1080:1920:x='(iw-1080)/2+12*sin(55*t)':y='(ih-1920)/2+10*cos(47*t)',fps={fps}".format(fps=FPS)
    return fill + f",fps={FPS}"


def emphasis_filter(text: str, impact: bool) -> str:
    if not text:
        return ''
    safe = esc_drawtext(text.upper())
    fontsize = 64 if len(text) <= 18 else 52
    # Top-safe callout keeps narration captions free at the lower third.
    alpha = "if(lt(t,0.12),t/0.12,if(lt(t,0.9),1,if(lt(t,1.15),(1.15-t)/0.25,0)))"
    box = "box=1:boxcolor=black@0.58:boxborderw=22"
    draw = (
        f"drawtext=fontfile='{FONT}':text='{safe}':fontsize={fontsize}:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.9:{box}:x=(w-text_w)/2:y=185:alpha='{alpha}'"
    )
    if impact:
        draw += ",eq=contrast=1.06:saturation=1.08"
    return ',' + draw


def render_scene(scene: dict, img: Path, out: Path):
    duration = float(scene.get('duration', 2.2))
    motion = scene.get('motion', 'micro_zoom_in')
    fx = float(scene.get('focus_x', 0.5))
    fy = float(scene.get('focus_y', 0.5))
    vf = motion_filter(motion, duration, fx, fy)
    vf += emphasis_filter(scene.get('emphasis', ''), bool(scene.get('impact', False)))
    run([
        'ffmpeg', '-y', '-loop', '1', '-i', str(img),
        '-t', f'{duration:.3f}', '-vf', vf,
        '-r', str(FPS), '-pix_fmt', 'yuv420p',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
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
        clip = work / f'{i:03d}.mp4'
        render_scene(scene, src, clip)
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
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p']
    if narration.exists():
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-shortest']
    else:
        cmd += ['-an']
    cmd += ['-movflags', '+faststart', str(final)]
    run(cmd)
    print(final)


if __name__ == '__main__':
    main()
