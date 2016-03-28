"""Contains grabber tools for embedded gui items"""

import tools
import math

import viz
import vizact
import vizconnect
import vizmat
import vizshape

from addons.interactive_menu import embedded_gui
from addons.interactive_menu import layout
from addons.interactive_menu import menu_highlight


COLLISTION_RAY = 1
COLLISTION_HAND = 2


class GUIAttacher(tools.attacher.Attacher):
	"""An attacher for GUI objects"""
	def __init__(self, *args, **kwargs):
		super(GUIAttacher, self).__init__(*args, **kwargs)
		self._attachedItem = None
	
	def _onAttach(self, dst):
		"""Set attach object"""
		if self._attachedItem != dst:
			self._attachedItem = dst
			return True
		return False
	
	def _onDetach(self, dst):
		"""Removes the attached object."""
		if self._attachedItem == dst:
			self._attachedItem = None
			return True
		return True


class CenterPointForItems(tools.collision_test.DistanceTest):
	"""Measures distance based on the center points of two objects"""
	def getClosest(self, start, list, closestItem=None, closestDistance=-1):
		"""Returns the closest node found along with the distance
		@return (viz.VizNode(), float)
		"""
		startPos = start.getPosition(viz.ABS_GLOBAL)
		for item in list:
			dist = vizmat.Distance(startPos, item.getBoundingSphere(self._mode).center)
			if dist < closestDistance or closestDistance == -1:
				closestItem = item
				closestDistance = dist
		return closestItem, closestDistance
	
	def getAllInRange(self, start, list, threshold):
		"""Returns a list of tuples containing the set of nodes within
		a given range node found along with the distance. If threshold
		is None, then the returned list is not be filtered by distance.
		@return []
		"""
		startPos = start.getPosition(viz.ABS_GLOBAL)
		result = []
		for item in list:
			dist = vizmat.Distance(startPos, item.getBoundingSphere(self._mode).center)
			if threshold is None or dist < threshold:
				result.append((item, dist))
		return result


class RayHand(tools.collision_test.CollisionTester):
	"""Ray-base collision tester. Intersects a node, then stops, then does distance test around intersection
	of the provided node.
	"""
	def __init__(self, node, panel, ignoreBackFace=False, computePath=False, ray=None, lineBeginDist=0.0, lineEndDist=1000.0, distanceThreshold=0.05, *args, **kwargs):
		self._node = node
		self._panel = panel
		
		self._ignoreBackFace = ignoreBackFace
		self._computePath = computePath
		self._lineBeginDist = lineBeginDist
		self._lineEndDist = lineEndDist
		self._ray = ray
		self._distanceThreshold = distanceThreshold
		self._endNode = embedded_gui.Cursor()
		super(RayHand, self).__init__(*args, **kwargs)
		self._distanceTest = CenterPointForItems()
	
	# saving reference for speed testing purposes
