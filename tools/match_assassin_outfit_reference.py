"""Fit the reference's layered dark armour and torn burgundy garments to the current rig."""
import bpy,os,math,random,json,shutil
from mathutils import Vector
from math import sin,cos,pi
ROOT=r'D:\SoftwareEng\Game';OUT=os.path.join(ROOT,'SourceAssets','characters','hooded_assassin','blendswap_assassin')
source=os.path.join(OUT,'assassin_refined.blend');backup=os.path.join(OUT,'backups','before_layered_outfit');os.makedirs(backup,exist_ok=True)
for n in ['assassin_refined.blend','assassin_refined.glb']:
    if not os.path.exists(os.path.join(backup,n)):shutil.copy2(os.path.join(OUT,n),os.path.join(backup,n))
shutil.copy2(r'C:\Users\cody_\AppData\Local\Temp\codex-clipboard-1ca16781-2924-4fae-a70a-38af16a15c26.png',os.path.join(OUT,'layered_outfit_reference.png'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(backup,'assassin_refined.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;scene.frame_set(1);rig.data.pose_position='REST';random.seed(704)
collection=bpy.data.collections.new('ASSASSIN • layered dark fantasy outfit');scene.collection.children.link(collection)
def material(name,color,metal=0,rough=.8,kind='leather'):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;bs.inputs['Sheen Weight'].default_value=.025 if kind=='cloth' else 0
    n=256;im=bpy.data.images.new(name+' • packed albedo',width=n,height=n);pixels=[]
    for y in range(n):
        for x in range(n):
            f=.9+random.uniform(-.055,.055)+.055*sin(x*.085+sin(y*.1))*cos(y*.067)
            if kind=='cloth':f+=.035*sin(x*pi)+.035*cos(y*pi)
            if kind=='metal' and random.random()<.006:f+=.25
            pixels.extend([min(1,max(0,c*f)) for c in color]+[1])
    im.pixels=pixels;im.pack();tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if kind=='cloth':
        old=bpy.data.images.get('Mask • packed woven thread normal')
        if old:
            t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=old;nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.25;m.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    return m
steel=material('OUTFIT • worn blackened steel',(.058,.065,.074),.78,.44,'metal')
edge=material('OUTFIT • exposed steel bevels',(.20,.22,.235),.82,.35,'metal')
bronze=material('OUTFIT • tarnished bronze borders',(.235,.145,.064),.73,.43,'metal')
black=material('OUTFIT • supple black leather',(.048,.037,.033),0,.82)
brown=material('OUTFIT • worn strap leather',(.105,.062,.037),0,.77)
cloth=material('OUTFIT • weathered burgundy linen',(.205,.022,.034),0,.94,'cloth')
clothlight=material('OUTFIT • raised burgundy folds',(.25,.034,.039),0,.94,'cloth')
thread=material('OUTFIT • faded ochre embroidery',(.25,.147,.047),0,.94,'cloth')
def bind(o,bone):
    o.vertex_groups.clear();o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;mod=o.modifiers.new('Outfit binding','ARMATURE');mod.object=rig
def mesh(name,vs,fs,mat,bone='chest',smooth=True):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);collection.objects.link(o);d.materials.append(mat)
    uv=d.uv_layers.new(name='Outfit UV')
    for p in d.polygons:
        p.use_smooth=smooth
        for li in p.loop_indices:
            v=d.vertices[d.loops[li].vertex_index].co;uv.data[li].uv=(v.x*3+v.y,v.z*3)
    if bone:bind(o,bone)
    return o
def tube(name,pts,radii,mat,bone='chest',sides=10):
    vs=[]
    for j,p in enumerate(pts):
        t=(Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(0,j-1)])).normalized();u=t.cross(Vector((0,0,1)))
        if u.length<.01:u=t.cross(Vector((0,1,0)))
        u.normalize();v=t.cross(u);r=radii[j];a,b=(r,r) if isinstance(r,(int,float)) else r
        for k in range(sides):vs.append(Vector(p)+u*cos(k*math.tau/sides)*a+v*sin(k*math.tau/sides)*b)
    fs=[tuple(range(sides-1,-1,-1))]
    for j in range(len(pts)-1):
        for k in range(sides):fs.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    fs.append(tuple((len(pts)-1)*sides+k for k in range(sides)))
    return mesh(name,vs,fs,mat,bone)
