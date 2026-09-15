"""Denoise completed PNGs using Blender's bundled Open Image Denoise library.

C API reference: https://www.openimagedenoise.org/documentation.html
Uses only Python's standard library, the installed OIDN library, and FFmpeg.
"""
import array
import ctypes as C
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'villa_video_clean'
DEST.mkdir(exist_ok=True)
lib = C.CDLL('/home/yudh/bin/blender-5.2.1-linux-x64/lib/libOpenImageDenoise.so')

def bind(name, result, *args):
    fn = getattr(lib, name)
    fn.restype = result
    fn.argtypes = list(args)
    return fn

new_device = bind('oidnNewDevice', C.c_void_p, C.c_int)
commit_device = bind('oidnCommitDevice', None, C.c_void_p)
device_error = bind('oidnGetDeviceError', C.c_int, C.c_void_p, C.POINTER(C.c_char_p))
new_filter = bind('oidnNewFilter', C.c_void_p, C.c_void_p, C.c_char_p)
set_image = bind('oidnSetSharedFilterImage', None, C.c_void_p, C.c_char_p, C.c_void_p, C.c_int,
                 C.c_size_t, C.c_size_t, C.c_size_t, C.c_size_t, C.c_size_t)
set_bool = bind('oidnSetFilterBool', None, C.c_void_p, C.c_char_p, C.c_bool)
commit_filter = bind('oidnCommitFilter', None, C.c_void_p)
execute = bind('oidnExecuteFilter', None, C.c_void_p)
release_filter = bind('oidnReleaseFilter', None, C.c_void_p)
release_device = bind('oidnReleaseDevice', None, C.c_void_p)
device = new_device(1)  # OIDN_DEVICE_TYPE_CPU
commit_device(device)

def check():
    msg = C.c_char_p()
    code = device_error(device, C.byref(msg))
    if code:
        raise RuntimeError(msg.value.decode() if msg.value else f'OIDN error {code}')

check()
filt = new_filter(device, b'RT')
set_bool(filt, b'hdr', False)
set_bool(filt, b'srgb', True)
files = sorted((ROOT / 'villa_video_frames').glob('frame_*.png'))
if '--test' in sys.argv:
    files = files[:1]
try:
    for path in files:
        outpath = DEST / path.name
        if outpath.exists():
            continue
        with path.open('rb') as f:
            f.seek(16)
            w, h = struct.unpack('>II', f.read(8))
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                       '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        assert len(raw) == w*h*3
        source = array.array('f', (v / 255 for v in raw))
        output = array.array('f', [0]) * len(source)
        set_image(filt, b'color', source.buffer_info()[0], 3, w, h, 0, 0, 0)
        set_image(filt, b'output', output.buffer_info()[0], 3, w, h, 0, 0, 0)
        commit_filter(filt)
        check()
        execute(filt)
        check()
        encoded = bytes(max(0, min(255, round(v*255))) for v in output)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
                        '-video_size', f'{w}x{h}', '-i', '-', '-frames:v', '1', '-update', '1',
                        str(outpath)], input=encoded, check=True)
        print('DENOISED', path.name, flush=True)
finally:
    release_filter(filt)
    release_device(device)
