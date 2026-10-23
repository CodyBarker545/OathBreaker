"""Local authored refinement of Meshy's pauldron silhouette; no generation calls."""
import bpy, bmesh, math, json, os
from mathutils import Vector

OUT='D:/SoftwareEng/Game/artifacts/meshy_left_pauldron/iterations/v002'
os.makedirs(OUT,exist_ok=True)
scene=bpy.data.scenes.new('Pauldron_v002_Refinement')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'
collection=bpy.data.collections.new('Pauldron_v002_Plates')
scene.collection.children.link(collection)
root=bpy.data.objects.new('Pauldron_v002',None);collection.objects.link(root)
root['iteration']='v002; locally rebuilt forged plates from Meshy v001 silhouette'
root['orientation']='Z up; outer armor -Y; inner shoulder cavity +Y. Character fit pending.'
root['approval']='Pending review'
parts=[]

def mat(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
steel=mat('V002_Blackened_Steel',(.065,.080,.098),.82,.34)
raised=mat('V002_Raised_Plate_Steel',(.095,.112,.135),.85,.30)
bronze=mat('V002_Aged_Bronze_Edges',(.28,.17,.078),.78,.35)
edge=mat('V002_Dark_Plate_Sides',(.025,.030,.038),.7,.42)
leather=mat('V002_Interior_Leather',(.027,.019,.016),0,.78)

def mesh(name,vs,fs,material,thick=0,bevel=0):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);collection.objects.link(ob);ob.parent=root
 me.materials.append(material);me.materials.append(edge)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if thick:
  score=sum(f.normal.dot(f.calc_center_median()-Vector((0,0,.215))) for f in bm.faces)
  if score<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(me);bm.free()
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 if thick:
  s=ob.modifiers.new('Forged plate thickness','SOLIDIFY');s.thickness=thick;s.offset=-1;s.material_offset=1
  bpy.ops.object.modifier_apply(modifier=s.name)
 if bevel:
  b=ob.modifiers.new('Crisp forged bevel','BEVEL');b.width=bevel;b.segments=1;b.limit_method='ANGLE';b.angle_limit=.6
  bpy.ops.object.modifier_apply(modifier=b.name)
 for p in me.polygons:p.use_smooth=True
 bm=bmesh.new();bm.from_mesh(me)
 for e in bm.edges:
  if len(e.link_faces)==2:e.smooth=e.calc_face_angle()<.6
 bm.to_mesh(me);bm.free()
 ob.select_set(False);parts.append(ob)
 return ob

def patch(name,fn,us,vs,material,thick=.003,bevel=.0006):
 verts=[fn(u,v) for v in vs for u in us];n=len(us)
 faces=[(j*n+i,(j+1)*n+i,(j+1)*n+i+1,j*n+i+1) for j in range(len(vs)-1) for i in range(n-1)]
 return mesh(name,verts,faces,material,thick,bevel)

def border(name,fn,material=bronze,width=.025):
 # Four narrow surface strips are integral overlays on the parent plate, not floating wires.
 for suffix,uf,vf in [('lower',lambda t:t,lambda t:1-width),('upper',lambda t:t,lambda t:0)]:
  patch(name+'_'+suffix,lambda u,v:Vector(fn(u,vf(u)+v*width))+Vector((0,.0012 if 'Rear' in name else -.0012,0)),[i/12 for i in range(13)],[0,1],material,.0012,0)
 for side in [0,1]:
  patch(name+'_side'+str(side),lambda u,v:Vector(fn(side*(1-width)+u*width,v))+Vector((0,-.0012,0)),[0,1],[i/4 for i in range(5)],material,.0012,0)

# A continuous, smooth shoulder cavity is covered by independent rigid plates.
def dome(name,rx,ry,height,zc,material,thick,theta=1.65):
 n=16;rings=5;verts=[(0,0,zc+height)];faces=[]
 for j in range(1,rings+1):
  p=theta*j/rings
  for i in range(n):
   a=2*math.pi*i/n;verts.append((rx*math.sin(p)*math.cos(a),ry*math.sin(p)*math.sin(a),zc+height*math.cos(p)))
 for i in range(n):faces.append((0,1+i,1+(i+1)%n))
 for j in range(rings-1):
  for i in range(n):
   a=1+j*n+i;b=1+j*n+(i+1)%n;faces.append((a,a+n,b+n,b))
 return mesh(name,verts,faces,material,thick,.0006)
shell=dome('01_Base_Shoulder_Shell',.102,.092,.080,.218,steel,.004)
lining=dome('02_Clean_Interior_Lining',.096,.086,.074,.217,leather,.002,1.60)

# Raised crown plate: broad, faceted, keeled, and stepped above the shell.
def crown(u,v):
 a=(u-.5)*2.8;p=.25+1.12*v
 x=.108*math.sin(p)*math.sin(a)
 y=-.100*math.sin(p)*math.cos(a)
 z=.230+.084*math.cos(p)+.006*(1-abs(2*u-1))
 # A central spear point makes the bottom edge recognizable at game distance.
 z-=.018*max(0,1-abs(u-.5)*4)**2*v**4
 return (x,y,z)
patch('03_Raised_Crown_Plate',crown,[i/12 for i in range(13)],[0,.25,.5,.75,1],raised,.004)
border('03_Crown_Bronze_Border',crown,width=.035)

