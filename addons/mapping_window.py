"""Module that provides a window showing the mappings for devices"""

import collections
import os

import viz
import vizconnect
import vizdlg
import vizinfo

import vizconnect_config_parser_tools



def _getMappingPanelList(parser, dataDict):
	"""Generate a grid panel"""
	subGridList = []
	
	for mappingTuple in parser.iterNodeMappings(dataDict):
		name, data = mappingTuple[0:2]
		subGrid = vizdlg.GridPanel()
		subGrid.addRow([viz.addText(name)])
		subGrid.addRow([viz.addText("____________________")])
		for mapping in data['list']:
			for signal in mapping['signalList']:
				if signal['negativeSignal']:
					subGrid.addRow([viz.addText(mapping['slotName']), viz.addText(": not "+signal['signalName'])])
				else:
					subGrid.addRow([viz.addText(mapping['slotName']), viz.addText(": "+signal['signalName'])])
		subGridList.append(subGrid)
	
	return subGridList


def _addProxyToolSubItems(subGridList, toolWrapper, data):
	"""add ref for each function proxy object supports"""
	callbackList = toolWrapper.getRaw().getCallbackDict().values()
	objRowDict = {}
	actionIndex = 1
	for callbackData in callbackList:
		if callbackData.obj:
			# generate a name
			mergedName = '{} based on {}'.format(callbackData.obj.__class__.__name__, toolWrapper.getName())
			if not mergedName in objRowDict:
				subGrid = vizdlg.GridPanel()
				subGrid.addRow([viz.addText(mergedName)])
				subGrid.addRow([viz.addText("____________________")])
				objRowDict[mergedName] = subGrid
			else:
				subGrid = objRowDict[mergedName]
			
			# add data to subGrid
			targetSlotName = 'action{}'.format(actionIndex)
			for mapping in data['list']:
				if mapping['slotName'] == targetSlotName:
					for signal in mapping['signalList']:
						# if slot name is open use that
						subGrid.addRow([
							viz.addText('{} ({})'.format(callbackData.callbackFunction.__name__, mapping['slotName'])),
							viz.addText(':{}{}'.format('not ' if signal['negativeSignal'] else '',
														signal['signalName']))
						])
		actionIndex += 1
	
	for subGrid in objRowDict.values():
		subGridList.append(subGrid)


def _getToolMappingPanelList(parser, dataDict):
	"""Generate a grid panel. Specialized for proxy tools."""
	subGridList = []
	
	for mappingTuple in parser.iterNodeMappings(dataDict):
		name, data = mappingTuple[0:2]
		toolWrapper = vizconnect.getTool(name)
		if toolWrapper.getManipulationMode() == 'Proxy':
			_addProxyToolSubItems(subGridList, toolWrapper, data)
		
		else:# add hard coded keys
			subGrid = vizdlg.GridPanel()
			subGrid.addRow([viz.addText(name)])
			subGrid.addRow([viz.addText("____________________")])
			for mapping in data['list']:
				for signal in mapping['signalList']:
					if signal['negativeSignal']:
						subGrid.addRow([viz.addText(mapping['slotName']), viz.addText(": not "+signal['signalName'])])
					else:
						subGrid.addRow([viz.addText(mapping['slotName']), viz.addText(": "+signal['signalName'])])
			subGridList.append(subGrid)
	
	return subGridList


def _getEventMappingPanelList(parser, dataDict, showDisabledEvents=False):
	"""Generate a grid panel"""
	subGridList = []
	
	subGrid = None
	for mappingTuple in parser.iterNodeMappings(dataDict):
		name, data = mappingTuple[0:2]
		if data['list'] and (vizconnect.getEvent(name).getEnabled() or showDisabledEvents):
			rowList = []
			rowList += [viz.addText(name)]
			for mapping in data['list']:
				for signal in mapping['signalList']:
					rowList += [viz.addText(": {}{}{}".format(
						'on ' if mapping['slotName'] == 'sendOnce' else 'while ', # freq
						'not ' if signal['negativeSignal'] else '', # negation text
						signal['signalName']
					))]
			if not subGrid:
				subGrid = vizdlg.GridPanel()
			subGrid.addRow(rowList)
	
	if subGrid:
		subGridList.append(subGrid)
	
	return subGridList


def _getSubGridPanels(grid, fileList, color, classification=''):
	"""Generate a grid panel"""
	for filename in fileList:
		dataDict, parser = vizconnect_config_parser_tools.getParsedData(filename, classification)
		subGridList = []
		if classification == 'event':
			# want to sample if event is live, so change context
			tempFilename = vizconnect.getConfiguration().getFilename()
			vizconnect.ConfigurationManager.setCurrent(filename)
			subGridList += _getEventMappingPanelList(parser, dataDict)
			vizconnect.ConfigurationManager.setCurrent(tempFilename)
		elif classification == 'tool':
			# want to sample if event is live, so change context
			tempFilename = vizconnect.getConfiguration().getFilename()
			vizconnect.ConfigurationManager.setCurrent(filename)
			subGridList += _getToolMappingPanelList(parser, dataDict)
			vizconnect.ConfigurationManager.setCurrent(tempFilename)
		else:
			subGridList += _getMappingPanelList(parser, dataDict)
		
		# make sure we have something in the grid list
		if subGridList:
			grid.addRow(subGridList)
		
		for subGrid in subGridList:
			skin = vizdlg.ModernSkin(alpha=0.85)
			theme = viz.getTheme()
			theme.borderColor = color
			skin.theme = theme
			subGrid.setSkin(skin)


