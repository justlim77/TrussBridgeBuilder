"""Add the ability to allow for an independent controller to adjust the plank settings"""

import viz
import vizconnect


def getEventNodeData(node):
	"""Returns the event node's data, None if not found."""
	# get the data from the event parser
	parser = vizconnect.code.Event()
	dataDict = {}
	filename = node.getConfiguration().getFilename()
	try:
		with open(filename, 'r') as tempFile:
			fullCode = tempFile.read()
			parser.parse(fullCode, dataDict, {})
	except IOError, e:
		viz.logError('** ERROR: Failed to load file {} for parsing.\n{}'.format(filename, e))
	return vizconnect.getData(dataDict, ['event', 'node', node.getName()])


def appendSignalToEventMapping(configurationFilename,
								eventName,
								signal,
								mode=None):
	"""Takes in an event name and appends the given signal"""
	# get the existing code for the given event
	classification = 'event'
	if configurationFilename is None:
		for tempFilename in vizconnect.ConfigurationManager.getFilenameList():
			if eventName in vizconnect.getConfiguration(tempFilename).event:
				configurationFilename = tempFilename
				break
	if configurationFilename is None:
		return
	
	nodeData = getEventNodeData(vizconnect.getConfiguration(configurationFilename).event[eventName])
	mappingCode = ''
	# cycle through the mappings for the 
	mappingList = vizconnect.getData(nodeData, ['mappings', 'raw', 'perframe', 'list'])
	if not mappingList:
		mappingList = []
	if mode:
		signal['mode'] = mode
	mappingList.append(vizconnect.code._Mapping(signalList=[signal],
												slotName=mappingList[0]['slotName'],
												classification=mappingList[0]['classification'],
												args=mappingList[0]['args'],
												kwargs=mappingList[0]['kwargs']))
	parser = vizconnect.code.Event()
	mappingCode = parser._generateNodeMappingsPerFrame(nodeData, 'raw')
	updateCode = """
import vizact
global rawEvent
rawEvent = vizconnect.getConfiguration('{0}').getRawDict('event')
def update({1}):
	_name = '{2}'
	initFlag = vizconnect.INIT_MAPPINGS_PER_FRAME
{3}
update(rawEvent['{2}'])
rawEvent['{2}'].setUpdateFunction(update)
		""".format(configurationFilename,
					classification,
					eventName,
					vizconnect.code._trimdent(mappingCode.rstrip(), 1))
	exec(updateCode)
