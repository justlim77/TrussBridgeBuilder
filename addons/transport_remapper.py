"""Script for remapping transports"""

import viz
import vizconnect


def getTransportNodeData(node):
	"""Returns the transport node's data, None if not found."""
	# get the data from the transport parser
	parser = vizconnect.code.Transport()
	dataDict = {}
	filename = node.getConfiguration().getFilename()
	try:
		with open(filename, 'r') as tempFile:
			fullCode = tempFile.read()
			parser.parse(fullCode, dataDict, {})
	except IOError, e:
		viz.logError('** ERROR: Failed to load file {} for parsing.\n{}'.format(filename, e))
	return vizconnect.getData(dataDict, ['transport', 'node', node.getName()])


def generateModifiedMappingCode(classification, mapping, newSlotName):
	"""Returns the modified mapping code."""
	argString = mapping.generateArgString()
	signalCode = mapping.generateSignalCode()
	metaCode = mapping.generateMetaCode()
	signalCode = """{0}# {1}""".format(signalCode, metaCode)
	return vizconnect.code._trimdent("""
if {0}
	{1}.{2}({3})
""".format(signalCode,
			classification,
			newSlotName,
			argString), 1)


def remapTransport(srcTransportWrapper, dstTransportRaw, triggeredFunctionMappings, mode='', modeList=None):
	"""Remaps the transport. Takes in a mapping of functions from a given transport
	and applies them to another transport.
	
	triggeredFunctionMappings e.g. 
	triggeredFunctionMappings = {
			'moveForward':'tiltForward',
			'moveBackward':'tiltBackward',
			'moveUp':'moveUp',
			'moveDown':'moveDown',
			'moveLeft':'tiltLeft',
			'moveRight':'tiltRight',
			'turnLeft':'rotateLeft',
			'turnRight':'rotateRight'
		}
	
	There are two ways to set mode:
	1.) via the mode parameter, which requires all inputs mapped to this transport
	be in the specified mode.
	
	2.) using the mode list to specify per input device modes.
	modeList is a list of tuples of the form (INPUT_NAME, INPUT_MODE). Signals
	which are for INPUT_NAME will require INPUT_MODE.
	modeList=[('keyboard', 'alt1')]
	
	@arg srcTransportWrapper vizconnect.Node()
	@arg dstTransportRaw viz.VizNode()
	"""
	nodeData = getTransportNodeData(srcTransportWrapper)
	classification = 'transport'
	mappingCode = ''
	# cycle through the mappings for the 
	mappingList = vizconnect.getData(nodeData, ['mappings', 'raw', 'perframe', 'list'])
	if mappingList:
		for mapping in mappingList:
			if mapping['slotName'] in triggeredFunctionMappings:
				if len(mapping['signalList']) > 0:
					for signal in mapping['signalList']:
						# if general mode requirement set, apply to signal
						if mode:
							signal['mode'] = mode
						# if per-device mode requirement set, apply to signal iff matching
						if modeList:
							for mlInputName, mlMode in modeList:
								if signal['inputName'] == mlInputName:
									signal['mode'] = mlMode
						
					mappingCode += generateModifiedMappingCode(classification, mapping, triggeredFunctionMappings[mapping['slotName']])
		
		updateCode = """
import vizact
global rawInput
rawInput = vizconnect.getConfiguration('{}').getRawDict('input')
def update({}):
{}
update(dstTransportRaw)
dstTransportRaw.setUpdateFunction(update)
""".format(srcTransportWrapper.getConfiguration().getFilename(),
			classification,
			mappingCode.rstrip())
		exec(updateCode)
		viz.logNotice('** Notice remapped controls for transport', dstTransportRaw)


def getTransportsWithMakeModel(make, model):
	"""Gets the transport with given make and model. If a default has been
	specified and matches, then it will be first in the list."""
	transportList = []
	# check default first
	default = vizconnect.getTransport()
	if default and default.getMake() == 'Virtual' and default.getModel() == 'WandMagicCarpet':
		transportList.append(default)
	# check any
	transportWrapperDict = vizconnect.getTransportDict()
	for transportWrapper in transportWrapperDict.values():
		if transportWrapper not in transportList and \
			transportWrapper.getMake() == make and \
			transportWrapper.getModel() == model:
				transportList.append(transportWrapper)
	return transportList
