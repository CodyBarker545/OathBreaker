"""Animate the existing assassin while the Blend Swap base download is pending.

Run using Blender --background --python animate_assassin.py.
This does not claim to contain the third-party base mesh.
"""
import bpy
import math
import os
import json
from mathutils import Vector, Quaternion, Euler

HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.environ.get('ASSASSIN_OUT',os.path.join(HERE,'animated_prototype'))
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.environ.get('ASSASSIN_INPUT',os.path.join(HERE,'hooded_assassin.blend')),use_scripts=False)
scene=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.name='Assassin_Animation_Rig'
parts=[o for o in bpy.data.collections['ASSASSIN | editable character parts'].objects if o.type=='MESH']
bpy.context.view_layer.objects.active=rig
rig.select_set(True)

# Additional cloth chains give the scarf and tabards secondary motion.
chains={
    'scarf_back': ([(0,.145,1.65),(.03,.20,1.42),(.12,.25,1.14),(.22,.29,.86),(.31,.30,.53)],'chest','Scarf | long torn back banner'),
    'scarf_side': ([(-.08,.12,1.65),(-.28,.18,1.58),(-.48,.21,1.62),(-.66,.20,1.53)],'chest','Scarf | wind-swept left ribbon'),
    'tabard_front': ([(.02,-.18,1.06),(.09,-.19,.91),(.16,-.17,.72),(.22,-.16,.47)],'pelvis','Waist | torn crimson tabard'),
    'tabard_side': ([(-.12,.05,1.10),(-.24,.08,.89),(-.31,.11,.67),(-.35,.13,.53)],'pelvis','Waist | narrow torn strip'),
}
bpy.ops.object.mode_set(mode='EDIT')
for prefix,(points,parent,objname) in chains.items():
    for i in range(len(points)-1):
        bb=rig.data.edit_bones.new(prefix+'.%02d'%i)
        bb.head=points[i]; bb.tail=points[i+1]
        bb.parent=rig.data.edit_bones[parent if i==0 else prefix+'.%02d'%(i-1)]
        bb.use_connect=i>0
bpy.ops.object.mode_set(mode='OBJECT')
for prefix,(points,parent,objname) in chains.items():
    obj=bpy.data.objects[objname]
    obj.vertex_groups.clear()
    names=[prefix+'.%02d'%i for i in range(len(points)-1)]
    groups=[obj.vertex_groups.new(name=n) for n in names]
    for v in obj.data.vertices:
        # Ribbons were authored with three vertices per longitudinal row.
        row=v.index//3
        if row==0:
            groups[0].add([v.index],1,'REPLACE')
        elif row>=len(groups):
            groups[-1].add([v.index],1,'REPLACE')
        else:
            groups[row-1].add([v.index],.55,'REPLACE')
            groups[row].add([v.index],.45,'REPLACE')
    obj['attachment']='Smooth weighted cloth chain: '+prefix

# Keep equipment as separate objects attached to the same skeleton.
for obj in parts:
    if 'dagger' in obj.name.lower() or 'grip wrap' in obj.name.lower():
        obj['attachment']='Rigid hand-bone weights; follows grip through every clip'
    elif 'Vambrace' in obj.name or 'Shoulder' in obj.name:
        obj['attachment']='Rigid armour weights; plate retains its shape'

def reset():
    for pb in rig.pose.bones:
        pb.rotation_mode='QUATERNION'
        pb.rotation_quaternion=(1,0,0,0)
        pb.location=(0,0,0)
        pb.scale=(1,1,1)

def rotate(name,x=0,y=0,z=0):
    # Describe rotations in model rest axes, convert to the bone's local axes.
    pb=rig.pose.bones[name]
    basis=pb.bone.matrix_local.to_quaternion()
    q=Euler((x,y,z),'XYZ').to_quaternion()
    pb.rotation_quaternion=basis.inverted() @ q @ basis

def translate(name,xyz):
    pb=rig.pose.bones[name]
    pb.location=pb.bone.matrix_local.to_3x3().inverted() @ Vector(xyz)

def cloth_motion(phase,strength=1,lean=0):
    for prefix,(points,parent,objname) in chains.items():
        for i in range(len(points)-1):
            rotate(prefix+'.%02d'%i,
                   x=(.035*math.sin(phase-i*.7)+lean)*strength,
                   y=.035*math.sin(phase-i*.5)*strength,
                   z=.025*math.cos(phase-i*.6)*strength)

def pose_idle(t):
    p=t*2*math.pi
    rotate('chest',x=.012*math.sin(p),z=.012*math.sin(p))
    rotate('head',x=-.01*math.sin(p),z=-.016*math.sin(p))
    for s,side in [(-1,'L'),(1,'R')]:
        rotate('upper_arm.'+side,x=-.12+.012*math.sin(p),y=-s*.04)
        rotate('forearm.'+side,x=-.13)
    cloth_motion(p,.7)

def pose_walk(t):
    p=t*2*math.pi
    translate('pelvis',(0,0,.024+.018*math.cos(2*p)))
    rotate('chest',x=-.04,z=.045*math.sin(p))
    rotate('pelvis',z=-.025*math.sin(p))
    for s,side,phase in [(-1,'L',p),(1,'R',p+math.pi)]:
        swing=math.sin(phase)
        rotate('thigh.'+side,x=.34*swing)
        bend=.38*max(0,swing)
        rotate('shin.'+side,x=bend)
        rotate('foot.'+side,x=-.34*swing-bend)
        rotate('upper_arm.'+side,x=-.12-.27*swing,y=-s*.045)
        rotate('forearm.'+side,x=-.18-.16*max(0,-swing))
    cloth_motion(p,1.6,.018)

