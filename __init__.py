bl_info = {
	"name": "Vray Render Passes",
	"author": "JuhaW",
	"version": (0, 1, 1),
	"blender": (2, 77, 0),
	"location": "Tools",
	"description": "Easier render/light passes, for exporter vb35",
	"warning": "beta",
	"wiki_url": "",
	"category": "",
}
# --------------------------------------------------------------------------
import importlib

if "LP" in locals():
	importlib.reload(RP)
	importlib.reload(LP)
	print("Reload:", LP)

import bpy  # , vb30
import operator
from vb30.plugins import PLUGINS_ID
from bpy.props import IntProperty, IntVectorProperty, StringProperty, BoolProperty, PointerProperty, BoolVectorProperty
from bpy.types import PropertyGroup
from . import RenderPasses as RP
from . LightPass import LightPass as LP
# --------------------------------------------------------------------------


def update_NodeDefaults(self, context):
	# print ('NodeDefaults update')
	# UpdateNodes.execute(self,context)
	color_mapping = ['Diffuse',
	                 'Specular',
	                 'Reflection Filter',
	                 'Refraction Filter',
	                 'Background']

	nodes = bpy.data.node_groups['RenderPasses'].nodes
	# set node colormapping
	colorbool = False if bpy.context.scene.NodeDefaults else True
	for i in nodes:
		if i.name in color_mapping:
			# print("passes colormapping:", i.name)
			i.RenderChannelColor.color_mapping = colorbool


def update_prop_group(self, context):
	# print("prop update:")
	pass


class Test(bpy.types.Operator):
	bl_idname = 'test.operator'
	bl_label = "Test operator"

	boolvar = IntProperty()


	def execute(self, context):
		# print(self.boolvar)

		# select node
		nodetree = bpy.data.node_groups['RenderPasses']
		nodes = nodetree.nodes
		nodeout = nodes.get('Render Channles Container')

		node = nodeout.inputs[self.boolvar].links[0].from_node
		for i in nodes:
			i.select = False
			if i != nodeout:
				i.hide = True

		node.select = True
		node.hide = False
		nodes.active = node
		if node.inputs and node.inputs[0].links:
			node.inputs[0].links[0].from_node.hide = False

		# reverse bool value
		b = context.scene.bool
		context.scene.bool = b[:self.boolvar] + str(int(b[self.boolvar]) ^ 1) + b[self.boolvar + 1:]

		UpdateNodes.execute(self, context)

		return {'FINISHED'}


class SettingsOperator(bpy.types.Operator):
	bl_idname = 'settings.operator'
	bl_label = "Test operator"


	def execute(self, context):
		Var.settings = not Var.settings
		#print (self.boolvar)

		return {'FINISHED'}


class Var():

	settings = BoolProperty(default = True)
	settings = True



class RenderPassPanel(bpy.types.Panel):
	"""Creates a Panel in the Tools panel"""
	bl_label = "Vray Render Passes"
	bl_idname = "renderpass.panel"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "render_layer"


	def draw(self, context):

		layout = self.layout
		sce = context.scene
		row = layout.row()

		row.operator('settings.operator', text="Settings", icon='VRAY_LOGO' if Var.settings else 'VRAY_LOGO_MONO' , emboss=True)
		#VRAY_LOGO, VRAY_LOGO_MONO,SCRIPTPLUGINS
		if Var.settings:
			box = layout.box()
			row = box.row()

			row.operator('clear.passes')
			row.prop(sce, "RPassSwitch", text="Passes on")
			# row = layout.row()
			row.prop(sce, "NodeDefaults", text="Default")
			row.prop(sce, "RenderPassColumns", text="2/3 Columns")

		col = layout.column_flow(columns=3 if sce.RenderPassColumns else 2, align=True)
		col.enabled = sce.RPassSwitch

		# RenderPasses = bpy.data.objects[V.name].constraints
		RenderPasses = RP.RPSettings.RenderPasses
		# RenderPasses = RenderChannelColor.ColorChannelNamesMenu
		# col.alert = False

		if sce.bool != None and RenderPasses:
			# o = bpy.data.objects[V.name]

			icon_on = 'RADIOBUT_ON'
			icon_off = 'RADIOBUT_OFF'

			for i in range(len(sce.bool)):

				bo = int(context.scene.bool[i])
				b = RP.RPSettings.bval[bo]

				if i < len(RenderPasses):
					bool = col.operator('test.operator', text=str(RenderPasses[i][1]),emboss=b,	icon=icon_on if b else icon_off)
					bool.boolvar = i
				else:
					diff = i - len(RenderPasses)
					bool = col.operator('test.operator', text=RP.RPSettings.RPassOther[diff][13:], emboss=b,icon=icon_on if b else icon_off)
					bool.boolvar = i

		# LIGHT PASS
		layout = self.layout
		sce = context.scene
		row = layout.row()
		row.enabled = sce.RPassSwitch
		row.operator("lightpass.add", icon='OUTLINER_OB_LAMP')
		# row.operator("lightpass.update")
		# layout.template_list("SCENE_UL_list", "", sce.prop_group, "coll", sce.prop_group, "index","", sce.prop_group.index)
		layout.template_list("SCENE_UL_list", "", sce.prop_group, "coll", sce.prop_group, "index", "",
			sce.prop_group.index)


class RenderPassGroup(bpy.types.PropertyGroup):
	juha = bpy.props.IntProperty()


def renderpass_onoff(self, context):
	scn = bpy.context.scene
	nodeout = scn.vray.ntree.nodes.get('Render Channles Container')
	RenderPasses = RP.RPSettings.RenderPasses

	pass_amount = len(context.scene.bool)
	# normal render passes
	for i in range(pass_amount):
		if scn.RPassSwitch:
			nodeout.inputs[i].use = int(context.scene.bool[i])
		else:
			nodeout.inputs[i].use = False

	# Light passes
	for i, passes in enumerate(scn.prop_group.coll):
		if scn.RPassSwitch:
			nodeout.inputs[i + pass_amount].use = True
		else:
			nodeout.inputs[i + pass_amount].use = False
		# print("light passes:", len(scn.prop_group.coll))


class UpdateNodes(bpy.types.Operator):
	bl_idname = 'update.nodes'
	bl_label = "Update nodes"

	def execute(self, context):
		LP.renderpass_bool(self, context)
		LP.LightPassUpdate.execute(self, context)

		return {'FINISHED'}


def register():
	bpy.utils.register_module(__name__)

	bpy.types.Scene.RPassSwitch = BoolProperty(default=True, update=renderpass_onoff)
	bpy.types.Scene.NodeDefaults = BoolProperty(default=False, update=update_NodeDefaults,description = "Default On: All render pass nodes are with default values \nDefault Off: Set color mapping On for Diffuse,Specular,Reflection filter,Refraction filter and Background passes, for combining render passes,")

	# LP
	bpy.types.Scene.prop_group = PointerProperty(type=LP.LPGroup, update=update_prop_group)

	bpy.types.Scene.bool = StringProperty()
	bpy.types.Scene.RenderPassColumns = BoolProperty(default=True)


def unregister():
	bpy.utils.unregister_module(__name__)

	del bpy.types.Scene.RPassSwitch
	del bpy.types.Scene.NodeDefaults
	del bpy.types.Scene.bool
	# LP
	bpy.types.Scene.prop_group

	del bpy.types.Scene.RenderPassColumns
	print("unregister Vray Passes addon")
