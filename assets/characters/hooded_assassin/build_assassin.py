"""Run with Blender: blender --background --python build_assassin.py.
Creates an editable, material-coloured prototype inspired by the supplied sheet.
Front is -Y, up is Z. Dimensions are metres. No external Python packages.
"""
import bpy
import math
import os
import random
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
random.seed(18)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection':
        bpy.data.collections.remove(c)
character = bpy.data.collections.new('ASSASSIN | editable character parts')
bpy.context.scene.collection.children.link(character)
studio = bpy.data.collections.new('STUDIO | excluded from model export')
bpy.context.scene.collection.children.link(studio)
parts = []

def material(name, rgb, metal=0, rough=.5):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    return m

steel = material('Armour | midnight steel', (.065,.077,.095), .8, .34)
edge = material('Trim | antique bronze', (.38,.24,.105), .78, .32)
leather = material('Leather | charcoal', (.023,.027,.034), .05, .64)
cloth = material('Cloth | oxblood crimson', (.23,.018,.032), 0, .82)
clothlight = material('Cloth | raised folds', (.34,.034,.045), 0, .8)
hoodmat = material('Hood | faded charcoal violet', (.05,.045,.067), 0, .86)
skin = material('Skin | warm pale', (.56,.37,.26), 0, .7)
hair = material('Hair | ash blond', (.55,.40,.23), .05, .63)
hairlight = material('Hair | pale strands', (.77,.62,.39), .03, .57)
blade = material('Blade | silver steel', (.48,.56,.64), .88, .21)
eye = material('Eyes | amber', (.78,.49,.14), .2, .3)
black = material('Eyes and seams | dark', (.008,.009,.012), 0, .6)

def register(obj, mat, bone='root'):
    obj.data.materials.append(mat)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    character.objects.link(obj)
    obj['bone'] = bone
    parts.append(obj)
    return obj

