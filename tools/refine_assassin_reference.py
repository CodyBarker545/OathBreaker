"""Blender refinement of the existing assassin; preserves hood, mask and animation rig."""
import bpy, math, random, os, shutil, json
from mathutils import Vector
from math import sin,cos,pi
random.seed(73)
ROOT=r'D:\SoftwareEng\Game'
OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
source=os.path.join(OUT,'assassin_refined.blend')
backup=os.path.join(OUT,'backups','before_blonde_reference');os.makedirs(backup,exist_ok=True)
for filename in ['assassin_refined.blend','assassin_refined.glb']:
    target=os.path.join(backup,filename)
    if not os.path.exists(target):shutil.copy2(os.path.join(OUT,filename),target)
shutil.copy2(r'C:\Users\cody_\Downloads\Blonde Assassin Walk Cycle Atlas.png',os.path.join(OUT,'blonde_assassin_reference.png'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(backup,'assassin_refined.blend'))
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;scene.frame_set(1)
rig.data.pose_position='REST'
old_actions=[a.name for a in bpy.data.actions]
collection=bpy.data.collections.new('ASSASSIN • reference detail pass');scene.collection.children.link(collection)
added=[]
def material(name,color,metal=0,rough=.7,kind='leather'):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    n=256;im=bpy.data.images.new(name+' • packed albedo',width=n,height=n);pixels=[]
    for y in range(n):
        for x in range(n):
            noise=random.uniform(-.045,.045);broad=.025*sin(x*.14)*sin(y*.17)
            if kind=='cloth':noise+=.022*((x%2)*2-1)+.022*((y%2)*2-1)
            if kind=='metal':noise+=.025*sin(y*.43)+(.11 if random.random()<.003 else 0)
            shade=.94+noise+broad
            pixels.extend([max(0,min(1,c*shade)) for c in color]+[1])
    im.pixels=pixels;im.pack();tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.008
    m.node_tree.links.new(tex.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
steel=material('REF • worn silver steel',(.48,.52,.55),.78,.4,'metal')
edge=material('REF • polished worn edges',(.66,.69,.68),.8,.31,'metal')
brass=material('REF • old brass fittings',(.48,.31,.13),.7,.48,'metal')
leather=material('REF • chestnut leather',(.24,.13,.075),rough=.72)
darkleather=material('REF • dark padded leather',(.12,.085,.064),rough=.84)
red=material('REF • burgundy woven cloth',(.29,.045,.055),rough=.88,kind='cloth')
redlight=material('REF • burgundy raised seams',(.38,.075,.075),rough=.87,kind='cloth')
hoodmat=material('REF • charcoal burgundy hood',(.16,.065,.074),rough=.9,kind='cloth')
maskmat=material('REF • charcoal face wrap',(.11,.105,.11),rough=.89,kind='cloth')
thread=material('REF • flax saddle stitching',(.53,.38,.21),rough=.9,kind='cloth')
hair=material('REF • honey blond hair',(.49,.31,.13),rough=.6,kind='hair')
hairlight=material('REF • blond strand highlights',(.60,.40,.18),rough=.57,kind='hair')
hairdark=material('REF • dark blond roots',(.27,.16,.065),rough=.76,kind='hair')
skin=material('REF • warm face and fingertips',(.65,.43,.30),rough=.68)
shadow=material('REF • eye creases',(.055,.033,.024),rough=.9)
white=material('REF • muted eye whites',(.65,.64,.57),rough=.4)
iris=material('REF • blue grey eyes',(.13,.23,.27),rough=.36)
def bind(o,bone):
    o.vertex_groups.clear();o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
    o.parent=rig;mod=o.modifiers.new('Preserved assassin rig','ARMATURE');mod.object=rig
    return o
def finish(o,name,mat,bone='chest',smooth=True):
    o.name=name;o.data.materials.clear();o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=smooth
    if not o.data.uv_layers:
        uv=o.data.uv_layers.new(name='Detail UV')
        for p in o.data.polygons:
            for li in p.loop_indices:
                v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x*3+v.y*.6,v.z*3)
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o);bind(o,bone);added.append(o);return o
def ell(name,pos,scale,mat,bone='chest',seg=24,rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=pos);o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,bone)
def mesh(name,vs,fs,mat,bone='chest'):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);collection.objects.link(o);return finish(o,name,mat,bone)
def tube(name,points,radii,mat,bone='chest',sides=10):
    vs=[]
    for j,p in enumerate(points):
        t=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized();u=t.cross(Vector((0,0,1)))
        if u.length<.01:u=t.cross(Vector((0,1,0)))
        u.normalize();v=t.cross(u);r=radii[j];a,b=(r,r) if isinstance(r,(int,float)) else r
        for k in range(sides):vs.append(Vector(p)+u*cos(k*2*pi/sides)*a+v*sin(k*2*pi/sides)*b)
    fs=[tuple(range(sides-1,-1,-1))]
    for j in range(len(points)-1):
        for k in range(sides):fs.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    fs.append(tuple((len(points)-1)*sides+k for k in range(sides)))
    return mesh(name,vs,fs,mat,bone)
