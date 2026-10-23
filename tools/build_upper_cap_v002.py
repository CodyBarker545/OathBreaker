import bpy,bmesh,math,json,os
from mathutils import Vector
OUT=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\modular\left_pauldron\upper_cap_v002'
os.makedirs(OUT,exist_ok=True)
scene=bpy.data.scenes.new('Upper_Cap_And_Crest_v002_Review')
col=bpy.data.collections.new('Assassin_Left_Pauldron');scene.collection.children.link(col)
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'

def mat(name,color,metal):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.38
 return m
steel=mat('Cap_Review_Charcoal_Steel',(.095,.105,.12),.8)
bronze=mat('Cap_Review_Antique_Bronze',(.34,.205,.105),.75)
# Authored dome surface; explicit longitudinal and circumferential loops.
vs=sorted(set([-1.43+2.86*i/32 for i in range(33)]+[-1.25,.36]))
ts=sorted(set([-1.12+2.80*j/26 for j in range(27)]+[.02,.18,1.53,1.61]))
bm=bmesh.new();uv=bm.verts.layers.float.new('longitudinal');tv=bm.verts.layers.float.new('cross_section')
def surface(v,t,inner=False):
 c=math.cos(v);r=.153
 x=.012+.163*c*math.sin(t);y=.173*math.sin(v);z=.023+r*c*math.cos(t)
 # Lower rim arch and a distinct front angular tongue, tapering into the dome.
 f=max(0,(t-1.15)/.53)
 notch=-.027*max(0,1-abs(v+.80)/.22)
 z+=f*(.030*c+notch)
 if inner:
  n=Vector((c*math.sin(t),math.sin(v),c*math.cos(t))).normalized()
  return Vector((x,y,z))-n*.004
 # Slight raised border integrated in the shell surface.
 if t>=1.53:
  x+=.0025 if t<1.68 else .001
 return Vector((x,y,z))
grid=[]
for v in vs:
 row=[]
 for t in ts:
  p=bm.verts.new(surface(v,t));p[uv]=v;p[tv]=t;row.append(p)
 grid.append(row)
outer=[];patch=[]
for i in range(len(vs)-1):
 for j in range(len(ts)-1):
  f=bm.faces.new((grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1]));outer.append(f)
  if ts[j]>=1.53:f.material_index=1
  if vs[i]>=-1.25001 and vs[i+1]<=.36001 and ts[j]>=.01999 and ts[j+1]<=.18001:patch.append(f)
# Extrude the narrow crown strip into a broad curved blade; no overlapping components.
for s in [.12,.42,.74,.94,1.0]:
 res=bmesh.ops.extrude_face_region(bm,geom=patch)
 newv=[p for p in res['geom'] if isinstance(p,bmesh.types.BMVert)];newset=set(newv)
 tops=[f for f in bm.faces if all(p in newset for p in f.verts)]
 bmesh.ops.delete(bm,geom=patch,context='FACES_ONLY')
 for p in newv:
  v=p[uv];t=p[tv];u=(v+1.25)/1.61;w=(t-.02)/.16
  base=surface(v,t)
  tip=Vector((.026+(w-.5)*.004*(1-.65*u),-.164+.365*u,.076+.229*math.sin(math.pi*.5*u)**.73))
  # Scooped rear edge and gently cambered blade faces.
  p.co=base.lerp(tip,s)
  p.co.y-=.028*math.sin(math.pi*s)*u**5
  p.co.x+=.008*math.sin(math.pi*s)*math.sin(math.pi*u)
 for f in tops:f.material_index=1 if s>=.94 else 0
 patch=tops
 bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
# Inner cavity remains the clean dome, without a fin cavity or extra internals.
inside=[]
for v in vs:
 inside.append([bm.verts.new(surface(v,t,True)) for t in ts])
for i in range(len(vs)-1):
 for j in range(len(ts)-1):bm.faces.new((inside[i][j+1],inside[i+1][j+1],inside[i+1][j],inside[i][j]))
perim=[(0,j) for j in range(len(ts))]+[(i,len(ts)-1) for i in range(1,len(vs))]+[(len(vs)-1,j) for j in range(len(ts)-2,-1,-1)]+[(i,0) for i in range(len(vs)-2,0,-1)]
for k,(i,j) in enumerate(perim):
 a,b=perim[(k+1)%len(perim)];f=bm.faces.new((grid[i][j],inside[i][j],inside[a][b],grid[a][b]));f.material_index=1
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for f in bm.faces:f.smooth=True
mesh=bpy.data.meshes.new('Upper_Cap_Continuous_Shell_Mesh');bm.to_mesh(mesh);bm.free();mesh.update()
ob=bpy.data.objects.new('Upper_Cap_Integrated_Sweeping_Crest',mesh);col.objects.link(ob)
ob.data.materials.append(steel);ob.data.materials.append(bronze)
bevel=ob.modifiers.new('Small_Forged_Edge_Bevel','BEVEL');bevel.width=.0007;bevel.segments=2
ob['orientation']='Z up; X outward; Y backward; origin at shoulder pivot'
ob['construction']='One connected closed structural mesh: curved cap, shared-vertex swept blade, 4mm cavity shell. No lower plates.'
scene['stage']='Upper cap and integrated crest only. Await user approval before lower plates.'
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D':
  sp=a.spaces.active;sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO';sp.overlay.show_overlays=False
  sp.region_3d.view_perspective='ORTHO';sp.region_3d.view_location=Vector((.04,.015,.14));sp.region_3d.view_distance=.72;sp.region_3d.view_rotation=Vector((1,-.6,.28)).to_track_quat('Z','Y')
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=OUT+'\\assassin_left_pauldron_upper_cap_v002.blend')
print('Created cap-only review. Saved',bpy.data.filepath)
