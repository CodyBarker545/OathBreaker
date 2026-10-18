"""Build an Ashveil outfit on the fitted Eliber body and existing animation rig.
Blender 4.5: --background --python-exit-code 1 --python this_file.py
"""
import bpy, os, math, json
import numpy as np
from mathutils import Vector

HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'ashveil'); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'hooded_assassin','blendswap_assassin','assassin_refined.blend'),use_scripts=False)
scene=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.name='Ashveil_Rig'
action=rig.animation_data.action; rig.animation_data.action=None
for pb in rig.pose.bones: pb.matrix_basis.identity()
rig.data.pose_position='REST'
col=bpy.data.collections['ASSASSIN | editable character parts']; col.name='ASHVEIL | body and editable outfit'

# Preserve the supplied continuous body and authored face, hands and footwear.
keep=('Eliber |','Head','Eye','Amber iris','Brow','Face mask','Neck','Glove.','Boot |')
for obj in list(col.objects):
    if obj.type=='MESH' and not obj.name.startswith(keep): bpy.data.objects.remove(obj,do_unlink=True)

def mat(name,rgb,metal=0,rough=.7,textile=False):
    m=bpy.data.materials.new('Ashveil | '+name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*rgb,1)
    bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=rough
    if textile:
        n=1024; y,x=np.mgrid[0:n,0:n].astype(np.float32)/n
        rng=np.random.default_rng(42)
        weave=np.sin(2*math.pi*240*x)*np.sin(2*math.pi*240*y)
        cloud=np.sin(2*math.pi*(7*x+3*y))*.07+np.sin(2*math.pi*(19*x-13*y))*.025
        v=1+cloud+weave*.035+(rng.random((n,n),dtype=np.float32)-.5)*.045
        linear=np.clip(v[:,:,None]*np.array(rgb)[None,None,:],0,1)
        srgb=np.where(linear<.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
        rgba=np.ones((n,n,4),dtype=np.float32); rgba[:,:,:3]=srgb
        im=bpy.data.images.new('Ashveil_'+name+'_weave',width=n,height=n)
        im.pixels.foreach_set(rgba.ravel()); im.filepath_raw=os.path.join(OUT,im.name+'.png'); im.file_format='PNG'; im.save(); im.pack()
        tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=im
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        normal=m.node_tree.nodes.new('ShaderNodeTexImage'); normal.image=bpy.data.images.get('cloth_hood_faded_charcoal_violet_normal')
        if normal.image:
            nm=m.node_tree.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value=.5
            m.node_tree.links.new(normal.outputs['Color'],nm.inputs['Color']); m.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    return m

ash=mat('weathered ash cloth',(.16,.15,.17),rough=.88,textile=True)
dark=mat('charcoal wraps',(.047,.043,.055),rough=.85,textile=True)
pants=mat('loose trouser cloth',(.065,.064,.073),rough=.86,textile=True)
steel=mat('engraved dark steel',(.07,.075,.085),.8,.4)
brass=mat('aged brass',(.28,.21,.13),.75,.5)
rope=mat('worn cord',(.23,.19,.14),rough=.9)
leather=bpy.data.materials['Leather | charcoal']
skin=bpy.data.materials['Skin | warm pale']

def attach(obj,material,bone):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    col.objects.link(obj); obj.data.materials.clear(); obj.data.materials.append(material)
    obj.parent=rig
    obj.vertex_groups.clear(); g=obj.vertex_groups.new(name=bone); g.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    for p in obj.data.polygons: p.use_smooth=True
    mod=obj.modifiers.new('Ashveil skeleton','ARMATURE'); mod.object=rig
    return obj

def mesh(name,verts,faces,material,bone,cloth=False):
    d=bpy.data.meshes.new(name); d.from_pydata(verts,[],faces); d.update()
    o=bpy.data.objects.new(name,d); col.objects.link(o)
    attach(o,material,bone)
    if cloth:
        mod=o.modifiers.new('Fabric body','SOLIDIFY'); mod.thickness=.006
    return o

def oval(name,loc,scale,material,bone):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return attach(o,material,bone)

def line(name,points,width,material,bone,closed=False):
    d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D'; d.bevel_depth=width; d.bevel_resolution=2
    sp=d.splines.new('POLY'); sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points): p.co=(*co,1)
    sp.use_cyclic_u=closed
    o=bpy.data.objects.new(name,d); col.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target='MESH')
    return attach(bpy.context.object,material,bone)

