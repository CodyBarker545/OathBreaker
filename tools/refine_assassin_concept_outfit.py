import bpy,bmesh,ast,math,json,random
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi,tau
ROOT=Path(r'D:\SoftwareEng\Game');OUT=ROOT/'SourceAssets/characters/hooded_assassin/outfit'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v001.blend'))
body=bpy.data.objects['Assassin_Body'];rig=bpy.data.objects['Assassin_Skeleton'];scene=bpy.context.scene
collections={name:bpy.data.collections['Outfit_'+name] for name in ['Head','Torso','Shoulders_Arms','Lower_Body','Red_Fabric']}
added=[];rng=random.Random(60121)
materials={'steel':'Painted_Blackened_Steel','gold':'Tarnished_Bronze_Gold','leather':'Brown_Strap_Leather','tunicmat':'Black_Fitted_Tunic','red':'Deep_Red_Tattered_Linen','hoodmat':'Charcoal_Hood','maskmat':'Black_Lower_Face_Mask','blond':'Layered_Ash_Blond','blondlight':'Blond_Painted_Highlights','blondshade':'Blond_Painted_Shadow'}
for variable,name in materials.items():globals()[variable]=bpy.data.materials['GC_'+name]
tree=ast.parse((ROOT/'tools/build_assassin_concept_outfit.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<outfit authoring helpers>','exec'),globals())
def darken(material,tint):
    nodes=material.node_tree.nodes;links=material.node_tree.links;bs=nodes.get('Principled BSDF')
    old=bs.inputs['Base Color'].links[0].from_socket
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1)
    links.new(old,mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
darken(steel,(.33,.35,.40));steel.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.28
steel.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.66
darken(tunicmat,(.50,.48,.50));darken(hoodmat,(.57,.53,.57));darken(red,(.63,.48,.53));darken(leather,(.68,.57,.48))
darken(gold,(.8,.72,.57))
# Replace the anatomical mask shell with a clean faceted cloth wrap.
for obj in list(collections['Head'].objects):
    if obj.name.startswith(('Mask_','Hair_')):bpy.data.objects.remove(obj,do_unlink=True)
ns=21;vs=[];fs=[];uv=[]
rows=[(1.552,.069,.101),(1.582,.078,.123),(1.609,.086,.132),(1.634,.088,.130),(1.649,.083,.128)]
for i,(z,rx,ry) in enumerate(rows):
    for j in range(ns):
        a=-1.25+2.5*j/(ns-1)
        zz=z+(.013*(1-abs(a)/1.25) if i==len(rows)-1 else 0)
        vs.append((rx*sin(a),-.07-ry*cos(a)-.0015*sin(a*5+i),zz));uv.append((j/(ns-1),i/(len(rows)-1)))
for i in range(len(rows)-1):
    for j in range(ns-1):fs.append((i*ns+j,i*ns+j+1,(i+1)*ns+j+1,(i+1)*ns+j))
mask=mesh('Mask_Black_Folded_Cloth_Wrap',vs,fs,maskmat,'Head','head',True,uv)
solid=mask.modifiers.new('Editable Mask Thickness','SOLIDIFY');solid.thickness=.0015
path('Mask_Nose_To_Chin_Seam',[(0,-.199,1.66),(0,-.204,1.636),(0,-.205,1.607),(0,-.193,1.58),(0,-.173,1.553)],.00065,hoodmat,'Head','head',4)
# Close the crown and soften the lower hood flare into the scarf.
hood=bpy.data.objects['Hood_Dark_Pointed_Cowl']
vs=[v.co.copy() for v in hood.data.vertices];fs=[tuple(p.vertices) for p in hood.data.polygons]
last=len(vs)-25;vs.append((0,-.018,1.880));tip=len(vs)-1
for j in range(24):fs.append((last+j,last+j+1,tip))
data=bpy.data.meshes.new('Closed_Pointed_Hood');data.from_pydata(vs,[],fs);data.update()
hood.data=data;data.materials.append(hoodmat)
uv=data.uv_layers.new(name='Painted_UV')
for p in data.polygons:
    p.use_smooth=True
    for li in p.loop_indices:
        v=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(v.x*3+.5,v.z*3)
for vg in list(hood.vertex_groups):hood.vertex_groups.remove(vg)
hood.vertex_groups.new(name='head').add(list(range(len(vs))),1,'REPLACE')
# Broad layered wedge locks and deliberately offset tips replace the straight fringe.
for sign,label in [(1,'L'),(-1,'R')]:
    for i in range(5):
        rootx=.010+i*.013
        endx=[.014,.033,.058,.073,.085][i]
        endz=[1.674,1.658,1.689,1.673,1.70][i]
        control=[(sign*rootx*.5,-.108,1.814-i*.002),(sign*(rootx+.006),-.164,1.805-i*.002),(sign*(endx+.018),-.196,1.739),(sign*endx,-.202,endz)]
        lock('Hair_'+label+'_Long_Angled_Lock_%02d'%i,control,.017 if i<3 else .014,[blondlight,blond,blondshade,blond,blond][i])
    for i in range(6):
        x=.010+i*.013
        control=[(sign*x*.15,-.087,1.815),(sign*x,-.121,1.852-i*.002),(sign*(x+.026),-.170,1.826-i*.008),(sign*(x+.042),-.187,1.765-i*.009)]
        lock('Hair_'+label+'_Messy_Upper_Tier_%02d'%i,control,.014,[blond,blondlight,blond][i%3])
    for i in range(3):
        control=[(sign*.060,-.135,1.791-i*.016),(sign*.080,-.174,1.772-i*.016),(sign*.095,-.181,1.731-i*.017),(sign*(.097+i*.002),-.176,1.696-i*.019)]
        lock('Hair_'+label+'_Spiked_Sideburn_%02d'%i,control,.011,blondshade if i%2 else blond)
# Off-centre crown blades give the forward fringe the concept's swept silhouette.
lock('Hair_Crown_Swept_Central_Blade',[(-.012,-.085,1.816),(.013,-.115,1.864),(.042,-.158,1.835),(.054,-.186,1.789)],.019,blondlight)
lock('Hair_Central_Crossing_Fringe',[(.025,-.125,1.803),(.015,-.183,1.786),(-.018,-.205,1.738),(-.028,-.204,1.690)],.018,blond)
# Smaller swept pauldron thorns; add back shells around the shoulder silhouette.
for obj in collections['Shoulders_Arms'].objects:
    if 'Crown_Spike' in obj.name:
        sign=1 if '_L_' in obj.name else -1
        low=min(v.co.z for v in obj.data.vertices)
        for v in obj.data.vertices:
            amount=max(0,v.co.z-low)
            v.co.x+=sign*amount*.40
            v.co.z=low+amount*.67
for sign,label in [(1,'L'),(-1,'R')]:
    for i in range(3):
        source=bpy.data.objects[f'Pauldron_{label}_Layer_{i:02d}']
        vs=[Vector((v.co.x,-.026-v.co.y,v.co.z)) for v in source.data.vertices]
        fs=[tuple(reversed(p.vertices)) for p in source.data.polygons]
        mesh(f'Pauldron_{label}_Rear_Shell_{i:02d}',vs,fs,steel,'Shoulders_Arms','upperarm_'+label.lower())
# Break up the lower silhouette: taper the front cloth to ragged points above the ankles.
for obj in list(collections['Red_Fabric'].objects):
    if obj.name.startswith('Waist_') and 'Long_Tattered_Red_Tabard' in obj.name:bpy.data.objects.remove(obj,do_unlink=True)
for sign,label in [(1,'L'),(-1,'R')]:
    cloth_panel('Waist_'+label+'_Tapered_Tattered_Tabard',[.99,.86,.73,.60,.47,.33],[.115,.130,.114,.090,.060,.018],[(sign*.062,-.166),(sign*.067,-.178),(sign*.081,-.187),(sign*.100,-.192),(sign*.120,-.183),(sign*.145,-.17)])
    # Shorter torn overlay corners and an inset red lining give the layers depth.
    cloth_panel('Waist_'+label+'_Frayed_Overlay',[.985,.89,.77,.66],[.082,.098,.078,.040],[(sign*.105,-.181),(sign*.125,-.19),(sign*.143,-.199),(sign*.153,-.196)])
    # Small bronze scarf clasp and matching chest pendant.
    x=sign*.018
    plate('Scarf_'+label+'_Diamond_Clasp',[(x,-.171,1.535),(x+sign*.015,-.176,1.514),(x,-.179,1.493),(x-sign*.012,-.176,1.514)],(x,-.184,1.514),'Red_Fabric','neck_01',False,gold)
    # Keep the main harness flush to the plate surface, including the upper ends.
    o=bpy.data.objects['Harness_'+label+'_Diagonal_Leather_Strap']
    for v in o.data.vertices:
        if v.co.z>1.42:v.co.y+=.024
for obj in collections['Lower_Body'].objects:
    if obj.name.endswith('_Fitted_Leather_Upper'):
        obj.data.materials.clear();obj.data.materials.append(tunicmat)
    if 'Leather_Body' in obj.name and obj.name.startswith('Pouch'):
        bevel=obj.modifiers.new('Editable Pouch Edge Softening','BEVEL');bevel.width=.003;bevel.segments=1
# Retain source topology while lowering visible garment and head density with editable modifiers.
for obj in [o for c in collections.values() for o in c.objects]:
    if any(s in obj.name for s in ['Fitted_Long_Sleeves','Armored_Underlayer','Full_Finger_Leather','Fitted_Leather_Upper']):
        dec=obj.modifiers.new('GameCube Silhouette Reduction (Editable)','DECIMATE');dec.ratio=.63
dec=body.modifiers.new('GameCube Visible Face Reduction (Editable)','DECIMATE');dec.ratio=.65
for material in [bpy.data.materials.get('Assassin_Portrait_Skin')]:
    if material:
        for node in material.node_tree.nodes:
            if node.type=='BUMP':node.inputs['Strength'].default_value=0
bpy.context.view_layer.update()
dest=OUT/'assassin_concept_v002.blend';scene['concept_outfit_version']=2
camera=scene.camera;camera.data.ortho_scale=2.32
camera.location=(2.5,-6,2.4);camera.rotation_euler=(Vector((0,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.cycles.samples=24;scene.render.resolution_x=1400;scene.render.resolution_y=1300
scene.render.filepath=str(OUT/'assassin_concept_v002_three_quarter.png')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest))
bpy.ops.render.render(write_still=True)
result={'file':str(dest),'version':2,'new_meshes':len(added)}