def line(name,a,b,r,mat,bone='chest'):return tube(name,[a,b],[r,r],mat,bone)
def box(name,pos,scale,mat,bone='pelvis',bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Rounded leather or forged edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o,name,mat,bone)
# Keep the user's hood and mask; replace the old angular armour and fringe.
remove_prefix=('Ash blond fringe','Side hair','Brow','Amber iris','Eye socket','Breastplate','Abdominal lame','Shoulder lame','Shoulder spike','Vambrace','Knee diamond','Ridged shin armour','Hip tasset','Cross-body harness','Belt pouch','Scarf | long torn','Scarf | wind-swept','Waist | torn','Waist | narrow','Glove.')
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.startswith(remove_prefix):bpy.data.objects.remove(o,do_unlink=True)
# Replace the covered torso surface to prevent the older faceted body poking through the jerkin.
import bmesh
body=bpy.data.objects.get('Eliber | fitted continuous body')
if body:
    bm=bmesh.new();bm.from_mesh(body.data)
    covered=[]
    for face in bm.faces:
        c=body.matrix_world@face.calc_center_median()
        if 1.16<c.z<1.61 and abs(c.x)<.22:covered.append(face)
    bmesh.ops.delete(bm,geom=covered,context='FACES');bm.to_mesh(body.data);bm.free()
for o in bpy.data.objects:
    if o.type!='MESH' or not any(mod.type=='ARMATURE' for mod in o.modifiers):continue
    for slot in o.material_slots:
        if not slot.material:continue
        n=slot.material.name
        if o.name.startswith('Hood'):
            slot.material=thread if 'rim' in o.name else hoodmat
        elif o.name=='Face mask':slot.material=maskmat
        elif n.startswith('Cloth'):slot.material=red if 'raised' not in n else redlight
        elif n.startswith('Leather'):slot.material=darkleather
        elif n.startswith('Trim'):slot.material=brass
        elif n.startswith('Armour'):slot.material=steel
        elif n.startswith('Skin'):slot.material=skin
    if o.name in ['Head','Neck']:
        for p in o.data.polygons:p.use_smooth=True
# Expressive upper face remains visible above the retained mask.
for s in [-1,1]:
    ell('Eye • almond whites',(s*.043,-.099,1.827),(.023,.007,.007),white,'head')
    ell('Eye • blue grey iris',(s*.043,-.106,1.827),(.0065,.002,.0065),iris,'head')
    ell('Eye • pupil',(s*.043,-.108,1.827),(.003,.001,.0048),shadow,'head')
    tube('Eye • shaped upper lid',[(s*.020,-.099,1.828),(s*.037,-.107,1.832),(s*.055,-.104,1.833),(s*.066,-.092,1.83)],[.002,.003,.003,.0015],skin,'head')
    tube('Eye • lower lid',[(s*.020,-.099,1.825),(s*.043,-.106,1.821),(s*.066,-.092,1.826)],[.0015,.0025,.001],skin,'head')
    tube('Stern blond eyebrow',[(s*.016,-.102,1.844),(s*.040,-.106,1.851),(s*.070,-.090,1.849)],[.003,.0045,.0015],hairdark,'head')
# Swept locks are curved solid ribbons; fine strands run along each lock.
ell('Blond crown beneath the hood',(0,.015,1.915),(.108,.091,.080),hairdark,'head')
def bezier(a,b,c,d,t):return (1-t)**3*Vector(a)+3*(1-t)**2*t*Vector(b)+3*(1-t)*t*t*Vector(c)+t**3*Vector(d)
for j in range(9):
    x=-.094+j*.023
    variation=random.uniform(-.008,.008)
    controls=[(x,-.082,1.903+.025*(1-abs(x)/.10)+variation),(min(.10,x+.037),-.12,1.963+variation),(min(.104,x+.045),-.010,2.005+variation),(x+.003,.07,1.95)]
    pts=[bezier(*controls,k/17) for k in range(18)]
    radii=[(.009+.009*sin(k/17*pi),.005+.006*sin(k/17*pi)) for k in range(18)]
    tube('Swept honey blond lock %02d'%j,pts,radii,hair,'head',12)
    for strand in [-1,1]:
        linepts=[p+Vector((strand*.0035,-.006,.005)) for p in pts]
        tube('Fine hair ridge %02d'%j,linepts,[.0008]*len(pts),hairlight if strand==1 else hairdark,'head',5)
