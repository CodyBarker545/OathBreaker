"""Editable concept outfit on the preserved MPFB assassin. Execute through Blender MCP."""
import bpy,bmesh,math,json,random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi,tau
ROOT=Path(r'D:\SoftwareEng\Game')
OUT=ROOT/'SourceAssets/characters/hooded_assassin/outfit'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'SourceAssets/characters/hooded_assassin/face/assassin_detailed.blend'))
scene=bpy.context.scene
body=bpy.data.objects['Assassin_Body'];rig=bpy.data.objects['Assassin_Skeleton']
root=bpy.data.collections['Character_Assassin']
rig_before={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}
pose_before={b.name:[list(row) for row in b.matrix_basis] for b in rig.pose.bones}
body_before=[tuple(v.co) for v in body.data.vertices]
for name in ['Assassin_Short_Copper_Hair','Assassin_Full_Copper_Beard','Assassin_Copper_Eyebrows']:
    obj=bpy.data.objects.get(name)
    if obj:obj.hide_render=True;obj.hide_set(True)
for mod in body.modifiers:
    if mod.type=='SUBSURF':mod.show_viewport=False;mod.show_render=False
collections={}
for name in ['Head','Torso','Shoulders_Arms','Lower_Body','Red_Fabric']:
    c=bpy.data.collections.new('Outfit_'+name);root.children.link(c);collections[name]=c
