# Modern Balinese villa

## Revised scene

- `modern_balinese_villa_v2.png` — 2400 × 1600 overview.
- `modern_balinese_villa_v2_poolside.png` — 2000 × 1400 poolside view.
- `modern_balinese_villa_v2.blend` — editable scene with both cameras.
- `scene_v2.py` — self-contained scene generator and renderer.

The revised design combines a slate-roofed living pavilion, flat-roofed bedroom wings, a teak dining pergola, travertine terraces, and a Sukabumi-stone swimming pool. Materials, furniture, and tropical planting are generated procedurally; no external textures or models are required.

## Render

```bash
/home/yudh/bin/blender-5.2.1-linux-x64/blender --background --python scene_v2.py
```

The script renders both views with Cycles, 128 samples, adaptive sampling, and denoising. It saves the Blender file with the overview camera active. Outputs are written beside the script.

The original `scene.py`, `modern_balinese_villa.blend`, and `modern_balinese_villa.png` are retained for comparison.

## Video tour

`modern_balinese_villa_tour.mp4` is an eight-second, 1280 × 720 H.264 video at 24 fps. It moves from a wide poolside view toward the living pavilion. The editable camera animation is in `modern_balinese_villa_animation.blend`.

```bash
/home/yudh/bin/blender-5.2.1-linux-x64/blender --background --python animate_villa.py
python3 encode_villa_video.py
```

The animation script loads `modern_balinese_villa_v2.blend` and saves 32 native EEVEE frames in `villa_video_frames/`. The encoder runs `denoise_villa_video.py` using Blender's bundled Open Image Denoise library, then uses the installed FFmpeg to reduce temporal noise, interpolate camera motion to 24 fps, and add short fades. Cleaned frames are kept in `villa_video_clean/`. It checks resolution, duration, codec, and frame count. This uses fewer native renders to suit this machine's CPU rendering performance; the saved Blender project retains camera keys at every frame for a full native 24 fps render if desired (set Frame Step to 1).

Interrupted rendering resumes from existing frames. For a changed camera or lighting setup, move the previous frame directory aside before rendering a new sequence.

For environments that interrupt long jobs, append `-- --batch 6` to the Blender command and repeat it until all 32 source frames exist. Each invocation renders at most six missing frames. When changing the source sequence, also move `villa_video_clean/` aside so denoising is refreshed.
