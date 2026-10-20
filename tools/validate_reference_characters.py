"""Import/export integrity checks and rendered pose spot checks for the four new assets."""
import bpy,os,json,struct
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';CHAR=os.path.join(ROOT,'SourceAssets','characters')
ASSETS=[('forsaken_sister','ForsakenSister','Lantern amber glass pane'),('masked_ninja','MaskedNinja','Fitted ninja headcloth'),('broken_oath_knight','BrokenOathKnight','Closed forged great helm'),('ash_scholar','AshScholar','Removable grimoire pages')]
all_reports=[]
for slug,runtime,feature in ASSETS:
 folder=os.path.join(CHAR,slug);path=os.path.join(folder,slug+'.glb')
 with open(path,'rb') as f:
  magic,version,total=struct.unpack('<III',f.read(12));length,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(length))
 assert magic==0x46546C67 and version==2,'Not a GLB 2.0 file'
 names=[n.get('name','') for n in data['nodes']];mesh_nodes=[n for n in data['nodes'] if 'mesh' in n]
 assert any(n.startswith('Eliber | fitted continuous body') for n in names),'Eliber base missing'
 assert any(n.startswith(feature) for n in names),'Distinctive character feature missing'
 assert all('skin' in n for n in mesh_nodes),'Unbound exported mesh'
 assert all(f'grip_index.01.{s}' in names for s in ['L','R']),'Finger skeleton missing'
 assert not any(any(w in n.lower() for w in ['sword','katana','dagger','wand']) for n in names),'Unexpected weapon'
 assert not data.get('cameras') and not data.get('extensions',{}).get('KHR_lights_punctual'),'Studio setup leaked into export'
 animations=[a.get('name','') for a in data.get('animations',[])]
 assert all(any(w in a for a in animations) for w in ['Idle','Walk','Arm_Motion_Test']),animations
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=path)
 rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];assert len(rigs)==1
 meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 points=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
 low=[min(p[i] for p in points) for i in range(3)];high=[max(p[i] for p in points) for i in range(3)]
 assert low[2]>-.10 and 1.6<high[2]<2.5,(slug,low,high)
 for o in meshes:o.data.calc_loop_triangles()
 triangles=sum(len(o.data.loop_triangles) for o in meshes)
 report={'passed':True,'character':slug,'base':'Eliber CC0 fitted mesh','meshes':len(meshes),'triangles':triangles,'bones':len(rigs[0].data.bones),'animations':animations,'embedded_images':len(data.get('images',[])),'bounds_min':low,'bounds_max':high,'studio_excluded':True,'weapons_excluded':True}
 with open(os.path.join(folder,'validation_report.json'),'w') as f:json.dump(report,f,indent=2)
 all_reports.append(report)
 # Use the saved native source for pose spot checks with its authoring studio.
 bpy.ops.wm.open_mainfile(filepath=os.path.join(folder,slug+'.blend'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
 scene.cycles.samples=16;scene.render.resolution_x=650;scene.render.resolution_y=720
 for action_name,frame,file in [('Walk',7,'walk_check.png'),('Arm_Motion_Test',18,'arm_check.png')]:
  action=bpy.data.actions[action_name];rig.animation_data.action=action
  if action.slots:rig.animation_data.action_slot=action.slots[0]
  scene.frame_set(frame);bpy.context.view_layer.update();scene.render.filepath=os.path.join(folder,file);bpy.ops.render.render(write_still=True)
 print('VALIDATED_CHARACTER',json.dumps(report),flush=True)
with open(os.path.join(CHAR,'four_character_validation.json'),'w') as f:json.dump(all_reports,f,indent=2)
print('ALL_FOUR_CHARACTER_CHECKS_PASSED',flush=True)
