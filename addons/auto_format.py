"""Functions for auto formatting vizconnect configuration files. Use these
functions if you need to ensure that a particular configuration file as say a
grabber object or a particular mode for an input.  The advantages of directly
modifying the configuration as opposed to performing the addition dynamically
include the following:

1.) It allows the user to customize any mappings for the auto added code.

2.) It allows for automated parsing of any adjustments that the user has made
to the device/tool/transport/etc.
"""

import viz
import vizconnect


def getTransportNodeData(node):
	"""Return node data for transport
	@return {}
	"""
	# get the data from the transport parser
	parser = vizconnect.code.Transport()
	dataDict = {}
	filename = node.getConfiguration().getFilename()
	try:
		with open(filename, 'r') as tempFile:
			fullCode = tempFile.read()
			parser.parse(fullCode, dataDict, {})
	except IOError:
		viz.logError('** ERROR: Failed to load file {} for parsing'.format(filename))
	return vizconnect.getData(dataDict, ['transport', 'node', node.getName()])


def forceAltModeForInput(inputWrapper=None):
	"""Force alt mode for the input
	TODO: DEPRICATED: NOT CURRENTLY USED
	"""
	if inputWrapper is None:
		# get the input node
		inputWrapper = vizconnect.getInput()
	
	if inputWrapper:
		# get the input editor
		editor = vizconnect.edit.add(inputWrapper.getConfiguration().getFilename())
		inputEditor = editor.get('input')
		
		# get/set the trigger information used to generate the mapping
		triggerSignals = inputWrapper.getTemplateObject().getTriggerList(inputWrapper.getName())
		triggerSlots = [{"index":0, "function":"setQuasimode", 'args':[vizconnect.code._Parameter(code="'alt1'")]}]
		
		# add mapping list
		mappingList = []
		for slot in triggerSlots:
			if slot['index'] < len(triggerSignals):
				signal = triggerSignals[slot["index"]]
				if signal:
					mappingList.append(vizconnect.code._Mapping(signalList=[signal],
																	slotName=slot['function'],
																	classification='input',
																	**slot))
		
		# add to file
		inputEditor.setNodeMappingList(vizconnect.getInput().getName(),
										'wrapper',
										'perframe',
										mappingList)
		inputEditor.commit()


def forceTransportNoneMode(transportWrapper=None, inputWrapper=None):
	"""Force transport mappings to use None mode, i.e. no mode for inputs."""
	if transportWrapper is None:
		# get the transport node
		transportWrapper = vizconnect.getTransport()
	inputName = None
	if inputWrapper:
		inputName = inputWrapper.getName()
	
	if transportWrapper:
		transportName = transportWrapper.getName()
		
		# get the transport editor
		editor = vizconnect.edit.add(transportWrapper.getConfiguration().getFilename())
		transportEditor = editor.get('transport')
		
		nodeData = getTransportNodeData(transportWrapper)
		# cycle through the mappings for the transport
		mappingList = vizconnect.getData(nodeData, ['mappings', 'raw', 'perframe', 'list'])
		if mappingList:
			for mapping in mappingList:
				signalList = mapping['signalList']
				for signal in signalList:
					if inputName:
						if signal['inputName'] == inputName:
							signal['mode'] = 'None'
					else:
						signal['mode'] = 'None'
			
			# add to file
			transportEditor.setNodeMappingList(transportName,
												'raw',
												'perframe',
												mappingList)
			transportEditor.commit()