def line(name,a,b,r,mat,bone='chest'):return tube(name,[a,b],[r,r],mat,bone,8)
def stud(name,p,r=.005,bone='chest',mat=bronze):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=r,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o)
    for poly in o.data.polygons:poly.use_smooth=True
    bind(o,bone);return o
def box(name,p,size,mat,bone='pelvis',bevel=.004):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Worked edge radius','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    o.name=name;o.data.materials.append(mat)
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o);bind(o,bone);return o
def plate(name,outline,peak,mat=steel,bone='chest',rim=True):
    # Closed shallow forged shell; raised centre facets follow the underlying garment.
    n=len(outline);back=[Vector(p)+Vector((0,.007,0)) for p in outline];vs=list(outline)+back+[Vector(peak)];fs=[]
    for i in range(n):fs.append((i,(i+1)%n,2*n));fs.append((i,n+i,n+(i+1)%n,(i+1)%n))
    fs.append(tuple(range(2*n-1,n-1,-1)))
    o=mesh(name,vs,fs,mat,bone,False)
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    bevel=o.modifiers.new('Forged softened plate edges','BEVEL');bevel.width=.0025;bevel.segments=2
    if rim:tube(name+' • bronze rolled border',list(outline)+[outline[0]],[.0028]*(n+1),bronze,bone,7)
    return o
remove=('Dished shoulder','Rolled shoulder','Shoulder brass','Pauldron wear','Bracer band','Bracer steel','Bracer rivet','Leather bracer','Rounded steel knee','Knee rivet','Tall leather boot','Boot lace','Crossed boot lace','Greave strap','Scarf |','Burgundy cape','Scalloped leather skirt','Tasset edge','Utility pouch','Pouch overlapping','Pouch brass','Pouch seam','Wide belt','Belt buckle','Buckle inset','Harness rivet','Fitted diagonal leather harness','Harness fine stitching','Tailored side seam','Boot | ankle strap','Boot | bronze buckle','Boot | curved steel toe')
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name.startswith(remove):bpy.data.objects.remove(o,do_unlink=True)
torso=bpy.data.objects['Continuous fitted leather torso'];torso.data.materials.clear();torso.data.materials.append(black)
for o in bpy.data.objects:
    if o.type!='MESH' or not any(m.type=='ARMATURE' for m in o.modifiers):continue
    if o.name.startswith(('Quilted leather sleeve','Padded thigh','Boot | shaped','Boot | articulated','Boot | welted')):
        o.data.materials.clear();o.data.materials.append(black)
def front(x,z,off=.008):
    # Ray-fit every chest component to the continuous torso instead of floating an oval plate above it.
    hit,p,n,i=torso.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
    return Vector((x,p.y-off if hit else -.145-off,z))
def weight_spine(o):
    o.vertex_groups.clear()
    for name in ['pelvis','lower_spine','mid_spine','chest']:o.vertex_groups.new(name=name)
    for v in o.data.vertices:
        z=(o.matrix_world@v.co).z;w=[math.exp(-((z-c)/.11)**2) for c in [1.06,1.17,1.34,1.52]];total=sum(w)
        for name,value in zip(['pelvis','lower_spine','mid_spine','chest'],w):o.vertex_groups[name].add([v.index],value/total,'REPLACE')
# Overlapping fitted breast and abdominal plates, with a continuous leather core underneath.
for sign in [-1,1]:
    outline=[front(sign*x,z) for x,z in [(.015,1.548),(.153,1.535),(.180,1.466),(.12,1.386),(.032,1.407)]]
    o=plate('Fitted blackened breastplate',outline,front(sign*.088,1.47,.017));weight_spine(o)
    for x,z in [(.04,1.52),(.14,1.49),(.09,1.41)]:stud('Chest plate rivet',front(sign*x,z,.019),.0045)
