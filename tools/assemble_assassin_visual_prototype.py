"""MCP assembly of existing assets only. No replacement mesh authoring or API generation."""
import bpy, json, math, os, hashlib, struct
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
ROOT=Path('D:/SoftwareEng/Game')
SRC=ROOT/'SourceAssets/characters/hooded_assassin'
OUT=SRC/'prototype_assembly_v001';OUT.mkdir(exist_ok=True)
scene=bpy.data.scenes.new('Pawns_of_Divinity_Assassin_Prototype_v001');bpy.context.window.scene=scene
collections={}
for short in ['Body','Clothing','Armor','Weapons','Accessories','Rig']:
 c=bpy.data.collections.new('Assassin_'+short);scene.collection.children.link(c);collections[short]=c
studio=bpy.data.collections.new('Prototype_Review_Studio');scene.collection.children.link(studio)
used=[];source_hashes={}
def track(path):
 path=Path(path)
 if str(path) not in source_hashes:source_hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 return str(path)
def append(path,names):
 path=track(path)
 with bpy.data.libraries.load(path,link=False) as(a,b):b.objects=[n for n in names if n in a.objects]
 return [o for o in b.objects if o]
def put(ob,category,source):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 collections[category].objects.link(ob)
 ob['assembly_source']=str(source);used.append(ob)
 return ob
def duplicate(src,name,category,path):
 ob=src.copy();ob.data=src.data.copy();ob.name=name
 mw=src.matrix_world.copy();ob.parent=None;ob.matrix_world=mw
 for m in list(ob.modifiers):
  if m.type=='ARMATURE':ob.modifiers.remove(m)
 ob.animation_data_clear();put(ob,category,path)
 return ob

# Primary body and original MPFB rig, appended without touching any source file.
basepath=SRC/'base/assassin_base.blend'
base=append(basepath,['Assassin_Body','Assassin_Skeleton','Assassin_Eyes'])
rig=next(o for o in base if o.type=='ARMATURE');rig.name='Assassin_Prototype_MPFB_Rig';put(rig,'Rig',basepath)
rig.animation_data_clear()
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
body=next(o for o in base if o.type=='MESH' and 'Body' in o.name);eyes=next(o for o in base if o.type=='MESH' and 'Eyes' in o.name)
for ob in [body,eyes]:
 ob.name='Prototype_'+ob.name;put(ob,'Body',basepath)
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
rig_snapshot={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}

def rawbounds(obs):
 pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
 lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
 return lo,hi
def fit(obs,lo,hi,rotation=None):
 if rotation:
  for o in obs:o.matrix_world=rotation@o.matrix_world
 bpy.context.view_layer.update();a,b=rawbounds(obs);lo=Vector(lo);hi=Vector(hi)
 sc=Vector(tuple((hi[i]-lo[i])/max(1e-6,b[i]-a[i]) for i in range(3)))
 M=Matrix.Translation(lo)@Matrix.Diagonal((*sc,1))@Matrix.Translation(-a)
 for o in obs:o.matrix_world=M@o.matrix_world
 bpy.context.view_layer.update()
def rigid(ob,bone):
 world=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=bone;ob.matrix_world=world
 ob['attachment']='Rigid bone parent: '+bone
def smooth_weights(ob):
 # Transfer nearest existing MPFB deform weights to an appended clothing copy.
 if not hasattr(smooth_weights,'kd'):
  kd=KDTree(len(body.data.vertices))
  for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index)
  kd.balance();smooth_weights.kd=kd
 for g in list(ob.vertex_groups):ob.vertex_groups.remove(g)
 groups={n:ob.vertex_groups.new(name=n) for n in rig.data.bones.keys()}
 for v in ob.data.vertices:
  _,idx,_=smooth_weights.kd.find(ob.matrix_world@v.co)
  weights=[(body.vertex_groups[g.group].name,g.weight) for g in body.data.vertices[idx].groups if body.vertex_groups[g.group].name in groups and g.weight>1e-5]
  total=sum(w for n,w in weights)
  if not total:weights=[('spine_03',1)];total=1
  for n,w in weights:groups[n].add([v.index],w/total,'REPLACE')
 world=ob.matrix_world.copy();ob.parent=rig;ob.matrix_world=world
 mod=ob.modifiers.new('Prototype MPFB weight transfer','ARMATURE');mod.object=rig
 ob['attachment']='Nearest MPFB body deform weights; provisional, requires weight painting'