def forceActionEventMappings(inputWrapper=None):
	"""Force add action event mappings."""
	if inputWrapper is None:
		# get the input node
		inputWrapper = vizconnect.getInput()
	if not inputWrapper:
		return
	
	# get the triggers/signals available for the input
	inputTemplateObject = inputWrapper.getTemplateObject()
	inputName = inputWrapper.getName()
	triggerSignals = inputTemplateObject.getTriggerList(inputName)
	
	# get the configuration filename for the input, add events to input's
	# configuration file.
	configFilename = inputWrapper.getConfiguration().getFilename()
	config = vizconnect.edit.get(configFilename)
	if not config:
		config = vizconnect.edit.add(configFilename)
	# get the event editor
	eventEditor = config.get('event')
	
	# add as many action events as possible given the input device
	for i in range(0, len(triggerSignals)):
		signal = triggerSignals[i]
		
		# add the events
		eventNameList = [
			('ACTION_EVENT_{}'.format(i+1), 'sendEvent', False), # eventName, slotName, negativeSignal
			('ACTION_EVENT_{}_START'.format(i+1), 'sendOnce', False),
			('ACTION_EVENT_{}_STOP'.format(i+1), 'sendOnce', True)
		]
		
		# add the action events if they're not found
		for eventName, slotName, negativeSignal in eventNameList:
			eventNode = eventEditor._getFinalNode(eventName)
			if not eventNode:
				eventEditor.addNode(eventName, 'Vizconnect', 'Custom')
				eventEditor.commit()
				eventNode = eventEditor._getFinalNode(eventName)
				
				slot = {}
				if eventNode:
					signal['negativeSignal'] = negativeSignal
					mappingList = []
					# now that we know there's an event, add the mapping
					mappingList.append(vizconnect.code._Mapping(signalList=[signal],
																slotName=slotName,
																classification='event',
																**slot))
					
					target = 'raw'
					frequency = 'perframe'
					eventEditor.setNodeMappingList(eventName, target, frequency, mappingList)
					eventEditor.commit()
				eventWrapper = vizconnect.getEvent(eventName)
				if eventWrapper:
					eventWrapper.getRaw().updateEvent.setEnabled(False)


def forceAvatarToggleMapping(inputWrapperList=None):
	"""Force add action event mappings."""
	# get the input node
	keyboardInputWrapper = None
	for inputWrapper in inputWrapperList:
		if inputWrapper.getModel() == 'Keyboard':
			keyboardInputWrapper = inputWrapper
	if not keyboardInputWrapper:
		return
	
	# get the triggers/signals available for the input
	separateMenuSignalList = []
	inputTemplateObject = keyboardInputWrapper.getTemplateObject()
	keyA = inputTemplateObject.getSignalData(keyboardInputWrapper.getName(), 'Key A')
	keyAltL = inputTemplateObject.getSignalData(keyboardInputWrapper.getName(), 'Key ALT_L')
	keyAltR = inputTemplateObject.getSignalData(keyboardInputWrapper.getName(), 'Key ALT_R')
	if keyA and keyAltL and keyAltR:
		separateMenuSignalList.append([keyA, keyAltL])
		separateMenuSignalList.append([keyA, keyAltR])
	
	# get the menu signal for the given device
	if separateMenuSignalList:
		# get the configuration filename for the input, add events to input's
		# configuration file.
		configFilename = keyboardInputWrapper.getConfiguration().getFilename()
		config = vizconnect.edit.get(configFilename)
		if not config:
			config = vizconnect.edit.add(configFilename)
		# get the event editor
		eventEditor = config.get('event')
		
		# add the events
		eventNameList = [
			('DEMO_LAUNCHER_TOGGLE_AVATAR_VISIBILITY', 'sendOnce', False), # eventName, slotName, negativeSignal
		]
		
		# add the action events if they're not found
		for eventName, slotName, negativeSignal in eventNameList:
			# check to make sure we have it, if not generate
			eventNode = eventEditor._getFinalNode(eventName)
			if not eventNode:
				viz.logNotice('**Notice: Force adding menu events.')
				eventEditor.addNode(eventName, 'Vizconnect', 'Custom')
				eventEditor.commit()
				eventNode = eventEditor._getFinalNode(eventName)
				
				slot = {}
				if eventNode:
					mappingList = []
					for signalList in separateMenuSignalList:
						for signal in signalList:
							signal['negativeSignal'] = negativeSignal
						# now that we know there's an event, add the mapping
						mappingList.append(vizconnect.code._Mapping(signalList=signalList,
																	slotName=slotName,
																	classification='event',
																	kwargs={'mode':vizconnect.code._Parameter(code='viz.TOGGLE')},
																	**slot))
					target = 'raw'
					frequency = 'perframe'
					eventEditor.setNodeMappingList(eventName, target, frequency, mappingList)
					eventEditor.commit()