def mesh(name, verts, faces, mat, bone='root', bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    character.objects.link(obj)
    obj.data.materials.append(mat)
    obj['bone'] = bone
    parts.append(obj)
    if bevel:
        mod = obj.modifiers.new('Soft forged edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj

def ellipsoid(name, loc, scale, mat, bone='root', segments=12, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register(obj, mat, bone)

def link(name, a, b, r1, r2, mat, bone='root', vertices=10):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2,
                                  depth=(b-a).length, location=(a+b)/2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    return register(obj, mat, bone)

def ribbon(name, points, width, mat, bone='chest'):
    verts=[]
    for i, p in enumerate(points):
        p=Vector(p)
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        side=tangent.cross(Vector((0,-1,0))).normalized()*width/2
        verts.extend([p-side,p+side])
    return mesh(name,verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)],mat,bone)

def plate(name, points, bone, mat=steel, rim=True):
    # Faceted raised centre gives armour its forged ridge silhouette.
    points=[Vector(p) for p in points]
    centre=sum(points,Vector())/len(points)
    centre.y-=.027
    n=len(points)
    obj=mesh(name,points+[centre],[(i,(i+1)%n,n) for i in range(n)],mat,bone)
    solid=obj.modifiers.new('Plate thickness','SOLIDIFY'); solid.thickness=.012
    if rim:
        for i in range(n):
            link(name+' | bronze edge', points[i], points[(i+1)%n], .004,.004,edge,bone,6)
    return obj

# Body under the independently editable plates.
ellipsoid('Torso | leather undersuit',(0,0,1.35),(.245,.135,.32),leather,'chest')
ellipsoid('Pelvis | quilted cloth',(0,0,1.045),(.205,.13,.16),leather,'pelvis')
for s,side in [(-1,'L'),(1,'R')]:
    hip=(s*.12,0,1.06); knee=(s*.16,-.015,.61); ankle=(s*.18,.005,.16)
    shoulder=(s*.255,0,1.56); elbow=(s*.38,-.005,1.29); wrist=(s*.47,-.045,1.045)
    link('Thigh undersuit.'+side,knee,hip,.085,.108,leather,'thigh.'+side)
    link('Calf undersuit.'+side,ankle,knee,.055,.082,leather,'shin.'+side)
    ellipsoid('Boot.'+side,(s*.18,-.07,.09),(.08,.17,.085),leather,'foot.'+side)
    ellipsoid('Toe armour.'+side,(s*.18,-.17,.09),(.081,.09,.055),steel,'foot.'+side)
    link('Upper arm.'+side,elbow,shoulder,.064,.081,skin,'upper_arm.'+side)
    link('Forearm sleeve.'+side,wrist,elbow,.05,.064,leather,'forearm.'+side)
    ellipsoid('Glove.'+side,(s*.49,-.045,.995),(.052,.055,.08),leather,'hand.'+side)
    for j in range(3):
        z=.40+j*.11; x=s*(.18-(z-.16)*.045)
        link('Greave strap.'+side,(x,.0,z-.012),(x,.0,z+.012),.074,.074,edge,'shin.'+side)
    x=s*.16
    plate('Knee diamond.'+side,[(x,-.095,.73),(x+s*.085,-.09,.64),(x,-.13,.52),(x-s*.07,-.09,.63)],'shin.'+side)
    plate('Ridged shin armour.'+side,[(s*.16-.065,-.067,.56),(s*.16+.065,-.067,.56),(s*.18+.045,-.07,.18),(s*.18,-.12,.12),(s*.18-.045,-.07,.18)],'shin.'+side)
    # Three overlapping shoulder lames, widest at the top.
    for j in range(3):
        x=s*(.267+j*.031); z=1.615-j*.082; w=.105-j*.012
        plate('Shoulder lame %d.%s'%(j+1,side),[(x-s*w,-.09,z+.055),(x+s*w,-.055,z+.025),(x+s*(w+.015),-.095,z-.07),(x,-.15,z-.03),(x-s*w,-.11,z-.035)],'upper_arm.'+side)
    link('Shoulder spike.'+side,(s*.30,.015,1.65),(s*.37,.02,1.76),.034,0,edge,'upper_arm.'+side)
    plate('Vambrace.'+side,[(s*.39-.055,-.065,1.26),(s*.39+.055,-.065,1.26),(s*.48+.047,-.09,1.035),(s*.48,-.125,1.01),(s*.48-.047,-.09,1.035)],'forearm.'+side)
    link('Vambrace blade.'+side,(s*.43,.015,1.16),(s*.48,.015,1.36),.026,0,edge,'forearm.'+side)
    for z in [1.08,1.23]:
        t=(1.29-z)/.245; x=s*(.38+.09*t)
        link('Bracer band.'+side,(x,-.014,z-.013),(x,-.014,z+.013),.067,.067,edge,'forearm.'+side)
    # Outer thigh layered plates.
    for j in range(3):
        x=s*(.14+j*.013); z=1.02-j*.075
        plate('Hip tasset %d.%s'%(j,side),[(x-.075,-.13,z+.04),(x+.075,-.13,z+.04),(x+.085,-.13,z-.035),(x,-.17,z-.085),(x-.085,-.13,z-.035)],'thigh.'+side)

# Breastplate split into fitted facets and abdominal lames.
for s in [-1,1]:
    plate('Breastplate',[(s*.018,-.14,1.57),(s*.20,-.08,1.55),(s*.205,-.13,1.40),(s*.08,-.17,1.34),(s*.014,-.16,1.42)],'chest')
for j in range(3):
    z=1.34-j*.069
    plate('Abdominal lame %d'%j,[(-.175,-.125,z+.025),(.175,-.125,z+.025),(.16,-.145,z-.04),(0,-.17,z-.067),(-.16,-.145,z-.04)],'chest')
for s in [-1,1]:
    ribbon('Cross-body harness',[(s*.185,-.105,1.57),(s*.10,-.186,1.39),(-s*.15,-.16,1.17)],.034,leather)

# Belt, buckle and equipment pouches.
link('Wide belt',(0,0,1.075),(0,0,1.145),.215,.215,leather,'pelvis',16)
plate('Belt buckle',[(-.048,-.222,1.143),(.048,-.222,1.143),(.048,-.222,1.077),(-.048,-.222,1.077)],'pelvis',edge,False)
plate('Buckle inset',[(-.028,-.235,1.128),(.028,-.235,1.128),(.028,-.235,1.092),(-.028,-.235,1.092)],'pelvis',leather,False)
for s in [-1,1]:
    ellipsoid('Belt pouch',(s*.205,-.03,1.09),(.045,.08,.065),leather,'pelvis')
    for j in range(3):
        ellipsoid('Harness rivet',(s*(.075+j*.037),-.171,1.135-j*.006),(.008,.006,.008),edge,'pelvis',8,4)

# Face and mask. Eyes remain readable from the isometric view.
link('Neck',(0,0,1.54),(0,0,1.73),.07,.072,skin,'head')
ellipsoid('Head',(0,-.005,1.80),(.112,.10,.153),skin,'head',16,12)
for s in [-1,1]:
    ellipsoid('Eye socket',(s*.043,-.098,1.825),(.033,.012,.012),black,'head')
    ellipsoid('Amber iris',(s*.042,-.11,1.825),(.008,.004,.008),eye,'head')
    link('Brow',(s*.018,-.104,1.846),(s*.07,-.095,1.85),.008,.005,hair,'head')
plate('Face mask',[(-.102,-.075,1.805),(-.055,-.112,1.797),(0,-.135,1.805),(.055,-.112,1.797),(.102,-.075,1.805),(.077,-.09,1.705),(0,-.122,1.682),(-.077,-.09,1.705)],'head',leather,False)

# Open hood shell: the cut rim frames the face rather than covering it.
verts=[]; faces=[]; count=17
hoodrings=[(1.65,.17,.145),(1.77,.174,.155),(1.91,.164,.145),(2.005,.075,.075)]
for z,rx,ry in hoodrings:
    for i in range(count):
        a=math.radians(-133+266*i/(count-1))
        verts.append((rx*math.sin(a),.025+ry*math.cos(a),z))
for j in range(len(hoodrings)-1):
    for i in range(count-1):
        a=j*count+i; faces.append((a,a+1,a+1+count,a+count))
verts.append((0,.025,2.035)); top=len(verts)-1
for i in range(count-1): faces.append((3*count+i,3*count+i+1,top))
obj=mesh('Hood | open faceted shell',verts,faces,hoodmat,'head')
mod=obj.modifiers.new('Cloth thickness','SOLIDIFY'); mod.thickness=.009
for k in [0,count-1]:
    for j in range(3): link('Hood stitched bronze rim',verts[j*count+k],verts[(j+1)*count+k],.003,.003,edge,'head',6)

# Sculpted pointed locks, each an individually editable wedge.
def lock(name, root, tip, width, mat):
    r,t=Vector(root),Vector(tip); mid=r.lerp(t,.47); mid.y-=.035
    v=[r+Vector((-width,0,0)),r+Vector((width,0,0)),mid+Vector((width*.65,0,0)),t,mid+Vector((-width*.65,0,0)),mid+Vector((0,-.028,.012))]
    return mesh(name,v,[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5)],mat,'head')
