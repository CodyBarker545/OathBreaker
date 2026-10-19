"""Replace the hood/fringe with a complete reference-inspired layered golden hairstyle."""
import bpy,os,math,random,json,shutil
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
source=os.path.join(OUT,'assassin_refined.blend');backup=os.path.join(OUT,'backups','before_unhooded_hair');os.makedirs(backup,exist_ok=True)
for name in ['assassin_refined.blend','assassin_refined.glb']:
    if not os.path.exists(os.path.join(backup,name)):shutil.copy2(os.path.join(OUT,name),os.path.join(backup,name))
shutil.copy2(r'C:\Users\cody_\AppData\Local\Temp\codex-clipboard-0ff41e23-ddcc-45b9-ba60-77b01d7b6b81.png',os.path.join(OUT,'tousled_blond_hair_reference.png'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(backup,'assassin_refined.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;scene.frame_set(1);rig.data.pose_position='REST';random.seed(118)
for o in list(bpy.data.objects):
    if o.type=='MESH' and (o.name.startswith(('Hood','Hair •','Hair |'))):bpy.data.objects.remove(o,do_unlink=True)
collection=bpy.data.collections.new('ASSASSIN • unhooded tousled golden hair');scene.collection.children.link(collection)
def material(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.61;bs.inputs['Specular IOR Level'].default_value=.28
    if bs.inputs.get('Anisotropic'):bs.inputs['Anisotropic'].default_value=.28
    n=256;im=bpy.data.images.new(name+' • packed strand colour',width=n,height=n);pixels=[]
    for y in range(n):
        for x in range(n):
            grain=.95+.055*math.sin(x*1.7)+.030*math.sin(x*.53+y*.012)+random.uniform(-.012,.012)
            root=.82+.18*(y/n)
            pixels.extend([c*grain*root for c in color]+[1])
    im.pixels=pixels;im.pack();tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return m
gold=material('HAIR • natural warm golden blond',(.43,.31,.16))
light=material('HAIR • sunlit golden strands',(.54,.405,.23))
shade=material('HAIR • dark blond roots',(.29,.20,.10))
# Shared tangent-space micro-grooves export with the hair so the strand finish survives in Godot.
n=256;normal=bpy.data.images.new('HAIR • packed longitudinal strand normals',width=n,height=n);normal.colorspace_settings.name='Non-Color';pix=[]
for y in range(n):
    for x in range(n):
        nx=.12*math.cos(x*1.7)+.045*math.cos(x*.53+y*.012);v=Vector((-nx,.007*math.sin(y*.08),1)).normalized();pix.extend([v.x*.5+.5,v.y*.5+.5,v.z*.5+.5,1])
normal.pixels=pix;normal.pack()
for m in [gold,light,shade]:
    t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=normal;nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.33;m.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],m.node_tree.nodes.get('Principled BSDF').inputs['Normal'])
def mesh(name,vs,fs,mat,uvcoords):
    data=bpy.data.meshes.new(name);data.from_pydata(vs,[],fs);data.update();o=bpy.data.objects.new(name,data);collection.objects.link(o);data.materials.append(mat)
    import bmesh
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    uv=data.uv_layers.new(name='Longitudinal hair UV')
    for p in data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:uv.data[li].uv=uvcoords[data.loops[li].vertex_index]
    o.vertex_groups.new(name='head').add(list(range(len(data.vertices))),1,'REPLACE');o.parent=rig;mod=o.modifiers.new('Rigid head-following hairstyle','ARMATURE');mod.object=rig
    return o
center=Vector((0,.014,1.855))
vs=[];fs=[];uv=[];rows=18;cols=64
for j in range(rows):
    t=j/(rows-1)
    for k in range(cols):
        a=k/cols*math.tau
        # High natural front hairline, lower sideburn/nape coverage around the uncovered head.
        frontness=max(0,-math.sin(a));backness=max(0,math.sin(a));phi=.035+t*(1.58-.50*frontness+.55*backness)
        p=center+Vector((.111*math.sin(phi)*math.cos(a),.104*math.sin(phi)*math.sin(a),.137*math.cos(phi)))
        vs.append(p);uv.append((k/cols*3,t))
for j in range(rows-1):
    for k in range(cols):fs.append((j*cols+k,j*cols+(k+1)%cols,(j+1)*cols+(k+1)%cols,(j+1)*cols+k))
fs.append(tuple(range(cols-1,-1,-1)))
fs.append(tuple((rows-1)*cols+k for k in range(cols)))
mesh('Hair | full shaded scalp foundation',vs,fs,shade,uv)
def bezier(controls,t):
    a,b,c,d=[Vector(p) for p in controls];return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
def lock(name,controls,width,depth,mat=gold,ridges=True):
    count=26;sides=10;points=[bezier(controls,i/(count-1)) for i in range(count)];vs=[];fs=[];uv=[];frames=[]
    for j,p in enumerate(points):
        t=j/(count-1);tangent=(points[min(j+1,count-1)]-points[max(j-1,0)]).normalized();normal=(p-center).normalized()
        across=normal.cross(tangent)
        if across.length<.05:across=Vector((1,0,0))-tangent*tangent.x
        across.normalize();out=tangent.cross(across).normalized()
        if out.dot(normal)<0:out=-out
        frames.append((across,out))
        # Broad overlapping bases become thin feathered points; the cross-section stays flattened.
        taper=max(.012,(1-t)**.65);w=width*(.77+.23*math.sin(t*math.pi))*taper;d=depth*(.7+.3*math.sin(t*math.pi))*max(.06,(1-t)**.55)
        for k in range(sides):
            a=k/sides*math.tau;ridge=1+.10*math.cos(a*3)
            vs.append(p+across*math.cos(a)*w+out*math.sin(a)*d*ridge);uv.append((k/sides,t))
    for j in range(count-1):
        for k in range(sides):fs.append((j*sides+k,(j+1)*sides+k,(j+1)*sides+(k+1)%sides,j*sides+(k+1)%sides))
    fs.extend([tuple(range(sides-1,-1,-1)),tuple((count-1)*sides+k for k in range(sides))])
    mesh(name,vs,fs,mat,uv)
    if ridges:
        for offset in [-.27,.22]:
            verts=[];faces=[];uvs=[]
            for j,p in enumerate(points):
                t=j/(count-1);across,out=frames[j];w=width*(.77+.23*math.sin(t*math.pi))*max(.012,(1-t)**.65)
                d=depth*(.7+.3*math.sin(t*math.pi))*max(.06,(1-t)**.55)
                q=p+across*w*offset+out*(d*.97+.0003);r=.00055*(1-t)+.00012
                for k in range(5):
                    a=k/5*math.tau;verts.append(q+across*math.cos(a)*r+out*math.sin(a)*r);uvs.append((k/5,t))
            for j in range(count-1):
                for k in range(5):faces.append((j*5+k,(j+1)*5+k,(j+1)*5+(k+1)%5,j*5+(k+1)%5))
            mesh('Hair | fine tapered strand ridge',verts,faces,light if offset>0 else shade,uvs)
# Asymmetric side part: long overlapping fringe sweeps across one eye like the portrait.
fringe=[(-.122,1.792,.030),(-.101,1.827,.033),(-.078,1.805,.031),(-.054,1.837,.029),(-.027,1.866,.026),(.010,1.899,.025),(.054,1.865,.021),(.091,1.824,.020)]
for j,(tipx,tipz,width) in enumerate(fringe):
    rootx=.025+j*.004+random.uniform(-.008,.008)
    controls=[(rootx,.012+random.uniform(-.01,.02),1.984),(-.018+j*.006,-.034,2.002),(tipx-.010,-.109,1.929),(tipx,-.118+abs(tipx)*.20,tipz)]
    lock('Hair | sweeping asymmetric fringe %02d'%j,controls,width,.0085,gold if j not in [1,5] else light)
# Crown layers fan outward, with varied directions and heights instead of a uniform fringe row.
for j in range(16):
    a=-.35+j/16*math.tau;phi=.72+random.uniform(-.10,.10)
    root=center+Vector((.116*math.sin(phi)*math.cos(a),.109*math.sin(phi)*math.sin(a),.141*math.cos(phi)))
    radial=Vector((math.cos(a),math.sin(a),0))
    tip=Vector((.155*math.cos(a),.014+.143*math.sin(a),1.982+random.uniform(-.014,.035)))
    controls=[root,root+radial*.035+Vector((0,0,.025)),tip-radial*.025+Vector((0,0,.020)),tip]
    lock('Hair | tousled crown layer %02d'%j,controls,random.uniform(.029,.038),.010,gold if j%5 else light)
for j in range(9):
    a=j/9*math.tau+.22
    root=center+Vector((.042*math.cos(a),.041*math.sin(a),.135))
    tip=Vector((.110*math.cos(a),.014+.105*math.sin(a),2.025+random.uniform(-.009,.015)))
    controls=[root,root+Vector((.025*math.cos(a),.025*math.sin(a),.020)),tip-Vector((.018*math.cos(a),.018*math.sin(a),-.007)),tip]
    lock('Hair | overlapping upper crown %02d'%j,controls,.030,.010,gold if j%4 else light)
# Mid and lower back layers cover the skull and kick out at the nape.
for ring in range(3):
    for j in range(12):
        a=.02+j/11*(math.pi-.04);phi=.84+ring*.34
        root=center+Vector((.116*math.sin(phi)*math.cos(a),.111*math.sin(phi)*math.sin(a),.140*math.cos(phi)))
        tip=Vector((.145*math.cos(a),.02+.145*math.sin(a),1.905-ring*.062+random.uniform(-.014,.010)))
        controls=[root,root+Vector((.018*math.cos(a),.018*math.sin(a),.012)),tip+Vector((-.004*math.cos(a),-.004*math.sin(a),.030)),tip]
        lock('Hair | layered nape and back %d.%02d'%(ring,j),controls,.029,.009,gold if j%5 else shade)
# Temple and side locks are shorter on the exposed-ear side.
for sign in [-1,1]:
    for j in range(4):
        root=(sign*.110,-.016+j*.020,1.918-j*.015)
        tip=(sign*(.133+j*.004),-.018+j*.020,1.802-j*.014+( .028 if sign==1 and j<2 else 0))
        controls=[root,(sign*.128,-.018+j*.020,1.912-j*.014),(sign*.138,-.023+j*.020,1.855),tip]
        lock('Hair | feathered temple layer',controls,.026-j*.001,.008,gold)
# A few thin flyaway strands break the crown silhouette without becoming separate hair spikes.
for j in range(2):
    controls=[(.020,.02,1.998),(-.025+j*.025,-.005,2.039),(-.080+j*.045,-.008,2.053),(-.110+j*.07,-.004,2.025)]
    lock('Hair | crown flyaway',controls,.0015,.0007,light,False)
# Small ears are now visible at the sides of the uncovered head, partly hidden by hair.
skin=next(m for m in bpy.data.materials if m.name.startswith('REF • warm face'))
for sign in [-1,1]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(sign*.098,.001,1.803));ear=bpy.context.object;ear.name='Face | ear beneath layered hair';ear.scale=(.016,.014,.029);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ear.data.materials.append(skin)
    for c in list(ear.users_collection):c.objects.unlink(ear)
    collection.objects.link(ear)
    for p in ear.data.polygons:p.use_smooth=True
    ear.vertex_groups.new(name='head').add(list(range(len(ear.data.vertices))),1,'REPLACE');ear.parent=rig;mod=ear.modifiers.new('Head binding','ARMATURE');mod.object=rig
rig.data.pose_position='POSE';scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
assert not any(o.name.startswith('Hood') for o in meshes)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
note=bpy.data.texts.new('CURRENT HAIR • hood removed');note.write('Reference: tousled_blond_hair_reference.png\nHood removed by request. Full golden-blond layered crown, asymmetric long fringe, feathered side/nape coverage and fine strand ridges. Mask, outfit and anatomical hands retained; no weapons.\nPrior hooded source in backups/before_unhooded_hair.\n')
bpy.ops.wm.save_as_mainfile(filepath=source)
reportpath=os.path.join(OUT,'reference_update_report.json')
with open(reportpath) as f:report=json.load(f)
for o in meshes:o.data.calc_loop_triangles()
report.update(hood_retained=False,hair_style='full tousled golden blond with asymmetric fringe',hair_reference='tousled_blond_hair_reference.png',mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes))
with open(reportpath,'w') as f:json.dump(report,f,indent=2)
print('TOUSLED_HAIR_COMPLETE')