class MappingWindow(object):
	"""Class for a mapping window, parses a list of configuration files to generate
	a GUI containing all the defined controls for events, inputs, tools, transports,
	etc.
	"""
	
	def __init__(self, fileList=None, autoReload=False, panelSettingsDict=None, alignment=None):
		self._autoReload = autoReload
		
		useIcon = False
		if alignment is None:
			displayType = vizconnect.getDisplay().getType()
			if displayType == vizconnect.DISPLAY_MONITOR:
				alignment = viz.ALIGN_LEFT_TOP
				useIcon = True
			else:
				alignment = viz.ALIGN_CENTER
				useIcon = False
		self._alignment = alignment
		self._useIcon = useIcon
		self._displayType = vizconnect.getDisplay().getType()
		
		if panelSettingsDict is None:
			panelSettingsDict = collections.OrderedDict()
			panelSettingsDict['event'] = {'color':(0.1, 0.0, 0, 1)}
			panelSettingsDict['tool'] = {'color':(0.0, 0.1, 0, 1)}
			panelSettingsDict['transport'] = {'color':(0.0, 0, 0.1, 1)}
#			panelSettingsDict['input'] = {'color':(0.077, 0.077, 0, 1)}
		self._panelSettingsDict = panelSettingsDict
		
		self._panelDict = collections.OrderedDict()
		
		self._step = 0
		
		if fileList is None and vizconnect.getConfiguration():
			self._fileList = vizconnect_config_parser_tools.getFullConfigurationList([vizconnect.getConfiguration().getFilename()])
		else:
			self._fileList = list(fileList)
	
	def setFileList(self, fileList):
		"""Sets the file list using the live session data"""
		self.clear()
		self._fileList = list(fileList)
	
	def clear(self):
		"""Clears the mapping window removing all sub panels"""
		while self._panelDict:
			panel = self._panelDict.pop(self._panelDict.keys()[0])
			panel.remove()
	
	def _makePanel(self, fileList, classification, color):
		"""Generate a grid panel"""
		# make a event panel
		title = classification.capitalize()+'s'
		panel = vizinfo.InfoPanel(title, align=self._alignment, skin=vizdlg.ModernSkin(alpha=0.5), icon=self._useIcon, key=None)
		panel.color([0.1, 0.3, 0.1])
		
		grid = vizdlg.GridPanel(border=False)
		panel.addItem(grid)
		_getSubGridPanels(grid, fileList, color, classification)
		
		self._panelDict[classification] = panel
	
	def setVisible(self, state):
		"""Sets the visibility for the panels"""
		if state == viz.TOGGLE:
			# check if any panel is visible, if so, set state to False
			for panel in self._panelDict.values():
				if panel.getVisible():
					state = False
		
		for panel in self._panelDict.values():
			panel.visible(state)
	
	def cycle(self):
		"""Cycles through the various panels"""
		self.setStep((self._step+1)%(len(self._panelSettingsDict.keys())+1))
		self._updatePanelAlignment()
	
	def reload(self):
		"""Reloads all of the panels, by re-parsing the configuration files."""
		self.clear()
		for classification in self._panelSettingsDict.keys():
			self._makePanel(self._fileList, classification, self._panelSettingsDict[classification]['color'])
			self._panelDict[classification].visible(False)
		self.setStep(self._step)
	
	def setStep(self, step):
		"""Set the step in the sequence of panels."""
		self._step = step
		
		for panel in self._panelDict.values():
			panel.visible(False)
		
		if step == 0:
			if self._autoReload:
				self.clear()
		elif self._step < len(self._panelSettingsDict.keys())+1:
			classification = self._panelSettingsDict.keys()[self._step-1]
			if not classification in self._panelDict:
				color = self._panelSettingsDict[classification]['color']
				self._makePanel(self._fileList, classification, color)
			else:
				self._panelDict[classification].visible(True)
		else:
			pass
	
	def _updatePanelAlignment(self):
		"""Updates the alignment of the panel so that it can usefully match 
		the display type.
		"""
		if self._displayType != vizconnect.getDisplay().getType():
			useIcon = False
			self._displayType = vizconnect.getDisplay().getType()
			if self._displayType == vizconnect.DISPLAY_MONITOR:
				alignment = viz.ALIGN_LEFT_TOP
				useIcon = True
			else:
				alignment = viz.ALIGN_CENTER
				useIcon = False
			self._alignment = alignment
			self._useIcon = useIcon
			for panel in self._panelDict.values():
				panel.setAlignment(self._alignment)
				panel.getIcon().visible(self._useIcon)