def band(name,z,rx,ry,material,bone,centre=(0,0),tilt=0,width=.012):
    points=[]
    for i in range(65):
        a=2*math.pi*i/64; points.append((centre[0]+rx*math.cos(a),centre[1]+ry*math.sin(a),z+tilt*math.cos(a)))
    return line(name,points,width,material,bone,True)

def cloth_wrap(name,z,rx,ry,material,bone,tilt=0,sag=0):
    verts=[]; n=65
    for row,(dz,bulge) in enumerate([(.021,1),(0,1.035),(-.021,1)]):
        for i in range(n):
            a=2*math.pi*i/(n-1)
            verts.append((rx*math.cos(a)*bulge,ry*math.sin(a)*bulge,z+dz+tilt*math.cos(a)-sag*max(0,-math.sin(a))))
    return mesh(name,verts,[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(2) for i in range(n-1)],material,bone,True)

def panel(name,rows,material,bone,chain=None):
    verts=[]
    for x,y,z,w in rows: verts.extend([(x-w,y,z),(x,y-.023,z+.012),(x+w,y+.008,z-.014)])
    faces=[]
    for j in range(len(rows)-1):
        a=j*3; faces.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
    o=mesh(name,verts,faces,material,bone,True)
    if chain:
        o.vertex_groups.clear()
        for v in o.data.vertices:
            row=v.index//3; bn=chain+('.%02d'%min(row,len(rows)-2))
            g=o.vertex_groups.get(bn) or o.vertex_groups.new(name=bn); g.add([v.index],1,'REPLACE')
    return o

# Recolour the retained gloves and boots to fit the wraps and sandals palette.
for obj in list(col.objects):
    if obj.type!='MESH': continue
    if obj.name.startswith('Face mask'):
        obj.data.materials.clear(); obj.data.materials.append(steel)
    elif obj.name.startswith('Boot |'):
        obj.data.materials.clear(); obj.data.materials.append(dark if 'buckle' not in obj.name else brass)
    elif obj.name.startswith('Brow'):
        obj.data.materials.clear(); obj.data.materials.append(dark)
    elif obj.name.startswith(('Eye socket','Amber iris')):
        obj.scale.z *= .55

