"""Parses vizconnect events and returns the keys/buttons/analogs used
to trigger the event.
"""

import vizconnect


def getParsedData(filename, classification):
	"""Return a set of parsed data given a filename and classification.
	@args '' ''
	@return {}
	"""
	if classification == 'event':
		parser = vizconnect.code.Event()
	elif classification == 'input':
		parser = vizconnect.code.Input()
	elif classification == 'tool':
		parser = vizconnect.code.Tool()
	elif classification == 'tracker':
		parser = vizconnect.code.Tracker()
	elif classification == 'transport':
		parser = vizconnect.code.Transport()
	else:
		raise ValueError('**Error: Parser for classification {} not valid'.format(classification))
	
	# read the file with the parser and return the data
	fullCode = ''
	with open(filename, 'r') as tempFile:
		fullCode = tempFile.read()
	dataDict = {}
	codeDict = {}
	parser.parse(fullCode, dataDict, codeDict)
	
	return dataDict, parser


def parse(filename, eventName):
	"""Parses a configuration file and returns a human readable version
	of the trigger for a particular event.
	@args '' ''
	@return ''
	"""
	dataDict, parser = getParsedData(filename, 'event')
	for mappingTuple in parser.iterNodeMappings(dataDict):
		name, data = mappingTuple[0:2]
		if data['list'] and name == eventName:
			for mapping in data['list']:
				for signal in mapping['signalList']:
					signalName = signal['signalName'].lower()
					
					# special keyboard formatting
					if signal['inputModel'] == "Keyboard":
						signalNameList = signalName.replace('_', ' ').split(' ')
						# handle left and right replacement
						for s, d, t in [('l', 'left', 1), ('r', 'right', 1)]:
							if s in signalNameList:
								signalNameList.pop(signalNameList.index(s))
								signalNameList.insert(t, d)
						# move key to the back
						if 'key' in signalNameList:
							signalNameList.pop(signalNameList.index('key'))
							signalNameList.append('key')
						# add 'the' to the front and join the items
						signalName = 'the '+' '.join(signalNameList)
					
					tapWord = 'Press' if 'key' in signalName or 'button' in signalName else 'Use'
					if signal['negativeSignal']:
						inst = 'Release' if mapping['slotName'] == 'sendOnce' else 'While released'
					else:
						inst = tapWord if mapping['slotName'] == 'sendOnce' else 'Hold'
					return '{} {}'.format(inst, signalName)
	return None


def getEventSignal(filename, eventName):
	"""Parses a configuration file and returns the raw event data dictionary
	of the trigger for a particular event.
	@args '' ''
	@return {}
	"""
	dataDict, parser = getParsedData(filename, 'event')
	for mappingTuple in parser.iterNodeMappings(dataDict):
		name, data = mappingTuple[0:2]
		if data['list'] and name == eventName:
			for mapping in data['list']:
				for signal in mapping['signalList']:
					return signal
	return None


if __name__ == '__main__':
	vizconnect.go('../../vizconnect_config_default_desktop.py')
	print parse(vizconnect.getConfiguration().getFilename(), 'SHOW_MENU_EVENT')

