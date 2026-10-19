"""Refine the current Blender assassin in place: continuous torso, human hands, hooded hair, unmasked face."""
import bpy,os,sys,math,random,json,shutil
from mathutils import Vector
from math import sin,cos,pi
random.seed(112)
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
source=os.path.join(OUT,'assassin_refined.blend');backup=os.path.join(OUT,'backups','before_anatomy_fix');os.makedirs(backup,exist_ok=True)
for n in ['assassin_refined.blend','assassin_refined.glb']:
    if not os.path.exists(os.path.join(backup,n)):shutil.copy2(os.path.join(OUT,n),os.path.join(backup,n))
bpy.ops.wm.open_mainfile(filepath=os.path.join(backup,'assassin_refined.blend'))
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;scene.frame_set(1);rig.data.pose_position='REST'
collection=bpy.data.collections.new('ASSASSIN • anatomy and natural silhouette');scene.collection.children.link(collection);created=[]
def mat(prefix):return next(m for m in bpy.data.materials if m.name.startswith(prefix))
skin=mat('REF • warm face');leather=mat('REF • chestnut');dark=mat('REF • dark padded');hair=mat('REF • honey');hairlight=mat('REF • blond strand');hairdark=mat('REF • dark blond');hoodmat=mat('REF • charcoal burgundy');thread=mat('REF • flax');brass=mat('REF • old brass');shadow=mat('REF • eye creases');eye_white=mat('REF • muted eye');iris=mat('REF • blue grey')
def simplemat(name,color,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
lips=simplemat('Anatomy • natural lip tone',(.32,.15,.11));nails=simplemat('Anatomy • natural fingernails',(.55,.37,.26),.44)
def place(o,name,material,bone=None):
    o.name=name;o.data.materials.clear();o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o)
    if bone:
        o.vertex_groups.clear();o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig
        m=o.modifiers.new('Assassin deformation','ARMATURE');m.object=rig
    created.append(o);return o
def uv(o):
    layer=o.data.uv_layers.new(name='Anatomy UV')
    for p in o.data.polygons:
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;layer.data[li].uv=(v.x*3+v.y*.8,v.z*3)
def ell(name,pos,scale,material,bone=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return place(o,name,material,bone)
def mesh(name,verts,faces,material,bone=None):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);collection.objects.link(o);place(o,name,material,bone);uv(o);return o
def tube(name,points,radii,material,bone=None,sides=12):
    vs=[]
    for j,p in enumerate(points):
        tangent=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized();u=tangent.cross(Vector((0,0,1)))
        if u.length<.01:u=tangent.cross(Vector((0,1,0)))
        u.normalize();v=tangent.cross(u);r=radii[j];a,b=(r,r) if isinstance(r,(int,float)) else r
        for k in range(sides):vs.append(Vector(p)+u*cos(k*2*pi/sides)*a+v*sin(k*2*pi/sides)*b)
    fs=[tuple(range(sides-1,-1,-1))]
    for j in range(len(points)-1):
        for k in range(sides):fs.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    fs.append(tuple((len(points)-1)*sides+k for k in range(sides)))
    return mesh(name,vs,fs,material,bone)
def line(name,a,b,r,material,bone='chest'):return tube(name,[a,b],[r,r],material,bone,8)
def fuse(objects,name,material,bone=None,voxel=.003):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=objects[0]
    rem=o.modifiers.new('Continuous anatomical surface','REMESH');rem.mode='VOXEL';rem.voxel_size=voxel;bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=o.modifiers.new('Organic transitions','SMOOTH');sm.factor=.6;sm.iterations=4;bpy.ops.object.modifier_apply(modifier=sm.name)
    dec=o.modifiers.new('Surface reduction','DECIMATE');dec.ratio=.6;bpy.ops.object.modifier_apply(modifier=dec.name)
    place(o,name,material,bone);uv(o);return o
