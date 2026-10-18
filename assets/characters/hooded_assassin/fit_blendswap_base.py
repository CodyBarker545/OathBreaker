"""Fit Eliber's downloaded CC0 body to the assassin equipment and a clean FK rig.

The original downloaded .blend is preserved unchanged under characters/.
"""
import bpy, os, math, bmesh
from mathutils import Matrix, Vector

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'..','..','..'))
BASE=os.path.join(ROOT,'characters','Eliber_Rigged_Base_Mesh','Lowpolymesh_Eliber.blend')
OUT=os.path.join(HERE,'blendswap_assassin')
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'hooded_assassin.blend'))
oldrig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
collection=bpy.data.collections['ASSASSIN | editable character parts']
oldparts=[o for o in collection.objects if o.type=='MESH']
with bpy.data.libraries.load(BASE,link=False) as (src,dst):
    dst.objects=['Armature','Base mesh']
rig,body=dst.objects
collection.objects.link(rig); collection.objects.link(body)
body.name='Eliber | fitted continuous body'
rig.name='Assassin | Eliber base skeleton'
rig.animation_data_clear()
for pb in rig.pose.bones:
    for con in list(pb.constraints): pb.constraints.remove(con)
    pb.custom_shape=None
    pb.matrix_basis=Matrix.Identity(4)
rig.data.pose_position='POSE'

# Normalize the downloaded body to approximately two metres, then fit the
# underlying bone landmarks to the already-authored outfit.
scale=1.95/11.25154686
M=Matrix.Translation((0,0,5.89101839*scale)) @ Matrix.Scale(scale,4)
rig.data.transform(M); body.data.transform(M)
rig.matrix_world=Matrix.Identity(4); body.matrix_world=Matrix.Identity(4)
# Remove the hidden head and hands in the fitted copy: the authored masked
# head and gloves replace these surfaces. The supplied source is untouched.
bm=bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if abs(v.co.x)>.72 or v.co.z>1.67],context='VERTS')
bm.to_mesh(body.data); bm.free()
oldmat={b.name:b.matrix_local.copy() for b in rig.data.bones}
oldlength={b.name:b.length for b in rig.data.bones}
targets={
    'Body control':((0,0,0),(0,0,.2)),
    'Body':((0,0,1.08),(0,-.14,1.08)),
    'Spine bot':((0,0,1.08),(0,0,1.25)),
    'Spine mid':((0,0,1.25),(0,0,1.43)),
    'Spine top':((0,0,1.43),(0,0,1.61)),
    'Neck':((0,0,1.61),(0,0,1.73)),
    'Head':((0,0,1.73),(0,0,1.97)),
}
renames={'Body control':'root','Body':'pelvis','Spine bot':'lower_spine','Spine mid':'mid_spine','Spine top':'chest','Neck':'neck','Head':'head'}
for s,base_side,side in [(1,'L','R'),(-1,'R','L')]:
    targets.update({
        'Hip .'+base_side:((0,0,1.08),(s*.12,0,1.06)),
        'Leg top .'+base_side:((s*.12,0,1.06),(s*.16,-.015,.61)),
        'Leg bot .'+base_side:((s*.16,-.015,.61),(s*.18,.005,.16)),
        'Feet top .'+base_side:((s*.18,.005,.16),(s*.18,.005,.12)),
        'Feet .'+base_side:((s*.18,.005,.12),(s*.18,-.16,.08)),
        'Shoulder .'+base_side:((0,0,1.43),(s*.255,0,1.56)),
        'Arm .'+base_side:((s*.255,0,1.56),(s*.38,-.005,1.29)),
        'Hand .'+base_side:((s*.38,-.005,1.29),(s*.47,-.045,1.045)),
        'Wrist .'+base_side:((s*.47,-.045,1.045),(s*.49,-.054,.995)),
    })
    for src,dest in [('Hip .','hip.'),('Leg top .','thigh.'),('Leg bot .','shin.'),('Feet top .','ankle.'),('Feet .','foot.'),('Shoulder .','clavicle.'),('Arm .','upper_arm.'),('Hand .','forearm.'),('Wrist .','hand.')]:
        renames[src+base_side]=dest+side

bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
edit=rig.data.edit_bones
for b in edit: b.use_connect=False
for name,(head,tail) in targets.items():
    b=edit[name]; b.head=head; b.tail=tail; b.roll=0
# Finger bones retain their original topology and hierarchy, transformed from
# the T-pose palm onto the new relaxed palm. No fingers are fabricated.
for side in ['L','R']:
    wrist=edit['Wrist .'+side]
    T=wrist.matrix @ Matrix.Scale(.65,4) @ oldmat['Wrist .'+side].inverted()
    for b in edit:
        ancestor=b.parent
        isfinger=False
        while ancestor:
            if ancestor.name=='Wrist .'+side: isfinger=True; break
            ancestor=ancestor.parent
        if isfinger: b.transform(T)
# The old IK helper bones are unnecessary for the clean FK animation setup.
for b in list(edit):
    if b.name not in targets and not b.use_deform:
        edit.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')

# Preserve and refit the supplied skinned mesh using its existing weights.
transforms={}
for b in rig.data.bones:
    stretch=b.length/max(oldlength[b.name],.0001)
    transforms[b.name]=b.matrix_local @ Matrix.Diagonal((1,stretch,1,1)) @ oldmat[b.name].inverted()
for v in body.data.vertices:
    q=Vector(); total=0
    for g in v.groups:
        n=body.vertex_groups[g.group].name
        if n in transforms and g.weight>0:
            q+=(transforms[n]@v.co)*g.weight; total+=g.weight
    if total>0: v.co=q/total
for old,new in renames.items():
    rig.data.bones[old].name=new
    if old in body.vertex_groups: body.vertex_groups[old].name=new
body.parent=rig; body.matrix_parent_inverse=Matrix.Identity(4)
for mod in body.modifiers:
    if mod.type=='ARMATURE': mod.object=rig

# A charcoal undersuit with skin only at the face and upper arms.
body.data.materials.clear()
for n in ['Leather | charcoal','Skin | warm pale']:
    body.data.materials.append(bpy.data.materials[n])
skin_groups={'head','neck','upper_arm.L','upper_arm.R'}
for poly in body.data.polygons:
    scores=[]
    for vi in poly.vertices:
        v=body.data.vertices[vi]
        scores.append(sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in skin_groups))
    poly.material_index=int(sum(scores)/len(scores)>.65)
    poly.use_smooth=True

# Retain the accessories; replace every procedural body segment with the
# downloaded, continuously skinned body. Gloves remain as fitted equipment.
replace_prefixes=('Torso |','Pelvis |','Thigh undersuit.','Calf undersuit.','Upper arm.','Forearm sleeve.')
for obj in oldparts:
    if obj.name.startswith(replace_prefixes) or 'dagger' in obj.name.lower() or 'grip wrap' in obj.name.lower() or 'hooked guard' in obj.name.lower():
        bpy.data.objects.remove(obj,do_unlink=True)
        continue
    for mod in obj.modifiers:
        if mod.type=='ARMATURE': mod.object=rig
    obj.parent=rig
bpy.data.objects.remove(oldrig,do_unlink=True)
rig.show_in_front=True
rig['base_author']='Eliber'
rig['base_url']='https://blendswap.com/blend/14675'
rig['base_license']='CC0; creator clarified change from CC-BY in listing comments'
rig['changes']='Normalized, body fitted, hidden head/hands replaced by authored face/gloves, skeleton converted to FK, legacy IK helpers removed. No weapons.'
scene=bpy.context.scene
scene['source_base']='Eliber Rigged Base Mesh, Blend Swap 14675, downloaded by user; fitted continuous body and adapted skeleton.'
scene['base_path']=BASE
scene.render.resolution_x=700; scene.render.resolution_y=770
scene.cycles.samples=16
scene.render.filepath=os.path.join(OUT,'fitted_rest.png')
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'assassin_fitted.blend'))
bpy.ops.render.render(write_still=True)
print('FITTED ELIBER BASE COMPLETE',len(body.data.vertices),'source body vertices',len(rig.data.bones),'bones')
