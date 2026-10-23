"""Refine the existing pauldron datablocks; do not regenerate the asset."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

root=bpy.data.objects['LP_Assembly']
col=bpy.data.collections['LEFT_PAULDRON_ONLY']
plates=[bpy.data.objects[n] for n in ['LP_01_Domed_Crown','LP_02_Upper_Chevron','LP_03_Middle_Chevron','LP_04_Long_Terminal_Plate']]
meshes=[o for o in root.children if o.type=='MESH']
for o in meshes:
 if 'rigid_layers_before' not in o:
  backup=o.data.copy();backup.name=o.name+'_Before_Rigid_Layers';backup.use_fake_user=True;o['rigid_layers_before']=backup.name

# Association uses the actual current plate surfaces, before changing them.
trees=[]
for o in plates:
 me=bpy.data.meshes[o['rigid_layers_before']]
 trees.append(BVHTree.FromPolygons([o.matrix_local@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]))

def components(me):
 adj=[[] for v in me.vertices]
 for e in me.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 todo=set(range(len(me.vertices)));groups=[]
 while todo:
  seed=todo.pop();stack=[seed];group=[seed]
  while stack:
   for n in adj[stack.pop()]:
    if n in todo:todo.remove(n);stack.append(n);group.append(n)
  groups.append(group)
 return groups

def nearest(p):
 return min(range(4),key=lambda i:trees[i].find_nearest(p)[3])

def shape(p,i,raised=False):
 x,y,z=p
 # Piecewise-planar cross sections give the steel a forged ridge and broad cheeks.
 cx=-.022 if i==0 else -.013
 a=math.atan2(y,x-cx);r=math.hypot(x-cx,y)
 step=math.pi/4
 factor=math.cos(step/2)/math.cos((a%step)-step/2)
 r*=factor
 x=cx+r*math.cos(a);y=r*math.sin(a)
 ztops=[.17,.030,-.052,-.135];bottoms=[-.078,-.153,-.234,-.330]
 v=max(0,min(1,(ztops[i]-z)/(ztops[i]-bottoms[i])))
 # Pronounced front and rear blade points, with intentionally unequal profiles.
 shoulder_point=math.exp(-((abs(a)-1.15)/.23)**2)
 z-=([.019,.035,.029,.021][i])*shoulder_point*v**3*(1.16 if y<0 else .82)
 y*=([1.12,1.055,1.03,1.01][i])
 if i:
  y+=math.copysign(.024*shoulder_point*v**3,y)
  x+=.010*shoulder_point*v**3
 if i==0:
  x+=.012*max(0,1-abs(y)/.15)
  z+=.008*max(0,1-abs(y)/.12)*(1-v)
 # Each pre-existing plate gets a distinct rigid resting angle and radial step.
 pivot=[.035,-.055,-.140,-.230][i]
 angle=[-.07,.09,.21,.34][i]
 q=Matrix.Rotation(angle,4,'Y')@Vector((x,y,z-pivot))
 q.z+=pivot
 q.x+=[.031,.005,-.018,-.031][i]
 q.z+=[.004,-.003,-.011,-.020][i]
 if raised:
  n=Vector((math.cos(a),math.sin(a),.14)).normalized()
  q+=Matrix.Rotation(angle,4,'Y').to_3x3()@n*.0045
 return q

for o in meshes:
 name=o.name;src=bpy.data.meshes[o['rigid_layers_before']]
 # The original source is used only to eliminate the previous continuous bend.
 # All existing vertices, plate topology, thickness and material slots are retained.
 base=bpy.data.meshes.get(o.get('shoulder_wrap_original',''))
 if base is None or len(base.vertices)!=len(o.data.vertices):base=src
 inv=o.matrix_local.inverted()
 fixed=next((i for i,p in enumerate(plates) if name.startswith(p.name)),None)
 if fixed is not None:
  for v,b in zip(o.data.vertices,base.vertices):v.co=inv@shape(o.matrix_local@b.co,fixed,'Trim' in name)
 elif name in ['LP_Decorative_Bronze_Appliques','LP_11_Subtle_Battle_Scratches','LP_12_Plate_And_Strap_Rivets']:
  for group in components(src):
   center=sum((o.matrix_local@src.vertices[k].co for k in group),Vector())/len(group)
   idx=nearest(center)
   # Inner suspension rivets remain on their leather supports.
   if 'Rivets' in name and center.x<-.04:
    continue
   for k in group:o.data.vertices[k].co=inv@shape(o.matrix_local@base.vertices[k].co,idx,'Appliques' in name)
 elif name.startswith('LP_05_') or name.startswith('LP_06_'):
  # Retain the rigid spikes, but bring the crest forward and sweep the thorns apart.
  for v,b in zip(o.data.vertices,base.vertices):
   p=o.matrix_local@b.co
   if name.startswith('LP_05_'):
    p.x+=.032;p.z+=.008;p.y*=1.06
    # Reduce the upright rear wall of the fin for the concept's swept blade profile.
    p.x-=max(0,p.z-.18)*.18
   else:
    p.y*=1.13;p.x+=.030;p.z+=.008
    if 'Rear' in name:p.z-=.009
   v.co=inv@p
 # Interior shell and belts retain the rounded fitting bend established previously.
 o.data.update()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

# Keep steel facets crisp where planes meet; small bevels and existing thickness remain.
for o in plates:
 bm=bmesh.new();bm.from_mesh(o.data)
 for e in bm.edges:
  if len(e.link_faces)==2 and e.calc_face_angle()>.19:e.smooth=False
 bm.to_mesh(o.data);bm.free()
 for p in o.data.polygons:p.use_smooth=True
 o['construction']='Separate rigid forged plate; freely articulating overlap above leather suspension'

root.location=(.255,-.01315,1.49)
root['rigid_layer_revision']='Angular cap; individually angled lames; stepped radial offsets; raised bronze borders; asymmetric front/rear blade points'
bpy.context.view_layer.update()
print('Refined existing plate, trim, crest, spike and hardware meshes. No replacement armor created.')
