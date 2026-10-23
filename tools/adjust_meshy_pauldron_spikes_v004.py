"""Adjust existing Meshy vertices on a duplicate; no generated/replacement geometry."""
import bpy, math, os, json, hashlib
from mathutils import Vector
OUT='D:/SoftwareEng/Game/artifacts/meshy_left_pauldron/iterations/v004_spike_alignment'
os.makedirs(OUT,exist_ok=True)
source=bpy.data.objects['Meshy_Left_Pauldron_v003_Game_5k']
if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')

def fingerprint(obj):
 return hashlib.sha256(repr(([tuple(v.co) for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],[[tuple(d.uv) for d in layer.data] for layer in obj.data.uv_layers],[m.name if m else None for m in obj.data.materials])).encode()).hexdigest()
before_hash=fingerprint(source)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/before_spike_adjustment_backup.blend',copy=True)
old_scene=bpy.context.scene
scene=bpy.data.scenes.new('Meshy_Pauldron_v004_Spike_Alignment')
scene.world=old_scene.world.copy() if old_scene.world else None
for ob in old_scene.objects:
 if ob.type in {'LIGHT','CAMERA'}:
  cp=ob.copy();cp.data=ob.data.copy();scene.collection.objects.link(cp)
  if ob==old_scene.camera:scene.camera=cp
edited=source.copy();edited.data=source.data.copy();edited.name='Meshy_Left_Pauldron_v004_Spike_Alignment'
scene.collection.objects.link(edited);bpy.context.window.scene=scene
bpy.context.view_layer.objects.active=edited;edited.select_set(True)
original=[v.co.copy() for v in edited.data.vertices]
basis=edited.shape_key_add(name='Basis',from_mix=False)
adjust=edited.shape_key_add(name='Balanced_Spikes_And_Sockets',from_mix=False)
adjust.value=1

def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)

# Every transform acts on the original spike and its existing socket. No topology edits.
specs=[
 {'name':'center','base':(.020,-.014,.291),'tip':(.02442,-.04373,.32456),'new_base':(0,-.014,.291),'new_tip':(0,-.029,.329),'core':.020,'outer':.044},
 {'name':'left','base':(-.079,-.022,.265),'tip':(-.09782,-.02712,.28053),'new_base':(-.081,-.020,.265),'new_tip':(-.106,-.027,.294),'core':.017,'outer':.037},
 {'name':'right','base':(.092,-.010,.266),'tip':(.11538,-.01634,.29014),'new_base':(.081,-.020,.265),'new_tip':(.106,-.027,.294),'core':.017,'outer':.037},
 {'name':'forward','base':(-.010,-.078,.265),'tip':(-.01365,-.10234,.29010),'new_base':(0,-.078,.265),'new_tip':(0,-.102,.290),'core':.014,'outer':.030}
]
for spec in specs:
 for key in ['base','tip','new_base','new_tip']:spec[key]=Vector(spec[key])
 spec['axis']=(spec['tip']-spec['base']).normalized()
 spec['old_length']=(spec['tip']-spec['base']).length
 spec['new_axis']=(spec['new_tip']-spec['new_base']).normalized()
 spec['new_length']=(spec['new_tip']-spec['new_base']).length
 spec['rotation']=spec['axis'].rotation_difference(spec['new_axis'])
 spec['weights']=[]
group_names=[]
for spec in specs:
 group_names.append(edited.vertex_groups.new(name='Spike_'+spec['name']+'_falloff'))

for idx,p in enumerate(original):
 contributions=[]
 for spec in specs:
  d=p-spec['base'];along=d.dot(spec['axis'])
  # Capsule encloses spike shaft and socket; the socket moves with the shaft.
  closest=spec['base']+spec['axis']*max(0,min(spec['old_length'],along))
  distance=(p-closest).length
  weight=(1-smooth(spec['core'],spec['outer'],distance))*smooth(.237,.258,p.z)
  # Exclude the rear crest and lower layered armor entirely.
  weight*=1-smooth(.012,.032,p.y) if spec['name']!='forward' else 1
  rotated=spec['rotation']@d
  # Extend the shaft axially, keeping socket cross-section unchanged.
  extra=spec['new_axis']*(max(0,along)*(spec['new_length']/spec['old_length']-1))
  target=spec['new_base']+rotated+extra
  contributions.append((weight,target-p));spec['weights'].append(weight)
 total=sum(w for w,d in contributions)
 if total:
  movement=sum((w*d for w,d in contributions),Vector())/max(1,total)
  adjust.data[idx].co=p+movement
 for group,(w,d) in zip(group_names,contributions):
  if w>0:group.add([idx],w,'REPLACE')

edited['change']='Localized existing spike/socket vertex transforms, smooth falloff; reversible shape key'
edited['source_object']=source.name
edited['no_api_generation']=True
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=950;scene.render.resolution_y=950;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
edited.data.update();bpy.context.view_layer.update()
assert fingerprint(source)==before_hash,'Source changed unexpectedly'
assert all((adjust.data[i].co-p).length<1e-9 for i,p in enumerate(original) if p.z<=.237),'Lower vertices changed'
report={'source':source.name,'source_fingerprint_unchanged':fingerprint(source)==before_hash,'backup':'before_spike_adjustment_backup.blend','method':'Existing Meshy geometry on new duplicate; reversible shape key; no topology changes','vertex_count':len(original),'polygons':len(edited.data.polygons),'triangles':sum(len(p.vertices)-2 for p in edited.data.polygons),'vertices_moved':sum((adjust.data[i].co-p).length>1e-8 for i,p in enumerate(original)),'lower_armor_z_limit_m':.237,'lower_vertices_unchanged':True,'uv_coordinates_unchanged':True,'material_datablocks_shared_with_source':[m.name for m in edited.data.materials if m],'meshy_calls':0,'spikes':[]}
for spec in specs:
 tip_index=min(range(len(original)),key=lambda i:(original[i]-spec['tip']).length)
 report['spikes'].append({'name':spec['name'],'original_tip':list(original[tip_index]),'adjusted_tip':list(adjust.data[tip_index].co),'target_tip':list(spec['new_tip'])})
with open(OUT+'/inspection.json','w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Meshy_Left_Pauldron_v004_spike_alignment.blend')
print(json.dumps(report))