def forceMenuEventMappings(inputWrapperList=None):
	"""Force add action event mappings."""
	if not inputWrapperList:
		# get the input node
		inputWrapperList = [vizconnect.getInput()]
	
	eventNameList = [
		('SHOW_MENU_EVENT', 'sendOnce', False), # eventName, slotName, negativeSignal
		('MOVE_MENU_EVENT', 'sendEvent', False), # eventName, slotName, negativeSignal
	]
	
	configFilename = vizconnect.getConfiguration().getFilename()
	config = vizconnect.edit.get(configFilename)
	if not vizconnect.getInput():
		if not config:
			config = vizconnect.edit.add(configFilename)
		# get the event editor
		eventEditor = config.get('event')
		# add the action events if they're not found
		for eventName, slotName, negativeSignal in eventNameList:
			viz.logNotice('**Notice: Force adding menu events.')
			eventEditor.addNode(eventName, 'Vizconnect', 'Custom')
			eventEditor.commit()
			eventNode = eventEditor._getFinalNode(eventName)
		return
	
	# get the triggers/signals available for the input
	# get the event editor
	eventEditor = config.get('event')
	
	# add the events
	# add the action events if they're not found
	for eventName, slotName, negativeSignal in eventNameList:
		# check to make sure we have it, if not generate
		eventNode = eventEditor._getFinalNode(eventName)
#				if not eventNode:
		viz.logNotice('**Notice: Force adding menu events.')
		eventEditor.addNode(eventName, 'Vizconnect', 'Custom')
		eventEditor.commit()
		eventNode = eventEditor._getFinalNode(eventName)
		if eventNode:
			mappingList = []
			for inputWrapper in inputWrapperList:
				inputTemplateObject = inputWrapper.getTemplateObject()
				# get the menu signal for the given device
				menuSignal = inputTemplateObject.getMenuSignal(inputWrapper.getName())
				if menuSignal:
					# get the configuration filename for the input, add events to input's
					# configuration file.
#					configFilename = inputWrapper.getConfiguration().getFilename()
#					config = vizconnect.edit.get(configFilename)
#					if not config:
#						config = vizconnect.edit.add(configFilename)
					
					slot = {}
					menuSignal['negativeSignal'] = negativeSignal
					# now that we know there's an event, add the mapping
					mappingList.append(vizconnect.code._Mapping(signalList=[menuSignal],
																slotName=slotName,
																classification='event',
																**slot))
			target = 'raw'
			frequency = 'perframe'
			eventEditor.setNodeMappingList(eventName, target, frequency, mappingList)
			eventEditor.commit()


