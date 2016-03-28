

class PanelSizeToAction(viz.ActionClass):

	def _applyScale(self, s, object, data, end=False):
		for item in data.shrinkItems:
			item.scale(s)
		
		if end:
			for item in data.shrinkItems:
				item.setVisible(data.endVisibility)
		
		size = object.getSize()
		width = 0
		for child in object.getChildren():
			if child.getVisible():
				width += child.getBoundingBox().width
		print width
		object.setSize([width, size[1]])
	
	def begin(self,object):

		data = self._actiondata_

		beginVal = vizact._paramvec_(data.begin,object)
		if beginVal is None:
			beginVal = object.getScale()
		else:
			self._applyScale(beginVal, object, data)
		for item in data.shrinkItems:
			item.setVisible(data.startVisibility)
		
		endVal = vizact._paramvec_(data.size,object)

		speed = vizact._paramval_(data.speed,object)
		time = vizact._paramval_(data.time,object)
		duration = 0.0
		
		if time is not None:
			duration = time
		elif speed is not None:
			duration = vizmat.Distance(beginVal,endVal) / speed

		if duration <= 0.0:
			self._applyScale(endVal, object, data, end=True)
			self.end(object)
			return

		interpolate = vizact._createActionInterpolator(data,beginVal,endVal)

		#Save elapsed/duration values
		self.elapsed = 0.0
		self.duration = duration

		#Create update function as closure
		def _update(e,object):
			self.elapsed += e
			p = self.elapsed / duration
			if p >= 1.0:
				self._overtime_ = self.elapsed - duration
				self._applyScale(endVal, object, data, end=True)
				self.end(object)
				return
			
			s = interpolate(beginVal,endVal,p)
			self._applyScale(s, object, data)
#			object.setSize([object.getBoundingBox().width+data.theme.borderSize*2+(0.05), size[1]])
		self.update = _update


def panelSizeTo(size,begin=None,speed=None, items=None, theme=None, startVisibility=True, endVisibility=False, time=None, interpolate=None):
	if items is None:
		items = []
	bla = viz.ActionData()
	bla.size = size
	bla.speed = speed
	bla.theme = theme
	bla.time = time
	bla.startVisibility = startVisibility
	bla.endVisibility = endVisibility
	bla.shrinkItems = items
	bla.begin = begin
	bla.interpolate = interpolate
	bla.actionclass = PanelSizeToAction
	return bla


class Movable(object):
	def __init__(self):
		self._movePanelButtonToSelfOffset = vizmat.Vector()
		self._grabberToMovePanelButtonOffset = vizmat.Transform()
	
	def getMinimizedPositionOffset(self, alignment):
		"""Returns the necessary positional offset based on alignment
		
		@return []
		"""
		titleBarSize = self.getSize()
		
		if alignment == viz.ALIGN_CENTER_BOTTOM:
			posOff = [0, titleBarSize[1]/2.0, 0]
		elif alignment == viz.ALIGN_CENTER_TOP:
			posOff = [0, -titleBarSize[1]/2.0, 0]
		else:
			posOff = [0, titleBarSize[1]/2.0, 0]
		return posOff
	
	def getPositionOffset(self, alignment):
		"""Returns the necessary positional offset based on alignment
		
		@return []
		"""
		attachedPanelSize = self._attachedPanel.getSize()
		titleBarSize = self.getSize()
		
		if alignment == viz.ALIGN_CENTER_BOTTOM:
			posOff = [0, (attachedPanelSize[1]/2.0+titleBarSize[1]/2.0), 0]
		elif alignment == viz.ALIGN_CENTER_TOP:
			posOff = [0, -(attachedPanelSize[1]/2.0+titleBarSize[1]/2.0), 0]
		else:
			posOff = [0, (attachedPanelSize[1]/2.0+titleBarSize[1]/2.0), 0]
		return posOff
