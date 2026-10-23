import bpy,bmesh,json,collections,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin');out=root/'inspection_original_models'
results=[]
for index,pattern in [(3,'*Bronze*'),(4,'*scar*'),(6,'*Mant*')]:
    path=next((root/'orignal_models').glob(pattern+'.glb'))
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=obj.data
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
    unseen=set(bm.verts);islands=[];vert_island={}
    while unseen:
        todo=[unseen.pop()];vs=[]
        while todo:
            v=todo.pop();vs.append(v)
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:unseen.remove(w);todo.append(w)
        islands.append(vs)
    islands.sort(key=len,reverse=True)
    for k,vs in enumerate(islands):
        for v in vs:vert_island[v.index]=k
    faces=[tuple(p.vertices) for p in mesh.polygons];vertices=[v.co.copy() for v in mesh.vertices]
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    pairs=collections.Counter()
    for a,b in tree.overlap(tree):
        if a<b and not set(faces[a]).intersection(faces[b]):
            pairs[str(tuple(sorted((vert_island[faces[a][0]],vert_island[faces[b][0]]))))]+=1
    item={'file':path.name,'island_vertices':[len(v) for v in islands],'intersection_pairs_by_island_indices':dict(pairs)}
    if len(islands)==2:
        major_faces=[faces[p.index] for p in bm.faces if vert_island[p.verts[0].index]==0]
        main=BVHTree.FromPolygons(vertices,major_faces,all_triangles=True)
        point=islands[1][0].co.copy();direction=Vector((1,.313,.173)).normalized();hits=[];origin=point.copy()
        for _ in range(100):
            hit,normal,idx,distance=main.ray_cast(origin,direction,20)
            if hit is None:break
            hits.append(list(hit));origin=hit+direction*.00001
        item['secondary_shell_test_point_inside_main_volume']=len(hits)%2==1
        item['ray_hits_to_outside']=len(hits)
        item['secondary_point']=list(point)
    results.append(item);bm.free()
bpy.ops.wm.open_mainfile(filepath=str(root/'base/assassin_base.blend'))
rig=bpy.data.objects['Assassin_Skeleton'];body=bpy.data.objects['Assassin_Body'];dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh()
def group_bounds(names):
    groups={body.vertex_groups[n].index for n in names if n in body.vertex_groups}
    coords=[body.matrix_world@v.co for v in mesh.vertices if sum(g.weight for g in v.groups if g.group in groups)>.5]
    if not coords:return None
    lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
    return {'vertices':len(coords),'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)],'definition':'evaluated visible body vertices with combined named-bone weights >0.5; approximate region envelope'}
base={'bones':{b.name:{'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local),'length':(rig.matrix_world@b.tail_local-rig.matrix_world@b.head_local).length} for b in rig.data.bones if b.name in ['pelvis','spine_01','spine_02','spine_03','neck_01','head','upperarm_l','lowerarm_l','hand_l','thigh_l','calf_l','foot_l','ball_l']},'weighted_region_bounds':{name:group_bounds(groups) for name,groups in {'head':['head'],'torso':['pelvis','spine_01','spine_02','spine_03'],'forearm_l':['lowerarm_l'],'foot_l':['foot_l','ball_l'],'lowerleg_l':['calf_l']}.items()}}
ev.to_mesh_clear()
(out/'supplemental_geometry.json').write_text(json.dumps({'islands':results,'mpfb_landmarks':base},indent=2))
print(json.dumps({'islands':results,'mpfb_landmarks':base},indent=2),flush=True)
