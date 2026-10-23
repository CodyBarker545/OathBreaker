"""Build ONLY the reference left pauldron. Keep the source character scene intact.

Run in Blender: blender --background --python tools/model_left_pauldron.py
Or execute this source through the installed Blender MCP bridge.
"""
from pathlib import Path
import bpy, bmesh, math, json, hashlib
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

ROOT = Path(r'D:\SoftwareEng\Game')
SOURCE = ROOT / 'SourceAssets/characters/hooded_assassin/outfit/assassin_concept_v005.blend'
OUT = ROOT / 'SourceAssets/characters/hooded_assassin/modular/left_pauldron'
OUT.mkdir(parents=True, exist_ok=True)


def geometry_hash(obj):
    payload = ([list(v.co) for v in obj.data.vertices], [list(p.vertices) for p in obj.data.polygons])
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


class LeftPauldron:
    """Curved, closed-thickness lames with solid raised perimeter bands."""

    ANGLES = [-.32, -.09, .19, .47, .74, 1.01, 1.29, 1.57, 1.85, 2.13, 2.40, 2.68, 2.96, 3.19, 3.46]
    ROWS = [0, .28, .64, 1]
    # Inner edge, outer edge, radius at the four longitudinal rows.
    LAYERS = [
        ('01_Crown', .151, .279, [.098, .116, .113, .111], .030),
        ('02_Upper_Lame', .246, .331, [.084, .094, .094, .093], .023),
        ('03_Middle_Lame', .306, .378, [.073, .080, .080, .079], .022),
        ('04_Lower_Lame', .357, .414, [.062, .067, .067, .066], .019),
    ]

    def __init__(self, scene, body, rig):
        self.scene, self.body, self.rig = scene, body, rig
        self.collection = bpy.data.collections.new('Equipment_Left_Pauldron')
        scene.collection.children.link(self.collection)
        self.origin = rig.data.bones['upperarm_l'].head_local.copy()
        self.root = bpy.data.objects.new('ASM_Left_Shoulder_Pauldron', None)
        self.collection.objects.link(self.root)
        self.root.location = self.origin
        self.root.empty_display_type = 'PLAIN_AXES'
        self.root.empty_display_size = .04
        self.root['component'] = 'Left shoulder pauldron only'
        self.root['rig_status'] = 'Static fitted component; not rigged or animation-tested'
        self.root['suggested_future_bone'] = 'upperarm_l'
        bpy.context.view_layer.update()
        self.parts, self.plates = [], []
        self.thickness = .004
        self.body_tree = self.make_body_tree(body)
        self.steel = self.copy_material('GC_Painted_Blackened_Steel', 'PAULDRON_L_Worn_Black_Steel', .56, .60)
        self.bronze = self.copy_material('GC_Tarnished_Bronze_Gold', 'PAULDRON_L_Aged_Bronze_Trim', .62, .52)
        self.leather = self.copy_material('GC_Brown_Strap_Leather', 'PAULDRON_L_Internal_Leather_Padding', 0, .86)

    @staticmethod
    def copy_material(source, name, metallic, roughness):
        material = bpy.data.materials[source].copy()
        material.name = name
        shader = material.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
        return material

    @staticmethod
    def make_body_tree(body):
        group = body.vertex_groups['body'].index
        indices = {v.index for v in body.data.vertices if any(g.group == group and g.weight > .5 for g in v.groups)}
        faces = [tuple(p.vertices) for p in body.data.polygons if all(i in indices for i in p.vertices)]
        return BVHTree.FromPolygons([body.matrix_world @ v.co for v in body.data.vertices], faces)

    def axis(self, x):
        return Vector((x, self.origin.y, self.origin.z))

    def radial(self, angle):
        return Vector((0, -math.cos(angle), math.sin(angle)))

    def body_radius(self, x, angle):
        direction = self.radial(angle)
        hit, normal, index, distance = self.body_tree.ray_cast(self.axis(x) + direction * .35, -direction, .35)
        return (hit - self.axis(x)).dot(direction) if hit is not None else .045

    @staticmethod
    def interpolate(values, stops, t):
        for a, b, va, vb in zip(stops, stops[1:], values, values[1:]):
            if a <= t <= b:
                f = (t-a)/(b-a)
                return va*(1-f)+vb*f
        return values[0] if t < stops[0] else values[-1]

    def surface(self, spec, u, v):
        name, inner, outer, radii, tip = spec
        angle = self.ANGLES[0] + v*(self.ANGLES[-1]-self.ANGLES[0])
        # Two pointed scallops in each outer edge; the arch remains a curved metal sheet.
        points=[1.35,.72,.22,.90,.48,.12,0,.04,0,.12,.48,.90,.22,.72,1.35]
        point=self.interpolate(points,self.ANGLES,angle)
        inside_sweep=.024*(1-math.sin(angle))
        x = inner + inside_sweep*(1-u) + (outer-inner)*u + tip*point*u**3
        radius = self.interpolate(radii, self.ROWS, u)
        ridge=max(0,1-abs(angle-.74)/.40)+max(0,1-abs(angle-2.40)/.40)
        ridge_scale={'01_Crown':1.,'02_Upper_Lame':.60,'03_Middle_Lame':.40,'04_Lower_Lame':.25}[name]
        radius += .008*ridge_scale*math.sin(math.pi*u)*ridge
        radius = max(radius, self.body_radius(x, angle)+.011)
        normal = self.radial(angle)
        return self.axis(x)+normal*radius, normal

    def mesh(self, name, world_vertices, faces, material, uv_coords=None, bevel=0, smooth=False):
        data = bpy.data.meshes.new(name+'_Mesh')
        data.from_pydata([Vector(p)-self.origin for p in world_vertices], [], faces)
        data.update()
        bm = bmesh.new(); bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if sum(f.calc_area() for f in bm.faces) and bm.calc_volume(signed=True) < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(data); bm.free()
        obj = bpy.data.objects.new('L_Pauldron_'+name, data)
        self.collection.objects.link(obj)
        obj.parent = self.root
        data.materials.append(material)
        uv = data.uv_layers.new(name='Pauldron_Painted_UV')
        for face in data.polygons:
            face.use_smooth = smooth
            for li in face.loop_indices:
                i = data.loops[li].vertex_index
                p = world_vertices[i]
                uv.data[li].uv = uv_coords[i] if uv_coords else (p[0]*5, p[2]*5)
        if bevel:
            mod = obj.modifiers.new('Editable_Forged_Edge_Bevel', 'BEVEL')
            mod.width = bevel; mod.segments = 1
            mod.limit_method = 'ANGLE'; mod.angle_limit = math.radians(28)
        obj['component'] = 'Left shoulder pauldron'
        obj['source_reference'] = 'Dark Fantasy Assassin Blueprint Sheet.png / shoulder close-up'
        self.parts.append(obj)
        return obj

    def build_plate(self, spec):
        name = spec[0]; ns = len(self.ANGLES); nr = len(self.ROWS)
        vs, uvs = [], []
        for inner_surface in [False, True]:
            for u in self.ROWS:
                for angle in self.ANGLES:
                    v = (angle-self.ANGLES[0])/(self.ANGLES[-1]-self.ANGLES[0])
                    p, normal = self.surface(spec, u, v)
                    vs.append(p-normal*self.thickness if inner_surface else p)
                    uvs.append((v, u))
        half = ns*nr; faces = []
        for i in range(nr-1):
            for j in range(ns-1):
                a=i*ns+j; b=a+1; c=a+ns+1; d=a+ns
                faces += [(a,b,c,d), (d+half,c+half,b+half,a+half)]
        border = list(range(ns)) + [i*ns+ns-1 for i in range(1,nr)] + list(range((nr-1)*ns+ns-2,(nr-1)*ns-1,-1)) + [i*ns for i in range(nr-2,0,-1)]
        for a,b in zip(border,border[1:]+border[:1]):faces.append((a,a+half,b+half,b))
        obj=self.mesh(name+'_Steel_Plate',vs,faces,self.steel,uvs,.00085,False)
        obj['actual_shell_thickness_m']=self.thickness
        self.plates.append(obj)
        self.build_trim(spec,border,ns)
        return obj

    def build_trim(self,spec,border,ns):
        vs=[];uv=[]
        for index in border:
            row,col=divmod(index,ns)
            u=self.ROWS[row];v=(self.ANGLES[col]-self.ANGLES[0])/(self.ANGLES[-1]-self.ANGLES[0])
            inset_u=min(.08,.0035/(spec[2]-spec[1]));inset_v=.011
            inward_u=min(1-inset_u,max(inset_u,u));inward_v=min(1-inset_v,max(inset_v,v))
            edge,n=self.surface(spec,u,v);inside,ni=self.surface(spec,inward_u,inward_v)
            vs.extend([edge+n*.0017,inside+ni*.0017,inside+ni*.0001,edge+n*.0001])
            uv.extend([(0,index/len(border)),(1,index/len(border)),(1,index/len(border)),(0,index/len(border))])
        faces=[]
        for i in range(len(border)):
            j=(i+1)%len(border)
            for k in range(4):faces.append((4*i+k,4*i+(k+1)%4,4*j+(k+1)%4,4*j+k))
        self.mesh(spec[0]+'_Raised_Bronze_Edge_Band',vs,faces,self.bronze,uv,.0004)

    def stud(self,name,p,normal,radius=.0034):
        normal=Vector(normal).normalized();u=normal.cross(Vector((1,0,0))).normalized();v=normal.cross(u)
        vs=[]
        for height in [0,.0022]:
            for j in range(8):vs.append(p+normal*height+u*math.cos(j*math.tau/8)*radius+v*math.sin(j*math.tau/8)*radius)
        faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
        return self.mesh(name,vs,faces,self.bronze,bevel=.00035)

    def spine(self,name,spec,u,v,height):
        p,n=self.surface(spec,u,v)
        ux=Vector((1,0,0));across=ux.cross(n).normalized()
        vs=[p-ux*.017-across*.008,p+ux*.019-across*.008,p+ux*.019+across*.008,p-ux*.017+across*.008,p+ux*.026+n*height-across*.003]
        self.mesh(name,vs,[(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],self.steel,bevel=.00055)
        # A narrow bronze leading ridge belongs to the same fin, rather than a separate equipment item.
        for edge in [(0,4),(1,4)]:
            a,b=[vs[i] for i in edge];d=(b-a).normalized();side=d.cross(across).normalized()*.0010
            self.mesh(name+'_Bronze_Ridge', [a-side,a+side,b+side,b-side,a-side+across*.001,a+side+across*.001,b+side+across*.001,b-side+across*.001],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],self.bronze)

    def padding(self):
        vs=[];faces=[];ns=19;nr=8
        for inside in [False,True]:
            for i in range(nr):
                x=.17+i/(nr-1)*.245
                for j in range(ns):
                    a=-.25+j/(ns-1)*3.65;n=self.radial(a)
                    vs.append(self.axis(x)+n*(self.body_radius(x,a)+(.003 if inside else .008)))
        half=ns*nr
        for i in range(nr-1):
            for j in range(ns-1):
                a=i*ns+j;faces.extend([(a,a+1,a+1+ns,a+ns),(a+half+ns,a+half+ns+1,a+half+1,a+half)])
        border=list(range(ns))+[i*ns+ns-1 for i in range(1,nr)]+list(range(nr*ns-2,(nr-1)*ns-1,-1))+[i*ns for i in range(nr-2,0,-1)]
        for a,b in zip(border,border[1:]+border[:1]):faces.append((a,b,b+half,a+half))
        self.mesh('Internal_Leather_Suspension_Pad',vs,faces,self.leather,smooth=True)

    def suspension_strips(self):
        """Physical internal connections between the independent overlapping lames."""
        for label,v in [('Front',.10),('Rear',.90)]:
            points=[];normals=[]
            angle=self.ANGLES[0]+v*(self.ANGLES[-1]-self.ANGLES[0])
            across=Vector((0,math.sin(angle),math.cos(angle)))
            for spec in self.LAYERS:
                for u in [.25,.72]:
                    p,n=self.surface(spec,u,v);points.append(p);normals.append(n)
            vs=[]
            for p,n in zip(points,normals):
                vs.extend([p-across*.006-n*.0032,p+across*.006-n*.0032,p+across*.006-n*.0065,p-across*.006-n*.0065])
            faces=[(3,2,1,0)]
            for i in range(len(points)-1):
                for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
            faces.append(tuple(4*(len(points)-1)+j for j in range(4)))
            self.mesh('Internal_'+label+'_Articulation_Strap',vs,faces,self.leather,smooth=True)
            for spec in self.LAYERS:
                p,n=self.surface(spec,.69,v);ux=Vector((1,0,0));t=n.cross(ux).normalized();vertices=[]
                for depth in [-.008,.001]:
                    for j in range(6):vertices.append(p+n*depth+ux*math.cos(j*math.tau/6)*.0014+t*math.sin(j*math.tau/6)*.0014)
                fs=[tuple(reversed(range(6))),tuple(range(6,12))]+[(j,(j+1)%6,(j+1)%6+6,j+6) for j in range(6)]
                self.mesh(spec[0]+'_'+label+'_Fastener_Shank',vertices,fs,self.bronze)

    def build(self):
        self.padding()
        for spec in self.LAYERS:
            self.build_plate(spec)
            for v in [.10,.90]:
                p,n=self.surface(spec,.69,v)
                self.stud(spec[0]+'_Bronze_Fastener',p+n*.0007,n)
        self.spine('Crown_Angular_Thorn_Front',self.LAYERS[0],.44,.32,.038)
        self.spine('Crown_Angular_Thorn_Rear',self.LAYERS[0],.52,.70,.029)
        self.suspension_strips()

    def validate(self):
        report={'component':'Left shoulder pauldron only','assembly_meshes':len(self.parts),'steel_lames':len(self.plates),'shell_thickness_m':self.thickness,'rigged':False,'animation_ready_claim':False,'nonmanifold_source_edges':{},'zero_area_source_faces':{},'minimum_plate_to_body_signed_distance_m':1.0}
        for obj in self.parts:
            bm=bmesh.new();bm.from_mesh(obj.data)
            nonmanifold=sum(not e.is_manifold for e in bm.edges);zero=sum(f.calc_area()<1e-12 for f in bm.faces)
            if nonmanifold:report['nonmanifold_source_edges'][obj.name]=nonmanifold
            if zero:report['zero_area_source_faces'][obj.name]=zero
            assert bm.calc_volume(signed=True)>0,obj.name
            bm.free()
        for obj in self.plates:
            for v in obj.data.vertices:
                p=obj.matrix_world@v.co;nearest,normal,index,d=self.body_tree.find_nearest(p)
                signed=(p-nearest).dot(normal)
                report['minimum_plate_to_body_signed_distance_m']=min(report['minimum_plate_to_body_signed_distance_m'],signed)
        assert not report['nonmanifold_source_edges']
        assert not report['zero_area_source_faces']
        assert report['minimum_plate_to_body_signed_distance_m']>.002
        crossings=[]
        for i,left in enumerate(self.plates):
            for right in self.plates[i+1:]:
                for a,b in [(left,right),(right,left)]:
                    points=[b.matrix_world@v.co for v in b.data.vertices]
                    tree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in b.data.polygons])
                    for edge in a.data.edges:
                        p,q=[a.matrix_world@a.data.vertices[j].co for j in edge.vertices];delta=q-p
                        if delta.length<1e-7:continue
                        hit,normal,index,d=tree.ray_cast(p+delta.normalized()*1e-6,delta.normalized(),max(0,delta.length-2e-6))
                        if hit is not None:crossings.append((a.name,b.name,edge.index))
        report['steel_plate_edge_intersections']=len(crossings)
        assert not crossings,crossings[:8]
        dg=bpy.context.evaluated_depsgraph_get();triangles=0
        for obj in self.parts:
            ev=obj.evaluated_get(dg);data=ev.to_mesh();triangles+=sum(len(p.vertices)-2 for p in data.polygons);ev.to_mesh_clear()
        report['evaluated_triangles']=triangles
        report['source_triangles']=sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in self.parts)
        report['all_parts_have_uvs']=all(obj.data.uv_layers for obj in self.parts)
        report['normals_outward_and_closed']=True
        report['limitations']=['Static neutral-pose fit; no skinning or shoulder-motion test yet.','Plate overlaps are intentional; articulation and extreme-pose clearance require an approved rigging pass.','Silhouette interpreted for the existing horizontal T-pose; source art mostly shows lowered arms.']
        return report


