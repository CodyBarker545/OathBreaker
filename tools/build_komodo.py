"""Build the reference-inspired Komodo warrior in Blender. Run with Blender -b -P."""
import bpy, math, random, os, json
from mathutils import Vector
from math import sin, cos, pi
random.seed(41)
ROOT=r'D:\SoftwareEng\Game'
OUT=os.path.join(ROOT,'SourceAssets','characters','komodo_axe_warrior')
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'SourceAssets','characters','_base','Eliber_Rigged_Base_Mesh','Lowpolymesh_Eliber.blend'))
base=bpy.data.objects['Base mesh']; base_copy=base.data.copy()
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for old_object in list(bpy.data.objects):bpy.data.objects.remove(old_object,do_unlink=True)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
parts=[]
def material(name, color, metallic=0, rough=.65, pattern=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Metallic'].default_value=metallic; bs.inputs['Roughness'].default_value=rough
    if pattern:
        n=256; im=bpy.data.images.new(name+'_albedo',width=n,height=n); pixels=[]
        for y in range(n):
            for x in range(n):
                grain=random.uniform(-.06,.06)
                if pattern=='scale':
                    u=(x/8+(y//6%2)*.5)%1; v=(y%6)/6
                    edge=(abs(u-.5)*1.35+abs(v-.5))>.63
                    shade=(.65 if edge else 1.0+.12*sin(v*pi))+grain
                elif pattern=='cloth': shade=.9+.07*sin(x*pi)+.07*cos(y*pi)+grain
                else: shade=.9+grain+.06*sin(x*.1)*sin(y*.13)
                pixels.extend([min(1,max(0,c*shade)) for c in color]+[1])
        im.pixels=pixels; im.pack(); tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=im
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        bump=m.node_tree.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.19; bump.inputs['Distance'].default_value=.025
        m.node_tree.links.new(tex.outputs['Color'],bump.inputs['Height']); m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
skin=material('01 • Ochre Komodo scales',(.39,.245,.085),pattern='scale')
goldskin=material('02 • Warm jaw and belly',(.64,.43,.17),pattern='scale')
darkskin=material('03 • Dorsal scutes',(.19,.14,.055),pattern='scale')
steel=material('04 • Hammered midnight iron',(.30,.34,.36),.68,.52,pattern='metal')
edge=material('05 • Worn silver cutting edges',(.49,.55,.54),.85,.28)
brass=material('06 • Tarnished bronze trim',(.48,.29,.09),.75,.37,pattern='metal')
cloth=material('07 • Oxblood woven cloth',(.32,.025,.032),pattern='cloth')
leather=material('08 • Scored dark leather',(.18,.105,.06),pattern='cloth')
bone=material('09 • Aged ivory claws',(.77,.66,.43),rough=.45)
black=material('10 • Mouth and pupils',(.014,.009,.006),rough=.4)
eye=material('11 • Amber eyes',(.95,.48,.025),.1,.22)
scar=material('12 • Pale healed scars',(.7,.49,.26),rough=.8)
def finish(o,name,mat,b='Spine',smooth=True):
    o.name=name; o.data.materials.clear(); o.data.materials.append(mat)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    o['bind_bone']=b; parts.append(o); return o
def ell(name,pos,scale,mat,b='Spine',seg=24,rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=pos); o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,b)
def mesh(name,vs,fs,mat,b='Spine',bevel=0):
    d=bpy.data.meshes.new(name); d.from_pydata(vs,[],fs); d.update(); o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o)
    uv=d.uv_layers.new(name='UVMap')
    for p in d.polygons:
        for li in p.loop_indices:
            v=d.vertices[d.loops[li].vertex_index].co; uv.data[li].uv=(v.x*1.7+v.y*.3,v.z*1.7)
    finish(o,name,mat,b)
    if bevel:
        mod=o.modifiers.new('Rounded forged edges','BEVEL'); mod.width=bevel; mod.segments=3
        bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.modifier_apply(modifier=mod.name); o.select_set(False)
    return o
def tube(name,points,radii,mat,b='Spine',sides=14):
    vs=[]
    for j,p in enumerate(points):
        tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        tangent.normalize(); u=tangent.cross(Vector((0,0,1)))
        if u.length<.01:u=tangent.cross(Vector((0,1,0)))
        u.normalize(); v=tangent.cross(u).normalized(); r=radii[j]; a,c=(r,r) if isinstance(r,(int,float)) else r
        for i in range(sides):vs.append(Vector(p)+u*cos(i*2*pi/sides)*a+v*sin(i*2*pi/sides)*c)
    fs=[tuple(range(sides-1,-1,-1))]
    for j in range(len(points)-1):
        for i in range(sides):fs.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
    fs.append(tuple((len(points)-1)*sides+i for i in range(sides)))
    return mesh(name,vs,fs,mat,b)
def rod(name,a,b,r,mat,bone_name='Spine',r2=None):return tube(name,[a,b],[r,r if r2 is None else r2],mat,bone_name)
def spike(name,a,b,r=.055,mat=bone,bn='Spine'):return rod(name,a,b,r,mat,bn,.003)
def box(name,pos,scale,mat,b='Spine',bev=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos); o=bpy.context.object; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); finish(o,name,mat,b)
    if bev:
        mod=o.modifiers.new('Soft bevel','BEVEL'); mod.width=bev; mod.segments=3; bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