# Reuse existing garments; exclude donor body/face and obsolete shoulder pieces.
donorpath=SRC/'blendswap_assassin/backups/before_unhooded_hair/assassin_refined.blend'
track(donorpath)
donors=[o for o in bpy.data.scenes['Assassin_Prototype_Assembly_Inspection'].objects if o.type=='MESH']
torso=next(o for o in donors if o.name.startswith('Continuous fitted leather torso'))
cloth=duplicate(torso,'Tunic_Leather_Inner','Clothing',donorpath)
fit([cloth],(-.208,-.147,.925),(.208,.123,1.490));smooth_weights(cloth)
for sign,label,old in [(1,'L','R'),(-1,'R','L')]:
 for prefix,name,lo,hi in [
  ('Padded thigh.','Trousers_Thigh',(.033,-.108,.520),(.234,.100,.976)),
  ('Quilted leather sleeve.','Tunic_Upper_Sleeve',(.205,-.085,1.389),(.466,.073,1.548)),
  ('Soft glove wrist cuff.','Glove_Cuff',(.702,-.052,1.424),(.756,.028,1.509)),
  ('Fingerless glove','Fingerless_Glove',(.731,-.058,1.427),(.832,-.029,1.510))]:
  src=next(o for o in donors if o.name.startswith(prefix) and o.name.endswith('.'+old))
  ob=duplicate(src,name+'.'+label,'Clothing',donorpath)
  lo=Vector(lo);hi=Vector(hi)
  if sign<0:lo.x,hi.x=-hi.x,-lo.x
  fit([ob],lo,hi)
  if 'Glove' in name:rigid(ob,'hand_'+label.lower())
  else:smooth_weights(ob)

# Existing lower-arm sleeves and daggers from the older complete prototype.
animated=SRC/'animated_prototype/assassin_animated.blend'
with bpy.data.libraries.load(track(animated),link=False) as(a,b):
 b.objects=[n for n in a.objects if n.startswith('Forearm sleeve.') or any(t in n.lower() for t in ['dagger','grip wrap'])]
weapon_sources=[o for o in b.objects if o and o.type=='MESH']
for sign,label,old in [(1,'L','R'),(-1,'R','L')]:
 sleeves=[o for o in weapon_sources if o.name.startswith('Forearm sleeve.') and o.name.endswith('.'+old)]
 for src in sleeves:
  ob=duplicate(src,'Tunic_Forearm_Sleeve.'+label,'Clothing',animated)
  x0,x1=(.442,.724) if sign>0 else(-.724,-.442)
  fit([ob],(x0,-.070,1.405),(x1,.047,1.530));smooth_weights(ob)
 blades=[o for o in weapon_sources if not o.name.startswith('Forearm') and ('.'+old in o.name)]
 obs=[duplicate(o,'Weapon_'+o.name.replace('.'+old,'.'+label),'Weapons',animated) for o in blades]
 if obs:
  # Prototype belt-mounted display avoids inventing a closed hand grip.
  x0,x1=(.206,.326) if sign>0 else(-.326,-.206)
  fit(obs,(x0,-.126,.600),(x1,-.055,1.000))
  for o in obs:rigid(o,'pelvis')

