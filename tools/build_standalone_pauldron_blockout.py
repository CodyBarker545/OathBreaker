"""Standalone silhouette approval stage only. No trim, textures or materials."""
import bpy,bmesh,math,bisect,json,os
from mathutils import Vector

OUT=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\modular\left_pauldron\standalone_blockout_v001'
scene=bpy.data.scenes.new('Assassin_Left_Pauldron_Blockout_Review')
col=bpy.data.collections.new('Assassin_Left_Pauldron_Standalone');scene.collection.children.link(col)
bpy.context.window.scene=scene
root=bpy.data.objects.new('PAULDRON_Standalone_Origin',None);col.objects.link(root)
root['orientation']='+X outward, -X inward (hollow opening); -Y front, +Y back; +Z top; -Z upper-arm descent'
root['stage']='BASIC SILHOUETTE BLOCKOUT ONLY. Await approval before detailed geometry, trim or materials.'
root['scale']='Meters; origin at shoulder-cavity center; no humanoid fitting'
def object_from_bmesh(name,bm):
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 for f in bm.faces:f.smooth=True
 me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.update()
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.parent=root
 return ob

# Broad angular crown. All points are authored in the standalone local frame.
keys=[-2.14,-1.78,-1.40,-1.05,-.72,-.37,0,.36,.76,1.10,1.44,1.80,2.14]
edge=[.014,.011,.001,-.020,-.054,-.022,-.025,-.006,-.030,-.012,.005,.012,.014]
rv=[0,.20,.43,.66,.84,.97,1.02,1.05]
zv=[.160,.157,.146,.126,.096,.062,.027,.010]
def profile(arr,v):
 q=v*(len(arr)-1);i=min(len(arr)-2,int(q));t=q-i
 return arr[i]*(1-t)+arr[i+1]*t
def surf(a,v):
 j=min(len(keys)-2,max(0,bisect.bisect_right(keys,a)-1));t=(a-keys[j])/(keys[j+1]-keys[j]);r=profile(rv,v)
 x=-.012+.160*r*(math.cos(keys[j])*(1-t)+math.cos(keys[j+1])*t)
 y=.150*r*(math.sin(keys[j])*(1-t)+math.sin(keys[j+1])*t)
 z=profile(zv,v)+(edge[j]*(1-t)+edge[j+1]*t)*v**3
 # The broad crest-root ridge is only a silhouette mass at this stage.
 h=.006*math.exp(-((a+.72)/.24)**2)*math.sin(math.pi*v*.72)
 return Vector((x+h*math.cos(a),y+h*math.sin(a),z+h*.3))

bm=bmesh.new();U=bm.verts.layers.float.new('theta');V=bm.verts.layers.float.new('cap_v');Z=bm.faces.layers.int.new('zone')
angles=[-2.14+4.28*j/48 for j in range(49)]
levels=sorted(set([j/20 for j in range(1,21)]+[.24,.29,.34,.39]))
pole=bm.verts.new((-.012,0,.160));pole[U]=0;pole[V]=0;grid=[]
for v in levels:
 row=[]
 for a in angles:
  p=bm.verts.new(surf(a,v));p[U]=a;p[V]=v;row.append(p)
 grid.append(row)
outer=[]
for j in range(48):outer.append(bm.faces.new((pole,grid[0][j],grid[0][j+1])))
for i in range(len(grid)-1):
 for j in range(48):outer.append(bm.faces.new((grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1])))
for f in outer:
 a=sum(v[U] for v in f.verts)/len(f.verts);v=sum(p[V] for p in f.verts)/len(f.verts)
 if .24<v<.39 and -1.38<a<1.43:f[Z]=1
 elif .56<v<.71 and -1.28<a<-1.00:f[Z]=2
 elif .56<v<.71 and 1.03<a<1.31:f[Z]=3
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));original=set(bm.verts)
bmesh.ops.solidify(bm,geom=outer,thickness=-.004)
for vert in bm.verts:
 if vert not in original:
  a=vert[U];v=vert[V];phi=v*1.65;n=Vector((math.sin(phi)*math.cos(a)/.160,math.sin(phi)*math.sin(a)/.150,math.cos(phi)/.150)).normalized()
  vert.co=surf(a,v)-n*.004
