# Animation and video on this Blender installation

## Budget the render before committing to a sequence

Load the existing `.blend` for a camera tour instead of rebuilding the geometry. Preview the start, middle, and end camera positions to catch clipping, obstructed views, and abrupt framing changes.

Benchmark the first frame **and a subsequent frame** with the intended engine, resolution, and scene. Startup and shader compilation made the first frame slower. In the villa scene, EEVEE at 1280 × 720 and 8 samples took roughly 38 seconds initially and 20 seconds per subsequent frame. These are observations for that scene, not a machine-wide performance guarantee. Even EEVEE can take a long time here.

Estimate total time from the number of native renders before promising a delivery format. Try a representative lower-cost preview rather than repeatedly launching long full-quality tests. Switching from Cycles to EEVEE changes lighting and transparency; inspect the result.

## Camera and scene state

- Animate the actual camera for a native 3D tour. A path with eased progress and a moving look target worked well; quaternion rotations made the look direction straightforward. Save the camera keys in the delivered `.blend`.
- Set frame range, frame rate, render percentage, and active camera explicitly. Restore the intended starting frame before saving the project.
- Keep a full-rate camera animation even if rendering selected frames as a performance compromise. Save the chosen Frame Step so the project records how the source sequence was produced.

## Resume safely

Render numbered PNGs before encoding an MP4. This preserves completed work if the render process stops.

Some long jobs ended with exit code 143; the cause was not established. Batches of six missing frames subsequently completed successfully. Treat that batch size as a useful starting point, not a fixed timeout rule. Resume only after the prior process has ended; repeated failures at the same frame call for diagnosis rather than endless retries.

Before skipping an existing frame, verify that it decodes and has the expected dimensions. Prefer rendering to a temporary filename and renaming it after success so interruptions cannot leave a partial file that looks complete. Keep a manifest of camera/scene version and render settings, or use a new output directory when they change. Refresh denoised frames too; existence alone does not establish that cached output is current.

## Native frame rate versus interpolation

Prefer native frames when the user's quality requirements and available render time allow them. Motion interpolation is an optional speed tradeoff for a slow camera move through a static scene; explain the choice when adopting it. It can distort foliage, reflections, and newly revealed surfaces. It is unsuitable as a silent replacement for an explicit request to render every frame.

The delivered villa example used an eight-second timeline at 24 fps, rendering frames 1, 7, …, 187: **32 native images at 4 fps**, interpolated to **192 video frames at 24 fps**. The output frame rate must not be presented as the native render rate.

FFmpeg and ffprobe were installed at `/usr/bin/ffmpeg` and `/usr/bin/ffprobe`. Check availability before relying on them. For a selected-frame sequence:

- Set the input rate to the actual source rate: timeline fps divided by Frame Step.
- Ensure filenames sort chronologically and the input contains only the expected images. A glob with stale extra frames silently changes the timing.
- FFmpeg's `minterpolate` worked for generating intermediate motion. Padding the last image before interpolation and trimming afterward preserved the requested duration.
- H.264 with `yuv420p` and `+faststart` produced a broadly playable MP4. Add audio or decorative titles only when the task calls for them.

## Denoising and delivery checks

Low-sample EEVEE left noticeable noise in the villa interiors. The compositor denoising attempt did not visibly resolve it. Blender also bundles `lib/libOpenImageDenoise.so`; calling that library separately barely changed the tested frame. Do not add a custom denoising pipeline just because the library is available. Compare output before retaining an extra pass; temporal filtering may reduce noise but can soften moving detail.

Validate the encoded artifact with ffprobe: dimensions, duration, codec, frame rate, and frame count. Decode the whole file with `ffmpeg -v error -i output.mp4 -f null -` to catch corrupt frames. Inspect samples across the clip, including interpolated moments, and playback when available; a contact sheet establishes framing but does not prove smooth motion. Deliver the MP4 and editable animation project, retaining source scripts for reproduction.