# Blocking poses for a deliberate two-dagger slash and recovery.
attack_keys=[
    (0.00, dict(rx=-.18,ry=-.04,lx=-.18,ly=.04,rz=0,cx=0,cz=0,bend=.0)),
    (0.22, dict(rx=-1.6,ry=-.48,lx=-.65,ly=.12,rz=-.35,cx=-.05,cz=-.20,bend=.04)),
    (0.38, dict(rx=-.65,ry=.85,lx=-.8,ly=.08,rz=.25,cx=-.14,cz=.22,bend=.055)),
    (0.56, dict(rx=-.45,ry=.18,lx=-1.55,ly=.48,rz=.10,cx=-.08,cz=.16,bend=.04)),
    (0.72, dict(rx=-.25,ry=-.04,lx=-.65,ly=-.72,rz=0,cx=-.12,cz=-.16,bend=.045)),
    (1.00, dict(rx=-.18,ry=-.04,lx=-.18,ly=.04,rz=0,cx=0,cz=0,bend=.0)),
]
def pose_attack(t):
    for (a,pa),(b,pb) in zip(attack_keys,attack_keys[1:]):
        if a<=t<=b:
            u=(t-a)/(b-a); u=u*u*(3-2*u)
            v={k:pa[k]*(1-u)+pb[k]*u for k in pa}; break
    rotate('upper_arm.R',v['rx'],v['ry'],v['rz'])
    rotate('upper_arm.L',v['lx'],v['ly'],-v['rz']*.5)
    rotate('forearm.R',-.22); rotate('forearm.L',-.22)
    rotate('chest',v['cx'],0,v['cz'])
    rotate('head',-v['cx']*.3,0,-v['cz']*.45)
    translate('pelvis',(0,0,-v['bend']))
    for side in ['L','R']:
        rotate('thigh.'+side,x=-v['bend']*3)
        rotate('shin.'+side,x=v['bend']*6)
        rotate('foot.'+side,x=-v['bend']*3)
    cloth_motion(t*math.pi*4,1.8,.025)

clips=[('Idle',49,pose_idle),('Walk',25,pose_walk),('Arm_Motion_Test',37,pose_attack)]
rig.animation_data_create()
for name,length,fn in clips:
    rig.animation_data.action=None
    act=bpy.data.actions.new(name); act.use_fake_user=True
    rig.animation_data.action=act
    for frame in range(1,length+1):
        scene.frame_set(frame)
        reset(); fn((frame-1)/(length-1))
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
            pb.keyframe_insert('location',frame=frame,group=pb.name)
    act['description']={'Idle':'Looping breathing and cloth sway','Walk':'In-place walk study','Arm_Motion_Test':'Alternating arm movement and recovery; no weapons'}[name]

scene.render.fps=24
rig['status']='Animated assassin study: idle, in-place walk, arm movement test. No weapons.'
if not scene.get('source_base'):
    scene['source_base']='Original procedural prototype; NOT the Eliber Blend Swap mesh.'
scene['clips']='Idle 1-49; Walk 1-25; Arm_Motion_Test 1-37, all at 24 fps'
scene['limitations']='Blocking animation; rigid armour, skinned cloth; not yet validated in Ursina.'

bpy.ops.object.select_all(action='DESELECT')
for obj in parts+[rig]: obj.select_set(True)
bpy.context.view_layer.objects.active=rig
rig.animation_data.action=bpy.data.actions['Idle']
scene.frame_start=1; scene.frame_end=49; scene.frame_set(1)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'assassin_animated.glb'),export_format='GLB',use_selection=True,
    export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_force_sampling=True,
    export_def_bones=True)

# Shareable scene and economical, actual 3D animation renders.
scene.render.engine='CYCLES'; scene.cycles.samples=8; scene.cycles.use_denoising=True
scene.render.resolution_x=480; scene.render.resolution_y=540; scene.render.resolution_percentage=100
scene.camera.data.ortho_scale=2.85
scene.camera.location=(3,-6,3.0)
scene.camera.rotation_euler=(Vector((0,0,1))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
scene.render.filepath=os.path.join(OUT,'preview.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'assassin_animated.blend'))

report={'source_base':scene['source_base'],'bones':len(rig.data.bones),'clips':{n:l for n,l,f in clips}}
# Check the bracer stays rigid in forearm space throughout the motion.
bracer=bpy.data.objects['Vambrace.R']
def centre(obj):
    eo=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return sum((eo.matrix_world@v.co for v in eo.data.vertices),Vector())/len(eo.data.vertices)
for name,length,fn in clips:
    rig.animation_data.action=bpy.data.actions[name]
    coords=[]
    for f in [1,length//3,length//2,length]:
        scene.frame_set(f); bpy.context.view_layer.update()
        coords.append((rig.matrix_world @ rig.pose.bones['forearm.R'].matrix).inverted() @ centre(bracer))
    assert max((p-coords[0]).length for p in coords)<.0001,(name,coords)
report['rigid_armour_attachment']='passed in all 3 clips'
with open(os.path.join(OUT,'validation.json'),'w') as f: json.dump(report,f,indent=2)

for name,length,fn in clips:
    frames_dir=os.path.join(OUT,'frames',name)
    os.makedirs(frames_dir,exist_ok=True)
    rig.animation_data.action=bpy.data.actions[name]
    for f in range(1,length,4 if name=='Idle' else 2):
        scene.frame_set(f)
        scene.render.filepath=os.path.join(frames_dir,'%04d.png'%f)
        bpy.ops.render.render(write_still=True)
print('ANIMATED PROTOTYPE COMPLETE',json.dumps(report))
