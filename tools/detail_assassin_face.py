"""Reference-directed MPFB head sculpt and a head-bound groom, executed via Blender MCP."""
import bpy, math, json, random, gzip, shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
from bl_ext.blender_org.mpfb.services.targetservice import TargetService
from bl_ext.blender_org.mpfb.services.locationservice import LocationService
ROOT=Path(r'D:\SoftwareEng\Game')
OUT=ROOT/'SourceAssets/characters/hooded_assassin/face'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'SourceAssets/characters/hooded_assassin/base/assassin_base.blend'))
body=bpy.data.objects['Assassin_Body']
rig=bpy.data.objects['Assassin_Skeleton']
eyes=bpy.data.objects['Assassin_Eyes']
col=bpy.data.collections['Character_Assassin']
before=[v.co.copy() for v in body.data.vertices]
targetroot=Path(LocationService.get_mpfb_data('targets'))
dataroot=Path(LocationService.get_user_data())
targets={'head/head-scale-horiz-incr':.23,'head/head-round':.20,'head/head-age-incr':.10,'forehead/forehead-scale-vert-incr':.13,'forehead/forehead-temple-incr':.10,'chin/chin-width-incr':.18,'chin/chin-height-decr':.12,'chin/chin-prominent-incr':.08,'nose/nose-point-width-incr':.32,'nose/nose-width3-incr':.16,'nose/nose-scale-depth-incr':.13,'nose/nose-point-down':.08,'mouth/mouth-scale-horiz-incr':.15,'mouth/mouth-lowerlip-volume-incr':.17,'mouth/mouth-upperlip-volume-incr':.07,'mouth/mouth-cupidsbow-incr':.12,'eyebrows/eyebrows-trans-forward':.17,'eyebrows/eyebrows-trans-down':.10}
for side in ['l','r']:
    targets.update({f'cheek/{side}-cheek-volume-incr':.20,f'cheek/{side}-cheek-bones-incr':.12,f'eyes/{side}-eye-height1-decr':.10,f'eyes/{side}-eye-eyefold-down':.16,f'eyes/{side}-eye-bag-incr':.10})
delta=[Vector() for _ in before]
for name,weight in targets.items():
    raw=gzip.open(targetroot/(name+'.target.gz'),'rt').read()
    info=TargetService._target_string_to_shape_key_info(raw,name)
    for i,x,y,z in info['vertices']:
        if before[i].z>1.54:
            delta[i]+=Vector((x,y,z))*(weight*.105)
for v,p,d in zip(body.data.vertices,before,delta): v.co=p+d
# Keep the original crown height and body below the neck unchanged.
top=max(v.co.z for v in body.data.vertices)
for v in body.data.vertices:
    if v.co.z>1.54: v.co.z=1.54+(v.co.z-1.54)*(.26/(top-1.54))
body['face_reference']='Early unfiltered frames of user-provided 2023-06-25-120122505.mp4'
body['face_morphs']=json.dumps(targets)
body['face_style']='Stylized likeness: broad forehead, hooded eyes, full cheeks, rounded nose and copper beard.'
def material(name,color,rough=.55):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    return mat
skin=material('Assassin_Portrait_Skin',(.55,.30,.20),.52)
nodes=skin.node_tree.nodes
links=skin.node_tree.links
bs=nodes.get('Principled BSDF')
tex=nodes.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(str(dataroot/'skins/toigo_light_skin_male_ginger/young_lightskinned_male_diffuse_Ginger.png'))
links.new(tex.outputs['Color'],bs.inputs['Base Color'])
bs.inputs['Subsurface Weight'].default_value=.075
bs.inputs['Subsurface Radius'].default_value=(1,.42,.22)
soften=nodes.new('ShaderNodeMixRGB')
soften.blend_type='MIX'
soften.inputs[0].default_value=.35
soften.inputs[2].default_value=(.58,.36,.27,1)
links.new(tex.outputs['Color'],soften.inputs[1])
links.new(soften.outputs[0],bs.inputs['Base Color'])
noise=nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value=1050
noise.inputs['Detail'].default_value=2
bump=nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=.16
bump.inputs['Distance'].default_value=.00012
links.new(noise.outputs['Fac'],bump.inputs['Height'])
links.new(bump.outputs['Normal'],bs.inputs['Normal'])
body.data.materials.clear()
body.data.materials.append(skin)
sub=body.modifiers.new('Portrait surface subdivision','SUBSURF')
sub.levels=1
sub.render_levels=2
# Install the supplied low-poly eyes' matching grey-blue material.
eye_mat=material('Assassin_Grey_Blue_Eyes',(.6,.7,.72),.26)
en=eye_mat.node_tree.nodes
et=en.new('ShaderNodeTexImage')
et.image=bpy.data.images.load(str(dataroot/'eyes/materials/grey_eye.png'))
el=eye_mat.node_tree.links
position=en.new('ShaderNodeNewGeometry')
sep=en.new('ShaderNodeSeparateXYZ')
el.new(position.outputs['Position'],sep.inputs[0])
def emath(operation,a,b=None):
    node=en.new('ShaderNodeMath')
    node.operation=operation
    for value,socket in [(a,node.inputs[0]),(b,node.inputs[1])]:
        if value is None: continue
        if isinstance(value,(int,float)): socket.default_value=value
        else: el.new(value,socket)
    return node.outputs[0]
