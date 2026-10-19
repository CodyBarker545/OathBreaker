extends SceneTree
## Offline authoring tool. Saves a regular, editable Godot scene and Terrain3D data.
## Run: Godot --headless --path . --script tools/BuildStartingLevel.gd

const DIRECTORY = "res://Assets/Levels/OathstoneCrossing/"
var level: Node3D
var terrain: Terrain3D
var props: Node3D
var grass: StandardMaterial3D
var timber: StandardMaterial3D
var stone: StandardMaterial3D
var gold: StandardMaterial3D

func _initialize():
	call_deferred("build")

func add(node: Node, parent: Node) -> Node:
	parent.add_child(node)
	node.owner = level
	return node

func material(color: Color, roughness: float = 0.9) -> StandardMaterial3D:
	var mat = StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = roughness
	return mat

func cube(label: String, location: Vector3, size: Vector3, mat: Material, parent: Node) -> MeshInstance3D:
	var mesh = MeshInstance3D.new()
	mesh.name = label
	mesh.position = location
	mesh.mesh = BoxMesh.new()
	mesh.mesh.size = size
	mesh.material_override = mat
	return add(mesh, parent)

func river_x(z: float) -> float:
	return 16.0 + 1.25 * sin((z - 16.0) * 0.28)

func elevation(x: float, z: float) -> float:
	var center_distance = Vector2(x - 16.0, z - 16.0).length()
	var plateau = 0.58 * (1.0 - smoothstep(2.0, 4.6, center_distance))
	var hill_a = 1.35 * exp(-Vector2((x - 8.0) / 3.3, (z - 8.0) / 4.0).length_squared())
	var hill_b = 1.35 * exp(-Vector2((x - 24.0) / 3.3, (z - 24.0) / 4.0).length_squared())
	var height = 0.16 + plateau + hill_a + hill_b
	var channel = (1.0 - smoothstep(0.7, 1.9, abs(x - river_x(z))))
	channel *= smoothstep(2.4, 3.6, center_distance)
	return lerpf(height, -0.62, channel)

func terrain_texture(label: String, albedo: String, normal: String, tint: Color) -> Terrain3DTextureAsset:
	var asset = Terrain3DTextureAsset.new()
	asset.name = label
	asset.albedo_texture = load(DIRECTORY + "Textures/" + albedo)
	asset.normal_texture = load(DIRECTORY + "Textures/" + normal)
	asset.albedo_color = tint
	asset.uv_scale = 0.45
	return asset

func mesh_bounds(node: Node3D, parent_transform: Transform3D = Transform3D.IDENTITY) -> AABB:
	var transform = parent_transform * node.transform
	var bounds = AABB()
	if node is MeshInstance3D:
		bounds = transform * node.get_aabb()
	for child in node.get_children():
		if child is Node3D:
			var child_bounds = mesh_bounds(child, transform)
			if child_bounds.size.length() > 0.0:
				bounds = child_bounds if bounds.size.length() == 0.0 else bounds.merge(child_bounds)
	return bounds

func dress_meshes(node: Node, file: String):
	# These older GLB exports kept geometry but lost their Blender shader colors.
	# Restore readable bark/leaf/stone materials per surface, keeping the source intact.
	if node is MeshInstance3D:
		for index in range(node.mesh.get_surface_count()):
			var original = node.mesh.surface_get_material(index)
			var label = original.resource_name.to_lower() if original else ""
			var mat: StandardMaterial3D
			if file.begins_with("stones_"):
				mat = material(Color(0.43, 0.46, 0.41))
				mat.albedo_texture = load(DIRECTORY + "Textures/rock023_alb_ht.png")
			elif "bark" in label or "wood" in label:
				mat = material(Color(0.19, 0.105, 0.045))
			else:
				mat = material(Color(0.12, 0.24, 0.075) if "pine" in file else Color(0.24, 0.33, 0.10))
				mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			node.set_surface_override_material(index, mat)
	for child in node.get_children():
		dress_meshes(child, file)