# Existing head materials and geometry are fitted together to the MPFB face envelope.
heads=[o for o in donors if o.name.startswith('Hair') and 'individual fine' not in o.name or o.name.startswith('Cloth mask')]
headcopies=[duplicate(o,'Head_'+o.name,'Accessories',donorpath) for o in heads]
fit(headcopies,(-.090,-.194,1.583),(.090,.030,1.817))
for o in headcopies:rigid(o,'head')

# Reuse packed existing materials as preview colors only on assets supplied untextured.
steel=bpy.data.materials.get('V002_Blackened_Steel');bronze=bpy.data.materials.get('V002_Aged_Bronze_Edges')
clothmat=cloth.data.materials[0]
red=next((m for m in bpy.data.materials if 'burgundy' in m.name.lower() or 'crimson' in m.name.lower()),clothmat)
def material(ob,m):
 if not ob.data.materials or not any(n.type=='TEX_IMAGE' for old in ob.data.materials if old and old.use_nodes for n in old.node_tree.nodes):
  ob.data.materials.clear();ob.data.materials.append(m)
  ob['material_note']='Source lacks color textures; existing project material assigned for preview'
def import_glb(filename,name,category,targetlo,targethi,mat,bone,limit=0):
 path=SRC/'orignal_models'/filename;track(path)
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));objects=list(set(bpy.data.objects)-before)
 meshes=[o for o in objects if o.type=='MESH']
 for i,o in enumerate(meshes):
  mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw;o.name=name+('' if i==0 else '_'+str(i));put(o,category,path)
  material(o,mat)
  if limit and len(o.data.polygons)>limit:
   d=o.modifiers.new('Reversible prototype display reduction','DECIMATE');d.ratio=limit/len(o.data.polygons)
   o['display_reduction_note']='Source mesh retained; unapplied Decimate for prototype responsiveness'
 fit(meshes,targetlo,targethi)
 for o in meshes:
  if bone:rigid(o,bone)
 for o in objects:
  if o.type!='MESH':
   for c in list(o.users_collection):c.objects.unlink(o)
 return meshes

# Chest uses the existing processed detailed Meshy derivative.
chestpath=SRC/'modular/chest_plate/assassin_chest_plate_v002.blend'
chest=append(chestpath,['ChestArmor_Initial_Optimized'])[0];put(chest,'Armor',chestpath);chest.name='Armor_Chest_Meshy'
material(chest,steel);fit([chest],(-.205,-.174,1.010),(.205,.144,1.472));rigid(chest,'spine_03')

waist=import_glb('Meshy_AI_Crimson_Tattered_Mant_1021005734_generate.glb','Waist_Belts_And_Tattered_Panels','Accessories',(-.242,-.164,.590),(.242,.154,1.054),red,'pelvis',45000)
for sign,label in [(1,'L'),(-1,'R')]:
 x0,x1=(.105,.263) if sign>0 else(-.263,-.105)
 boots=import_glb('Meshy_AI__1021003710_model-edit.glb','Armor_Boot_Greave.'+label,'Armor',(x0,-.238,.005),(x1,.075,.487),steel,'calf_'+label.lower(),32000)
 x0,x1=(.053,.220) if sign>0 else(-.220,-.053)
 import_glb('Meshy_AI_assassin_knee_guard_b_1021010856_generate.glb','Armor_Knee.'+label,'Armor',(x0,-.142,.413),(x1,-.026,.634),steel,'calf_'+label.lower(),18000)
 # Bracer supplied vertical; rotate onto the T-pose forearm before fitting.
 br=import_glb('Meshy_AI_Bronze_Vanguard_Brace_1020235333_generate.glb','Armor_Bracer.'+label,'Armor',(-.07,-.07,0),(.07,.07,.25),steel,None)
 for o in br:o.matrix_world=Matrix.Rotation(sign*math.pi/2,4,'Y')@o.matrix_world
 x0,x1=(.489,.707) if sign>0 else(-.707,-.489)
 fit(br,(x0,-.092,1.390),(x1,.063,1.548))
 for o in br:rigid(o,'lowerarm_'+label.lower())

