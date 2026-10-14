#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageStat

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    print('+', ' '.join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        'ffprobe','-v','error','-show_entries','format=duration',
        '-of','default=noprint_wrappers=1:nokey=1',str(path)
    ], text=True).strip()
    return float(out)


def esc_filter_path(p: Path) -> str:
    return str(p).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")


def esc_drawtext(s: str) -> str:
    return (s.replace("'", "’")
             .replace('\\', '\\\\')
             .replace(':', '\\:')
             .replace('%', '\\%'))


def crop_filter(crop_box):
    x0, y0, x1, y1 = [float(v) for v in crop_box]
    w = x1 - x0
    h = y1 - y0
    return (
        f"crop=w='trunc(iw*{w:.6f}/2)*2':h='trunc(ih*{h:.6f}/2)*2':"
        f"x='iw*{x0:.6f}':y='ih*{y0:.6f}'"
    )


def _blank_fraction(values, mode):
    if not values:
        return 0.0
    if mode == 'dark':
        return sum(v <= 14 for v in values) / len(values)
    return sum(v >= 244 for v in values) / len(values)


def tighten_crop_box(img_path: Path, crop_box):
    """Trim only near-uniform black/white gutters from the OUTER edges of a requested crop.

    This intentionally does not try to understand artwork. It only removes rows/columns
    that are overwhelmingly blank so WEBTOON gutters do not become the visual subject.
    """
    try:
        im = Image.open(img_path).convert('L')
        iw, ih = im.size
        x0, y0, x1, y1 = [float(v) for v in crop_box]
        left, top = int(iw*x0), int(ih*y0)
        right, bottom = max(left+2, int(iw*x1)), max(top+2, int(ih*y1))
        region = im.crop((left, top, right, bottom))
        # Keep detection cheap and robust.
        region.thumbnail((500, 900))
        rw, rh = region.size
        px = region.load()

        def row_blank(y):
            vals = [px[x, y] for x in range(rw)]
            return max(_blank_fraction(vals, 'dark'), _blank_fraction(vals, 'light')) >= 0.965

        def col_blank(x):
            vals = [px[x, y] for y in range(rh)]
            return max(_blank_fraction(vals, 'dark'), _blank_fraction(vals, 'light')) >= 0.965

        t, b, l, r = 0, rh-1, 0, rw-1
        while t < rh-1 and row_blank(t):
            t += 1
        while b > t and row_blank(b):
            b -= 1
        while l < rw-1 and col_blank(l):
            l += 1
        while r > l and col_blank(r):
            r -= 1

        # Add a small breathing margin around detected content.
        pad_x = max(2, int(rw * 0.025))
        pad_y = max(2, int(rh * 0.025))
        l, r = max(0, l-pad_x), min(rw-1, r+pad_x)
        t, b = max(0, t-pad_y), min(rh-1, b+pad_y)

        # Refuse pathological trims; semantic crop_box remains the main director.
        keep_w = (r-l+1) / max(1, rw)
        keep_h = (b-t+1) / max(1, rh)
        if keep_w < 0.42 or keep_h < 0.28:
            return crop_box

        base_w, base_h = x1-x0, y1-y0
        nx0 = x0 + base_w * (l / rw)
        nx1 = x0 + base_w * ((r+1) / rw)
        ny0 = y0 + base_h * (t / rh)
        ny1 = y0 + base_h * ((b+1) / rh)
        return [max(0,nx0), max(0,ny0), min(1,nx1), min(1,ny1)]
    except Exception as e:
        print(f'auto-trim skipped for {img_path}: {e}')
        return crop_box


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
        return fill + f",zoompan=z='min(zoom+0.0007,1.06)':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'micro_zoom_out':
        return fill + f",zoompan=z='if(eq(on,1),1.06,max(zoom-0.0007,1.0))':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'zoom_in':
        return fill + f",zoompan=z='min(zoom+0.0013,1.11)':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'zoom_out':
        return fill + f",zoompan=z='if(eq(on,1),1.11,max(zoom-0.0013,1.0))':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'punch_in':
        return fill + f",zoompan=z='min(1+on/{max(frames,1)}*0.13,1.13)':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"
    if motion == 'pan_left':
        return large + ",crop=1080:1920:x='max(0,(iw-1080)*(1-t/{d}))':y='max(0,(ih-1920)*{fy})',fps={fps}".format(d=max(duration,.001), fy=focus_y, fps=FPS)
    if motion == 'pan_right':
        return large + ",crop=1080:1920:x='min(iw-1080,(iw-1080)*(t/{d}))':y='max(0,(ih-1920)*{fy})',fps={fps}".format(d=max(duration,.001), fy=focus_y, fps=FPS)
    if motion == 'pan_up':
        return large + ",crop=1080:1920:x='max(0,(iw-1080)*{fx})':y='max(0,(ih-1920)*(1-t/{d}))',fps={fps}".format(d=max(duration,.001), fx=focus_x, fps=FPS)
    if motion == 'pan_down':
        return large + ",crop=1080:1920:x='max(0,(iw-1080)*{fx})':y='min(ih-1920,(ih-1920)*(t/{d}))',fps={fps}".format(d=max(duration,.001), fx=focus_x, fps=FPS)
    if motion == 'shake':
        return large + ",crop=1080:1920:x='(iw-1080)/2+9*sin(43*t)':y='(ih-1920)/2+7*cos(39*t)',fps={fps}".format(fps=FPS)
    return fill + f",fps={FPS}"


