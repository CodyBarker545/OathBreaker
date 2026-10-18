"""Improve boots, curved-surface shading and portable PBR textures.
Preserves the source animated file and all three animation actions.
"""
import bpy, os, math, bmesh, json
import numpy as np
from mathutils import Vector

HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'blendswap_assassin')
TEX=os.path.join(OUT,'textures'); os.makedirs(TEX,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'assassin_animated.blend'),use_scripts=False)
scene=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
action=rig.animation_data.action
rig.animation_data.action=None
for pb in rig.pose.bones: pb.matrix_basis.identity()
rig.data.pose_position='REST'
collection=bpy.data.collections['ASSASSIN | editable character parts']

# Replace both oval placeholders and the redundant toe caps.
for obj in list(collection.objects):
    if obj.name.startswith(('Boot.','Toe armour.')):
        bpy.data.objects.remove(obj,do_unlink=True)
body=bpy.data.objects['Eliber | fitted continuous body']
bm=bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<.135],context='VERTS')
bm.to_mesh(body.data); bm.free()

def make_mesh(name,verts,faces,mat,weights):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); collection.objects.link(obj)
    obj.data.materials.append(bpy.data.materials[mat])
    for v in data.vertices:
        for bn,w in weights(v.co).items():
            group=obj.vertex_groups.get(bn) or obj.vertex_groups.new(name=bn)
            group.add([v.index],w,'REPLACE')
    for p in data.polygons: p.use_smooth=True
    obj.parent=rig
    mod=obj.modifiers.new('Skeleton','ARMATURE'); mod.object=rig
    return obj

def before_rig(obj,mod):
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)

def soften(obj,width=.006,segments=3):
    mod=obj.modifiers.new('Rounded edge craftsmanship','BEVEL'); mod.width=width; mod.segments=segments
    mod.limit_method='ANGLE'; mod.angle_limit=.45
    before_rig(obj,mod)

for sign,side in [(-1,'L'),(1,'R')]:
    x=sign*.18
    rigid=lambda p,side=side: {'foot.'+side:1}
    # Anatomical shoe last: tapered toe, broad forefoot, raised instep and heel.
    sections=[(-.278,.001,.001),(-.267,.022,.042),(-.246,.054,.058),(-.20,.073,.072),(-.13,.079,.083),(-.065,.073,.11),(.005,.061,.145),(.065,.057,.12),(.084,.045,.08)]
    verts=[]; faces=[]; count=15
    for y,w,h in sections:
        for j in range(count):
            a=math.pi*j/(count-1)
            verts.append((x+w*math.cos(a),y,.033+h*math.sin(a)**.85))
    for i in range(len(sections)-1):
        for j in range(count-1):
            a=i*count+j; faces.append((a,a+count,a+count+1,a+1))
        a=i*count; faces.append((a,a+count-1,a+count*2-1,a+count))
    faces.extend([tuple(reversed(range(count))),tuple((len(sections)-1)*count+j for j in range(count))])
    obj=make_mesh('Boot | shaped leather upper.'+side,verts,faces,'Leather | charcoal',rigid)
    mod=obj.modifiers.new('Smooth boot form','SUBSURF'); mod.levels=2
    before_rig(obj,mod)
    # A real outsole, with a defined waist and toe rather than an ellipsoid.
    outline=[(-.043,.087),(-.062,.062),(-.068,.005),(-.080,-.105),(-.082,-.17),(-.065,-.235),(-.028,-.267),(.028,-.267),(.065,-.235),(.082,-.17),(.080,-.105),(.068,.005),(.062,.062),(.043,.087)]
    verts=[(x+xx,y,z) for z in [.008,.035] for xx,y in outline]
    n=len(outline); faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=make_mesh('Boot | welted outsole.'+side,verts,faces,'Leather | charcoal',rigid); soften(obj,.007)
    # Taller ankle cuff blends across the ankle joint.
    verts=[]; faces=[]; n=32
    for z,rx,ry in [(.12,.060,.067),(.17,.063,.064),(.23,.062,.062),(.26,.064,.064)]:
        for i in range(n):
            a=2*math.pi*i/n; verts.append((x+rx*math.cos(a),.008+ry*math.sin(a),z))
    for k in range(3):
        for i in range(n):
            a=k*n+i; b=k*n+(i+1)%n; faces.append((a,b,b+n,a+n))
    def cuffweights(p,side=side):
        t=min(1,max(0,(p.z-.13)/.10))
        return {'foot.'+side:1-t,'shin.'+side:t}
    make_mesh('Boot | articulated ankle cuff.'+side,verts,faces,'Leather | charcoal',cuffweights)
    # Low-profile forged toe guard, curved over the forefoot.
    verts=[]; faces=[]
    for y,w,h in [(-.245,.059,.070),(-.215,.076,.083),(-.17,.084,.095)]:
        for j in range(13):
            a=.32+(math.pi-.64)*j/12
            verts.append((x+w*math.cos(a),y,.037+h*math.sin(a)**.85))
    for k in range(2):
        for j in range(12):
            a=k*13+j; faces.append((a,a+13,a+14,a+1))
    obj=make_mesh('Boot | curved steel toe guard.'+side,verts,faces,'Armour | midnight steel',rigid)
    sol=obj.modifiers.new('Toe guard thickness','SOLIDIFY'); sol.thickness=.004; before_rig(obj,sol)
    soften(obj,.003)
    # Two leather straps with a small bronze buckle on the outward side.
    for z in [.16,.225]:
        verts=[]; faces=[]
        for zz in [z-.009,z+.009]:
            for i in range(32):
                a=2*math.pi*i/32; verts.append((x+.066*math.cos(a),.008+.067*math.sin(a),zz))
        for i in range(32): faces.append((i,(i+1)%32,(i+1)%32+32,i+32))
        make_mesh('Boot | ankle strap.'+side,verts,faces,'Leather | charcoal',cuffweights)
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x+sign*.067,-.014,z))
        ob=bpy.context.object; ob.name='Boot | bronze buckle.'+side
        ob.scale=(.008,.026,.021); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        for c in list(ob.users_collection): c.objects.unlink(ob)
        collection.objects.link(ob); ob.data.materials.append(bpy.data.materials['Trim | antique bronze'])
        group=ob.vertex_groups.new(name='shin.'+side); group.add(list(range(len(ob.data.vertices))),1,'REPLACE')
        ob.parent=rig; mod=ob.modifiers.new('Skeleton','ARMATURE'); mod.object=rig; soften(ob,.002)

