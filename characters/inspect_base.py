import bpy, os, json
root=os.path.dirname(os.path.abspath(__file__))
for path,dirs,files in os.walk(os.path.join(root,'Eliber_Rigged_Base_Mesh')):
    for name in files:
        if name.endswith('.blend'):
            bpy.ops.wm.open_mainfile(filepath=os.path.join(path,name),use_scripts=False)
            report=[]
            for o in bpy.data.objects:
                entry={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions)}
                if o.type=='ARMATURE':
                    entry['bones']=[{'name':b.name,'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local),'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in o.data.bones]
                if o.type=='MESH':
                    entry['vertices']=len(o.data.vertices)
                    entry['groups']=[g.name for g in o.vertex_groups]
                    entry['modifiers']=[(m.name,m.type) for m in o.modifiers]
                    entry['bounds']=[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box]
                report.append(entry)
            with open(os.path.join(root,'base_inspection.json'),'w') as f: json.dump({'source':os.path.join(path,name),'objects':report},f,indent=2)
            print(json.dumps(report))
