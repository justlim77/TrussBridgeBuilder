
import copy

import viz


STD_TEXT_LINE_HEIGHT = 0.02
STD_TEXT_LINE_SPACING = 0.2


def getDarkTheme():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(viz.getTheme())
	
	theme.titleBarLocation = viz.ALIGN_CENTER_BOTTOM
	
	theme.helpIndex = 1
	theme.constantPanelButtons = False
	theme.collisionTestFlag = 1|2
	
	# font
	theme.lineHeight = STD_TEXT_LINE_HEIGHT*1.1
	theme.H1 = theme.lineHeight*3.0
	theme.H2 = theme.lineHeight*2.5
	theme.H3 = theme.lineHeight*2.0
	theme.H4 = theme.lineHeight*1.5
	
	theme.stdButtonSize = [theme.lineHeight*12.0, theme.lineHeight*3.5]
	
	theme.useTopBackButton = False
	
	theme.name = 'Dark'
	theme.borderSize = 0.003
	theme.borderColor = (1, 1, 1, 1)
	theme.topBackColor = (0.2, 0.2, 0.2, 0.75)
	theme.backColor = (0.1, 0.1, 0.1, 1.0)
	theme.lightBackColor = (0.1, 0.1, 0.1, 1)
	theme.darkBackColor = (0.1, 0.1, 0.1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (1, 1, 1, 1)
	theme.highlightColor = (0.8, 0.8, 1.0, 0.7)
	theme.textColor = (1, 1, 1, 1)
	theme.cornerRadius = 0
	
	# text/font
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.font = 'Segoe UI'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.indexTextColor = viz.YELLOW
	
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0
	theme.dimAmount = 0.5
	theme.highlightAmount = 1.0
	
	theme.screenBrightnessCompensationLevel = 0
	
	theme.cursorSize = [0.05, 0.05]
	theme.cursorHotSpot = [1, -1]
	
	theme.cursorIcon = 'resources/icons/pointer_hand.png'
	theme.arrowIcon = './resources/icons/arrow.png'
	theme.backIcon = './resources/icons/back.png'
	theme.cancelIcon = './resources/icons/cancel.png'
	theme.dotIcon = './resources/icons/dot.png'
	theme.homeIcon = './resources/icons/home_unstylized.png'
	theme.minimizeIcon = 'resources/icons/minimize.png'
	theme.maximizeIcon = 'resources/icons/maximize.png'
	theme.moveIcon = 'resources/icons/move.png'
	theme.anchorIcon = 'resources/icons/anchor.png'
	
	theme.buttonCornerRadius = 0.0
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0, 0, 0, 1)
	theme.tooltipTheme.backColor = (1, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getCaveTheme():
	theme = copy.deepcopy(getDarkTheme())
	theme.screenBrightnessCompensationLevel = 1
	theme.name = 'CAVE Default'
	return theme


def getStriVRTheme():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(viz.getTheme())
	
	theme.name = 'STRIVR'
	theme.titleBarLocation = viz.ALIGN_CENTER_BOTTOM
	
	theme.helpIndex = 2
	theme.constantPanelButtons = False
	theme.collisionTestFlag = 1|2
	
	# font
	theme.lineHeight = STD_TEXT_LINE_HEIGHT*1.5
	theme.H1 = theme.lineHeight*3.0
	theme.H2 = theme.lineHeight*2.5
	theme.H3 = theme.lineHeight*2.0
	theme.H4 = theme.lineHeight*1.5
	
	theme.stdButtonSize = [theme.lineHeight*12.0, theme.lineHeight*3.5]
	
	theme.useTopBackButton = False
	
	theme.name = 'Dark'
	theme.borderSize = 0.003
	theme.borderColor = (1, 1, 1, 1)
	theme.topBackColor = (0.6, 0.2, 0.2, 0.01)
	theme.backColor = (0.1, 0.1, 0.1, 0.01)
	theme.lightBackColor = (0.1, 0.1, 0.1, 1)
	theme.darkBackColor = (0.1, 0.1, 0.1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (1, 1, 1, 1)
	theme.highlightColor = (0.8, 0.8, 1.0, 0.7)
	theme.textColor = (1, 1, 1, 1)
	theme.cornerRadius = 0
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.font = 'Segoe UI'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0
	theme.dimAmount = 0.5
	
	theme.cursorSize = [0.10, 0.10]
	theme.cursorHotSpot = [0, 0]
	
	theme.cursorIcon = 'art/Cursor.tif'
	theme.arrowIcon = './resources/icons/arrow.png'
	theme.backIcon = './resources/icons/back.png'
	theme.cancelIcon = './resources/icons/cancel.png'
	theme.dotIcon = './resources/icons/dot.png'
	theme.homeIcon = './resources/icons/home_unstylized.png'
	theme.minimizeIcon = 'resources/icons/minimize.png'
	theme.maximizeIcon = 'resources/icons/maximize.png'
	theme.moveIcon = 'resources/icons/move.png'
	theme.anchorIcon = 'resources/icons/anchor.png'
	
	theme.buttonCornerRadius = 0.0
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0, 0, 0, 1)
	theme.tooltipTheme.backColor = (1, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getCyanOnBlack():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	
	theme.useTopBackButton = False
	theme.titleBarLocation = viz.ALIGN_CENTER_BOTTOM
	
	theme.name = 'CyanOnBlack'
	theme.borderSize = 0.003
	theme.borderColor = (0, 1, 1, 1)#(0.2, 0.2, 0.2, 1)
	theme.backColor = (0.2, 0.2, 0.2, 1)
	theme.lightBackColor = (0.3, 0.3, 0.3, 1)
	theme.darkBackColor = (0.1, 0.1, 0.1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (1, 1, 1, 1)
	theme.highlightColor = (0.8, 1.0, 1.0, 0.7)
	theme.textColor = (0, 1, 1, 1)#(1, 1, 1, 1)
	theme.cornerRadius = 0
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0
	theme.dimAmount = 0.5
	
	theme.buttonCornerRadius = 0.01
	
	theme.cursorIcon = 'resources/icons/dot.png'
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0, 0, 0, 1)
	theme.tooltipTheme.backColor = (1, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getWhiteOnBlack():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	
	theme.useTopBackButton = False
	theme.titleBarLocation = viz.ALIGN_CENTER_BOTTOM
	
	theme.name = 'CyanOnBlack'
	theme.borderSize = 0.003
	theme.topBackColor = (0.9, 0.9, 0.9, 0.75)
	theme.borderColor = (0, 0, 0, 1)#(0.2, 0.2, 0.2, 1)
	theme.backColor = (0.9, 0.9, 0.9, 1)
	theme.lightBackColor = (0.3, 0.3, 0.3, 1)
	theme.darkBackColor = (1, 1, 1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (0, 0, 0, 1)
	theme.highlightColor = (0.1, 0.1, 0.1, 0.7)
	theme.textColor = (0, 0, 0, 1)#(1, 1, 1, 1)
	theme.cornerRadius = 0
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0
	theme.dimAmount = 0.8
	theme.highlightAmount = 1.0
	
	theme.buttonCornerRadius = 0.01
	
	theme.cursorIcon = 'resources/icons/dot.png'
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0, 0, 0, 1)
	theme.tooltipTheme.backColor = (1, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getCyanLightOnBlack():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	theme.name = 'CyanLightOnBlack'
	
	theme.cursorIcon = 'resources/icons/blank.png'
	theme.homeIcon = './resources/icons/home_unstylized.png'
	
	theme.useTopBackButton = False
	
	theme.borderSize = 0.003
	theme.borderColor = (0.35, 1, 1, 1)
	theme.backColor = (0.2, 0.2, 0.2, 1)
	theme.lightBackColor = (0.3, 0.3, 0.3, 1)
	theme.darkBackColor = (0.1, 0.1, 0.1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (1, 1, 1, 1)
	theme.highlightColor = (0.8, 1.0, 1.0, 0.7)
	theme.textColor = (0.35, 1, 1, 1)
	theme.cornerRadius = 0
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0.0
	theme.dimAmount = 0.5
	
	updateLineHeight(theme, STD_TEXT_LINE_HEIGHT*1.1)
	
	theme.buttonCornerRadius = 0.01
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0.2, 0.2, 0.2, 1)
	theme.tooltipTheme.backColor = (0.35, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getBlueOnBlack():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	theme.name = 'BlueOnBlack'
	theme.borderSize = 0.003
	theme.topBackColor = (0.1, 0.1, 0.1, 1.0)
	theme.borderColor = (0, 0.5, 1, 1)#(0.2, 0.2, 0.2, 1)
	theme.backColor = (0.1, 0.1, 0.1, 1)
	theme.lightBackColor = (0.1, 0.1, 0.1, 1)
	theme.darkBackColor = (0.1, 0.1, 0.1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (1, 1, 1, 1)
	theme.highlightColor = (0.8, 1.0, 1.0, 0.7)
	theme.textColor = (0, 0.5, 1, 1)#(1, 1, 1, 1)
	theme.cornerRadius = 0
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0.0
	theme.dimAmount = 0.5
	
	updateLineHeight(theme, STD_TEXT_LINE_HEIGHT*1.1)
	
	theme.buttonCornerRadius = 0.01
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0, 0, 0, 1)
	theme.tooltipTheme.backColor = (1, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getGreenOnBlack():
	"""Returns a sample 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	theme.name = 'GreenOnBlack'
	theme.borderSize = 0.003
	theme.borderColor = (0, 1, 0, 1)#(0.2, 0.2, 0.2, 1)
	theme.backColor = (0.1, 0.1, 0.1, 1)
	theme.lightBackColor = (0.1, 0.1, 0.1, 1)
	theme.darkBackColor = (0.1, 0.1, 0.1, 1)
	theme.highBackColor = (0, 0, 0, 1)
	theme.highTextColor = (1, 1, 1, 1)
	theme.highlightColor = (0.8, 0.8, 1.0, 0.7)
	theme.textColor = (0, 1, 0, 1)#(1, 1, 1, 1)
	theme.cornerRadius = 0
	theme.font = 'resources/fonts/Roboto-Regular.ttf'
	theme.backdrop = viz.BACKDROP_OUTLINE
	theme.backdropColor = viz.BLACK
	theme.backdropOffset = 0.05
	theme.overlayPercent = 1.0
	theme.overlayCornerRadius = 0.0
	theme.dimAmount = 0.5
	
	theme.buttonCornerRadius = 0.01
	
	theme.tooltipTheme = copy.deepcopy(theme)
	theme.tooltipTheme.font = theme.font
	theme.tooltipTheme.textColor = (0, 0, 0, 1)
	theme.tooltipTheme.backColor = (1, 1, 1, 1)
	theme.tooltipTheme.topBackColor = (1, 1, 1, 1)
	
	return copy.deepcopy(theme)


def getBlueTheme():
	"""Returns a sample 'blue' theme based on the dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	theme.backColor = (0.2, 0.2, 0.6, 1.0)
	return copy.deepcopy(theme)


def getGreenTheme():
	"""Returns a sample 'green' theme based on the 'dark' theme.
	
	@return viz.Theme()
	"""
	theme = copy.deepcopy(getDarkTheme())
	theme.backColor = (0.2, 0.6, 0.2, 1.0)
	return copy.deepcopy(theme)


def updateLineHeight(theme, lineHeight):
	theme.lineHeight = lineHeight
	theme.H1 = theme.lineHeight*3.0
	theme.H2 = theme.lineHeight*2.5
	theme.H3 = theme.lineHeight*2.0
	theme.H4 = theme.lineHeight*1.5
	theme.stdButtonSize = [theme.lineHeight*12.0, theme.lineHeight*3.5]


def themeUpdater(func):
	def inner(self, *args, **kwargs):
		theme = self._getTheme()
		retVal = func(self, theme=theme, *args, **kwargs)
		self._setTheme(theme)
		return retVal
	return inner

def themeColorUpdater(func):
	def inner(self, *args, **kwargs):
		theme = self._getTheme()
		color = vizinput.color()
		retVal = func(self, theme=theme, color=color, *args, **kwargs)
		self._setTheme(theme)
		return retVal
	return inner


import vizconfig

class ThemeConfig(vizconfig.Configurable):
	def __init__(self, gui):
		self._gui = gui
		
		self._vizconfigWindow = vizconfig.getConfigWindow('Embedded Menu Config')
		vizconfig.Configurable.__init__(self, 'Utility Menu')
		self.registerConfig()
	
	def createConfigUI(self):
		"""Creates the vizconfig configuration ui. You do not need to call this
		function directly.
		"""
		ui = vizconfig.DefaultUI()
		ui.addFloatRangeItem('line height', [0.01, 0.03], self._config_setLineHeight, lambda: self._getTheme().lineHeight)
		ui.addChoiceListItem('font', [['segoe UI', 'Segoe UI'], ['Roboto-Regular', 'resources/fonts/Roboto-Regular.ttf']], self._config_setFont)
		button = viz.addButton()
		ui.addInteractiveItem('color', button)
		return ui
	
	def registerConfig(self):
		"""Registers this tracker with the vizconfig window associated with the
		wrapper's configuration file.
		"""
		vizconfig.register(self, window='Embedded Menu Config', name='Utility Menu')
	
	def unregisterConfig(self):
		"""Unregisters this wrapper with vizconfig."""
		vizconfig.unregister(self, window='Embedded Menu Config')
	
	@themeUpdater
	def _config_setLineHeight(self, size, theme):
		updateLineHeight(theme, size)
	
	@themeUpdater
	def _config_setFont(self, font, theme):
		theme.font = font
	
	@themeUpdater
	def _config_setColor(self, font, theme):
		theme.font = font
	
	def _getTheme(self):
		return copy.deepcopy(self._gui.getTheme())
	
	def _setTheme(self, theme):
		self._gui.setTheme(theme)


import vizact
def haltEverything():
	import vizconnect
	for tracker in vizconnect.getTrackerDict().values():
		tracker.setEnabled(viz.TOGGLE)
	for transport in vizconnect.getTransportDict().values():
		transport.getRaw().updateEvent.setEnabled(viz.TOGGLE)
	for tool in vizconnect.getToolDict().values():
		tool.getRaw().updateEvent.setEnabled(viz.TOGGLE)

vizact.onkeydown(viz.KEY_PAUSE, haltEverything)



#	
#	def _config_getTitleBarOnTop(self):
#		return self._theme.titleBarLocation == viz.ALIGN_CENTER_TOP
#	
#	def _config_setTitleBarOnTop(self, state):
#		theme = copy.deepcopy(self._theme)
#		if state:
#			theme.titleBarLocation = viz.ALIGN_CENTER_TOP
#		else:
#			theme.titleBarLocation = viz.ALIGN_CENTER_BOTTOM
#		self.setTheme(theme)
#	
#	def _config_setUseTopBackButton(self, state):
#		theme = copy.deepcopy(self._theme)
#		theme.useTopBackButton = state
#		self.setTheme(theme)
#




#	def _config_setBackColor(self, index, val):
#		theme = copy.deepcopy(self._theme)
#		theme.backColor = [theme.backColor[0], theme.backColor[1], theme.backColor[2], theme.backColor[3]]
#		theme.backColor[index] = val
#		self.setTheme(theme)
#	
#	def _config_setTopColor(self, index, val):
#		theme = copy.deepcopy(self._theme)
#		theme.topBackColor = [theme.topBackColor[0], theme.topBackColor[1], theme.topBackColor[2], theme.topBackColor[3]]
#		theme.topBackColor[index] = val
#		self.setTheme(theme)
#	
#	def _config_setTextColor(self, index, val):
#		theme = copy.deepcopy(self._theme)
#		theme.textColor = [theme.textColor[0], theme.textColor[1], theme.textColor[2], theme.textColor[3]]
#		theme.textColor[index] = val
#		self.setTheme(theme)
#	
#	def _config_setButtonCornerRadius(self, val):
#		theme = copy.deepcopy(self._theme)
#		theme.buttonCornerRadius = val
#		self.setTheme(theme)
#	
#		ui.addBoolItem('title bar on top', self._config_setTitleBarOnTop, self._config_getTitleBarOnTop)
#		ui.addBoolItem('use top back button', self._config_setUseTopBackButton, lambda: self.getTheme().useTopBackButton)
#		
#		ui.addFloatRangeItem('buttonCornerRadius', [0.0, 0.03], self._config_setButtonCornerRadius, lambda: self.getTheme().buttonCornerRadius)
#		
#		ui.addFloatRangeItem('back r', [0.0, 1.0], lambda val: self._config_setBackColor(0, val), lambda: self.getTheme().backColor[0])
#		ui.addFloatRangeItem('back g', [0.0, 1.0], lambda val: self._config_setBackColor(1, val), lambda: self.getTheme().backColor[1])
#		ui.addFloatRangeItem('back b', [0.0, 1.0], lambda val: self._config_setBackColor(2, val), lambda: self.getTheme().backColor[2])
#		ui.addFloatRangeItem('back a', [0.0, 1.0], lambda val: self._config_setBackColor(3, val), lambda: self.getTheme().backColor[3])
#		
#		ui.addFloatRangeItem('top r', [0.0, 1.0], lambda val: self._config_setTopColor(0, val), lambda: self.getTheme().topBackColor[0])
#		ui.addFloatRangeItem('top g', [0.0, 1.0], lambda val: self._config_setTopColor(1, val), lambda: self.getTheme().topBackColor[1])
#		ui.addFloatRangeItem('top b', [0.0, 1.0], lambda val: self._config_setTopColor(2, val), lambda: self.getTheme().topBackColor[2])
#		ui.addFloatRangeItem('top a', [0.0, 1.0], lambda val: self._config_setTopColor(3, val), lambda: self.getTheme().topBackColor[3])
#		
#		ui.addFloatRangeItem('text r', [0.0, 1.0], lambda val: self._config_setTextColor(0, val), lambda: self.getTheme().textColor[0])
#		ui.addFloatRangeItem('text g', [0.0, 1.0], lambda val: self._config_setTextColor(1, val), lambda: self.getTheme().textColor[1])
#		ui.addFloatRangeItem('text b', [0.0, 1.0], lambda val: self._config_setTextColor(2, val), lambda: self.getTheme().textColor[2])
#		ui.addFloatRangeItem('text a', [0.0, 1.0], lambda val: self._config_setTextColor(3, val), lambda: self.getTheme().textColor[3])
