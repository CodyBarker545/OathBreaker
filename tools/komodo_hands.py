"""Human-proportioned clawed hands with three joints per digit and grip controls."""
import bpy, math
from mathutils import Vector

def build_hands(rig, collection, skin, ivory, darkskin, belly):
    created=[]; specs={}; claws=[]; handmeshes=[]
    def sphere(name,pos,scale,mat):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=pos)
        o=bpy.context.object;o.name=name;o.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.data.materials.append(mat)
        return o
    def segment(name,a,b,r1,r2,mat):
        a,b=Vector(a),Vector(b);direction=b-a
        bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r1,radius2=r2,depth=direction.length,location=(a+b)/2)
        o=bpy.context.object;o.name=name;o.rotation_euler=direction.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
        return o
    def curved_claw(name,points,radii):
        vs=[];faces=[];sides=12
        for j,point in enumerate(points):
            t=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized()
            u=t.cross(Vector((1,0,0))).normalized();v=t.cross(u).normalized()
            for k in range(sides):vs.append(Vector(point)+radii[j]*(u*math.cos(k*math.tau/sides)+v*math.sin(k*math.tau/sides)))
        faces.append(tuple(range(sides-1,-1,-1)))
        for j in range(len(points)-1):
            for k in range(sides):faces.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
        faces.append(tuple((len(points)-1)*sides+k for k in range(sides)))
        data=bpy.data.meshes.new(name);data.from_pydata(vs,[],faces);data.update()
        o=bpy.data.objects.new(name,data);collection.objects.link(o);data.materials.append(ivory)
        return o
    for sign,side in [(-1,'R'),(1,'L')]:
        pieces=[sphere('Palm', (sign*.66,-.40,1.085),(.104,.064,.114),skin),
                sphere('Wrist', (sign*.66,-.38,1.16),(.079,.066,.075),skin)]
        chains=[]
        for digit,offset,length in [('Index',-.073,.18),('Middle',-.024,.215),('Ring',.027,.20),('Little',.074,.157)]:
            x=sign*(.66+offset);spread=offset*.13
            p=[Vector((x,-.40,1.018)),Vector((x+sign*spread,-.40,1.018-length*.45)),Vector((x+sign*spread*1.3,-.377,1.018-length*.78)),Vector((x+sign*spread*1.4,-.351,1.018-length))]
            radius=.026 if digit!='Little' else .023
            names=[]
            for j in range(3):
                bn=f'{digit}.{j+1:02d}.{side}';names.append(bn)
                specs[bn]=(p[j],p[j+1],f'Hand.{side}' if j==0 else names[j-1])
                pieces.append(segment('Finger segment',p[j],p[j+1],radius*(1-j*.12),radius*(.9-j*.12),skin))
                pieces.append(sphere('Finger joint',p[j],(radius,radius,radius),skin))
            pieces.append(sphere('Fingertip',p[-1],(radius*.7,)*3,skin))
            tip=p[-1]
            clawpoints=[tip+Vector((0,-.012,.018)),tip+Vector((0,-.009,-.010)),tip+Vector((0,.008,-.046)),tip+Vector((0,.037,-.077))]
            claws.append((curved_claw(f'Long claw • {digit}.{side}',clawpoints,[radius*.70,radius*.57,.009,.001]),names[-1]))
            chains.extend(names)
        # Thumb is lower and rotated out of the finger plane, with a real opposing tip.
        p=[Vector((sign*.586,-.395,1.115)),Vector((sign*.533,-.386,1.065)),Vector((sign*.510,-.350,1.014)),Vector((sign*.537,-.310,.987))]
        names=[]
        pieces.append(sphere('Thenar thumb pad',(sign*.588,-.371,1.075),(.050,.048,.067),skin))
        for j in range(3):
            bn=f'Thumb.{j+1:02d}.{side}';names.append(bn);specs[bn]=(p[j],p[j+1],f'Hand.{side}' if j==0 else names[j-1])
            r=.034-j*.005
            pieces.append(segment('Thumb segment',p[j],p[j+1],r,r*.82,skin));pieces.append(sphere('Thumb joint',p[j],(r,)*3,skin))
        pieces.append(sphere('Thumb tip',p[-1],(.022,)*3,skin));chains.extend(names)
        tip=p[-1]
        claws.append((curved_claw(f'Long claw • Thumb.{side}',[tip,tip+Vector((sign*.016,.010,-.01)),tip+Vector((sign*.034,.023,-.027)),tip+Vector((sign*.047,.040,-.047))],[.019,.016,.009,.001]),names[-1]))
        # Fuse the palm and fingers into a continuous surface before skinning.
        bpy.ops.object.select_all(action='DESELECT')
        for o in pieces:o.select_set(True)
        bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();o=pieces[0];o.name=f'Articulated humanlike claw hand.{side}'
        remesh=o.modifiers.new('Continuous palm and finger topology','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.0045
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        smooth=o.modifiers.new('Organic joint transitions','SMOOTH');smooth.factor=.7;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
        dec=o.modifiers.new('Hand surface reduction','DECIMATE');dec.ratio=.60;bpy.ops.object.modifier_apply(modifier=dec.name)
        handmeshes.append((o,side,chains))
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for name,(head,tail,parent) in specs.items():
        b=rig.data.edit_bones.new(name);b.head=head;b.tail=tail;b.parent=rig.data.edit_bones[parent];b.align_roll(Vector((0,-1,0)))
    bpy.ops.object.mode_set(mode='OBJECT')
    def distance(p,a,b):
        d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-a-t*d).length
    for o,side,chains in handmeshes:
        candidates=[f'Hand.{side}']+chains
        for n in candidates:o.vertex_groups.new(name=n)
        for vertex in o.data.vertices:
            p=o.matrix_world@vertex.co
            candidates_dist=[]
            for n in candidates:
                if n.startswith('Hand.'):
                    a,b=Vector(((-1 if side=='R' else 1)*.66,-.40,1.18)),Vector(((-1 if side=='R' else 1)*.66,-.40,1.04))
                else:a,b,_=specs[n]
                candidates_dist.append((distance(p,a,b),n))
            candidates_dist.sort();near=candidates_dist[:2]
            weights=[1/(d+.008)**4 for d,n in near];total=sum(weights)
            for (d,n),w in zip(near,weights):o.vertex_groups[n].add([vertex.index],w/total,'REPLACE')
        created.append(o)
    for o,bn in claws:
        o.vertex_groups.new(name=bn).add(list(range(len(o.data.vertices))),1,'REPLACE');created.append(o)
    for o in created:
        for old in list(o.users_collection):old.objects.unlink(o)
        collection.objects.link(o)
        for p in o.data.polygons:p.use_smooth=True
        uv=o.data.uv_layers.new(name='Hand UV')
        for polygon in o.data.polygons:
            for li in polygon.loop_indices:
                v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x*2.5+v.y*.3,v.z*2.5)
        mod=o.modifiers.new('Finger articulation','ARMATURE');mod.object=rig;o.parent=rig;o['asset_role']='Character mesh'
    for side in ['R','L']:
        key=f'Grip.{side}';rig[key]=0.0;rig.id_properties_ui(key).update(min=0,max=1,description='Curl fingers around a held object: 0 relaxed, 1 grip')
        for n in specs:
            if not n.endswith('.'+side):continue
            p=rig.pose.bones[n];p.rotation_mode='XYZ'
            driver=p.driver_add('rotation_euler',0).driver;driver.type='SCRIPTED'
            var=driver.variables.new();var.name='grip';var.type='SINGLE_PROP';var.targets[0].id=rig;var.targets[0].data_path=f'["{key}"]'
            sign=1 if rig.data.bones[n].matrix_local.col[0].xyz.x>0 else -1
            angle=.65 if n.startswith('Thumb') else (1.05 if '.02.' in n else .85)
            driver.expression=f'grip*{sign*angle}'
        grip=bpy.data.objects.new(f'WeaponGrip.{side}',None);collection.objects.link(grip);grip.empty_display_type='ARROWS';grip.empty_display_size=.07
        grip.parent=rig;grip.parent_type='BONE';grip.parent_bone=f'Hand.{side}'
        # Bone-parent inverse puts the attachment origin in the middle of the palm.
        bpy.context.view_layer.update();grip.matrix_world.translation=Vector(((-1 if side=='R' else 1)*.66,-.335,1.00))
    return created