#	def _intersectPlaneVectorBased(self, panel, lineBegin, lineEnd):
#		panelMat = panel.getMatrix(viz.ABS_GLOBAL)
#		V0 = vizmat.Vector(panelMat.getPosition())
#		lineBegin = vizmat.Vector(lineBegin)
#		lineEnd = vizmat.Vector(lineEnd)
#		w = lineBegin - V0
#		u = (lineEnd - lineBegin).normalize()
#		n = -vizmat.Vector(panelMat.getForward())
#		den = (n*u)
#		if den == 0:
#			return viz.Data(point=lineBegin, object=None)
#		d = (-n*w) / den
#		intersection = viz.Data(point=lineBegin+(u*d), object=panel)
#		return intersection
	
	def _intersectPlane(self, panel, lineBegin, lineEnd):
		# instead of doing a viz.intersect test, check the intersection with the plane of the panel
		panelMat = panel.getMatrix(viz.ABS_GLOBAL)
		V0 = panelMat.getPosition()
		w = [lineBegin[0] - V0[0],
			lineBegin[1] - V0[1],
			lineBegin[2] - V0[2]]
		d = [lineEnd[0] - lineBegin[0],
			lineEnd[1] - lineBegin[1],
			lineEnd[2] - lineBegin[2]]
		mag = math.sqrt(d[0]*d[0]+d[1]*d[1]+d[2]*d[2])
		u = [d[0]/mag, d[1]/mag, d[2]/mag]#vizmat.Vector(d).normalize()
		n = panelMat.getForward()
		den = -(n[0]*u[0] + n[1]*u[1] + n[2]*u[2])
		if den == 0:
			return viz.Data(point=lineBegin, object=None)
		d = (n[0]*w[0] + n[1]*w[1] + n[2]*w[2]) / den
		o = [u[0]*d, u[1]*d, u[2]*d]
		p = [lineBegin[0]+o[0],
			lineBegin[1]+o[1],
			lineBegin[2]+o[2]]
		return viz.Data(point=p, object=panel)
	
	def _onGet(self, validList):
		"""An internal method which must be implemented in any subclass. It
		returns either a list of items, if self._all is True, or a single tuple
		if False. This function should apply the distanceTest in order to 
		filter/order the objects as appropriate. This method is called by
		getAllInRange and getClosest.
		"""
		# get a list of all the items intersected
		mat = self._node.getMatrix(viz.ABS_GLOBAL)
		lineBegin = mat.preMultVec([0, 0, self._lineBeginDist])
		lineEnd = mat.preMultVec([0, 0, self._lineEndDist])
		
		if self._ray is not None:
			self._ray.setStart(lineBegin)
			self._ray.setEnd(lineEnd)
		
		intersection = self._intersectPlane(self._panel, lineBegin, lineEnd)
		
		if intersection.object is not None and intersection.object.id != -1 and hasattr(intersection.object, 'getTheme'):
			self._ray.setEnd(intersection.point)
			self._endNode.setPosition(intersection.point, viz.ABS_GLOBAL)
			self._endNode.setQuat(intersection.object.getRoot().getVizNode().getQuat(viz.ABS_GLOBAL), viz.ABS_GLOBAL)
		
		if intersection.object is not None and intersection.object.id != -1:
			for node in validList:
				if node.holdsPoint(intersection.point):
					return (node, vizmat.Distance(self._endNode.getPosition(viz.ABS_GLOBAL), node.getBoundingSphere(viz.ABS_GLOBAL).center))
		
		return (None, -1)
	
	def remove(self):
		self._endNode.remove()


class GUIGrabber(tools.grabber.AbstractGrabber):
	LOCK_HOVER = 4#TODO remove after 5.2 release
	
	"""A grabber class for grabbing GUI items"""
	def __init__(self,
					highlightObject,
					panel,
					collisionTestFlag=COLLISTION_HAND|COLLISTION_RAY,
					**kwargs):
		self._panel = panel
		
		self._previewRay = None
		self._previewObject = None
		self._lastHighlightedObject = None
		self._heldIntersection = None
		vizconnect.getAvatar().getRaw().disable(viz.INTERSECTION)
		self._collisionTestFlag = collisionTestFlag
		self._cursor = None
		self._hoverStartObject = None
		self._hoverStartTime = -1
		self._hoverTime = 2.0
		
		with viz.MainResourceContext:
			self._clickSound = viz.add('resources/sounds/click.wav')
			self._clickSound.stop()
			
			node = viz.addGroup()
			attachmentObj = GUIAttacher(src=node, multiAttach=False)
			self._placer = tools.placer.MidAir()
			
			collisionTester = None
			
			# make a hand tester
			self._handTester = tools.collision_test.Distance(node=node, distanceThreshold=0.3)
			# make a ray tester
			self._ray = tools.ray_caster.SimpleRay()
			self._ray._ray.disable(viz.INTERSECTION)
			self._ray.visible(False)
			group = viz.addGroup()
			group.disable(viz.INTERSECTION)
			group.setParent(node)
			self._rayTester = RayHand(node=group, panel=self._panel, ray=self._ray)
			self._cursor = self._rayTester._endNode
			
			if self._collisionTestFlag&COLLISTION_RAY:
				collisionTester = self._rayTester
			if self._collisionTestFlag&COLLISTION_HAND:
				collisionTester = self._handTester
			
			super(GUIGrabber, self).__init__(node=node,
												collisionTester=collisionTester,
												attacher=attachmentObj,
												placer=self._placer,
												highlighter=highlightObject,
												useToolTag=False)
