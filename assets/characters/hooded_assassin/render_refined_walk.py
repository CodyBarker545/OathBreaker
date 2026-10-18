import bpy, os
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'blendswap_assassin')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'assassin_refined.blend'),use_scripts=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data.action=bpy.data.actions['Walk']
scene=bpy.context.scene
scene.render.resolution_x=480; scene.render.resolution_y=540; scene.cycles.samples=8
scene.camera.data.ortho_scale=2.75
folder=os.path.join(ROOT,'refined_walk_frames'); os.makedirs(folder,exist_ok=True)
for frame in range(1,25,2):
    scene.frame_set(frame)
    scene.render.filepath=os.path.join(folder,'%04d.png'%frame)
    bpy.ops.render.render(write_still=True)
print('REFINED WALK RENDER COMPLETE')
