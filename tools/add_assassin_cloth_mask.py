"""Add a soft woven face wrap to the current assassin, preserving all other geometry."""
import bpy,os,math,random,json,shutil
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
source=os.path.join(OUT,'assassin_refined.blend');backup=os.path.join(OUT,'backups','before_cloth_mask');os.makedirs(backup,exist_ok=True)
for n in ['assassin_refined.blend','assassin_refined.glb']:
    if not os.path.exists(os.path.join(backup,n)):shutil.copy2(os.path.join(OUT,n),os.path.join(backup,n))
bpy.ops.wm.open_mainfile(filepath=source)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;scene.frame_set(1);rig.data.pose_position='REST'
for o in list(bpy.data.objects):
    if o.name.startswith('Cloth mask •'):bpy.data.objects.remove(o,do_unlink=True)
collection=bpy.data.collections.new('ASSASSIN • woven fabric face wrap');scene.collection.children.link(collection)
random.seed(42)
mat=bpy.data.materials.new('Mask • soft charcoal woven linen');mat.use_nodes=True;mat.diffuse_color=(.19,.18,.20,1)
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.94;bs.inputs['Sheen Weight'].default_value=.38;bs.inputs['Sheen Roughness'].default_value=.75;bs.inputs['Specular IOR Level'].default_value=.23
size=512;albedo=bpy.data.images.new('Mask • packed woven charcoal albedo',width=size,height=size);normal=bpy.data.images.new('Mask • packed woven thread normal',width=size,height=size);normal.colorspace_settings.name='Non-Color';colors=[];normals=[]
for y in range(size):
    for x in range(size):
        a=x*math.tau/8;b=y*math.tau/8
        warp=math.sin(a);weft=math.sin(b);over=1 if (x//8+y//8)%2 else -1
        shade=.95+.065*warp+.055*weft+.025*over+random.uniform(-.025,.025)
        colors.extend([.19*shade,.18*shade,.20*shade,1])
        nx=.17*math.cos(a)*(1 if over>0 else .45);ny=.17*math.cos(b)*(1 if over<0 else .45);v=Vector((-nx,-ny,1)).normalized();normals.extend([v.x*.5+.5,v.y*.5+.5,v.z*.5+.5,1])
albedo.pixels=colors;normal.pixels=normals;albedo.pack();normal.pack()
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
nt=mat.node_tree.nodes.new('ShaderNodeTexImage');nt.image=normal;nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.45;mat.node_tree.links.new(nt.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
thread=bpy.data.materials.new('Mask • muted cloth seam thread');thread.use_nodes=True;pbs=thread.node_tree.nodes.get('Principled BSDF');pbs.inputs['Base Color'].default_value=(.095,.085,.091,1);pbs.inputs['Roughness'].default_value=.95
def finish(o):
    for p in o.data.polygons:p.use_smooth=True
    o.vertex_groups.clear();o.vertex_groups.new(name='head').add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig
    arm=o.modifiers.new('Follows head beneath hood','ARMATURE');arm.object=rig
    return o
def position(u,t,offset=0):
    theta=u*1.34
    top=1.804-.010*abs(u)**.8
    bottom=1.678+.034*abs(u)**1.3
    z=top*(1-t)+bottom*t
    x=.106*math.sin(theta)
    base=.100-.009*t
    nose=.028*math.exp(-(u/.33)**2)*math.exp(-((t-.22)/.27)**2)
    # Irregular diagonal folds and side gathering, with a soft under-chin drape.
    fold=.0048*math.sin(t*math.pi*5.5+u*1.7+.4*math.sin(u*5))*math.sin(t*math.pi)**.7
    gather=.0035*math.sin(t*math.pi*10+abs(u)*4)*abs(u)**3*math.sin(t*math.pi)
    drape=.006*math.sin(t*math.pi)
    y=-(base+nose+fold+gather+drape)*math.cos(theta)-offset
    return Vector((x,y,z))
verts=[];faces=[];cols=81;rows=41
for j in range(rows):
    for k in range(cols):verts.append(position(k/(cols-1)*2-1,j/(rows-1)))
for j in range(rows-1):
    for k in range(cols-1):faces.append((j*cols+k,j*cols+k+1,(j+1)*cols+k+1,(j+1)*cols+k))
data=bpy.data.meshes.new('Soft draped mask surface');data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new('Cloth mask • draped woven face wrap',data);collection.objects.link(o);data.materials.append(mat)
uv=data.uv_layers.new(name='Fabric weave UV')
for p in data.polygons:
    for li in p.loop_indices:
        i=data.loops[li].vertex_index;uv.data[li].uv=((i%cols)/(cols-1)*2,(i//cols)/(rows-1))
sol=o.modifiers.new('Thin cloth with soft hem','SOLIDIFY');sol.thickness=.0012;sol.offset=0
bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name);finish(o)
def curve(name,points,radius,material):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=radius;d.bevel_resolution=2;s=d.splines.new('POLY');s.points.add(len(points)-1)
    for point,p in zip(s.points,points):point.co=(*p,1)
    o=bpy.data.objects.new(name,d);collection.objects.link(o);d.materials.append(material);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');return finish(bpy.context.object)
for t,name in [(0,'upper nose hem'),(1,'soft lower hem')]:
    curve('Cloth mask • '+name,[position(i/80*2-1,t,.0007) for i in range(81)],.00135,mat)
    for i in range(34):
        u=-.94+i/33*1.88;ts=.025 if t==0 else .975
        curve('Cloth mask • fine hem stitch',[position(u,ts,.0017),position(u+.015,ts,.0017)],.00035,thread)
# The wrap extends around the cheeks beneath the hood; short ties remain tucked inside it.
for sign in [-1,1]:
    curve('Cloth mask • tucked cheek tie',[(sign*.102,-.024,1.765),(sign*.114,.020,1.765),(sign*.108,.059,1.766)],.006,mat)
rig.data.pose_position='POSE';scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
notes=bpy.data.texts.new('CURRENT • fabric mask restored');notes.write('Current preferences: hood and soft fabric mask, no weapons.\nMask: draped folds, gathered cheeks, fine stitched hems, packed weave albedo and normal textures, soft sheen, thin cloth thickness. Bound to the head.\nHands and continuous torso preserved.\n')
bpy.ops.wm.save_as_mainfile(filepath=source)
report_path=os.path.join(OUT,'reference_update_report.json')
with open(report_path) as f:report=json.load(f)
for o in meshes:o.data.calc_loop_triangles()
report.update(mask_retained=True,mask_style='soft draped woven fabric',mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes))
with open(report_path,'w') as f:json.dump(report,f,indent=2)
print('CLOTH_MASK_COMPLETE')