def emphasis_filter(text: str, impact: bool) -> str:
    if not text:
        return ''
    safe = esc_drawtext(text.upper())
    fontsize = 58 if len(text) <= 18 else 46
    alpha = "if(lt(t,0.10),t/0.10,if(lt(t,1.05),1,if(lt(t,1.30),(1.30-t)/0.25,0)))"
    box = "box=1:boxcolor=black@0.48:boxborderw=18"
    draw = (
        f"drawtext=fontfile='{FONT}':text='{safe}':fontsize={fontsize}:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.9:{box}:x=(w-text_w)/2:y=155:alpha='{alpha}'"
    )
    if impact:
        draw += ",eq=contrast=1.05:saturation=1.06"
    return ',' + draw


def framed_filter(crop_box, motion: str, duration: float, fx: float, fy: float, emphasis: str, impact: bool) -> str:
    crop = crop_filter(crop_box)
    pre = (
        f"[0:v]{crop}[src];"
        "[src]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=24[bg2];"
        "[fg]scale=1040:1820:force_original_aspect_ratio=decrease[fg2];"
        "[bg2][fg2]overlay=(W-w)/2:(H-h)/2[comp];"
    )
    chain = motion_filter(motion, duration, fx, fy) + emphasis_filter(emphasis, impact)
    return pre + f"[comp]{chain}[v]"


def render_scene(scene: dict, img: Path, out: Path, duration: float):
    motion = scene.get('motion', 'micro_zoom_in')
    layout = scene.get('layout', 'fill')
    requested = scene.get('crop_box', [0, 0, 1, 1])
    crop_box = tighten_crop_box(img, requested)
    if crop_box != requested:
        print(f'auto-trim {img.name}: {requested} -> {[round(v,4) for v in crop_box]}')
    fx = float(scene.get('focus_x', 0.5))
    fy = float(scene.get('focus_y', 0.5))
    emphasis = scene.get('emphasis', '')
    impact = bool(scene.get('impact', False))

    cmd = ['ffmpeg', '-y', '-loop', '1', '-i', str(img), '-t', f'{duration:.3f}']
    if layout == 'framed':
        fc = framed_filter(crop_box, motion, duration, fx, fy, emphasis, impact)
        cmd += ['-filter_complex', fc, '-map', '[v]']
    else:
        vf = crop_filter(crop_box) + ',' + motion_filter(motion, duration, fx, fy) + emphasis_filter(emphasis, impact)
        cmd += ['-vf', vf]

    cmd += [
        '-r', str(FPS), '-pix_fmt', 'yuv420p',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
        '-an', str(out)
    ]
    run(cmd)


def timed_durations(scenes, narration_duration):
    base = [float(s.get('duration', 2.6)) for s in scenes]
    if not narration_duration:
        return base

    # Align the full visual story to the narration instead of letting -shortest
    # chop off the intended final reveal. Preserve at least ~2.35s for a title reveal.
    target_total = narration_duration + 0.35
    if len(scenes) >= 2 and scenes[-1].get('story_role') == 'title_reveal':
        final_d = min(max(base[-1], 2.35), max(2.35, target_total * 0.11))
        prefix_base = sum(base[:-1])
        prefix_target = max(0.1, target_total - final_d)
        scale = prefix_target / prefix_base
        durations = [d * scale for d in base[:-1]] + [final_d]
        print(f'visual timing: prefix scale={scale:.3f}; title reveal={final_d:.2f}s; target={target_total:.2f}s')
        return durations

    scale = target_total / sum(base)
    print(f'visual timing scale={scale:.3f}; target={target_total:.2f}s')
    return [d * scale for d in base]


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: render.py projects/<id>/project.json')

    cfg_path = Path(sys.argv[1]).resolve()
    root = cfg_path.parent
    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    scenes = cfg.get('scenes', [])
    if not scenes:
        raise SystemExit('project.json must contain at least one scene')

    narration = root / cfg.get('narration_file', 'narration.wav')
    narration_duration = probe_duration(narration) if narration.exists() else None
    durations = timed_durations(scenes, narration_duration)

    work = root / '.render'
    outdir = root / 'output'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    outdir.mkdir(parents=True, exist_ok=True)

    clips = []
    for i, (scene, duration) in enumerate(zip(scenes, durations), start=1):
        src = root / scene['source']
        if not src.exists():
            raise FileNotFoundError(src)
        clip = work / f'{i:03d}.mp4'
        print(f"scene {i:02d}: {scene.get('story_role')} | viewer sees: {scene.get('viewer_should_see')}")
        render_scene(scene, src, clip, duration)
        clips.append(clip)

    concat = work / 'concat.txt'
    concat.write_text('\n'.join(f"file '{c.as_posix()}'" for c in clips), encoding='utf-8')
    picture = work / 'picture.mp4'
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(picture)])

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
