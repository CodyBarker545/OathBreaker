import bpy, math, random, json, os
from mathutils import Vector
from math import sin, cos, pi

OUT=r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\modular\left_pauldron\concept_match'
os.makedirs(OUT,exist_ok=True)
previous=bpy.data.collections.get('LEFT_PAULDRON_ONLY')
if previous:
 for obj in list(previous.objects):bpy.data.objects.remove(obj,do_unlink=True)
 bpy.data.collections.remove(previous)
old_scene=bpy.data.scenes.get('PAULDRON_Concept_Match')
if old_scene:bpy.data.scenes.remove(old_scene)
scene=bpy.data.scenes.new('PAULDRON_Concept_Match')
bpy.context.window.scene=scene
col=bpy.data.collections.new('LEFT_PAULDRON_ONLY');scene.collection.children.link(col)
root=bpy.data.objects.new('LP_Assembly',None);col.objects.link(root)
root.location=(.245,-.01315,1.48);root.rotation_euler[1]=-pi/2
root['reference']='Assassin Pauldron Concept Reference Sheet.png'
root['design']='Domed crown, swept crest, paired thorns, three independent pointed lames; open interior'

def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=next(n for n in n if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=170;tex.inputs['Detail'].default_value=2
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.00035
 l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(*(c*.65 for c in color),1)
 ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*(c*1.3 for c in color),1)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
 return m
steel=material('LP_Charcoal_Forged_Steel',(.042,.048,.057),.86,.37)
bronze=material('LP_Antique_Bronze',(.29,.173,.075),.78,.34)
leather=material('LP_Dark_Brown_Leather',(.043,.018,.012),0,.68)
lining=material('LP_Oxblood_Inner_Binding',(.068,.017,.012),0,.73)
wear=material('LP_Restrained_Edge_Wear',(.19,.142,.087),.8,.47)

def mesh(name,vs,fs,mat,thick=0,bev=0):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;o.data.materials.append(mat)
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 if thick:
  m=o.modifiers.new('Forged thickness','SOLIDIFY');m.thickness=thick;m.offset=-1
  bpy.ops.object.modifier_apply(modifier=m.name)
 if bev:
  m=o.modifiers.new('Soft forged edges','BEVEL');m.width=bev;m.segments=2
  bpy.ops.object.modifier_apply(modifier=m.name)
 for p in me.polygons:p.use_smooth=True
 o.select_set(False);return o

def ribbon(name,pts,width,mat,thick=.001):
 vs=[]
 for i,p in enumerate(pts):
  p=Vector(p);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])
  normal=Vector((p.x,p.y,.05)).normalized();side=t.cross(normal).normalized()*width/2
  vs.extend([p-side,p+side])
 return mesh(name,vs,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)],mat,thick,.00035)

def tube(name,pts,r,mat,sides=6):
 vs=[]
 for i,p in enumerate(pts):
  p=Vector(p);t=(Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)])).normalized()
  a=t.cross(Vector((0,1,0)))
  if a.length<.01:a=t.cross(Vector((1,0,0)))
  a.normalize();b=t.cross(a)
  vs.extend([p+r*(cos(j*2*pi/sides)*a+sin(j*2*pi/sides)*b) for j in range(sides)])
 fs=[tuple(range(sides-1,-1,-1))]
 for i in range(len(pts)-1):
  for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
 fs.append(tuple((len(pts)-1)*sides+j for j in range(sides)))
 return mesh(name,vs,fs,mat)

N=40;M=12
def crown(t,v):
 a=t*2.12;phi=.10+v*1.53
 edge=.038-.114*max(0,cos(a))**5-.024*abs(sin(a))**10
 return Vector((.165*sin(phi)*cos(a)-.022,.162*sin(phi)*sin(a),.172*cos(phi)+edge*v**5))

def lame_func(index):
 radii=[.153,.132,.108];tops=[.030,-.052,-.135];ends=[-.153,-.234,-.330]
 def f(t,v):
  a=t*2.03;r=radii[index]*(1-.12*v)
  # Three non-uniform cusps, with the long central shield point.
  zbottom=ends[index]+.091*(abs(sin(a))**.8)+.019*(abs(sin(2*a))**1.4)-.030*abs(sin(a*1.65))**14
  z=tops[index]*(1-v)+zbottom*v+.009*sin(pi*v)
  x=r*cos(a)-.013+.010*sin(pi*v)+.014*max(0,cos(a))**12*v
  y=r*sin(a)
  return Vector((x,y,z))
 return f