dx=emath('SUBTRACT',emath('ABSOLUTE',sep.outputs['X']),.03244)
dz=emath('SUBTRACT',sep.outputs['Z'],1.6788)
radius=emath('DIVIDE',emath('SQRT',emath('ADD',emath('MULTIPLY',dx,dx),emath('MULTIPLY',dz,dz))),.007)
ramp=en.new('ShaderNodeValToRGB')
el.new(radius,ramp.inputs[0])
stops=[(0,(.002,.003,.004,1)),(.30,(.002,.003,.004,1)),(.35,(.10,.17,.18,1)),(.68,(.15,.22,.23,1)),(.79,(.025,.045,.047,1)),(.88,(.70,.72,.69,1)),(1,(.70,.72,.69,1))]
for i,(pos,color) in enumerate(stops):
    element=ramp.color_ramp.elements[i] if i<2 else ramp.color_ramp.elements.new(pos)
    element.position=pos
    element.color=color
el.new(ramp.outputs['Color'],en.get('Principled BSDF').inputs['Base Color'])
en.get('Principled BSDF').inputs['Coat Weight'].default_value=.3
eyes.data.materials.clear()
eyes.data.materials.append(eye_mat)
# Fit an existing short hairstyle from the installed CC0 system pack.
hair=HumanService.add_mhclo_asset(str(dataroot/'hair/short04/short04.mhclo'),body,asset_type='Hair',subdiv_levels=0)
hair.name='Assassin_Short_Copper_Hair'
for c in list(hair.users_collection): c.objects.unlink(hair)
col.objects.link(hair)
hairmat=material('Assassin_Copper_Hair_Cards',(.21,.085,.035),.8)
hairmat.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.15
hn=hairmat.node_tree.nodes
hl=hairmat.node_tree.links
ht=hn.new('ShaderNodeTexImage')
ht.image=bpy.data.images.load(str(dataroot/'hair/short04/short04_diffuse.png'))
mix=hn.new('ShaderNodeMixRGB')
mix.blend_type='MULTIPLY'
mix.inputs[0].default_value=1
mix.inputs[2].default_value=(.68,.30,.12,1)
hl.new(ht.outputs['Color'],mix.inputs[1])
hl.new(mix.outputs[0],hn.get('Principled BSDF').inputs['Base Color'])
hl.new(ht.outputs['Alpha'],hn.get('Principled BSDF').inputs['Alpha'])
hair.data.materials.clear()
hair.data.materials.append(hairmat)
for poly in hair.data.polygons: poly.use_smooth=True
bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
rng=random.Random(20230625)
palette=[material('Beard_Copper_Shadow',(.045,.015,.005),.8),material('Beard_Auburn',(.12,.045,.012),.78),material('Beard_Golden_Copper',(.24,.11,.035),.76),material('Beard_Straw_Highlight',(.36,.22,.09),.76)]
def groom(name,strands,radius):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D'
    curve.resolution_u=2
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    curve.resolution_u=3
    for mat in palette: curve.materials.append(mat)
    for points,shade in strands:
        spline=curve.splines.new('POLY')
        spline.points.add(len(points)-1)
        spline.material_index=shade
        for i,(dest,p) in enumerate(zip(spline.points,points)):
            dest.co=(*p,1)
            dest.radius=max(.05,(1-i/(len(points)-1))**.65)
    obj=bpy.data.objects.new(name,curve)
    col.objects.link(obj)
    # Rigid head binding preserves the existing skeleton and neutral rest pose.
    matrix=obj.matrix_world.copy()
    obj.parent=rig
    obj.parent_type='BONE'
    obj.parent_bone='head'
    obj.matrix_world=matrix
    return obj
