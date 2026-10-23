"""One connected forged cap, using a continuous quad surface and region extrusion.
Does not touch lower lames, character, skeleton, straps or unrelated geometry.
"""
import bpy,bmesh,math,bisect
from mathutils import Vector

cap=bpy.data.objects['LP_01_Domed_Crown']
D=bpy.data.objects['LP_Pauldron_Review_Instance'].matrix_world
M=D@cap.matrix_world;I=M.inverted()
for o in list(cap.children_recursive):bpy.data.objects.remove(o,do_unlink=True)

angles=[-2.24,-1.90,-1.57,-1.25,-.94,-.70,-.38,0,.38,.75,1.06,1.40,1.72,2.02,2.24]
edges=[.013,.013,.006,-.014,-.049,-.053,-.020,-.020,-.004,-.031,-.018,.002,.008,.013,.013]
radii=[0,.20,.43,.66,.84,.97,1.025,1.055]
zs=[1.577,1.574,1.564,1.545,1.520,1.490,1.461,1.442]
hook=[(.85,.24),(1.25,.31),(1.50,.46),(1.53,.60),(1.33,.68),(1.19,.63),(1.10,.68),(.95,.82),(.73,.95)]
def profile(vals,v):
 f=v*(len(vals)-1);i=min(len(vals)-2,int(f));t=f-i
 return vals[i]*(1-t)+vals[i+1]*t
def line_distance(a,v):
 p=Vector((abs(a)*.65,v));distance=100
 for k in range(len(hook)-1):
  A=Vector((hook[k][0]*.65,hook[k][1]));B=Vector((hook[k+1][0]*.65,hook[k+1][1]));e=B-A;t=max(0,min(1,(p-A).dot(e)/e.length_squared));distance=min(distance,(p-(A+t*e)).length)
 return distance
def surface(a,v,details=True):
 j=min(len(angles)-2,max(0,bisect.bisect_right(angles,a)-1));t=(a-angles[j])/(angles[j+1]-angles[j]);r=profile(radii,v)
 # Broad sculpted cheeks use controlled angular sections rather than a cylinder.
 x=.212+.118*r*(math.cos(angles[j])*(1-t)+math.cos(angles[j+1])*t)
 y=-.01315+.128*r*(math.sin(angles[j])*(1-t)+math.sin(angles[j+1])*t)
 z=profile(zs,v)+(edges[j]*(1-t)+edges[j+1]*t)*v**3
 if abs(a)>1.8:y+=math.copysign(.009*(abs(a)-1.8)/.44*v,y+.01315)
 # Ridge, sculpted cheek contours and raised perimeter are all vertex displacement
 # of this same surface; no independent strips or intersecting ornaments exist.
 ridge=.0105*math.exp(-((a+.70)/.19)**2)*math.sin(math.pi*v*.72)
 detail=.0035*max(0,1-line_distance(a,v)/.065)**1.3
 rim=.0032*max(0,min(1,(v-.88)/.045))
 neck=.0025*max(0,min(1,(abs(a)-2.10)/.10))
 h=(ridge+detail+rim+neck) if details else 0
 n=Vector((math.cos(a)*.8,math.sin(a)*.8,.65*(1-v)+.10)).normalized()
 return Vector((x,y,z))+n*h

bm=bmesh.new();U=bm.verts.layers.float.new('cap_theta');V=bm.verts.layers.float.new('cap_v')
zone=bm.faces.layers.int.new('feature_region')
theta=[-2.24+4.48*k/84 for k in range(85)]
levels=sorted(set([k/36 for k in range(1,37)]+[.24,.29,.34,.39,.88,.91,.94,.97]))
pole=bm.verts.new((.212,-.01315,1.577));pole[U]=0;pole[V]=0
grid=[]
for v in levels:
 row=[]
 for a in theta:
  vert=bm.verts.new(surface(a,v));vert[U]=a;vert[V]=v;row.append(vert)
 grid.append(row)
outer=[]
for j in range(len(theta)-1):outer.append(bm.faces.new((pole,grid[0][j],grid[0][j+1])))
for i in range(len(grid)-1):
 for j in range(len(theta)-1):outer.append(bm.faces.new((grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1])))
for f in outer:
 a=sum(v[U] for v in f.verts)/len(f.verts);v=sum(p[V] for p in f.verts)/len(f.verts)
 f.material_index=1 if v>.91 or abs(a)>2.13 or (.13<abs(a+.70)<.205 and v>.15) else 0
 # Dedicated rectangular face regions become the crest and the two side points.
 if .24<v<.39 and -1.44<a<1.50:f[zone]=1
 elif .57<v<.69 and -1.25<a<-.98:f[zone]=2
 elif .57<v<.69 and 1.04<a<1.31:f[zone]=3

bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
# The curved underside is established before the outer features are extruded.
# It stays a hollow shoulder cup while crest/spikes are solid metal volumes.
original_verts=set(bm.verts)
bmesh.ops.solidify(bm,geom=list(outer),thickness=-.0038)
# Shape the inner skin from the smooth shoulder volume. Offsetting the fine
# outer ridge normals directly would make the inner edge loops fold together.
for vert in bm.verts:
 if vert not in original_verts:
  a=vert[U];v=vert[V];phi=v*1.65
  n=Vector((math.sin(phi)*math.cos(a)/.118,math.sin(phi)*math.sin(a)/.128,math.cos(phi)/.128)).normalized()
  vert.co=surface(a,v,False)-n*.0038

def cleanup():
 bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS')

def extrude_region(faces,stage_transform,stage):
 result=bmesh.ops.extrude_face_region(bm,geom=faces,use_keep_orig=False)
 verts=[v for v in result['geom'] if isinstance(v,bmesh.types.BMVert)]
 vset=set(verts)
 tops=[f for f in result['geom'] if isinstance(f,bmesh.types.BMFace) and all(v in vset for v in f.verts)]
 if not tops:tops=[f for f in bm.faces if all(v in vset for v in f.verts)]
 bmesh.ops.delete(bm,geom=[f for f in faces if f.is_valid],context='FACES_ONLY')
 for v in verts:v.co=stage_transform(v[U],v[V],stage)
 for f in tops:f.material_index=0
 cleanup()
 return tops

crest=[f for f in outer if f.is_valid and f[zone]==1]
amin=min(v[U] for f in crest for v in f.verts);amax=max(v[U] for f in crest for v in f.verts)
vmin=min(v[V] for f in crest for v in f.verts);vmax=max(v[V] for f in crest for v in f.verts)
column_ranges={}
for f in crest:
 for vert in f.verts:
  key=round(vert[U],6);lo,hi=column_ranges.get(key,(10,-10));column_ranges[key]=(min(lo,vert[V]),max(hi,vert[V]))
def crest_shape(a,v,s):
 base=surface(a,v);t=(a-amin)/(amax-amin);w=(v-vmin)/(vmax-vmin)
 # The fin is drawn from a broad rooted strip into a swept, tapered forged blade.
 h=.030+.068*t**.72
 top_y=-.105+.235*t
 # A narrow roof and a taller aft tip give the distinctive swept blade contour.
 half=.0065*(1-.82*t**4)
 target=Vector((.243+(w-.5)*2*half,top_y,base.z+h))
 if s==.10:return base+Vector((0,0,.006))
 blend=(s-.10)/.90
 return (base+Vector((0,0,.006))).lerp(target,blend)
for stage in [.10,.32,.65,1.0]:crest=extrude_region(crest,crest_shape,stage)

for number,side in [(2,-1),(3,1)]:
 faces=[f for f in outer if f.is_valid and f[zone]==number]
 av=sum(v[U] for f in faces for v in f.verts)/sum(len(f.verts) for f in faces)
 vv=sum(v[V] for f in faces for v in f.verts)/sum(len(f.verts) for f in faces)
 basecenter=surface(av,vv);direction=Vector((.033,side*.037,.060 if side<0 else .066))
 def spike_shape(a,v,s):
  p=surface(a,v);tip=basecenter+direction
  # Multiple cross-section loops taper the surface extrusion continuously to a point.
  scale=1-s*.96
  return basecenter+direction*s+(p-basecenter)*scale
 for stage in [.12,.42,.76,1.0]:faces=extrude_region(faces,spike_shape,stage)

cleanup();bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for e in bm.edges:
 e.smooth=not (len(e.link_faces)==2 and e.calc_face_angle()>.85)
for f in bm.faces:f.smooth=True
bm.transform(I)
me=bpy.data.meshes.new('LP_Upper_Cap_Connected_Extruded_Forging');bm.to_mesh(me);bm.free()
me.materials.append(bpy.data.materials['LP_Charcoal_Forged_Steel']);me.materials.append(bpy.data.materials['LP_Antique_Bronze'])
cap.data=me
cap['construction']='ONE connected mesh: quad shoulder cup; solidified underside; face-region extruded crest and side points; vertex-shaped ridges and borders'
cap['thickness_m']=.0038
bpy.context.view_layer.update()
print('One cap object, no cap children. Crest and thorns were region-extruded from the cap topology.')