def create_review_scene(original):
    scene=bpy.data.scenes.new('REVIEW_Left_Pauldron_Only')
    base=bpy.data.collections.new('Base_Character_Unchanged_References');scene.collection.children.link(base)
    names=['Assassin_Body','Assassin_Eyes','Assassin_Eye_Shading_Space','Assassin_Skeleton','Tunic_Black_Fitted_Long_Sleeves','Trousers_Black_Armored_Underlayer','Glove_L_Full_Finger_Leather','Glove_R_Full_Finger_Leather','Boot_L_Fitted_Leather_Upper','Boot_R_Fitted_Leather_Upper']
    for name in names:
        obj=bpy.data.objects.get(name)
        if obj:base.objects.link(obj)
    bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene.world=bpy.data.worlds.new('Pauldron_Review_World');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.20,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
    studio=bpy.data.collections.new('Pauldron_Review_Studio');scene.collection.children.link(studio)
    for name,position,power,size in [('Key',(.0,-1.0,2.5),65,1.0),('Fill',(.8,.4,2.0),38,.8),('Rim',(-.4,.5,1.8),65,.65)]:
        data=bpy.data.lights.new('Pauldron_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        obj=bpy.data.objects.new('Pauldron_'+name,data);studio.objects.link(obj);obj.location=position
        obj.rotation_euler=(Vector((.28,0,1.52))-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Pauldron_Review_Camera');camera=bpy.data.objects.new('Pauldron_Review_Camera',data);studio.objects.link(camera)
    data.type='ORTHO';data.ortho_scale=.43;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=40
    scene.render.resolution_x=1300;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    return scene


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    original=bpy.context.scene;body=bpy.data.objects['Assassin_Body'];rig=bpy.data.objects['Assassin_Skeleton']
    body_hash=geometry_hash(body)
    skeleton={b.name:(tuple(b.head_local),tuple(b.tail_local),b.parent.name if b.parent else None) for b in rig.data.bones}
    poses={b.name:[list(row) for row in b.matrix_basis] for b in rig.pose.bones}
    existing_meshes={o.name:geometry_hash(o) for o in original.objects if o.type=='MESH'}
    review=create_review_scene(original)
    assembly=LeftPauldron(review,body,rig);assembly.build();bpy.context.view_layer.update()
    report=assembly.validate()
    assert body_hash==geometry_hash(body)
    assert skeleton=={b.name:(tuple(b.head_local),tuple(b.tail_local),b.parent.name if b.parent else None) for b in rig.data.bones}
    assert poses=={b.name:[list(row) for row in b.matrix_basis] for b in rig.pose.bones}
    assert all(geometry_hash(bpy.data.objects[n])==h for n,h in existing_meshes.items())
    report.update(base_body_unchanged=True,existing_equipment_geometry_unchanged=True,skeleton_unchanged=True,t_pose_unchanged=True,original_scene_preserved=original.name,active_review_scene=review.name)
    versions=[int(p.stem.rsplit('_v',1)[-1]) for p in OUT.glob('assassin_left_pauldron_v[0-9][0-9][0-9].blend')]
    version=max(versions,default=0)+1;stem=f'assassin_left_pauldron_v{version:03d}'
    dest=OUT/(stem+'.blend');report['file']=str(dest)
    (OUT/(stem+'_validation.json')).write_text(json.dumps(report,indent=2))
    camera=review.camera;target=Vector((.285,-.008,1.515))
    views=[('front',(.285,-1.1,1.54)),('side',(1.35,-.008,1.76)),('three_quarter',(.83,-.86,1.96))]
    for label,position in views:
        camera.location=position;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        review.render.filepath=str(OUT/(stem+'_'+label+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
    bpy.ops.object.select_all(action='DESELECT');assembly.root.select_set(True);bpy.context.view_layer.objects.active=assembly.root
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.region_3d.view_location=target;space.region_3d.view_distance=.6;space.shading.type='MATERIAL'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    return report


result=main()