for i in range(12):
    x=-.105+i*.018
    root=(x*.45,-.066,1.965-random.random()*.015)
    tip=(x,-.122-random.random()*.02,1.815+random.random()*.067)
    if i in [3,4,8]: tip=(x-.025,-.147,1.775)
    lock('Ash blond fringe %02d'%i,root,tip,.023,hairlight if i%3==0 else hair)
for s in [-1,1]:
    for j in range(3):
        lock('Side hair', (s*.09,-.045,1.925-j*.02),(s*(.135+j*.007),-.077,1.76-j*.015),.022,hair)

# Scarf cowl consists of folded rings with an angular front drop.
for j in range(3):
    verts=[]
    for i in range(17):
        a=2*math.pi*i/16
        front=max(0,-math.sin(a))
        x=(.14+j*.013)*math.cos(a); y=(.12+j*.016)*math.sin(a)
        z=1.675-j*.036-front*.065
        verts.extend([(x,y,z+.025),(x*1.025,y*1.025,z-.025)])
    obj=mesh('Scarf | wrapped fold %d'%j,verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(16)],clothlight if j==1 else cloth,'chest')
    obj.modifiers.new('Woven thickness','SOLIDIFY').thickness=.006

def tail(name, points, widths, bone):
    verts=[]
    for i,(p,w) in enumerate(zip(points,widths)):
        x,y,z=p
        verts.extend([(x-w,y,z),(x,y-.018,z+.006),(x+w,y+.012,z-.018)])
    faces=[]
    for j in range(len(points)-1):
        a=j*3; faces.extend([(a,a+1,a+4,a+3),(a+1,a+2,a+5,a+4)])
    obj=mesh(name,verts,faces,cloth,bone)
    obj.modifiers.new('Fabric thickness','SOLIDIFY').thickness=.005
    return obj