for j in range(3):
    z=1.37-j*.068;w=.160-j*.007
    outline=[front(-w,z+.014,.013),front(w,z+.014,.013),front(w*.88,z-.036,.013),front(0,z-.060,.013),front(-w*.88,z-.036,.013)]
    o=plate('Articulated abdominal lame',outline,front(0,z-.01,.022),steel,'mid_spine');weight_spine(o)
# Angular shoulder shells, stepped rims and short integral armour points.
for sign,side in [(1,'R'),(-1,'L')]:
    arm='upper_arm.'+side;fore='forearm.'+side;shin='shin.'+side;foot='foot.'+side
    for j in range(3):
        cx=sign*(.270+j*.040);z=1.61-j*.064;scale=1-j*.10
        local=[(-.100,-.065,-.010),(-.067,-.138,.002),(.047,-.145,-.025),(.148,-.063,-.095),(.127,.075,-.070),(.015,.126,-.015),(-.090,.080,.007)]
        points=[Vector((cx+sign*x*scale,y*scale,z+zz)) for x,y,zz in local]
        plate('Layered pointed pauldron.'+side,points,(cx,-.009,z+.038),steel,arm)
        for idx in [1,2,4]:stud('Pauldron fastener',points[idx]+Vector((0,-.003,.008)),.005,arm)
    tube('Short pauldron crest.'+side,[(sign*.290,.045,1.625),(sign*.312,.09,1.702),(sign*.32,.115,1.735)],[.025,.014,.001],steel,arm,10)
    # Forearm splints are fitted over a dark leather wrap.
    tube('Fitted wrapped bracer.'+side,[(sign*.389,-.012,1.276),(sign*.43,-.030,1.16),(sign*.47,-.046,1.055)],[.070,.070,.052],brown,fore,20)
    poly=[(sign*.365,-.088,1.274),(sign*.425,-.106,1.282),(sign*.501,-.111,1.077),(sign*.47,-.127,1.043),(sign*.426,-.117,1.09)]
    plate('Tapered steel vambrace.'+side,poly,(sign*.440,-.145,1.174),steel,fore)
    for j in range(3):
        z=1.08+j*.077;x=sign*(.465-j*.030)
        tube('Bracer leather binding.'+side,[(x-.056,-.04,z),(x-.035,-.10,z+.014),(x+.038,-.10,z+.014),(x+.059,-.03,z)],[.006]*4,black,fore)
    # A leather shin foundation and a long ridged plate taper into the articulated boot.
    tube('Fitted black boot shaft.'+side,[(sign*.18,.005,.15),(sign*.175,.002,.35),(sign*.165,-.004,.56)],[.074,.079,.076],black,shin,20)
    cx=sign*.167
    poly=[(cx,-.105,.736),(cx+.082,-.103,.659),(cx+.063,-.138,.566),(cx,-.153,.524),(cx-.063,-.138,.566),(cx-.082,-.103,.659)]
    plate('Faceted diamond knee guard.'+side,poly,(cx,-.179,.64),steel,shin)
    poly=[(cx-.062,-.09,.559),(cx+.062,-.09,.559),(sign*.228,-.094,.238),(sign*.18,-.138,.167),(sign*.125,-.094,.238)]
    plate('Long ridged greave.'+side,poly,(sign*.174,-.165,.39),steel,shin)
    # Narrow secondary ridges give the shin armour a forged multi-layer profile.
    for dx in [-.036,.036]:
        tube('Greave raised bronze ridge.'+side,[(cx+dx,-.119,.545),(cx+dx*.7,-.147,.39),(sign*.18+dx*.45,-.128,.22)],[.0028,.003,.0015],bronze,shin,7)
    for z in [.27,.49]:
        tube('Greave rear fastening.'+side,[(sign*.10,.02,z),(sign*.13,.077,z),(sign*.22,.077,z),(sign*.25,.015,z)],[.006]*4,brown,shin)
    # Foot plates remain on foot bones so the ankle can bend.
    for j in range(3):
        y=-.075-j*.058;z=.151-j*.028;rx=.071+j*.001
        poly=[(sign*.18-rx,y+.022,z-.014),(sign*.18,y+.027,z+.022),(sign*.18+rx,y+.022,z-.014),(sign*.18+rx,y-.028,z-.022),(sign*.18,y-.045,z-.009),(sign*.18-rx,y-.028,z-.022)]
        plate('Articulated boot sabaton.'+side,poly,(sign*.18,y-.005,z+.026),steel,foot)
    # Padded upper sleeves retain their original shape, with diagonal compression wraps.
    for j in range(3):
        x=sign*(.30+j*.026);z=1.46-j*.063
        tube('Upper arm leather wrap.'+side,[(x-sign*.060,-.028,z+.01),(x,-.080,z-.005),(x+sign*.065,-.020,z-.020)],[.006]*3,brown,arm)