for s in [-1,1]:
    for j in range(4):
        pts=[(s*(.084+j*.008),-.060,1.923-j*.012),(s*(.104+j*.006),-.092,1.876-j*.015),(s*(.101+j*.006),-.081,1.825-j*.012)]
        tube('Swept temple lock',pts,[(.012,.010),(.013,.009),(.001,.002)],hair,'head')
# Mask seams and cloth creases follow the original mask silhouette.
for s in [-1,1]:
    tube('Mask • stitched upper seam',[(0,-.151,1.79),(s*.045,-.148,1.782),(s*.086,-.123,1.79)],[.0025]*3,thread,'head',6)
    for j in range(4):
        z=1.704+j*.016
        tube('Mask • compressed fabric fold',[(s*.008,-.151,z),(s*.052,-.145,z+.006),(s*.084,-.125,z+.015)],[.002,.0035,.001],maskmat,'head',6)
    for j in range(9):
        z=1.69+j*.029;x=s*(.126 if z<1.89 else .126-(z-1.89)*.7);y=-.083 if z<1.89 else -.07
        line('Hood • visible saddle stitch',(x-.003,y-.006,z),(x+.003,y-.006,z+.009),.0016,thread,'head')
    tube('Hood • fabric edge fold',[(s*.145,.005,1.69),(s*.15,-.01,1.83),(s*.13,.003,1.94),(s*.065,.035,2.01)],[.005,.008,.007,.002],hoodmat,'head')
# Leather cuirass, padded sleeves and shorter layered skirt instead of faceted plates.
ell('Fitted padded leather jerkin',(0,.003,1.365),(.23,.18,.238),leather)
def chest_surface(x,z):
    y=.003-.18*math.sqrt(max(.025,1-(x/.23)**2-((z-1.365)/.238)**2))-.003
    return (x,y,z)
for row in range(4):
    z=1.23+row*.065
    for col in range(4):
        x=-.137+col*.09
        pts=[chest_surface(x-.035,z),chest_surface(x,z+.032),chest_surface(x+.035,z),chest_surface(x,z-.032),chest_surface(x-.035,z)]
        tube('Jerkin • quilted diamond seam',pts,[.0013]*5,darkleather,'chest',5)