# Reuse Eliber's torso and legs. The new head, arms, tail, costume and weapon are bespoke.
body=bpy.data.objects.new('Eliber • adapted torso and legs',base_copy); bpy.context.collection.objects.link(body)
for v in base_copy.vertices:
    x,y,z=v.co; v.co=(x*.235,y*.24,(z+5.9)*.19)
# Remove the human head and outstretched arms, retaining a fitted core.
import bmesh
bm=bmesh.new(); bm.from_mesh(base_copy)
remove=[v for v in bm.verts if v.co.z>1.78 or (abs(v.co.x)>.32 and v.co.z>1.48)]
bmesh.ops.delete(bm,geom=remove,context='VERTS'); bm.to_mesh(base_copy); bm.free()
finish(body,body.name,skin)
ell('Powerful chest',(0,.025,1.52),(.385,.24,.35),skin)
ell('Forward reptilian neck',(0,-.015,1.88),(.235,.22,.27),skin,'Head')
for i in range(7):ell('Overlapping belly plate %02d'%i,(0,-.216,1.12+i*.082),(.21+sin(i/7*pi)*.045,.037,.057),goldskin)
# Low, long Komodo skull, brows, lips, nostrils and visible slit pupils.
ell('Komodo cranium',(0,-.075,2.085),(.245,.27,.185),skin,'Head')
ell('Broad tapered muzzle',(0,-.36,2.075),(.215,.33,.100),goldskin,'Head')
ell('Dark lip seam',(0,-.352,2.015),(.216,.278,.017),black,'Head')
ell('Heavy lower jaw',(0,-.33,1.974),(.206,.269,.061),goldskin,'Head')
for s in [-1,1]:
    ell('Inset eye socket',(s*.202,-.215,2.164),(.061,.091,.063),darkskin,'Head')
    ell('Amber eye',(s*.238,-.242,2.168),(.025,.06,.034),eye,'Head')
    ell('Vertical slit pupil',(s*.26,-.258,2.17),(.008,.016,.028),black,'Head')
    rod('Heavy angular brow',(s*.16,-.324,2.205),(s*.245,-.135,2.22),.039,skin,'Head',.052)
    ell('Nostril',(s*.134,-.616,2.111),(.028,.024,.012),black,'Head')
    for j in range(4):spike('Small exposed tooth',(s*(.10+j*.022),-.48+j*.072,2.02),(s*(.105+j*.023),-.48+j*.072,1.986),.014,bone,'Head')
