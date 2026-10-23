"""Upper cap only. Lower lames, lining, character and skeleton are protected."""
import bpy,bmesh,math,bisect
from mathutils import Vector,Matrix

cap=bpy.data.objects['LP_01_Domed_Crown']
col=bpy.data.collections['LEFT_PAULDRON_ONLY']
D=bpy.data.objects['LP_Pauldron_Review_Instance'].matrix_world
M=D@cap.matrix_world;I=M.inverted()
steel=bpy.data.materials['LP_Charcoal_Forged_Steel'];gold=bpy.data.materials['LP_Antique_Bronze']
review=bpy.context.window.scene
bpy.context.window.scene=bpy.data.scenes['PAULDRON_Concept_Match']
for child in list(cap.children_recursive):bpy.data.objects.remove(child,do_unlink=True)

def finish(o,thickness=0,bevel=0):
 bpy.context.view_layer.objects.active=o
 if thickness:
  mod=o.modifiers.new('Forged metal thickness','SOLIDIFY');mod.thickness=thickness/.65;mod.offset=-1
  bpy.ops.object.modifier_apply(modifier=mod.name)
 if bevel:
  mod=o.modifiers.new('Physical edge bevel','BEVEL');mod.width=bevel/.65;mod.segments=2
  mod.limit_method=next(e.identifier for e in mod.bl_rna.properties['limit_method'].enum_items if e.identifier=='ANGLE');mod.angle_limit=.55
  bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 for e in bm.edges:
  e.smooth=not (len(e.link_faces)==2 and e.calc_face_angle()>.75)
 bm.to_mesh(o.data);bm.free()
 for p in o.data.polygons:p.use_smooth=True
 return o

def part(name,points,faces,mat,thickness=0,bevel=0):
 me=bpy.data.meshes.new(name);me.from_pydata([I@Vector(p) for p in points],[],faces);me.update();me.materials.append(mat)
 o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=cap;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4)
 return finish(o,thickness,bevel)

# Explicit non-uniform angular sections and a shoulder-shaped crown profile.
angles=[-2.24,-1.90,-1.57,-1.25,-.94,-.70,-.38,0,.38,.75,1.06,1.40,1.72,2.02,2.24]
radii=[0,.20,.43,.66,.84,.97,1.025,1.055]
heights=[1.577,1.574,1.564,1.545,1.520,1.490,1.461,1.442]
edgez=[.013,.013,.006,-.014,-.049,-.053,-.020,-.020,-.004,-.031,-.018,.002,.008,.013,.013]

def lerp_profile(values,t):
 a=t*(len(values)-1);j=min(len(values)-2,max(0,int(a)));w=max(0,min(1,a-j))
 return values[j]*(1-w)+values[j+1]*w

def endpoint(a,v,edge):
 r=lerp_profile(radii,v);z=lerp_profile(heights,v)+edge*v**3
 x=.212+.118*r*math.cos(a);y=-.01315+.128*r*math.sin(a)
 # The medial opening has a broader fore/aft return to cover the shoulder apex.
 if abs(a)>1.8:y+=math.copysign(.009*(abs(a)-1.8)/.44*v,y+.01315)
 # The principal ridge is forged into the cap, ending at its asymmetric front beak.
 ridge=.011*math.exp(-((a+.70)/.19)**2)*math.sin(math.pi*v*.72)
 return Vector((x+ridge*math.cos(a),y+ridge*math.sin(a),z+ridge*.45))

def surf(a,v):
 j=min(len(angles)-2,max(0,bisect.bisect_right(angles,a)-1));w=(a-angles[j])/(angles[j+1]-angles[j])
 return endpoint(angles[j],v,edgez[j])*(1-w)+endpoint(angles[j+1],v,edgez[j+1])*w

def normal(a,v):
 du=surf(min(2.24,a+.001),v)-surf(max(-2.24,a-.001),v)
 dv=surf(a,min(1,v+.001))-surf(a,max(.001,v-.001))
 return dv.cross(du).normalized()

theta=[]
for j in range(len(angles)-1):
 for k in range(3):theta.append(angles[j]+(angles[j+1]-angles[j])*k/3)
theta.append(angles[-1]);N=len(theta);rows=14
pts=[Vector((.212,-.01315,1.577))]
for i in range(1,rows+1):pts.extend(surf(a,i/rows) for a in theta)
faces=[(0,1+j,1+j+1) for j in range(N-1)]
for i in range(rows-1):
 for j in range(N-1):
  a=1+i*N+j;faces.append((a,a+N,a+N+1,a+1))
me=bpy.data.meshes.new('LP_Target_Upper_Cap_Forged_Shell');me.from_pydata([I@p for p in pts],[],faces);me.update();me.materials.append(steel)
cap.data=me;finish(cap,.0038,.0008)
cap['design']='Angular shoulder cap with front beak, rear return, structural diagonal ridge, swept blade crest and integrated side thorns'

# Broad raised bronze borders, individually thickened rather than painted lines.
def surface_band(name,uvs):
 p=[surf(a,v)+normal(a,max(.01,v))*.0018 for a,v in uvs]
 fs=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(uvs)//2-1)]
 return part(name,p,fs,gold,.0025,.0005)