#	
#	def _repositionWindow(self, alignment=None, posOff=None):
#		"""Repositions the hide panel"""
#		if alignment is None:
#			alignment = self._theme.titleBarLocation
#		with self.getRC():
#			if posOff is None:
#				posOff = self.getPositionOffset(alignment)
#			
#			mat = self.getMatrix(viz.ABS_GLOBAL)
#			posOff = mat.preMultVec(posOff)
#			self._attachedPanel.setPosition(posOff, viz.ABS_GLOBAL)
#			self._attachedPanel.setQuat(mat.getQuat(), viz.ABS_GLOBAL)
#	
#	def _repositionTitleBar(self, alignment=None):
#		"""Repositions the title bar """
#		if alignment is None:
#			alignment = self._theme.titleBarLocation
#		with self.getRC():
#			posOff = -vizmat.Vector(self.getPositionOffset(alignment))
#			
#			self._windowTitleBarLink.reset(viz.RESET_OPERATORS)
#			self._windowTitleBarLink.preTrans(posOff)
	
	def _adjustLocation(self, referenceNode=None):
		"""Adjusts the location of the event menu to match the hand to avatar
		orientation
		"""
		if referenceNode is None:
			referenceNode = self
		if not referenceNode._grabber:
			return
		with self.getRC():
			if not referenceNode._isGrabbed:# first frame, so get the offset
				grabberInvMat = referenceNode._grabber.getMatrix(viz.ABS_GLOBAL).inverse()
				self._grabberToMovePanelButtonOffset = vizmat.Transform(grabberInvMat)
				self._grabberToMovePanelButtonOffset.preMult(referenceNode.getMatrix(viz.ABS_GLOBAL))
				self._movePanelButtonToSelfOffset = -vizmat.Vector(self.getMatrix(viz.ABS_GLOBAL).inverse().preMultVec(referenceNode.getPosition(viz.ABS_GLOBAL)))
				
				# set the position based on the difference
				grabberMat = referenceNode._grabber.getMatrix(viz.ABS_GLOBAL)
				mat = vizmat.Transform(grabberMat)
				
				# eliminate the tracker pos from the transport
				# make a look at matrix using the avatar's z vector
				rot = vizmat.Transform(self._grabberToMovePanelButtonOffset)
				grabberYawMat = vizmat.Transform()
				fv = grabberMat.getForward()
				if abs(vizmat.Vector(fv) * [0, 1, 0]) < 0.9:
					grabberYawMat.makeVecRotVec([0, 0, 1], [fv[0], 0, fv[2]])
				else:
					fv = grabberMat.getSide()
					grabberYawMat.makeVecRotVec([1, 0, 0], [fv[0], 0, fv[2]])
				rot.postMult(grabberYawMat)
				
				mat.setEuler([rot.getEuler()[0], 0, 0])
				self._grabberToMovePanelButtonOffset.setPosition(vizmat.Vector(mat.inverse().preMultVec(referenceNode.getPosition(viz.ABS_GLOBAL))))
			else:
				# set the position based on the difference
				grabberMat = referenceNode._grabber.getMatrix(viz.ABS_GLOBAL)
				mat = vizmat.Transform(grabberMat)
				
				# eliminate the tracker pos from the transport
				# make a look at matrix using the avatar's z vector
				rot = vizmat.Transform(self._grabberToMovePanelButtonOffset)
				grabberYawMat = vizmat.Transform()
				fv = grabberMat.getForward()
				if abs(vizmat.Vector(fv) * [0, 1, 0]) < 0.9:
					grabberYawMat.makeVecRotVec([0, 0, 1], [fv[0], 0, fv[2]])
				else:
					fv = grabberMat.getSide()
					grabberYawMat.makeVecRotVec([1, 0, 0], [fv[0], 0, fv[2]])
				rot.postMult(grabberYawMat)
				
				mat.setEuler([rot.getEuler()[0], 0, 0])
				
				pos = vizmat.Vector(mat.preMultVec(self._movePanelButtonToSelfOffset + self._grabberToMovePanelButtonOffset.getPosition()))
				
				mat = vizmat.Transform(grabberMat)
				mat.preMult(self._grabberToMovePanelButtonOffset)
				grabberYawMat = vizmat.Transform()
				fv = mat.getForward()
				if abs(vizmat.Vector(fv) * [0, 1, 0]) < 0.9:
					grabberYawMat.makeVecRotVec([0, 0, 1], [fv[0], 0, fv[2]])
				else:
					fv = mat.getSide()
					grabberYawMat.makeVecRotVec([1, 0, 0], [fv[0], 0, fv[2]])
				quat = grabberYawMat.getQuat()
				
				self.setQuat(quat, viz.ABS_GLOBAL)
				self.setPosition(pos, viz.ABS_GLOBAL)