# Smooth curved pieces; retain intended hard armour silhouettes.
for obj in list(collection.objects):
    if obj.type!='MESH': continue
    if obj.name.startswith('Boot |'): continue
    bpy.context.view_layer.objects.active=obj
    for p in obj.data.polygons: p.use_smooth=True
    if obj.name.startswith(('Head','Glove.','Hood |','Scarf |','Waist |')):
        mod=obj.modifiers.new('Refined curved surface','SUBSURF'); mod.levels=2 if obj.name.startswith(('Head','Glove.')) else 1
        # Keep cloth thickness after surface smoothing.
        while obj.modifiers.find(mod.name)>0:
            bpy.ops.object.modifier_move_up(modifier=mod.name)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    elif any(m.type=='SOLIDIFY' for m in obj.modifiers):
        # Apply shell thickness so soft edges also export to the game model.
        for mod in list(obj.modifiers):
            if mod.type=='SOLIDIFY': bpy.ops.object.modifier_apply(modifier=mod.name)
        soften(obj,.0025,3)
    # Existing cylindrical bronze trim is now smooth, not polygonally shaded.

# UVs for the new meshes; leave the existing source mesh and outfit UVs intact.
for obj in list(collection.objects):
    if obj.type!='MESH' or obj.data.uv_layers: continue
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.025); bpy.ops.object.mode_set(mode='OBJECT')

# Actual 1024px seamless material maps, packed into the .blend and embedded in
# GLB. These replace the previous plain colours and survive engine export.
size=1024; rng=np.random.default_rng(84)
yy,xx=np.mgrid[0:size,0:size].astype(np.float32)
x=xx/size; y=yy/size
fine=rng.random((size,size),dtype=np.float32)-.5
cloud=sum(np.sin(2*math.pi*(a*x+b*y)+p)*v for a,b,p,v in [(3,2,.3,.4),(7,-5,1.4,.22),(17,11,2.1,.10),(43,-29,.5,.045)])
def image(name,rgb,normal=False):
    arr=np.empty((size,size,4),dtype=np.float32)
    if rgb.ndim==2: arr[:,:,:3]=rgb[:,:,None]
    else: arr[:,:,:3]=rgb
    if not normal:
        # Shader base colours are linear; PNG colour samples are sRGB.
        rgbdata=np.clip(arr[:,:,:3],0,1)
        arr[:,:,:3]=np.where(rgbdata<=.0031308,rgbdata*12.92,1.055*np.power(rgbdata,1/2.4)-.055)
    arr[:,:,3]=1
    im=bpy.data.images.new(name,width=size,height=size,alpha=True)
    im.colorspace_settings.name='Non-Color' if normal else 'sRGB'
    im.pixels.foreach_set(np.clip(arr,0,1).ravel())
    im.filepath_raw=os.path.join(TEX,name+'.png'); im.file_format='PNG'; im.save(); im.pack()
    return im

