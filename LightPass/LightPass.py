import bpy
import random
from bpy.props import IntProperty, StringProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy.types import PropertyGroup, UIList, Panel, Operator
from __init__ import *
from .. import RenderPasses as RP

# -------------------------------------------------------------------------------
#LIGHT PASS

def LPprops(self, context):
	types = {ob.name: ob for ob in context.scene.objects if ob.type =='LAMP'}
	objlist = []
	types = list(types)
	for o in bpy.data.objects:
		if o.type == 'MESH'and o.vray.ntree:
			nodes = [i for i in o.vray.ntree.nodes if i.vray_plugin == 'LightMesh']
			if nodes:
				types.append(o.name)



	#print ("object is lightmesh",objlist)

	return [(t, t,"") for t in types]

def update_lpprop(self, context):

	renderpass_bool(self, context)
	LightPassUpdate.execute(self, context)

# -------------------------------------------------------------------------------
class LPitems(PropertyGroup):

	type = EnumProperty(
		items=(
			('A', "Object", ""),
			('B', "Group", ""),
		)
	)

	obj = StringProperty(update = update_lpprop)


class LPGroup(PropertyGroup):
	coll = CollectionProperty(type=LPitems)
	index = IntProperty()

# -------------------------------------------------------------------------------

class LightPassUpdate(bpy.types.Operator):
	bl_idname = "lightpass.update"
	bl_label = "Update nodes"

	def execute(self, context):

		#print ("LightPass.Update")
		#print("RPSettings.RenderPasses:",RP.RPSettings.RenderPasses)

		sce = bpy.context.scene
		# get nodetree
		nodetree = bpy.data.node_groups['RenderPasses']
		nodes = nodetree.nodes
		# get linktree
		links = nodetree.links
		#find RenderChannel node
		node_out = [x for x in nodetree.nodes if x.bl_idname == 'VRayNodeRenderChannels']
		if node_out:
			node_out = node_out[0]
		else:
			print ("No RenderChannelNode found")
			return

		#node_out   = Channel container node
		#node       = Object select node
		#nodeLight  = Light select node

		#first delete light pass input sockets
		#index = len(sce.RPass) + len(sce.RPassOther)
		index = len(sce.bool)
		#print ("index = len(RPSettings.RenderPasses):", index)
		indexmax = len(node_out.inputs)
		if indexmax > index:

			for i in range(0, indexmax - index):
				node_out.inputs.remove(node_out.inputs[-1])

		#delete also light pass nodes
		nodes_lightpass = [x for x in nodetree.nodes if x.bl_idname in ('VRayNodeRenderChannelLightSelect','VRayNodeSelectObject','VRayNodeSelectGroup')]
		#print ("Light pass nodes to delete:", nodes_lightpass)
		for i in nodes_lightpass:
			nodetree.nodes.remove(i)

		#add light passes
		for x, i in enumerate(sce.prop_group.coll):

			nodeLight = nodes.new('VRayNodeRenderChannelLightSelect')
			nodeLight.RenderChannelLightSelect.name = 'Light ' + i.obj

			#object select/group select
			if i.type =='A':
				# create Object Select node
				node = nodes.new('VRayNodeSelectObject')
				node.objectName = i.obj
			else:
				# create Group Select node
				node = nodes.new('VRayNodeSelectGroup')
				node.groupName = i.obj

			# add input socket
			input = node_out.inputs.new(name='Channel', type='VRaySocketRenderChannel')
			input.name = "Lightpass " + i.obj

			node.location.x = -100
			node.location.y = -600 - x * 200
			nodeLight.location.x = 100
			nodeLight.location.y = -600 - x * 200
			#node_out.select = False

			# link ObjectNode to Render channel node
			l = node_out.inputs
			link = links.new(nodeLight.outputs[0], input)
			link = links.new(node.outputs[0], nodeLight.inputs[0])


		return {'FINISHED'}
# -------------------------------------------------------------------------------


class LightPassAdd(bpy.types.Operator):
	bl_idname = "lightpass.add"
	bl_label = "Add light pass"

	def execute(self, context):

		item = context.scene.prop_group.coll.add()
		item.type = 'A'
		context.scene.prop_group.index += 1

		return {'FINISHED'}
# -------------------------------------------------------------------------------

class LightPassDelete(bpy.types.Operator):
	'''Delete light pass'''
	bl_idname = "lightpass.delete"
	bl_label = "Delete Light pass"

	delindex = IntProperty()

	def execute(self, context):
		sce = context.scene
		sce.prop_group.coll.remove(self.delindex)
		sce.prop_group.index = 0

		renderpass_bool(self, context)
		LightPassUpdate.execute(self, context)


		return {'FINISHED'}

# UI -------------------------------------------------------------------------------

class SCENE_UL_list(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname,index):

		if self.layout_type in {'DEFAULT', 'COMPACT'}:
			#print ("index", index)
			split = layout.split(percentage = 0.2, align=False)
			split.enabled = layout.enabled = context.scene.RPassSwitch


			split.label(str(index+1))
			#layout.prop(item, "name", text="", emboss=True)
			#layout.prop(item, "val", text="")

			if item.type == 'A':
				split.prop_search(item, "obj", context.scene, "objects", text = "")
				pass
			else:
				split.prop_search(item, "obj", bpy.data, "groups", text = "")

			layout.prop(item, "type", text="", emboss = True)
			layout.operator('lightpass.delete', text ='', icon = 'X').delindex = index

		elif self.layout_type in {'GRID'}:
			layout.alignment = 'CENTER'
			layout.label(text="", icon_value=icon)


#-----------------------------------------------------------------------------

def renderpass_bool(self, context):
	scn = context.scene

	nodeout = scn.vray.ntree.nodes.get('Render Channles Container')
	RenderPasses = RP.RPSettings.RenderPasses

	for i in range(len(scn.bool)):
		nodeout.inputs[i].use = RP.RPSettings.bval[int(scn.bool[i])]

	# update nodeout
	nodeout.location.x = nodeout.location.x

# REGISTER -------------------------------------------------------------------