added=[];rng=random.Random(60121)
def mat(name,mapname,metal=0,rough=.8):
    m=bpy.data.materials.new('GC_'+name);m.use_nodes=True
    n=m.node_tree.nodes;links=m.node_tree.links;bs=n.get('Principled BSDF')
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    bs.inputs['Specular IOR Level'].default_value=.28
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'textures'/(mapname+'_painted.png')))
    tex.interpolation='Linear';links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    # The broad gradients, edge wear, scratches and woven strokes live in the albedo.
    if mapname in ['tunic','hood','scarlet','leather','mask']:
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.1;bump.inputs['Distance'].default_value=.00035
        links.new(tex.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    m.diffuse_color=({'blacksteel':(.10,.11,.14,1),'gold':(.45,.29,.1,1),'scarlet':(.32,.025,.04,1),'blond':(.6,.43,.2,1),'blondlight':(.75,.58,.32,1)}.get(mapname,(.065,.055,.065,1)))
    return m
steel=mat('Painted_Blackened_Steel','blacksteel',.42,.55)
gold=mat('Tarnished_Bronze_Gold','gold',.5,.52)
leather=mat('Brown_Strap_Leather','leather',0,.85)
tunicmat=mat('Black_Fitted_Tunic','tunic')
red=mat('Deep_Red_Tattered_Linen','scarlet',0,.9)
hoodmat=mat('Charcoal_Hood','hood',0,.91)
maskmat=mat('Black_Lower_Face_Mask','mask',0,.93)
blond=mat('Layered_Ash_Blond','blond',0,.74)
blondlight=mat('Blond_Painted_Highlights','blondlight',0,.76)
blondshade=mat('Blond_Painted_Shadow','blondshade',0,.8)
def bind(obj,bone):
    obj.parent=rig
    obj.vertex_groups.new(name=bone).add(list(range(len(obj.data.vertices))),1,'REPLACE')
    mod=obj.modifiers.new('Preserved Assassin Skeleton','ARMATURE');mod.object=rig
def mesh(name,vs,fs,material,group='Torso',bone='spine_03',smooth=False,uvs=None):
    data=bpy.data.meshes.new(name);data.from_pydata(vs,[],fs);data.update()
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    obj=bpy.data.objects.new(name,data);collections[group].objects.link(obj);data.materials.append(material)
    uv=data.uv_layers.new(name='Painted_UV')
    mins=[min(v[i] for v in vs) for i in range(3)];maxs=[max(v[i] for v in vs) for i in range(3)]
    axes=sorted(range(3),key=lambda i:maxs[i]-mins[i],reverse=True)[:2]
    for poly in data.polygons:
        poly.use_smooth=smooth
        for li in poly.loop_indices:
            vi=data.loops[li].vertex_index;p=data.vertices[vi].co
            uv.data[li].uv=uvs[vi] if uvs else tuple((p[a]-mins[a])/max(.001,maxs[a]-mins[a]) for a in axes)
    if bone:bind(obj,bone)
    obj['editable_component']=True;obj['style']='GameCube fantasy / painted albedo'
    added.append(obj);return obj
def tube(name,points,radii,material,group='Torso',bone='spine_03',sides=6):
    vs=[];uvs=[]
    for i,p in enumerate(points):
        tangent=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        u=tangent.cross(Vector((0,0,1)))
        if u.length<.01:u=tangent.cross(Vector((0,1,0)))
        u.normalize();v=tangent.cross(u)
        a,b=radii[i] if isinstance(radii[i],(tuple,list)) else (radii[i],radii[i])
        for j in range(sides):
            angle=tau*j/sides
            vs.append(Vector(p)+u*cos(angle)*a+v*sin(angle)*b)
            uvs.append((j/sides,i/max(1,len(points)-1)))
    fs=[tuple(reversed(range(sides)))]
    for i in range(len(points)-1):
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    fs.append(tuple((len(points)-1)*sides+j for j in range(sides)))
    return mesh(name,vs,fs,material,group,bone,True,uvs)
def path(name,points,r,material,group='Torso',bone='spine_03',sides=5):return tube(name,points,[r]*len(points),material,group,bone,sides)
def plate(name,outline,peak,group='Torso',bone='spine_03',trim=True,material=steel):
    outline=[Vector(p) for p in outline];peak=Vector(peak);n=len(outline)
    normal=(outline[1]-outline[0]).cross(outline[2]-outline[0]).normalized()
    if normal.y>0:normal=-normal
    vs=outline+[p-normal*.005 for p in outline]+[peak]
    fs=[]
    for i in range(n):
        fs.extend([(i,(i+1)%n,2*n),(i,n+i,n+(i+1)%n,(i+1)%n)])
    fs.append(tuple(reversed(range(n,2*n))))
    obj=mesh(name,vs,fs,material,group,bone)
    if trim:path(name+'_Bronze_Border',outline+[outline[0]],.0018,gold,group,bone,4)
    return obj
def box(name,center,size,material,group='Torso',bone='pelvis'):
    x,y,z=center;a,b,c=[v/2 for v in size]
    vs=[(x+i*a,y+j*b,z+k*c) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,group,bone)
def buckle(name,center,width,height,group='Torso',bone='pelvis'):
    x,y,z=center
    outline=[(x-width/2,y,z-height/2),(x+width/2,y,z-height/2),(x+width/2,y,z+height/2),(x-width/2,y,z+height/2)]
    path(name,outline+[outline[0]],.003,gold,group,bone,4)
    path(name+'_Tongue',[(x-width*.35,y-.001,z),(x+width*.30,y-.001,z)],.0018,gold,group,bone,4)
def rivet(name,p,group='Torso',bone='spine_03',r=.003):
    p=Vector(p)
    return mesh(name,[p+Vector((0,-r,0)),p+Vector((-r,0,0)),p+Vector((0,0,r)),p+Vector((r,0,0)),p+Vector((0,0,-r))],[(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,4,3,2)],gold,group,bone)
def surface_copy(name,predicate,material,group,offset=.004):
    bodygroup=body.vertex_groups['body'].index
    visible={v.index for v in body.data.vertices if any(g.group==bodygroup and g.weight>.5 for g in v.groups)}
    faces=[p for p in body.data.polygons if all(i in visible for i in p.vertices) and predicate(sum((body.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices))]
    indices=sorted({i for p in faces for i in p.vertices});lookup={v:i for i,v in enumerate(indices)}
    vs=[body.data.vertices[i].co+body.data.vertices[i].normal*offset for i in indices]
    obj=mesh(name,vs,[tuple(lookup[i] for i in p.vertices) for p in faces],material,group,None,True)
    deform={g.index:g.name for g in body.vertex_groups if g.name in rig.data.bones}
    for g in deform.values():obj.vertex_groups.new(name=g)
    for i,source in enumerate(indices):
        for weight in body.data.vertices[source].groups:
            if weight.group in deform:obj.vertex_groups[deform[weight.group]].add([i],weight.weight,'REPLACE')
    obj.parent=rig;mod=obj.modifiers.new('Transferred Original Body Weights','ARMATURE');mod.object=rig
    return obj
def weight_spine(obj):
    for vg in list(obj.vertex_groups):obj.vertex_groups.remove(vg)
    centers=[('pelvis',1.0),('spine_01',1.08),('spine_02',1.16),('spine_03',1.35)]
    for n,z in centers:obj.vertex_groups.new(name=n)
    for v in obj.data.vertices:
        w=[math.exp(-((v.co.z-z)/.10)**2) for n,z in centers];total=sum(w)
        for (n,z),q in zip(centers,w):obj.vertex_groups[n].add([v.index],q/total,'REPLACE')
    obj.parent=rig
    if not any(m.type=='ARMATURE' for m in obj.modifiers):mod=obj.modifiers.new('Spine Skinning','ARMATURE');mod.object=rig
def ribbon(name,points,widths,material,group='Torso',bone='spine_03'):
    vs=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        side=Vector((-tangent.z,0,tangent.x)).normalized()*widths[i]/2
        vs.extend([Vector(p)-side,Vector(p)+side])
    fs=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)]
    obj=mesh(name,vs,fs,material,group,bone,True)
    return obj