# Three diagonal scar ridges over the left cheek, distinctive from the other units.
for i in range(3):rod('Healed muzzle scar %d'%i,(-.215,-.365+i*.045,2.08),(-.228,-.285+i*.045,2.19),.008,scar,'Head',.005)
for j in range(6):ell('Cranial pebble scale',(0,.02+j*.024,2.26-j*.012),(.036,.04,.022),darkskin,'Head')
# Curved tail with an articulated skeleton below.
tailpts=[(0,.15,1.05),(0,.43,1.0),(.08,.75,.80),(.27,1.04,.55),(.55,1.24,.32),(.85,1.28,.23),(1.13,1.16,.29),(1.30,.99,.41)]
tail=tube('Long curved Komodo tail',tailpts,[.21,.19,.155,.125,.092,.06,.035,.004],skin,'Tail.01',20)
for j,p in enumerate(tailpts[1:-1]):
    r=[.19,.155,.125,.092,.06,.035][j]; spike('Tail dorsal scute',Vector(p)+Vector((0,0,r*.6)),Vector(p)+Vector((0,.015,r+ .07*(1-j/7))),r*.32,darkskin,'Tail.01' if j<2 else 'Tail.02')
for i in range(5):spike('Back dorsal ridge',(0,.215,1.4+i*.105),(0,.34,1.44+i*.105),.055,darkskin)
# Thick bent arms, gauntlets and clawed hands; keep an animation-friendly rest stance.
for s,label in [(-1,'R'),(1,'L')]:
    ell('Powerful scaled thigh '+label,(s*.215,.005,.78),(.175,.175,.28),skin,'Thigh.'+label)
    upper=(s*.35,.015,1.72); elbow=(s*.59,-.10,1.40); hand=(s*.66,-.38,1.14)
    tube('Muscular upper arm '+label,[upper,(s*.49,-.035,1.58),elbow],[.18,.175,.135],skin,'UpperArm.'+label)
    tube('Forearm '+label,[elbow,(s*.64,-.27,1.24),hand],[.145,.16,.115],skin,'Forearm.'+label)
    # Segmented forearm plates with bronze rails.
    for j in range(3):
        z=1.24+j*.066; y=-.36+j*.043
        ell('Forged bracer plate '+label,(s*.65,y,z),(.16,.105,.063),steel,'Forearm.'+label)
        rod('Bracer bronze seam '+label,(s*.65-.105,y-.09,z),(s*.65+.105,y-.09,z),.012,brass,'Forearm.'+label)
    # Shin guards, leather bindings and three large toes.
    for z in [.29,.61]:ell('Shin binding '+label,(s*.23,0,z),(.145,.13,.027),leather,'Shin.'+label)
    ell('Hammered greave '+label,(s*.23,-.14,.43),(.145,.075,.23),steel,'Shin.'+label)
    rod('Greave central ridge '+label,(s*.23,-.22,.24),(s*.23,-.225,.61),.017,brass,'Shin.'+label)
    ell('Broad reptilian foot '+label,(s*.25,-.155,.12),(.18,.26,.105),skin,'Foot.'+label)
    for k in range(3):
        x=s*.25+(k-1)*.11
        ell('Thick toe '+label,(x,-.34,.105),(.06,.13,.065),goldskin,'Foot.'+label)
        spike('Ivory toe talon '+label,(x,-.43,.11),(x,-.54,.065),.044,bone,'Foot.'+label)
# Asymmetrical layered pauldrons: broad riveted left, leather strapped right.
for s,label in [(-1,'R'),(1,'L')]:
    for j in range(3 if s==1 else 2):
        ell('Layered shoulder armour '+label,(s*(.39+j*.065),.005,1.80-j*.072),(.255-j*.035,.265-j*.014,.135),steel,'UpperArm.'+label)
        # Front embossed trim and individual rivets.
        rod('Shoulder trim '+label,(s*(.24+j*.065),-.22,1.81-j*.072),(s*(.55+j*.035),-.22,1.76-j*.072),.016,brass,'UpperArm.'+label)
        for k in range(3):ell('Shoulder rivet',(s*(.30+k*.09+j*.04),-.237,1.79-j*.072),(.019,.013,.019),brass,'UpperArm.'+label,12,8)
