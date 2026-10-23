import json
from pathlib import Path
root=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin');out=root/'inspection_original_models'
data=json.loads((out/'inventory_geometry.json').read_text())
supp=json.loads((out/'supplemental_geometry.json').read_text())
integrity=json.loads((out/'original_file_integrity.json').read_text())
names=['Armored boot / greave','Knee guard with straps','Bronze forearm bracer','Scarf with tattered shoulder cape','Crimson hood','Belted waist skirt / hanging panels','Dark fantasy pauldron','Spiked shoulder pauldron','Strapped chest armor']
lines=['''# Hooded Assassin — Asset Inspection and Preparation

Inspection date: 2026-10-20. Project: Pawns of Divinity. Scope: inspection and recommendations only; approval required before repairs, assembly, optimization, texturing or rigging.

## Findings and preservation

Located character directory: `D:/SoftwareEng/Game/SourceAssets/characters/hooded_assassin`.

The requested `original_models` folder is actually spelled **`orignal_models`** on disk. It was not renamed. Recursive search found **nine GLB files**, no GLTF, FBX or OBJ files, and no texture sidecars. All nine imported successfully in Blender 5.2.2 LTS. Combined count: **7,171,221 triangles**. There are no byte-identical files: nine distinct SHA-256 hashes.

Blender MCP was attempted first; both the add-on handshake and scene query returned **Not connected to Blender**. Actual mesh inspection and six-view renders were therefore performed in separate background Blender processes. This report does not claim a successful live MCP inspection for this phase. The live scene was not used, reset or saved. Each original was imported into a disposable scratch scene; no original model file was saved, modified, deleted or repaired. Before/after SHA-256 checks match for every file in the source folder. Base projects were opened read-only and were not saved.

All nine source meshes are fully triangulated, have no UV maps, no armatures, no vertex groups, and no modifiers. Six have a single placeholder `Material_0` assigned throughout; three have no material. None has embedded image textures. There are no existing separate steel, bronze, leather or fabric material regions to preserve. Names and silhouettes are the evidence for intended roles, not proof of material color.

**Quality decision:** all nine are **Major Fixes** relative to final animated game use. Eight need substantial topology reduction and all need UV/material preparation and fitting; the small bracer needs overlap/open-edge review. They remain useful sources for their exterior designs. No piece currently warrants **Regenerate** based on inspected geometry, and none is **Ready** for final assembly/export. This rating includes production preparation, not just artistic quality.

## 1. Complete asset inventory

Dimensions below are imported world-space bounding-box X × Y × Z in Blender units, not verified real-world garment sizes. Object count includes Empty parents; every file contains exactly one mesh object. Armatures = 0 and UV maps = 0 for every row.

| ID | Identified asset | Filename | Format | Dimensions X × Y × Z | Objects (meshes) | Vertices | Triangles | Materials |
|---|---|---|---|---|---:|---:|---:|---|
''']
for i,(entry,name) in enumerate(zip(data,names),1):
    dims=' × '.join(f'{v:.4f}' for v in entry['bounds']['dimensions'])
    mats=', '.join(entry['meshes'][0]['materials']) or 'None'
    lines.append(f"| {i:02} | {name} | `{entry['filename']}` | GLB | {dims} | {entry['object_count']} (1) | {entry['vertices']:,} | {entry['triangles']:,} | {mats} |\n")
lines.append('''
Asset 01 has one Empty parent plus its mesh. Its world transform inherits uniform scale approximately 1.001512 and a small translation from the parent; the mesh object's own local transform is identity. Other meshes have identity local/world placement. No mirrored/negative object scales were found. Meshes are centered near world origin, commonly with geometry below Z=0, rather than positioned on a character or given anatomical pivots. This is normal for isolated generation, but unsuitable for direct attachment. Unit scale 1 is not evidence that a 1.9-unit bracer or hood should be 1.9 meters tall.

![Asset overview](inspection_original_models/asset_overview.jpg)

## 2. Geometry screening

| ID | Connected islands | Open boundary edges | Edges with >2 faces | Exact duplicate vertex coordinates | Duplicate faces by vertex IDs | Nonadjacent triangle intersection pairs | Rating |
|---|---:|---:|---:|---:|---:|---:|---|
''')
for i,entry in enumerate(data,1):
    m=entry['meshes'][0]
    lines.append(f"| {i:02} | {m['island_count']} | {m['boundary_edges']} | {m['overconnected_edges']} | {m['exact_duplicate_vertices']} | {m['duplicate_index_faces']} | {m['self_intersection_pairs']} | Major Fixes |\n")