surface_band('LP_CAP_Raised_Sculpted_Lower_Border',[(a,v) for a in theta for v in [.895,1]])
for a,sign in [(-2.24,1),(2.24,-1)]:
 surface_band('LP_CAP_Neck_Return_Border_'+str(sign),[(aa,.06+.94*j/20) for j in range(21) for aa in [a,a+sign*.105]])

# A broad steel spine with raised beveled bronze shoulders, down to the front beak.
spine=surface_band('LP_CAP_Main_Ridge_Front_Bracer',[(a,.09+.91*j/24) for j in range(25) for a in [-.775,-.625]])
spine.data.materials[0]=steel
for a in [-.79,-.61]:
 surface_band('LP_CAP_Ridge_Edge_'+str(a),[(aa,.12+.85*j/24) for j in range(25) for aa in [a-.018,a+.018]])

# Sculpted cheek-frame: a hooked shape, with an inward scallop and a pointed lower junction.
for s in [-1,1]:
 path=[(.85,.25),(1.25,.31),(1.50,.46),(1.53,.60),(1.33,.68),(1.19,.63),(1.10,.68),(.95,.82),(.73,.95),(.53,.84),(.57,.62),(.63,.41)]
 ca=sum(p[0] for p in path)/len(path);cv=sum(p[1] for p in path)/len(path)
 inside=[(ca+(a-ca)*.79,cv+(v-cv)*.79) for a,v in path]
 uv=[]
 for k in range(len(path)):
  q=(k+1)%len(path)
  for n in range(4):
   t=n/4
   for ring in [inside,path]:
    a=ring[k][0]*(1-t)+ring[q][0]*t;v=ring[k][1]*(1-t)+ring[q][1]*t;uv.append((s*a,v))
 uv.extend([(s*inside[0][0],inside[0][1]),(s*path[0][0],path[0][1])])
 surface_band('LP_CAP_Sculpted_Cheek_Frame_'+str(s),uv)

# The defining swept blade crest: a closed, faceted steel blade with broad bronze bevels.
outline=[(-.135,1.450),(-.119,1.506),(-.094,1.550),(-.052,1.592),(.006,1.627),(.066,1.653),(.120,1.670),(.092,1.632),(.080,1.596),(.088,1.537),(.026,1.558),(-.046,1.525)]
n=len(outline);cy=sum(p[0] for p in outline)/n;cz=sum(p[1] for p in outline)/n
front=[Vector((.251,y,z)) for y,z in outline]
inside=[Vector((.260,cy+(y-cy)*.79,cz+(z-cz)*.79)) for y,z in outline]
back=[Vector((.241,y,z)) for y,z in outline]
vs=front+inside+back
fs=[];mats=[]
for j in range(n):
 q=(j+1)%n;fs.append((j,q,n+q,n+j));mats.append(1)
fs.append(tuple(n+j for j in range(n)));mats.append(0)
fs.append(tuple(2*n+j for j in reversed(range(n))));mats.append(0)
for j in range(n):fs.append((j,2*n+j,2*n+(j+1)%n,(j+1)%n));mats.append(1)
blade=part('LP_CAP_Back_Swept_Blade_Crest',vs,fs,steel,0,.0008);blade.data.materials.append(gold)
# Set material slots by face centres, after the bevel has added its own faces.
for f in blade.data.polygons:
 c=M@f.center
 f.material_index=0 if c.x>.256 or c.x<.244 else 1
blade['construction']='Rigid swept blade; steel inset with bronze bevel; integrated into front ridge and rear cap'

def thorn(name,a,v,delta):
 base=surf(a,v)+normal(a,v)*.001;tip=base+Vector(delta);axis=(tip-base).normalized()
 A=axis.cross(Vector((0,0,1))).normalized();B=axis.cross(A)
 ring=[base+A*.017,base+B*.021,base-A*.017,base-B*.021]
 o=part(name,ring+[tip],[(0,3,2,1)]+[(j,(j+1)%4,4) for j in range(4)],steel,0,.0006);o.data.materials.append(gold)
 for f in o.data.polygons:
  if f.index%3==0:f.material_index=1
 surface_band(name+'_Flared_Base',[(aa,vv) for aa in [a-.18,a-.09,a,a+.09,a+.18] for vv in [v-.07,v+.06]])
 return o
thorn('LP_CAP_Integrated_Front_Thorn',-.98,.64,(.032,-.040,.068))
thorn('LP_CAP_Integrated_Rear_Thorn',1.03,.65,(.044,.039,.073))

# Sparse structural fasteners at the ridge foot, on the upper cap only.
for a in [-1.17,.98]:
 p=surf(a,.81)+normal(a,.81)*.005;axis=normal(a,.81);A=axis.cross(Vector((0,0,1))).normalized();B=axis.cross(A)
 points=[]
 for depth,r in [(0,.0052),(.0022,.0047)]:points.extend(p+axis*depth+r*(math.cos(j*math.pi/6)*A+math.sin(j*math.pi/6)*B) for j in range(12))
 faces=[tuple(range(11,-1,-1)),tuple(range(12,24))]+[(j,(j+1)%12,(j+1)%12+12,j+12) for j in range(12)]
 part('LP_CAP_Ridge_Fastener_'+str(a),points,faces,gold,0,.0003)

bpy.context.view_layer.update();bpy.context.window.scene=review
print('Rebuilt ONLY upper cap and cap-owned ridge/border/crest/thorn/fastener geometry. Lower plates untouched.')