for j in range(3):spike('Ivory trophy on large pauldron',(.33+j*.12,.06,1.88),(.32+j*.16,.065,2.10-abs(j-1)*.05),.057,bone,'UpperArm.L')
# Hammer strikes and silver abrasions are modelled so they also survive the GLB export.
for s,l in [(-1,'R'),(1,'L')]:
    for j in range(5):
        x=s*(.32+.043*j);z=1.82-.045*(j%2)
        rod('Pauldron edge abrasion',(x,-.235,z),(x+s*.024,-.24,z+.014),.0035,edge,'UpperArm.'+l)
    for j in range(3):
        x=s*.23+(j-1)*.036
        rod('Greave nick',(x,-.213,.39+j*.055),(x+.027,-.216,.42+j*.055),.0035,edge,'Shin.'+l)
# Leather baldric follows chest contours; no floating straight strap.
tube('Diagonal leather baldric',[(-.28,-.18,1.77),(-.16,-.255,1.62),(0,-.265,1.43),(.19,-.21,1.20)],[(.062,.026)]*4,leather)
for i in range(6):ell('Baldric bronze stud',(-.24+i*.071,-.285,1.72-i*.085),(.013,.012,.013),brass,seg=12,rings=8)
ell('Wide leather belt',(0,0,1.075),(.335,.235,.082),leather,'Pelvis')
box('Bronze belt buckle',(0,-.249,1.09),(.155,.045,.13),brass,'Pelvis')
box('Buckle dark inset',(0,-.278,1.09),(.11,.018,.085),steel,'Pelvis')
# Tattered solid cloth panels, each with an outline and fold geometry.
for s in [-1,1]:
    vs=[(s*.025,-.245,1.04),(s*.25,-.20,1.04),(s*.30,-.23,.73),(s*.21,-.31,.61),(s*.12,-.32,.70),(s*.06,-.31,.59)]
    o=mesh('Split oxblood battle tabard',vs,[(0,1,2,3,4,5)],cloth,'Pelvis')
    sol=o.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.018
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=sol.name)
    rod('Raised tabard fold',(s*.13,-.255,1.02),(s*.19,-.328,.72),.014,cloth,'Pelvis',.004)
    rod('Bronze embroidered hem',(s*.07,-.325,.63),(s*.12,-.333,.73),.008,brass,'Pelvis')
for s in [-1,1]:
    o=mesh('Side skirt leather tasset',[(s*.24,-.10,1.05),(s*.34,.04,1.03),(s*.38,.04,.78),(s*.29,-.14,.76)],[(0,1,2,3)],leather,'Pelvis')
    sol=o.modifiers.new('Tasset thickness','SOLIDIFY');sol.thickness=.025
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name)
ell('Back oxblood cloth knot',(0,.25,1.06),(.13,.07,.09),cloth,'Pelvis')
# Broken-crown chest medallion: a personal heraldic mark.
ell('Broken crown chest medallion',(-.17,-.30,1.64),(.074,.025,.078),brass)
for x,z in [(-.205,1.66),(-.17,1.69),(-.135,1.65)]:rod('Crown emblem spike',(x,-.329,1.62),(x,-.329,z),.009,steel)
rod('Crown emblem baseline',(-.21,-.329,1.62),(-.13,-.329,1.62),.009,steel)
# Belt trophy: bone teeth tied with dark cord.
for j in range(3):
    x=.17+j*.057;rod('Trophy cord',(x,-.22,1.06),(x,-.28,.94-j*.025),.009,leather,'Pelvis')
    spike('Belt tooth trophy',(x,-.28,.95-j*.025),(x+.015,-.29,.84-j*.025),.032,bone,'Pelvis')
