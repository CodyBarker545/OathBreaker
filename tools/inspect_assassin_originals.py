import bpy, bmesh, json, math, hashlib, collections, traceback
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

root = Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin')
originals = root / 'orignal_models'
out = root / 'inspection_original_models'
out.mkdir(exist_ok=True)
files = sorted(p for p in originals.rglob('*') if p.is_file() and p.suffix.lower() in {'.glb','.gltf','.fbx','.obj'})
manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in originals.rglob('*') if p.is_file()}
results = []

def bounds(objects):
    points = [o.matrix_world @ Vector(c) for o in objects if o.type == 'MESH' for c in o.bound_box]
    if not points: return None
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return {'min': lo, 'max': hi, 'dimensions': [hi[i]-lo[i] for i in range(3)]}

def inspect_mesh(obj):
    m = obj.data
    bm = bmesh.new(); bm.from_mesh(m)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    unseen = set(bm.verts); islands = []
    while unseen:
        stack = [unseen.pop()]; vs = []
        while stack:
            v = stack.pop(); vs.append(v)
            for e in v.link_edges:
                other = e.other_vert(v)
                if other in unseen: unseen.remove(other); stack.append(other)
        fs = {f for v in vs for f in v.link_faces}
        es = {e for v in vs for e in v.link_edges}
        closed = bool(fs) and all(e.is_manifold for e in es)
        volume = sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co))/6 for f in fs if len(f.verts)==3) if closed else None
        islands.append({'vertices':len(vs), 'faces':len(fs), 'bounds':[[min(v.co[i] for v in vs) for i in range(3)],[max(v.co[i] for v in vs) for i in range(3)]], 'closed':closed, 'signed_volume':volume})
    coord_counts = collections.Counter(tuple(v.co) for v in m.vertices)
    face_counts = collections.Counter(tuple(sorted(p.vertices)) for p in m.polygons)
    polygons = [tuple(p.vertices) for p in m.polygons]
    tree = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], polygons)
    overlaps = [(a,b) for a,b in tree.overlap(tree) if a<b and not set(polygons[a]).intersection(polygons[b])]
    result = {'name':obj.name,'vertices':len(m.vertices),'triangles':sum(len(p.vertices)-2 for p in m.polygons),'faces':len(m.polygons), 'tri_faces':sum(len(p.vertices)==3 for p in m.polygons),'quads':sum(len(p.vertices)==4 for p in m.polygons),'ngons':sum(len(p.vertices)>4 for p in m.polygons),
      'island_count':len(islands),'islands':sorted(islands,key=lambda x:-x['vertices']),
      'boundary_edges':sum(e.is_boundary for e in bm.edges),'overconnected_edges':sum(len(e.link_faces)>2 for e in bm.edges),'wire_edges':sum(e.is_wire for e in bm.edges),'nonmanifold_vertices':sum(not v.is_manifold for v in bm.verts),'loose_vertices':sum(not v.link_edges for v in bm.verts),'inconsistent_winding_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'exact_duplicate_vertices':sum(n-1 for n in coord_counts.values()),'duplicate_index_faces':sum(n-1 for n in face_counts.values()),'self_intersection_pairs':len(overlaps),
      'intersection_sample_centres':[[list(m.polygons[a].center),list(m.polygons[b].center)] for a,b in overlaps[:8]],
      'uv_layers':[u.name for u in m.uv_layers],'materials':[mat.name if mat else None for mat in m.materials], 'material_face_counts':dict(collections.Counter(p.material_index for p in m.polygons)),
      'location':list(obj.location),'rotation_degrees':[math.degrees(x) for x in obj.rotation_euler],'scale':list(obj.scale),'matrix_world':[list(row) for row in obj.matrix_world], 'origin_world':list(obj.matrix_world.translation),'bounds':bounds([obj]),'vertex_groups':list(obj.vertex_groups.keys()),'modifiers':[(mod.name,mod.type) for mod in obj.modifiers]}
    bm.free()
    return result