# Broad crossing leather harnesses lie over the fitted plates.
for sign in [-1,1]:
    points=[front(sign*(.175-.32*t),1.555-.405*t,.034) for t in [j/24 for j in range(25)]]
    tube('Wide crossing leather baldric',points,[(.026,.007)]*len(points),brown)
    for j in range(15):
        t=j/14;x=sign*(.175-.32*t);z=1.555-.405*t
        line('Baldric edge stitch',front(x-.017,z,.044),front(x-.012,z+.005,.044),.0011,thread)
    p=front(sign*.07,1.43,.047)
    box('Baldric square buckle',p,(.057,.013,.043),bronze,'chest',.004)
    box('Baldric buckle leather inset',p+Vector((0,-.009,0)),(.038,.007,.027),black,'chest',.002)
# Two tilted waist belts, small buckles, keepers and discreet utility pouches.
for belt,zbase in enumerate([1.135,1.067]):
    pts=[]
    for k in range(81):
        a=k/80*math.tau;x=.202*cos(a);y=.151*sin(a);z=zbase+(.020 if belt==0 else -.016)*cos(a)
        pts.append((x,y,z))
    tube('Overlapping waist leather belt',pts,[(.020,.009)]*len(pts),brown,'pelvis',12)
    bx=.025 if belt==0 else -.045;bz=zbase
    outline=[(bx-.039,-.166,bz+.026),(bx+.037,-.166,bz+.026),(bx+.039,-.166,bz-.020),(bx,-.177,bz-.032),(bx-.039,-.166,bz-.020)]
    plate('Angular belt buckle',outline,(bx,-.185,bz),bronze,'pelvis',False)
    line('Buckle dark central bar',(bx-.022,-.188,bz),(bx+.022,-.188,bz),.006,black,'pelvis')
    for x in [-.15,-.105,.10,.15]:
        p=front(x,zbase,.030);box('Belt keeper',p,(.012,.015,.048),black,'pelvis',.002)
        stud('Belt keeper rivet',p+Vector((0,-.011,.013)),.0035,'pelvis')
for sign in [-1,1]:
    p=Vector((sign*.218,.012,1.045));box('Side utility pouch',p,(.080,.083,.128),brown,'pelvis',.012)
    box('Side pouch folded flap',p+Vector((0,-.049,.038)),(.087,.014,.044),black,'pelvis',.007)
    stud('Pouch clasp',p+Vector((0,-.06,.025)),.006,'pelvis')
# Tapered leather tassets and small overlying steel leaves protect the hips.
for sign,side in [(1,'R'),(-1,'L')]:
    for j in range(3):
        x=sign*(.092+j*.045);z=1.08-j*.028
        poly=[(x-sign*.036,-.160,z),(x+sign*.039,-.135,z+.005),(x+sign*.052,-.143,z-.153),(x+sign*.010,-.170,z-.202),(x-sign*.039,-.177,z-.165)]
        plate('Layered pointed leather tasset.'+side,poly,(x,-.189,z-.07),black,'pelvis')
        if j!=1:
            upper=[Vector(p) for p in poly[:2]]+[Vector((x+sign*.044,-.164,z-.071)),Vector((x,-.187,z-.096)),Vector((x-sign*.034,-.180,z-.061))]
            plate('Steel hip leaf.'+side,upper,(x,-.201,z-.039),steel,'pelvis')
        stud('Hip tasset rivet',(x,-.185,z-.018),.004,'pelvis')