# Three curved, overlapping chevron lames, progressively smaller toward the arm.
profiles=[(.113,.113,.246,.142,.028),(.098,.098,.180,.078,.023),(.079,.080,.112,.015,.018)]
for idx,(w,depth,top,bottom,notch) in enumerate(profiles):
 def lame(u,v,w=w,depth=depth,top=top,bottom=bottom,notch=notch):
  a=(u-.5)*3.10
  x=w*math.sin(a)*(1-.22*v)
  y=-depth*math.cos(a)-.006*max(0,1-abs(u-.5)*5)*math.sin(math.pi*v)
  # Central point, small side points, broad planar cheeks between them.
  center=abs(2*u-1)
  zb=bottom+.076*center**.7-.025*math.exp(-((center-.72)/.13)**2)
  zb+=.005*(2*u-1)
  z=(top+.014*center)*(1-v)+zb*v
  return (x,y,z)
 ob=patch('%02d_Overlapping_Chevron_Lame'%(4+idx),lame,[i/12 for i in range(13)],[0,.22,.55,1],steel if idx!=1 else raised,.0035)
 ob['construction']='Independent rigid overlapping plate; upper edge tucked beneath preceding plate'
 border('%02d_Lame_Border'%(4+idx),lame,width=.022)

# Tall swept rear collar retains the characteristic menacing silhouette.
def collar(u,v):
 a=(u-.5)*2.9;x=.115*math.sin(a)*(.85+.15*v)
 y=.042+.042*math.cos(a)+.014*v+.005*(1-abs(2*u-1))
 top=.244+.108*(1-abs(2*u-1))**.8
 z=.207*(1-v)+top*v
 return (x,y,z)
patch('07_Swept_Rear_Gorget_Plate',collar,[i/12 for i in range(13)],[0,.35,.7,1],steel,.004,.001)
border('07_Rear_Collar_Edge',collar,width=.035)

# Paired secondary side shields have deliberately unequal drop lengths.
for side in [-1,1]:
 def sideplate(u,v,side=side):
  x=side*(.079-.017*v+.008*math.sin(math.pi*u))
  y=.019+(.5-u)*.105*(1-.3*v)
  z=.221*(1-v)+(.120+.048*abs(2*u-1)-(.008 if side==1 else 0))*v
  return (x,y,z)
 patch('08_Secondary_Side_Plate_'+str(side),sideplate,[0,.25,.5,.75,1],[0,.3,.7,1],steel,.003,.0006)

def spike(name,base,tip,radius):
 base=Vector(base);tip=Vector(tip);axis=(tip-base).normalized()
 x=axis.cross(Vector((0,1,0))).normalized();y=axis.cross(x).normalized()
 n=6;verts=[]
 for center,r in [(base,radius),(base+(tip-base)*.28,radius*.72)]:
  for i in range(n):
   a=i*2*math.pi/n;verts.append(center+r*(x*math.cos(a)+y*math.sin(a)))
 verts.append(tip);faces=[tuple(range(n-1,-1,-1))]
 for i in range(n):faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n),(i+n,(i+1)%n+n,2*n)])
 mesh(name,verts,faces,raised,0,.0003)
 # Low, broad socket collar penetrates the supporting plate; no disconnected thorn roots.
 verts=[]
 for d,r in [(-.002,radius*1.38),(.003,radius*1.25)]:
  for i in range(n):
   a=i*2*math.pi/n;verts.append(base+axis*d+r*(x*math.cos(a)+y*math.sin(a)))
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh(name+'_Forged_Socket',verts,faces,bronze,0,.0004)
spike('09_Outer_Crown_Spike',(.071,-.035,.282),(.109,-.047,.336),.015)
spike('10_Inner_Crown_Spike',(-.068,-.027,.286),(-.092,-.033,.325),.012)
spike('11_Forward_Blade_Spike',(.033,-.080,.280),(.043,-.112,.315),.011)

# Recessed support straps make the hollow shoulder opening intentional and wearable.
for s in [-1,1]:
 patch('12_Inner_Leather_Suspension_'+str(s),lambda u,v,s=s:(s*(.070-.007*v),-.059+.104*u,.223-.063*v),[0,.18,.82,1],[0,1],leather,.003,0)

# Preserve sharp macro facets; add UVs for later baked texture work.
for ob in parts:
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(island_margin=.025)
 bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
 bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Forged surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=40
 bpy.ops.object.modifier_apply(modifier=mod.name)

root['note']='One pauldron assembly with separate solid plate components. No Meshy requests or credits.'
scene.world=bpy.data.worlds.new('V002_Studio_World');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.12,.14,.18,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.35
for name,loc,power,size in [('Key',(.4,-.6,.8),35,.65),('Fill',(-.45,-.3,.4),18,.55),('Rim',(.2,.5,.6),45,.45)]:
 data=bpy.data.lights.new('V002_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.18))-ob.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('V002_Review_Camera');cam=bpy.data.objects.new('V002_Review_Camera',camdata);scene.collection.objects.link(cam)
cam.location=(.48,-.73,.42);cam.rotation_euler=(Vector((0,0,.185))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=.46;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=OUT+'/pauldron_v002_three_quarter.png'
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False
   sp.region_3d.view_location=Vector((0,0,.18));sp.region_3d.view_distance=.65;sp.region_3d.view_rotation=Vector((1,-1,.5)).to_track_quat('Z','Y')
bpy.context.view_layer.update()
print('Created',len(parts),'solid components;',sum(len(o.data.polygons) for o in parts),'polygons')
print('Triangles',sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts))