# Fitted base garments retain the source skin weights, including the individual fingers.
surface_copy('Tunic_Black_Fitted_Long_Sleeves',lambda p:.94<p.z<1.53 and abs(p.x)<.735,tunicmat,'Torso',.006)
surface_copy('Trousers_Black_Armored_Underlayer',lambda p:.12<p.z<1.015 and abs(p.x)<.3,tunicmat,'Lower_Body',.006)
for side,sign in [('L',1),('R',-1)]:
    surface_copy('Glove_'+side+'_Full_Finger_Leather',lambda p,s=sign:s*p.x>.712,maskmat,'Shoulders_Arms',.003)
    surface_copy('Boot_'+side+'_Fitted_Leather_Upper',lambda p,s=sign:p.z<.365 and s*p.x>.06,leather,'Lower_Body',.008)
bpy.context.view_layer.update()
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
def front(x,z,off=.012):
    p,n,idx,d=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
    return Vector((x,(p.y if p else -.11)-off,z))
# Dark fitted lower-face mask, shaped over the bridge of the nose.
surface_copy('Mask_Black_Sculpted_Lower_Face',lambda p:1.55<p.z<1.638+.025*max(0,1-abs(p.x)/.085) and p.y<-.055 and abs(p.x)<.085,maskmat,'Head',.004)
for sign in [-1,1]:
    pts=[front(sign*x,z,.006) for x,z in [(0,1.663),(.025,1.658),(.055,1.647),(.078,1.639)]]
    path('Mask_Top_Stitch_'+str(sign),pts,.0007,hoodmat,'Head','head',4)
# Hood: a low-polygon cowl with an open face, inner lining and a pointed crown.
rings=[(1.535,.095,.135,.60),(1.60,.112,.153,.62),(1.69,.119,.160,.58),(1.77,.120,.158,.54),(1.82,.109,.145,.43),(1.855,.075,.100,.25),(1.873,.020,.036,.08)]
ns=25;vs=[];fs=[];uv=[]
for i,(z,rx,ry,opening) in enumerate(rings):
    for j in range(ns):
        t=j/(ns-1);a=opening+(tau-2*opening)*t
        fold=.0025*cos(6*a+i*.55)*sin(t*pi)
        vs.append(((rx+fold)*sin(a),-.04-(ry+fold)*cos(a),z+.002*cos(a*4)))
        uv.append((t,i/(len(rings)-1)))
for i in range(len(rings)-1):
    for j in range(ns-1):fs.append((i*ns+j,i*ns+j+1,(i+1)*ns+j+1,(i+1)*ns+j))