def render_views(tag, objects, views):
    scene=bpy.context.scene
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=480;scene.render.resolution_y=560;scene.render.resolution_percentage=100
    allowed=[e.identifier for e in scene.render.image_settings.bl_rna.properties['file_format'].enum_items]
    scene.render.image_settings.file_format=next(e for e in allowed if e=='PNG')
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.69)
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=False
    scene.display.shading.background_type='WORLD'
    if scene.world is None: scene.world=bpy.data.worlds.new('InspectionWorld')
    scene.world.color=(.045,.045,.045)
    box=bounds(objects);center=Vector([(a+b)/2 for a,b in zip(box['min'],box['max'])]);size=max(box['dimensions'])
    data=bpy.data.cameras.new('InspectionCamera');camera=bpy.data.objects.new('InspectionCamera',data);scene.collection.objects.link(camera);scene.camera=camera
    data.type='ORTHO';data.ortho_scale=size*1.65;data.clip_start=max(size*.0001,.00001);data.clip_end=max(size*100,100)
    for label,direction in views.items():
        camera.location=center+Vector(direction).normalized()*size*4
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/f'{tag}_{label}.png')
        bpy.ops.render.render(write_still=True)

for index,path in enumerate(files,1):
    print('INSPECT_START',index,path.name,flush=True)
    entry={'path':str(path.relative_to(root)),'filename':path.name,'format':path.suffix.lower(),'bytes':path.stat().st_size,'sha256':manifest[str(path.relative_to(root))]}
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if path.suffix.lower() in {'.glb','.gltf'}:bpy.ops.import_scene.gltf(filepath=str(path))
        elif path.suffix.lower()=='.fbx':bpy.ops.import_scene.fbx(filepath=str(path))
        else:bpy.ops.wm.obj_import(filepath=str(path))
        objects=list(bpy.context.scene.objects)
        entry.update({'status':'inspected','object_count':len(objects),'object_types':dict(collections.Counter(o.type for o in objects)), 'bounds':bounds(objects),'armatures':[{'name':o.name,'bones':len(o.data.bones)} for o in objects if o.type=='ARMATURE'], 'meshes':[inspect_mesh(o) for o in objects if o.type=='MESH'], 'materials':[{'name':m.name,'images':[{'name':n.image.name,'size':list(n.image.size),'path':n.image.filepath} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]} for m in bpy.data.materials if m.use_nodes]})
        entry['vertices']=sum(m['vertices'] for m in entry['meshes']);entry['triangles']=sum(m['triangles'] for m in entry['meshes'])
        render_views(f'{index:02}',objects,{'front':(0,-1,0),'back':(0,1,0),'side':(1,0,0),'three_quarter':(3,-5,2),'top':(0,0,1),'bottom':(0,0,-1)})
    except Exception:
        entry['status']='inspection_failed';entry['error']=traceback.format_exc()
    results.append(entry)
    (out/'inventory_geometry.json').write_text(json.dumps(results,indent=2))
    print('INSPECT_DONE',path.name,entry.get('triangles'),entry['status'],flush=True)

bases=[]
for relative in ['base/assassin_base.blend','blendswap_assassin/assassin_refined.blend']:
    path=root/relative
    if not path.exists():continue
    try:
        bpy.ops.wm.open_mainfile(filepath=str(path))
        objects=list(bpy.context.scene.objects)
        base={'path':relative,'unit_scale':bpy.context.scene.unit_settings.scale_length,'bounds':bounds(objects),'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons) if o.type=='MESH' else None,'bounds':bounds([o]) if o.type=='MESH' else None,'custom_property_keys':list(o.keys()),'groups':len(o.vertex_groups) if o.type=='MESH' else None,'modifiers':[(m.name,m.type) for m in o.modifiers]} for o in objects], 'armatures':[{'name':o.name,'bones':len(o.data.bones),'bone_names':[b.name for b in o.data.bones],'custom_property_keys':list(o.keys())} for o in objects if o.type=='ARMATURE']}
        bases.append(base)
        render_views('base_'+path.stem,objects,{'front':(0,-1,0),'side':(1,0,0)})
    except Exception:bases.append({'path':relative,'error':traceback.format_exc()})
(out/'base_assessment.json').write_text(json.dumps(bases,indent=2))
after={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in originals.rglob('*') if p.is_file()}
(out/'original_file_integrity.json').write_text(json.dumps({'before':manifest,'after':after,'all_original_files_unchanged':manifest==after},indent=2))
assert manifest==after
print('ALL_INSPECTIONS_COMPLETE',len(results),flush=True)
