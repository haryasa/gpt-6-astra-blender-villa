"""Encode the rendered villa camera move as a browser-friendly H.264 MP4."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
frames = root / 'villa_video_frames'
expected = [frames / f'frame_{n:04d}.png' for n in range(1, 193, 6)]
missing = [p.name for p in expected if not p.is_file()]
if missing:
    raise SystemExit(f'Render the missing frames first: {missing}')
if set(frames.glob('frame_*.png')) != set(expected):
    raise SystemExit('The frame directory contains unexpected frame numbers; use a clean sequence.')
ffmpeg = shutil.which('ffmpeg')
ffprobe = shutil.which('ffprobe')
if not ffmpeg or not ffprobe:
    raise SystemExit('ffmpeg and ffprobe must be installed.')
subprocess.run([sys.executable, str(root / 'denoise_villa_video.py')], check=True)
clean_frames = root / 'villa_video_clean'

output = root / 'modern_balinese_villa_tour.mp4'
filters = (
    'hqdn3d=3:2.25:4.5:3.375,'
    'tpad=stop_mode=clone:stop_duration=1,'
    'minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,'
    'trim=duration=8,'
    'fade=t=in:st=0:d=0.25,fade=t=out:st=7.7:d=0.3'
)
subprocess.run([
    ffmpeg, '-hide_banner', '-loglevel', 'warning', '-y',
    '-framerate', '4', '-pattern_type', 'glob', '-i', str(clean_frames / 'frame_*.png'),
    '-vf', filters, '-an', '-c:v', 'libx264', '-preset', 'medium',
    '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output),
], check=True)
probe = json.loads(subprocess.check_output([
    ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output),
]))
video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
assert (video['width'], video['height']) == (1280, 720), video
assert video['codec_name'] == 'h264', video
assert video['r_frame_rate'] == '24/1', video
assert int(video['nb_frames']) == 192, video
assert abs(float(probe['format']['duration']) - 8) < .05, probe['format']
subprocess.run([
    ffmpeg, '-hide_banner', '-loglevel', 'warning', '-y', '-ss', '3.5',
    '-i', str(output), '-frames:v', '1', '-update', '1',
    str(root / 'modern_balinese_villa_tour_poster.png'),
], check=True)
print(f'Validated: {output.name} / 8 seconds / 1280 x 720 / H.264 / 24 fps / 192 frames')
