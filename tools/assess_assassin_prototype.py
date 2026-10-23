"""Read inventory, test copied rig poses temporarily, restore pose, save review evidence."""
import bpy,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path('D:/SoftwareEng/Game');SRC=ROOT/'SourceAssets/characters/hooded_assassin';OUT=SRC/'prototype_assembly_v001'
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
manifest=[]
for p in SRC.rglob('*'):
 if not p.is_file() or OUT in p.parents or p.suffix.lower() not in {'.blend','.glb','.gltf','.fbx','.obj'}:continue
 item={'path':str(p.relative_to(SRC)),'bytes':p.stat().st_size,'format':p.suffix.lower()}
 if p.suffix.lower()=='.glb':
  try:
   with p.open('rb') as f:f.read(12);length,kind=struct.unpack('<II',f.read(8));doc=json.loads(f.read(length))
   item.update(meshes=len(doc.get('meshes',[])),skins=len(doc.get('skins',[])),textures=len(doc.get('images',[])),animations=len(doc.get('animations',[])))
  except Exception as e:item['inspection_error']=str(e)
 manifest.append(item)
primary=['base/assassin_base.blend','face/assassin_detailed.blend','animated_prototype/assassin_animated.blend','blendswap_assassin/assassin_refined.blend','orignal_models/assassin_tpose.blend','modular/chest_plate/assassin_chest_plate_v002.blend']
for rel in primary:
 with bpy.data.libraries.load(str(SRC/rel),link=False) as(a,b):
  entry=next(x for x in manifest if x['path'].replace('\\','/')==rel)
  entry.update(object_names=a.objects,material_names=a.materials,scene_names=a.scenes)
with (OUT/'asset_inventory.json').open('w') as f:json.dump(manifest,f,indent=2)

baseline={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
def restore():
 for n,m in baseline.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def coords(name):
 o=scene.objects[name];dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh()
 pts=[o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return pts
sample_names=['Tunic_Upper_Sleeve.L','Tunic_Forearm_Sleeve.L','Armor_Bracer.L','Armor_Meshy_Pauldron.L','Armor_Chest_Meshy','Scarf_And_Back_Mantle']
base={n:coords(n) for n in sample_names};results={}
cam=scene.camera;cam.location=(3,-6,2.6);cam.rotation_euler=(Vector((0,0,.97))-cam.location).to_track_quat('-Z','Y').to_euler()
oldres=(scene.render.resolution_x,scene.render.resolution_y);scene.render.resolution_x=650;scene.render.resolution_y=800;scene.cycles.samples=16
for label,bone,axis,angle in [('small_arm_lift','upperarm_l','Z',15),('small_shoulder_motion','clavicle_l','X',8),('small_torso_bend','spine_03','X',10)]:
 restore();pb=rig.pose.bones[bone];pb.matrix_basis=baseline[bone]@Matrix.Rotation(math.radians(angle),4,axis)
 bpy.context.view_layer.update();motion={}
 for n in sample_names:
  after=coords(n);motion[n]=max((p-q).length for p,q in zip(base[n],after))
 results[label]={'bone':bone,'local_axis':axis,'degrees':angle,'max_displacement_m':motion,'collision_certified':False}
 scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
restore();scene.render.resolution_x,scene.render.resolution_y=oldres;scene.cycles.samples=24
with (OUT/'rig_movement_assessment.json').open('w') as f:json.dump(results,f,indent=2)

dg=bpy.context.evaluated_depsgraph_get();items=[];triangles=0
for o in scene.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();tris=sum(len(p.vertices)-2 for p in me.polygons);triangles+=tris
 items.append({'object':o.name,'source':o.get('assembly_source'),'source_triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'evaluated_triangles':tris,'materials':[m.name for m in o.data.materials if m],'uv_layers':len(o.data.uv_layers),'attachment':o.get('attachment','Original MPFB rig weights'),'dimensions_m':list(o.dimensions),'modifiers':[m.type for m in o.modifiers]});ev.to_mesh_clear()
with (OUT/'final_assembly_manifest.json').open('w') as f:json.dump({'objects':items,'evaluated_triangles':triangles,'bones':len(rig.data.bones),'pose':'A-pose presentation, original T-pose rest preserved','no_new_mesh_geometry_authored':True,'meshy_requests':0},f,indent=2)
with (OUT/'source_integrity.json').open() as f:hashes=json.load(f)
integrity={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest for p,digest in hashes.items()}
assert all(integrity.values())
with (OUT/'source_integrity_verified.json').open('w') as f:json.dump(integrity,f,indent=2)
print(json.dumps({'files_in_inventory':len(manifest),'assembly_meshes':len(items),'evaluated_triangles':triangles,'movement_tests':results,'all_used_sources_unchanged':True}))