for s,label in [(1,'R'),(-1,'L')]:
    upper=f'upper_arm.{label}';fore=f'forearm.{label}';thigh=f'thigh.{label}';shin=f'shin.{label}';foot=f'foot.{label}'
    tube('Quilted leather sleeve.'+label,[(s*.254,0,1.56),(s*.318,-.002,1.43),(s*.38,-.005,1.29)],[.09,.084,.07],darkleather,upper,20)
    tube('Padded thigh.'+label,[(s*.12,0,1.04),(s*.145,-.008,.83),(s*.16,-.015,.65)],[.107,.102,.079],darkleather,thigh,20)
    # Dished overlapping shoulder plates, each with a rolled edge and rivets.
    for j in range(3):
        cx=s*(.273+j*.035);z=1.595-j*.058;rx=.128-j*.014;ry=.126-j*.007
        # Partial ellipsoid shell, open below the arm rather than a complete ball.
        vs=[];fs=[];nr=6;ns=24
        for row in range(nr):
            t=.12+(row/(nr-1))*1.44
            for k in range(ns):
                a=k*2*pi/ns;vs.append((cx+rx*sin(t)*cos(a),ry*sin(t)*sin(a),z+.09*cos(t)))
        for row in range(nr-1):
            for k in range(ns):fs.append((row*ns+k,row*ns+(k+1)%ns,(row+1)*ns+(k+1)%ns,(row+1)*ns+k))
        fs.append(tuple(range(ns-1,-1,-1)))
        o=mesh('Dished shoulder lame.'+label,vs,fs,steel,upper)
        sol=o.modifiers.new('Forged shell thickness','SOLIDIFY');sol.thickness=.009;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name)
        path=[(cx+rx*cos(k*2*pi/32),ry*sin(k*2*pi/32),z) for k in range(33)]
        tube('Rolled shoulder rim.'+label,path,[.004]*len(path),edge,upper,6)
        for k in range(5):
            a=pi+pi*(k+.5)/5;ell('Shoulder brass rivet',(cx+rx*.91*cos(a),ry*.99*sin(a)-.003,z+.018),(.008,.006,.008),brass,upper,12,8)
    # Thick leather vambrace, steel reinforcing strips and closure straps.
    tube('Leather bracer.'+label,[(s*.39,-.015,1.275),(s*.43,-.028,1.16),(s*.472,-.045,1.065)],[.075,.077,.060],leather,fore,20)
    for j in range(3):
        z=1.10+j*.061;x=s*(.46-j*.025)
        box('Bracer steel splint',(x,-.104,z),(.105,.025,.043),steel,fore,.009)
        for dx in [-.037,.037]:ell('Bracer rivet',(x+dx,-.121,z),(.006,.003,.006),brass,fore,12,8)
    ell('Rounded steel kneecap',(s*.162,-.093,.637),(.086,.060,.092),steel,shin)
    for dx in [-.061,.061]:ell('Knee rivet',(s*.162+dx,-.132,.638),(.007,.004,.007),brass,shin,12,8)
    # Boots retain the existing shaped foot mesh, with taller leather and real laces.
    tube('Tall leather boot shaft.'+label,[(s*.18,.005,.16),(s*.175,.005,.31),(s*.17,0,.48)],[.078,.083,.076],leather,shin,20)
    for j in range(6):
        z=.20+j*.043
        for k in [-1,1]:
            ell('Boot lace eyelet',(s*.176+k*.026,-.079,z),(.005,.003,.005),brass,shin,10,6)
        line('Crossed boot lace',(s*.176-.026,-.084,z),(s*.176+.026,-.086,z+.035),.0025,thread,shin)
        line('Crossed boot lace',(s*.176+.026,-.084,z),(s*.176-.026,-.086,z+.035),.0025,thread,shin)
    # Human fingerless gloves: separate curled fingers and opposing thumb, no weapons.
    hc=(s*.49,-.06,1.005)
    ell('Fingerless glove palm.'+label,hc,(.057,.047,.068),leather,'hand.'+label)
    for j in range(4):
        x=s*(.454+j*.025);z=.969
        pts=[(x,-.065,z),(x,-.080,z-.035),(x,-.103,z-.052),(x,-.116,z-.038)]
        tube('Gloved finger.'+label,pts[:3],[.015,.014,.012],darkleather,'hand.'+label,12)
        ell('Bare fingertip.'+label,pts[-1],(.013,.017,.017),skin,'hand.'+label,16,10)
        ell('Glove stitched knuckle',(x,-.104,1.008),(.012,.008,.012),leather,'hand.'+label,12,8)
    tube('Opposing thumb.'+label,[(s*.447,-.063,1.027),(s*.424,-.088,1.006),(s*.438,-.123,.982)],[.023,.021,.015],skin,'hand.'+label,14)
# Diagonal belts, seam stitches, buckles and flatter, recognisable utility pouches.
for s in [-1,1]:
    pts=[(s*.18,-.083,1.56),(s*.10,-.158,1.45),(0,-.167,1.33),(-s*.14,-.145,1.18)]
    tube('Crossed chestnut harness',pts,[(.028,.013)]*4,leather)
    for j in range(14):
        t=j/13;x=s*(.16-.28*t);z=1.54-.35*t;y=-.17
        line('Harness • double saddle stitch',(x-.014,y-.009,z),(x-.009,y-.01,z+.005),.0015,thread)
    box('Harness buckle',(s*.07,-.185,1.40),(.060,.019,.05),brass,'chest',.006)
    box('Harness buckle inset',(s*.07,-.198,1.40),(.042,.006,.032),leather,'chest',.004)
    box('Utility pouch',(s*.203,-.103,1.06),(.108,.089,.125),leather,'pelvis',.018)
    box('Pouch overlapping flap',(s*.203,-.158,1.10),(.116,.024,.058),darkleather,'pelvis',.012)
    ell('Pouch brass closure',(s*.203,-.175,1.085),(.009,.005,.009),brass,'pelvis',12,8)
    for j in range(6):
        z=1.015+j*.014
        for side in [-1,1]:line('Pouch seam stitch',(s*.203+side*.046,-.153,z),(s*.203+side*.046,-.153,z+.005),.0015,thread,'pelvis')
    # Small layered leather skirt panels with worn hem stitches.
    for j in range(3):
        x=s*(.065+j*.060);z=1.06-j*.015
        vs=[(x-.037,-.153,z),(x+.037,-.153,z),(x+.041,-.173,z-.19),(x+.010,-.18,z-.214),(x-.038,-.173,z-.19)]
        o=mesh('Scalloped leather skirt panel',vs,[(0,1,2,3,4)],leather,'pelvis');sol=o.modifiers.new('Leather thickness','SOLIDIFY');sol.thickness=.011;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name)
        for k in range(5):line('Tasset edge stitching',(x-.027+k*.013,-.182,z-.186),(x-.024+k*.013,-.182,z-.192),.0015,thread,'pelvis')
