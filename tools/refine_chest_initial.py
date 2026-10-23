import bpy, bmesh, math, json, array, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

folder = Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\modular\chest_plate')
bpy.ops.wm.open_mainfile(filepath=str(folder / 'assassin_chest_plate_v002.blend'))
scene = bpy.context.scene
src = bpy.data.objects.get('mesh_node')
assert src is not None and len(src.data.polygons) == 697806

def fingerprint(mesh):
    coords = array.array('f', [0.0]) * (len(mesh.vertices) * 3)
    indices = array.array('i', [0]) * len(mesh.loops)
    mesh.vertices.foreach_get('co', coords)
    mesh.loops.foreach_get('vertex_index', indices)
    return hashlib.sha256(coords.tobytes() + indices.tobytes()).hexdigest()

original_hash = fingerprint(src.data)
assert original_hash == '12d10e9bb5b6e751f0d0ae4beb2eda6ba2e968885c5b092e5e98b62250d9ff34'
high = bpy.data.collections.new('ChestArmor_HighPoly_Source')
game = bpy.data.collections.new('ChestArmor_GameReady')
scene.collection.children.link(high)
scene.collection.children.link(game)
for collection in list(src.users_collection):
    collection.objects.unlink(src)
high.objects.link(src)
src.name = 'ChestArmor_HighPoly_Original'
work = src.copy()
work.data = src.data.copy()
game.objects.link(work)
work.name = 'ChestArmor_Initial_Optimized'

bm = bmesh.new()
bm.from_mesh(work.data)
bm.verts.ensure_lookup_table()
buckets = {}
for vertex in bm.verts:
    angle = max((edge.calc_face_angle(0.0) for edge in vertex.link_edges), default=0.0)
    protected = round((0.15 + 0.85 * min(1.0, angle / math.radians(12))) * 20) / 20
    allowance = round((1.05 - protected) * 20) / 20
    buckets.setdefault(allowance, []).append(vertex.index)
bm.free()
group = work.vertex_groups.new(name='Reduction_Allowance_Lower_At_Creases')
for weight, indices in buckets.items():
    group.add(indices, weight, 'REPLACE')
modifier = work.modifiers.new('Curvature_Protected_60k_Review', 'DECIMATE')
modifier.ratio = 60000 / 697806
modifier.use_collapse_triangulate = True
modifier.vertex_group = group.name
modifier.vertex_group_factor = 0.00001
for polygon in work.data.polygons:
    polygon.use_smooth = True
depsgraph = bpy.context.evaluated_depsgraph_get()
low = bpy.data.meshes.new_from_object(work.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
work.modifiers.clear()
work.data = low
low.name = 'ChestArmor_60k_Initial_Mesh'
assert len(low.polygons) == 60000

bm = bmesh.new()
bm.from_mesh(low)
unseen = set(bm.verts)
components = []
while unseen:
    stack = [unseen.pop()]
    count = 0
    while stack:
        vertex = stack.pop()
        count += 1
        for edge in vertex.link_edges:
            other = edge.other_vert(vertex)
            if other in unseen:
                unseen.remove(other)
                stack.append(other)
    components.append(count)
faces = [tuple(p.vertices) for p in low.polygons]
tree = BVHTree.FromPolygons([v.co.copy() for v in low.vertices], faces, all_triangles=True)
intersections = sum(a < b and not set(faces[a]).intersection(faces[b]) for a,b in tree.overlap(tree))
errors = sorted(tree.find_nearest(v.co)[3] for v in list(src.data.vertices)[::23])
assert fingerprint(src.data) == original_hash
report = {
    'source_vertices': len(src.data.vertices), 'source_triangles': len(src.data.polygons),
    'source_sha256': original_hash, 'source_unchanged': True,
    'working_vertices': len(low.vertices), 'working_triangles': len(low.polygons),
    'components': components, 'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
    'inconsistent_winding_edges': sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
    'degenerate_faces': sum(f.calc_area() < 1e-12 for f in bm.faces),
    'nonadjacent_self_intersection_pairs': intersections,
    'uv_layers': list(low.uv_layers.keys()), 'material_slots': len(low.materials),
    'sampled_surface_error_local_units': {'median': errors[len(errors)//2], 'p95': errors[int(.95*len(errors))], 'p99': errors[int(.99*len(errors))], 'max': errors[-1]},
    'method': 'Curvature-weighted quadric collapse; 60k/30k/15k trials inspected through MCP; 15k rejected visually; 60k retained with gentler feature weighting.',
    'status': 'Initial review only. Interior repair, component retopology, UVs, materials, baking and rigging deferred.'
}
bm.free()
(folder / 'validation_v002.json').write_text(json.dumps(report, indent=2))
src.hide_set(True)
src.hide_render = True
work.hide_set(False)
work.hide_render = False
work['stage'] = 'Initial optimization only; approval pending'
work['interior_repaired'] = False
for obj in bpy.context.selected_objects:
    obj.select_set(False)
work.select_set(True)
bpy.context.view_layer.objects.active = work
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(folder / 'assassin_chest_plate_v002.blend'), compress=True)
print('INITIAL_REVIEW_SAVED', json.dumps(report), flush=True)

# Temporary inspection camera and Workbench settings are not saved into the asset.
try:
    scene.render.engine = 'BLENDER_WORKBENCH'
except TypeError as error:
    raise RuntimeError(str(error))
scene.render.resolution_x = 640
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
formats = [x.identifier for x in scene.render.image_settings.bl_rna.properties['file_format'].enum_items]
scene.render.image_settings.file_format = next(x for x in formats if x == 'PNG')
scene.display.shading.light = 'STUDIO'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = False
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.62, 0.64, 0.67)
scene.display.shading.background_type = 'WORLD'
scene.world.color = (0.055, 0.055, 0.055)
camera_data = bpy.data.cameras.new('Inspection_Camera_Temporary')
camera = bpy.data.objects.new('Inspection_Camera_Temporary', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 2.35
views = {'front': (0,-5,0), 'back': (0,5,0), 'side': (5,0,0), 'three_quarter': (3,-5,2.3)}
for label, obj in [('highpoly', src), ('optimized', work)]:
    src.hide_render = obj != src
    work.hide_render = obj != work
    src.hide_set(obj != src)
    work.hide_set(obj != work)
    for view, direction in views.items():
        camera.location = Vector(direction)
        camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(folder / f'v002_{label}_{view}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', scene.render.filepath, flush=True)
print('REVIEW_COMPLETE', flush=True)
