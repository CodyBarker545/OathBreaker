"""Fit existing outfit to supplied rigged GLB; source geometry and files preserved."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
ROOT=Path('D:/SoftwareEng/Game');OUT=ROOT/'SourceAssets/characters/hooded_assassin/prototype_glb_base_v002';OUT.mkdir(exist_ok=True)
basefile=ROOT/'SourceAssets/characters/_base/Meshy_AI_Human_Base_Male_All_Animations.glb'
sourcefile=ROOT/'SourceAssets/characters/hooded_assassin/prototype_assembly_v001/Hooded_Assassin_Prototype_v001_assembled.blend'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [basefile,sourcefile]}
scene=bpy.context.scene;scene.name='Assassin_Prototype_Rigged_GLB_Base_v002'
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.name='Assassin_Supplied_GLB_Rig'
body=next(o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));body.name='Assassin_Supplied_GLB_Body'
cols={}
for key in ['Body','Clothing','Armor','Weapons','Accessories','Rig']:
 col=bpy.data.collections.new('GLB_Assassin_'+key);scene.collection.children.link(col);cols[key]=col
studio=bpy.data.collections.new('GLB_Prototype_Studio');scene.collection.children.link(studio)
def put(o,key):
 for c in list(o.users_collection):c.objects.unlink(o)
 cols[key].objects.link(o)
put(rig,'Rig');put(body,'Body')
for o in list(scene.objects):
 if o.type=='MESH' and o!=body:
  put(o,'Rig');o.hide_render=True;o.hide_set(True);o['role']='Imported rig display helper; not character geometry'
rest={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}

srcscene=bpy.data.scenes['Pawns_of_Divinity_Assassin_Prototype_v001'];oldrig=next(o for o in srcscene.objects if o.type=='ARMATURE')
oldpose=oldrig.data.pose_position
bpy.context.window.scene=srcscene;oldrig.data.pose_position='REST';bpy.context.view_layer.update()
sources=[(o,o.matrix_world.copy()) for o in srcscene.objects if o.type=='MESH' and not any('Assassin_Body' in o.name or 'Assassin_Eyes' in o.name for _ in [0])]
oldrig.data.pose_position=oldpose;bpy.context.view_layer.update();bpy.context.window.scene=scene

bonemap={'Root':'mixamorig:Hips','pelvis':'mixamorig:Hips','spine_01':'mixamorig:Spine','spine_02':'mixamorig:Spine1','spine_03':'mixamorig:Spine2','neck_01':'mixamorig:Neck','head':'mixamorig:Head'}
for short,full in [('l','Left'),('r','Right')]:
 for a,b in [('clavicle','Shoulder'),('upperarm','Arm'),('lowerarm','ForeArm'),('hand','Hand'),('thigh','UpLeg'),('calf','Leg'),('foot','Foot'),('ball','ToeBase')]:bonemap[a+'_'+short]='mixamorig:'+full+b

def limb_transform(oldbone):
 a=oldrig.data.bones[oldbone];b=rig.data.bones[bonemap[oldbone]]
 p=oldrig.matrix_world@a.head_local;q=rig.matrix_world@b.head_local
 av=oldrig.matrix_world.to_3x3()@(a.tail_local-a.head_local);bv=rig.matrix_world.to_3x3()@(b.tail_local-b.head_local)
 rot=av.rotation_difference(bv).to_matrix().to_4x4()
 # Modest uniform fitting preserves armor details and source orientation.
 scale=max(.84,min(1.05,bv.length/av.length))
 return Matrix.Translation(q)@rot@Matrix.Diagonal((scale,scale,scale,1))@Matrix.Translation(-p)
globalfit=Matrix.Translation((.003,.036,0))@Matrix.Diagonal((.92,.94,1.7/1.8,1))
kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index)
kd.balance()
def bind_cloth(o):
 for g in list(o.vertex_groups):o.vertex_groups.remove(g)
 groups={n:o.vertex_groups.new(name=n) for n in rig.data.bones.keys()}
 for v in o.data.vertices:
  _,idx,_=kd.find(o.matrix_world@v.co)
  weights=[(body.vertex_groups[g.group].name,g.weight) for g in body.data.vertices[idx].groups if body.vertex_groups[g.group].name in groups and g.weight>1e-5]
  total=sum(w for n,w in weights)
  if not total:weights=[('mixamorig:Spine2',1)];total=1
  for n,w in weights:groups[n].add([v.index],w/total,'REPLACE')
 world=o.matrix_world.copy();o.parent=rig;o.matrix_world=world
 mod=o.modifiers.new('Provisional weights from supplied GLB body','ARMATURE');mod.object=rig
 o['attachment']='Nearest source GLB body weights; provisional'
def rigid(o,bone):
 world=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;o.matrix_world=world
 o['attachment']='Rigid supplied GLB bone: '+bone

clones=[]
for src,world in sources:
 category=next((c.name.replace('Assassin_','') for c in src.users_collection if c.name.startswith('Assassin_')),'Accessories')
 flexible=src.name.startswith(('Tunic_','Trousers_'))
 o=src.copy();o.data=src.data.copy() if flexible else src.data;o.name='GLB_'+src.name
 o.parent=None;o.matrix_world=world;o.animation_data_clear()
 for mod in list(o.modifiers):
  if mod.type=='ARMATURE':o.modifiers.remove(mod)
 put(o,category if category in cols else 'Accessories')
 label='l' if src.name.endswith('.L') else 'r' if src.name.endswith('.R') else None
 if label and any(t in src.name for t in ['Sleeve','Bracer','Glove']):
  limb=('upperarm_' if 'Upper_Sleeve' in src.name else 'hand_' if 'Glove' in src.name else 'lowerarm_')+label
  M=limb_transform(limb)
 elif label and 'Boot_Greave' in src.name:
  # Recenter boots on supplied ankle/leg; keep detailed toe geometry intact.
  a=oldrig.data.bones['calf_'+label];b=rig.data.bones[bonemap['calf_'+label]]
  center=oldrig.matrix_world@a.tail_local;target=rig.matrix_world@b.tail_local
  M=Matrix.Translation(target)@Matrix.Diagonal((.92,.94,.90,1))@Matrix.Translation(-center)
 elif label and 'Knee' in src.name:
  center=oldrig.matrix_world@oldrig.data.bones['calf_'+label].head_local;target=rig.matrix_world@rig.data.bones[bonemap['calf_'+label]].head_local
  M=Matrix.Translation(target)@Matrix.Diagonal((.90,.94,.96,1))@Matrix.Translation(-center)
 elif label and 'Trousers' in src.name:
  M=limb_transform('thigh_'+label)
 else:M=globalfit
 o.matrix_world=M@world
 if flexible:bind_cloth(o)
 else:
  oldbone=src.parent_bone if src.parent_type=='BONE' else 'spine_03'
  rigid(o,bonemap.get(oldbone,'mixamorig:Spine2'))
 o['prototype_source']=str(sourcefile);clones.append(o)

# Neutral fitting pose: source rest retained; arms lowered slightly for the review.
for sign,side in [(1,'Left'),(-1,'Right')]:
 p=rig.pose.bones['mixamorig:'+side+'Arm'];head=p.head.copy()
 p.matrix=Matrix.Translation(head)@Matrix.Rotation(sign*math.radians(25),4,'Y')@Matrix.Translation(-head)@p.matrix
bpy.context.view_layer.update()

# Preserve source clips in their existing muted NLA tracks and as fake-user actions.
for act in bpy.data.actions:act.use_fake_user=True
rig['preview_note']='Neutral A-pose. Walking and Running actions retained; NLA tracks muted for fitting.'
rig['source_glb']=str(basefile)
scene.world=srcscene.world.copy() if srcscene.world else None
for src in srcscene.objects:
 if src.type in {'CAMERA','LIGHT'}:
  o=src.copy();o.data=src.data.copy();studio.objects.link(o)
  if src==srcscene.camera:scene.camera=o
cam=scene.camera;center=Vector((0,.015,.89));cam.location=(3,-6,2.5);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.05
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for n,digest in hashes.items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==digest
with (OUT/'source_integrity.json').open('w') as f:json.dump(hashes,f,indent=2)
with (OUT/'rig_rest_preserved.json').open('w') as f:json.dump(rest,f,indent=2)
with (OUT/'assembly_manifest.json').open('w') as f:json.dump({'base':str(basefile),'base_triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'bones':len(rig.data.bones),'animations':[a.name for a in bpy.data.actions],'fitted_objects':[{'name':o.name,'source':o.get('assembly_source'),'attachment':o.get('attachment'),'materials':[m.name for m in o.data.materials if m]} for o in clones],'notes':['No source mesh replacement; existing detailed armor retained','Clothing weights newly transferred only on copies','Rig rest geometry, original body weights, textures and clips preserved']},f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hooded_Assassin_GLB_Base_v002_working.blend'),compress=True)
print('Fitted',len(clones),'existing parts to',rig.name,'with',len(rig.data.bones),'bones; clips preserved.')
