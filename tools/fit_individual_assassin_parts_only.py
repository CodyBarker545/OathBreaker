"""Fresh supplied GLB + original individual parts. Object fitting only."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('D:/SoftwareEng/Game');SRC=ROOT/'SourceAssets/characters/hooded_assassin'
OUT=SRC/'prototype_individual_parts_v003';OUT.mkdir(exist_ok=True)
targets=json.loads((ROOT/'artifacts/individual_piece_fit_targets.json').read_text())
basepath=ROOT/'SourceAssets/characters/_base/Meshy_AI_Human_Base_Male_All_Animations.glb'
hashes={str(basepath):hashlib.sha256(basepath.read_bytes()).hexdigest()}
scene=bpy.data.scenes.new('Assassin_Individual_Parts_On_Original_GLB');bpy.context.window.scene=scene
groups={}
for n in ['Base_Unmodified','Armor','Cloth','Rig_Helpers','Review_Studio']:
 c=bpy.data.collections.new('Individual_'+n);scene.collection.children.link(c);groups[n]=c
def put(o,key):
 for c in list(o.users_collection):c.objects.unlink(o)
 groups[key].objects.link(o)
def load_glb(p):
 hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p))
 return list(set(bpy.data.objects)-before)
loaded=load_glb(basepath);rig=next(o for o in loaded if o.type=='ARMATURE')
body=next(o for o in loaded if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
rig.name='Original_GLB_Rig';body.name='Original_GLB_Body'
for o in loaded:
 put(o,'Base_Unmodified' if o in [rig,body] else 'Rig_Helpers')
 if o not in [rig,body]:o.hide_render=True;o.hide_set(True)
# Keep original action/NLA state and all bone/skin/texture data. Rest is a display mode only.
rig.data.pose_position='REST'
for act in bpy.data.actions:act.use_fake_user=True
bpy.context.view_layer.update()
def fingerprint():
 return hashlib.sha256(repr(([tuple(v.co) for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons],[[tuple(d.uv) for d in l.data] for l in body.data.uv_layers],[[tuple((g.group,g.weight) for g in v.groups)] for v in body.data.vertices],[(b.name,tuple(b.head_local),tuple(b.tail_local),b.parent.name if b.parent else None) for b in rig.data.bones],[m.name for m in body.data.materials])).encode()).hexdigest()
before=fingerprint();manifest=[]
def bounds(obs):
 pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
 return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
def fit(obs,lo,hi):
 bpy.context.view_layer.update();a,b=bounds(obs);lo=Vector(lo);hi=Vector(hi)
 s=tuple((hi[i]-lo[i])/max(1e-6,b[i]-a[i]) for i in range(3))
 M=Matrix.Translation(lo)@Matrix.Diagonal((*s,1))@Matrix.Translation(-a)
 for o in obs:o.matrix_world=M@o.matrix_world
def attach(o,bone):
 # Reversible object constraint; no base rig edits or added weights.
 mw=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;o.matrix_world=mw
 o['fit_method']='Object translation, rotation, scale and rigid bone parenting only'
def add(fn,label,key,bone,target=None,matrix=None):
 p=SRC/'orignal_models'/fn;objects=load_glb(p);meshes=[o for o in objects if o.type=='MESH']
 for i,o in enumerate(meshes):
  mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw;o.name=label+('' if i==0 else '_'+str(i));put(o,key)
  o['original_file']=str(p)
  if matrix is not None:o.matrix_world=Matrix(matrix)
 if target:fit(meshes,*target)
 for o in meshes:
  if bone:attach(o,bone)
  manifest.append({'object':o.name,'source':str(p),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'materials':[m.name for m in o.data.materials if m],'uv_layers':len(o.data.uv_layers),'attachment':bone,'modifiers_added':0})
 for o in objects:
  if o not in meshes:put(o,'Rig_Helpers');o.hide_render=True;o.hide_set(True)
 return meshes

for name,filename,key,bone in [
 ('GLB_Armor_Chest_Meshy','Meshy_AI_Strapped_Leather_Ches_1020234350_generate.glb','Armor','mixamorig:Spine2'),
 ('GLB_Waist_Belts_And_Tattered_Panels','Meshy_AI_Crimson_Tattered_Mant_1021005734_generate.glb','Cloth','mixamorig:Hips'),
 ('GLB_Scarf_And_Back_Mantle','Meshy_AI_crimson_assassin_scar_1021004838_generate.glb','Cloth','mixamorig:Spine2'),
 ('GLB_Hood_Meshy_Original','Meshy_AI_Crimson_Hood_1021005559_generate.glb','Cloth','mixamorig:Head')]:
 target=targets[name]['bounds'];add(filename,name.replace('GLB_','Individual_'),key,bone,target=target)

for sign,label,side in [(1,'L','Left'),(-1,'R','Right')]:
 center=rig.matrix_world@rig.data.bones['mixamorig:'+side+'Leg'].tail_local
 add('Meshy_AI__1021003710_model-edit.glb','Individual_Boot_Greave.'+label,'Armor','mixamorig:'+side+'Leg',target=((center.x-.082,-.188,-.005),(center.x+.082,.120,.484)))
 knee=rig.matrix_world@rig.data.bones['mixamorig:'+side+'Leg'].head_local
 add('Meshy_AI_assassin_knee_guard_b_1021010856_generate.glb','Individual_Knee.'+label,'Armor','mixamorig:'+side+'Leg',target=((knee.x-.087,-.100,.410),(knee.x+.087,.078,.637)))
 add('Meshy_AI_Bronze_Vanguard_Brace_1020235333_generate.glb','Individual_Bracer.'+label,'Armor','mixamorig:'+side+'ForeArm',matrix=targets['GLB_Armor_Bracer.'+label]['matrix'])

# Individually saved Meshy pauldron, geometry/textures retained exactly as supplied in v003.
p=ROOT/'artifacts/meshy_left_pauldron/iterations/v003/Meshy_Left_Pauldron_v003_game_5k.blend'
hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
with bpy.data.libraries.load(str(p),link=False) as(a,b):b.objects=['Meshy_Left_Pauldron_v003_Game_5k']
pauldron=b.objects[0];pauldron.parent=None;put(pauldron,'Armor');pauldron.name='Individual_Meshy_Pauldron.L'
pauldron.matrix_world=Matrix(targets['GLB_Armor_Meshy_Pauldron.L']['matrix']);attach(pauldron,'mixamorig:LeftShoulder')
other=pauldron.copy();other.name='Individual_Meshy_Pauldron.R';other.parent=None;put(other,'Armor')
other.matrix_world=Matrix(targets['GLB_Armor_Meshy_Pauldron.R']['matrix']);attach(other,'mixamorig:RightShoulder')
for o in [pauldron,other]:manifest.append({'object':o.name,'source':str(p),'triangles':len(o.data.polygons),'materials':[m.name for m in o.data.materials if m],'attachment':o.parent_bone})

assert fingerprint()==before,'Base data unexpectedly modified'
scene.world=bpy.data.worlds.new('Individual_Fit_Studio_World');scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.12,.14,.17,1);bg.inputs[1].default_value=.4
for name,loc,power,size in [('Key',(3,-4,5),450,4),('Fill',(-3,-2,3),250,3),('Rim',(1,3,4),450,3)]:
 data=bpy.data.lights.new('IndividualFit_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 o=bpy.data.objects.new(data.name,data);groups['Review_Studio'].objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Individual_Fit_Camera');cam=bpy.data.objects.new('Individual_Fit_Camera',cd);groups['Review_Studio'].objects.link(cam);scene.camera=cam
cd.type='ORTHO';cd.ortho_scale=2.04;cam.location=(3,-6,2.4);cam.rotation_euler=(Vector((0,.015,.88))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
report={'base_source':str(basepath),'base_fingerprint_before':before,'base_fingerprint_after':fingerprint(),'base_geometry_uvs_weights_materials_and_rest_bones_unchanged':True,'base_active_action':rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None,'display':'Original rest pose, rig pose_position REST; animation clips and NLA state retained','parts':manifest,'borrowed_prototype_sleeves_gloves_hair_mask_trousers_weapons_added':False,'geometry_simplification_applied':False,'source_files':hashes,'credits_spent':0,'notes':['Original individual GLB materials retained; most supplied armor/cloth files have no color textures','No base-body masking, material edits, reweighting, topology changes, or rig regeneration','Rigid attachments are provisional; cloth is not newly skinned']}
with (OUT/'assembly_manifest.json').open('w') as f:json.dump(report,f,indent=2)
for path,digest in hashes.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Assassin_Individual_Parts_v003_working.blend'),compress=True)
print('Individual pieces assembled',len(manifest),'base verified unchanged; imported original action',report['base_active_action'])
