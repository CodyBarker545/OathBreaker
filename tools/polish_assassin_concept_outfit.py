import bpy,bmesh,ast,math,json,random
from pathlib import Path
from mathutils import Vector,Quaternion
from math import sin,cos,pi,tau
ROOT=Path(r'D:\SoftwareEng\Game');OUT=ROOT/'SourceAssets/characters/hooded_assassin/outfit'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v003.blend'))
scene=bpy.context.scene;body=bpy.data.objects['Assassin_Body'];rig=bpy.data.objects['Assassin_Skeleton']
collections={name:bpy.data.collections['Outfit_'+name] for name in ['Head','Torso','Shoulders_Arms','Lower_Body','Red_Fabric']}
added=[]
steel=bpy.data.materials['GC_Painted_Blackened_Steel'];gold=bpy.data.materials['GC_Tarnished_Bronze_Gold'];tunicmat=bpy.data.materials['GC_Black_Fitted_Tunic'];maskmat=bpy.data.materials['GC_Black_Lower_Face_Mask'];hoodmat=bpy.data.materials['GC_Charcoal_Hood']
tree=ast.parse((ROOT/'tools/build_assassin_concept_outfit.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<outfit helpers>','exec'),globals())
# Break the smooth cowl into cloth folds while keeping the original face opening.
hood=bpy.data.objects['Hood_Dark_Pointed_Cowl']
for i,v in enumerate(hood.data.vertices):
    p=v.co
    if p.z>1.78:p.z=1.78+(p.z-1.78)*.79
    angle=math.atan2(p.x,-(p.y+.04))
    if abs(angle)>.80:
        fold=.0035*sin(angle*6+int(i/25)*.65)
        p.x+=fold*sin(angle);p.y-=fold*cos(angle)
for obj in collections['Head'].objects:
    if obj.name.startswith('Hood_') and obj!=hood:
        for v in obj.data.vertices:
            if v.co.z>1.78:v.co.z=1.78+(v.co.z-1.78)*.79
# More substantial boot uppers: closed heel/toe shells and a distinct ankle cuff.
for sign,label in [(1,'L'),(-1,'R')]:
    xc=sign*.189
    outline=[(-.045,.054,.107),(.045,.054,.107),(.052,-.035,.106),(.057,-.145,.063),(.049,-.235,.046),(-.049,-.235,.046),(-.057,-.145,.063),(-.052,-.035,.106)]
    vs=[(xc+x,y,.017) for x,y,z in outline]+[(xc+x,y,z) for x,y,z in outline]
    fs=[tuple(reversed(range(8))),tuple(range(8,16))]+[(j,(j+1)%8,8+(j+1)%8,8+j) for j in range(8)]
    mesh('Boot_'+label+'_Angular_Closed_Shoe',vs,fs,tunicmat,'Lower_Body','foot_'+label.lower())
    tube('Boot_'+label+'_Ankle_Cuff',[(sign*.180,-.005,.105),(sign*.177,-.005,.145)],[(.052,.050),(.052,.049)],maskmat,'Lower_Body','calf_'+label.lower(),12)
    for obj in collections['Lower_Body'].objects:
        if obj.name.startswith('Boot_'+label+'_Steel_Toe_Cap'):
            for v in obj.data.vertices:v.co.z+=.016
    plate('Boot_'+label+'_Ankle_Armor',[(xc-.039,-.075,.176),(xc+.039,-.075,.176),(xc+.048,-.096,.126),(xc,-.111,.101),(xc-.048,-.096,.126)],(xc,-.12,.14),'Lower_Body','foot_'+label.lower())
# Irregular diagonal tears replace box-shaped cuts along the mantle's lower edge.
for obj in collections['Red_Fabric'].objects:
    if obj.name=='Back_Drapery_Torn_Red_Mantle':
        cols=13
        for i,v in enumerate(obj.data.vertices):
            row,col=divmod(i,cols)
            if row>=4:
                weight=(row-3)/3
                v.co.x+=.009*sin(col*2.7+row)*weight
                v.co.z+=.022*sin(col*3.1+row*.5)*weight
        obj.data.update()
lamps=[o for o in bpy.data.objects if o.type=='LIGHT']
if len(lamps)>=3:lamps[2].data.energy=650
report=json.loads((OUT/'assassin_concept_v003_validation.json').read_text())
outfit=[o for c in collections.values() for o in c.objects if o.type=='MESH']
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();counts={}
for obj in [o for o in scene.objects if o.type=='MESH' and not o.hide_render]:
    evaluated=obj.evaluated_get(dg);data=evaluated.to_mesh();counts[obj.name]=sum(len(p.vertices)-2 for p in data.polygons);evaluated.to_mesh_clear()
zero={};unweighted={}
for obj in outfit:
    bm=bmesh.new();bm.from_mesh(obj.data);n=sum(f.calc_area()<1e-12 for f in bm.faces);bm.free()
    if n:zero[obj.name]=n
    ids={g.index for g in obj.vertex_groups if g.name in rig.data.bones}
    n=sum(not any(g.group in ids and g.weight>0 for g in v.groups) for v in obj.data.vertices)
    if n:unweighted[obj.name]=n
assert not zero and not unweighted
baseline=json.loads((ROOT/'artifacts/assassin_outfit_base.json').read_text())['bones']
assert all((b.head_local-Vector(baseline[b.name]['head'])).length<1e-7 and (b.tail_local-Vector(baseline[b.name]['tail'])).length<1e-7 for b in rig.data.bones)
assert all(max(abs(b.matrix_basis[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-6 for b in rig.pose.bones)
report.update(file=str(OUT/'assassin_concept_v004.blend'),version=4,separate_outfit_meshes=len(outfit),visible_evaluated_triangles=sum(counts.values()),outfit_source_triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in outfit),visible_triangle_counts=counts,degenerate_outfit_faces=zero,unweighted_outfit_vertices=unweighted,collections={name:len(c.objects) for name,c in collections.items()})
(OUT/'assassin_concept_v004_validation.json').write_text(json.dumps(report,indent=2))
scene['concept_outfit_version']=4
camera=scene.camera;scene.cycles.samples=32;scene.render.resolution_x=1400;scene.render.resolution_y=1300
def view(name,location,target=(0,0,.94),scale=2.32):
    camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(OUT/f'assassin_concept_v004_{name}.png');bpy.ops.render.render(write_still=True)
view('three_quarter',(2.5,-6,2.4))
view('front',(0,-6,1.0))
view('rear',(2.1,6,2.15))
scene.render.resolution_x=1100;scene.render.resolution_y=1100
view('head',(.38,-1,1.78),(0,-.06,1.70),.46)
camera.location=(2.5,-6,2.4);camera.rotation_euler=(Vector((0,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=2.32
scene.render.resolution_x=1400;scene.render.resolution_y=1300
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=report['file'])
result={k:v for k,v in report.items() if k!='visible_triangle_counts'}