def plate(name,f):
 vs=[f(-1+2*j/N,i/M) for i in range(M+1) for j in range(N+1)]
 fs=[(i*(N+1)+j,(i+1)*(N+1)+j,(i+1)*(N+1)+j+1,i*(N+1)+j+1) for i in range(M) for j in range(N)]
 o=mesh(name,vs,fs,steel,.0032,.00065)
 # Flat bronze strips that follow each surface rather than round piping.
 for edge in ['lower','front','rear']:
  vv=[];ff=[];steps=N if edge=='lower' else M
  for k in range(steps+1):
   q=k/steps
   params=[(-1+2*q,.935),(-1+2*q,1)] if edge=='lower' else ([(-1,q),(-.945,q)] if edge=='front' else [(.945,q),(1,q)])
   for t,v in params:
    p=f(t,v);p+=Vector((cos(t*2.05),sin(t*2.05),.3))*.0013;vv.append(p)
  ff=[(2*k+2,2*k+3,2*k+1,2*k) for k in range(steps)]
  mesh(name+'_Bronze_'+edge,vv,ff,bronze,.0014,.00035)
 return o

plate('LP_01_Domed_Crown',crown)
for i in range(3):plate(['LP_02_Upper_Chevron','LP_03_Middle_Chevron','LP_04_Long_Terminal_Plate'][i],lame_func(i))
# Neck-side arch closes the crown top while leaving the whole underside open.
ribbon('LP_Crown_Inner_Arch',[crown(-1+2*k/32,.15) for k in range(33)],.010,bronze,.002)
for s in [-1,1]:
 ribbon('LP_Crown_Gothic_Swept_Rib_'+str(s),[crown(s*(.12+.72*k/24),.22+.74*k/24)+Vector((.002,s*.001,.001)) for k in range(25)],.012,bronze,.0018)

def fin(name,outline,halfwidth):
 # Faceted double sided blade with a bronze perimeter and a dark recessed face.
 center=sum((Vector(p) for p in outline),Vector())/len(outline)
 for side in [-1,1]:
  outer=[Vector((p[0],side*halfwidth,p[2])) for p in outline]
  inner=[center+(p-center)*.76+Vector((0,side*(halfwidth+.0006),0)) for p in outer]
  vs=outer+inner;n=len(outer)
  mesh(name+'_Trim_'+str(side),vs,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],bronze,.0015,.0003)
  mesh(name+'_Steel_'+str(side),inner,[tuple(range(n))],steel,.0018,.0003)
 mesh(name+'_Spine',[Vector((p[0],s*halfwidth,p[2])) for s in [-1,1] for p in outline],[(i,(i+1)%len(outline),(i+1)%len(outline)+len(outline),i+len(outline)) for i in range(len(outline))],bronze)

fin('LP_05_Swept_Crown_Crest',[(-.075,0,.114),(-.064,0,.220),(-.029,0,.282),(.032,0,.250),(.112,0,.154),(.143,0,.087),(.066,0,.137)],.006)

def spike(name,base,tip,r):
 base=Vector(base);tip=Vector(tip);axis=(tip-base).normalized();a=axis.cross(Vector((1,0,0))).normalized();b=axis.cross(a)
 vs=[base+r*(cos(j*pi/2)*a+sin(j*pi/2)*b) for j in range(4)]+[tip]
 o=mesh(name,vs,[(0,3,2,1)]+[(j,(j+1)%4,4) for j in range(4)],bronze,0,.0004)
 for j in [0,2]:tube(name+'_Ridge_'+str(j),[vs[j],tip],.0007,wear,4)
for s in [-1,1]:spike('LP_06_Side_Thorn_'+('Front' if s<0 else 'Rear'),(.047,s*.133,.108),(.084,s*.207,.204),.027)

# Pointed bronze appliques accent the corners and central keel.
for layer,f in enumerate([crown]+[lame_func(i) for i in range(3)]):
 for t in [-.72,0,.72]:
  v=.87 if t else .9
  params=[(t-.11,v-.09),(t-.045,v-.12),(t,v-.23),(t+.045,v-.12),(t+.11,v-.09),(t+.06,.98),(t,1),(t-.06,.98)]
  vs=[f(max(-1,min(1,a)),b)+Vector((cos(a*2),sin(a*2),.2))*.0029 for a,b in params]
  mesh('LP_Ornament_%d_%s'%(layer,t),vs,[tuple(range(8))],bronze,.001,.00025)
 # Proud central steel ridge, underlined in bronze.
 tube('LP_Central_Keel_%d'%layer,[f(0,k/12)+Vector((.002,0,.001)) for k in range(13)],.0012,bronze,4)

