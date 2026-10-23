import bpy,bmesh,math,json,os
from mathutils import Vector
ob=bpy.data.objects['Upper_Cap_Integrated_Sweeping_Crest']
materials=list(ob.data.materials)
# Authored dome surface; explicit longitudinal and circumferential loops.
vs=sorted(set([-1.43+2.86*i/32 for i in range(33)]+[-1.25,.36,-1.0,-.5,.55,1.0]))
ts=sorted(set([-1.12+2.80*j/26 for j in range(27)]+[-.26,.48,1.53,1.61]))
bm=bmesh.new();uv=bm.verts.layers.float.new('longitudinal');tv=bm.verts.layers.float.new('cross_section')
def surface(v,t,inner=False):
 c=math.cos(v);r=.153
 x=.012+.163*c*math.sin(t);y=.173*math.sin(v);z=.023+r*c*math.cos(t)
 # Lower rim arch and a distinct front angular tongue, tapering into the dome.
 f=max(0,(t-1.15)/.53)
 notch=-.027*max(0,1-abs(v+.80)/.22)
 z+=f*(.059*c+notch-.014*max(0,1-abs(v-.78)/.32))
 # Asymmetric shoulder silhouette with flatter outer cheek and rear flare.
 x+=max(0,math.sin(t))*(.012*v+.009*max(0,1-abs(v-.65)/.35))
 if x>.125: x-=.005*((x-.125)/.055)**2
 y*=1+.055*max(0,math.sin(t))*(1 if v>0 else -.4)
 if abs(v)>1.25:
  mix=min(1,(abs(v)-1.25)/.18)
  z=z
 # Piecewise outer boundary keeps the dome but breaks its circular perimeter.
 anchors=[(-1.43,.035,-.177),(-1.0,.115,-.155),(-.5,.164,-.090),(0,.171,0),(.55,.180,.095),(1.0,.140,.160),(1.43,.025,.185)]
 k=next((i for i in range(len(anchors)-1) if v<=anchors[i+1][0]),len(anchors)-2)
 a,b=anchors[k],anchors[k+1];q=(v-a[0])/(b[0]-a[0]);blend=max(0,min(1,(t-.6)/1.08))**2*max(0,min(1,(1.43-abs(v))/.3))
 x=x*(1-blend)+(a[1]*(1-q)+b[1]*q)*blend
 y=y*(1-blend)+(a[2]*(1-q)+b[2]*q)*blend
 if inner:
  return Vector((x*.965,y*.965,z*.965))
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
  if vs[i]>=-1.25001 and vs[i+1]<=.36001 and ts[j]>=-.26001 and ts[j+1]<=.48001:patch.append(f)
# Extrude the narrow crown strip into a broad curved blade; no overlapping components.
for s in [.12,.42,.74,.94,1.0]:
 res=bmesh.ops.extrude_face_region(bm,geom=patch)
 newv=[p for p in res['geom'] if isinstance(p,bmesh.types.BMVert)];newset=set(newv)
 tops=[f for f in bm.faces if all(p in newset for p in f.verts)]
 bmesh.ops.delete(bm,geom=patch,context='FACES_ONLY')
 for p in newv:
  v=p[uv];t=p[tv];u=(v+1.25)/1.61;w=(t+.26)/.74
  base=surface(v,t)
  tip=Vector((.022+.065*math.sin(math.pi*u*.72)+(w-.5)*.012*(1-.45*u),-.170+.390*u,.077+.184*(.7*math.sin(math.pi*.5*u)**.75+.3*u)))
  # Scooped rear edge and gently cambered blade faces.
  tip.z+=.032*math.sin(math.pi*u)
  p.co=base.lerp(tip,s)
  p.co.z+=.014*math.sin(math.pi*s)*math.sin(math.pi*u)
  p.co.y-=.052*math.sin(math.pi*s)*u**4
  p.co.x+=.018*math.sin(math.pi*s)*math.sin(math.pi*u)+(w-.5)*.014*math.sin(math.pi*s)
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

ob.data=mesh
for m in materials: ob.data.materials.append(m)
print('Rebuilt only upper-cap geometry; retained original material datablocks and bevel modifier.')