# Sleeveless tunic and baggy trousers, covering the same source body.
oval('Ashveil | sleeveless under-tunic',(0,.005,1.34),(.238,.145,.28),dark,'chest')
panel('Ashveil | diagonal tunic front',[(-.10,-.135,1.60,.10),(.015,-.18,1.43,.15),(.055,-.165,1.23,.16),(0,-.16,1.10,.16)],ash,'chest')
panel('Ashveil | tunic back',[(0,.13,1.58,.19),(0,.16,1.40,.21),(0,.14,1.15,.18)],ash,'chest')
for s,side in [(-1,'L'),(1,'R')]:
    oval('Ashveil | gathered trousers.'+side,(s*.14,.005,.84),(.123,.119,.235),pants,'thigh.'+side)
    # Fold lines follow each leg, with tapered volume at the knee.
    for k in range(5):
        a=2*math.pi*k/5
        line('Ashveil | trouser fold',[(s*.14+.12*math.cos(a),.115*math.sin(a),1.00),(s*.15+.126*math.cos(a),.12*math.sin(a),.84),(s*.16+.075*math.cos(a),.08*math.sin(a),.63)],.006,dark,'thigh.'+side)
    # Exposed upper-arm muscle volume under the sleeve openings.
    oval('Ashveil | upper-arm silhouette.'+side,(s*.31,0,1.43),(.077,.077,.145),skin,'upper_arm.'+side)
    for z in [1.34,1.36]: band('Ashveil | upper-arm tie',z,.074,.073,dark,'upper_arm.'+side,(s*.355,0),width=.009)
    # Wrapped shin silhouette and criss-cross cords.
    oval('Ashveil | shin wraps.'+side,(s*.175,.005,.36),(.075,.077,.22),dark,'shin.'+side)
    for direction in [-1,1]:
        pts=[]
        for i in range(129):
            t=i/128; a=direction*t*math.pi*8
            pts.append((s*.177+.08*math.cos(a),.005+.082*math.sin(a),.16+.39*t))
        line('Ashveil | crossed shin cord.'+side,pts,.008,rope,'shin.'+side)
    band('Ashveil | knee knot',.56,.078,.079,rope,'shin.'+side,(s*.17,0),width=.012)
    # Open-sided curved bracer, with real geometric trim and etching.
    a=Vector((s*.39,-.004,1.26)); b=Vector((s*.47,-.045,1.05))
    verts=[]; n=17
    for t in [0,.5,1]:
        c=a.lerp(b,t)
        for i in range(n):
            angle=math.pi+.23+(math.pi-.46)*i/(n-1)
            verts.append((c.x+.072*math.cos(angle),c.y+.083*math.sin(angle),c.z))
    faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(2) for i in range(n-1)]
    mesh('Ashveil | engraved bracer.'+side,verts,faces,steel,'forearm.'+side,True)
    for j in [0,2]: line('Ashveil | bracer rim',verts[j*n:(j+1)*n],.004,brass,'forearm.'+side)
    for j in range(4):
        t=.15+j*.22; c=a.lerp(b,t)
        line('Ashveil | bracer etched chevron',[(c.x-s*.04,c.y-.077,c.z+.025),(c.x,c.y-.088,c.z-.015),(c.x+s*.04,c.y-.077,c.z+.025)],.002,brass,'forearm.'+side)

# Cloth headwrap covers hair while leaving the eyes visible.
oval('Ashveil | fitted head cloth',(0,.012,1.882),(.127,.116,.15),dark,'head')
for i in range(7):
    cloth_wrap('Ashveil | layered head wrap',1.87+i*.020,.133-i*.003,.120-i*.003,dark,'head',tilt=(-.018 if i%2 else .019))
# Neck cowl, visually separate from the headwrap.
for i in range(4): cloth_wrap('Ashveil | cowl fold',1.68-i*.026,.150+i*.018,.132+i*.013,ash,'chest',tilt=.012,sag=.045)
panel('Ashveil | long headwrap tails',[(0,.13,1.91,.07),(.025,.205,1.60,.065),(.08,.22,1.28,.08),(.13,.25,.97,.055),(.17,.26,.64,.001)],ash,'chest',chain='scarf_back')

# Single domed shoulder pauldron on the character's left side (+X).
for k in range(3):
    cx=.265+k*.032; z=1.64-k*.069; verts=[]; n=19
    for row in range(3):
        for i in range(n):
            a=math.pi*i/(n-1)
            verts.append((cx+(.105-row*.012)*math.cos(a),.03-(.145-row*.013)*math.sin(a),z+row*.024))
    mesh('Ashveil | single shoulder lame %d'%k,verts,[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(2) for i in range(n-1)],steel,'upper_arm.R',True)
    line('Ashveil | shoulder gilt edge',verts[:n],.004,brass,'upper_arm.R')
    for j in range(4):
        a=.35+j*.70
        line('Ashveil | shoulder etched scroll',[(cx+.09*math.cos(a+t),.022-.14*math.sin(a+t),z+.02+.008*math.sin(t*8)) for t in np.linspace(0,.3,12)],.002,brass,'upper_arm.R')

# Crossed leather harness, bronze clasp, layered waist sash and rope knot.
for s in [-1,1]:
    line('Ashveil | diagonal harness',[(s*.19,-.15,1.60),(s*.10,-.215,1.43),(-s*.15,-.205,1.18)],.016,leather,'chest')
    for j in range(6):
        t=j/5; oval('Ashveil | harness rivet',(s*(.18-.31*t),-.187,1.58-.37*t),(.004,.004,.004),brass,'chest')
