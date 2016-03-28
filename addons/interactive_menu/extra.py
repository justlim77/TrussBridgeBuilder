


#class HideAvatarToggleButton(Panel):
#	"""*MSS
#	Class for text buttons. Text surrounded by a panel item.
#	"""
#	def __init__(self, size, text, **kwargs):
#		self._text = text
#		
#		super(HideAvatarToggleButton, self).__init__(size=size, padding=0.002, **kwargs)
#		
#		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
#									horizontalAlignment=layout.ALIGN_CENTER))
#		
#		# add a text node
#		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
#		interiorSize = self.getInteriorSize()
#		self._textNode.setSize([interiorSize[0]*0.9, interiorSize[1]*0.75])
#		self.addChild(self._textNode)
#		
#		self._trueText = 'Hide Avatar'
#		self._falseText = 'Show Avatar'
#		self._state = False
#		with self.getRC():
#			self._updateEvent = vizact.onupdate(100, self._test)
#		
#		self.refreshLayout()
#		
#		# add/overwrite the necessary functions to the self
#		def addHighlight(_):
#			"""Adds a highlight"""
#			pass
#		self.addHighlight = addHighlight
#		def removeHighlight(_):
#			"""Removes a highlight"""
#			pass
#		self.removeHighlight = removeHighlight
#		def getHighlightVisible(_):
#			"""Gets a highlight visible"""
#			return True
#		self.getHighlightVisible = getHighlightVisible
#		def setHighlightVisible(self, state):
#			"""Sets a highlight visible"""
#			if state == viz.TOGGLE:
#				state = not self.getHighlightVisible()
#			if not state:
#				with self.getRC():
#					menu_highlight.dim(self._textNode, self.getTheme().dimAmount)
#					menu_highlight.dim(self, self.getTheme().dimAmount)
#					menu_highlight.dim(self._quadInterior, 1.0)
#			else:
#				with self.getRC():
#					menu_highlight.dim(self._textNode, 1.0)
#					menu_highlight.dim(self, 1.0)
#					menu_highlight.dim(self._quadInterior, 1.0)
#		self.setHighlightVisible = setHighlightVisible
#	
#	def getSelectables(self):
#		"""Returns a list of selectable objects.
#		
#		@return []
#		"""
#		return [self]
#	
#	def remove(self, *args, **kwargs):
#		"""Removes the GUI node."""
#		with self.getRC():
#			self._updateEvent.remove()
#		super(HideAvatarToggleButton, self).remove()
#	
#	def _test(self):
#		"""Tests the true'ness of the button"""
#		if vizconnect.getAvatar().getNode3d().getVisible() != self._state:
#			self._state = not self._state
#			if self._state:
#				self._textNode.setText(self._trueText)
#			else:
#				self._textNode.setText(self._falseText)
#	
#	def _applyTheme(self, theme):
#		"""Applies the given theme, if applicable"""
#		localTheme = copy.deepcopy(theme)
#		localTheme.cornerRadius = localTheme.buttonCornerRadius
#		localTheme.borderColor = localTheme.textColor
#		return super(HideAvatarToggleButton, self)._applyTheme(localTheme)



class BackButton(PanelButton):
	def __init__(self, text, size, **kwargs):
		panel = Group(size=size)
		panel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
											horizontalAlignment=layout.ALIGN_CENTER))
		texture = viz.add('resources/icons/back.png')
		self._imageNode = TextureQuad(maxSize=[size[0]*0.4, size[1]*0.8],
													texture=texture)
		panelTextWrapper = Group(size=[size[0]*0.6, size[1]],
														margin=[0, 0, 0, 0.01])
		panelTextWrapper.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
														horizontalAlignment=layout.ALIGN_CENTER))
		panelTextWrapper.addChild(Text(text=text))
		panel.addChild(self._imageNode)
		panel.addChild(panelTextWrapper)
		
		super(BackButton, self).__init__(size=size,
											panel=panel,
											monitorRelease=False,
											**kwargs)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		self._imageNode.color(localTheme.textColor)
		return super(BackButton, self)._applyTheme(localTheme)


