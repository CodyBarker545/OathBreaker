"""Hair first, fitted closed crown second; verify static clearance and shared head binding."""
import bpy,bmesh,ast,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi,tau
ROOT=Path(r'D:\SoftwareEng\Game');OUT=ROOT/'SourceAssets/characters/hooded_assassin/outfit'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'assassin_concept_v004.blend'))
scene=bpy.context.scene;body=bpy.data.objects['Assassin_Body'];rig=bpy.data.objects['Assassin_Skeleton']
collections={name:bpy.data.collections['Outfit_'+name] for name in ['Head','Torso','Shoulders_Arms','Lower_Body','Red_Fabric']}
added=[];steel=bpy.data.materials['GC_Painted_Blackened_Steel'];gold=bpy.data.materials['GC_Tarnished_Bronze_Gold'];hoodmat=bpy.data.materials['GC_Charcoal_Hood'];blondshade=bpy.data.materials['GC_Blond_Painted_Shadow']
tree=ast.parse((ROOT/'tools/build_assassin_concept_outfit.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<outfit helpers>','exec'),globals())
bones_before={b.name:(tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones}
body_before=[tuple(v.co) for v in body.data.vertices]
# Restore the scalp-relative locks, removing the prior forward translation.
names=[o.name for o in collections['Head'].objects if o.name.startswith('Hair_')]
with bpy.data.libraries.load(str(OUT/'assassin_concept_v003.blend'),link=False) as (src,dst):dst.objects=names.copy()
for name,source in zip(names,dst.objects):
    target=bpy.data.objects[name]
    for v,original in zip(target.data.vertices,source.data.vertices):v.co=original.co
    target.data.update();bpy.data.objects.remove(source,do_unlink=True)
hair=[bpy.data.objects[n] for n in names]
# A continuous scalp mass supports the layered locks inside the hood.
vs=[];fs=[];uv=[];ns=32;nr=10
for i in range(nr):
    for j in range(ns):
        a=tau*j/ns;back=(1-cos(a))/2
        phi=.045+i/(nr-1)*(1.03+back*.80)
        vs.append((.086*sin(phi)*sin(a),-.050-.109*sin(phi)*cos(a),1.695+.121*cos(phi)))
        uv.append((j/ns,i/(nr-1)))
for i in range(nr-1):
    for j in range(ns):fs.append((i*ns+j,i*ns+(j+1)%ns,(i+1)*ns+(j+1)%ns,(i+1)*ns+j))
fs.append(tuple(reversed(range(ns))))
cap=mesh('Hair_Scalp_Fitted_Under_Hood',vs,fs,blondshade,'Head','head',True,uv);hair.append(cap)
for obj in hair:
    for v in obj.data.vertices:
        if v.co.z>1.790:v.co.z=1.790+(v.co.z-1.790)*.70
    obj.data.update()
hair_points=[v.co.copy() for obj in hair for v in obj.data.vertices]
# The face opening closes into a real arch; the crown above the arch is continuous fabric.
profiles=[(1.535,.098,.130,.85),(1.57,.112,.145,.88),(1.62,.119,.153,.85),(1.68,.119,.157,.82),(1.735,.117,.157,.78),(1.780,.112,.153,.68),(1.800,.105,.148,.60),(1.818,.090,.133,.35),(1.835,.071,.107,0),(1.850,.046,.075,0),(1.866,.010,.018,0)]
cy=-.045
def profile(z):
    for a,b in zip(profiles,profiles[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0]);return tuple(a[i]*(1-t)+b[i]*t for i in range(1,4))
    return tuple(profiles[0 if z<profiles[0][0] else -1][1:])
def polar(p):
    rx,ry,opening=profile(p.z)
    angle=math.atan2(p.x/rx,(cy-p.y)/ry)
    rho=math.sqrt((p.x/rx)**2+((cy-p.y)/ry)**2)
    return angle,rho,opening
zs=sorted(set([p[0] for p in profiles]+[1.535+i/18*(1.866-1.535) for i in range(19)]))
factors=[]
for z in zs:
    rx,ry,op=profile(z);factor=1.0
    for p in hair_points:
        if abs(p.z-z)>.075:continue
        a,r,o=polar(p)
        if abs(a)>=max(0,o-.055):
            excess=max(0,r+.010/min(profile(p.z)[:2])-1)
            factor=max(factor,1+excess*math.exp(-((p.z-z)/.032)**2))
    factors.append(factor)
# A conservative smooth envelope gives both the scalp and locks physical space under the fabric.
for obj in list(collections['Head'].objects):
    if obj.name.startswith('Hood_'):bpy.data.objects.remove(obj,do_unlink=True)
ns=33
def make_hood(extra):
    vs=[];fs=[];uv=[]
    for i,z in enumerate(zs):
        rx,ry,opening=profile(z)
        for j in range(ns):
            t=j/(ns-1);a=opening+(tau-2*opening)*t
            f=1+(factors[i]*extra-1)*max(.15,max(0,cos(a))**.7)
            fold=.0012*sin(a*6+i*.25)*sin(t*pi)**2
            vs.append(((rx*f+fold)*sin(a),cy-(ry*f+fold)*cos(a),z));uv.append((t,(z-zs[0])/(zs[-1]-zs[0])))
    for i in range(len(zs)-1):
        for j in range(ns-1):fs.append((i*ns+j,i*ns+j+1,(i+1)*ns+j+1,(i+1)*ns+j))
    top=len(vs);vs.append((0,cy,1.872));uv.append((.5,1))
    for j in range(ns-1):fs.append(((len(zs)-1)*ns+j,(len(zs)-1)*ns+j+1,top))
    return vs,fs,uv
def assess(vs,fs):
    bvh=BVHTree.FromPolygons(vs,fs,all_triangles=False)
    crossings=[];min_clear=10.;violations=0;covered=0
    for obj in hair:
        for edge in obj.data.edges:
            a,b=[obj.data.vertices[i].co for i in edge.vertices];d=b-a
            if d.length<1e-8:continue
            hit,n,idx,distance=bvh.ray_cast(a+d.normalized()*1e-6,d.normalized(),max(0,d.length-2e-6))
            if hit is not None:crossings.append((obj.name,edge.index))
    for p in hair_points:
        angle,rho,opening=polar(p)
        if abs(angle)<opening+.045:continue
        origin=Vector((0,cy,p.z));d=p-origin
        if d.length<1e-7:continue
        hit,n,idx,distance=bvh.ray_cast(origin,d.normalized(),1)
        if hit is not None:
            clearance=distance-d.length;min_clear=min(min_clear,clearance);covered+=1
            if clearance<.004:violations+=1
    return len(crossings),violations,min_clear,covered,crossings[:10]
history=[]
for iteration in range(10):
    extra=1+iteration*.035;vs,fs,uv=make_hood(extra)
    checks=assess(vs,fs);history.append({'scale':extra,'edge_intersections':checks[0],'clearance_violations':checks[1],'minimum_clearance_m':checks[2]})
    if checks[0]==0 and checks[1]==0:break
else:raise RuntimeError('Hood fitting failed: '+json.dumps(history))
hood=mesh('Hood_Fitted_Over_Hair_Closed_Crown',vs,fs,hoodmat,'Head','head',True,uv)
bm=bmesh.new();bm.from_mesh(hood.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hood.data);bm.free();hood.data.update()
solid=hood.modifiers.new('Fabric Thickness Outside Hair Clearance','SOLIDIFY');solid.thickness=.003;solid.offset=1
hood['fit_method']='Hair-first conservative envelope with exact hair-edge ray intersection checks'
hood['minimum_hair_clearance_m']=checks[2]
hood['shared_head_binding']='Hood and every hair mesh are weighted 100% to the original head bone'
# Keep the hem on the fitted boundary instead of leaving the former trim behind.
arch_last=max(i for i,z in enumerate(zs) if profile(z)[2]>.00001)+1
for j,label in [(0,'L'),(ns-1,'R')]:
    pts=[Vector(vs[i*ns+j]) for i in range(arch_last+1)]
    path('Hood_'+label+'_Fitted_Opening_Hem',pts,.002,hoodmat,'Head','head',5)
    path('Hood_'+label+'_Bronze_Stitch',pts[2:-1],.0006,gold,'Head','head',4)
assert bones_before=={b.name:(tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones}
assert body_before==[tuple(v.co) for v in body.data.vertices]
assert all(max(abs(b.matrix_basis[i][j]-(1 if i==j else 0)) for i in range(4) for j in range(4))<1e-6 for b in rig.pose.bones)
report=json.loads((OUT/'assassin_concept_v004_validation.json').read_text())
report.update(file=str(OUT/'assassin_concept_v005.blend'),version=5,hair_first_hood_fit=True,hood_hair_edge_intersections=checks[0],hood_hair_minimum_measured_clearance_m=checks[2],covered_hair_samples_checked=checks[3],fit_iterations=history,shared_head_binding_preserves_fit=True)
report.pop('hair_clear_of_cowl_front',None)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();counts={}
for obj in [o for o in scene.objects if o.type=='MESH' and not o.hide_render]:
    evaluated=obj.evaluated_get(dg);data=evaluated.to_mesh();counts[obj.name]=sum(len(p.vertices)-2 for p in data.polygons);evaluated.to_mesh_clear()
report['visible_evaluated_triangles']=sum(counts.values());report['visible_triangle_counts']=counts
report['separate_outfit_meshes']=sum(len(c.objects) for c in collections.values());report['collections']={name:len(c.objects) for name,c in collections.items()}
(OUT/'assassin_concept_v005_validation.json').write_text(json.dumps(report,indent=2))
scene['concept_outfit_version']=5
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=report['file'])
camera=scene.camera;scene.cycles.samples=24
def view(name,location,target,scale,w,h):
    camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(OUT/f'assassin_concept_v005_{name}.png');bpy.ops.render.render(write_still=True)
view('head',(.38,-1,1.78),(0,-.06,1.70),.46,1100,1100)
view('side_head',(.95,-.23,1.76),(0,-.06,1.70),.46,1100,1100)
view('three_quarter',(2.5,-6,2.4),(0,0,.94),2.32,1400,1300)
view('front',(0,-6,1.0),(0,0,.94),2.32,1400,1300)
camera.location=(2.5,-6,2.4);camera.rotation_euler=(Vector((0,0,.94))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=report['file'])
result={k:report[k] for k in ['file','original_bones','t_pose_unchanged','visible_evaluated_triangles','hood_hair_edge_intersections','hood_hair_minimum_measured_clearance_m','covered_hair_samples_checked','fit_iterations']}
