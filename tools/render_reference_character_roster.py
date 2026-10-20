"""Render an uncluttered front lineup of the four exported game assets."""
import bpy,os,math
from mathutils import Vector
ROOT=r'D:\SoftwareEng\Game';CHAR=os.path.join(ROOT,'SourceAssets','characters')
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
assets=[('forsaken_sister','FORSAKEN SISTER'),('masked_ninja','MASKED NINJA'),('broken_oath_knight','BROKEN OATH KNIGHT'),('ash_scholar','ASH SCHOLAR')]
positions=[-2.40,-.80,.80,2.40]
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9;return m
floor=material('Roster charcoal',(.025,.032,.041));label=material('Roster ivory lettering',(.63,.64,.61))
for (slug,title),x in zip(assets,positions):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=os.path.join(CHAR,slug,slug+'.glb'));new=[o for o in bpy.data.objects if o not in before]
 for o in list(new):
  if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):bpy.data.objects.remove(o,do_unlink=True);new.remove(o)
 for o in new:
  if o.parent is None:o.location.x+=x
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.72,depth=.055,location=(x,0,-.035));bpy.context.object.data.materials.append(floor)
 data=bpy.data.curves.new(title,'FONT');data.body=title;data.align_x='CENTER';data.size=.108;data.extrude=.0003;o=bpy.data.objects.new(title,data);scene.collection.objects.link(o);o.location=(x,-.73,-.075);o.rotation_euler=(math.pi/2,0,0);data.materials.append(label)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.084));bpy.context.object.data.materials.append(floor)
for name,pos,power,color,size in [('key',(-4,-5,7),1000,(1,.91,.80),7),('fill',(5,-3,4),650,(.73,.84,1),5),('rim',(1,4,5),1100,(.92,.96,1),6)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Roster studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.18,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.camera_add(location=(0,-12,4.0));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.00))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=7.35;scene.camera=cam
scene.frame_set(1);scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX'
scene.render.resolution_x=2400;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(ROOT,'artifacts','new_character_roster.png');bpy.ops.render.render(write_still=True)
print('ROSTER_PREVIEW_COMPLETE')