remove=('Face mask','Mask •','Eye •','Stern blond eyebrow','Eyebrow hair','Head','Neck','Swept honey','Fine hair ridge','Swept temple','Blond crown','Fingerless glove','Gloved finger','Bare fingertip','Glove stitched','Opposing thumb','Fitted padded','Jerkin •','Crossed chestnut harness','Harness • double','Harness buckle','Hood stitched','Hood •','Hood | lining')
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.startswith(remove):bpy.data.objects.remove(o,do_unlink=True)
# A single lofted torso connects the shoulders, ribcage, abdomen and hip line.
levels=[(1.055,.196,.139),(1.10,.196,.137),(1.18,.175,.125),(1.28,.188,.143),(1.40,.216,.153),(1.50,.235,.143),(1.56,.233,.122),(1.605,.105,.075),(1.64,.075,.060)]
ns=48;vs=[];fs=[]
for z,width,depth in levels:
    for k in range(ns):
        a=k*2*pi/ns;x=width*cos(a);y=depth*sin(a)
        # Subtle pectoral fullness, without a separate oval chest object.
        if y<0:y-=.009*math.exp(-((z-1.44)/.11)**2)*(1-(x/width)**2)
        vs.append((x,y,z))
for row in range(len(levels)-1):
    for k in range(ns):fs.append((row*ns+k,row*ns+(k+1)%ns,(row+1)*ns+(k+1)%ns,(row+1)*ns+k))