func copy_glb_meshes(source: Node3D, target: Node3D, parent_transform: Transform3D = Transform3D.IDENTITY):
	# Author mesh nodes with shared imported geometry. Surface overrides then persist
	# in the saved level without depending on editable-child state of GLB instances.
	var transform = parent_transform * source.transform
	if source is MeshInstance3D:
		var mesh = MeshInstance3D.new()
		mesh.name = source.name
		mesh.transform = transform
		mesh.mesh = source.mesh
		add(mesh, target)
	for child in source.get_children():
		if child is Node3D:
			copy_glb_meshes(child, target, transform)

func prop(file: String, label: String, location: Vector3, height: float, angle: float = 0.0, blocking: bool = true) -> Node3D:
	var wrapper = Node3D.new()
	wrapper.name = label
	wrapper.position = location
	wrapper.rotation.y = angle
	add(wrapper, props)
	wrapper.set_meta("blocks_movement", blocking)
	wrapper.set_meta("blocking_radius", 0.58)
	var pivot = Node3D.new()
	pivot.name = "ModelScale"
	add(pivot, wrapper)
	var imported = load("res://Assets/Levels/" + file + ".glb").instantiate()
	var model = Node3D.new()
	model.name = file
	add(model, pivot)
	copy_glb_meshes(imported, model)
	imported.free()
	dress_meshes(model, file)
	var bounds = mesh_bounds(model)
	var factor = height / maxf(bounds.size.y, 0.01)
	pivot.scale = Vector3.ONE * factor
	pivot.position = -Vector3(bounds.get_center().x, bounds.position.y, bounds.get_center().z) * factor
	return wrapper

func cell(x: int, z: int) -> Vector3:
	var pos = Vector3(16.0 + (x - 7.5) * 1.25, 0.0, 16.0 + (z - 7.5) * 1.25)
	pos.y = terrain.data.get_height(pos)
	return pos

func bridge(z: float, label: String):
	var origin = Vector3(river_x(z), 0.3, z)
	var node = Node3D.new()
	node.name = label
	node.position = origin
	node.set_meta("bridge_size", Vector2(5.0, 1.25))
	add(node, level.get_node("Bridges"))
	for i in range(20):
		cube("Plank%02d" % i, Vector3((i - 9.5) * 0.25, -0.06, 0.0), Vector3(0.238, 0.12, 1.25), timber, node)
	for side in [-1.0, 1.0]:
		cube("Support", Vector3(0, -0.17, side * 0.43), Vector3(5.0, 0.18, 0.13), timber, node)
		for end in [-2.25, 2.25]:
			cube("Post", Vector3(end, 0.2, side * 0.64), Vector3(0.12, 0.7, 0.12), timber, node)
		cube("Rail", Vector3(0, 0.44, side * 0.64), Vector3(4.6, 0.085, 0.085), timber, node)

func water_segment(start: float, end: float, label: String):
	var mesh = SurfaceTool.new()
	mesh.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(64):
		var z1 = lerpf(start, end, i / 64.0)
		var z2 = lerpf(start, end, (i + 1) / 64.0)
		var points = [Vector3(river_x(z1) - 1.13, -0.13, z1), Vector3(river_x(z1) + 1.13, -0.13, z1), Vector3(river_x(z2) - 1.13, -0.13, z2), Vector3(river_x(z2) + 1.13, -0.13, z2)]
		for index in [0, 2, 1, 1, 2, 3]:
			mesh.set_uv(Vector2(0 if index % 2 == 0 else 1, points[index].z / 28.0))
			mesh.set_normal(Vector3.UP)
			mesh.add_vertex(points[index])
	var surface = MeshInstance3D.new()
	surface.name = label
	surface.mesh = mesh.commit()
	var mat = ShaderMaterial.new()
	mat.shader = load("res://Assets/Shaders/Creek.gdshader")
	surface.material_override = mat
	add(surface, level.get_node("River"))