tail('Scarf | long torn back banner',[(0,.145,1.65),(.03,.20,1.42),(.12,.25,1.14),(.22,.29,.86),(.31,.30,.53)],[.12,.13,.10,.08,.002],'chest')
tail('Scarf | wind-swept left ribbon',[(-.08,.12,1.65),(-.28,.18,1.58),(-.48,.21,1.62),(-.66,.20,1.53)],[.06,.055,.04,0],'chest')
tail('Waist | torn crimson tabard',[(.02,-.18,1.06),(.09,-.19,.91),(.16,-.17,.72),(.22,-.16,.47)],[.09,.10,.075,0],'pelvis')
tail('Waist | narrow torn strip',[(-.12,.05,1.10),(-.24,.08,.89),(-.31,.11,.67),(-.35,.13,.53)],[.07,.065,.04,0],'pelvis')

# Two curved, double-faceted daggers. Mesh outlines are actual geometry.
for s,side in [(-1,'L'),(1,'R')]:
    x=s*.50; y=-.07; z=.98; bone='hand.'+side
    link('Dagger grip.'+side,(x,y,z+.015),(x+s*.025,y,z-.13),.022,.022,leather,bone)
    for j in range(6):
        zz=z-.02-j*.02; xx=x+s*(z-zz)*.17
        link('Grip wrap.'+side,(xx,y,zz-.003),(xx,y,zz+.003),.024,.024,edge,bone,8)
    guardz=z-.14; gx=x+s*.027
    link('Dagger guard.'+side,(gx-.065,y,guardz+.012),(gx+.065,y,guardz-.012),.013,.013,edge,bone)
    link('Hooked guard.'+side,(gx+s*.065,y,guardz-.012),(gx+s*.095,y,guardz+.05),.014,0,edge,bone)
    outline=[(0,0),(-.045,-.06),(-.038,-.16),(.015,-.29),(.115,-.43),(.085,-.26),(.045,-.10),(.035,-.025)]
    ps=[(gx+s*dx,y,guardz+dz) for dx,dz in outline]
    mid=(gx+s*.025,y-.018,guardz-.19)
    n=len(ps)
    obj=mesh('Curved dagger blade.'+side,ps+[mid],[(i,(i+1)%n,n) for i in range(n)],blade,bone)
    obj.modifiers.new('Blade thickness','SOLIDIFY').thickness=.009
    for a,b in [(0,1),(1,2),(6,7)]: link('Dagger bronze spine.'+side,ps[a],ps[b],.005,.003,edge,bone,6)

# Beginner rig: segmented parts use rigid vertex weights. No auto-weight guesswork.
bpy.ops.object.armature_add(enter_editmode=True)
rig=bpy.context.object; rig.name='Assassin_Rig | rigid prototype weights'
for c in list(rig.users_collection): c.objects.unlink(rig)
character.objects.link(rig)
edit=rig.data.edit_bones
edit.remove(edit[0])
def bone(name,a,b,parent=None):
    bb=edit.new(name); bb.head=a; bb.tail=b
    if parent: bb.parent=edit[parent]