for i in range(5): band('Ashveil | layered waist sash',1.09+i*.018,.218,.156,leather,'pelvis',tilt=.008*(i%2),width=.015)
for z in [1.105,1.145]: band('Ashveil | waist cord',z,.225,.165,rope,'pelvis',width=.006)
line('Ashveil | shoulder round clasp',[(.21+.035*math.cos(a),-.162,1.595+.035*math.sin(a)) for a in np.linspace(0,2*math.pi,48)],.008,brass,'chest',True)
line('Ashveil | hanging belt ring',[(.01+.028*math.cos(a),-.19,1.035+.028*math.sin(a)) for a in np.linspace(0,2*math.pi,40)],.006,brass,'pelvis',True)
for j in range(5): line('Ashveil | belt tassel',[(.012+j*.004,-.19,1.0),(.02+j*.004,-.195,.87)],.003,rope,'pelvis')

# Ragged layered skirt panels. Front and side chains reuse the proven rig.
panel('Ashveil | central weathered tabard',[(0,-.18,1.07,.10),(.02,-.19,.91,.115),(.03,-.16,.71,.10),(.04,-.15,.48,.002)],ash,'pelvis',chain='tabard_front')
for s,side in [(-1,'L'),(1,'R')]:
    panel('Ashveil | layered side skirt.'+side,[(s*.18,-.04,1.08,.09),(s*.22,-.03,.91,.10),(s*.26,-.02,.71,.07),(s*.29,0,.54,.001)],dark,'thigh.'+side)
    panel('Ashveil | trailing side cloth.'+side,[(s*.16,.14,1.10,.08),(s*.20,.16,.89,.095),(s*.22,.15,.69,.06),(s*.23,.14,.50,.001)],ash,'thigh.'+side)
# Etched mask lines and a pale embroidered tabard sigil.
for s in [-1,1]:
    line('Ashveil | mask engraved border',[(s*.084,-.094,1.79),(s*.047,-.133,1.76),(0,-.144,1.704)],.002,brass,'head')
    for j in range(3): line('Ashveil | mask etching',[(s*(.02+j*.019),-.143+j*.008,1.78),(s*.012,-.143,1.72+j*.009)],.0012,brass,'head')
line('Ashveil | embroidered sigil',[(.02+.034*math.cos(a),-.202,.78+.045*math.sin(a)) for a in np.linspace(0,2*math.pi,48)],.0025,rope,'tabard_front.02',True)
for a in [0,2.094,4.189]:
    line('Ashveil | sigil rays',[(.02,-.205,.78),(.02+.05*math.cos(a),-.205,.78+.06*math.sin(a))],.002,rope,'tabard_front.02')

# UV coordinates on newly authored parts, then retain the three existing clips.
parts=[o for o in col.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
new=[o for o in parts if not o.data.uv_layers]
for o in new: o.select_set(True)
if new:
    bpy.context.view_layer.objects.active=new[0]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(island_margin=.025); bpy.ops.object.mode_set(mode='OBJECT')
rig.data.pose_position='POSE'; rig.animation_data.action=action
rig['character']='Ashveil'; rig['reference']='User supplied Oathbreakers Ashveil ninja portfolio sheet.png'
scene['source_base']='Eliber CC0 base body; fitted skeleton reused from assassin; original Ashveil outfit interpretation.'
scene['character_notes']='Stylized interpretation; no weapon or smoke/teleport gameplay. Idle, Walk and Arm_Motion_Test clips retained.'
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for o in parts+[rig]: o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'ashveil.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_force_sampling=True,export_def_bones=True)
scene.render.resolution_x=800; scene.render.resolution_y=950; scene.cycles.samples=24
scene.render.filepath=os.path.join(OUT,'ashveil_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'ashveil.blend'))
bpy.ops.render.render(write_still=True)
print('ASHVEIL COMPLETE:',len(parts),'mesh parts')
