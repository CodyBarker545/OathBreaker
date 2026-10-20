"""Shared Blender authoring utilities for reference-based Eliber character assets."""
import bpy,os,math,random,json,shutil,bmesh
from mathutils import Vector
from math import sin,cos,pi
ROOT=r'D:\SoftwareEng\Game'
BASE=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin','assassin_refined.blend')
KEEP=('Eliber | fitted continuous body','Continuous fitted leather torso','Unmasked sculpted face','Human hand •','Fingerless glove •','Fingernail •','Natural eye white','Blue grey iris','Eye pupil','Upper eyelid','Lower eyelid','Natural blond eyebrow','Inset nostril','Upper lip','Lower lip','Mouth seam','Face | ear','Soft glove wrist cuff','Boot | shaped leather upper','Boot | welted outsole','Boot | articulated ankle cuff')
class Character:
 def __init__(self,slug,title,runtime,reference):
  self.slug=slug;self.title=title;self.runtime=runtime;self.out=os.path.join(ROOT,'SourceAssets','characters',slug);os.makedirs(self.out,exist_ok=True)
  bpy.ops.wm.open_mainfile(filepath=BASE)
  if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
  self.rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');self.rig.name=title+' • Eliber deformation rig';self.rig.data.pose_position='REST';bpy.context.scene.frame_set(1)
  for o in list(bpy.data.objects):
   if o!=self.rig and not (o.type=='MESH' and o.name.startswith(KEEP)):bpy.data.objects.remove(o,do_unlink=True)
  self.collection=bpy.data.collections.new(title+' • character');bpy.context.scene.collection.children.link(self.collection)
  self.equipment=bpy.data.collections.new(title+' • removable equipment');bpy.context.scene.collection.children.link(self.equipment)
  for o in list(bpy.context.scene.objects):
   for col in list(o.users_collection):col.objects.unlink(o)
   self.collection.objects.link(o)
  # Reduce excessive source density while retaining the anatomical hand and face shapes.
  for o in list(self.collection.objects):
   if o.type!='MESH':continue
   ratio=.24 if o.name=='Unmasked sculpted face' else (.42 if o.name.startswith('Human hand') else (.40 if o.name.startswith(('Continuous fitted','Fingernail')) else 1))
   if ratio<1:
    bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Shared base surface reduction','DECIMATE');mod.ratio=ratio
    while o.modifiers.find(mod.name)>0:bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
   o['provenance']='Eliber CC0 fitted base / shared anatomical refinement'
  self.body=bpy.data.objects['Eliber | fitted continuous body'];self.torso=bpy.data.objects['Continuous fitted leather torso'];self.face=bpy.data.objects['Unmasked sculpted face']
  self.reference=os.path.join(self.out,'reference.png');shutil.copy2(reference,self.reference)
  self.palette={};random.seed(sum(ord(x) for x in slug))
 def mat(self,name,color,metal=0,rough=.8,kind='cloth',emission=0):
  m=bpy.data.materials.new(self.title+' • '+name);m.use_nodes=True;m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
  bs.inputs['Sheen Weight'].default_value=.035 if kind=='cloth' else 0
  size=192;im=bpy.data.images.new(m.name+' albedo',width=size,height=size);pixels=[]
  for y in range(size):
   for x in range(size):
    f=.93+random.uniform(-.045,.045)+.045*sin(x*.16+sin(y*.12))*cos(y*.13)
    if kind=='cloth':f+=.025*sin(x*pi)+.025*cos(y*pi)
    if kind=='mail':
     dx=(x/12+(y//10%2)*.5)%1-.5;dy=(y%10)/10-.5;r=math.sqrt(dx*dx+dy*dy);f*=.36 if r<.25 else (1.45 if r<.40 else .52)
    if kind=='metal' and random.random()<.004:f+=.20
    pixels.extend([max(0,min(1,c*f)) for c in color]+[1])
  im.pixels=pixels;im.pack();t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color'])
  if kind in ['cloth','mail','leather']:
   bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22 if kind=='mail' else .12;bump.inputs['Distance'].default_value=.005
   m.node_tree.links.new(t.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
  if emission:
   bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=emission
  self.palette[name]=m;return m
 def bind(self,o,bone='chest',spine=False):
  o.vertex_groups.clear()
  if spine:
   names=['pelvis','lower_spine','mid_spine','chest']
   for n in names:o.vertex_groups.new(name=n)
   for v in o.data.vertices:
    z=(o.matrix_world@v.co).z;w=[math.exp(-((z-c)/.11)**2) for c in [1.06,1.17,1.34,1.52]];total=sum(w)
    for n,q in zip(names,w):o.vertex_groups[n].add([v.index],q/total,'REPLACE')
  else:o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
  o.parent=self.rig;mod=o.modifiers.new('Shared character skeleton','ARMATURE');mod.object=self.rig
 def mesh(self,name,vs,fs,mat,bone='chest',spine=False,smooth=True,equipment=False):
  d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);(self.equipment if equipment else self.collection).objects.link(o);d.materials.append(mat)
  uv=d.uv_layers.new(name='Character UV')
  for p in d.polygons:
   p.use_smooth=smooth
   for li in p.loop_indices:
    v=d.vertices[d.loops[li].vertex_index].co;uv.data[li].uv=(v.x*3+v.y,v.z*3)
  if bone:self.bind(o,bone,spine)
  return o
 def ell(self,name,pos,scale,mat,bone='chest',equipment=False):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=pos);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
  for col in list(o.users_collection):col.objects.unlink(o)
  (self.equipment if equipment else self.collection).objects.link(o)
  for p in o.data.polygons:p.use_smooth=True
  self.bind(o,bone);return o
 def tube(self,name,pts,radii,mat,bone='chest',sides=12,equipment=False):
  vs=[]
  for j,p in enumerate(pts):
   t=(Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(j-1,0)])).normalized();u=t.cross(Vector((0,0,1)))
   if u.length<.01:u=t.cross(Vector((0,1,0)))
   u.normalize();v=t.cross(u);r=radii[j];a,b=(r,r) if isinstance(r,(int,float)) else r
   for k in range(sides):vs.append(Vector(p)+u*cos(k*math.tau/sides)*a+v*sin(k*math.tau/sides)*b)
  fs=[tuple(range(sides-1,-1,-1))]
  for j in range(len(pts)-1):
   for k in range(sides):fs.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
  fs.append(tuple((len(pts)-1)*sides+k for k in range(sides)))
  return self.mesh(name,vs,fs,mat,bone,equipment=equipment)
 def line(self,name,a,b,r,mat,bone='chest',equipment=False):return self.tube(name,[a,b],[r,r],mat,bone,8,equipment)
 def box(self,name,pos,size,mat,bone='pelvis',bevel=.005,equipment=False):
  bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  mod=o.modifiers.new('Soft worked edges','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
  o.data.materials.append(mat)
  for col in list(o.users_collection):col.objects.unlink(o)
  (self.equipment if equipment else self.collection).objects.link(o);self.bind(o,bone);return o
 def plate(self,name,outline,peak,mat,bone='chest',rim=None,spine=False,equipment=False):
  n=len(outline);vs=[Vector(p) for p in outline]+[Vector(p)+Vector((0,.006,0)) for p in outline]+[Vector(peak)];fs=[]
  for i in range(n):fs.extend([(i,(i+1)%n,2*n),(i,n+i,n+(i+1)%n,(i+1)%n)])
  fs.append(tuple(range(2*n-1,n-1,-1)))
  o=self.mesh(name,vs,fs,mat,bone,spine,False,equipment)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  bevel=o.modifiers.new('Forged edge bevel','BEVEL');bevel.width=.0025;bevel.segments=2
  if rim:self.tube(name+' rim',list(outline)+[outline[0]],[.0028]*(n+1),rim,bone,7,equipment)
  return o
 def front(self,x,z,offset=.008):
  hit,p,n,i=self.torso.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
  return Vector((x,p.y-offset if hit else -.15-offset,z))
 def set_base(self,cloth,leather,skin=None):
  self.torso.data.materials.clear();self.torso.data.materials.append(cloth)
  for o in self.collection.objects:
   if o.type!='MESH':continue
   if o.name.startswith(('Boot |','Fingerless glove','Soft glove')):o.data.materials.clear();o.data.materials.append(leather)
   if o==self.body:
    for i in range(len(o.data.materials)):o.data.materials[i]=cloth
   if skin and o.name.startswith(('Unmasked','Human hand','Face |','Upper eyelid','Lower eyelid')):o.data.materials.clear();o.data.materials.append(skin)
 def belt(self,mat,trim,z=1.10):
  pts=[(.203*cos(k/72*math.tau),.160*sin(k/72*math.tau),z+.012*cos(k/72*math.tau)) for k in range(73)]
  self.tube('Broad waist belt',pts,[(.010,.024)]*len(pts),mat,'pelvis')
  self.box('Belt buckle',(0,-.180,z),(.086,.019,.062),trim);self.box('Buckle leather inset',(0,-.193,z),(.056,.009,.037),mat)
  for sign in [-1,1]:
   self.box('Leather utility pouch',(sign*.22,.005,z-.06),(.075,.080,.12),mat)
   self.box('Pouch flap',(sign*.22,-.040,z-.025),(.083,.014,.044),mat)
   self.ell('Pouch clasp',(sign*.22,-.052,z-.045),(.005,.003,.005),trim,'pelvis')
 def harness(self,mat,trim):
  for sign in [-1,1]:
   pts=[self.front(sign*(.17-.31*t),1.56-.39*t,.016) for t in [i/18 for i in range(19)]]
   o=self.tube('Cross-body leather baldric',pts,[(.006,.025)]*len(pts),mat);self.bind_spine_existing(o)
   p=self.front(sign*.075,1.43,.030);self.box('Baldric buckle',p,(.054,.014,.044),trim,'chest')
 def bind_spine_existing(self,o):
  for m in list(o.modifiers):
   if m.type=='ARMATURE':o.modifiers.remove(m)
  self.bind(o,spine=True)
 def sleeves(self,mat,wide=.08):
  for sign,side in [(1,'R'),(-1,'L')]:
   bridge=self.tube('Continuous shoulder cloth bridge.'+side,[(sign*.115,0,1.565),(sign*.20,0,1.57),(sign*.265,0,1.56)],[wide*.98,wide*1.12,wide*1.10],mat,'chest',20)
   bridge.vertex_groups.clear();bridge.vertex_groups.new(name='chest');bridge.vertex_groups.new(name='upper_arm.'+side)
   for v in bridge.data.vertices:
    w=max(0,min(1,(abs(v.co.x)-.12)/.145));bridge.vertex_groups['chest'].add([v.index],1-w,'REPLACE');bridge.vertex_groups['upper_arm.'+side].add([v.index],w,'REPLACE')
   self.tube('Fitted upper sleeve.'+side,[(sign*.255,0,1.56),(sign*.32,-.003,1.43),(sign*.38,-.005,1.29)],[wide*1.12,wide,wide*.85],mat,'upper_arm.'+side,20)
   self.tube('Fitted lower sleeve.'+side,[(sign*.38,-.005,1.29),(sign*.43,-.028,1.16),(sign*.47,-.045,1.055)],[wide*.85,wide*.82,wide*.64],mat,'forearm.'+side,20)
 def robe(self,name,mat,zbottom=.34,top=.99,radius=.31,bones=None,ragged=True):
  # Open, folded skirt surface with waist fitting and a naturally flared uneven hem.
  rows=18;cols=64;vs=[];fs=[]
  for j in range(rows):
   t=j/(rows-1);rx=.20+(radius-.20)*t;ry=.142+(.17 if radius>.34 else .10)*t
   for k in range(cols):
    a=k/cols*math.tau;ripple=.012*sin(a*8+t*.7)*t+.006*sin(a*13)*t
    z=top+(zbottom-top)*t
    if j==rows-1 and ragged:z+=random.uniform(0,.045)+(.045 if k%9==0 else 0)
    vs.append(((rx+ripple)*cos(a),(ry+ripple)*sin(a),z))
  for j in range(rows-1):
   for k in range(cols):
    if ragged and j>=rows-3 and k in [2,17,33,49]:continue
    fs.append((j*cols+k,(j+1)*cols+k,(j+1)*cols+(k+1)%cols,j*cols+(k+1)%cols))
  o=self.mesh(name,vs,fs,mat,'pelvis');sol=o.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.004
  if bones:
   o.vertex_groups.clear()
   for n in bones:o.vertex_groups.new(name=n)
   for v in o.data.vertices:
    t=(v.index//cols)/(rows-1);w=t*(len(bones)-1);a=min(len(bones)-2,int(w));f=w-a
    o.vertex_groups[a].add([v.index],1-f,'REPLACE');o.vertex_groups[a+1].add([v.index],f,'REPLACE')
  return o
 def panel(self,name,mat,points,width=.13,bonechain=None,ragged=True):
  rows=19;cols=13;vs=[];fs=[]
  for j in range(rows):
   t=j/(rows-1);a,b,c,d=[Vector(p) for p in points];p=(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
   for k in range(cols):
    u=k/(cols-1)*2-1;q=p+Vector((u*width*(.75+.25*t),.014*cos(u*pi*3)*sin(t*pi),0))
    if j==rows-1 and ragged:q.z+=random.uniform(0,.075)
    vs.append(q)
  for j in range(rows-1):
   for k in range(cols-1):
    if ragged and j>rows-4 and k in [2,8]:continue
    fs.append((j*cols+k,(j+1)*cols+k,(j+1)*cols+k+1,j*cols+k+1))
  o=self.mesh(name,vs,fs,mat,None);chain=bonechain or ['pelvis','tabard_front.00','tabard_front.01','tabard_front.02']
  for n in chain:o.vertex_groups.new(name=n)
  for v in o.data.vertices:
   w=(v.index//cols)/(rows-1)*(len(chain)-1);a=min(len(chain)-2,int(w));f=w-a;o.vertex_groups[a].add([v.index],1-f,'REPLACE');o.vertex_groups[a+1].add([v.index],f,'REPLACE')
  o.parent=self.rig;arm=o.modifiers.new('Existing cloth chain','ARMATURE');arm.object=self.rig;sol=o.modifiers.new('Thin frayed cloth','SOLIDIFY');sol.thickness=.004
  return o
 def cowl(self,mat):
  vs=[];fs=[];cols=64;rows=9
  for j in range(rows):
   t=j/(rows-1)
   for k in range(cols):
    a=k/cols*math.tau;fold=.006*sin(t*pi*5+a)*sin(t*pi);rx=.11+.08*t;ry=.10+.055*t
    vs.append(((rx+fold)*cos(a),(ry+fold)*sin(a),1.706-.115*t-.07*t*max(0,-sin(a))**2))
  for j in range(rows-1):
   for k in range(cols):fs.append((j*cols+k,(j+1)*cols+k,(j+1)*cols+(k+1)%cols,j*cols+(k+1)%cols))
  o=self.mesh('Layered draped neck cowl',vs,fs,mat);sol=o.modifiers.new('Folded fabric thickness','SOLIDIFY');sol.thickness=.004
 def sun(self,name,pos,size,mat,bone='chest',equipment=False,normal='front'):
  x,y,z=pos;pts=[]
  for k in range(49):
   a=k/48*math.tau;pts.append((x+size*.49*cos(a),y,z+size*.49*sin(a)))
  self.tube(name+' circular seal',pts,[size*.045]*len(pts),mat,bone,7,equipment)
  for k in range(8):
   a=k/8*math.tau;self.line(name+' ray',(x+size*.62*cos(a),y,z+size*.62*sin(a)),(x+size*.90*cos(a),y,z+size*.90*sin(a)),size*.034,mat,bone,equipment)
  self.ell(name+' centre',(x,y,z),(size*.17,size*.07,size*.17),mat,bone,equipment)
 def finish(self,scale=(1,1,1)):
  self.rig.data.pose_position='POSE';self.rig.scale=scale;scene=bpy.context.scene;scene.frame_set(1)
  meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==self.rig for m in o.modifiers)]
  bpy.ops.object.select_all(action='DESELECT')
  for o in meshes+[self.rig]:o.select_set(True)
  bpy.context.view_layer.objects.active=self.rig
  # Blender height bump is not a tangent-space normal texture. Exclude it from glTF.
  normal_links=[];sheen_values=[]
  for mat in bpy.data.materials:
   if not mat.use_nodes:continue
   for node in mat.node_tree.nodes:
    if node.type=='BSDF_PRINCIPLED':
     sheen_values.append((node,node.inputs['Sheen Weight'].default_value));node.inputs['Sheen Weight'].default_value=0
     for link in list(node.inputs['Normal'].links):
      if link.from_node.type=='BUMP':normal_links.append((mat.node_tree,link.from_socket,link.to_socket));mat.node_tree.links.remove(link)
  glb=os.path.join(self.out,self.slug+'.glb');bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
  for tree,source,target in normal_links:tree.links.new(source,target)
  for node,value in sheen_values:node.inputs['Sheen Weight'].default_value=value
  runtime=os.path.join(ROOT,'Assets','Characters',self.runtime);os.makedirs(runtime,exist_ok=True);shutil.copy2(glb,os.path.join(runtime,self.runtime+'.glb'))
  # Neutral studio is a separate collection and excluded from the exported character.
  studio=bpy.data.collections.new('STUDIO • preview only');scene.collection.children.link(studio)
  ground=self.mat('studio slate',(.045,.052,.063),rough=.9,kind='stone')
  bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.90,depth=.075,location=(0,0,-.046));plinth=bpy.context.object;plinth.name='STUDIO • plinth';plinth.data.materials.append(ground)
  for c in list(plinth.users_collection):c.objects.unlink(plinth)
  studio.objects.link(plinth);bevel=plinth.modifiers.new('Rounded plinth','BEVEL');bevel.width=.03;bevel.segments=3
  bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.087));plane=bpy.context.object;plane.data.materials.append(ground)
  for c in list(plane.users_collection):c.objects.unlink(plane)
  studio.objects.link(plane)
  for name,pos,power,color,size in [('key',(-3,-4,5),500,(1,.90,.79),4),('fill',(4,-2,3),270,(.72,.83,1),3),('rim',(1,3,4),650,(.91,.95,1),3)]:
   data=bpy.data.lights.new('STUDIO • '+name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size;o=bpy.data.objects.new(data.name,data);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
  data=bpy.data.cameras.new('STUDIO • camera');cam=bpy.data.objects.new(data.name,data);studio.objects.link(cam);cam.location=(3.4,-6,3.0);cam.rotation_euler=(Vector((0,0,1.03))-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=2.7;scene.camera=cam
  scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(self.out,'preview.png')
  if scene.world:
   scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.12,.14,.18,1);bg.inputs[1].default_value=.5
  note=bpy.data.texts.new('START HERE • '+self.title);note.write(self.title+'\nBase: Eliber CC0 Rigged Base Mesh, fitted body with shared anatomical refinements. Original licence: ../_base/Eliber_Rigged_Base_Mesh/.\nOriginal Idle, Walk and Arm_Motion_Test actions retained. HandGrip.L/R controls are Blender drivers; bake held-item poses for game use.\nCharacter and removable equipment are separate collections. Studio is excluded from GLB.\nReference: reference.png\nPrototype: cloth collisions, final deformation polish and LOD optimisation remain production work.\n')
  bpy.ops.wm.save_as_mainfile(filepath=os.path.join(self.out,self.slug+'.blend'))
  report={'character':self.title,'base':'Eliber CC0 fitted mesh','rig_bones':len(self.rig.data.bones),'meshes':len(meshes),'actions':[a.name for a in bpy.data.actions],'source':self.slug+'.blend','export':self.slug+'.glb','reference':'reference.png'}
  with open(os.path.join(self.out,'asset_report.json'),'w') as f:json.dump(report,f,indent=2)
  bpy.ops.render.render(write_still=True)
  cam.location=(-3.3,5,2.8);cam.rotation_euler=(Vector((0,0,1.05))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(self.out,'rear.png');bpy.ops.render.render(write_still=True)
  print('CHARACTER_BUILT',json.dumps(report))