func build():
	level = Node3D.new()
	level.name = "OathstoneCrossing"
	root.add_child(level)
	for label in ["LevelProps", "Bridges", "River", "SpawnPoints", "Objective"]:
		var group = Node3D.new()
		group.name = label
		add(group, level)
	props = level.get_node("LevelProps")
	timber = material(Color(0.26, 0.15, 0.075))
	stone = material(Color(0.32, 0.35, 0.32))
	gold = material(Color(0.75, 0.51, 0.16), 0.4)
	gold.emission_enabled = true
	gold.emission = Color(0.38, 0.21, 0.04)
	terrain = Terrain3D.new()
	terrain.name = "Terrain3D"
	terrain.region_size = 64
	terrain.vertex_spacing = 0.5
	add(terrain, level)
	terrain.material.world_background = Terrain3DMaterial.NONE
	terrain.material.auto_shader = false
	terrain.material.set_shader_param("blend_sharpness", 0.7)
	terrain.assets = Terrain3DAssets.new()
	terrain.assets.set_texture(0, terrain_texture("Meadow", "ground037_alb_ht.png", "ground037_nrm_rgh.png", Color(0.17, 0.25, 0.105)))
	terrain.assets.set_texture(1, terrain_texture("Old stone", "rock023_alb_ht.png", "rock023_nrm_rgh.png", Color(0.38, 0.40, 0.33)))
	terrain.assets.set_texture(2, terrain_texture("Worn earth", "ground037_alb_ht.png", "ground037_nrm_rgh.png", Color(0.40, 0.29, 0.17)))
	var heights = Image.create_empty(64, 64, false, Image.FORMAT_RF)
	var controls = Image.create_empty(64, 64, false, Image.FORMAT_RF)
	var colors = Image.create_empty(64, 64, false, Image.FORMAT_RGBA8)
	for x in range(64):
		for z in range(64):
			var wx = x * 0.5
			var wz = z * 0.5
			var distance = Vector2(wx - 16, wz - 16).length()
			heights.set_pixel(x, z, Color(elevation(wx, wz), 0, 0, 1))
			var path_distance = minf(abs(wz - 16.0), minf(abs(wz - 9.125), abs(wz - 22.875)))
			var texture_id = 0 if path_distance > 0.8 else 2
			if distance < 2.25:
				texture_id = 1
			var packed = PackedInt32Array([(texture_id << 27) | (texture_id << 22)]).to_byte_array().decode_float(0)
			controls.set_pixel(x, z, Color(packed, 0, 0, 1))
			var variation = 0.93 + 0.06 * sin(wx * 1.3) * cos(wz * 0.7)
			colors.set_pixel(x, z, Color(variation, variation, variation, 0.85))
	terrain.data.import_images([heights, controls, colors], Vector3.ZERO, 0, 1)
	terrain.data.save_directory(DIRECTORY + "TerrainData")
	terrain.data_directory = DIRECTORY + "TerrainData"
	ResourceSaver.save(terrain.assets, DIRECTORY + "TerrainAssets.tres")
	ResourceSaver.save(terrain.material, DIRECTORY + "TerrainMaterial.tres")
	terrain.assets.take_over_path(DIRECTORY + "TerrainAssets.tres")
	terrain.material.take_over_path(DIRECTORY + "TerrainMaterial.tres")
	water_segment(0, 13.65, "NorthCreek")
	water_segment(18.35, 31.5, "SouthCreek")
	bridge(9.125, "NorthBridge")
	bridge(22.875, "SouthBridge")
	# Paired placements preserve equal routes from both starting sides.
	var trees = [Vector2i(2, 2), Vector2i(4, 2), Vector2i(2, 4), Vector2i(5, 3), Vector2i(1, 11), Vector2i(3, 12), Vector2i(5, 13)]
	for side in range(2):
		for i in range(trees.size()):
			var p = trees[i] if side == 0 else Vector2i(15, 15) - trees[i]
			var file = ["foliage_006_tree_pine_joined", "foliage_007_tree_oak_joined", "foliage_008_tree_small_joined"][i % 3]
			prop(file, "Tree_%d_%d" % [side, i], cell(p.x, p.y), 2.2 + 0.25 * (i % 3), i * 1.7)
		for p in [Vector2i(4, 5), Vector2i(4, 9), Vector2i(6, 12)]:
			var q = p if side == 0 else Vector2i(15, 15) - p
			prop("stones_002_stone_03", "Boulder_%d_%d_%d" % [side, q.x, q.y], cell(q.x, q.y), 0.8, q.x)
	# Border groves frame the battlefield without hiding the central approach.
	for i in range(7):
		for side in range(2):
			var pos = Vector3(3.8 + i * 4, 0, 3.4 if side == 0 else 28.6)
			if abs(pos.x - river_x(pos.z)) < 2.0:
				continue
			pos.y = terrain.data.get_height(pos)
			prop("foliage_006_tree_pine_joined", "BorderPine_%d_%d" % [side, i], pos, 2.5 + 0.2 * (i % 3), i, false)
	for i in range(18):
		var z = 2.4 + i * 1.6
		if abs(z - 16) < 4 or abs(z - 9.125) < 1 or abs(z - 22.875) < 1:
			continue
		for side in [-1, 1]:
			var pos = Vector3(river_x(z) + side * 1.7, 0, z)
			pos.y = terrain.data.get_height(pos)
			prop("stones_000_stone_01", "RiverStone_%d_%d" % [i, side], pos, 0.28, i, false)
	# Low ferns decorate clearings; they do not block tactical movement.
	for p in [Vector2i(2, 3), Vector2i(4, 12), Vector2i(13, 12), Vector2i(11, 3)]:
		prop("foliage_010_bush_fern_joined", "Fern_%d_%d" % [p.x, p.y], cell(p.x, p.y), 0.45, p.y, false)
	var objective = level.get_node("Objective")
	objective.position = Vector3(16, terrain.data.get_height(Vector3(16, 0, 16)), 16)
	var pedestal = MeshInstance3D.new()
	pedestal.name = "AncientPlinth"
	pedestal.mesh = CylinderMesh.new()
	pedestal.mesh.top_radius = 0.52
	pedestal.mesh.bottom_radius = 0.65
	pedestal.mesh.height = 0.17
	pedestal.mesh.radial_segments = 8
	pedestal.position.y = 0.04
	pedestal.material_override = stone
	add(pedestal, objective)
	var relic = prop("stones_001_stone_02", "Oathstone", objective.position + Vector3(0, 0.12, 0), 1.1, 0.25, false)
	# Keep the monolith narrow enough to leave all four capture cells accessible.
	relic.scale.x = 0.52
	relic.scale.z = 0.52
	var ring = MeshInstance3D.new()
	ring.name = "CaptureRing"
	ring.mesh = TorusMesh.new()
	ring.mesh.inner_radius = 1.47
	ring.mesh.outer_radius = 1.53
	ring.position.y = 0.08
	ring.material_override = gold
	add(ring, objective)
	var beacon = MeshInstance3D.new()
	beacon.name = "Beacon"
	beacon.mesh = SphereMesh.new()
	beacon.mesh.radius = 0.17
	beacon.mesh.height = 0.46
	beacon.mesh.radial_segments = 4
	beacon.mesh.rings = 2
	beacon.position.y = 1.5
	beacon.material_override = gold
	add(beacon, objective)
	for i in range(8):
		var angle = i * TAU / 8
		var mark = cube("Rune", Vector3(sin(angle) * 1.2, 0.045, cos(angle) * 1.2), Vector3(0.08, 0.025, 0.25), gold, objective)
		mark.rotation.y = angle
	for i in range(2):
		var marker = Marker3D.new()
		marker.name = "Assassin" if i == 0 else "Ashveil"
		marker.position = cell(1, 7) if i == 0 else cell(14, 8)
		add(marker, level.get_node("SpawnPoints"))
		var disc = MeshInstance3D.new()
		disc.name = "WestDeployment" if i == 0 else "EastDeployment"
		disc.position = marker.position + Vector3(0, 0.018, 0)
		disc.mesh = CylinderMesh.new()
		disc.mesh.top_radius = 0.64
		disc.mesh.bottom_radius = 0.64
		disc.mesh.height = 0.016
		disc.material_override = material(Color(0.07, 0.38, 0.52) if i == 0 else Color(0.55, 0.13, 0.16))
		add(disc, level)
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(level)
	if result == OK:
		result = ResourceSaver.save(packed_scene, "res://Scenes/StartingLevel.tscn")
	print("STARTING LEVEL BUILT: ", error_string(result), "; props=", props.get_child_count(), "; regions=", terrain.data.get_region_count())
	# Release authored objects before shutting down the headless tool.
	level.free()
	packed_scene = null
	terrain = null
	quit(0 if result == OK else 1)