# Broad cloth cape with sculpted folds, split torn hem, and existing scarf-chain weights.
vs=[];fs=[];rows=16;cols=17
for j in range(rows):
    t=j/(rows-1);z=1.65-.76*t;cy=.14+.16*t
    for k in range(cols):
        u=k/(cols-1)*2-1;width=.13+.15*sin(t*pi*.75)
        x=u*width+.10*sin(t*pi);y=cy+.028*cos(u*pi*3)*(sin(t*pi)*.7+.3)
        zz=z+(.055*(sin(k*2.2)*.5+.5) if j==rows-1 else 0)
        vs.append((x,y,zz))
for j in range(rows-1):
    for k in range(cols-1):fs.append((j*cols+k,j*cols+k+1,(j+1)*cols+k+1,(j+1)*cols+k))
cape=mesh('Burgundy cape • folded split hem',vs,fs,red)
cape.vertex_groups.clear()
for n in ['scarf_back.00','scarf_back.01','scarf_back.02']:cape.vertex_groups.new(name=n)
for v in cape.data.vertices:
    z=v.co.z
    w=max(0,min(2,(1.58-z)/.29));a=int(min(1,w));t=w-a
    cape.vertex_groups[a].add([v.index],1-t,'REPLACE');cape.vertex_groups[a+1].add([v.index],t,'REPLACE')
sol=cape.modifiers.new('Fabric hem thickness','SOLIDIFY');sol.thickness=.007
# A few directional scuffs catch the light without covering the model in noise.
for s,label in [(1,'R'),(-1,'L')]:
    for j in range(5):
        x=s*(.22+j*.025);z=1.648-j*.008
        line('Pauldron wear scratch',(x,-.085,z),(x+.015,-.087,z+.007),.0012,edge,'upper_arm.'+label)
    for j in range(5):
        x=s*.18+(j-2)*.024
        ell('Boot welt stitch',(x,-.252,.046),(.0028,.002,.003),thread,'foot.'+label,8,6)
# Store notes and the reference alongside the Blender scene.
notes=bpy.data.texts.new('REFERENCE PASS • hood and mask retained')
notes.write('Reference: Blonde Assassin Walk Cycle Atlas.png\nUser choices: keep hood and mask, no weapons.\nDetail pass: swept blond locks/strands, expressive eyes, stitched mask and hood, dished steel shoulders, padded leather, laced boots, utility pouches, folded burgundy cape.\nOriginal rig and Idle/Walk/Arm_Motion_Test actions retained.\nPrior source and export: backups/before_blonde_reference.\n')
rig.data.pose_position='POSE';scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
cam=scene.camera
def aim(target):cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
cam.location=(3,-6,3);aim((0,0,1.02));cam.data.type='ORTHO';cam.data.ortho_scale=2.5
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'refined_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=source)
bpy.ops.render.render(write_still=True)
cam.location=(-3,5,2.8);aim((0,0,1.06));scene.render.filepath=os.path.join(OUT,'reference_rear.png');bpy.ops.render.render(write_still=True)
cam.location=(1.0,-3,2.1);aim((0,-.03,1.83));cam.data.ortho_scale=.59;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.filepath=os.path.join(OUT,'reference_head_detail.png');bpy.ops.render.render(write_still=True)
for o in meshes:o.data.calc_loop_triangles()
report={'mesh_objects':len(meshes),'triangles':sum(len(o.data.loop_triangles) for o in meshes),'bones':len(rig.data.bones),'actions':old_actions,'hood_retained':True,'mask_retained':True,'weapons_included':False}
with open(os.path.join(OUT,'reference_update_report.json'),'w') as f:json.dump(report,f,indent=2)
print('ASSASSIN_REFERENCE_COMPLETE',json.dumps(report))