class Collapseable(object):
	def __init__(self):
		self._inTransition = False
		self._collapsed = False
	
	def _expandTask(self):
		# re-show collapsed items
#		self._titleBarText.setVisible(True)
		# run expansion
		expandTime = 0.3
		maxAction = panelSizeTo([1, 1, 1],
									begin=[0.00001, 1, 1],
									items=[self._homePanelButton, self._backPanelButton, self._closePanelButton]+self._spacers,
									theme=self._theme,
									startVisibility=True,
									endVisibility=True,
									time=expandTime)
		self.runAction(maxAction)
		yield viztask.waitActionEnd(self, maxAction)
		# expand attached panel
		yield viztask.waitTask(self._expandAttachedPanelTask)
		# change icons
		self._minimizePanelButton.setVisible(True)
		self._maximizePanelButton.setVisible(False)
		self._repositionWindow()
		self._windowTitleBarLink.setEnabled(True)
		# update state
		self._inTransition = False
		self._collapsed = False
		self.refreshLayout()
		self._attachedPanel._refreshSelectables()
	
	def _expandAttachedPanelTask(self):
		expandTime = 0.3
		if self._theme.titleBarLocation == viz.ALIGN_CENTER_TOP:
			targetPos = [0.0,-self._attachedPanel._size[1]/2.0, 0.0]
		else:
			targetPos = [0.0, self._attachedPanel._size[1]/2.0, 0.0]
		
		# reposition the window to match with the title bar
		self._windowTitleBarLink.setEnabled(False)
		self._repositionWindow(posOff=self.getMinimizedPositionOffset(self._theme.titleBarLocation))
		self._attachedPanel.setVisible(True)
		
		minAction = vizact.parallel(vizact.sizeTo([1, 1, 1], time=expandTime),
									vizact.moveTo(vizmat.Vector(self._attachedPanel.getPosition())+targetPos, time=expandTime))
		self._attachedPanel.runAction(minAction)
		yield viztask.waitActionEnd(self._attachedPanel, minAction)
	
	def _shrinkTask(self):
		# collapse attached panel
		yield viztask.waitTask(self._shrinkAttachedPanelTask)
		# run collapse
		expandTime = 0.3
		minAction = panelSizeTo([0.00001, 1.0, 1.0],
									begin=[1, 1, 1],
									items=[self._homePanelButton, self._backPanelButton, self._closePanelButton]+self._spacers,
									theme=self._theme,
									startVisibility=True,
									endVisibility=False,
									time=expandTime)
		self.runAction(minAction)
		yield viztask.waitActionEnd(self, minAction)
#		self._titleBarText.setVisible(False)
		# change icons
		self._maximizePanelButton.setVisible(True)
		self._minimizePanelButton.setVisible(False)
		# update state
		self._inTransition = False
		self._collapsed = True
		self.setVisible(True)
		self.refreshLayout()
		self._attachedPanel._refreshSelectables()
	
	def _shrinkAttachedPanelTask(self):
		expandTime = 0.3
		if self._theme.titleBarLocation == viz.ALIGN_CENTER_TOP:
			targetPos = [0.0, self._attachedPanel._size[1]/2.0, 0.0]
		else:
			targetPos = [0.0,-self._attachedPanel._size[1]/2.0, 0.0]
		
		minAction = vizact.parallel(vizact.sizeTo([1.0, 0.001, 1.0], time=expandTime),
									vizact.moveTo(vizmat.Vector(self._attachedPanel.getPosition())+targetPos, time=expandTime))
		self._attachedPanel.runAction(minAction)
#		self._repositionWindow()
		self._windowTitleBarLink.setEnabled(False)
		yield viztask.waitActionEnd(self._attachedPanel, minAction)
		self._attachedPanel.setVisible(False)
	
	def minimizeWindow(self):
		"""Minimizes the window."""
		with self.getRC():
			if (not self._inTransition
					and not self._collapsed):
				self._inTransition = True
				viztask.schedule(self._shrinkTask)
	
	def maximizeWindow(self):
		"""Minimizes the window."""
		with self.getRC():
			if (not self._inTransition
					and self._collapsed):
				self._inTransition = True
				viztask.schedule(self._expandTask)