# Small actual geometry scale clusters catch the light at game viewing distances.
for s in [-1,1]:
    for j in range(9):
        x=s*(.10+(j%3)*.06);z=1.53+(j//3)*.07
        ell('Chest pebble scale',(x,-.222,z),(.032,.019,.027),skin)
    for j in range(6):ell('Cheek scale',(s*(.21+.004*(j%2)),-.13+(j%3)*.065,2.05+(j//3)*.06),(.022,.032,.021),darkskin,'Head',12,8)
# Simple deformation rig; custom bones are deliberately named for editing.
arm=bpy.data.armatures.new('Komodo skeleton');rig=bpy.data.objects.new('Komodo • deformation rig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
bones={}
def addbone(n,h,t,parent=None):
    b=arm.edit_bones.new(n);b.head=h;b.tail=t
    if parent:b.parent=arm.edit_bones[parent]
    bones[n]=(Vector(h),Vector(t))
addbone('Root',(0,0,.05),(0,0,.35))
addbone('Pelvis',(0,0,.93),(0,0,1.15),'Root');addbone('Spine',(0,0,1.15),(0,0,1.78),'Pelvis');addbone('Head',(0,0,1.78),(0,-.25,2.16),'Spine')
addbone('Tail.01',tailpts[0],tailpts[3],'Pelvis');addbone('Tail.02',tailpts[3],tailpts[-1],'Tail.01')
for s,l in [(-1,'R'),(1,'L')]:
    addbone('UpperArm.'+l,(s*.35,.015,1.72),(s*.59,-.10,1.40),'Spine')
    addbone('Forearm.'+l,(s*.59,-.10,1.40),(s*.66,-.38,1.14),'UpperArm.'+l)
    addbone('Hand.'+l,(s*.66,-.38,1.14),(s*.66,-.50,1.1),'Forearm.'+l)
    addbone('Thigh.'+l,(s*.17,0,1.02),(s*.23,-.04,.56),'Pelvis')
    addbone('Shin.'+l,(s*.23,-.04,.56),(s*.25,0,.15),'Thigh.'+l)
    addbone('Foot.'+l,(s*.25,0,.15),(s*.25,-.38,.10),'Shin.'+l)
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for o in parts:
    o.vertex_groups.clear();bn=o['bind_bone']
    if o==body:
        for v in o.data.vertices:
            z=v.co.z;side='L' if v.co.x>0 else 'R'
            name='Spine' if z>1.15 else ('Pelvis' if z>.90 else ('Thigh.'+side if z>.55 else ('Shin.'+side if z>.18 else 'Foot.'+side)))
            vg=o.vertex_groups.get(name) or o.vertex_groups.new(name=name);vg.add([v.index],1,'REPLACE')
    elif o==tail:
        for v in o.data.vertices:
            w=max(0,min(1,(v.co.y-.65)/.45))
            for n,weight in [('Tail.01',1-w),('Tail.02',w)]:
                vg=o.vertex_groups.get(n) or o.vertex_groups.new(name=n);vg.add([v.index],weight,'REPLACE')
    else:o.vertex_groups.new(name=bn).add(list(range(len(o.data.vertices))),1,'REPLACE')
    mod=o.modifiers.new('Komodo skin binding','ARMATURE');mod.object=rig;o.parent=rig
    o['asset_role']='Character mesh'
# Articulated humanoid hands, with long claws and opposing thumbs.
import sys
sys.path.insert(0,os.path.join(ROOT,'tools'))
from komodo_hands import build_hands
parts.extend(build_hands(rig,bpy.context.collection,skin,bone,darkskin,goldskin))
# Gentle idle cycle only; combat and locomotion require authored clips.
scene=bpy.context.scene;scene.render.fps=24;scene.frame_start=1;scene.frame_end=72
for f,amount in [(1,0),(19,1),(37,0),(55,-1),(73,0)]:
    for n,axis,amp in [('Spine',0,.012),('Head',1,.023),('Tail.01',1,.035),('Tail.02',1,.055)]:
        p=rig.pose.bones[n];p.rotation_mode='XYZ';p.rotation_euler[axis]=amount*amp;p.keyframe_insert(data_path='rotation_euler',frame=f,group=n)
rig.animation_data.action.name='Komodo_Idle'
scene.frame_set(1)
# Export only rigged meshes, keeping the studio separate from the runtime asset.
bpy.ops.object.select_all(action='DESELECT')
for o in parts+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'komodo_axe_warrior.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
runtime=os.path.join(ROOT,'Assets','Characters','Komodo');os.makedirs(runtime,exist_ok=True)
import shutil
shutil.copy2(os.path.join(OUT,'komodo_axe_warrior.glb'),os.path.join(runtime,'Komodo.glb'))
# Soft studio lighting evokes the dimensional pre-rendered game aesthetic.
ground=material('Studio • charcoal',(.027,.033,.041),rough=.9)
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.6,depth=.10,location=(0,.25,-.065));plinth=bpy.context.object;plinth.name='STUDIO • display plinth';plinth.data.materials.append(ground)
mod=plinth.modifiers.new('Plinth bevel','BEVEL');mod.width=.06;mod.segments=3
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.12));bpy.context.object.name='STUDIO • ground';bpy.context.object.data.materials.append(ground)
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,pos,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1.15))
area('STUDIO • warm key',(-3,-4,6),650,(1,.79,.56),4)
area('STUDIO • cool fill',(4,-2,3),430,(.54,.74,1),3)
area('STUDIO • tail rim',(1,4,4),850,(1,.55,.26),3)
world=bpy.data.worlds.new('Slate studio') if not bpy.data.worlds else bpy.data.worlds[0];scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.075,.10,.14,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
bpy.ops.object.camera_add(location=(3.35,-5.9,3.05));cam=bpy.context.object;cam.name='STUDIO • hero camera';aim(cam,(-.06,.15,1.13));cam.data.type='ORTHO';cam.data.ortho_scale=3.45;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'komodo_preview.png')
# Keep the editable character and presentation setup easy to find in the Outliner.
character_collection=bpy.data.collections.new('KOMODO • character and equipment');scene.collection.children.link(character_collection)
studio_collection=bpy.data.collections.new('STUDIO • render setup (not exported)');scene.collection.children.link(studio_collection)
for o in list(scene.objects):
    target=character_collection if o in parts or o==rig or o.name.startswith('WeaponGrip.') else studio_collection
    for old in list(o.users_collection):old.objects.unlink(o)
    target.objects.link(o)