#			self.updateEvent.remove()
#			self.updateEvent = vizact.onupdate(viz.PRIORITY_LINKS-1, self.onUpdate)
	
	def finalize(self):
		"""Finalizes the grabbing"""
		with viz.MainResourceContext:
			super(GUIGrabber, self).finalize()
			grabbedItem = self._attacher.getDst()
			if self._held and grabbedItem is not None:
				grabbedItem.hold()
			self._highlighter.updateHighlightLinks()
			
			if self._lastHighlightedObject != self._hoverStartObject:
				if self._frameLocked&self.LOCK_HOVER:
					self._hoverEnd()
				self._hoverStartObject = self._lastHighlightedObject
				self._hoverStartTime = viz.getFrameTime()
			elif self._hoverStartObject:
				if viz.getFrameTime() - self._hoverStartTime > self._hoverTime:
					self._hover()
	
	def _hover(self):
		if not self._frameLocked&self.LOCK_HOVER:
			self._hoverStartObject.hover()
		self._lockRequested |= self.LOCK_HOVER
	
	def _hoverEnd(self):
		self._hoverStartObject.hoverEnd()
	
	def getCursor(self):
		return self._cursor
	
	def getIntersection(self):
		"""Returns the intersected object.
		
		@return GUINode()
		"""
		with viz.MainResourceContext:
			for grabberWrapper in vizconnect.getToolsWithMode('Grabber'):
				if grabberWrapper.getRaw().getAttacher().getDst():
					return None
			
			grabbedItem = None
			# test ray casting intersection (iff applicable) HEAVIER
			if self._collisionTestFlag&COLLISTION_RAY:
				self._collisionTester = self._rayTester
				if self._useToolTag:
					grabbedItem, dist = self._collisionTester.get(tag=tools.TAG_GRAB)
				else:
					grabbedItem, dist = self._collisionTester.get()
			# test hand intersection if applicable and if no grabbing intersection found
			# setting self._collisionTester in case of success 
			if (grabbedItem is None) and self._collisionTestFlag&COLLISTION_HAND:
				self._collisionTester = self._handTester
				if self._useToolTag:
					grabbedItem, dist = self._collisionTester.get(tag=tools.TAG_GRAB)
				else:
					grabbedItem, dist = self._collisionTester.get()
			
			# if the grabbedItem is different, update the current grabbedItem
			if grabbedItem != self._currentIntersection:
				self._updateHighlight(grabbedItem)
				# send out an event
				viz.sendEvent(tools.grabber.UPDATE_INTERSECTION_EVENT, viz.Event(grabber=self, new=grabbedItem, old=self._currentIntersection))
				# save the new grabbedItem
				self._currentIntersection = grabbedItem
			
			if not self._frameLocked&self.LOCK_HOLD:
				if not self._held:
					if grabbedItem != self._lastHighlightedObject:
						if grabbedItem:
							grabbedItem.highlight()
							self._updateHighlight(grabbedItem)
						# disable proxy items for tools when highlighting menu item
						self._setOtherToolsEnabled(grabbedItem is None)
					self._lastHighlightedObject = grabbedItem
			return grabbedItem
	
	def grabAndHold(self):
		"""Grabs and holds"""
		if not self._frameLocked&self.LOCK_HOLD:
			if not self._held and not self.getIntersection():
				found = False
				for proxyWrapper in vizconnect.getToolsWithMode('Proxy'):
					rawProxy = proxyWrapper.getRaw()
					rawProxy._updateFunction(rawProxy)
					for obj, _ in rawProxy._functionQueueDict.iteritems():
						if obj and obj.id != -1:
							if rawProxy._functionQueueDict[obj]:
								found = True
							rawProxy._functionQueueDict[obj] = []
				if found:
					self._lockRequested |= self.LOCK_HOLD
					return
			self._held = self.grab()
			self._heldIntersection = self._held
		
		if self._held:
			intersection = self.getIntersection()
			if intersection != self._heldIntersection:
				if self._held != intersection:
					self.getHighlight().setVisible(self._held, False)
				else:
					self.getHighlight().setVisible(self._held, True)
				self._heldIntersection = intersection
		
		self._lockRequested |= self.LOCK_HOLD
	
	def applyTheme(self, theme):
		self._collisionTestFlag = theme.collisionTestFlag
		self._cursor.setVisible(self._collisionTestFlag&COLLISTION_RAY!=0)
	
	def setItems(self, *args, **kwargs):
		"""Sets the list of grabbable items"""
		super(GUIGrabber, self).setItems(*args, **kwargs)
		self._updateHighlight(None)
		self.getIntersection()
		if self._rayTester:
			self._rayTester.setItems(self._items)
		if self._handTester:
			self._handTester.setItems(self._items)
	
	def grab(self):
		"""Triggers a grab/hold action. Returns the grabbed object.
		
		@return GUINode()
		"""
		with viz.MainResourceContext:
			grabbedItem = super(GUIGrabber, self).grab()
			if grabbedItem:
				grabbedItem.grab(monitorRelease=False, highlight=self.getHighlight(), grabber=self)
				self._clickSound.play()
			return grabbedItem
	
	def release(self):
		"""Triggers a release action. Returns the released object.
		
		@return GUINode()
		"""
		with viz.MainResourceContext:
			releasedItem = super(GUIGrabber, self).release()
			if releasedItem:
				releasedItem.release(silent=(self._held != self._heldIntersection))
			self._heldIntersection = None
			return releasedItem
	
	def silentRelease(self):
		"""Forces a release of the grabbed object, but does not trigger a
		released callback.
		
		@return GUINode()
		"""
		with viz.MainResourceContext:
			releasedItem = super(GUIGrabber, self).release()
			if releasedItem:
				releasedItem.release(silent=True)
			self._setOtherToolsEnabled(True)
			return releasedItem
	
	def remove(self):
		"""Removes the grabber object"""
		with viz.MainResourceContext:
			super(GUIGrabber, self).remove()
			self._node.remove()
			self._attacher.remove()
			self._placer.remove()
			if self._highlighter:
				self._highlighter.remove()
			if self._previewRay:
				self._previewRay.remove()
				self._previewRay = None
			if self._previewObject:
				self._previewObject.remove()
				self._previewObject = None
			if self._rayTester:
				self._rayTester.remove()
				self._rayTester = None
			if self._handTester:
				self._handTester.remove()
				self._handTester = None
	
	def _setOtherToolsEnabled(self, state):
		"""Sets other tools enabled/disabled state must be True or False"""
		# TODO: slight hack for grabber since it's grabber specific code
		if state:
			for proxyWrapper in vizconnect.getToolsWithMode('Proxy'):
				proxyWrapper.getRaw().updateEvent.setEnabled(True)
			for grabberWrapper in vizconnect.getToolsWithMode('Grabber'):
				intersection = grabberWrapper.getRaw().getIntersection()
				if intersection is not None:
					grabberWrapper.getRaw().getHighlight().setVisible(intersection, True)#	def visible(self, *args, **kwargs):
		else:
			for proxyWrapper in vizconnect.getToolsWithMode('Proxy'):
				proxyWrapper.getRaw().updateEvent.setEnabled(False)
			for grabberWrapper in vizconnect.getToolsWithMode('Grabber'):
				grabberWrapper.getRaw().getHighlight().setVisible(None, False)