def maps(matname,kind):
    mat=bpy.data.materials[matname]; nodes=mat.node_tree.nodes; links=mat.node_tree.links
    bs=nodes.get('Principled BSDF'); base=np.array(mat.diffuse_color[:3],dtype=np.float32)
    if kind=='cloth':
        weave=np.sin(2*math.pi*128*x)*np.sin(2*math.pi*128*y)
        height=weave*.12+fine*.035
        variation=1+cloud*.09+weave*.025
        rough=.78+fine*.06
    elif kind=='leather':
        height=cloud*.04+fine*.18
        variation=1+cloud*.13+fine*.11
        rough=.57+cloud*.07+fine*.06
    else:
        height=fine*.035+np.sin(2*math.pi*220*x)*.014
        variation=1+cloud*.10+fine*.028
        rough=(.36 if kind=='steel' else .42)+cloud*.055+fine*.04
    label=kind+'_'+matname.replace('|','').replace('  ',' ').replace(' ','_').lower()
    col=image(label+'_basecolor',variation[:,:,None]*base)
    orm=np.ones((size,size,3),dtype=np.float32)
    orm[:,:,1]=rough; orm[:,:,2]=float(bs.inputs['Metallic'].default_value)
    packed=image(label+'_orm',orm,True)
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*.22
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*.22
    norm=np.stack([-dx,-dy,np.ones_like(dx)],axis=2)
    norm/=np.linalg.norm(norm,axis=2,keepdims=True)
    normal=image(label+'_normal',norm*.5+.5,True)
    tex=nodes.new('ShaderNodeTexImage'); tex.image=col; tex.label='Fine seamless '+kind+' colour'
    links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    tex=nodes.new('ShaderNodeTexImage'); tex.image=packed
    sep=nodes.new('ShaderNodeSeparateColor'); links.new(tex.outputs['Color'],sep.inputs[0])
    links.new(sep.outputs['Green'],bs.inputs['Roughness']); links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    tex=nodes.new('ShaderNodeTexImage'); tex.image=normal
    nm=nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=.35
    links.new(tex.outputs['Color'],nm.inputs['Color']); links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    mat['texture_resolution']='1024x1024; packed basecolor, ORM and tangent normal'
    return [col.name,packed.name,normal.name]

textures=[]
for name,kind in [('Leather | charcoal','leather'),('Cloth | oxblood crimson','cloth'),('Cloth | raised folds','cloth'),('Hood | faded charcoal violet','cloth'),('Armour | midnight steel','steel'),('Trim | antique bronze','bronze')]:
    textures+=maps(name,kind)

rig.data.pose_position='POSE'; rig.animation_data.action=action
scene.frame_set(1)
parts=[o for o in collection.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for obj in parts+[rig]: obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,
    export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_force_sampling=True,export_def_bones=True)
scene['refinements']='Shaped leather boots, layered outsole, curved steel toe guards, weighted ankle cuffs; smooth surfaces and 1024px packed PBR texture sets.'
scene.render.resolution_x=900; scene.render.resolution_y=1000; scene.cycles.samples=32
scene.camera.data.ortho_scale=2.65
scene.render.filepath=os.path.join(OUT,'refined_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'assassin_refined.blend'))
bpy.ops.render.render(write_still=True)
# Close-up makes it possible to judge boot silhouette and surface detail.
cam=scene.camera
cam.location=(1.0,-2,.8); cam.rotation_euler=(Vector((0,-.06,.19))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=.82
scene.render.resolution_x=1000; scene.render.resolution_y=700
scene.render.filepath=os.path.join(OUT,'refined_boots.png')
bpy.ops.render.render(write_still=True)
with open(os.path.join(OUT,'refinement_report.json'),'w') as f:
    json.dump({'boot_parts':[o.name for o in parts if o.name.startswith('Boot |')],'texture_images':textures,'actions':[a.name for a in bpy.data.actions],'weapons':False},f,indent=2)
print('REFINEMENT COMPLETE')