notes=bpy.data.texts.new('START HERE • Komodo warrior')
notes.write('Komodo Axe Warrior / Broken Crown\nEditable character meshes in the KOMODO collection.\nEliber CC0 torso/legs; bespoke reptilian head, arms, tail and equipment.\nPacked albedo maps; 48-bone draft deformation rig; Komodo_Idle action.\nSelect rig and character meshes only when exporting GLB.\nThe STUDIO collection contains presentation objects.\nCombat and locomotion animation still need production work.\nReference: https://chatgpt.com/s/m_6ad64e5848088191bce75c6247986cd3\n')
# Save a convenient camera/material view in the editable source.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for space in screen.areas:
        if space.type=='VIEW_3D':
            space.spaces.active.region_3d.view_perspective='CAMERA';space.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'komodo_axe_warrior.blend'))
bpy.ops.render.render(write_still=True)
cam.location=(-3.3,5.3,2.8);aim(cam,(0,.25,1.1));scene.render.filepath=os.path.join(OUT,'komodo_rear.png');bpy.ops.render.render(write_still=True)
report={'mesh_objects':len(parts),'triangles':sum(len(o.data.loop_triangles) for o in parts),'rig_bones':len(arm.bones),'animations':['Komodo_Idle'],'base':'Eliber CC0 torso and legs','source_reference':'https://chatgpt.com/s/m_6ad64e5848088191bce75c6247986cd3'}
for o in parts:o.data.calc_loop_triangles()
report['triangles']=sum(len(o.data.loop_triangles) for o in parts)
with open(os.path.join(OUT,'build_report.json'),'w') as f:json.dump(report,f,indent=2)
print('KOMODO_COMPLETE',json.dumps(report))