# A triangular folded cowl replaces the three smooth scarf rings.
vs=[];fs=[];ns=80;rows=10
for j in range(rows):
    t=j/(rows-1);rx=.112+.080*t;ry=.098+.057*t
    for k in range(ns):
        a=k/ns*math.tau;frontness=max(0,-sin(a))
        z=1.716-.116*t-.105*t*frontness**2
        fold=.007*sin(t*pi*6+a*1.4)*sin(t*pi)
        vs.append(((rx+fold)*cos(a),(ry+fold)*sin(a),z))
for j in range(rows-1):
    for k in range(ns):fs.append((j*ns+k,(j+1)*ns+k,(j+1)*ns+(k+1)%ns,j*ns+(k+1)%ns))
cowl=mesh('Layered triangular burgundy neck cowl',vs,fs,cloth,'chest');sol=cowl.modifiers.new('Woven cowl thickness','SOLIDIFY');sol.thickness=.005
for j in [2,5,8]:
    points=[Vector(vs[j*ns+k])+Vector((0,-.001,.001)) for k in range(ns)]+[Vector(vs[j*ns])]
    tube('Cowl • raised irregular fold',points,[.0022]*len(points),clothlight,'chest',7)
def cloth_panel(name,sign,length,width,bonechain,back=False,stream=False):
    rows=23;cols=13;verts=[];faces=[]
    # Shared sampling for the cloth and its fading embroidered border.
    def pos(t,u):
        if stream:
            x=-.11-.57*t;y=.13+.10*t+.015*cos(u*pi*2)*sin(t*pi);z=1.65-.23*t+u*width*(.7+.3*t)+.04*sin(t*pi)
        elif back:
            x=.035+.12*t+u*width*(.65+.35*t);y=.135+.20*t+.026*cos(u*pi*3)*sin(t*pi);z=1.64-length*t
        else:
            x=sign*(.065+.19*t)+u*width*(.75+.25*t)+.045*sin(t*pi);y=-.177-.028*sin(t*pi)+.018*cos(u*pi*3)*sin(t*pi);z=1.073-length*t
        # Torn cloth has uneven side edges and deep, irregular splits in its lower third.
        if abs(u)>.95:x+=.010*sin(t*39+sign*3)*t
        return Vector((x,y,z))
    for j in range(rows):
        t=j/(rows-1)
        for k in range(cols):
            u=k/(cols-1)*2-1;p=pos(t,u)
            if j==rows-1:p.z+=random.uniform(0,.10 if not stream else .035)
            verts.append(p)
    for j in range(rows-1):
        for k in range(cols-1):
            # Multiple narrow slits, rather than a uniform zigzag hem.
            if j>rows-6 and k in [2,8] and j>rows-(5 if k==2 else 4):continue
            if j>rows-3 and k in [0,5,11]:continue
            faces.append((j*cols+k,(j+1)*cols+k,(j+1)*cols+k+1,j*cols+k+1))
    o=mesh(name,verts,faces,cloth,None)
    for n in bonechain:o.vertex_groups.new(name=n)
    for v in o.data.vertices:
        t=(v.index//cols)/(rows-1);w=t*(len(bonechain)-1);a=min(len(bonechain)-2,int(w));f=w-a
        o.vertex_groups[a].add([v.index],1-f,'REPLACE');o.vertex_groups[a+1].add([v.index],f,'REPLACE')
    o.parent=rig;arm=o.modifiers.new('Weighted cloth chain','ARMATURE');arm.object=rig;sol=o.modifiers.new('Soft torn cloth thickness','SOLIDIFY');sol.thickness=.003
    # Broken embroidery follows the draped surface. Its segments share the cloth weights.
    for side in [-1,1]:
        for section in range(8):
            t=.16+section*.082
            if section in [3,6]:continue
            pts=[pos(t,side*.80),pos(t+.022,side*.75),pos(t+.043,side*.82)]
            pts=[p+Vector((0,.004 if back or stream else -.004,0)) for p in pts]
            detail=tube('Faded broken cloth embroidery',pts,[.0013]*3,thread,bonechain[0],6)
            detail.vertex_groups.clear()
            for n in bonechain:detail.vertex_groups.new(name=n)
            for v in detail.data.vertices:
                a=min(len(bonechain)-2,int(t*(len(bonechain)-1)));f=t*(len(bonechain)-1)-a
                detail.vertex_groups[a].add([v.index],1-f,'REPLACE');detail.vertex_groups[a+1].add([v.index],f,'REPLACE')
    return o
cloth_panel('Long torn front burgundy sash',1,.77,.105,['tabard_front.00','tabard_front.01','tabard_front.02'])
cloth_panel('Split side burgundy sash',-1,.60,.074,['tabard_side.00','tabard_side.01','tabard_side.02'])
cloth_panel('Tattered back cloak',1,1.14,.19,['scarf_back.00','scarf_back.01','scarf_back.02','scarf_back.03'],back=True)
cloth_panel('Wind-torn shoulder scarf stream',-1,.25,.065,['scarf_side.00','scarf_side.01','scarf_side.02'],stream=True)
# Restrained scratches and chipped edges on metal catch light at game viewing distances.
for sign,side in [(1,'R'),(-1,'L')]:
    for j in range(7):
        x=sign*(.23+j*.018);z=1.647-j*.012
        line('Pauldron worn edge',(x,-.111,z),(x+sign*.013,-.116,z+.005),.0011,edge,'upper_arm.'+side)
    for j in range(3):
        x=sign*.167+(j-1)*.022
        line('Greave shallow abrasion',(x,-.153,.36+j*.036),(x+.017,-.157,.374+j*.036),.001,edge,'shin.'+side)
# Neutral studio lighting makes the reference's blackened steel and bronze readable.
for light in list(bpy.data.objects):
    if light.type=='LIGHT':bpy.data.objects.remove(light,do_unlink=True)
def studio_light(name,pos,power,color,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1.05))-obj.location).to_track_quat('-Z','Y').to_euler()
studio_light('STUDIO • neutral warm key',(-3,-4,5),450,(1,.90,.79),4)
studio_light('STUDIO • cool soft fill',(4,-2,3),230,(.72,.83,1),3)
studio_light('STUDIO • neutral armour rim',(1,3,4),600,(.90,.94,1),3)
# Keep the continuous torso, anatomical hands, hood/mask/hair and all original actions.
rig.data.pose_position='POSE';scene.frame_set(1)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
assert not any('weapon' in o.name.lower() or 'dagger' in o.name.lower() for o in meshes)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_refined.glb'),export_format='GLB',use_selection=True,export_animations=True,export_yup=True,export_apply=False)
shutil.copy2(os.path.join(OUT,'assassin_refined.glb'),os.path.join(ROOT,'Assets','Characters','Assassin','Assassin.glb'))
notes=bpy.data.texts.new('CURRENT OUTFIT • layered dark fantasy reference');notes.write('Reference: layered_outfit_reference.png\nWeapons intentionally omitted. Current hood, mask, hair and human hands retained.\nDark fitted torso, blackened stepped armour, bronze rolled borders, crossed leather straps, two waist belts, pointed hip tassets, long torn burgundy sashes/cape and faded cloth embroidery.\nOriginal skeleton/actions retained; cloth uses existing scarf/tabard chains.\nBaseline backup: backups/before_layered_outfit.\n')
bpy.ops.wm.save_as_mainfile(filepath=source)
reportpath=os.path.join(OUT,'reference_update_report.json')
with open(reportpath) as f:report=json.load(f)
for o in meshes:o.data.calc_loop_triangles()
report.update(outfit_reference='layered_outfit_reference.png',mesh_objects=len(meshes),triangles=sum(len(o.data.loop_triangles) for o in meshes),weapons_included=False)
with open(reportpath,'w') as f:json.dump(report,f,indent=2)
print('LAYERED_OUTFIT_COMPLETE',len(meshes))