def extrude(faces,transform,s):
 res=bmesh.ops.extrude_face_region(bm,geom=faces,use_keep_orig=False);vs=[v for v in res['geom'] if isinstance(v,bmesh.types.BMVert)];ss=set(vs)
 tops=[f for f in bm.faces if all(v in ss for v in f.verts)]
 bmesh.ops.delete(bm,geom=[f for f in faces if f.is_valid],context='FACES_ONLY')
 for v in vs:v.co=transform(v[U],v[V],s)
 bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS')
 return tops
faces=[f for f in outer if f.is_valid and f[Z]==1]
amin=min(v[U] for f in faces for v in f.verts);amax=max(v[U] for f in faces for v in f.verts);vmin=min(v[V] for f in faces for v in f.verts);vmax=max(v[V] for f in faces for v in f.verts)
def crest(a,v,s):
 base=surf(a,v);t=(a-amin)/(amax-amin);w=(v-vmin)/(vmax-vmin)
 target=Vector((.035+(w-.5)*.012*(1-.75*t**4),-.115+.250*t,base.z+.028+.065*t**.75))
 if s==.12:return base+Vector((0,0,.007))
 return (base+Vector((0,0,.007))).lerp(target,(s-.12)/.88)
for s in [.12,.44,1]:faces=extrude(faces,crest,s)
for number,side in [(2,-1),(3,1)]:
 fs=[f for f in outer if f.is_valid and f[Z]==number];allvs=[v for f in fs for v in f.verts]
 a=sum(v[U] for v in allvs)/len(allvs);v=sum(v[V] for v in allvs)/len(allvs);center=surf(a,v);direction=Vector((.034,side*.029,.048 if side<0 else .055))
 def spike(a,v,s):return center+direction*s+(surf(a,v)-center)*(1-.95*s)
 for s in [.22,.65,1]:fs=extrude(fs,spike,s)
cap=object_from_bmesh('BLOCKOUT_01_Angular_Cap_And_Swept_Crest',bm)
cap['role']='Broad cap + connected swept-back crest and small outward shoulder points; blockout mass only'

# Independent, non-identical rigid shield lames. No rotations, fitting or decorative borders.
profiles=[
 [ .083,.064,.034,.052,.016,.025,0,.025,.057,.025,.064,.080,.090],
 [ .078,.056,.026,.044,.008,.022,0,.023,.046,.018,.055,.073,.085],
 [ .118,.101,.079,.090,.058,.028,0,.036,.077,.058,.095,.111,.126]
]
widths=[(.151,.148),(.132,.128),(.108,.105)]
tops=[-.010,-.082,-.153];bottoms=[-.153,-.236,-.335]
for i in range(3):
 bm=bmesh.new();rows=[]
 for v in [0,.22,.55,.82,1]:
  row=[]
  for j,a in enumerate(keys):
   xrad,yrad=widths[i];taper=1-.12*v
   x=.004+xrad*taper*math.cos(a)+.009*math.sin(math.pi*v)
   y=yrad*taper*math.sin(a)
   zb=bottoms[i]+profiles[i][j]
   z=tops[i]*(1-v)+zb*v
   # An outer keel and distinct front/rear corners break the band-like outline.
   x+=.010*max(0,math.cos(a))**8*v
   row.append(bm.verts.new((x,y,z)))
  rows.append(row)
 fs=[]
 for k in range(4):
  for j in range(len(keys)-1):fs.append(bm.faces.new((rows[k][j],rows[k+1][j],rows[k+1][j+1],rows[k][j+1])))
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.solidify(bm,geom=fs,thickness=-.0035)
 ob=object_from_bmesh(['BLOCKOUT_02_Broad_Upper_Lame','BLOCKOUT_03_Scalloped_Middle_Lame','BLOCKOUT_04_Long_Pointed_Terminal_Lame'][i],bm)
 ob['role']='Independent rigid articulated plate; consistent local orientation; no skinning or fitting'

bpy.context.view_layer.update()
scene['orientation']=root['orientation'];scene['approval_gate']='STOP: silhouette blockout approval required before further detail'
scene.unit_settings.system='METRIC'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  s=area.spaces.active;s.shading.type='SOLID';s.shading.color_type='SINGLE';s.shading.single_color=(.52,.52,.52);s.overlay.show_overlays=False;s.region_3d.view_perspective='ORTHO';s.region_3d.view_location=Vector((.02,0,-.04));s.region_3d.view_distance=.88;s.region_3d.view_rotation=Vector((1,-1,.18)).to_track_quat('Z','Y')
print('Standalone blockout created:',col.name,'four neutral meshes, origin at cavity, consistent axes. All original scenes retained and absent from this modeling view.')
