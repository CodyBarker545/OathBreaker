import bpy, json
from pathlib import Path
out=Path(r'D:\SoftwareEng\Game\artifacts\assassin_face_reference')
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
editor=scene.sequence_editor_create()
strip=editor.strips.new_movie('Face reference',r'F:\pictures\2023-06-25-120122505.mp4',channel=1,frame_start=1)
element=strip.elements[0]
scene.render.resolution_x=element.orig_width
scene.render.resolution_y=element.orig_height
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG'
scene.render.image_settings.quality=92
scene.render.use_sequencer=True
frames=[round(1+(strip.frame_final_duration-1)*i/11) for i in range(12)]
(out/'video_info.json').write_text(json.dumps({'width':element.orig_width,'height':element.orig_height,'frames':strip.frame_final_duration,'samples':frames},indent=2))
for index,frame in enumerate(frames):
    scene.frame_set(frame)
    scene.render.filepath=str(out/f'frame_{index:02d}.jpg')
    bpy.ops.render.render(write_still=True)