lines.append('''
No wire edges, loose vertices, inconsistent winding across manifold edges, or faces below area 1e-12 local units² were found in any asset. No non-manifold vertices were reported by BMesh; the bracer nevertheless has 11 boundary edges, so it is not watertight. Zero boundary edges on the other assets means their surfaces close around a volume, not that they have usable wearable cavities. A thick garment with connected inner and outer surfaces may correctly have no boundary edges.

The intersection test uses Blender BVH surface overlaps, excludes triangle pairs sharing a vertex, and counts triangle pairs rather than separate defect sites. It can flag intentional interpenetrating layers; coplanar, adjacent-face, near-contact and fully enclosed non-intersecting surfaces are not exhaustively resolved by it. Duplicate-face screening checks common vertex IDs; it does not prove absence of all geometrically coincident sheets. Signed volume and winding tests do not prove that every surface normal has the intended artistic orientation. Six-view renders plus island/containment analysis inform the observations below. No automatically detected island, open edge or interior shell is recommended for indiscriminate deletion.

### 01 — Armored boot / greave — Major Fixes

**Observed:** the generically named model-edit file is one boot with a tall armored shin shaft. Recognizable toe, sole, ankle bands, shin relief and top rim. A single connected closed surface fuses the boot and greave construction; no loose debris islands. One nonadjacent intersection pair is flagged. The top view shows a deep closed-looking shaft recess; a continuous calf/foot-sized cavity is not established. The closed sole is intentional and should remain. The underside's simple sole pattern is also intentional geometry, not a cap to remove indiscriminately.

**Preparation:** retain the silhouette and major shin plates as the source. Inspect a section along the shaft and ankle against the MPFB calf and foot; remove fill only where it obstructs those regions. Resolve the one overlap if visible/problematic. Derive an economical shell with ankle articulation; rigid shin plates should not deform through the ankle. Toe/sole and upper boot must follow foot/ball movement. Only one side is supplied; determine handedness after fitting and create the opposite working copy later. Use calf and ankle/foot pivots, not the import center.

Views: [six-view sheet](inspection_original_models/01_views.jpg).

### 02 — Knee guard with straps — Major Fixes

**Observed:** faceted knee plate with smaller lower plate, two buckled rear straps and a visually open region behind the guard. All features are fused into one connected mesh. Twenty-two triangle intersection pairs are flagged; location/visibility must determine which need correction. No loose island or open boundary defects were found. Intentional strap/plate overlaps and the guard's concavity must not be mistaken for trash or repaired into a solid knee block.

**Preparation:** preserve the angular front outline, strap silhouette and buckle relief. Refit the strap loops to the knee envelope; inspect posterior-knee clearance during flexion. Use low-poly rigid knee/lower plates with deforming straps or carefully chosen bone influence; do not bridge the joint with a single rigid assembly that locks the knee. Selectively retain/separate moving layers only when the animation requires it. One guard supplied; confirm whether the complete costume wants a pair.

Views: [six-view sheet](inspection_original_models/02_views.jpg).

### 03 — Bronze forearm bracer — Major Fixes

**Observed:** already relatively light at 4,419 triangles, but six islands contain 742, 440, 382, 242, 211 and 207 vertices. These are substantial overlapping plate/strap components, not isolated single-vertex debris. The two ends appear open and the shaft has wearable potential. Eleven boundary edges occur on the largest plate, and one pair of exactly coincident vertex coordinates exists. These are inspection targets; the coincident vertices may belong to intended component contact and must not be globally welded without review.

The 441 intersection pairs split into **430 between separate islands** and **11 within the largest plate**. Much of the between-island overlap is consistent with intentional layered construction, although excessive penetration can still create shading/baking problems. The within-plate intersections deserve priority. There is no reason to delete the straps merely because they are disconnected.

**Preparation:** retain the existing low-poly forms where sound. Review the main plate's 11 open edges and 11 within-plate overlaps locally. Separate rigid forearm armor from the hand-covering extension if wrist flexion requires it. Refit cross-section without flattening the decorative ridge; check elbow spikes and wrist range. Rotate its length axis from imported Z to the MPFB arm axis, then reposition. A rigid cuff can follow `lowerarm_l/r`; a hand plate can follow `hand_l/r`; spanning straps need a short blend. No UV/material exists despite the bronze filename.

Views: [six-view sheet](inspection_original_models/03_views.jpg).

### 04 — Scarf with tattered shoulder cape — Major Fixes

**Observed:** this is not only a short neck scarf. It includes a neck wrap and long shoulder/back cloth with many ragged tears and fine hanging threads. A visible neck passage exists in top/bottom views. Two closed islands contain 647,045 and 4,556 vertices. The smaller shell has negative signed volume and lies inside the major component (ray-parity containment test; no triangle intersections). This is consistent with a sealed inward-facing cavity shell, not proof of externally floating debris or a globally flipped mesh.

**Preparation:** preserve the scarf folds, broad drape, ragged outer silhouette and important large tears. Keep a few purposeful tears; simplify subpixel threads and micro-perforations on a gameplay derivative. Section the smaller interior shell before deciding whether it is unnecessary hidden geometry. Do not flip all its normals solely because its volume is negative. Create cloth edge flow across shoulders and down the back; pin the upper wrap with neck/chest influence, then use a few cloth chains or manually animated cloth bones. The 53-bone MPFB rig has no cape chains, so those would require a later approved rig extension. Check the hood hem, pauldrons and crossed chest straps. Two-sided shading may suit thin cloth; keep thickness only at visible folds and hems where justified.

Views: [six-view sheet](inspection_original_models/04_views.jpg).

### 05 — Crimson hood — Major Fixes

**Observed:** a clean broad pointed silhouette, rim and readable folds. One connected closed surface; no reported intersections, duplicate coordinates or open-edge defects. The face aperture leads into a cup-like inner surface; the bottom view shows a largely enclosed neck/hem region. This is not verified to be a head-and-neck-sized cavity just because the face aperture is visible. Its 189,676 triangles are excessive for these broad shapes.

**Preparation:** preserve rim thickness, point, profile and a few large folds. Check a section for head volume, neck access and back-of-head clearance against the actual MPFB head. Retopologize a simple hood shell around the existing exterior. Do not remove the back of the hood or its visible inner lining as if they were errors. Mostly follow `head`, with a modest `neck_01`/upper-chest blend at the hem if needed. Check head turns and chin tuck against scarf/chest/pauldrons. No UV or crimson texture is present.

Views: [six-view sheet](inspection_original_models/05_views.jpg).

### 06 — Belted waist skirt / hanging panels — Major Fixes

**Observed:** despite the truncated “Tattered_Mant” filename, this is waist equipment: belt, crossed straps, upper hip plates and long hanging cloth panels. It is distinct from the shoulder cape. The top is substantially capped around a tiny square recess/passage; the underside shows filled rounded interior forms. This is an assembly obstruction at the pelvis/waist, not a reason to delete the belt or upper plates. Four intersection pairs are within the major shell.

Two islands contain 454,464 and 9,747 vertices. The second has negative volume and is contained inside the major volume with no inter-island intersections. As with the scarf, classify the nested shell in a section before removing it or reversing normals.

**Preparation:** establish a pelvis-sized opening and leg clearance on a derivative while retaining the belt, crossed straps, plates, major torn edges and cloth length. Inspect the internal filled forms against upper thighs; simplify only hidden/nonfunctional fill. Distinguish rigid hip plates from skirt panels for deformation. Belt should primarily follow `pelvis`; panels require thigh-aware weighting or a few separate cloth chains. Test wide stance, walking stride, crouch and kneel. Resolve its belt overlap with the chest armor's belt deliberately; do not stack both by default or silently remove either design.

Views: [six-view sheet](inspection_original_models/06_views.jpg).

### 07 — Dark fantasy pauldron — Major Fixes

**Observed:** spiked upper shoulder cap, several lower plates and rear/underside strap-like geometry. All are fused into one connected closed mesh. Fourteen triangle intersection pairs are flagged. Bottom/rear views show substantial filled surfaces, rather than a verified shoulder cavity. There are no disconnected fragments to remove automatically. Some bulky underside forms may be functional straps, inner supports or unwanted AI fill; a fitted section must decide.

**Preparation:** preserve the crest/spikes, overlapping plate edges and asymmetric profile. Fit to a shoulder envelope and remove only confirmed obstructing underside material. A shoulder cap can follow the clavicle/upper-arm relationship; lower plates may need separate upper-arm influence to preserve overlap through an arm raise. Do not bind the entire long silhouette rigidly to the chest or uniformly skin its plates like cloth. Inspect scarf contact. This overlaps the role of asset 08; use an intentional asymmetric pair or select one design, rather than overlapping them on the same shoulder.

Views: [six-view sheet](inspection_original_models/07_views.jpg).

### 08 — Spiked shoulder pauldron — Major Fixes

**Observed:** a second pauldron design, with a large pointed cap, prominent raised crest and long lower lames. This is not a shield despite the truncated “Bulwa” filename. One fused connected surface, with three flagged intersection pairs and no boundary/winding defects. The inner/back surface is broad and mostly closed; it can serve as the inner side of a thick armor shell and is not automatically a defect. Clearance has not been verified at a shoulder scale.

**Preparation:** preserve its recognizable cap, crest and long tapered silhouette. Reduce broad hidden inner geometry only after fitting and section inspection. Keep motion between lower plates if required by the selected animation range. Use the same shoulder-motion principles as asset 07. Confirm intended left/right assignment before mirroring or making both shoulders identical. The prior standalone pauldron projects are derivatives/context, not extra originals in this inventory.

Views: [six-view sheet](inspection_original_models/08_views.jpg).

### 09 — Strapped chest armor — Major Fixes

**Observed:** one connected mesh fuses sculpted chest/side plates, crossed straps, belt, buckles and raised decorations. No self-intersection pairs or topology defects were flagged by this screen. Neck/arm rims lead into restricted filled recesses; bottom is capped around a small square feature. It lacks a continuous torso-sized cavity. No UVs or material assignments exist. This is the same 697,806-triangle source design inspected earlier.

**Preparation:** retain it as the exterior detail source. Reconstruct only the necessary interior and openings on a derivative, preserving visible rims, silhouette and decorated front/back. Retopologize deformation zones deliberately around waist and armholes; retain rigid plates where appropriate. Spine-weight the flexible underlayer/straps and use consistent rigid weights on plate regions. Check twist, side bend, arm lift, and interaction with waist panels and both shoulder designs. Keep belts/straps visually attached throughout motion. Do not replace the exterior with primitives.

The earlier `modular/chest_plate/assassin_chest_plate_v002.blend` contains a 60k initial review derivative. That is outside this original-file inventory, is not the final low-poly solution, and has unresolved intersection flags. The earlier 15k trial visibly degraded relief; it should not be adopted by count alone. The lower style budget below would require intentional selective retopology and detail transfer, not repeated global collapse.

Views: [six-view sheet](inspection_original_models/09_views.jpg).

## 3. Humanoid base and proportional compatibility

**Verified MPFB candidate:** `base/assassin_base.blend`, objects `Assassin_Body`, `Assassin_Skeleton`, `Assassin_Eyes`. Rest-pose body height **1.8000 m**, T-pose span **1.8356 m**, scene unit scale 1. Skeleton has **53 bones** including `pelvis`, `spine_01`–`spine_03`, `neck_01`, `head`, `clavicle_l/r`, `upperarm_l/r`, `lowerarm_l/r`, `hand_l/r`, `thigh_l/r`, `calf_l/r`, `foot_l/r`, `ball_l/r`. Body source mesh has 19,158 vertices and 36,972 triangles including helper geometry; an existing Mask modifier hides helpers. This is not the final body export triangle count. Eyes add 172 source triangles. Preserve the existing skeleton and helper workflow.

These measured envelopes use evaluated visible body vertices with combined named-bone weight >0.5, so they are approximate fitting references rather than exact anatomical slices:

| MPFB region | Measured reference |
|---|---|
''')
regions=supp['mpfb_landmarks']['weighted_region_bounds']
for name in ['head','torso','forearm_l','lowerleg_l','foot_l']:
    d=regions[name]['dimensions']
    lines.append(f"| {name} | X × Y × Z = {' × '.join(f'{v:.4f}' for v in d)} m |\n")