#		if self._collisionTestFlag&COLLISTION_RAY:
#			self._collisionTester.visible(*args, **kwargs)


class Grabbable(object):
	def __init__(self):
		self._proxyList = []
		with self.getRC():
			self._eventManager = viz.EventClass()
			self._eventManager.callback(viz.getEventID('EMBEDDED_GUI_CLEAR_SELECTION_TOOLS'), self.removeSelectionTools)
	
	def addSelectionTools(self, collisionTestFlag=COLLISTION_HAND|COLLISTION_RAY):
		"""Adds the selection tools to be used with this GUI."""
		with self.getRC():
			vcProxyList = vizconnect.getToolsWithMode('Proxy')
			self._proxyList = []
			# duplicate the proxy list
			nameList = []
			for vcProxy in vcProxyList:
				rawProxy = tools.proxy.Proxy()
				rawProxy.setUpdateFunction(vcProxy.getRaw().getUpdateFunction())
				rawProxy.updateEvent.remove()
				rawProxy.updateEvent = vizact.onupdate(viz.PRIORITY_LINKS-1, rawProxy.onUpdate)
				rawProxy.setParent(vcProxy.getParent().getNode3d())
				rawProxy.disable(viz.INTERSECTION)
				self._proxyList.append(rawProxy)
				nameList.append(vcProxy.getName())
			self._selectionTools = self._createProxyBasedGrabbers(nameList,
																	theme=self.getTheme(),
																	collisionTestFlag=collisionTestFlag)
			for i, rawProxy in enumerate(self._proxyList):
				selectionTool = vizconnect.getTool('panel_{}_highlight_tool_based_on_{}'.format(self.id, nameList[i]))
				rawProxy.setCallback(selectionTool.getRaw(), selectionTool.getRaw().grabAndHold, 1)
			self._refreshSelectables()
	
	def getRC(self):
		return viz.MainResourceContext
	
	def _createProxyBasedGrabbers(self,
									nameList,
									theme,
									collisionTestFlag):
		"""Creates the proxy-based grabber objects for the menu, will not create
		the objects if they already exists. Returns a full list of grabber objects
		not just those created.
		
		@return []
		"""
		# set the grabbable items on the highlight tool, fix
		with self.getRC():
			selectionTools = []
			for proxyName in nameList:
				toolDict = vizconnect.getToolDict()
				grabberName = 'panel_{}_highlight_tool_based_on_{}'.format(self.id, proxyName)
				if grabberName in toolDict:
					highlightWrapper = toolDict[grabberName]
				else:
					selectionTool = GUIGrabber(highlightObject=menu_highlight.QuadHighlight(theme=theme),
												panel=self,
												collisionTestFlag=collisionTestFlag)
					cursor = selectionTool.getCursor()
					self.setCursor(cursor)
					selectionTool.updateEvent.setEnabled(False)
					highlightWrapper = vizconnect.addTool(raw=selectionTool,
														name=grabberName,
														make='Virtual',
														model='Highlighter')
					# parent the highlight wrapper to the proxy's parent
					highlightWrapper.setParent(vizconnect.getTool(proxyName).getParent())
				
				selectionTools.append(highlightWrapper)
			return selectionTools
	
	def removeSelectionTools(self):
		"""Removes the selection tools used by this GUI"""
		with self.getRC():
			for proxyTool in self._proxyList:
				proxyTool.remove()
			self._proxyList = []
			for selectionTool in self._selectionTools:
				selectionTool.remove()
			self._selectionTools = []
	
	def remove(self):
		self._eventHandler.unregister()




