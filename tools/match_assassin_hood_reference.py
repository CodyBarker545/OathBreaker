"""Reference-driven hood, layered ash-blond hair and fitted dark fabric mask."""
import bpy,os,math,random,json,shutil
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
source=os.path.join(OUT,'assassin_refined.blend');backup=os.path.join(OUT,'backups','before_dark_hood_reference');os.makedirs(backup,exist_ok=True)
for n in ['assassin_refined.blend','assassin_refined.glb']:
    if not os.path.exists(os.path.join(backup,n)):shutil.copy2(os.path.join(OUT,n),os.path.join(backup,n))
shutil.copy2(r'C:\Users\cody_\AppData\Local\Temp\codex-clipboard-81105f00-8816-442f-936e-e3c7cbf30c83.png',os.path.join(OUT,'hood_mask_hair_reference.png'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(backup,'assassin_refined.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;scene.frame_set(1);rig.data.pose_position='REST'
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.startswith(('Hood |','Hood •','Hood stitched','Hair •','Cloth mask •')):bpy.data.objects.remove(o,do_unlink=True)
collection=bpy.data.collections.new('ASSASSIN • dark hood reference');scene.collection.children.link(collection)
random.seed(506)
def material(name,color,rough=.85,sheen=.06,strands=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough;bs.inputs['Sheen Weight'].default_value=sheen;bs.inputs['Specular IOR Level'].default_value=.22
    n=256;im=bpy.data.images.new(name+' albedo',width=n,height=n);pixels=[]
    for y in range(n):
        for x in range(n):
            if strands:f=.96+.045*math.sin(x*1.7)+.025*math.sin(x*.49+y*.012)
            else:f=.94+random.uniform(-.04,.04)+.018*math.sin(x*math.pi)+.018*math.sin(y*math.pi)
            pixels.extend([c*f for c in color]+[1])
    im.pixels=pixels;im.pack();tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return m
hoodmat=material('STYLE • weathered charcoal hood',(.022,.020,.028),.96,.006)
liningmat=material('STYLE • deep hood lining',(.035,.030,.040),.98,.005)
seammat=material('STYLE • charcoal cloth seams',(.105,.09,.115),.96,.01)
hairmat=material('STYLE • ash blond hair',(.62,.565,.445),.67,.05,True)
hairlight=material('STYLE • pale blond strands',(.75,.69,.56),.62,.05,True)
hairshade=material('STYLE • blond roots and shadow',(.39,.34,.255),.76,.03,True)
maskmat=bpy.data.materials['Mask • soft charcoal woven linen'].copy();maskmat.name='STYLE • dark fitted woven mask'
bs=maskmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Sheen Weight'].default_value=.045;bs.inputs['Specular IOR Level'].default_value=.16;bs.inputs['Roughness'].default_value=.94
for node in maskmat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image and 'albedo' in node.image.name:
        image=node.image.copy();image.name='STYLE • packed dark mask weave';p=list(image.pixels)
        for i in range(0,len(p),4):p[i]*=.46;p[i+1]*=.44;p[i+2]*=.47
        image.pixels=p;image.pack();node.image=image
def finish(o,material):
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    o.vertex_groups.new(name='head').add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;mod=o.modifiers.new('Head binding','ARMATURE');mod.object=rig
    return o
def mesh(name,vs,fs,material,uvcoords=None):
    data=bpy.data.meshes.new(name);data.from_pydata(vs,[],fs);data.update();o=bpy.data.objects.new(name,data);collection.objects.link(o)
    layer=data.uv_layers.new(name='Style UV')
    for p in data.polygons:
        for li in p.loop_indices:
            i=data.loops[li].vertex_index;v=data.vertices[i].co;layer.data[li].uv=uvcoords[i] if uvcoords else (v.x*4+v.y,v.z*4)
    return finish(o,material)
def tube(name,points,radii,material,sides=8):
    vs=[]
    for j,p in enumerate(points):
        d=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=d.cross(Vector((0,1,0)))
        u.normalize();v=d.cross(u);r=radii[j];a,b=(r,r) if isinstance(r,(int,float)) else r
        for k in range(sides):vs.append(Vector(p)+u*math.cos(k*math.tau/sides)*a+v*math.sin(k*math.tau/sides)*b)
    fs=[tuple(range(sides-1,-1,-1))]
    for j in range(len(points)-1):
        for k in range(sides):fs.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    fs.append(tuple((len(points)-1)*sides+k for k in range(sides)))
    return mesh(name,vs,fs,material)
# Close-fitting cowl: opening edges frame the face; the crown slopes into a small point.
rings=[(1.655,.124,.103,1.02),(1.70,.128,.113,1.04),(1.77,.133,.125,1.06),(1.84,.136,.130,1.02),(1.905,.128,.124,.94),(1.955,.108,.108,.72),(1.982,.070,.080,.48),(1.998,.020,.032,.18)]
ns=57;vs=[];uvs=[];fs=[]
for row,(z,rx,ry,opening) in enumerate(rings):
    for k in range(ns):
        t=k/(ns-1);a=opening+(math.tau-2*opening)*t
        folds=.0045*math.cos(a*5+row*.55)+.0025*math.sin(a*9-row*.6)
        foldstrength=math.sin(t*math.pi)**.6
        radial=folds*foldstrength
        x=(rx+radial)*math.sin(a);y=.018-(ry+radial)*math.cos(a)
        zz=z+( .010*math.sin(a*5)**2 if row==0 else 0)
        vs.append((x,y,zz));uvs.append((t*2,row/(len(rings)-1)))
for row in range(len(rings)-1):
    for k in range(ns-1):fs.append((row*ns+k,row*ns+k+1,(row+1)*ns+k+1,(row+1)*ns+k))
top=len(vs);vs.append((0,.016,2.007));uvs.append((.5,1))
for k in range(ns-1):fs.append(((len(rings)-1)*ns+k,(len(rings)-1)*ns+k+1,top))
hood=mesh('Hood | tailored pointed charcoal cowl',vs,fs,hoodmat,uvs)
sol=hood.modifiers.new('Cloth thickness and lining','SOLIDIFY');sol.thickness=.0028;sol.offset=-1;hood.data.materials.append(liningmat);sol.material_offset=1
# Narrow cloth piping along the face opening, rather than a thick rounded hood edge.
for k in [0,ns-1]:
    points=[Vector(vs[row*ns+k])+Vector((0,-.0006,0)) for row in range(len(rings))]
    tube('Hood • soft face opening hem',points,[.0025]*len(points),hoodmat)
# Fold seams run down the back and break up the silhouette in profile.
for a in [2.25,math.pi,4.03]:
    pts=[]
    for row,(z,rx,ry,opening) in enumerate(rings[:-1]):
        pts.append(((rx+.001)*math.sin(a),.018-(ry+.002)*math.cos(a),z+.003))
    tube('Hood • back panel seam',pts,[.0013]*len(pts),seammat,6)
# Smaller, flattened layered locks. Roots stay inside the opening instead of sitting on its rim.
def bezier(points,t):
    a,b,c,d=[Vector(p) for p in points];return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
# The scalp is a shallow crown, only visible through gaps between the layered fringe.
capvs=[];capfs=[]
for j in range(10):
    phi=.06+j/9*1.30
    for k in range(32):
        a=k*math.tau/32;capvs.append((.099*math.sin(phi)*math.cos(a),.012+.079*math.sin(phi)*math.sin(a),1.909+.055*math.cos(phi)))
for j in range(9):
    for k in range(32):capfs.append((j*32+k,j*32+(k+1)%32,(j+1)*32+(k+1)%32,(j+1)*32+k))
mesh('Hair • shaded scalp beneath cowl',capvs,capfs,hairshade)
locks=[(-.080,-.105,1.800),(-.066,-.092,1.835),(-.057,-.078,1.866),(-.044,-.053,1.891),(-.031,-.025,1.867),(-.018,-.012,1.840),(-.004,.017,1.881),(.010,.039,1.906),(.025,.052,1.865),(.039,.064,1.840),(.054,.086,1.816),(.066,.101,1.792)]
for j,(rootx,tipx,tipz) in enumerate(locks):
    rootz=1.956+random.uniform(-.006,.008)
    controls=[(rootx,.010,rootz),(rootx-.015,-.056,1.976),(tipx-.014,-.108,1.922),(tipx,-.105+abs(tipx)*.24,tipz)]
    pts=[bezier(controls,k/24) for k in range(25)]
    # Fixed left/right ribbon direction gives a flat organic hair sheet, avoiding round sausages.
    verts=[];uv=[];faces=[];basewidth=random.uniform(.0075,.0125)
    for k,p in enumerate(pts):
        t=k/24;width=basewidth*(.70+.30*math.sin(t*math.pi))*max(.015,(1-t)**.55)
        depth=.0028*(1-t)+.0003
        for dx,dy in [(-width,0),(0,-depth),(width,0),(0,depth)]:verts.append(p+Vector((dx,dy,0)))
        for u in [0,.5,1,.5]:uv.append((u,t))
    for k in range(24):
        for q in range(4):faces.append((k*4+q,k*4+(q+1)%4,(k+1)*4+(q+1)%4,(k+1)*4+q))
    faces.extend([(3,2,1,0),tuple(24*4+q for q in range(4))])
    mesh('Hair • layered ash blond fringe %02d'%j,verts,faces,hairmat if j%4 else hairlight,uv)
    for offset in [-.0022,.0018]:
        strandpts=[p+Vector((offset*(1-k/24),-.0030*(1-k/24)-.0003,.0003)) for k,p in enumerate(pts)]
        tube('Hair • individual fine strand',strandpts,[.0004*(1-k/25)+.0001 for k in range(25)],hairlight if offset>0 else hairshade,5)
# Fitted fabric mask follows the nose and gathers diagonally into the cheek ties.
def maskpoint(u,t,offset=0):
    theta=u*1.34;z=(1.802-.014*abs(u))*(1-t)+(1.695+.040*abs(u)**1.3)*t
    nose=.026*math.exp(-(u/.34)**2)*math.exp(-((t-.19)/.28)**2)
    fold=.0034*math.sin(t*math.pi*4+u*2.4)*math.sin(t*math.pi)
    pinch=.0025*math.sin(t*math.pi*8+abs(u)*4)*abs(u)**2*math.sin(t*math.pi)
    y=-(.098-.006*t+nose+fold+pinch)*math.cos(theta)-offset
    return Vector((.105*math.sin(theta),y,z))
cols=73;rows=37;vs=[];fs=[];uv=[]
for j in range(rows):
    for k in range(cols):vs.append(maskpoint(k/(cols-1)*2-1,j/(rows-1)));uv.append((k/(cols-1)*2,j/(rows-1)))
for j in range(rows-1):
    for k in range(cols-1):fs.append((j*cols+k,(j+1)*cols+k,(j+1)*cols+k+1,j*cols+k+1))
mask=mesh('Cloth mask • draped woven face wrap',vs,fs,maskmat,uv);sol=mask.modifiers.new('Thin flexible fabric','SOLIDIFY');sol.thickness=.0012;sol.offset=0
for t in [0,1]:
    pts=[maskpoint(k/72*2-1,t,.0004) for k in range(73)]
    tube('Cloth mask • dark sewn hem',pts,[.0011]*len(pts),maskmat,6)
for sign in [-1,1]:tube('Cloth mask • tucked tie',[(sign*.102,-.021,1.77),(sign*.109,.018,1.77),(sign*.106,.052,1.77)],[.0045]*3,maskmat)
rig.data.pose_position='POSE';scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
note=bpy.data.texts.new('CURRENT STYLE • dark hood reference');note.write('Reference: hood_mask_hair_reference.png\nClose pointed charcoal hood with back panel folds. Dark fitted woven mask. Layered thin ash-blond fringe with roots beneath the cowl. Body, hands and weapons-free outfit retained.\n')
bpy.ops.wm.save_as_mainfile(filepath=source)
reportpath=os.path.join(OUT,'reference_update_report.json')
with open(reportpath) as f:report=json.load(f)
for o in meshes:o.data.calc_loop_triangles()
report.update(hood_style='close pointed charcoal cowl',hair_style='layered ash blond fringe',mask_style='dark fitted woven cloth',mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes))
with open(reportpath,'w') as f:json.dump(report,f,indent=2)
print('HOOD_REFERENCE_COMPLETE')
