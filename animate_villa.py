"""Render an eight-second native Blender camera move; encode the PNGs separately."""
import bpy
import math
import os
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'modern_balinese_villa_v2.blend'))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 192
scene.frame_step = 6
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.compression = 15
scene.render.film_transparent = False
scene.render.use_file_extension = True
if hasattr(scene, 'eevee'):
    ee = scene.eevee
    print('EEVEE SETTINGS', [p.identifier for p in ee.bl_rna.properties], flush=True)
    if hasattr(ee, 'taa_render_samples'):
        ee.taa_render_samples = 8
    if hasattr(ee, 'use_raytracing'):
        ee.use_raytracing = True

# Image denoising keeps the CPU preview renderer useful for an animation.
# Blender 5.2 uses a compositor node group with a group output.
scene.use_nodes = True
comp = bpy.data.node_groups.new('Video image denoising', 'CompositorNodeTree')
comp.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
layers = comp.nodes.new('CompositorNodeRLayers')
denoise = comp.nodes.new('CompositorNodeDenoise')
output = comp.nodes.new('NodeGroupOutput')
comp.links.new(layers.outputs['Image'], denoise.inputs['Image'])
comp.links.new(denoise.outputs['Image'], output.inputs['Image'])
scene.compositing_node_group = comp
scene.render.use_compositing = True

camera = scene.camera
camera.name = 'Camera • animated villa highlight'
camera.animation_data_clear()
camera.data.animation_data_clear()
camera.data.type = 'PERSP'
camera.data.clip_end = 300
camera.data.dof.use_dof = False
camera.rotation_mode = 'QUATERNION'

# Bake each frame, including look direction, for a repeatable gentle orbit/dolly.
for frame in range(1, 193):
    t = (frame - 1) / 191
    t = t * t * (3 - 2 * t)
    start = Vector((16.2, -26.5, 8.2))
    control = Vector((10.0, -23.0, 6.2))
    end = Vector((4.6, -18.0, 4.4))
    camera.location = (1-t)**2 * start + 2*(1-t)*t*control + t*t*end
    target = Vector((-.2 - .8*t, 2.5 + 1.0*t, 2.45 - .15*t))
    camera.rotation_quaternion = (target-camera.location).to_track_quat('-Z', 'Y')
    camera.data.lens = 37 + t
    camera.keyframe_insert(data_path='location', frame=frame)
    camera.keyframe_insert(data_path='rotation_quaternion', frame=frame)
    camera.data.keyframe_insert(data_path='lens', frame=frame)

scene.frame_set(1)
scene.render.filepath = str(ROOT / 'villa_video_frames' / 'frame_')
scene['Video'] = '8 seconds / 24 fps / 1280 x 720 / native camera; render every sixth frame and motion-interpolate for the delivery video'

if '--preview' in sys.argv:
    for frame in [1, 192]:
        scene.frame_set(frame)
        scene.render.filepath = str(ROOT / f'villa_video_preview_{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'PREVIEW COMPLETE {frame}', flush=True)
else:
    (ROOT / 'villa_video_frames').mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'modern_balinese_villa_animation.blend'))
    limit = int(sys.argv[sys.argv.index('--batch') + 1]) if '--batch' in sys.argv else 192
    completed = 0
    for frame in range(1, 193, 6):
        target = ROOT / 'villa_video_frames' / f'frame_{frame:04d}.png'
        if target.exists():
            continue
        scene.frame_set(frame)
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        print(f'VIDEO FRAME {frame}/192 COMPLETE', flush=True)
        completed += 1
        if completed >= limit:
            break
    print(f'RENDER BATCH COMPLETE: {completed} new source frames', flush=True)

# This installation has hung during PulseAudio teardown after successful rendering.
sys.stdout.flush()
os._exit(0)
