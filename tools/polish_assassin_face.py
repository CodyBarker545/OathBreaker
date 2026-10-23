import bpy,math,json
from mathutils import Vector
from pathlib import Path
OUT=Path(r'D:\SoftwareEng\Game\SourceAssets\characters\hooded_assassin\face')
rig=bpy.data.objects['Assassin_Skeleton']
col=bpy.data.collections['Character_Assassin']
eyes=bpy.data.materials['Assassin_Grey_Blue_Eyes']
nodes=eyes.node_tree.nodes
links=eyes.node_tree.links
for node in nodes:
    if node.type=='MATH' and node.operation=='SUBTRACT':
        if abs(node.inputs[1].default_value-1.6788)<.0001: node.inputs[1].default_value=1.6705
anchor=bpy.data.objects.new('Assassin_Eye_Shading_Space',None)
col.objects.link(anchor)
anchor.empty_display_size=.01
matrix=anchor.matrix_world.copy()
anchor.parent=rig
anchor.parent_type='BONE'
anchor.parent_bone='head'
anchor.matrix_world=matrix
bpy.context.view_layer.update()
coord=nodes.new('ShaderNodeTexCoord')
coord.object=anchor
sep=next(n for n in nodes if n.type=='SEPXYZ')
links.new(coord.outputs['Object'],sep.inputs[0])
hair=bpy.data.materials['Assassin_Copper_Hair_Cards']
hn=hair.node_tree.nodes
hl=hair.node_tree.links
texture=next(n for n in hn if n.type=='TEX_IMAGE')
colors=hn.new('ShaderNodeValToRGB')
colors.color_ramp.elements[0].position=0
colors.color_ramp.elements[0].color=(.055,.017,.005,1)
colors.color_ramp.elements[1].position=.65
colors.color_ramp.elements[1].color=(.4,.185,.065,1)
hl.new(texture.outputs['Color'],colors.inputs[0])
hl.new(colors.outputs['Color'],hn.get('Principled BSDF').inputs['Base Color'])
for name,color in [('Beard_Copper_Shadow',(.07,.022,.006)),('Beard_Auburn',(.20,.075,.020)),('Beard_Golden_Copper',(.36,.17,.05)),('Beard_Straw_Highlight',(.45,.27,.12))]:
    bpy.data.materials[name].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1)
skin=bpy.data.materials['Assassin_Portrait_Skin']
next(n for n in skin.node_tree.nodes if n.type=='MIX_RGB').inputs[0].default_value=.60
scene=bpy.context.scene
camera=scene.camera
camera.location=(.29,-.94,1.71)
camera.rotation_euler=(Vector((0,-.075,1.669))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.ortho_scale=.38
scene.cycles.samples=12
scene.render.resolution_x=650
scene.render.resolution_y=720
scene.render.filepath=str(OUT/'face_preview.png')
bpy.ops.render.render(write_still=True)
result={'eye_shader_bone_binding':anchor.parent_bone}