bone('root',(0,0,0),(0,0,.2))
bone('pelvis',(0,0,.95),(0,0,1.14),'root')
bone('chest',(0,0,1.14),(0,0,1.61),'pelvis')
bone('head',(0,0,1.61),(0,0,1.97),'chest')
for s,side in [(-1,'L'),(1,'R')]:
    bone('thigh.'+side,(s*.12,0,1.06),(s*.16,-.015,.61),'pelvis')
    bone('shin.'+side,(s*.16,-.015,.61),(s*.18,.005,.16),'thigh.'+side)
    bone('foot.'+side,(s*.18,.005,.16),(s*.18,-.16,.08),'shin.'+side)
    bone('upper_arm.'+side,(s*.255,0,1.56),(s*.38,-.005,1.29),'chest')
    bone('forearm.'+side,(s*.38,-.005,1.29),(s*.47,-.045,1.045),'upper_arm.'+side)
    bone('hand.'+side,(s*.47,-.045,1.045),(s*.50,-.06,.96),'forearm.'+side)
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front=True
for obj in parts:
    group=obj.vertex_groups.new(name=obj['bone'])
    group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    mod=obj.modifiers.new('Prototype skeleton','ARMATURE'); mod.object=rig
    obj.parent=rig
rig['reference']='https://chatgpt.com/s/m_6ad51238f2e48191a466b2054db3ca65'
rig['status']='Stylized segmented prototype; rigid weights; no animation or texture baking.'

# UVs are provided for later painting; visible colours currently use materials.
bpy.ops.object.select_all(action='DESELECT')
for obj in parts: obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.025)
bpy.ops.object.mode_set(mode='OBJECT')

# Export only the character, never the presentation plinth, lights or cameras.
rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'hooded_assassin.glb'),export_format='GLB',use_selection=True,export_animations=False)

def studio_obj(obj):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    studio.objects.link(obj)
    return obj

groundmat=material('Studio | slate',(.032,.043,.054),.25,.58)
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.79,depth=.08,location=(0,0,-.045))
obj=studio_obj(bpy.context.object); obj.name='Display plinth'; obj.data.materials.append(groundmat)
mod=obj.modifiers.new('Plinth bevel','BEVEL'); mod.width=.025; mod.segments=3
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.091))
obj=studio_obj(bpy.context.object); obj.data.materials.append(groundmat)

def aim(obj,point): obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,power,size,rgb):
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size; data.color=rgb
    obj=bpy.data.objects.new(name,data); studio.objects.link(obj); obj.location=location; aim(obj,(0,0,1.1))
area('Key | warm softbox',(-3,-4,5),550,4,(1,.83,.65))
area('Fill | cool softbox',(3,-2,3),350,3,(.62,.78,1))
area('Rim | crimson',(1,3,3.5),650,2,(1,.3,.22))
area('Top | pale',(-1,1,5),300,2,(.8,.85,1))
data=bpy.data.cameras.new('Portrait camera'); cam=bpy.data.objects.new('Portrait camera',data)
studio.objects.link(cam); cam.location=(3,-6,3.0); aim(cam,(0,0,1.0)); data.type='ORTHO'; data.ortho_scale=2.65
scene=bpy.context.scene; scene.camera=cam
scene.render.engine='CYCLES'; scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1000; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.world.color=(.15,.15,.15)
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath=os.path.join(OUT,'preview_front.png')
# Save an inviting material-coloured viewport.
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True); bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_distance=3.4
            ar.spaces.active.region_3d.view_location=(0,0,1)
            ar.spaces.active.shading.color_type='MATERIAL'
            ar.spaces.active.overlay.show_extras=False
scene['model_notes']='Approximation of reference, not a production sculpt. Separate parts, 16-bone rigid rig, smart UVs, material colours.'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'hooded_assassin.blend'))
bpy.ops.render.render(write_still=True)
cam.location=(3,5,2.8); aim(cam,(0,0,1.0))
scene.render.filepath=os.path.join(OUT,'preview_back.png')
bpy.ops.render.render(write_still=True)
print('CHARACTER COMPLETE:',len(parts),'mesh parts;',sum(len(o.data.polygons) for o in parts),'base polygons')