# Preserve generated v003 details; choose it over the distorted v004 derivative.
v3=ROOT/'artifacts/meshy_left_pauldron/iterations/v003/Meshy_Left_Pauldron_v003_game_5k.blend'
pauldron=append(v3,['Meshy_Left_Pauldron_v003_Game_5k'])[0];put(pauldron,'Armor',v3);pauldron.name='Armor_Meshy_Pauldron.L'
pauldron.parent=None;pauldron.matrix_world=Matrix.Rotation(math.pi/2,4,'Z')
fit([pauldron],(.132,-.145,1.279),(.421,.133,1.625));rigid(pauldron,'clavicle_l')
other=pauldron.copy();other.data=pauldron.data.copy();other.name='Armor_Meshy_Pauldron.R';other.parent=None
put(other,'Armor',v3);other.matrix_world=Matrix.Diagonal((-1,1,1,1))@pauldron.matrix_world
rigid(other,'clavicle_r')
for o in [pauldron,other]:o['selection_reason']='v003 appearance retained; v004 known socket distortion avoided'

import_glb('Meshy_AI_crimson_assassin_scar_1021004838_generate.glb','Scarf_And_Back_Mantle','Clothing',(-.330,-.156,.740),(.330,.230,1.572),red,'spine_03',50000)
import_glb('Meshy_AI_Crimson_Hood_1021005559_generate.glb','Hood_Meshy_Original','Clothing',(-.138,-.205,1.532),(.138,.143,1.853),clothmat,'head',35000)

# Everything is existing geometry. Default rest pose remains original T; presentation A pose.
bpy.context.view_layer.update()
for sign,label in [(1,'l'),(-1,'r')]:
 p=rig.pose.bones['upperarm_'+label];head=p.head.copy()
 p.matrix=Matrix.Translation(head)@Matrix.Rotation(sign*math.radians(35),4,'Y')@Matrix.Translation(-head)@p.matrix
bpy.context.view_layer.update()
scene.unit_settings.system='METRIC';scene.world=bpy.data.worlds.new('Prototype_Neutral_Studio');scene.world.use_nodes=True
back=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');back.inputs[0].default_value=(.11,.13,.16,1);back.inputs[1].default_value=.35
for name,loc,power,size in [('Key',(3,-4,5),450,4),('Fill',(-3,-2,3),240,3),('Rim',(1,3,4),500,3)]:
 data=bpy.data.lights.new('Prototype_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(data.name,data);studio.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Prototype_Review_Camera');cam=bpy.data.objects.new('Prototype_Review_Camera',cd);studio.objects.link(cam)
scene.camera=cam;cam.location=(3,-6,2.7);cam.rotation_euler=(Vector((0,0,.97))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=2.25
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1100;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for name,digest in source_hashes.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
with open(OUT/'source_integrity.json','w') as f:json.dump(source_hashes,f,indent=2)
with open(OUT/'rig_original_rest.json','w') as f:json.dump(rig_snapshot,f,indent=2)
manifest=[{'object':o.name,'source':o.get('assembly_source'),'category':[c.name for c in o.users_collection],'attachment':o.get('attachment','Existing body weights'),'materials':[m.name for m in o.data.materials if m] if o.type=='MESH' else [],'source_triangles':sum(len(p.vertices)-2 for p in o.data.polygons) if o.type=='MESH' else 0,'modifiers':[m.type for m in o.modifiers]} for o in used]
with open(OUT/'assets_used.json','w') as f:json.dump(manifest,f,indent=2)
for image in bpy.data.images:
 if image.has_data and image.filepath and not image.packed_file:
  try:image.pack()
  except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hooded_Assassin_Prototype_v001.blend'))
print('ASSEMBLED',len(used),'objects; MPFB bones',len(rig.data.bones),'sources',len(source_hashes))
