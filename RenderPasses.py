import bpy
import operator
from vb30.plugins import PLUGINS_ID


def node_add(nodetree, node, newnodetype):
	newnode = nodetree.nodes.new(type=newnodetype)
	newnode.location.x = node.location.x - 200
	newnode.location.y = node.location.y + 70

	# get linktree
	links = nodetree.links
	# link new node to existing node
	link = links.new(newnode.outputs[0], node.inputs[0])


class RPSettings:

	def getAttrDesc(plugin, attrName):
		for attrDesc in plugin.PluginParams:
			if attrDesc['attr'] == attrName:
				return attrDesc



	RPassCustom = [0,
				   1, 21, 18,
				   2, 15, 14,
				   3, 17, 16,
				   6, 4, 7,
				   11, 23, 24,
				   8, 10, 9,
				   5, 12, 22,
				   20, 19, 25,
				   27, 26, 13,
				   28, 29, 30, 31,
				   32, 33, 34,
				   35, 36, 37, 38, 39, 40, 41, 42]

	RenderPasses = []
	# RenderPasses = [i['items'][:2] for i in PLUGINS_ID['RenderChannelColor'].PluginParams if i['attr'] == 'alias']

	# RenderChannelObjectSelect ?
	RPassOther = ['RenderChannelBumpNormals', 'RenderChannelColorModo', 'RenderChannelCoverage',
				  'RenderChannelDRBucket', 'RenderChannelExtraTex', 'RenderChannelGlossiness',
				  'RenderChannelMultiMatte', 'RenderChannelNodeID', 'RenderChannelNormals',
				  'RenderChannelObjectSelect',
				  'RenderChannelRenderID', 'RenderChannelVelocity', 'RenderChannelZDepth',
				  'RenderChannelDenoiser']

	bval = [False, True, True]

	bicons ={0:['RADIOBUT_OFF','RADIOBUT_ON', 'RADIOBUT_OFF'],
			'RenderChannelExtraTex':['ZOOMIN','RADIOBUT_ON', 'ANTIALIASED']}
	btext = {0:[''],'RenderChannelExtraTex':['ExtraTex','ExtraTex', 'ExtraTex/AO']}

	def passes():

		# clear render passes booleans
		bpy.context.scene.bool = ""

		attrDesc = RPSettings.getAttrDesc(PLUGINS_ID['RenderChannelColor'], 'alias')
		if attrDesc:
			RPSettings.RenderPasses = [i[:2] for i in attrDesc['items']]
			for i in RPSettings.RenderPasses:
				bpy.context.scene.bool += "0"

			#print(RPSettings.RenderPasses)
			# sort by 2.item
			RPSettings.RenderPasses.sort(key=operator.itemgetter(1))

			for i in RPSettings.RPassOther:
				bpy.context.scene.bool += "0"


class ClearPasses(bpy.types.Operator):
	bl_idname = 'clear.passes'
	bl_label = "Clear passes"

	#print ("init ClearPasses")

	def node_create_color_channel(self, node_out, nodetree, RenderPasses):

		color_channel = []
		sizex = [140, 87]
		sizey = [176, 45]

		# create render pass nodes

		for i, passes in enumerate(RenderPasses):
			node = nodetree.nodes.new(type='VRayNodeRenderChannelColor')

			# render pass type
			node.RenderChannelColor.alias = RenderPasses[i][0]

			node.location.x = (i % 4) * sizex[1]
			node.location.y = 700 - (((i % 4 * sizey[1]) / 2.5) + ((int(i / 4) * sizey[1]) * 2))

			node.hide = True
			node.select = False
			# node name to RenderPasses names
			node.name = RPSettings.RenderPasses[i][1]
			# new version of exporter uses this
			node.RenderChannelColor.name = RPSettings.RenderPasses[i][1]
			
			# add input socket
			node_out.inputs.new(name='Channel', type='VRaySocketRenderChannel')
			# set renderpass off
			node_out.inputs[i].use = False
			# add socket name to RenderPasses names
			node_out.inputs[i].name = RPSettings.RenderPasses[i][1]

			# get linktree
			links = nodetree.links
			# link color nodes to Render channel node
			link = links.new(node.outputs[0], node_out.inputs[i])

			color_channel.append(node)

		return

	def node_create_renderid(self, node_out, nodetree, RenderPasses):

		sizex = [140, 87]
		sizey = [176, 45]

		for i, nlist in enumerate(RPSettings.RPassOther):
			name = [nlist][0][13:]
			#print("name:", name)
			nodetype = 'VRayNode' + nlist
			node = nodetree.nodes.new(type=nodetype)
			node.name = name

			node.location.x = (i % 4) * sizex[1]
			node.location.y = -270 - (((i % 4 * sizey[1]) / 2.5) + ((int(i / 4) * sizey[1]) * 2))

			node.hide = True
			node.select = False

			# add input socket
			input = node_out.inputs.new(name='Channel', type='VRaySocketRenderChannel')
			# set renderpass off
			input.use = False
			# add socket name to RenderPasses names
			input.name = name

			# get linktree
			links = nodetree.links
			# link color nodes to Render channel node
			link = links.new(node.outputs[0], input)

			# if it is ExtraTex
			if node.vray_plugin == 'RenderChannelExtraTex':
				# print('RenderChannelExtraTex')
				if not node.inputs[0].links:
					# create textdirt node
					node_add(nodetree, node, 'VRayNodeTexDirt')


		return

	def execute(self, context):

		#print("RenderPasses.ClearPasses.execute")
		for area in bpy.context.screen.areas:
			if area.type == "NODE_EDITOR":
				override = {'screen': bpy.context.screen, 'area': area}

		RPSettings.passes()
		ClearPasses(bpy.context)
		scn = bpy.context.scene
		# clear render passes UI booleans
		# RenderPasses = RenderChannelColor.ColorChannelNamesMenu
		# scn.RPass = [False for x in range(len(RPSettings.RenderPasses))]
		# scn.RPassOther = [False for x in range(len(RPSettings.RPassOther))]

		ng = bpy.data.node_groups
		LName = 'RenderPasses'
		RLayer = ng.new(LName, 'VRayNodeTreeScene') if LName not in ng else ng[LName]
		bpy.context.scene.vray.ntree = RLayer

		# get nodetree
		nodetree = bpy.context.scene.vray.ntree
		nodes = nodetree.nodes
		nodes.clear()
		# create Render Channel node
		node_out = nodes.new('VRayNodeRenderChannels')
		# clear all input sockets
		node_out.inputs.clear()

		node_out.location.x = 600
		node_out.location.y = 800
		node_out.select = False

		self.node_create_color_channel(node_out, nodetree, RPSettings.RenderPasses)
		self.node_create_renderid(node_out, nodetree, RPSettings.RenderPasses)

		# clear Light passes
		scn.prop_group.coll.clear()

		return {'FINISHED'}