def forceGrabber(inputWrapper=None):
	"""Force add grabber tool."""
	toolName = 'grabber'
	
	if not inputWrapper:
		inputWrapper = vizconnect.getInput()
	if not inputWrapper:
		return
	
	inputName = inputWrapper.getName()
	
	# get the tool editor
	editor = vizconnect.edit.add(inputWrapper.getConfiguration().getFilename())
	toolEditor = editor.get('tool')
	toolNode = toolEditor._getFinalNode(toolName)
	
	# get the input editor and node
	inputName = 'r_hand_input'
	inputEditor = vizconnect.edit.get(inputWrapper.getConfiguration().getFilename()).get('input')
	inputNode = inputEditor._getFinalNode(inputName)
	
	if toolName not in inputWrapper.getConfiguration().tool:
		# if we have an input add a tool and set the mapping list
		if inputNode:
			# check the default tool
			toolNode = toolEditor._getFinalNode(toolName)
			if not toolNode:
				# add node
				toolEditor.addNode(name=toolName,
									make='Virtual',
									model='Grabber')
				toolEditor.commit()
				
				# set to default
				toolEditor.setDefault(toolName)
				toolEditor.commit()
				toolNode = toolEditor._getFinalNode(toolName)
		else:
			# if there's no input remove the tool node
			toolNode = toolEditor._getFinalNode(toolName)
			if toolNode:
				toolEditor.removeNode(toolName)
				toolEditor.commit()
				toolNode = None
	
	# check if we need to add mappings
	mappings = vizconnect.getData(toolNode, ['mappings', 'raw', 'perframe', 'list'])
	if toolNode and not mappings and inputNode:
		# add mappings
		mappingList = toolEditor.getAutoGeneratedMappingList(toolName, inputName, inputNode)
		toolEditor.setNodeMappingList(toolName, 'raw', 'perframe', mappingList)
		toolEditor.commit()
	
	# set using physics to false
	parameters = toolEditor.getNodeRawParameters(toolName)
	if parameters['usingPhysics']['value'] != False:
		parameters['usingPhysics'].setCode('False')
		toolEditor.setNodeRawParameters(toolName, parameters)
		toolEditor.commit()
	
	# parent the new tool
	parentData = toolEditor.getNodeParent(toolName)
	avatar = vizconnect.getAvatar()
	if avatar:
		avatarName = avatar.getName()
		parentedCorrectly = False
		if parentData and parentData['parentName'] == avatarName and parentData['parentClassification'] == 'avatar' and parentData['attachmentPointName'] == vizconnect.AVATAR_R_HAND:
			parentedCorrectly = True
		if not parentedCorrectly:
			toolEditor.setNodeParent(toolName, parentClassification='avatar', parentName=avatarName, attachmentPointName=vizconnect.AVATAR_R_HAND)
			toolEditor.commit()


def forceProxy(inputWrapper=None):
	"""Force add proxy tool."""
	toolName = 'proxy'
	
	# prefer the r_hand_input if present
	if 'r_hand_input' in vizconnect.getInputDict():
		inputWrapper = vizconnect.getInput('r_hand_input')
	
	if not inputWrapper:
		inputWrapper = vizconnect.getInput()
	if not inputWrapper:
		return
	
	inputName = inputWrapper.getName()
	
	# get the tool editor
	editor = vizconnect.edit.add(inputWrapper.getConfiguration().getFilename())
	toolEditor = editor.get('tool')
	toolNode = toolEditor._getFinalNode(toolName)
	
	# get the input editor and node
	inputEditor = vizconnect.edit.get(inputWrapper.getConfiguration().getFilename()).get('input')
	inputNode = inputEditor._getFinalNode(inputName)
	
	if toolName not in inputWrapper.getConfiguration().tool:
		# if we have an input add a tool and set the mapping list
		if inputNode:
			# check the default tool
			toolNode = toolEditor._getFinalNode(toolName)
			if not toolNode:
				# add node
				toolEditor.addNode(name=toolName, make='Virtual', model='Proxy')
				toolEditor.commit()
				
				# set to default
				toolEditor.setDefault(toolName)
				toolEditor.commit()
				toolNode = toolEditor._getFinalNode(toolName)
		else:
			# if there's no input remove the tool node
			toolNode = toolEditor._getFinalNode(toolName)
			if toolNode:
				toolEditor.removeNode(toolName)
				toolEditor.commit()
				toolNode = None
	
	# check if we need to add mappings
	mappings = vizconnect.getData(toolNode, ['mappings', 'raw', 'perframe', 'list'])
	if toolNode and not mappings and inputNode:
		# add mappings
		mappingList = toolEditor.getAutoGeneratedMappingList(toolName, inputName, inputNode)
		toolEditor.setNodeMappingList(toolName, 'raw', 'perframe', mappingList)
		toolEditor.commit()
	
	# parent the new tool
	parentData = toolEditor.getNodeParent(toolName)
	avatar = vizconnect.getAvatar()
	if avatar:
		avatarName = avatar.getName()
		parentedCorrectly = False
		if parentData and parentData['parentName'] == avatarName and parentData['parentClassification'] == 'avatar' and parentData['attachmentPointName'] == vizconnect.AVATAR_R_HAND:
			parentedCorrectly = True
		
		if not parentedCorrectly:
			toolEditor.setNodeParent(toolName, parentClassification='avatar', parentName=avatarName, attachmentPointName=vizconnect.AVATAR_R_HAND)
			toolEditor.commit()