fs.extend([tuple(range(ns-1,-1,-1)),tuple((len(levels)-1)*ns+k for k in range(ns))])
torso=mesh('Continuous fitted leather torso',vs,fs,leather)
sub=torso.modifiers.new('Smooth tailored torso','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=torso;bpy.ops.object.modifier_apply(modifier=sub.name)
for name in ['pelvis','lower_spine','mid_spine','chest']:torso.vertex_groups.new(name=name)
for vertex in torso.data.vertices:
    z=vertex.co.z;centers=[1.06,1.17,1.34,1.52];weights=[math.exp(-((z-c)/.11)**2) for c in centers];total=sum(weights)
    for n,w in zip(['pelvis','lower_spine','mid_spine','chest'],weights):torso.vertex_groups[n].add([vertex.index],w/total,'REPLACE')
mod=torso.modifiers.new('Blended spine deformation','ARMATURE');mod.object=rig;torso.parent=rig
# Hide the covered original torso all the way to its side seams.
import bmesh
body=bpy.data.objects.get('Eliber | fitted continuous body')
if body:
    bm=bmesh.new();bm.from_mesh(body.data);faces=[]
    for f in bm.faces:
        p=body.matrix_world@f.calc_center_median()
        if 1.065<p.z<1.615 and abs(p.x)<.253:faces.append(f)
    bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(body.data);bm.free()
def front(x,z,offset=.004):
    for i in range(len(levels)-1):
        if levels[i][0]<=z<=levels[i+1][0]:
            t=(z-levels[i][0])/(levels[i+1][0]-levels[i][0]);w=levels[i][1]*(1-t)+levels[i+1][1]*t;d=levels[i][2]*(1-t)+levels[i+1][2]*t;break
    else:w,d=.2,.14
    return (x,-d*math.sqrt(max(.04,1-(x/w)**2))-.009*math.exp(-((z-1.44)/.11)**2)-offset,z)
for sign in [-1,1]:
    pts=[front(sign*(.19-.34*t),1.555-.40*t,.012) for t in [i/18 for i in range(19)]]
    tube('Fitted diagonal leather harness',pts,[(.023,.009)]*len(pts),dark,'chest')
    for i in range(19):
        t=i/18;x=sign*(.19-.34*t);z=1.555-.40*t
        line('Harness fine stitching',front(x-.013,z,.023),front(x-.009,z+.005,.023),.0012,thread)
    for x in [sign*.165]:
        pts=[front(x,1.16+i*.035,.006) for i in range(11)];tube('Tailored side seam',pts,[.0015]*len(pts),dark,'chest',6)
# Sculpt a continuous face with nose, jaw and cheek transitions beneath the hood.
faceparts=[ell('skull',(0,.008,1.804),(.100,.087,.143),skin),ell('jaw',(0,-.002,1.717),(.078,.070,.064),skin),ell('chin',(0,-.025,1.686),(.042,.033,.024),skin),ell('continuous neck',(0,.018,1.655),(.060,.060,.100),skin)]
for s in [-1,1]:faceparts.append(ell('cheek',(s*.052,-.037,1.778),(.032,.027,.032),skin))
faceparts.extend([ell('nose bridge',(0,-.073,1.802),(.013,.018,.036),skin),ell('nose tip',(0,-.093,1.772),(.018,.022,.015),skin)])
face=fuse(faceparts,'Unmasked sculpted face',skin,'head',.0022)
for s in [-1,1]:
    cutter=ell('temporary eye socket cutter',(s*.042,-.067,1.825),(.027,.021,.016),skin)
    boolean=face.modifiers.new('Sculpted orbital recess','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
    bpy.context.view_layer.objects.active=face;bpy.ops.object.modifier_apply(modifier=boolean.name);bpy.data.objects.remove(cutter,do_unlink=True)
# Boolean-created orbital vertices must be rigidly attached to the head too.
face.vertex_groups.clear();face.vertex_groups.new(name='head').add(list(range(len(face.data.vertices))),1,'REPLACE')
for s in [-1,1]:
    ell('Natural eye white',(s*.042,-.064,1.825),(.021,.008,.0075),eye_white,'head')
    ell('Blue grey iris',(s*.042,-.072,1.825),(.006,.002,.0065),iris,'head')
    ell('Eye pupil',(s*.042,-.074,1.825),(.0028,.001,.0044),shadow,'head')
    tube('Upper eyelid',[(s*.022,-.068,1.828),(s*.041,-.074,1.832),(s*.062,-.062,1.830)],[.002,.003,.0015],skin,'head')
    tube('Lower eyelid',[(s*.022,-.068,1.823),(s*.041,-.074,1.819),(s*.062,-.062,1.825)],[.0015,.002,.001],skin,'head')
    tube('Natural blond eyebrow',[(s*.019,-.081,1.842),(s*.040,-.086,1.848),(s*.066,-.073,1.844)],[.002,.004,.001],hairdark,'head')
    ell('Inset nostril',(s*.009,-.109,1.765),(.004,.0015,.002),shadow,'head')
ell('Upper lip',(0,-.074,1.731),(.031,.005,.0025),lips,'head')
ell('Lower lip',(0,-.075,1.725),(.029,.005,.0028),lips,'head')
tube('Mouth seam',[(-.028,-.077,1.728),(0,-.080,1.728),(.028,-.077,1.728)],[.0005,.0008,.0005],shadow,'head',6)
# Smooth the existing hood and add a dark inner lining; keep hair inside its opening.
hood=bpy.data.objects.get('Hood | open faceted shell')
if hood:
    bpy.context.view_layer.objects.active=hood
    sub=hood.modifiers.new('Soft fabric hood shape','SUBSURF');sub.levels=2
    bpy.ops.object.modifier_move_up(modifier=sub.name)
    bpy.ops.object.modifier_apply(modifier=sub.name)
    for p in hood.data.polygons:p.use_smooth=True
    hood.name='Hood | soft fitted cloth shell'
    lining=hood.copy();lining.data=hood.data.copy();collection.objects.link(lining);lining.name='Hood | dark inner lining'
    center=Vector((0,.045,1.83))
    for v in lining.data.vertices:
        world=lining.matrix_world@v.co;v.co=lining.matrix_world.inverted()@(center+(world-center)*.972)
    lining.data.materials.clear();lining.data.materials.append(dark)
    created.append(lining)
# Several broad, asymmetric locks grow from a scalp cap hidden inside the hood.
capverts=[];capfaces=[]
for row in range(12):
    t=.04+row/11*1.31
    for k in range(40):
        a=k*2*pi/40;capverts.append((.102*sin(t)*cos(a),.016+.084*sin(t)*sin(a),1.91+.060*cos(t)))
for row in range(11):
    for k in range(40):capfaces.append((row*40+k,row*40+(k+1)%40,(row+1)*40+(k+1)%40,(row+1)*40+k))
capfaces.append(tuple(range(39,-1,-1)))
mesh('Hair • scalp beneath hood',capverts,capfaces,hair,'head')
def bezier(points,t):
    a,b,c,d=[Vector(p) for p in points];return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
for j,(rootx,tipx,tipz) in enumerate([(-.067,-.094,1.847),(-.035,-.074,1.884),(-.005,-.038,1.900),(.026,.007,1.906),(.057,.053,1.884),(.078,.099,1.846)]):
    controls=[(rootx,.034,1.933),(rootx-.006,-.018,1.968),(tipx-.025,-.105,1.956),(tipx,-.106,tipz)]
    pts=[bezier(controls,i/23) for i in range(24)]
    radii=[]
    for i in range(24):
        t=i/23;width=.014+.009*sin(pi*t)
        if t>.62:width*=max(.035,(1-t)/.38)
        radii.append((width,.0065*(.5+.5*sin(pi*t))))
    tube('Hair • falling swept lock %02d'%j,pts,radii,hair,'head',16)
    for strand in [-1,0,1]:
        strands=[]
        for i,p in enumerate(pts):
            t=i/23;strands.append(p+Vector((strand*.005*(1-t),-.006,.002)))
        tube('Hair • fine lengthwise strand',strands,[.00065]*len(pts),hairlight if strand==0 else hairdark,'head',5)
# Five-finger hands with fused thenar pads and knuckles, plus articulated grip bones.
specs={};newhands=[];attachments=[]
for sign,side in [(1,'R'),(-1,'L')]:
    pieces=[ell('human palm',(sign*.490,-.058,.994),(.045,.028,.059),skin),ell('tapered wrist',(sign*.476,-.048,1.035),(.035,.028,.037),skin),ell('thenar pad',(sign*.458,-.048,.989),(.026,.026,.039),skin)]
    chains=[]
    for digit,offset,length,radius in [('Index',-.031,.098,.012),('Middle',-.009,.114,.0128),('Ring',.014,.105,.012),('Little',.035,.081,.010)]:
        x=sign*(.49+offset);z=.953+(0 if digit!='Little' else .008)
        p=[Vector((x,-.057,z)),Vector((x+sign*offset*.09,-.058,z-length*.44)),Vector((x+sign*offset*.12,-.044,z-length*.78)),Vector((x+sign*offset*.12,-.029,z-length))]
        names=[]
        for j in range(3):
            name=f'grip_{digit.lower()}.{j+1:02d}.{side}';names.append(name);specs[name]=(p[j],p[j+1],f'hand.{side}' if j==0 else names[j-1])
            pieces.append(tube('finger shaft',[p[j],p[j+1]],[radius*(1-j*.12),radius*(.9-j*.12)],skin,None,14))
            pieces.append(ell('anatomical joint',p[j],(radius,radius,radius*.96),skin))
        pieces.append(ell('rounded fingertip',p[-1],(radius*.70,radius*.70,radius*.8),skin));chains.extend(names)
        # Flat nails sit on the dorsal surface and follow the last phalanx.
        pos=p[-1]+Vector((0,-radius*.72,.006))
        nail=ell('Fingernail • '+digit+'.'+side,pos,(radius*.53,.0018,.009),nails)
        attachments.append((nail,names[-1]))
    p=[Vector((sign*.458,-.049,1.005)),Vector((sign*.429,-.053,.980)),Vector((sign*.422,-.072,.956)),Vector((sign*.437,-.089,.943))]
    names=[]
    for j in range(3):
        name=f'grip_thumb.{j+1:02d}.{side}';names.append(name);specs[name]=(p[j],p[j+1],f'hand.{side}' if j==0 else names[j-1]);r=.018-j*.003
        pieces.append(tube('thumb shaft',[p[j],p[j+1]],[r,r*.85],skin,None,14));pieces.append(ell('thumb joint',p[j],(r,)*3,skin))
    pieces.append(ell('thumb tip',p[-1],(.012,)*3,skin));chains.extend(names)
    hand=fuse(pieces,'Human hand • continuous palm and fingers.'+side,skin,None,.0024)
    newhands.append((hand,side,chains,sign))
    # A thin, fitted glove panel follows the hand instead of forming a box.
    glove=hand.copy();glove.data=hand.data.copy();collection.objects.link(glove);glove.name='Fingerless glove • fitted dorsal panel.'+side
    bm=bmesh.new();bm.from_mesh(glove.data)
    discard=[]
    for f in bm.faces:
        p=glove.matrix_world@f.calc_center_median()
        if p.y>-.061 or p.z<.960 or p.z>1.024:discard.append(f)
    bmesh.ops.delete(bm,geom=discard,context='FACES');bm.to_mesh(glove.data);bm.free()
    for v in glove.data.vertices:v.co+=v.normal*.0015
    place(glove,glove.name,leather,f'hand.{side}')
    sol=glove.modifiers.new('Thin glove leather','SOLIDIFY');sol.thickness=.0015
    tube('Soft glove wrist cuff.'+side,[(sign*.472,-.046,1.046),(sign*.481,-.052,1.022)],[.039,.038],dark,f'hand.{side}',24)
# Add new, consistently named finger joints while leaving the original animation skeleton intact.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b,parent) in specs.items():
    bone=rig.data.edit_bones.new(name);bone.head=a;bone.tail=b;bone.parent=rig.data.edit_bones[parent];bone.align_roll(Vector((0,-1,0)))
bpy.ops.object.mode_set(mode='OBJECT')
def distance(p,a,b):
    d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-a-t*d).length
for hand,side,chains,sign in newhands:
    names=[f'hand.{side}']+chains
    for n in names:hand.vertex_groups.new(name=n)
    for v in hand.data.vertices:
        p=hand.matrix_world@v.co;ds=[]
        for n in names:
            if n.startswith('hand.'):
                a,b=Vector((sign*.481,-.052,1.04)),Vector((sign*.49,-.058,.965))
            else:a,b,_=specs[n]
            ds.append((distance(p,a,b),n))
        ds.sort();near=ds[:2];weights=[1/(d+.004)**4 for d,n in near];total=sum(weights)
        for (d,n),w in zip(near,weights):hand.vertex_groups[n].add([v.index],w/total,'REPLACE')
    mod=hand.modifiers.new('Finger and palm deformation','ARMATURE');mod.object=rig;hand.parent=rig
for o,n in attachments:
    o.vertex_groups.new(name=n).add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;mod=o.modifiers.new('Follows distal finger','ARMATURE');mod.object=rig
for side in ['R','L']:
    key='HandGrip.'+side;rig[key]=0.;rig.id_properties_ui(key).update(min=0,max=1,description='Human hand grip: relaxed to curled. Adjust to the held object.')
    for name in specs:
        if not name.endswith('.'+side):continue
        pb=rig.pose.bones[name];pb.rotation_mode='XYZ';d=pb.driver_add('rotation_euler',0).driver;d.type='SCRIPTED';var=d.variables.new();var.name='grip';var.type='SINGLE_PROP';var.targets[0].id=rig;var.targets[0].data_path=f'["{key}"]'
        sign=1 if rig.data.bones[name].matrix_local.col[0].xyz.x>0 else -1
        d.expression=f'grip*{sign*(.6 if "thumb" in name else .9)}'
# Export and render from the same preserved source and rig.
rig.data.pose_position='POSE';scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
assert not any(o.name.startswith(('Face mask','Mask •')) for o in meshes)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
notes=bpy.data.texts.new('ANATOMY UPDATE • unmasked assassin')
notes.write('Current preferences: hood retained, mask removed, no weapons.\nContinuous spine-weighted fitted torso.\nHuman five-finger hands: HandGrip.R / HandGrip.L custom controls on the rig, plus independent grip_ finger bones.\nThese Blender drivers must be baked for game grip animation.\nHair roots sit beneath a smoothed hood with inner lining.\nPrior source in backups/before_anatomy_fix.\n')
cam=scene.camera
def camera(pos,target,scale):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
camera((3,-6,3),(0,0,1.02),2.5)
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.cycles.samples=32
scene.render.filepath=os.path.join(OUT,'refined_preview.png');bpy.ops.wm.save_as_mainfile(filepath=source);bpy.ops.render.render(write_still=True)
camera((1,-3,2.03),(0,-.02,1.82),.56);scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.filepath=os.path.join(OUT,'reference_head_detail.png');bpy.ops.render.render(write_still=True)
camera((1.4,-2.6,1.25),(.48,-.065,.96),.35);scene.render.filepath=os.path.join(OUT,'reference_hand_detail.png');bpy.ops.render.render(write_still=True)
camera((-3,5,2.8),(0,0,1.06),2.5);scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.filepath=os.path.join(OUT,'reference_rear.png');bpy.ops.render.render(write_still=True)
for o in meshes:o.data.calc_loop_triangles()
report={'mesh_objects':len(meshes),'triangles':sum(len(o.data.loop_triangles) for o in meshes),'bones':len(rig.data.bones),'hood_retained':True,'mask_retained':False,'weapons_included':False,'continuous_torso':True,'hand_digits':5,'grip_properties':['HandGrip.L','HandGrip.R']}
with open(os.path.join(OUT,'reference_update_report.json'),'w') as f:json.dump(report,f,indent=2)
print('ANATOMY_COMPLETE',json.dumps(report))