lines.append('''
Left forearm bone length is 0.2656 m; left calf bone length is 0.4523 m. MPFB arms extend along X in rest pose, whereas the bracer's long axis is Z. All generated assets require substantial scale and placement changes; the hood is nearly body-height at import, the boot/greave is 1.9074 units tall, and the bracer is 1.0 unit long. Their independent normalized sizes prevent treating them as proportionally compatible at import scale.

Examples of dimensional starting points, **not approved or demonstrated fits**: matching the bracer's 1.0-unit length to the 0.2656 m forearm gives scale 0.2656 before hand-extension/elbow clearance adjustments; matching hood external height to the measured 0.2525 m head envelope gives a lower-bound scale about 0.134, which must increase for internal clearance, cloth thickness and rim shape; matching the boot's 1.1173-unit depth to the 0.2655 m foot depth gives scale about 0.238, before checking calf coverage and armor thickness. These independent ratios are not instructions to force exact dimension matches. They show why cavity-aware fitting and some reshaping will be necessary.

**Attachments:** 01 foot/calf; 02 knee; 03 forearm/hand; 04 neck/shoulders/back; 05 head/neck; 06 pelvis/hips/upper legs; 07–08 shoulders/upper arms; 09 torso. All have useful shapes, but actual fit remains unverified. No asset has been transformed, assembled on the body, bound or pose-tested in this inspection.

**Other existing character:** `blendswap_assassin/assassin_refined.blend` contains the historical clothed Eliber-based character and a different 96-bone `Assassin_Animation_Rig`. It is not the MPFB skeleton. Its scene includes a 200 × 200-unit floor, so whole-scene bounds and the auto-framed inspection render are unsuitable for body measurements. The report uses the verified neutral MPFB candidate above, not that scene's bounding box. Do not combine skeletons or transfer weights by matching names blindly.

### Layer and proportion risks to test after approval

- Chest belt versus waist-skirt belt: competing waist widths, heights and buckles; select an intentional overlap hierarchy.
- Hood hem versus scarf collar: both occupy neck space; preserve throat/chin clearance through head turn and nod.
- Scarf/cape versus pauldrons: cloth needs a consistent route over/under the rigid caps; check snagging and armor exposure through arm raises.
- Chest armholes versus pauldrons/upper arms: present filled interiors and thick rims may block motion.
- Knee guards versus greave top and skirt panels: preserve hinge clearance during crouch, kneel and wide stance.
- Bracer hand extension versus wrist/glove: rigid spans across the wrist will restrict grips unless articulated or separated locally.

These are predicted collision zones from independent shapes and attachment roles, not measured assembled interpenetrations. Exact inter-asset overlap, cavity fit, side assignment and corrective reshaping remain untested because assembly is explicitly deferred.

## 4. Real-time optimization proposal

These are art-direction starting budgets for a **GameCube-inspired stylized tactical camera**, not a claim about exact historical hardware limits or a tested engine budget. Target a complete visible LOD0 character at roughly **12k–20k triangles including body, outfit, paired armor and a small weapon**. Prioritize readable silhouettes, joint movement and broad folds. Reserve higher counts only for camera-tested close-up needs. Profile pawn count and draw calls before fixing the final budget.

| Asset | Suggested gameplay triangles | Preserve as geometry | Simplify / transfer later |
|---|---:|---|---|
| 01 Boot + greave | 900–1,400 each; 1,800–2,800 pair | Sole/toe outline, shin silhouette, ankle separation | Fine engraving, hidden shaft detail, small layered ridges |
| 02 Knee guard | 250–450 each; 500–900 pair | Faceted knee outline, lower point, major straps | Tiny rivets/buckle microdetail |
| 03 Bracer | 350–650 each; 700–1,300 pair | Cuff profile, main ridge, hand point, strap silhouette | Inner overlap complexity and subpixel seams |
| 04 Scarf + cape | 1,200–2,000 total | Scarf bulk, drape, major torn edge and selected tears | Tiny hanging threads, interior bubble, micro-perforations after review |
| 05 Hood | 600–1,000 | Hood point, face rim, major folds | Dense smooth patches and minor wrinkles |
| 06 Waist skirt | 800–1,400 total | Belt silhouette, hip plates, large hanging panels | Fine rivets/chains/engraving and sealed internal shells after review |
| 07 or 08 Pauldron | 600–1,000 each; 1,200–2,000 for two shoulders | Crest/spikes, cap silhouette, overlap of main lames | Hidden underside density, tiny raised lines |
| 09 Chest assembly | 1,800–3,000 | Chest planes, crossed straps, belt/buckle silhouette, major relief | Fine raised patterns and tiny bevels |
| Visible body, head, hands and basic underclothes | 2,500–4,500 combined | Face/hand silhouette and joint loops | Hidden body areas only on an approved export derivative |
| Small weapon | 400–800 | Blade/grip silhouette | Engraving and subpixel bevels |

The approximate summed range is 11.5k–19.7k with two shoulder pieces. If these budgets erase important details, raise the relevant budget deliberately after visual comparison. Do not force 15k—or any count—by blind global decimation. The current 7.17M source set is a high-poly reference library, not a gameplay assembly. Controlled retopology is especially important for cape folds, waist panels, armpits and wrist/ankle zones. Rigid plates may use economical triangulation; an all-quad requirement is unnecessary for them.

**Textures/materials:** begin with a shared 1024² armor/leather atlas and a 512² cloth atlas (hood/scarf/skirt); 512² for both can be tested for a stricter low-resolution look. A small 256²–512² weapon atlas may be shared with armor. This is a texel-density proposal, not existing texture content. Use coherent painted steel/bronze/leather/fabric regions inside shared atlases rather than creating a draw call for every buckle or strap. At most two main character material batches is a useful initial goal, subject to cloth transparency needs. For a deliberately retro look, strong painted values and broad folds can carry the design; optional baked normals should be subtle, not used to rescue a destroyed silhouette. Keep only meaningful torn openings; alpha clipping can represent selected fine tears if stable at tactical distance. Avoid dense transparent thread meshes and unnecessary double-sided overdraw.

**Later source-to-low workflow:** preserve original high-poly files; use distinct derivative collections; establish clean wearable cavities; build low-poly surfaces around the existing design; define material masks and UVs; bake normals/AO only after explicit approval, checking ray cages around overlapping straps and thin cloth. Preserve actual rim thickness and major bevel silhouettes. Validate in the tactical camera, then make LOD1 around 50–60% and LOD2 around 25–35% of the approved LOD0, retaining garment lengths and signature spikes. These are proposals only; no optimization or baking was performed here.

## 5. Missing pieces and duplicate roles

- **No weapon, dagger, sword, bow, sheath or holster** exists in `orignal_models`. A weapon is therefore missing from this new source set if the assassin requires one.
- No separate gloves/hand underlayer, trousers/leggings, torso undershirt, upper-arm sleeves or dedicated face mask are supplied here. They may be created from the approved base workflow or selectively sourced elsewhere later; this inspection does not authorize reusing or editing historical clothing. Bare hands/upper arms may be an intentional costume choice, so not every absent garment is mandatory.
- Only one boot/greave, knee guard and bracer asset is supplied. Opposite-side counterparts are absent as explicit files. Mirroring derivative geometry may suffice after handedness, buckles and asymmetry are reviewed; do not regenerate automatically.
- Assets 07 and 08 are two different shoulder designs, not exact duplicates. They could be an intentional asymmetric pair or alternatives. Do not stack them on the same shoulder.
- Asset 04 is the neck/shoulder cape; asset 06 is waist clothing despite its filename. They are not duplicate capes.
- Chest 09 and skirt 06 both include belts. This is duplicated functional coverage that requires an art decision, not a byte-identical duplicate asset.
- No UV layouts, embedded texture images, generated-asset skeletons or weights are included. The verified MPFB skeleton exists outside this folder and should be reused rather than replaced.

## 6. Proposed assembly order, after approval

1. Choose the neutral MPFB base as the fitting reference; retain its T pose, body scale, helper-mask setup and 53-bone skeleton. Work in a new derivative project, preserving originals.
2. Establish underclothes/skin coverage and compare all source silhouettes in separate fitting copies. Set side assignments and decide whether both shoulder designs and both waist belts belong in the costume.
3. Fit foot/greave and knee armor to establish leg scale and knee/ankle clearance. Prepare opposite-side copies only after fit is sound.
4. Fit the waist skirt/belt around pelvis and thighs. Keep stride clearance and intended hem lengths.
5. Fit chest armor over the torso/waist layer, correcting only confirmed blocking interior geometry and resolving the belt hierarchy.
6. Fit bracers and any hand plates; check elbow/wrist limits and weapon grip space.
7. Fit shoulder armor against the chest and upper-arm motion envelope. Set plate articulation and scarf-over/under ordering.
8. Fit hood and scarf/cape around head, neck and shoulders together, preserving recognizable outlines and allowing head turns.
9. Approve a neutral-pose silhouette, then optimize selectively, create UV/material regions, and validate before any rigging or baking stage is started.

This is a recommendation, not an assembly already performed. Solve simple fitting proxies first if needed; they must not replace detailed production exteriors.

## 7. Rigging and animation workflow, after separate approval

Reuse `Assassin_Skeleton`; do not delete, rename or rescale its bones to accommodate arbitrary import dimensions. Transform fitting derivatives into the rig's coordinate space before binding. Retain the original body and use a separate export derivative for any hidden-body culling. Export helpers through the established mask workflow rather than deleting MPFB source helper geometry.

Transfer body weights only as a starting point for flexible underlayers, then manually correct joint zones. Armor plates should use consistent rigid-region weights or local bone following; straps may need blended weights. `spine_01`–`spine_03` support torso follow, `pelvis` supports belts, `lowerarm_l/r` supports bracer cuffs, `hand_l/r` supports hand plates, `calf_l/r` supports shin plates, and `foot_l/r`/`ball_l/r` support boot motion. Knee and shoulder pieces require pose-tested attachment choices, not a blanket single-bone rule. Hood generally follows `head` with hem blending to neck. Cape/skirt free ends need a small approved cloth-bone extension or an explicit simpler animation approach; the existing MPFB rig has no dedicated cloth chains.

Test idle breathing, full stride/run, crouch/kneel, torso twist, arm raise, cross-body reach, head turn/nod, dagger grip and attack/recovery. Check plate separation, strap attachment, skirt leg clipping and cape/shoulder collisions from the tactical camera. Correct the fitted derivative, not the source. Limit deform influences and material batches to the chosen engine/export settings; validate deformation, normal maps, tangents, backface behavior and GLB export in the game engine before calling an asset Ready.

## 8. Evidence, limitations and next approval

Inspection evidence is saved in `inspection_original_models/`:

- `inventory_geometry.json`: full per-file and per-object counts, bounding boxes, transforms, island bounds, surface checks, materials and UV records.
- `supplemental_geometry.json`: bracer intersection grouping, nested-shell containment checks and measured MPFB landmarks/envelopes.
- `base_assessment.json`: MPFB and historical Eliber project object/skeleton metadata. Historical scene-wide bounds include its studio floor and must not be used as body measurements.
- `original_file_integrity.json`: original file SHA-256 values before and after inspection; all match.
- `asset_overview.jpg`, `01_views.jpg`–`09_views.jpg`: labeled overview and six-view sheets; individual front/back/side/three-quarter/top/bottom PNG renders are also retained.
- `base_assassin_base_front.png` and `base_assassin_base_side.png`: neutral MPFB reference renders. The historical clothed scene's auto-framed renders include its huge studio floor and are not useful fitting views.

Every supported file found was imported and inspected. The remaining limitations are live MCP unavailability, unperformed assembled clearance/pose tests, and the normal limitations of BVH, duplicate-index and signed-volume screening described above. Small visual surface defects, exact deformation requirements and hidden-layer removal decisions require closer fitted section inspection after approval. No original was repaired to make a test pass.

**Stop for approval:** approve a base/side/layer plan and a repair order before proceeding. Recommended first repair studies are the chest and waist openings, bracer local overlap/open-edge cleanup, and shoulder motion clearance. Keep the original exterior designs as the reference throughout. No repairs, assembly, new rig, texture bake or automatic optimization has been started in this inspection phase.
''')
assert len(data)==9 and all(d['status']=='inspected' for d in data)
assert integrity['all_original_files_unchanged']
path=root/'asset_inspection_report.md';path.write_text(''.join(lines),encoding='utf-8')
print('REPORT_SAVED',path,'bytes',path.stat().st_size)