hood=mesh('Hood_Dark_Pointed_Cowl',vs,fs,hoodmat,'Head','head',True,uv)
solid=hood.modifiers.new('Editable Hood Thickness','SOLIDIFY');solid.thickness=.003;solid.offset=-1
for j,label in [(0,'L'),(ns-1,'R')]:
    pts=[Vector(vs[i*ns+j])+Vector((0,-.001,0)) for i in range(len(rings))]
    path('Hood_'+label+'_Face_Hem',pts,.002,hoodmat,'Head','head',5)
    path('Hood_'+label+'_Bronze_Stitch',pts[1:6],.00065,gold,'Head','head',4)
for a in [1.7,pi,4.58]:
    pts=[((rx+.001)*sin(a),-.04-(ry+.001)*cos(a),z) for z,rx,ry,opening in rings[:-1]]
    path('Hood_Panel_Seam',pts,.0008,leather,'Head','head',4)
# Angular layered hair locks, each an independent editable mesh.
def lock(name,control,width,material):
    a,b,c,d=[Vector(v) for v in control];pts=[];vs=[];uv=[];segments=6
    for i in range(segments):
        t=i/(segments-1)
        p=(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
        w=max(.00025,width*sin(pi*(.16+.84*t))**.75*(1-t)**.35)
        if i==segments-1:w=.0002
        tangent=(b-a) if i==0 else p-pts[-1]
        pts.append(p);side=tangent.cross(Vector((0,-1,0))).normalized()
        normal=side.cross(tangent).normalized()
        for j,(s,n) in enumerate([(-1,0),(0,1),(1,0),(0,-.3)]):
            vs.append(p+side*w*s+normal*w*.27*n);uv.append((j/3,t))
    fs=[]
    for i in range(segments-1):
        for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    fs.extend([(3,2,1,0),tuple((segments-1)*4+j for j in range(4))])
    return mesh(name,vs,fs,material,'Head','head',False,uv)
# The fringe falls below the hood opening and breaks into sharp anime-influenced points.
for sign,label in [(-1,'R'),(1,'L')]:
    for i in range(7):
        x=.009+i*.011
        control=[(sign*x*.40,-.095,1.815-i*.002),(sign*x*.65,-.17,1.812),(sign*(x+.012),-.193,1.736),(sign*(x+.003),-.192,1.670+(i%3)*.014)]
        lock('Hair_'+label+'_Long_Fringe_%02d'%i,control,.0105 if i<4 else .012,[blond,blondlight,blondshade][i%3])
    for i in range(5):
        x=.015+i*.014
        lock('Hair_'+label+'_Crown_Spike_%02d'%i,[(sign*x*.25,-.07,1.814),(sign*x,-.10,1.845),(sign*(x+.02),-.137,1.819),(sign*(x+.033),-.17,1.783-i*.007)],.012,[blondlight,blond,blond][i%3])
    for i in range(4):
        lock('Hair_'+label+'_Temple_Layer_%02d'%i,[(sign*.073,-.088,1.784-i*.014),(sign*.087,-.132,1.765-i*.014),(sign*.099,-.151,1.718-i*.014),(sign*(.089+i*.004),-.155,1.680-i*.009)],.010,blond if i%2 else blondshade)
    path('Blond_Brow_'+label,[(sign*.017,-.171,1.694),(sign*.033,-.175,1.698),(sign*.053,-.161,1.694)],.0015,blondshade,'Head','head',4)
lock('Hair_Central_Crown_Spike',[(0,-.075,1.813),(0,-.12,1.87),(0,-.15,1.837),(0,-.18,1.79)],.014,blondlight)
# Breastplate and articulated abdomen.
for sign,label in [(1,'L'),(-1,'R')]:
    outline=[front(sign*x,z,.014) for x,z in [(.006,1.435),(.105,1.457),(.180,1.408),(.169,1.335),(.100,1.283),(.015,1.306)]]
    plate('Chest_'+label+'_Black_Steel_Pectoral',outline,front(sign*.086,1.378,.035))
    for x,z in [(.035,1.422),(.145,1.396),(.10,1.31)]:rivet('Chest_'+label+'_Bronze_Rivet',front(sign*x,z,.026))
    # Engraved curling motifs cut across the painted plate face.
    pts=[front(sign*x,z,.038) for x,z in [(.026,1.405),(.066,1.382),(.12,1.39),(.131,1.371),(.10,1.353),(.07,1.362)]]
    path('Chest_'+label+'_Gold_Filigree',pts,.0012,gold)
for i,z in enumerate([1.275,1.213,1.154,1.101]):
    w=[.135,.124,.119,.126][i]
    outline=[front(x,zz,.017) for x,zz in [(-w,z+.035),(-w*.52,z+.047),(0,z+.027),(w*.52,z+.047),(w,z+.035),(w*.86,z-.022),(0,z-.039),(-w*.86,z-.022)]]
    o=plate('Abdomen_Overlapping_Steel_Lame_%02d'%i,outline,front(0,z,.030),bone='spine_02' if i<2 else 'spine_01')
for sign,label in [(1,'L'),(-1,'R')]:
    # Harness straps cross above the breastplates and continue around the waist.
    pts=[front(sign*x,z,.052) for x,z in [(.14,1.465),(.11,1.38),(.055,1.28),(-.008,1.16),(-.06,1.065)]]
    o=ribbon('Harness_'+label+'_Diagonal_Leather_Strap',pts,[.024]*len(pts),leather);weight_spine(o)
    buckle('Harness_'+label+'_Bronze_Buckle',front(sign*.08,1.33,.064),.030,.037,bone='spine_03')
    # Mirrored layered pauldrons follow the horizontal upper arms.
    for i in range(3):
        x=.218+i*.058;z=1.514-i*.012
        outline=[(sign*(x-.066),-.071,z+.030),(sign*(x-.025),-.130,z+.019),(sign*(x+.062),-.120,z-.010),(sign*(x+.078),-.087,z-.058),(sign*(x+.027),-.151,z-.043),(sign*(x-.053),-.137,z-.017)]
        plate('Pauldron_'+label+'_Layer_%02d'%i,outline,(sign*x,-.09,z+.053),'Shoulders_Arms','upperarm_'+label.lower())
        # An angular crown fin and smaller projecting spikes.
        tube('Pauldron_'+label+'_Crown_Spike_%02d'%i,[(sign*x,-.044,z+.035),(sign*(x+.020),-.034,z+.095),(sign*(x+.032),-.020,z+.135)],[.015,.008,.0003],steel,'Shoulders_Arms','upperarm_'+label.lower(),5)
        rivet('Pauldron_'+label+'_Rivet',(sign*x,-.153,z-.008),'Shoulders_Arms','upperarm_'+label.lower())
    # Upper arm cuffs and articulated elbow caps.
    for x in [.39,.468]:
        tube('Arm_'+label+'_Leather_Band',[(sign*(x-.012),-.013,1.467),(sign*(x+.012),-.013,1.467)],[(.049,.050),(.049,.050)],leather,'Shoulders_Arms','upperarm_'+label.lower() if x<.45 else 'lowerarm_'+label.lower(),10)
    # Bracer body and a faceted dark front plate.
    bone='lowerarm_'+label.lower()
    tube('Bracer_'+label+'_Leather_Underwrap',[(sign*.49,-.013,1.467),(sign*.59,-.013,1.467),(sign*.708,-.013,1.467)],[(.049,.046),(.043,.041),(.029,.028)],maskmat,'Shoulders_Arms',bone,12)
    outline=[(sign*.50,-.066,1.495),(sign*.56,-.080,1.514),(sign*.694,-.049,1.488),(sign*.718,-.048,1.464),(sign*.688,-.057,1.437),(sign*.535,-.074,1.429),(sign*.494,-.068,1.452)]
    plate('Bracer_'+label+'_Black_Steel_Plate',outline,(sign*.595,-.092,1.472),'Shoulders_Arms',bone)
    for x,r in [(.51,.049),(.681,.033)]:
        tube('Bracer_'+label+'_Bronze_Cuff',[(sign*(x-.004),-.013,1.467),(sign*(x+.004),-.013,1.467)],[(r,r),(r,r)],gold,'Shoulders_Arms',bone,10)
    tube('Bracer_'+label+'_Blade_Fin',[(sign*.535,-.025,1.502),(sign*.567,-.01,1.55),(sign*.62,-.009,1.52)],[.012,.007,.0003],steel,'Shoulders_Arms',bone,5)
    # Knuckle and individual phalanx plates retain separate finger bindings.
    plate('Glove_'+label+'_Backhand_Guard',[(sign*.745,-.042,1.484),(sign*.788,-.057,1.485),(sign*.832,-.031,1.488),(sign*.833,.034,1.484),(sign*.776,.029,1.483)],(sign*.792,-.007,1.503),'Shoulders_Arms','hand_'+label.lower())
    for finger in ['thumb','index','middle','ring','pinky']:
        for segment in [1,2,3]:
            b=rig.data.bones[f'{finger}_{segment:02d}_{label.lower()}'];a=b.head_local.copy();c=b.tail_local.copy()
            a.z+=.009;c.z+=.009
            d=(c-a).normalized();u=d.cross(Vector((0,0,1))).normalized()*.006
            outline=[a-u,a+u,c+u*.7,c-u*.7]
            plate(f'Finger_{label}_{finger}_{segment:02d}_Protection',outline,(a+c)*.5+Vector((0,0,.004)),'Shoulders_Arms',b.name,False)
# Three wrap belts with visible buckles and side pouches.
for i,z in enumerate([1.034,.989,.944]):
    vs=[];fs=[];n=32
    for row in [-1,1]:
        for j in range(n):
            a=tau*j/n;vs.append((.169*sin(a),-.013-.122*cos(a),z+row*.013+.015*cos(a*2+i*.7)))
    for j in range(n):fs.append((j,(j+1)%n,n+(j+1)%n,n+j))
    mesh('Belt_%02d_Leather_Wrap'%i,vs,fs,leather,'Lower_Body','pelvis',True)
    buckle('Belt_%02d_Bronze_Buckle'%i,((-.04 if i%2 else .04),-.148,z),.048,.034,'Lower_Body')
for sign,label in [(1,'L'),(-1,'R')]:
    for i in range(2):
        x=sign*(.169+i*.031);z=.965-i*.068
        box('Pouch_'+label+'_%02d_Leather_Body'%i,(x,.003,z),(.067,.075,.082),leather,'Lower_Body')
        plate('Pouch_'+label+'_%02d_Flap'%i,[(x-.034,-.039,z+.041),(x+.034,-.039,z+.041),(x+.031,-.047,z+.002),(x,-.052,z-.013),(x-.031,-.047,z+.002)],(x,-.054,z+.018),'Lower_Body','pelvis',False,leather)
        rivet('Pouch_'+label+'_Clasp',(x,-.056,z+.003),'Lower_Body','pelvis',.004)
    # Hip and thigh tassets form the angular skirt silhouette.
    for i in range(3):
        z=.918-i*.061;x=sign*(.132+i*.017)
        outline=[(x-sign*.055,-.128,z+.03),(x+sign*.049,-.106,z+.027),(x+sign*.060,-.103,z-.04),(x+sign*.005,-.153,z-.075),(x-sign*.044,-.151,z-.045)]
        plate('Tasset_'+label+'_Hip_Layer_%02d'%i,outline,(x,-.166,z-.01),'Lower_Body','thigh_'+label.lower())
    # Knee, greave, ankle and toe armor, laid over the weighted boot upper.
    knee=rig.data.bones['calf_'+label.lower()].head_local.copy();x=knee.x
    plate('Knee_'+label+'_Pointed_Guard',[(x-.052,-.105,.574),(x,-.128,.615),(x+.052,-.105,.574),(x+.050,-.108,.505),(x,-.138,.464),(x-.050,-.108,.505)],(x,-.155,.548),'Lower_Body','calf_'+label.lower())
    for i in range(3):
        z=.445-i*.105;xc=sign*(.150+i*.012)
        outline=[(xc-.046,-.075,z+.042),(xc,-.104,z+.068),(xc+.046,-.075,z+.042),(xc+.034,-.082,z-.05),(xc,-.118,z-.076),(xc-.034,-.082,z-.05)]
        plate('Greave_'+label+'_Steel_Layer_%02d'%i,outline,(xc,-.134,z),'Lower_Body','calf_'+label.lower())
    # Calf binding straps and boot buckles stay distinct from armor.
    for z,xc,r in [(.411,sign*.151,.063),(.286,sign*.163,.055),(.155,sign*.177,.046)]:
        tube('Boot_'+label+'_Leather_Strap',[(xc,-.008,z-.008),(xc,-.008,z+.008)],[(r,r),(r,r)],leather,'Lower_Body','calf_'+label.lower(),12)
        buckle('Boot_'+label+'_Small_Buckle',(xc+sign*r,-.048,z),.022,.020,'Lower_Body','calf_'+label.lower())
    footx=sign*.19
    outline=[(footx-.05,-.23,.033),(footx+.05,-.23,.033),(footx+.055,-.145,.065),(footx+.034,-.067,.102),(footx-.037,-.067,.102),(footx-.057,-.145,.065)]
    plate('Boot_'+label+'_Steel_Toe_Cap',outline,(footx,-.155,.102),'Lower_Body','foot_'+label.lower())
    sole=[(footx-.052,-.235,.012),(footx+.052,-.235,.012),(footx+.063,-.18,.012),(footx+.048,.055,.012),(footx-.048,.055,.012),(footx-.063,-.18,.012)]
    path('Boot_'+label+'_Heavy_Welted_Sole',sole+[sole[0]],.009,maskmat,'Lower_Body','foot_'+label.lower(),5)
# Folded scarf around the neck and upper chest.
ns=32;rows=[(1.485,.134,.124),(1.515,.135,.140),(1.540,.112,.137),(1.560,.084,.120)]
vs=[];uv=[];fs=[]
for i,(z,rx,ry) in enumerate(rows):
    for j in range(ns):
        a=tau*j/ns;zz=z+.009*cos(a*3+i*.8)+(.014 if i==0 else 0)*cos(a)
        vs.append((rx*sin(a),-.02-ry*cos(a),zz));uv.append((j/ns,i/(len(rows)-1)))
for i in range(len(rows)-1):
    for j in range(ns):fs.append((i*ns+j,i*ns+(j+1)%ns,(i+1)*ns+(j+1)%ns,(i+1)*ns+j))
scarf=mesh('Scarf_Deep_Red_Wrapped_Neck',vs,fs,red,'Red_Fabric','neck_01',True,uv)
for i in range(3):
    pts=[]
    for j in range(17):
        a=-1.35+j/16*2.7;pts.append((.137*sin(a),-.02-.143*cos(a),1.50+i*.014+.005*cos(a*3+i)))
    path('Scarf_Painted_Fold_Ridge_%02d'%i,pts,.0025,red,'Red_Fabric','neck_01',5)
# Tattered hanging cloth is genuine editable topology, including open tears.
def cloth_panel(name,rows,widths,centers,back=False):
    cols=13;vs=[];fs=[];uv=[]
    for i,z in enumerate(rows):
        for j in range(cols):
            u=j/(cols-1);x=centers[i][0]+(u-.5)*widths[i]
            y=centers[i][1]+.009*sin(u*pi*6+i*.20)
            zz=z
            if i==len(rows)-1:zz+=.040*sin(j*2.8)**2+.018*cos(j*2.1)
            vs.append((x,y,zz));uv.append((u,i/(len(rows)-1)))
    for i in range(len(rows)-1):
        for j in range(cols-1):
            if (i==len(rows)-2 and j in [1,8]) or (i==len(rows)-3 and j==11):continue
            fs.append((i*cols+j,i*cols+j+1,(i+1)*cols+j+1,(i+1)*cols+j))
    obj=mesh(name,vs,fs,red,'Red_Fabric','spine_03' if back else 'pelvis',True,uv)
    solid=obj.modifiers.new('Editable Cloth Thickness','SOLIDIFY');solid.thickness=.0015
    # Restrained gold hem stitches follow surviving panel edges.
    for j in [0,cols-1]:
        pts=[Vector(vs[i*cols+j])+Vector((0,.001 if back else -.001,0)) for i in range(len(rows)-1)]
        path(name+'_Faded_Gold_Hem',pts,.00065,gold,'Red_Fabric','spine_03' if back else 'pelvis',4)
    return obj
cape=cloth_panel('Back_Drapery_Torn_Red_Mantle',[1.49,1.36,1.18,.98,.78,.59,.43],[.24,.32,.37,.39,.40,.39,.36],[(0,.118),(0,.144),(0,.161),(0,.175),(0,.185),(0,.204),(0,.221)],True)
# Weight the mantle to existing spine/pelvis bones without adding or editing bones.
weight_spine(cape)
for sign,label in [(1,'L'),(-1,'R')]:
    cloth_panel('Waist_'+label+'_Long_Tattered_Red_Tabard',[.99,.88,.72,.55,.37,.20],[.115,.122,.126,.112,.095,.072],[(sign*.062,-.166),(sign*.067,-.174),(sign*.079,-.18),(sign*.090,-.184),(sign*.104,-.182),(sign*.117,-.17)])
    cloth_panel('Waist_'+label+'_Side_Red_Tails',[1.0,.88,.72,.55,.40],[.08,.094,.086,.07,.04],[(sign*.154,.003),(sign*.181,.034),(sign*.207,.06),(sign*.233,.073),(sign*.248,.087)])
    # Torn scarf ends stream behind the shoulders without moving the arms.
    cloth_panel('Scarf_'+label+'_Torn_Rear_End',[1.53,1.48,1.42,1.36],[.055,.063,.056,.025],[(sign*.12,.11),(sign*.21,.13),(sign*.27,.16),(sign*.30,.18)],True)
    # Bronze textile motifs and small diamond pendants echo the reference embroidery.
    pts=[(sign*x,-.19,z) for x,z in [(.040,.88),(.074,.81),(.055,.73),(.093,.65),(.073,.57)]]
    path('Tabard_'+label+'_Faded_Bronze_Rune',pts,.0013,gold,'Red_Fabric','pelvis',4)
    for x,z in [(.066,.82),(.085,.65)]:
        x*=sign
        plate('Tabard_'+label+'_Diamond_Emblem',[(x,-.193,z+.020),(x+.009,-.194,z),(x,-.193,z-.020),(x-.009,-.194,z)],(x,-.196,z),'Red_Fabric','pelvis',False,gold)
# Mask only the covered body surface; the original anatomical mesh remains intact and editable.
skin=body.vertex_groups.new(name='Outfit_Visible_Skin')
skin.add([v.index for v in body.data.vertices if v.co.z>1.535],1,'REPLACE')
mask=body.modifiers.new('Hide Body Beneath Editable Outfit','MASK');mask.vertex_group=skin.name
# Preserve all original matrices and poses; attachments only reference the existing rig.
assert rig_before=={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}
assert pose_before=={b.name:[list(row) for row in b.matrix_basis] for b in rig.pose.bones}
assert body_before==[tuple(v.co) for v in body.data.vertices]
versions=[int(p.stem.rsplit('_v',1)[-1]) for p in OUT.glob('assassin_concept_v[0-9][0-9][0-9].blend')]
version=max(versions,default=0)+1
dest=OUT/f'assassin_concept_v{version:03d}.blend'
scene['concept_outfit_version']=version
scene['concept_reference']='Hooded Assassin Character Design Sheet.png'
scene['outfit_notes']='Separate editable meshes, painted 512px materials, original skeleton and T-pose preserved.'
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1400;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.38
camera.location=(2.5,-6,2.5);target=Vector((0,0,.94));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
for lamp,power in zip([o for o in bpy.data.objects if o.type=='LIGHT'],[650,450,900]):lamp.data.energy=power
scene.render.filepath=str(OUT/f'assassin_concept_v{version:03d}_three_quarter.png')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
bpy.ops.render.render(write_still=True)
report={'file':str(dest),'version':version,'original_bones':len(rig.data.bones),'skeleton_unchanged':True,'pose_unchanged':True,'body_geometry_unchanged':True,'outfit_meshes':len(added),'outfit_source_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in added),'painted_maps':10,'map_resolution':'512x512','collections':list(collections.keys()),'all_outfit_meshes_bound':all(any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) for o in added)}
(OUT/f'assassin_concept_v{version:03d}_validation.json').write_text(json.dumps(report,indent=2))
result=report