beard=[]
for _ in range(14000):
    x=rng.uniform(-.085,.085)
    z=rng.uniform(1.548,1.659)
    p,n,idx,dist=bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)),.6)
    if p is None or p.y>-.065: continue
    ax=abs(x)
    # Moustache, cheek line, sideburns and chin form one natural beard silhouette.
    moustache=ax<.030 and 1.615<z<1.631
    cheek_top=1.606+min(1,ax/.070)*.034
    main=z<cheek_top and (ax>.028 or z<1.603)
    if not (main or moustache): continue
    if ax<.030 and 1.601<z<1.615: continue
    if z<1.562 and p.y>-.12: continue
    if rng.random()>.72: continue
    if main and z>cheek_top-.004 and rng.random()>.4: continue
    length=rng.uniform(.005,.013) if main else rng.uniform(.004,.007)
    if ax<.04 and z<1.596: length*=1.55
    out=Vector((x*.10,-.5,-1)).normalized()
    if moustache: out=Vector((math.copysign(.45,x),-.22,-.55)).normalized()
    phase=rng.uniform(0,math.tau)
    pts=[]
    for j in range(6):
        t=j/5
        offset=n*(.00025+.004*math.sin(t*math.pi/2))
        pos=p+offset+out*(length*t)
        pos.x+=math.sin(phase+t*7)*.0013*t
        pts.append(pos)
    beard.append((pts,rng.choices(range(4),[.20,.43,.30,.07])[0]))
groom('Assassin_Full_Copper_Beard',beard,.00023)
# Light brows follow the actual sculpted forehead surface.
brows=[]
for sign in [-1,1]:
    for _ in range(420):
        x=sign*rng.uniform(.014,.060)
        z=1.699-.009*((abs(x)-.026)/.040)**2+rng.uniform(-.0025,.0025)
        p,n,idx,dist=bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)),.6)
        if p is None: continue
        pts=[p+n*.0004+Vector((sign*.004*t,-.0005*t,.002*math.sin(t*math.pi))) for t in [0,.25,.5,.75,1]]
        brows.append((pts,rng.choice([1,2,2,3])))
groom('Assassin_Copper_Eyebrows',brows,.00018)
for obj in [hair]:
    # All hair-card vertices are bound to the same head bone.
    for vg in list(obj.vertex_groups): obj.vertex_groups.remove(vg)
    vg=obj.vertex_groups.new(name='head')
    vg.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    obj.parent=rig
    for mod in obj.modifiers:
        if mod.type=='ARMATURE': mod.object=rig
    if not any(m.type=='ARMATURE' for m in obj.modifiers):
        mod=obj.modifiers.new('Head binding','ARMATURE')
        mod.object=rig
scene=bpy.context.scene
for lamp,power in zip([o for o in bpy.data.objects if o.type=='LIGHT'],[300,100,180]): lamp.data.energy=power
camera=scene.camera
camera.location=(.34,-.94,1.73)
camera.rotation_euler=(Vector((0,-.075,1.669))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=.38
scene.cycles.samples=48
scene.render.resolution_x=1100
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.filepath=str(OUT/'assassin_face_three_quarter.png')
bpy.ops.render.render(write_still=True)
camera.location=(0,-1,1.68)
camera.rotation_euler=(Vector((0,-.075,1.669))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'assassin_face_front.png')
bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assassin_detailed.blend'))
result={'file':str(OUT/'assassin_detailed.blend'),'beard_strands':len(beard),'brow_strands':len(brows),'body_vertices':len(body.data.vertices),'body_below_neck_unchanged':all((v.co-before[i]).length<1e-7 for i,v in enumerate(body.data.vertices) if before[i].z<=1.54),'bones':len(rig.data.bones)}
(OUT/'face_validation.json').write_text(json.dumps(result,indent=2))
