---
name: blender-local
description: Build, edit, and render native 3D scenes with the locally installed Blender at /home/yudh/bin/blender-5.2.1-linux-x64/blender. Use for scripted Blender modeling, scene generation, lighting, still renders, and camera animations on this machine.
---

# Local Blender

## Run the installed binary

Use `/home/yudh/bin/blender-5.2.1-linux-x64/blender` (observed version: **5.2.1 LTS**). It is already installed; no download or separate Python `bpy` package is needed. Run scripts with Blender's embedded Python:

```bash
/home/yudh/bin/blender-5.2.1-linux-x64/blender --background --python scene.py
```

Follow the project's shell conventions. Where RTK is required, use `rtk proxy` before this command to preserve Blender's output. If RTK is unavailable, report that briefly and use the binary directly.

Write scripts and outputs in the authorized project directory. Use `os.path.dirname(os.path.abspath(__file__))` for output paths so results do not depend on the shell's working directory. Keep the `.py`, editable `.blend`, and rendered images together.

## Render workflow

1. Build the requested scene in native Blender geometry. Prefer procedural materials or pack any external assets into the `.blend`.
2. Render a small preview first; inspect the actual image for framing, light, material scale, intersections, and reflections. A successful command alone does not establish visual quality.
3. Refine the scene, then render at delivery resolution. Useful starting points: Cycles with denoising, 32–64 samples for previews, and 128 samples with `adaptive_threshold = 0.025` for final images. Tune these to the scene and available time.
4. Set `scene.camera`, `scene.render.filepath`, and `scene.render.resolution_percentage` explicitly. A forgotten preview percentage silently reduces final image dimensions.
5. Save with `bpy.ops.wm.save_as_mainfile(filepath=...)` and render with `bpy.ops.render.render(write_still=True)`. For multiple views, restore the intended default camera and render settings before the final save.
6. Inspect the final image and verify file existence and dimensions. Deliver clickable image, `.blend`, and script links.

Long renders can be quiet for minutes. Poll the existing process rather than starting duplicate renders; communicate progress without inventing a percentage.

For video or camera tours, read [Animation and video](references/animation.md) before choosing the frame count and render settings. It covers measured performance, resumable rendering, interpolation tradeoffs, and MP4 validation.

## Lessons from this installation

- **Sky API changed:** `ShaderNodeTexSky.sky_type = 'NISHITA'` raised an enum error here. Reported values were `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING`, `PREETHAM`, and `HOSEK_WILKIE`. `HOSEK_WILKIE` with `sun_direction` worked. For unfamiliar properties, inspect this binary's RNA rather than assuming an older tutorial matches it.
- **Material sockets:** this build accepted Principled BSDF inputs `Transmission Weight`, `Subsurface Weight`, `Emission Color`, and `Emission Strength`. `use_nodes = True` worked but emitted a Blender 6.0 deprecation warning; that warning did not prevent rendering.
- **Exit status can mislead:** Blender returned exit code 0 after a Python traceback during scene construction. Read the output for tracebacks and confirm fresh artifacts before claiming completion.
- **Thumbnail cache failure:** saving could report an OpenImageIO error under `/home/yudh/.cache/thumbnails/large/` while the project and render still saved correctly. Verify the requested files; do not expand filesystem permissions merely to repair an incidental thumbnail.
- **Headless EEVEE:** `BLENDER_EEVEE` rendered successfully despite repeated `EGL_BAD_MATCH` messages. Check whether frames actually finish before treating those messages as fatal. Cycles device discovery reported only an Intel i5-12400 CPU in this session; recheck available devices when performance matters, and do not assume EEVEE has accelerated GPU access.
- **Compositor API:** this build exposed `scene.compositing_node_group` and `NodeGroupOutput`; `CompositorNodeComposite` was absent. A compositor group with an Image output socket could be assigned, but the attempted denoising setup left visible noise. Verify its effect on a rendered image rather than treating accepted node creation as proof that denoising worked.
- **Headless teardown hang:** some completed renders hung during PulseAudio cleanup (`pa_write() failed`). If this recurs in a dedicated background script, an observed workaround is `print(..., flush=True); os._exit(0)` **only after all renders and saves have succeeded**. Do not use it by default, in interactive Blender, or to hide an exception; it bypasses cleanup.

## Efficient geometry and visual checks

- Thousands of repeated `bpy.ops` calls were much slower than direct data creation. For repeated parts, use `bpy.data.meshes.new`, `mesh.from_pydata`, and linked objects; batch leaves or grass into meshes. Reserve operators for cases where their convenience justifies the overhead.
- Keep mesh vertices local to their intended origin when objects need rotation. Applying furniture rotations to meshes with world-space vertices rotates them around the wrong point.
- Avoid overlapping coplanar surfaces: duplicate steps, ground slabs, and pool coping produced black patches. Build continuous ground with a pool opening and fit adjacent pieces without overlapping top faces.
- Actual pool depth, a tiled basin, transmission, IOR 1.333, and restrained ripple bump gave better water than a shallow colored plane.
- Architecture improved more through varied building volumes, a lower camera, layered planting, and material detail than through sample count alone. Use individual curved leaves and varied palm crowns instead of smooth ellipsoids for visible trees.
- Keep vegetation and roof detail proportional to the camera distance. Save expensive final renders until the composition passes inspection.