# Hollow oxblood leather liner follows the plates inside; never a solid shoulder plug.
def liner(t,v):
 a=t*2.0;r=.087+.036*sin(pi*v*.9)-.025*v
 return Vector((r*cos(a)-.02,r*sin(a),.125-.327*v))
vs=[liner(-1+2*j/32,i/12) for i in range(13) for j in range(33)]
mesh('LP_07_Curved_Hollow_Leather_Liner',vs,[(i*33+j,i*33+j+1,(i+1)*33+j+1,(i+1)*33+j) for i in range(12) for j in range(32)],lining,.002,.0005)
for t in [-1,1]:tube('LP_Liner_Bound_Edge_'+str(t),[liner(t,k/20) for k in range(21)],.0022,leather,6)

for s in [-1,1]:
 # Long interior suspension straps with rivets, visible through the open neck side.
 pts=[liner(s*.73,k/18)+Vector((-.002,0,0)) for k in range(19)]
 ribbon('LP_08_Interior_Suspension_'+str(s),pts,.016,leather,.0025)
 # A curved arm belt runs around the underside, with a hanging tail.
pts=[Vector((.102*cos(a)-.020,.102*sin(a),-.176+.016*sin(a))) for a in [-2.15+4.3*k/40 for k in range(41)]]
ribbon('LP_09_Underarm_Leather_Belt',pts,.023,leather,.003)

def buckle(name,center):
 c=Vector(center);# frame in the YZ plane, opening is real geometry
 outline=[(-.014,-.018),(.014,-.018),(.014,.018),(-.014,.018),(-.014,-.018)]
 tube(name+'_Frame',[c+Vector((0,y,z)) for y,z in outline],.0025,bronze,6)
 tube(name+'_Tongue',[c+Vector((-.001,0,-.016)),c+Vector((.002,0,.010))],.0014,bronze,6)
for i,c in enumerate([(.067,-.083,-.164),(-.060,-.080,-.065)]):buckle('LP_10_Buckle_%d'%i,c)
ribbon('LP_Belt_Punched_Tail',[(.064,-.084,-.166),(.064,-.084,-.200),(.058,-.079,-.235)],.019,leather,.003)

def rivet(name,p,normal,r=.0032):
 p=Vector(p);normal=Vector(normal).normalized()
 bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=5,radius=1)
 o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=root;o.location=p;o.scale=(r,r,r*.45);o.rotation_euler=normal.to_track_quat('Z','Y').to_euler();o.data.materials.append(bronze)
 o.select_set(False)
for i,f in enumerate([crown]+[lame_func(i) for i in range(3)]):
 for t in [-.91,.91]:rivet('LP_Rivet_Plate_%d_%s'%(i,t),f(t,.59)+Vector((0,math.copysign(.002,t),0)),(cos(t*2),sin(t*2),.1))
for s in [-1,1]:
 for k in [2,7,12,17]:rivet('LP_Rivet_Leather_%s_%s'%(s,k),liner(s*.73,k/18)+Vector((-.003,0,0)),(-1,0,0),.0023)

# Sparse short scratches are geometry, complementing the fine material grain.
random.seed(42)
for layer,f in enumerate([crown]+[lame_func(i) for i in range(3)]):
 for k in range(20):
  t=random.uniform(-.88,.88);v=random.uniform(.16,.87);dt=random.uniform(.008,.035);dv=random.uniform(.015,.045)
  ps=[f(t,v),f(t+dt,v+dv)]
  ps=[p+Vector((cos(t*2),sin(t*2),.25))*.001 for p in ps]
  tube('LP_Wear_%d_%02d'%(layer,k),ps,.00010,wear,3)

# Join minor hardware by material family for a clean asset hierarchy.
def join_prefix(prefix,newname):
 objs=[o for o in col.objects if o.type=='MESH' and o.name.startswith(prefix)]
 if not objs:return
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();objs[0].name=newname;bpy.ops.object.select_all(action='DESELECT')
join_prefix('LP_Wear_','LP_11_Subtle_Battle_Scratches')
join_prefix('LP_Rivet_','LP_12_Plate_And_Strap_Rivets')
root['fit']='Left shoulder position from Assassin_Skeleton upperarm_l; character preserved in original scenes'
bpy.context.view_layer.update()
print('CREATED',len(col.objects),'objects')
