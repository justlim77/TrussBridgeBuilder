"""Contains code for embedded (3d) GUI items"""

import collections
import copy
import math
import os
import textwrap

import viz
import vizconnect
import vizmat
import vizact
import vizshape
import viztask

from addons.interactive_menu import layout
from addons.interactive_menu import menu_highlight
import tools

import themes


SHOW_MENU_EVENT = viz.getEventID('SHOW_MENU_EVENT')
MOVE_MENU_EVENT = viz.getEventID('MOVE_MENU_EVENT')
STENCIL_MODE_TOP_LEVEL = 1
STENCIL_MODE_HIERARCHY = 2
STENCIL_MODE = STENCIL_MODE_HIERARCHY

RENDER_OFFSET_DISABLED = 5
RENDER_OFFSET_OVERLAY = 6
RENDER_OFFSET_HIGHLIGHT = 7
RENDER_OFFSET_OUTLINE = 8
RENDER_OFFSET_CURSOR = 9

MAX_DRAW_DEPTH_OFFSET = 50000
BASE_OFFSET = 10

BUTTON_OK = 1
BUTTON_CANCEL = 2
BUTTON_NEXT = 4
BUTTON_BACK = 8
BUTTON_MIN_MAX = 16
BUTTON_HOME = 32

SIZE_MODE_METERS = 1
SIZE_MODE_PERCENT_PARENT = 2
SIZE_MODE_PERCENT_REMAINING = 4
SIZE_MODE_SYNC = 8
SIZE_MODE_THEME = 16
SIZE_MODE_FUNCTION = 32

STATUS_OVERLAY_ID = 'OVERLAY_STATUS'

_T = 0
_R = 1
_B = 2
_L = 3

viz.res.addPath(os.path.dirname(__file__))



def _getScale(maxSize, aspect):
	"""Returns a scale that fits a given max size and aspect ratio.
	
	@return float
	"""
	# height is greater
	if maxSize[0] and maxSize[1]:
		# fit max height
		scale = min(float(maxSize[0])/aspect, float(maxSize[1]))
	elif maxSize[0]:
		# no max size in width so resize to fit height
		scale = float(maxSize[0])/aspect
	elif maxSize[1]:
		# no max size in height so resize to fit width
		scale = float(maxSize[1])
	else:
		scale = 1.0
	return scale


def _addQuad(size=(1.0, 1.0), axis=-vizshape.AXIS_Z, cullFace=False, cornerRadius=0.0, **kw):
	"""Add a quad"""
	w = size[0]/2.0
	h = size[1]/2.0
	
	radius = viz.clamp(cornerRadius, 0.0, min(w, h))
	
	s = vizshape._Shape()
	
	if radius > 0.0:
		step = 5
	else:
		step = 90
	
	s.begin(viz.TRIANGLE_FAN)
	
	s.normal([0, 0, -1])
	
	#Helper function for adding vertex with computed tex coord
	width = float(size[0])
	height = float(size[1])
	def _vertex(x, y):
		"""Makes a vertex for the shape"""
		s.texCoord([(x+w) / width, (y+h) / height])
		s.vertex([x, y, 0])
	
	#Center of quad
	_vertex(0, 0)
	
	#Upper left corner
	for deg in range(0, 90+step, step):
		x = math.sin(viz.radians(deg)) * radius
		y = math.cos(viz.radians(deg)) * radius
		_vertex(-w+radius-x, h-radius+y)
	
	#Lower left corner
	for deg in range(0, 90+step, step):
		x = math.cos(viz.radians(deg)) * radius
		y = math.sin(viz.radians(deg)) * radius
		_vertex(-w+radius-x, -h+radius-y)
	
	#Lower right corner
	for deg in range(0, 90+step, step):
		x = math.sin(viz.radians(deg)) * radius
		y = math.cos(viz.radians(deg)) * radius
		_vertex(w-radius+x, -h+radius-y)
	
	#Upper right corner
	for deg in range(0, 90+step, step):
		x = math.cos(viz.radians(deg)) * radius
		y = math.sin(viz.radians(deg)) * radius
		_vertex(w-radius+x, h-radius+y)
	
	#Close out fan
	_vertex(-w+radius, h)
	
	_axisEulerDict = { +vizshape.AXIS_X : [-90, 0, 0]
					, -vizshape.AXIS_X : [90, 0, 0]
					, +vizshape.AXIS_Y : [0, 90, 0]
					, -vizshape.AXIS_Y : [0, -90, 0]
					, +vizshape.AXIS_Z : [180, 0, 0]
					, -vizshape.AXIS_Z : [0, 0, 0] }
	s.transform(viz.Matrix.euler(_axisEulerDict.get(axis, [0, 0, 0])))
	
	return s.end(cullFace=cullFace, **kw)


def _updateQuad(s, size=(1.0, 1.0), cornerRadius=0.0):#, axis=-AXIS_Z#, cullFace=False
	"""Update a quad"""
	w = size[0]/2.0
	h = size[1]/2.0
	
	radius = viz.clamp(cornerRadius, 0.0, min(w, h))
	s.clearVertices()
	
	if radius > 0.0:
		step = 5
	else:
		step = 90
	
	#Helper function for adding vertex with computed tex coord
	width = float(size[0])
	height = float(size[1])
	def _vertex(x, y):
		"""Makes a vertex for the shape"""
		texCoord = [(x+w) / width, (y+h) / height]
		s.addVertex([x, y, 0], texCoord=texCoord)
	
	#Center of quad
	_vertex(0, 0)
	
	#Upper left corner
	for deg in range(0, 90+step, step):
		x = math.sin(viz.radians(deg)) * radius
		y = math.cos(viz.radians(deg)) * radius
		_vertex(-w+radius-x, h-radius+y)
	
	#Lower left corner
	for deg in range(0, 90+step, step):
		x = math.cos(viz.radians(deg)) * radius
		y = math.sin(viz.radians(deg)) * radius
		_vertex(-w+radius-x, -h+radius-y)
	
	#Lower right corner
	for deg in range(0, 90+step, step):
		x = math.sin(viz.radians(deg)) * radius
		y = math.cos(viz.radians(deg)) * radius
		_vertex(w-radius+x, -h+radius-y)
	
	#Upper right corner
	for deg in range(0, 90+step, step):
		x = math.cos(viz.radians(deg)) * radius
		y = math.sin(viz.radians(deg)) * radius
		_vertex(w-radius+x, h-radius+y)
	
	#Close out fan
	_vertex(-w+radius, h)
	
	return s


class GUINode(viz.VizNode):
	"""A base GUI node class"""
	def __init__(self, node=None,
					size=None,
					padding=None,
					margin=None,
					theme=None,
					internalDepth=0,
					sizeMode=None,
					sizeReference=None,
					baseOffset=BASE_OFFSET,
					baseDepthOffset=MAX_DRAW_DEPTH_OFFSET):
		
		self._baseDepthOffset = baseDepthOffset
		
		self._tt = None
		self._tooltipsEnabled = True
		self._pageDict = {}
		self._pageHistoryStack = []
		self._pageParent = None
		
		if sizeMode is None:
			sizeMode = [SIZE_MODE_METERS]*2
		self._sizeMode = sizeMode
		
		if sizeReference is None:
			sizeReference = [1.0]*2
		self._sizeReference = sizeReference
		
		self._node = node
		
		self._root = self
		self._isGroup = False
		# padding for the object for internal items
		if padding is None:
			padding = [0, 0, 0, 0]
		if not viz.islist(padding):
			padding = [padding]*4
		else:
			while len(padding) < 4:
				padding += [0]
		self._padding = padding[:]
		
		if theme is None:
			theme = themes.getDarkTheme()
		self._theme = copy.deepcopy(theme)
		self._localTheme = copy.deepcopy(theme)
		
		# margin
		if margin is None:
			margin = [0, 0, 0, 0]
		if not viz.islist(margin):
			margin = [margin]*4
		else:
			while len(margin) < 4:
				margin += [0]
		self._margin = margin[:]
		
		self._postChildrenDrawIndex = 0
		
		self._overlayStack = []
		
		with self.getRC():
			super(GUINode, self).__init__(id=self._node.id)
#			self.appearance(viz.TEXDECAL)
#		self.disable(viz.INTERSECTION)
		self.disable(viz.LIGHTING)
		
		if size is None:
			bb = self.getBoundingBox()
			size = [bb.width, bb.height]
		self._size = self._getConstrainedSize(size)
		self._baseOffset = baseOffset
		
		self._internalDepth = internalDepth
		
		self._cursor = None
		
		self._drawOrderIndex = 0
		self._stencilDepth = 0
		self._disabled = False
		self._disableMask = None
		self._overlay = None
		self._overlayParent = None
		self._parent = viz.WORLD
		self._children = []
		self._scale = 1.0
		self._layout = None
		self._prevSelectables = []
		self._selectionTools = []
		self._refreshSGDepth()
	
	def addChild(self, child, **kwargs):
		"""Adds a child object, redirects to setParent"""
		child.setParent(self, **kwargs)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		return theme
	
	def disable(self, *args, **kwargs):
		"""Disables the node"""
		with self.getRC():
			self._node.disable(*args, **kwargs)
	
	def enable(self, *args, **kwargs):
		"""Disables the node"""
		with self.getRC():
			self._node.enable(*args, **kwargs)
	
	def drawOrder(self, *args, **kwargs):
		"""Overwritten drawOrder.
		
		NOTE: drawOrders set for non GUINode parents of GUINodes can cause issues 
		unless the draw order is explicitly set for the GUINode as well.
		"""
		self._refreshSGDepth()
	
	def getBoundingBox(self, *args, **kwargs):
		"""Returns the bouding box for the VizNode
		
		@return viz.BoundingBox()
		"""
		with self.getRC():
			return viz.VizNode.getBoundingBox(self, *args, **kwargs)
	
	def holdsPoint(self, pos):
		"""Returns true if the node holds the given point.
		
		@return bool
		"""
		with self.getRC():
			if self.getParent() != viz.WORLD:
				pos = self.getParent().getMatrix(viz.ABS_GLOBAL).inverse().preMultVec(pos)
			bb = self.getBoundingBox()
			if (pos[0] > bb.xmin and pos[0] < bb.xmax
					and pos[1] > bb.ymin and pos[1] < bb.ymax):
				return True
		return False
	
	def getBoundedBoundingBox(self):
		"""Returns a bounding box for the node bounded by the size of the object
		
		@return viz.BoundingBox()
		"""
		with self.getRC():
			for child in self._children:
				viz.VizNode.setParent(child, viz.WORLD)
		bb = self.getBoundingBox()
		bb.width = min(bb.width, self._size[0])
		bb.height = min(bb.height, self._size[1])
		bb.size = [bb.width, bb.height, bb.depth]
		with self.getRC():
			for child in self._children:
				viz.VizNode.setParent(child, self)
		return bb
	
	def getChildren(self):
		"""Returns the list of child nodes
		
		@return []
		"""
		return self._children[:]
	
	def getContainerNode3d(self):
		"""Returns the vizard node used as a rendering container
		
		@return viz.VizNode()
		"""
		return self._node
	
	def getDisabled(self):
		"""Returns whether or not this node is disabled.
		
		@return bool
		"""
		return self._disabled
	
	def getInteriorCenter(self):
		"""Returns the center of the node for placing child objects.
		
		@return []
		"""
		return [(self._padding[_L]-self._padding[_R])/2.0, (self._padding[_B]-self._padding[_T])/2.0, 0]
	
	def getInteriorSize(self):
		"""Returns the size available for placing child objects.
		
		@return []
		"""
		return [
			self._size[0] - (self._padding[_L] + self._padding[_R]),
			self._size[1] - (self._padding[_T] + self._padding[_B])
		]
	
	def getInternalDepth(self):
		"""Returns the internal depth added as an offset to child objects, for stenciling
		and depth testing.
		
		@return int
		"""
		return self._internalDepth
	
	def getLayout(self):
		"""Returns the layout of the node.
		
		@return layout.BaseLayout()
		"""
		return self._layout
	
	def getMinSize(self):
		"""Returns the min size for the GUINode
		
		@return []
		"""
		return [0.001+self._padding[_R]+self._padding[_L],
				0.001+self._padding[_T]+self._padding[_B]]
	
	def getMargin(self):
		"""Returns the padding placed between items.
		
		@return []
		"""
		return self._margin[:]
	
	def getPadding(self):
		"""Returns the padding placed between items.
		
		@return []
		"""
		return self._padding[:]
	
	def getParent(self):
		"""Returns the assigned parent GUINode node.
		
		@return GUINode()
		"""
		return self._parent
	
	def getVizNode(self):
		"""Returns the vizard node for the gui item
		
		@return viz.VizNode()
		"""
		return self._node
	
	def getRC(self):
		"""Returns the resource context used by this object.
		
		@return viz.VizResourceContext()
		"""
#		if self._parent != viz.WORLD:
#			return self._parent.getRC()
#		else:
#			return None
		return viz.MainResourceContext
	
	def getRoot(self):
		"""Returns the root GUINode object"""
		root = self._root
		if root._overlayParent:
			root = root._overlayParent.getRoot()
		return root
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self._overlay:
			return self._overlay.getSelectables()
		selectableList = []
		for child in self._children:
			if not child.getDisabled():
				selectableList += child.getSelectables()
		return selectableList
	
	def getSize(self):
		"""Returns the size (not scale) of the GUI object.
		
		return []
		"""
		return self._size[:]
	
	def getSizeMode(self):
		"""Returns the size mode of the object.
		
		return int
		"""
		return self._sizeMode
	
	def getTheme(self):
		"""Returns the theme used by the object.
		
		@return viz.Theme()
		"""
		return self._theme
	
	def insertChild(self, index, child):
		"""Sets the child at the given index for sorting gui layouts. None can
		be used to place the child at the end of the list. Will add the child
		if not already parented to this object.
		"""
		if child not in self._children:
			self.addChild(child)
		self._children.remove(child)
		if index is None:
			self._children.append(child)
		else:
			self._children.insert(index, child)
		self.refreshLayout()
	
	def refreshLayout(self, recurse=True):
		"""Refreshes the layout of the GUI."""
		if recurse:
			for child in self._children:
				child.refreshLayout()
		if self._layout:
			self._layout.refresh(self, self._children)
			if self._overlay:
				self._layout.refresh(self, [self._overlay])
				self._overlay.refreshLayout()
	
	def remove(self, *args, **kwargs):
		"""Removes the GUI node."""
		self.setParent(viz.WORLD)
		with self.getRC():
			self._node.remove(*args, **kwargs)
	
	def removeChild(self, child, delete=False):
		"""Removes a specific GUI child object. By default this only removes
		the child object from the list of children. Setting delete to True
		will also remove the object.
		"""
		self._children.remove(child)
		with self.getRC():
			child.getVizNode().setParent(viz.WORLD)
		child._parent = viz.WORLD
		if delete:
			child.remove()
	
	def removeChildren(self, delete=False):
		"""Removes all GUI child objects. By default this only removes
		the children. Setting delete to True will also remove the object.
		"""
		while self._children:
			self.removeChild(self._children[0], delete=delete)
	
	def back(self):
		"""Moves back to the previous page in the history"""
		if len(self._pageHistoryStack) > 1:
			self._pageHistoryStack.pop(-1)
			self.showPage(self._pageHistoryStack[-1])
			if self._backCallbackFunction:
				self._backCallbackFunction()
		#self.removeOverlay(self._overlay.overlayId)
	
	def home(self):
		"""Moves to the home, or bottom page in the stack."""
		homePage = self._pageHistoryStack[0]
		if len(self._pageHistoryStack) <= 1:
			return
		self._pageHistoryStack = []
		self.showPage(homePage)
		#self.removeOverlay(self._overlay.overlayId)
	
	def removeOverlay(self, overlayId, delete=True, hideOverlaid=True):
		"""Removes and deletes the overlay object"""
		if self._overlay:
			# find items to remove
			removeList = [o for o in self._overlayStack if o.overlayId == overlayId]
			# find items to keep
			self._overlayStack = [o for o in self._overlayStack if o.overlayId != overlayId]
			
			# if the top one matches remove it, pop it off, etc
			if self._overlay.overlayId == overlayId:
				self._overlay = None
				self.setDisabled(False)
				if self._overlayStack:
					self._overlayStack[-1].setVisible(True)
					self._setOverlay(self._overlayStack[-1].overlayId, self._overlayStack[-1])
				self._refreshSelectables()
			
			if delete:
				for overlay in removeList:
					overlay.remove()
		if hideOverlaid:
			self._hideOverlaid()
	
	def removeAllOverlays(self):
		"""Removes and deletes all overlay objects"""
		for overlay in self._overlayStack:
			overlay.remove()
		self._overlayStack = []
		self.setDisabled(False)
		self._refreshSelectables()
	
	def setCursor(self, cursor):
		"""Sets the cursor used for the menu"""
		self._cursor = cursor
		if self._cursor:
			with self.getRC():
				self._cursor.getVizNode().setParent(self)
			self._cursor.disable(viz.DEPTH_TEST)
			self._cursor.setTheme(self._theme)
		self._refreshSGDepth()
	
	def setDisabled(self, state):
		"""Sets the disable state of the node."""
		if state == viz.TOGGLE:
			state = not self._disabled
#		if state:
#			menu_highlight.dim(self, 2.0, off=[0.5]*3)
#		else:
#			menu_highlight.dim(self, 1.0)
			self._disabled = state
#			if self._disabled:
#				self._disableMask = self._getDisabledMask()
#				self._disableMask.setVisible(True)
#			else:
#				self._disableMask.setVisible(False)
#			self._refreshDisabled()
			self._refreshSGDepth()
	
#	def _refreshDisabled(self):
#		"""Refresh the disabled mask for the node"""
#		with self.getRC():
#			stencilFunction = viz.StencilFunc()
#			stencilFunction.funcRef = self._stencilDepth
#			stencilFunction.func = viz.GL_LEQUAL
#			stencilFunction.zpass = viz.GL_KEEP
#			self._disableMask.stencilFunc(stencilFunction)
#			self._disableMask.drawOrder(self._baseDepthOffset+self._postChildrenDrawIndex+RENDER_OFFSET_DISABLED)
	
	def setLayout(self, newLayout):
		"""Sets the layout used by the GUI for arranging items."""
		self._layout = newLayout
	
	def setMargin(self, margin):
		"""Sets the padding placed between items.
		"""
		if margin is None:
			margin = [0, 0, 0, 0]
		if not viz.islist(margin):
			margin = [margin]*4
		else:
			while len(margin) < 4:
				margin += [0]
		self._margin = margin[:]
	
	def addPage(self, overlayId, page):
		"""Adds a page. Stored pages will all be updated at the same time."""
		page.overlayId = overlayId
		page._pageParent = self
		self._pageDict[overlayId] = page
		self._refreshOverlay(page)
	
	def showPage(self, overlayId, hideOverlaid=True):
		"""Shows the page, transitions should be relatively fast as layouts
		and themes should already be matched. The hideOverlaid option determines
		if we will hide the previous page.
		"""
		if not self._overlay or overlayId != self._overlay.overlayId:
			if not self._pageHistoryStack or self._pageHistoryStack[-1] != overlayId:
				self._pageHistoryStack.append(overlayId)
			self.showOverlay(overlayId=overlayId,
								panel=self._pageDict[overlayId],
								refresh=False,
								hideOverlaid=hideOverlaid)
			self.refreshLayout()
	
	def hidePage(self, overlayId, hideOverlaid=True):
		"""Function which hides the given page based on overlayId/name."""
		self.removeOverlay(overlayId, delete=False, hideOverlaid=hideOverlaid)
		self._pageDict[overlayId].setVisible(False)
	
	def showOverlay(self, overlayId, panel=None, refresh=True, hideOverlaid=True):
		"""Shows the configuration overlay"""
		panel.setVisible(True)
		if self._overlay:
			self._overlay.setParent(viz.WORLD)
			self._overlay.setVisible(False)
			self.setDisabled(False)
		
		if panel.getTheme().name != self.getTheme().name:
			panel.setTheme(self.getTheme())
		
		self._setOverlay(overlayId, panel, refresh=refresh)
		self._refreshSelectables()
		self._overlayStack.append(panel)
		
		if hideOverlaid:
			self._hideOverlaid()
	
	def _setOverlay(self,
					overlayId,
					overlay,
					refresh=False):
		"""Sets the overlay of the GUI item."""
		self._backCallbackFunction = None
		
		self._overlay = overlay
		self._overlay.overlayId = overlayId
		if self._overlay is not None:
			# apply changes to viz.VizNode
			with self.getRC():
				# parent to overlay to node but not to gui item, so it's not a 'gui child'
				self._overlay.getVizNode().setParent(self)
			self._overlay.disable(viz.DEPTH_TEST)
			self._refreshSGDepth()
			self.setDisabled(True)
		overlay._overlayParent = self
		if self._overlay and refresh:
			self._refreshOverlay(self._overlay)
		
		if self._overlay and hasattr(self._overlay, '_backCallbackFunction'):
			self._backCallbackFunction = self._overlay._backCallbackFunction
		
		if not self._theme.constantPanelButtons:
			state = (overlayId in self._pageDict) and (overlayId != 'MAIN_WINDOW')
			#try:
			if self.getRoot().getNavigationBar():
				self.getRoot().getNavigationBar().setButtonEnabled(BUTTON_BACK, state)
			#except AttributeError:
			#	print 'unable to set', self
	
	def getCurrentPageName(self):
		"""Returns the current page, by name, throws an error if no page is set.
		@return ""
		"""
		return self._pageHistoryStack[-1]
	
	def getPage(self, name):
		"""Returns the page given by name.
		@return GUINode()
		"""
		return self._pageDict[name]
	
	def setPadding(self, padding):
		"""Sets the padding placed between items.
		"""
		if padding is None:
			padding = [0, 0, 0, 0]
		if not viz.islist(padding):
			padding = [padding]*4
		else:
			while len(padding) < 4:
				padding += [0]
		self._applySize(self.getSize(), padding=padding)
		self._padding = padding[:]
	
	def setParent(self, parent, autoRefresh=True, **kwargs):
		"""Sets the parent GUI node."""
		if self._parent != viz.WORLD:
			self._parent.removeChild(self)
		with self.getRC():
			self._node.setParent(parent, **kwargs)
		self._parent = parent
		if self._parent != viz.WORLD:
			parent._children.append(self)
			self._baseOffset = self._parent._baseOffset
			self.setTheme(parent.getTheme())
			# apply changes to local node
			self.disable(viz.DEPTH_TEST)
			with self.getRC():
				self._node.setPosition(0, 0, 0)
		root = self._findRoot()
		# update the root node
		self._setRoot(root)
		# refresh everything necessary starting at the root
		if autoRefresh:
			root._refreshSGDepth()
			root.refreshLayout()
			root._refreshSelectables()
		
		if self._parent != viz.WORLD:
			self.setTooltipsEnabled(parent._tooltipsEnabled)
		if self._tt:
			viz.VizNode.setParent(self._tt, root)
			self._tt.setTheme(self._theme.tooltipTheme)
		if autoRefresh and self._parent != viz.WORLD:
			parent.setSize(parent.getSize())
	
	def setScale(self, *args, **kwargs):
		"""Sets the scale of the viz.VizNode object."""
		with self.getRC():
			self._node.setScale(*args, **kwargs)
	
	def setTT(self, tt):
		"""Sets the current tool tip. The tool tips theme will be updated
		along with the theme of thsi node.
		"""
		self._tt = tt
		if self._tt:
			self._tt.setTarget(self)
			self._tt.setEnabled(self._tooltipsEnabled)
			viz.VizNode.setParent(self._tt, self.getRoot())
			self._tt.setTheme(self._theme.tooltipTheme)
	
	def setTooltipsEnabled(self, state):
		"""Sets/toggles tooltips on and off."""
		if state == viz.TOGGLE:
			state = not self._tooltipsEnabled
		self._tooltipsEnabled = state
		if self._tt:
			self._tt.setEnabled(self._tooltipsEnabled)
			if not self._tooltipsEnabled:
				self._tt.setVisible(False)
		for child in self.getChildren()+self._overlayStack+self._pageDict.values():
			child.setTooltipsEnabled(self._tooltipsEnabled)
	
	def _refreshRenderDepth(self):
		"""Sets the render depth (draw order) of the GUI item."""
		with self.getRC():
			viz.VizNode.drawOrder(self, self._baseDepthOffset+self._drawOrderIndex)
	
	def setSize(self, size):
		"""Set the size as opposed to setting the scale. Setting the scale will
		force the scale for all sub components. Setting the size will change the
		size used for the layout of the components.
		"""
		prevSize = self._size[:]
		adjSize = self._applySize(size)
		if adjSize is None:
			self._size = prevSize
		self.refreshLayout()
		
		# update the size of the overlays
		interiorSize = self.getInteriorSize()
		overlaySize = [interiorSize[0]*self._localTheme.overlayPercent,
						interiorSize[1]*self._localTheme.overlayPercent]
		for overlay in self._overlayStack+self._pageDict.values():
			self._refreshOverlay(overlay)
		
		# call update size on the children
		for child in self._children:
			child._updateSize(self.getInteriorSize())
	
	def setTheme(self, theme, recurse=True):
		"""Sets the theme of the GUI object."""
		self._setTheme(theme, recurse=recurse)
		
		self._refreshSGDepth()
		self._postSetTheme()
		
		self._refreshSelectables()
	
	def _postSetTheme(self):
		"""Recursive callback triggered after the theme as been set/applied. In case
		there is any cleanup remaining.
		"""
		for child in self._children:
			child._postSetTheme()
	
	def _setTheme(self, theme, recurse=True):
		"""Internal set theme"""
		theme = copy.deepcopy(theme)
		menu_highlight.restore(self)
		
		self._localTheme = self._applyTheme(theme)
		
		menu_highlight.reset(self)
		menu_highlight.restoreVal(self)
		self._theme = theme
		
		self._applySize(self._size)
		self.refreshLayout()
		
		for overlay in self._overlayStack+self._pageDict.values():
			overlay._setTheme(theme)
			self._refreshOverlay(overlay)
		
		if self._cursor:
			self._cursor.setTheme(self._theme.tooltipTheme)
		
		if self._tt:
			self._tt.setTheme(self._theme.tooltipTheme)
		
		if recurse:
			for child in self._children:
				child._setTheme(theme)
		
		self._applySize(self._size)
		
		self.refreshLayout()
	
	def setVisible(self, *args, **kwargs):
		"""Sets the visible state of this GUI"""
		with self.getRC():
			viz.VizNode.visible(self, *args, **kwargs)
	
	def visible(self, *args, **kwargs):
		"""Sets the visible state of this GUI"""
		self.setVisible(*args, **kwargs)
	
	def _applySize(self, size, padding=None):
		"""Adjust the scale so the node fits in given physical dimensions. Note
		that the implementation is dependent on the subclass. However, this 
		should not change the scale of the sub object. Instead it should affect
		formatting and layout. For example text should wrap to fewer characters
		when reducing the size, and ListWrap layouts should have fewer columns,
		etc.
		"""
		return None
	
	def _findRoot(self):
		"""Refreshes the root item in the scene graph"""
		if self._parent and self._parent != viz.WORLD:
			return self._parent._findRoot()
		else:
			return self._root
	
	def _getConstrainedSize(self, size):
		"""Returns the given size constrained by the requirements of the GUINode.
		
		@return []
		"""
		size = size[:]
		minSize = self.getMinSize()
		for i in range(0, len(size)):
			size[i] = max(size[i], minSize[i])
		return size
	
	def _refreshSelectables(self):
		"""Refreshes the list of selectable items and applies it to each of the
		selection tools.
		"""
		root = self.getRoot()
		if root != self:
			root._refreshSelectables()
	
	def _hide(self):
		"""Hides this node and all children by disabling color write. This
		should generally be avoided, and is used only for handling overlays.
		"""
		# REVISE
		self.disable(viz.COLOR_WRITE, op=viz.OP_ROOT)
		for child in self._children:
			child._hide()
	
	def _show(self):
		"""Essentially undoes a hide."""
		# REVISE
		self.enable(viz.COLOR_WRITE, op=viz.OP_ROOT)
		for child in self._children:
			child._show()
	
	def _hideOverlaid(self):
		"""Hides iff this node is overlaid. Otherwise shows/restores visibility."""
		# REVISE
		if self._overlay:
			self._hide()
			self._overlay._show()
		else:
			self._show()
			for child in self._children:
				child._hideOverlaid()
	
	def _reapplySGDepth(self, index=0, stencilDepth=0, sFunc=viz.GL_EQUAL, sZpass=viz.GL_KEEP):
		"""Reapplys the scene graph depth to this node and child nodes 
		recursively. Note that a better function to use directly may be
		_refreshSGDepth which goes to the root before refreshing the depth
		of all nodes.
		"""
		# once we've got the root parent, start going through
		# the children
		# set the stencil function for this node to the stencil depth
		with self.getRC():
			if not self._isGroup:
				s = viz.StencilFunc()
				s.funcRef = stencilDepth
				s.func = sFunc
				s.zpass = sZpass
				self.stencilFunc(s)
			else:
				for child in viz.VizNode(self).getChildren():
					s = viz.StencilFunc()
					s.func = viz.GL_EQUAL
					s.funcRef = self._stencilDepth
					s.zpass = viz.GL_KEEP
					child.stencilFunc(s)
		
		# save the draw order and stencil depth
		self._drawOrderIndex = index
		self._stencilDepth = stencilDepth
		
		# set the draw order for this node
#		if not self._isGroup:
		self._refreshRenderDepth()
		
		# set the index for the child in the scene graph
		for child in self._children:
			index = child._reapplySGDepth(index=index+10,
											stencilDepth=stencilDepth+self._internalDepth)
		
		# save the post draw index
		self._postChildrenDrawIndex = index
		
		# render the overlay
		if self._overlay:
			index = self._overlay._reapplySGDepth(index=index+RENDER_OFFSET_OVERLAY,
													stencilDepth=stencilDepth+self._internalDepth,
													sFunc=viz.GL_LEQUAL,
													sZpass=viz.GL_REPLACE)
		
		# render the cursor
		if self._cursor:
			index = self._cursor._reapplySGDepth(index=index+RENDER_OFFSET_CURSOR,
															stencilDepth=stencilDepth+self._internalDepth,
															sFunc=viz.GL_LEQUAL,
															sZpass=viz.GL_REPLACE)
		
		if self._tt:
			self._tt._reapplySGDepth(index=index+10+RENDER_OFFSET_CURSOR,
										stencilDepth=stencilDepth+self._internalDepth+1,
										sFunc=viz.GL_ALWAYS,
										sZpass=viz.GL_REPLACE)
			self._tt.getContainerNode3d().enable(viz.DEPTH_TEST)
		
		# save the post draw index
		self._postDrawIndex = index
		
#		if self._disableMask and self._disabled and self._disableMask.getVisible():
#			self._refreshDisabled()
		
		return index
	
	def _refreshSGDepth(self):
		"""Refreshes the scene graph depth of the object, and applies any
		appropriate changes to the object based on its depth.
		"""
		# set the stencil function for the base node to always replace
		self.getRoot()._reapplySGDepth(index=0,
										stencilDepth=self._baseOffset,
										sFunc=viz.GL_ALWAYS,
										sZpass=viz.GL_REPLACE)
		
		self.getRoot()._hideOverlaid()
	
	def _refreshOverlay(self, overlay):
		"""Refreshes the given overlay with the current size/layout of this node"""
		interiorSize = self.getInteriorSize()
		overlaySize = [interiorSize[0]*self._theme.overlayPercent,
						interiorSize[1]*self._theme.overlayPercent]
		overlay.setSize(overlaySize)
		overlay.refreshLayout()
		self.refreshLayout()
	
	def _setRoot(self, root):
		"""Sets the root node for this node and all child nodes"""
		self._root = root
		for child in self._children:
			child._setRoot(root)
	
	def _getAbsoluteChildrenSizes(self, index):
		"""Returns the size of all children with known sizes.
		e.g. children where the size mode is not SIZE_MODE_PRERCENT_REMAINING.
		
		@return []
		"""
		absSize = 0
		for child in self._children:
			if child.getSizeMode()[index] == SIZE_MODE_METERS and child.getVisible():
				absSize += child.getSize()[index]
		return absSize
	
	def _getModeModifiedSize(self, size, parentSize):
		"""Returns a mode modified size.
		e.g. if sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_PARENT]
		and sizeReference is [0.5, 0.5] then it will return half the width
		and height of the parent object.
		
		Function is used by default in _updateSize functions.
		
		@return []
		"""
		updated = False
		sizeOut = size[:]
		for index in [0, 1]:
			if self._sizeMode[index] == SIZE_MODE_PERCENT_REMAINING:
				# get the absolute children size
				totalSize = parentSize[index]
				remaining = totalSize - self._parent._getAbsoluteChildrenSizes(index)
				sizeOut[index] = remaining*self._sizeReference[index]
				updated = True
			elif self._sizeMode[index] == SIZE_MODE_PERCENT_PARENT:
				# get the absolute children size
				totalSize = parentSize[index]
				sizeOut[index] = totalSize*self._sizeReference[index]
				updated = True
			elif self._sizeMode[index] == SIZE_MODE_SYNC:
				# get the absolute children size
				sizeOut[index] = self._sizeReference[index].getSize()[index]
				updated = True
			elif self._sizeMode[index] == SIZE_MODE_THEME:
				# get the absolute children size
				sizeOut[index] = getattr(self._theme, self._sizeReference[index])[index]
				updated = True
			elif self._sizeMode[index] == SIZE_MODE_FUNCTION:
				# get the absolute children size
				sizeOut[index] = self._sizeReference[index](self)
				updated = True
			
			# check if anything's changed
			if (updated
					and abs(sizeOut[0]-size[0]) < 0.00001
					and abs(sizeOut[1]-size[1]) < 0.00001):
				updated = False
		return updated, sizeOut
	
	def _updateSize(self, parentSize):
		"""Applies the given size to the quad"""
		size = self.getSize()
		updated, size = self._getModeModifiedSize(size, parentSize)
		
		if updated:
			self.setSize(size)
			self.getRoot().refreshLayout()


class MessageContainer(object):
	"""A parent class for any GUINodes which also want to act as containers
	for messages. Provides extra functionality for suppporting typical popup
	windows, etc. Currently all groups are MessageContainers by default.
	"""
	def clearStatusOverlays(self):
		"""Clears all 'status' overlays"""
		self.removeOverlay(STATUS_OVERLAY_ID)
	
	def showAskOverlay(self, title, message, okCallback=None, okArgs=None, cancelCallback=None, cancelArgs=None):
		"""Shows an overlay asking a yes or no question, ok or cancel."""
		size = self.getInteriorSize()
		size = [size[0]*self._localTheme.overlayPercent, size[1]*self._localTheme.overlayPercent]
		panel = MessageBox(size=size, title=title, text=message, buttonMask=BUTTON_OK|BUTTON_CANCEL)
		if okArgs is None:
			okArgs = []
		if cancelArgs is None:
			cancelArgs = []
		if okCallback:
			panel._okButton.addOnReleaseCallback(okCallback, *okArgs)
		if cancelCallback:
			panel._cancelButton.addOnReleaseCallback(cancelCallback, *cancelArgs)
		self.showOverlay(message, panel)
	
	def showMessageOverlay(self, message):
		"""Shows an overlay that's just a message box, no way to close manually,
		some criteria has to be met.
		"""
		size = self.getInteriorSize()
		size = [size[0]*self._localTheme.overlayPercent, size[1]*self._localTheme.overlayPercent]
		panel = MessageBox(size=size, text=message, buttonMask=0)
		self.showOverlay(message, panel)
	
	def showNotificationOverlay(self, title, message, okCallback=None, okArgs=None, buttonMask=BUTTON_OK):
		"""Shows an overlay that has only an ok button"""
		if okArgs is None:
			okArgs = []
		with self.getRC():
			size = self.getInteriorSize()
			size = [size[0]*self._localTheme.overlayPercent, size[1]*self._localTheme.overlayPercent]
			panel = MessageBox(size=size,
								title=title,
								text=message,
								buttonMask=buttonMask)
			if okCallback:
				if buttonMask == BUTTON_OK:
					btn = panel._okButton
				elif buttonMask == BUTTON_NEXT:
					btn = panel._nextButton
#				elif buttonMask == BUTTON_BACK:
#					btn = panel._backButton
				else:
					raise ValueError('Invalid button value')
				btn.addOnReleaseCallback(okCallback, *okArgs)
			self.showOverlay(message, panel)
		return panel
	
	def showStatusOverlay(self, message):
		"""Shows a status overlay that's just a message box, no way to close manually,
		only one status overlay is present at a time.
		Note that <overlay>.overlayId is always set to STATUS_OVERLAY_ID
		"""
		self.clearStatusOverlays()
		size = self.getInteriorSize()
		size = [size[0]*self._localTheme.overlayPercent, size[1]*self._localTheme.overlayPercent]
		panel = MessageBox(size=size, text=message, buttonMask=0)
		panel._mainPanel.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
												horizontalAlignment=layout.ALIGN_CENTER))
		self.showOverlay(STATUS_OVERLAY_ID, panel)


class Grabbable(GUINode):
	"""Base class for grabbable GUI objects"""
	def __init__(self, monitorRelease=False, **kwargs):
		super(Grabbable, self).__init__(**kwargs)
		self._monitorRelease = monitorRelease
		self._isGrabbed = False
		self._monitorReleaseEvent = None
		self._lastGrabFrame = -1
		self._lastHighlightFrame = -1
		self._highlight = None
		self._grabber = None
		self._selectable = True
		self._onGrabCallbacks = []
		self._onHoldCallbacks = []
		self._onHoverCallbacks = []
		self._onReleaseCallbacks = []
		self._onQuickReleaseCallbacks = []
		self._onHighlightCallbacks = []
	
	def addOnGrabCallback(self, function, *args, **kwargs):
		"""Adds a callback function which will be called when the object is
		grabbed.
		"""
		self._onGrabCallbacks.append(viz.Data(function=function, args=args, kwargs=kwargs))
	
	def addOnHighlightCallback(self, function, *args, **kwargs):
		"""Adds a callback function which will be called when the object is
		released.
		"""
		self._onHighlightCallbacks.append(viz.Data(function=function, args=args, kwargs=kwargs))
	
	def addOnHoverCallback(self, function, *args, **kwargs):
		"""Adds a callback function which will be called when the object is
		held.
		"""
		self._onHoverCallbacks.append(viz.Data(function=function, args=args, kwargs=kwargs))
	
	def addOnHoldCallback(self, function, *args, **kwargs):
		"""Adds a callback function which will be called when the object is
		held.
		"""
		self._onHoldCallbacks.append(viz.Data(function=function, args=args, kwargs=kwargs))
	
	def addOnReleaseCallback(self, function, *args, **kwargs):
		"""Adds a callback function which will be called when the object is
		released.
		"""
		self._onReleaseCallbacks.append(viz.Data(function=function, args=args, kwargs=kwargs))
	
	def addOnQuickReleaseCallback(self, function, *args, **kwargs):
		"""Adds a callback function which will be called when the object is
		released.
		"""
		self._onQuickReleaseCallbacks.append(viz.Data(function=function, args=args, kwargs=kwargs))
	
	def grab(self, monitorRelease=False, highlight=None, grabber=None):
		"""Grabs the GUI object"""
		self._grabTime = viz.getFrameTime()
		if not self._isGrabbed:
			self._highlight = highlight
			self._grabber = grabber
			if self._highlight:
				self._highlight.setColorForActive(viz.GREEN)
			self._onGrab()
			if monitorRelease and not self._monitorReleaseEvent:
				self._monitorReleaseEvent = vizact.onupdate(100, self._onMonitorRelease)
		self._onHold()
		self._isGrabbed = True
		self._lastGrabFrame = viz.getFrameNumber()
	
	def highlight(self, highlight=None, grabber=None):
		"""Highlights the GUI object."""
		self._onHighlight()
		self._lastHighlightFrame = viz.getFrameNumber()
	
	def hold(self):
		"""Holds the GUI object"""
		self._onHold()
	
	def release(self, silent=False):
		"""Releases the GUI object"""
		dt = viz.getFrameTime() - self._grabTime
		if self._isGrabbed:
			if self._monitorReleaseEvent:
				self._monitorReleaseEvent.remove()
				self._monitorReleaseEvent = None
			if self._highlight:
				if self._highlight.highlightingNode(self) and not silent:
					if dt < 0.5:
						self._onQuickRelease()
					self._onRelease()
				self._highlight.restoreColorForActive()
			self.clearActions()
		self._isGrabbed = False
		self._highlight = None
		self._grabber = None
	
	def hover(self):
		"""Method triggered when the object is hover."""
		for data in self._onHoverCallbacks:
			data.function(*(data.args), **(data.kwargs))
	
	def hoverEnd(self):
		"""Method triggered when the object is hover."""
		pass
#		for data in self._onHoverCallbacks:
#			data.function(*(data.args), **(data.kwargs))
	
	def _onGrab(self):
		"""Method triggered when the object is grabbed."""
		for data in self._onGrabCallbacks:
			data.function(*(data.args), **(data.kwargs))
	
	def _onHighlight(self):
		"""Method triggered when the object is highlighted."""
		for data in self._onHighlightCallbacks:
			data.function(*(data.args), **(data.kwargs))
	
	def _onHold(self):
		"""Method triggered while the object is being held. If it is the first 
		frame of holding, _isGrabbed will be False.
		"""
		for data in self._onHoldCallbacks:
			data.function(*(data.args), **(data.kwargs))
	
	def _onMonitorRelease(self):
		"""Method that monitors the release of the GUI object"""
		if viz.getFrameNumber() != self._lastGrabFrame:
#			if self._monitorRelease:
			self.release()
	
	def _onQuickRelease(self):
		"""Method triggered when the object is released."""
		for data in self._onQuickReleaseCallbacks:
			data.function(*(data.args), **(data.kwargs))
	
	def _onRelease(self):
		"""Method triggered when the object is released."""
		for data in self._onReleaseCallbacks:
			data.function(*(data.args), **(data.kwargs))
	
	def setSelectable(self, state):
		"""Sets whether or not this item is selectable"""
		if state == viz.TOGGLE:
			state = not self._selectable
		self._selectable = state


class Highlightable(object):
	"""A base class for highlightable objects"""
	def __init__(self):
		self._highlightVisibleState = False
	
	def addHighlight(self, _):
		"""Adds a highlight"""
		pass
	
	def removeHighlight(self, _):
		"""Removes a highlight"""
		pass
	
	def getHighlightVisible(self):
		"""Gets a highlight visible"""
		return self._highlightVisibleState
	
	def setHighlightVisible(self, state):
		"""Sets a highlight visible"""
		if state == viz.TOGGLE:
			state = not self.getHighlightVisible()
		self._highlightVisibleState = state


class DimHighlightable(Highlightable):
	"""A base class for dimable highlightable objects."""
	def __init__(self, theme):
		super(DimHighlightable, self).__init__()
		menu_highlight.dim(self, theme.dimAmount)
	
	def setHighlightVisible(self, state):
		"""Sets a highlight visible"""
		super(DimHighlightable, self).setHighlightVisible(state)
		if self._highlightVisibleState:
			menu_highlight.dim(self, self.getTheme().highlightAmount)
		else:
			menu_highlight.dim(self, self.getTheme().dimAmount)


class HorizontalRule(GUINode):
	"""Base class for quad-based GUI items"""
	def __init__(self,
					size,
					cornerRadius=0,
					sizeMode=None,
					sizeReference=None,
					**kwargs):
		
		if sizeMode is None:
			sizeMode = [SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS]
		if sizeReference is None:
			sizeReference = [0.95, 1.0]
		
		with self.getRC():
			self._quadNode = vizshape.addQuad(size=size, cornerRadius=cornerRadius)
		super(HorizontalRule, self).__init__(node=self._quadNode,
												size=size,
												sizeMode=sizeMode,
												sizeReference=sizeReference,
												**kwargs)
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the quad"""
		size = self._getConstrainedSize(size)
		with self.getRC():
			for i in range(0, self._quadNode.getVertexCount()):
				vert = self._quadNode.getVertex(i)
				vert[0] *= size[0]/self._size[0]
				vert[1] *= size[1]/self._size[1]
				self._quadNode.setVertex(i, vert)
		self._size = size
		return size
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		self._quadNode.color(theme.borderColor)
		self._quadNode.alpha(theme.borderColor[3])
		return super(HorizontalRule, self)._applyTheme(theme)


class Quad(Grabbable):
	"""Base class for quad-based GUI items"""
	def __init__(self, size, cornerRadius=0, **kwargs):
		with self.getRC():
			self._quadNode = vizshape.addQuad(size=size, cornerRadius=cornerRadius)
		super(Quad, self).__init__(node=self._quadNode, size=size, **kwargs)
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the quad"""
		size = self._getConstrainedSize(size)
		with self.getRC():
			for i in range(0, self._quadNode.getVertexCount()):
				vert = self._quadNode.getVertex(i)
				vert[0] *= size[0]/self._size[0]
				vert[1] *= size[1]/self._size[1]
				self._quadNode.setVertex(i, vert)
		self._size = size
		return size


class TextureQuad(Quad):
	"""Use to scale the quad to the size given while maintaining aspect ratio.
	If maxSize has None as a component, it will ignore that component and 
	resize using the other, e.g. [None, 0.4] guarantees a height of 0.4m
	regardless of the aspect of the image. A value of [0.4, 0.4] will set
	the size so that the largest component is not greater than 0.4 while
	maintaining aspect.
	"""
	def __init__(self,
					maxSize,
					texture,
					maintainAspect=True,
					cornerRadius=0,
					matchTextColor=False,
					themeSyncAttribute=None,
					**kwargs):
		
		self._maintainAspect = maintainAspect
		self._matchTextColor = matchTextColor
		self._themeSyncAttribute = themeSyncAttribute
		self._maxSize = maxSize
		
		textureSize = texture.getSize()
		if textureSize[1]:
			aspect = float(textureSize[0])/float(textureSize[1])
		else:
			aspect = 1.0
		self._aspect = aspect
		if self._maintainAspect:
			size = self._getAspectConstrainedSize(self._maxSize)
		else:
			size = maxSize[:]
		
		super(TextureQuad, self).__init__(size=size,
											cornerRadius=cornerRadius,
											**kwargs)
		
		self._setTexture(texture)
	
	def _setTexture(self, texture):
		"""Handles setting of a texture and managing size/aspect ratio
		considerations
		"""
		textureSize = texture.getSize()
		if textureSize[1]:
			aspect = float(textureSize[0])/float(textureSize[1])
		else:
			aspect = 1.0
		self._aspect = aspect
		if self._maintainAspect:
			size = self._getAspectConstrainedSize(self._maxSize)
		else:
			size = self._maxSize[:]
		
		self.setSize(size=size)
		
		with self.getRC():
			self.texture(texture)
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the object."""
		size = self._getConstrainedSize(size)
		if self._maintainAspect:
			size = self._getAspectConstrainedSize(size)
		
		with self.getRC():
			for i in range(0, self._quadNode.getVertexCount()):
				vert = self._quadNode.getVertex(i)
				vert[0] *= size[0]/self._size[0]
				vert[1] *= size[1]/self._size[1]
				self._quadNode.setVertex(i, vert)
		self._size = size
		self._maxSize = size[:]
		return size
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		
		if self._themeSyncAttribute:
			try:
				self._setTexture(viz.add(getattr(self._theme, self._themeSyncAttribute)))
			except AttributeError:
				viz.logWarn('**WARNING: unable to change texture to match theme using attribute: {}.'.format(self._themeSyncAttribute))
		
		if self._matchTextColor:
			self.color(localTheme.textColor)
		#		if self._parent != viz.WORLD:
#			size = self.getSize()
#			parentSize = self._parent.getInteriorSize()
#			updated, size = self._getModeModifiedSize(size, parentSize)
#			if updated:
#				if self._maintainAspect:
#					size = self._getAspectConstrainedSize(size)
#				self.setSize(size)
		
		return super(TextureQuad, self)._applyTheme(localTheme)
	
	def _getAspectConstrainedSize(self, size):
		"""Returns the size constrained by aspect ratio"""
		scale = _getScale(size, self._aspect)# assume max size
		return [scale*self._aspect, scale]
	
	def getSize(self):
		size = self._size
		if self._maintainAspect:
			size = self._getAspectConstrainedSize(self._maxSize)
		return size
	
	def _updateSize(self, parentSize):
		"""Applies the given size to the quad"""
		size = self.getSize()
		updated, size = self._getModeModifiedSize(size, parentSize)
		if updated:
			if self._maintainAspect:
				size = self._getAspectConstrainedSize(size)
			self.setSize(size)
			self.getRoot().refreshLayout()


class TextureQuadButton(TextureQuad):
	"""Convenience class for a quad with a texture which also acts as a button"""
	def __init__(self, matchTextColor=True, **kwargs):
		super(TextureQuadButton, self).__init__(matchTextColor=matchTextColor, **kwargs)
		self._highlightVisibleState = False
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self.getVisible():
			return [self]
		else:
			return []
	
	def addHighlight(self, _):
		"""Adds a highlight"""
		pass
	
	def removeHighlight(self, _):
		"""Removes a highlight"""
		pass
	
	def getHighlightVisible(self):
		"""Gets a highlight visible"""
		return self._highlightVisibleState
	
	def setHighlightVisible(self, state):
		"""Sets a highlight visible"""
		if state == viz.TOGGLE:
			state = not self.getHighlightVisible()
		self._highlightVisibleState = state
		with self.getRC():
			if not state:
				menu_highlight.dim(self, self.getTheme().dimAmount)
			else:
				menu_highlight.dim(self, self.getTheme().highlightAmount)#menu_highlight.dim(self, 1.0)


class Text(Grabbable):
	"""Generic text GUI item. Handles wrapping of text to match container size,
	and scaling of text to adjust for differences in fonts to match line height.
	"""
	def __init__(self,
					text,
					lineHeight=themes.STD_TEXT_LINE_HEIGHT,
					lineSpacing=themes.STD_TEXT_LINE_SPACING,
					sizeMode=None,
					sizeReference=None,
					relativeLineHeightScale=1,
					**kwargs):
		
		self._finalText = text
		self._baselineShift = 0
		self._needsBaselineShift = False
		
		if sizeMode is None:
			sizeMode = [SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_REMAINING]
		if sizeReference is None:
			sizeReference = [1.0, 1.0]
		self._relativeLineHeightScale = relativeLineHeightScale
		
		self._textNode = None
		with self.getRC():
			self._textNode = viz.addText(text)
			self._textNode.color(themes.getDarkTheme().textColor)
		
		super(Text, self).__init__(node=self._textNode,
									sizeMode=sizeMode,
									sizeReference=sizeReference,
									**kwargs)
		self.setScale([1]*3)
		self._text = text
		self._lineHeight = lineHeight*self._relativeLineHeightScale
		self._lineSpacing = lineSpacing
		self._charaterWidth = 30
		self._replaceWhitespace = False
		
		with self.getRC():
			self.message(textwrap.fill(self._text, width=self._charaterWidth))
			self.alignment(viz.TEXT_CENTER_TOP)#viz.ALIGN_LEFT_BOTTOM_BASE)#
	
	def _adaptToFont(self):
		"""Adjusts to the given font"""
		with self.getRC():
			self.setScale([1]*3)
			self.setLineSpacing(0)
			
			# match the size of the font to the phyiscal size we need
			self.message('A')
			bb1 = self.getBoundingBox()
			self.message('A\nA')
			bb = self.getBoundingBox()
			self._nativeLineHeight = bb.getHeight()-bb1.getHeight()
			
			self.setScale([self._lineHeight / self._nativeLineHeight]*3)
			self.setLineSpacing(self._lineSpacing)
			
			# find the baseline shift for this font
			self.message('Aqpyg')
			bbWQ = viz.VizNode.getBoundingBox(self._textNode)
			# get the bounding box as default
			self.message('A')
			bbNQ = viz.VizNode.getBoundingBox(self._textNode)
			self._baselineShift = bbWQ.size[1] - bbNQ.size[1]
		self._applySize(self._size)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		if theme:
			self._lineHeight = theme.lineHeight*self._relativeLineHeightScale
			
			self.font(theme.font)
			self._adaptToFont()
			
			self._textNode.color(theme.textColor)
			
			self.setText(self._text)
		return super(Text, self)._applyTheme(theme)
	
	def font(self, *args, **kwarg):
		"""Wrapper around the font setter function"""
		with self.getRC():
			self._textNode.font(*args, **kwarg)
			self._adaptToFont()
	
	def setLineSpacing(self, *args, **kwarg):
		"""Wrapper around the setLineSpacing function"""
		with self.getRC():
			self._textNode.setLineSpacing(*args, **kwarg)
	
	def message(self, *args, **kwargs):
		"""Wrapper around the message function"""
		with self.getRC():
			self._textNode.message(*args, **kwargs)
	
	def getBoundedBoundingBox(self):
		"""Wrapper around the bounding box function.
		
		@return viz.BoundingBox()
		"""
		bb = self.getBoundingBox()
		if self._needsBaselineShift:
			bb.setCenter([bb.center[0], bb.center[1]-self._baselineShift/2.0, bb.center[2]])
			bb.setSize([bb.size[0], bb.size[1]+self._baselineShift, bb.size[2]])
		return bb
	
	def setText(self, text, updateSize=True, refreshLayout=True):
		"""Sets the text of the node."""
		self._text = text
		self.message(textwrap.fill(self._text, width=self._charaterWidth, replace_whitespace=self._replaceWhitespace))
		if updateSize:
			self._applySize(self._size, padding=None)
		if self._parent != viz.WORLD and refreshLayout:
			self._parent.refreshLayout()
	
	def _applySize(self, size, padding=None):
		"""Adjusts the number of characters on a line to fit in the given 
		physical dimensions.
		"""
		size = self._getConstrainedSize(size)
		guess = int((size[0]/self._lineHeight)*2.0)
		self._findMinBoundingBox(guess, guess, size)
		# add a lowercase q to the text and get the bounding box
		self.message(self._finalText[:-1]+'q\n')
		bbWQ = viz.VizNode.getBoundingBox(self._textNode)
		# get the bounding box as default
		self.message(self._finalText)
		bbNQ = viz.VizNode.getBoundingBox(self._textNode)
		self._needsBaselineShift = abs(bbWQ.size[1] - bbNQ.size[1]) > 0.00001
		
		self._size = size
		return size
	
	def _findMinBoundingBox(self, center, search, size, depth=0):
		"""Utility method to find the optimal number of characters that fit
		in a given width.
		"""
		if center > 0:
			finalText = ''
			if not self._replaceWhitespace:
				paragraphs = self._text.split('\n')
				for paragraph in paragraphs:
					finalText += textwrap.fill(paragraph, width=center, replace_whitespace=True)
					finalText += '\n'
			else:
				finalText = textwrap.fill(self._text, width=center, replace_whitespace=True)
			self.message(finalText)
			self._finalText = finalText
		else:
			finalText = textwrap.fill(self._text, width=5, replace_whitespace=self._replaceWhitespace)
			self.message(finalText)
			self._finalText = finalText
			viz.logWarn('**Warning: Bounding Box for text is too small to auto fit the text.')
			depth = 20
		bb = self.getBoundingBox()
		if depth < 20:
			# if the bounding box is greater than the given size
			search = int(search/2.0)
			if bb.width < size[0]-(self._lineHeight*5):
				self._findMinBoundingBox(center+search, search, size, depth=depth+1)
			if bb.width > size[0]:
				self._findMinBoundingBox(center-search, search, size, depth=depth+1)


class IndexText(Text):
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		theme = super(IndexText, self)._applyTheme(theme)
		if theme:
			self._textNode.color(theme.indexTextColor)
		return theme


class Header(Text):
	"""Convenience class which allows text to be added as headers ala HTML
	e.g. index=1 => 'H1 tag', index=2 => 'H2 tag', etc
	"""
	def __init__(self, index=1, *args, **kwargs):
		self._index = index
		super(Header, self).__init__(*args, **kwargs)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		lineHeight = theme.lineHeight
		if self._index == 1:
			lineHeight = theme.H1
		elif self._index == 2:
			lineHeight = theme.H2
		elif self._index == 3:
			lineHeight = theme.H3
		elif self._index == 4:
			lineHeight = theme.H4
		theme.lineHeight = lineHeight
		return super(Header, self)._applyTheme(theme)



class Group(Grabbable, MessageContainer):
	"""A base group object, should be used often for organizing since it doesn't add
	much overhead."""
	def __init__(self, size, node=None, **kwargs):
		if node is None:
			node = viz.addGroup()
		super(Group, self).__init__(node=node, size=size, internalDepth=0, **kwargs)
		self._isGroup = True
	
	def getInteriorSize(self):
		"""Returns the size available for placing child objects.
		
		@return []
		"""
		return [
			self._size[0] - (self._padding[_L] + self._padding[_R]),
			self._size[1] - (self._padding[_T] + self._padding[_B])
		]
	
	def getBoundingBox(self, *args, **kwargs):
		"""Returns the bouding box for the VizNode
		
		@return viz.BoundingBox()
		"""
		with self.getRC():
			bb = viz.Data()
			bb.center = self.getPosition(*args, **kwargs)
			bb.width = self._size[0]
			bb.height = self._size[1]
			bb.depth = 0
			bb.xmin = bb.center[0]-bb.width/2.0
			bb.xmax = bb.center[0]+bb.width/2.0
			bb.ymin = bb.center[1]-bb.height/2.0
			bb.ymax = bb.center[1]+bb.height/2.0
			bb.zmin = bb.center[2]-bb.depth/2.0
			bb.zmax = bb.center[2]+bb.depth/2.0
			return bb
	
	def getMinSize(self):
		"""Returns the min size for the GUINode
		
		@return []
		"""
		return [0.001+self._padding[_R]+self._padding[_L] + self._localTheme.cornerRadius*2,
				0.001+self._padding[_T]+self._padding[_B] + self._localTheme.cornerRadius*2]
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the object."""
		size = self._getConstrainedSize(size)
		if padding is not None:
			self._padding = padding[:]
		self._size = size[:]
		return size


class Panel(Grabbable):
	"""A base panel object"""
	def __init__(self, size, theme=None, padding=None, **kwargs):
		if theme is None:
			theme = themes.getDarkTheme()
		
		# padding for the object for internal items
		if padding is None:
			padding = [0, 0, 0, 0]
		if not viz.islist(padding):
			padding = [padding]*4
		else:
			while len(padding) < 4:
				padding += [0]
		self._padding = padding[:]#[v+self._theme.cornerRadius for v in padding]
		
		self._usingBorder = True
		
		self._quadBorder = None
		self._quadInterior = None
		with self.getRC():
			self._quadBorder = _addQuad(size, cornerRadius=theme.cornerRadius)
			self._quadBorder.disable(viz.INTERSECTION)
			self._quadBorder.disable(viz.LIGHTING)
			self._quadBorder.disable(viz.DEPTH_TEST)
			interiorSize = [size[0]-(self._padding[_L]+self._padding[_R]),
							size[1]-(self._padding[_T]+self._padding[_B])]
			self._quadInterior = _addQuad(interiorSize, cornerRadius=theme.cornerRadius)
			self._quadInterior.setParent(self._quadBorder)
			self._quadInterior.disable(viz.INTERSECTION)
			self._quadInterior.disable(viz.LIGHTING)
			self._quadInterior.disable(viz.DEPTH_TEST)
		
		super(Panel, self).__init__(node=self._quadBorder, size=size, internalDepth=1, padding=self._padding, **kwargs)
		
		with self.getRC():
			self._quadInterior.setPosition(self.getInteriorCenter())
	
	def _applyTheme(self, theme): 
		"""Applies the given theme, if applicable"""
		with self.getRC():
			size = self._size
			
			_updateQuad(self._quadBorder, size=size, cornerRadius=theme.cornerRadius)
			interiorSize = [size[0]-(self._padding[_L]+self._padding[_R]), # - theme.cornerRadius*2,
							size[1]-(self._padding[_T]+self._padding[_B])]# - theme.cornerRadius*2]
			if sum(interiorSize+size) == 0:
				raise ValueError()
			
			if self._parent == viz.WORLD:
				backColor = theme.topBackColor
			else:
				backColor = theme.backColor
			
			if self._padding[0] == 0 and self._padding[1] == 0:
				self._quadBorder.alpha(backColor[3])
				self._quadBorder.color(backColor)
				
				_updateQuad(self._quadInterior, size=interiorSize, cornerRadius=theme.cornerRadius)
				self._quadInterior.alpha(backColor[3])
				self._quadInterior.color(backColor)
			else:
				self._quadBorder.alpha(theme.borderColor[3])
				self._quadBorder.color(theme.borderColor)
				
				_updateQuad(self._quadInterior, size=interiorSize, cornerRadius=theme.cornerRadius)
				self._quadInterior.alpha(backColor[3])
				self._quadInterior.color(backColor)
		self._autoHideInteriorQuad()
		return super(Panel, self)._applyTheme(theme)
	
	def getMinSize(self):
		"""Returns the min size for the GUINode
		
		@return []
		"""
		return [0.001+self._padding[_R]+self._padding[_L] + self._localTheme.cornerRadius*2,
				0.001+self._padding[_T]+self._padding[_B] + self._localTheme.cornerRadius*2]
	
	def getInteriorSize(self):
		"""Returns the size available for placing child objects.
		
		@return []
		"""
		return [
			self._size[0] - (self._padding[_L] + self._padding[_R]) - self._localTheme.cornerRadius*2,
			self._size[1] - (self._padding[_T] + self._padding[_B]) - self._localTheme.cornerRadius*2
		]
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the object."""
		size = self._getConstrainedSize(size)
		with self.getRC():
			for i in range(0, self._quadBorder.getVertexCount()):
				vert = self._quadBorder.getVertex(i)
				vert[0] *= size[0]/self._size[0]
				vert[1] *= size[1]/self._size[1]
				self._quadBorder.setVertex(i, vert)
		
		if padding is None:
			padding = self._padding
		
		if self._usingBorder:
			oldInteriorSize = [self._size[0]-(self._padding[_L]+self._padding[_R]),
								self._size[1]-(self._padding[_T]+self._padding[_B])]
			interiorSize = [size[0]-(padding[_L]+padding[_R]),
							size[1]-(padding[_T]+padding[_B])]
			with self.getRC():
				for i in range(0, self._quadInterior.getVertexCount()):
					vert = self._quadInterior.getVertex(i)
					vert[0] *= interiorSize[0]/oldInteriorSize[0]
					vert[1] *= interiorSize[1]/oldInteriorSize[1]
					self._quadInterior.setVertex(i, vert)
				self._quadInterior.setPosition(self.getInteriorCenter())
			self._padding = padding[:]
		
		self._autoHideInteriorQuad()
		self._size = size
		
		return size
	
	def _autoHideInteriorQuad(self):
		"""Auto hides the interior quad if there's no padding, so it cuts down
		on the number of drawables
		"""
		with self.getRC():
			if self._padding[0] == 0 and self._padding[1] == 0:
				self._internalDepth = 0
				self._quadInterior.visible(False)
			else:
				self._internalDepth = 1
				self._quadInterior.visible(True)
	
	def _reapplySGDepth(self, *args, **kwargs):
		"""Refreshes the scene graph depth of the object, and applies any
		appropriate changes to the object based on its depth.
		"""
		index = super(Panel, self)._reapplySGDepth(*args, **kwargs)
		with self.getRC():
			if self._internalDepth == 1:
				# draw order
				viz.VizNode.drawOrder(self._quadBorder, self._baseDepthOffset+self._drawOrderIndex+1)
				self._quadInterior.drawOrder(self._baseDepthOffset+self._drawOrderIndex)
				
				s = viz.StencilFunc()
				s.func = viz.GL_EQUAL
				s.funcRef = self._stencilDepth
				s.zpass = viz.GL_KEEP
				self._quadBorder.stencilFunc(s)
				# stencil
				s = viz.StencilFunc()
				s.func = viz.GL_EQUAL
				s.funcRef = self._stencilDepth
				s.zpass = viz.GL_INCR
				self._quadInterior.stencilFunc(s)
			else:
				viz.VizNode.drawOrder(self, self._baseDepthOffset+self._drawOrderIndex)
		
		return index
	
	def _refreshRenderDepth(self):
		"""Sets the render depth (draw order) of the GUI item."""
		with self.getRC():
			if self._internalDepth == 1:
				# draw order
				viz.VizNode.drawOrder(self._quadBorder, self._baseDepthOffset+self._drawOrderIndex+1)
				self._quadInterior.drawOrder(self._baseDepthOffset+self._drawOrderIndex)
				
				s = viz.StencilFunc()
				s.func = viz.GL_EQUAL
				s.funcRef = self._stencilDepth
				s.zpass = viz.GL_KEEP
				self._quadBorder.stencilFunc(s)
				# stencil
				s = viz.StencilFunc()
				s.func = viz.GL_EQUAL
				s.funcRef = self._stencilDepth
				s.zpass = viz.GL_INCR
				self._quadInterior.stencilFunc(s)
			else:
				viz.VizNode.drawOrder(self._quadBorder, self._baseDepthOffset+self._drawOrderIndex)


class TitleGroup(Group):
	"""A simple progress bar GUI."""
	def __init__(self,
					title,
					size=None,
					sizeMode=None,
					sizeReference=None,
					**kwargs):
		if sizeMode is None:
			sizeMode = [SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS]
		if sizeReference is None:
			sizeReference = [1, 1]
		
		self._textNode = Header(index=4,
								text=title,
								size=[0.1, themes.STD_TEXT_LINE_HEIGHT],
								sizeMode=sizeMode,
								sizeReference=sizeReference)
		super(TitleGroup, self).__init__(size=[0.1, self._textNode._theme.H4*2],
											sizeMode=sizeMode,
											sizeReference=sizeReference,
											**kwargs)
		self.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_CENTER,
									verticalAlignment=layout.ALIGN_CENTER))
		self.addChild(self._textNode)
	
	def _applyTheme(self, theme): 
		"""Applies the given theme, if applicable"""
		newTheme = super(TitleGroup, self)._applyTheme(theme)
		self.setSize([self._size[0], theme.H4*2])
		return newTheme


class ProgressBar(Panel):
	"""A simple progress bar GUI."""
	def __init__(self, size, **kwargs):
		super(ProgressBar, self).__init__(size=size, **kwargs)
		self._innerBar = Panel(size=self.getInteriorSize(),
								sizeMode=[SIZE_MODE_PERCENT_PARENT]*2,
								sizeReference=[1, 1])
		self.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_LEFT))
		self.addChild(self._innerBar)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		theme.backColor = [0, 0, 0, 1]
		theme = super(ProgressBar, self)._applyTheme(theme)
		theme.backColor = [1]*4
#		with self.getRC():
#			self._quadBorder.alpha(1)#theme.borderColor[3])
#			self._quadBorder.color(viz.BLACK)#theme.borderColor)
#			self._quadInterior.alpha(1)#theme.backColor[3])
#			self._quadInterior.color(viz.WHITE)
		return theme
	
	def setProgress(self, progress):
		"""Sets the progress as a value between 0 - 1(complete)."""
#		fullSize = self.getSize()
#		padding = self._padding[:]
#		padding[_R] = (fullSize[0])*(1.0-min(1, max(0.001, progress)))
#		self._innerBar._sizeReference[0] = progress
		self._innerBar.setScale(max(0.001, progress), 1, 1)
		self.refreshLayout()
#		self.setPadding(padding)


class VPanel(Panel):
	"""A panel object which displays a list of items"""
	def refreshLayout(self):
		"""Refreshes the layout of the GUI."""
		if self._layout is not None:
			size = [self._size[0], # + self._padding[_L] + self._padding[_R],
					self._layout.getSize(self, self._children)[1] + self._padding[_T] + self._padding[_B] + self._localTheme.cornerRadius*2]
			if size[1] > 0:
				self._applySize(size)
				self._size = self._getConstrainedSize(size)
			super(VPanel, self).refreshLayout()


class VGroup(Group):
	"""A panel object which displays a list of items"""
	def refreshLayout(self):
		"""Refreshes the layout of the GUI."""
		if self._layout is not None:
			size = [self._size[0], # + self._padding[_L] + self._padding[_R],
					self._layout.getSize(self, self._children)[1] + self._padding[_T] + self._padding[_B] + self._localTheme.cornerRadius*2]
			if size[1] > 0:
				self._applySize(size)
				self._size = self._getConstrainedSize(size)
			super(VGroup, self).refreshLayout()


class HighlightButtonPanel(Panel):
	"""Base class for highlightable buttons"""
	def __init__(self, size=None, sizeMode=None, sizeReference=None, **kwargs):
		if size is None:
			size = [0.1, 0.1]
		self._highlightVisibleState = False
		if sizeMode is None:
			sizeMode = [SIZE_MODE_THEME]*2
		if sizeReference is None:
			sizeReference = ['stdButtonSize']*2
		super(HighlightButtonPanel, self).__init__(size=size,
													sizeMode=sizeMode,
													sizeReference=sizeReference,
													**kwargs)
	
	def addHighlight(self, _):
		"""Adds a highlight"""
		pass
	
	def removeHighlight(self, _):
		"""Removes a highlight"""
		pass
	
	def getHighlightVisible(self):
		"""Gets a highlight visible"""
		return self._highlightVisibleState
	
	def setHighlightVisible(self, state):
		"""Sets a highlight visible"""
		if state == viz.TOGGLE:
			state = not self.getHighlightVisible()
		if not state:
			with self.getRC():
				menu_highlight.dim(self._contentNode, self.getTheme().dimAmount)
				if self._quadInterior.getVisible():
					menu_highlight.dim(self, self.getTheme().dimAmount)
					menu_highlight.dim(self._quadInterior, self.getTheme().dimAmount)
				else:
					menu_highlight.dim(self._quadBorder, self.getTheme().highlightAmount)
					menu_highlight.dim(self._contentNode, self.getTheme().dimAmount)
		else:
			with self.getRC():
				menu_highlight.dim(self._contentNode, self.getTheme().highlightAmount)
				menu_highlight.dim(self, self.getTheme().highlightAmount)
				if self._quadInterior.getVisible():
					menu_highlight.dim(self._quadInterior, self.getTheme().highlightAmount)
		self._highlightVisibleState = state
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self.getVisible() and self._selectable:
			return [self]
		else:
			return []


class OutlineButton(HighlightButtonPanel):
	"""*MSS
	Class for text buttons. Text surrounded by a panel item.
	"""
	def __init__(self, text, size=None, padding=0.002, **kwargs):
		self._text = text
		self._contentNode = None
		
		super(OutlineButton, self).__init__(size=size, padding=padding, **kwargs)
		
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		# add a text node
		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
		interiorSize = self.getInteriorSize()
		self._textNode.setSize([interiorSize[0]*0.9, interiorSize[1]*0.75])
		self.addChild(self._textNode)
		self._contentNode = self._textNode
		
		self.refreshLayout()
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = localTheme.buttonCornerRadius
		localTheme.borderColor = localTheme.textColor
		return super(OutlineButton, self)._applyTheme(localTheme)


class TextButton(Panel, DimHighlightable):
	"""Class for text buttons. Text surrounded by a panel item."""
	def __init__(self, size, text, **kwargs):
		self._text = text
		
		super(TextButton, self).__init__(size=size, **kwargs)
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
		interiorSize = self.getInteriorSize()
		self._textNode.setSize([interiorSize[0]*0.9, interiorSize[1]*0.75])
		self.addChild(self._textNode)
		
		self.refreshLayout()
		DimHighlightable.__init__(self, self._theme)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = localTheme.buttonCornerRadius
		return super(TextButton, self)._applyTheme(localTheme)
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self.getVisible():
			return [self]
		else:
			return []


class PanelButton(HighlightButtonPanel):
	"""*MSS
	Class for image buttons. TextureQuad surrounded by a panel item.
	"""
	def __init__(self, size, panel, padding=0.002, **kwargs):
		self._contentNode = panel
		
		super(PanelButton, self).__init__(size=size, padding=padding, **kwargs)
		
		self.addChild(panel)
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		self.refreshLayout()
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = localTheme.buttonCornerRadius
		localTheme.borderColor = localTheme.textColor
		return super(PanelButton, self)._applyTheme(localTheme)


class ImageButton(HighlightButtonPanel):
	"""*MSS
	Class for image buttons. TextureQuad surrounded by a panel item.
	"""
	def __init__(self, size, texture, padding=0.002, imagePadding=1.0, matchTextColor=False, **kwargs):
		self._texture = texture
		self._matchTextColor = matchTextColor
		self._contentNode = None
		
		self._imageNode = TextureQuad(maxSize=size, texture=texture)
		
		super(ImageButton, self).__init__(size=size, padding=padding, **kwargs)
		
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		# add a text node
		interiorSize = self.getInteriorSize()
		self._imageNode.setSize([interiorSize[0]*imagePadding, interiorSize[1]*imagePadding])
		self.addChild(self._imageNode)
		self._contentNode = self._imageNode
		
		self.refreshLayout()
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = localTheme.buttonCornerRadius
		localTheme.borderColor = localTheme.textColor
		if self._matchTextColor:
			self._imageNode.color(theme.textColor)
		return super(ImageButton, self)._applyTheme(localTheme)


class ToggleButton(HighlightButtonPanel):
	"""*MSS
	Class for text buttons. Text surrounded by a panel item.
	"""
	def __init__(self, size, trueText, falseText, **kwargs):
		self._text = falseText
		self._contentNode = None
		
		super(ToggleButton, self).__init__(size=size, padding=0.002, **kwargs)
		
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		# add a text node
		self._textNode = Text(self._text, lineHeight=self._theme.lineHeight)
		interiorSize = self.getInteriorSize()
		self._textNode.setSize([interiorSize[0]*0.9, interiorSize[1]*0.75])
		self.addChild(self._textNode)
		self._contentNode = self._textNode
		
		self._trueText = trueText
		self._falseText = falseText
		self._state = False
		
		self.refreshLayout()
		self._event = None
		self.addOnReleaseCallback(self._onToggle)
	
	def setOnToggleEvent(self, event):
		"""Sets the callback event when this button is toggled."""
		self._event = event
	
	def remove(self, *args, **kwargs):
		"""Removes the GUI node."""
		super(ToggleButton, self).remove()
	
	def _onToggle(self):
		"""Internal function triggered when button is pressed."""
		self._state = not self._state
		if self._state:
			self._textNode.setText(self._trueText)
		else:
			self._textNode.setText(self._falseText)
		if self._event:
			viz.sendEvent(self._event, viz.Event(state=self._state))
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = localTheme.buttonCornerRadius
		localTheme.borderColor = localTheme.textColor
		return super(ToggleButton, self)._applyTheme(localTheme)


class ImageAndTextPanel(Group):
	"""Convenience class for a simple panel with images and text"""
	def __init__(self,
					textNode,
					texture,
					size,
					matchTextColor=True,
					themeSyncAttribute=None,
					iconSizeReference=None,
					**kwargs):
		if iconSizeReference is None:
			iconSizeReference = [0.3, 1.0]
		textSizeReference = [1.0-iconSizeReference[0], 1.0]
		self._textNode = textNode
		super(ImageAndTextPanel, self).__init__(size=size)
		self.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		self._imageNode = TextureQuad(maxSize=[size[0]*iconSizeReference[0], size[1]*iconSizeReference[1]],
										sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_PARENT],
										sizeReference=iconSizeReference,
										matchTextColor=matchTextColor,
										themeSyncAttribute=themeSyncAttribute,
										texture=texture,
										margin=[0, themes.STD_TEXT_LINE_HEIGHT*0.5, 0, 0])
		self._homePanelTextWrapper = Group(size=[size[0]*textSizeReference[0], size[1]*textSizeReference[1]],
											sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_PARENT],
											sizeReference=textSizeReference)
		self._homePanelTextWrapper.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
															horizontalAlignment=layout.ALIGN_LEFT))
		self._homePanelTextWrapper.addChild(textNode)
		self.addChild(self._imageNode)
		self.addChild(self._homePanelTextWrapper)


class ImageAndTextPanelButton(ImageAndTextPanel):
	"""Convenience class for a button with text and an image"""
	def __init__(self, *args, **kwargs):
		self._highlightVisibleState = False
		super(ImageAndTextPanelButton, self).__init__(*args,
														**kwargs)
	
	def addHighlight(self, _):
		"""Adds a highlight"""
		pass
	
	def removeHighlight(self, _):
		"""Removes a highlight"""
		pass
	
	def getHighlightVisible(self):
		"""Gets a highlight visible"""
		return self._highlightVisibleState
	
	def setHighlightVisible(self, state):
		"""Sets a highlight visible"""
		if state == viz.TOGGLE:
			state = not self.getHighlightVisible()
		with self.getRC():
			if not state:
				menu_highlight.dim(self, self.getTheme().dimAmount)
			else:
				menu_highlight.dim(self, self.getTheme().highlightAmount)
		self._highlightVisibleState = state
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self.getVisible() and self._selectable:
			return [self]
		else:
			return []


class HomeButton(PanelButton):
	"""Convenience class for a home button"""
	def __init__(self, text, size, **kwargs):
		homePanel = ImageAndTextPanel(texture=viz.add('resources/icons/home.png'),
										textNode=Text(text=text),
										size=size,
										themeSyncAttribute='homeIcon',
										iconSizeReference=[0.3, 0.6])
		
		super(HomeButton, self).__init__(size=size,
											panel=homePanel,
											monitorRelease=False,
											**kwargs)


#class SelectableText(Panel):
#	"""Class for text buttons. Text surrounded by a panel item."""
#	def __init__(self, size, text, **kwargs):
#		self._text = text
#		
#		super(SelectableText, self).__init__(size=size, **kwargs)
#		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
#									horizontalAlignment=layout.ALIGN_CENTER))
#		with self.getRC():
#			self._quadBorder.disable(viz.COLOR_WRITE)
#			self._quadInterior.disable(viz.COLOR_WRITE)
#		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
#		interiorSize = self.getInteriorSize()
#		self._textNode.setSize([interiorSize[0]*0.9, interiorSize[1]*0.75])
#		self.addChild(self._textNode)
#		
#		self.refreshLayout()
#		# add/overwrite the necessary functions to the node
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
#			with viz.MainResourceContext:
#				if state:
#					self._quadBorder.enable(viz.COLOR_WRITE)
#					self._quadInterior.enable(viz.COLOR_WRITE)
#				else:
#					self._quadBorder.disable(viz.COLOR_WRITE)
#					self._quadInterior.disable(viz.COLOR_WRITE)
#		self.setHighlightVisible = setHighlightVisible
#	
#	def getSelectables(self):
#		"""Returns a list of selectable objects.
#		
#		@return []
#		"""
#		return [self]
#	
#	def _applyTheme(self, theme):
#		"""Applies the given theme, if applicable"""
#		localTheme = copy.deepcopy(theme)
#		localTheme.cornerRadius = localTheme.buttonCornerRadius
#		return super(SelectableText, self)._applyTheme(localTheme)



class ConstrainedGrabbable(HighlightButtonPanel):
	"""Base class for a constrained grabbable object (e.g. a scroll bar puck)"""
	def __init__(self, *args, **kwargs):
		super(ConstrainedGrabbable, self).__init__(*args, **kwargs)
		self.addOnGrabCallback(self._updateStartPos)
		self.addOnHoldCallback(self._updatePos)
		self._refPos = vizmat.Vector([0, 0, 0])
		self._updateCallback = None
	
	def setUpdateCallback(self, func):
		"""adds an update callback"""
		self._updateCallback = func
	
	def setPercentageY(self, percent):
		"""Sets the position as a percentage"""
		size = self._parent.getInteriorSize()
		size[1] -= self.getSize()[1]
		newPos = vizmat.Vector(self._refPos)
		halfSize = size[1]/2.0
		newPos[1] = (size[1] * (1.0-percent)) - halfSize
		newPos[0] = self._refPos[0]
		self.setPosition(newPos)
	
	def _boundPos(self, diff):
		"""Function that binds the position given diff which is a relative
		transformation from the start pos
		"""
		size = self._parent.getInteriorSize()
		size[1] -= self.getSize()[1]
		
		newPos = vizmat.Vector(self._refPos)
		halfSize = size[1]/2.0
		newPos[1] = min(halfSize, max(-halfSize, newPos[1]-diff[1]))
		newPos[0] = self._refPos[0]
		self.setPosition(newPos)
		percent = [0, 1.0-(newPos[1]+halfSize)/float(size[1])]
		
		if self._updateCallback:
			self._updateCallback(percent[1])
	
	def _updateStartPos(self):
		"""Updates the start and reference positions of the grabbable, used to 
		determine limits."""
		self._startPos = vizmat.Vector(self._grabber.getPosition(viz.ABS_GLOBAL))
		self._refPos = vizmat.Vector(self.getPosition())
	
	def _updatePos(self):
		"""Updates the position of the grabbable"""
		diff = self._startPos - self._grabber.getPosition(viz.ABS_GLOBAL)
		self._boundPos(diff)
	
	def setHighlightVisible(self, state):
		"""Sets a highlight visible"""
		if state == viz.TOGGLE:
			state = not self.getHighlightVisible()
		if not state:
			with self.getRC():
				menu_highlight.dim(self, self.getTheme().dimAmount)
		else:
			with self.getRC():
				menu_highlight.dim(self, self.getTheme().highlightAmount)
	
	def _applyTheme(self, theme): 
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = localTheme.buttonCornerRadius
		localTheme.borderColor = localTheme.textColor
		localTheme.backColor = localTheme.borderColor
		theme = super(ConstrainedGrabbable, self)._applyTheme(localTheme)
		return theme


class VScrollbarPanel(Group):
	"""A vertical panel which expands with its content."""
	def __init__(self,
					scrollPanel=None,
					scrollableTarget=None,
					container=None,
					**kwargs):
		
		self._scrollPanel = scrollPanel
		self._scrollableTarget = scrollableTarget
		self._container = container
		
		self._scrollPercentage = 0
		
		# add the vertical scroll panel
		super(VScrollbarPanel, self).__init__(**kwargs)
		
		# create the control panel
		self.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_CENTER,
													verticalAlignment=layout.ALIGN_JUSTIFY))
		
		# add an arrow texture
		self._arrowTexture = None
		with self.getRC():
			self._arrowTexture = viz.addTexture(self._theme.arrowIcon)
		
		# Add arrows to control panel
		# up
		upArrow = TextureQuadButton(texture=self._arrowTexture,
									maxSize=[self.getInteriorSize()[0], None])
		upArrow.addOnHoldCallback(self._scrollPage, mag=-0.05)
		upArrow.setEuler(0, 0, -90)
		self._upArrow = upArrow
		self.addChild(upArrow)
		
		# add a constrained gui
		self._thumbContainer = Group(size=self.getInteriorSize(),
										sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_REMAINING],
										sizeReference=[1.0, 1.0])
		self._thumbContainer.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_CENTER,
												verticalAlignment=layout.ALIGN_TOP))
		self._thumb = ConstrainedGrabbable(size=[self.getInteriorSize()[0], 0.05],
										sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS],
										sizeReference=[1.0, 1.0])
		self._thumbContainer.addChild(self._thumb)
		self.addChild(self._thumbContainer)
		self._thumb.setUpdateCallback(self._moveTo)
		
		# down
		downArrow = TextureQuadButton(texture=self._arrowTexture,
										maxSize=[self.getInteriorSize()[0], None])
		downArrow.addOnHoldCallback(self._scrollPage, mag=0.05)
		downArrow.setEuler(0, 0, 90)
		self._downArrow = downArrow
		self.addChild(downArrow)
	
	def _moveTo(self, scrollPercent, diff=None):
		"""Moves the card holder to the given index."""
		if diff is None:
			diff = max(0, self._scrollableTarget.getSize()[1] - self._container.getInteriorSize()[1])
		
		with self.getRC():
			if diff <= 0:
				scrollPercent = 0
			
			if scrollPercent >= 1 or diff <= 0:
				self._downArrow.alpha(0.0)
			else:
				self._downArrow.alpha(1.0)
			if scrollPercent <= 0 or diff <= 0:
				self._upArrow.alpha(0.0)
			else:
				self._upArrow.alpha(1.0)
			
			self._scrollPercentage = max(0, min(1, scrollPercent))
			self._scrollPanel._moveToImpl(scrollPercent, diff)
	
	def _scrollPage(self, mag):
		"""Scrolls the page by the given amount (relative movement)."""
		totalHeight = self._scrollableTarget.getSize()[1]
		currentAdj = self._container.getInteriorSize()[1]*mag
		
		diff = max(0, totalHeight - self._container.getInteriorSize()[1])
		totalAdj = self._scrollPercentage*diff + currentAdj
		
		# distance comes from scroll percent * scrollable distance
#		newPos = self._startPosition + [0, totalAdj, 0]
		if diff > 0:
			scrollPercentage = max(0, min(1, totalAdj/diff))
		else:
			scrollPercentage = 0
		self._moveTo(scrollPercentage, diff)
		self._thumb.setPercentageY(scrollPercentage)
	
	def updateThumbSize(self):
		"""Thumb size should be same percentage of parent as scroll window is"""
		totalHeight = self._scrollableTarget.getSize()[1]
		diff = max(0, totalHeight - self._container.getInteriorSize()[1])
		if diff > 0:
			size = self._thumb.getSize()
			windowPercent = self._container.getInteriorSize()[1] / totalHeight
			size[1] = windowPercent * self._thumbContainer.getInteriorSize()[1]
			self._thumb.setSize(size)
			self._thumb.setVisible(True)
		else:
			self._thumb.setVisible(False)


class ScrollPanel(Panel):
	"""A panel object which allows for scrolls to fit the child objects"""
	def __init__(self, size, **kwargs):
		self._mainPanel = None
		self._vscrollPanel = None
		self._initialized = False
		
		super(ScrollPanel, self).__init__(size=size,
											padding=0.002,
											**kwargs)
		# add a side panel so we have a place to put in children
		interiorSize = self.getInteriorSize()
		
		scrollBarWidth = 0.05
		self.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_LEFT,
									verticalAlignment=layout.ALIGN_TOP))
		
		# add a main panel
		self._mainPanelHolder = Group(size=[interiorSize[0]-scrollBarWidth, interiorSize[1]],
										padding=0.002,
										sizeReference=[1, 1],
										sizeMode=[SIZE_MODE_PERCENT_REMAINING, SIZE_MODE_PERCENT_PARENT])
		self._mainPanelHolder.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_LEFT,
												verticalAlignment=layout.ALIGN_TOP))
		super(ScrollPanel, self).addChild(self._mainPanelHolder)
		
		self._mainPanel = VGroup(size=[interiorSize[0]-scrollBarWidth, interiorSize[1]],
										sizeReference=[1, 1],
										sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS])
		self._mainPanel.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_LEFT,
												verticalAlignment=layout.ALIGN_TOP))
		self._mainPanelHolder.addChild(self._mainPanel)
		
		self._vscrollPanel = VScrollbarPanel(scrollPanel=self,
											scrollableTarget=self._mainPanel,
											container=self._mainPanelHolder,
											size=[scrollBarWidth, interiorSize[1]],
											padding=0.002,
											sizeMode=[SIZE_MODE_METERS, SIZE_MODE_PERCENT_PARENT],
											sizeReference=[1, 1])
		super(ScrollPanel, self).addChild(self._vscrollPanel)
		
		self._initialized = True
		# store the start position of the main panel
		self._startPosition = vizmat.Vector(self._mainPanel.getPosition())
	
	def getMainPanel(self):
		"""Returns the main panel
		
		@return Panel()
		"""
		return self._mainPanel
	
	def addChild(self, *args, **kwargs):
		"""Adds a new child"""
		self._mainPanel.addChild(*args, **kwargs)
		self._mainPanelHolder.refreshLayout()
		self.refreshLayout()
	
	def refreshLayout(self, *args, **kwargs):
		"""Refreshes the layout of the GUI."""
		super(ScrollPanel, self).refreshLayout(*args, **kwargs)
		if self._initialized:
			self._mainPanelHolder.getLayout().refresh(self._mainPanelHolder, self._mainPanelHolder.getChildren())
			self._startPosition = vizmat.Vector(self._mainPanel.getPosition())
			
			diff = max(0, self._mainPanel.getSize()[1] - self._mainPanelHolder.getInteriorSize()[1])
			self._vscrollPanel._moveTo(0, diff)
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self._overlay:
			return self._overlay.getSelectables()
		selectables = self._mainPanel.getSelectables()
		selectables += self._vscrollPanel.getSelectables()
		return selectables
	
	def _moveToImpl(self, scrollPercent, diff):
		"""Moves the card holder to the given index."""
		with self.getRC():
			if diff <= 0:
				scrollPercent = 0
			
			self._scrollPercentage = max(0, min(1, scrollPercent))
			
			# distance comes from scroll percent * scrollable distance
			newPos = self._startPosition + [0, self._scrollPercentage*diff, 0]
			self._mainPanel.runAction(vizact.moveTo(newPos, time=0.05, interpolate=vizact.easeInOut))
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the quad"""
		super(ScrollPanel, self)._applySize(size=size,
												padding=padding)
		if self._vscrollPanel:
			self._vscrollPanel.updateThumbSize()
		return size
	
	def setSize(self, *args, **kwargs):
		"""Applies the given size to the quad"""
		super(ScrollPanel, self).setSize(*args, **kwargs)
		if self._vscrollPanel:
			self._vscrollPanel.updateThumbSize()


class ListPanel(VGroup):
	"""A panel object which displays a list of items"""
	def __init__(self, size, numCols=2, rowTheme=None, colWidths=None, **kwargs):
		self._title = None
		self._rowList = []
		
		super(ListPanel, self).__init__(size=size,
										**kwargs)
		self._numCols = numCols
		self._rowPadding = 0.01
		self._rowTheme = rowTheme
		rowLayout = layout.VBox(horizontalAlignment=layout.ALIGN_LEFT)
		if colWidths is None:
			colWidths = []
		self._colWidths = colWidths[:]
		self.setLayout(rowLayout)
	
	def addTitle(self, itemList, theme=None):
		"""Adds a title to the list panel"""
		if theme is None:
			theme = copy.deepcopy(self._theme)
			theme.backColor[3] = 1.0
			theme.borderColor[3] = 1.0
			theme.cornerRadius = 0
		if not self._title:
			self._title = self.addRow(itemList, theme, colWidths=[1.0, 0])
		return self._title
	
	def addRow(self, itemList, theme=None, colWidths=None):
		"""Adds a row of items to the list of items."""
		if  colWidths is None:
			colWidths = self._colWidths
		
		fullWidth = self.getInteriorSize()[0]
		fullHeight = self.getInteriorSize()[1]
		innerWidth = fullWidth-self._rowPadding*2
		innerHeight = fullHeight-self._rowPadding*2
		i = 0
		
		# fit the child into the given width
		for child in itemList:
#			child.setMargin(0.02)
			child._applySize([innerWidth*colWidths[i], innerHeight])
			child.refreshLayout()
			i += 1
		
		# get the max height of the bounding box of each child
		rowHeight = layout.getMaxHeight(itemList)
		
		# add a panel with the full width, and necessary height
		if theme is None:
			theme = copy.deepcopy(self._theme)
			c = len(self.getChildren())+1
			if self._title:
				c += 1
			c %= 2
			theme.backColor = [i+i*c for i in theme.backColor]
			theme.backColor[3] = 1.0
			theme.borderColor = [i+i*c for i in theme.borderColor]
			theme.borderColor[3] = 1.0
			theme.cornerRadius = 0
		
#		rowPanel = VPanel(theme=theme,
#							size=[fullWidth, rowHeight+self._rowPadding*2])#,
##							padding=self._rowPadding)
		rowPanel = VGroup(theme=theme,
							size=[fullWidth, rowHeight+self._rowPadding*2],
							sizeReference=[1, 1],
							sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS],
							padding=self._rowPadding)
		rowLayout = layout.HBox(horizontalAlignment=layout.ALIGN_LEFT,
								verticalAlignment=layout.ALIGN_BOTTOM)
		rowLayout.setFixedWidthList(colWidths)
		rowPanel.setLayout(rowLayout)
#		rowPanel.setPadding(0.02)
		
		# add children to the row panel
		for child in itemList:
			rowPanel.addChild(child)
		
		self._rowList.append(rowPanel)
		
		self.addChild(rowPanel)
		if itemList:
			rowPanel.refreshLayout()
		for panel in self._children:
			panel.refreshLayout()
		for panel in self._children:
			panel.refreshLayout()
		
		self.refreshLayout()
		
		return rowPanel
	
	def _setTheme(self, theme, recurse=True):
		"""Internal set theme"""
		theme = copy.deepcopy(theme)
		self._localTheme = self._applyTheme(theme)
		self._theme = theme
		
		self._applySize(self._size)
		self.refreshLayout()
		
		for overlay in self._overlayStack:
			overlay._setTheme(theme)
		
		if recurse:
			if self._title:
				titleTheme = copy.deepcopy(self._theme)
				titleTheme.backColor[3] = 1.0
				titleTheme.borderColor[3] = 1.0
				titleTheme.cornerRadius = 0
				self._title._setTheme(titleTheme)
			
			for i, row in enumerate(self._rowList):
				rowTheme = copy.deepcopy(theme)
				rowTheme.borderColor = rowTheme.backColor
				rowTheme.backColor = [c+c*(i%2) for c in rowTheme.backColor]
				rowTheme.backColor[3] = 1.0
				rowTheme.borderColor = [c+c*(i%2) for c in rowTheme.borderColor]
				rowTheme.borderColor[3] = 1.0
				rowTheme.cornerRadius = 0
				row._setTheme(rowTheme)
		
		self._applySize(self._size)
		self.refreshLayout()


class Icon(Panel, DimHighlightable):
	"""A icon GUI including representation and text."""
	def __init__(self, representation, text, **kwargs):
		self._text = text
		self._representation = representation
		self._representation.setSize([0.2, 0.2])
		
		super(Icon, self).__init__(size=[0.2, representation.getBoundingBox().height+0.15], **kwargs)
		self.setLayout(layout.VBox())
		with self.getRC():
			self._quadBorder.disable(viz.COLOR_WRITE)
			self._quadInterior.disable(viz.COLOR_WRITE)
		
		self.addChild(self._representation)
		
		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
		repWidth = representation.getSize()[0]
		self._textNode.setSize([repWidth, repWidth*0.75])
		
		self._textPanel = Panel(size=[0.2, 0.15])
		self._textPanel.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER))
		self._textPanel.addChild(self._textNode)
		self.addChild(self._textPanel)
		self._textPanel.refreshLayout()
		self.refreshLayout()
		
		DimHighlightable.__init__(self, self._theme)


class CardPanel(Group):
	"""A card panel class. Holds cards (Panels) in a card holder manipulated by
	a control panel at the bottom.
	"""
	def __init__(self, controlPanelHeight=0.07,
					autoHideControlPanel=False,
					*args, **kwargs):
		self._controlPanel = None
		self._dotPanel = None
		self._rightArrow = None
		self._leftArrow = None
		self._cardHolder = None
		self._autoHideControlPanel = autoHideControlPanel
		self._controlPanelSelectables = []
		
		super(CardPanel, self).__init__(padding=0.0,
										*args, **kwargs)
		
		self._cardHolderLayout = layout.HBox(horizontalAlignment=layout.ALIGN_LEFT)
		
		self.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_LEFT))
		self._useNumbers = False
		
		self._currentCardIndex = 0
		with self.getRC():
			self._pageAdvanceSound = viz.add('resources/sounds/page_advance.wav')
			self._pageAdvanceSound.stop()
		
		self._controlPanelHeight = controlPanelHeight
		
		# create the card holder
		cardSize = [self.getInteriorSize()[0],
					self.getInteriorSize()[1]-self._controlPanelHeight]
		self._cardScreen = Panel(size=cardSize,
										sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_REMAINING],
										sizeReference=[1, 1],
										padding=0.002)
		self._cardScreen._quadInterior.disable(viz.COLOR_WRITE)
		self._cardScreen._quadBorder.disable(viz.COLOR_WRITE)
		self.addChild(self._cardScreen)
		self._cardScreen.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_TOP,
														horizontalAlignment=layout.ALIGN_LEFT))
		
		cardSize = [self.getInteriorSize()[0],
					self.getInteriorSize()[1]-self._controlPanelHeight]
		self._cardHolder = Group(size=cardSize,
									sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_PARENT],
									sizeReference=[1, 1])
		self._cardScreen.addChild(self._cardHolder)
		self._cardHolder.setLayout(self._cardHolderLayout)
		
		# create the control panel
		self._controlPanel = Panel(padding=0.0,
									size=[self.getInteriorSize()[0], self._controlPanelHeight],
									sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS],
									sizeReference=[1, 1])
		self._controlPanel.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_JUSTIFY, verticalAlignment=layout.ALIGN_CENTER))
		
		self._dotPanel = Group(size=[self.getInteriorSize()[0]*0.8, self._controlPanelHeight],
									sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_PARENT],
									sizeReference=[0.8, 1])
		self._dotPanel.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_CENTER, verticalAlignment=layout.ALIGN_CENTER))
		# hide control panel?
#		self._controlPanel._quadInterior.disable(viz.COLOR_WRITE)
#		self._controlPanel._quadBorder.disable(viz.COLOR_WRITE)
		
		# add an arrow texture
		self._arrowTexture = None
		with self.getRC():
			self._arrowTexture = viz.addTexture(self._theme.arrowIcon)
		# add a dot texture
		self._dotTexture = None
		with self.getRC():
			self._dotTexture = viz.addTexture(self._theme.dotIcon)
		
		# Add arrows to control panel
		# left
		self._leftArrow = TextureQuadButton(texture=self._arrowTexture,
											maxSize=[None, self._controlPanel.getInteriorSize()[1]*0.6])
		self._leftArrow.addOnReleaseCallback(self._scrollPage, mag=-1)
		self._leftArrow.alpha(0.1)
		# right
		self._rightArrow = TextureQuadButton(texture=self._arrowTexture,
											maxSize=[None, self._controlPanel.getInteriorSize()[1]*0.6])
		self._rightArrow.addOnReleaseCallback(self._scrollPage, mag=1)
		self._rightArrow.setEuler(0, 0, 180)
		
		self._controlPanel.addChild(self._leftArrow)
		self._controlPanel.addChild(self._dotPanel)
		self._controlPanel.addChild(self._rightArrow)
		
		# refresh the layout of the control panel
		self.addChild(self._controlPanel)
		
		self.addCard()
		
		self.refreshLayout()
		self._updateControlPanelIcons(self._currentCardIndex)
	
	def addCard(self):
		"""Adds a card to the card layout"""
		cardSize = [self.getInteriorSize()[0],
					self.getInteriorSize()[1]-self._controlPanelHeight]
		card = Group(size=cardSize,
						sizeMode=[SIZE_MODE_SYNC, SIZE_MODE_SYNC],
						sizeReference=[self._cardScreen, self._cardScreen])
		self._cardHolder.addChild(card)
		card.setLayout(layout.ListWrap(horizontalAlignment=layout.ALIGN_JUSTIFY,
										lastLineAlignment=layout.ALIGN_LEFT,
										singleLineAlignment=layout.ALIGN_JUSTIFY,
										unifySpacing=True))
		self._cardHolder.refreshLayout()
		
		self._addControlIcon()
		self._cardHolder.refreshLayout()
		self._controlPanel.refreshLayout()
		self.refreshLayout()
		self._updateControlPanelIcons(self._currentCardIndex)
		
		return card
	
	def refreshLayout(self, recurse=True):
		"""Refreshes the layout of the GUI."""
		if recurse:
			for child in self._children:
				child.refreshLayout()
		if self._layout:
			self._layout.refresh(self, self._children)
		if self._cardHolder:
			self._cardHolder.setLayout(self._cardHolderLayout)
			self._cardScreen.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_TOP,
														horizontalAlignment=layout.ALIGN_LEFT))
			self._cardScreen.refreshLayout()
			self._cardScreen.setLayout(None)
			self._cardHolder.setLayout(None)
			self._startPosition = vizmat.Vector(self._cardHolder.getPosition())
		if self._dotPanel and self._dotPanel.getChildren():
			self._moveTo(self._currentCardIndex, forceRefresh=True, immediate=True)
	
	def _addControlIcon(self):
		"""Adds a control icon"""
		if self._useNumbers:
			icon = Text('{}'.format(len(self._cardHolder.getChildren())), lineHeight=self._theme.lineHeight, margin=[0, 0.04, 0, 0.04])
		else:
			icon = TextureQuadButton(texture=self._dotTexture,
										maxSize=[None, self._controlPanel.getInteriorSize()[1]*0.6],
										margin=[0, 0.04, 0, 0.04])
		# have the icon reference the 
		icon.addOnReleaseCallback(self._setPage, index=len(self._cardHolder.getChildren())-1)
		self._dotPanel.addChild(icon)
#		width = layout.getTotalWidth(self._cardHolder.getChildren())
#		self._cardHolder.setSize([width, self._cardHolder.getSize()[1]])
	
	def getCurrentCard(self):
		"""Returns the current card for the card holder
		
		@return Panel()
		"""
		return self._cardHolder.getChildren()[self._currentCardIndex]
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self._overlay:
			return self._overlay.getSelectables()
		return self._controlPanelSelectables + self.getCurrentCard().getSelectables()
	
	def _moveTo(self, index, wrap=False, forceRefresh=False, immediate=False):
		"""Moves the card holder to the given index."""
		with self.getRC():
			if wrap:
				index = index % len(self._cardHolder.getChildren())
			else:
				index = max(0, min(len(self._cardHolder.getChildren())-1, index))
			
			if self._currentCardIndex == index and not forceRefresh:
				return
			
			self._updateControlPanelIcons(index)
			
			cardWidth = self.getInteriorSize()[0] + self._cardHolder.getPadding()[0]
			newPos = self._startPosition-[index*cardWidth-self._cardHolder.getBoundedBoundingBox().width/2.0+self.getInteriorSize()[0]/2.0, 0, 0]
			if immediate:
				self._cardHolder.clearActions()
				self._cardHolder.setPosition(newPos)
			else:
				self._cardHolder.runAction(vizact.moveTo(newPos, speed=4, interpolate=vizact.easeInOut))
			
			if self._currentCardIndex != index:
				self._pageAdvanceSound.stop()
				self._pageAdvanceSound.play()
			
			self._currentCardIndex = index
		
		self._refreshSelectables()
	
	def _scrollPage(self, mag):
		"""Scrolls the page by the given amount (relative movement)."""
		self._moveTo(self._currentCardIndex+mag)
	
	def _setPage(self, index):
		"""Sets the page to the given index."""
		self._moveTo(index, wrap=True)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		# set the theme for the control panel
		if self._controlPanel:
			controlPanelTheme = copy.deepcopy(theme)
#			controlPanelTheme.cornerRadius = controlPanelTheme.buttonCornerRadius
			controlPanelTheme.borderColor = controlPanelTheme.textColor
			self._controlPanel._setTheme(controlPanelTheme)
			for child in self._controlPanel.getChildren():
				child.color(theme.textColor)
			for child in self._dotPanel.getChildren():
				child.color(theme.textColor)
			with self.getRC():
				self._dotTexture = viz.addTexture(self._theme.dotIcon)
		return super(CardPanel, self)._applyTheme(theme)
	
	def _updateControlPanelIcons(self, index):
		"""Refreshes which of the control panel items are selectable"""
		with self.getRC():
			dotPanelChildren = self._dotPanel.getChildren()
			self._controlPanelSelectables = [self._leftArrow, self._rightArrow]+self._dotPanel.getChildren()[:]
			for child in self._controlPanelSelectables:
				child.alpha(1.0)
				child.color(self._theme.textColor)
				menu_highlight.reset(child)
			
			# hide arrows if necessary
			if index == 0:
				self._leftArrow.alpha(0)
				self._controlPanelSelectables.remove(self._leftArrow)
			if index == len(dotPanelChildren)-1:
				self._rightArrow.alpha(0)
				self._controlPanelSelectables.remove(self._rightArrow)
			# change local button
			dotPanelChildren[index].color([0]*3+[1])
			self._controlPanelSelectables.remove(dotPanelChildren[index])
	
	def _setTheme(self, theme, recurse=True):
		"""Internal set theme"""
		super(CardPanel, self)._setTheme(theme, recurse=recurse)
		self._cardScreen._internalDepth = 1
		self._cardScreen._quadInterior.visible(True)
		self._updateControlPanelIcons(self._currentCardIndex)
	
	def _postSetTheme(self):
		for child in self._children:
			child._postSetTheme()
		self._moveTo(self._currentCardIndex, forceRefresh=True, immediate=True)
	
	def _updateSize(self, parentSize):
		"""Applies the given size to the quad"""
		# trigger updates of the size of the child nodes
		super(CardPanel, self)._updateSize(parentSize)
		
		# now that the cards are updated, redetermine how many items we need per card
		cardList = self._cardHolder.getChildren()[:]
		# get a list of the children
		fullChildList = []
		for i, card in enumerate(cardList):
			fullChildList += card.getChildren()[:]
		remainingChildList = fullChildList[:]
		
		for i, card in enumerate(cardList):
			# get a clear list to which we can add extra children
			overflowChildren = []
			
			# get the next card
			nextCard = None
			if i+1 < len(cardList):
				nextCard = cardList[i+1]
			
			card.getLayout().refresh(card, remainingChildList)
			while card.getLayout().isFull():
				overflowChildren.append(remainingChildList.pop())
				card.getLayout().refresh(card, remainingChildList)
			
			if len(overflowChildren) == len(fullChildList):
				break
			
			# reset the children for this node
			card.removeChildren()
			for child in remainingChildList:
				card.addChild(child)
			
			# if we have extra cards with now children remove them
			if not overflowChildren:
				while len(self._cardHolder.getChildren()) > i+1:
					if self._currentCardIndex == len(self._cardHolder.getChildren())-1:
						self._moveTo(self._currentCardIndex-1)
					self._cardHolder.removeChild(self._cardHolder.getChildren()[-1])
					self._dotPanel.removeChild(self._dotPanel.getChildren()[-1])
				break
			
			# if we have extra children ensure we have an extra card
			if overflowChildren and not nextCard:
				nextCard = self.addCard()
			
			# remove the extra children from this card
			for child in overflowChildren:
				# add them to the next card
				nextCard.insertChild(0, child)
			
			remainingChildList = overflowChildren[:]
		
		if self._autoHideControlPanel:
			self._controlPanel.setVisible(len(self._cardHolder.getChildren()) > 1)


class TabPanel(Group):
	"""A tab panel class. Holds tabs (Panels) in a tab holder manipulated by
	a tab panel at the bottom.
	"""
	def __init__(self, *args, **kwargs):
		super(TabPanel, self).__init__(*args, **kwargs)
		self.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_LEFT))
		self._tabPanelHeight = 0.06
		
		self._currentCardTitle = None
		self._tabDict = collections.OrderedDict()
		self._tabButtonDict = collections.OrderedDict()
		
		# set the theme used for the tabs
		self._tabTheme = themes.getDarkTheme()
		self._tabTheme.borderColor = [1]*4
		
		# create the tab holder
		self._tabSize = [self.getInteriorSize()[0],
						self.getInteriorSize()[1]-self._tabPanelHeight]
		self._tabHolder = Group(size=self._tabSize)
		self._tabHolder.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_LEFT))
		
		# create the tab panel
		self._tabPanel = Group(size=[self.getInteriorSize()[0],
										self._tabPanelHeight])
		tabLayout = layout.HBox(horizontalAlignment=layout.ALIGN_JUSTIFY,
								verticalAlignment=layout.ALIGN_BOTTOM)
		self._tabPanel.setLayout(tabLayout)
		
		# refresh the layout of the tab panel
		self._tabPanel.refreshLayout()
		self.addChild(self._tabPanel)
		self.addChild(self._tabHolder)
		
		self.refreshLayout()
		self._startPosition = vizmat.Vector(self._tabHolder.getPosition())
	
	def addTab(self, title):
		"""Adds a tab to the tab panel."""
		with self.getRC():
	#		self._tabTheme.backColor = (0.2*len(self._tabDict), 0.8-0.2*len(self._tabDict), 0.2, 1.0)
			tab = Panel(theme=self._tabTheme, size=self._tabSize, padding=self._tabTheme.borderSize)
	#		tab.disable(viz.COLOR_WRITE)
			self._tabHolder.addChild(tab)
			self._tabHolder.refreshLayout()
			interiorSize = self._tabPanel.getInteriorSize()
			self._tabDict[title] = tab
			# resize the tab holder
			width = layout.getTotalWidth(self._tabHolder.getChildren())
			self._tabHolder.setSize([width, self._tabSize[1]])
			self._tabHolder.refreshLayout()
			
			# add a button for the tab
			tabCount = len(self._tabDict)
			pct = 1.0/float(max(2.0, tabCount))
			availableWidth = interiorSize[0]
			sep = 0
			if tabCount > 1:
				sep = 0.01*(tabCount-1)
			buttonSize = [availableWidth*pct-sep, interiorSize[1]]
			for button in self._tabPanel.getChildren():
				button.setSize(buttonSize)
			
			button = TabButton(size=buttonSize,
								text=title,
								monitorRelease=False,
								theme=self._tabTheme)
			button.addOnReleaseCallback(self._moveTo, title=title)
			button.refreshLayout()
			
	#		button.START_HIGHLIGHT_RESTORE_COLOR = vizmat.Vector(button.getColor())
			
			self._tabPanel.addChild(button)
			self._tabPanel.refreshLayout()
			self._tabButtonDict[title] = button
			
			self.refreshLayout()
			self._refreshSelectables()
			if self._currentCardTitle is None:
				self._moveTo(title)
			else:
				self._moveTo(self._currentCardTitle)
			return tab
	
	def getCurrentCardTitle(self):
		"""Returns the title of the current card.
		
		@return ""
		"""
		return self._currentCardTitle
	
	def getTab(self, title):
		"""Returns the tab with the given title.
		
		@return Panel()
		"""
		return self._tabDict[title]
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self._overlay:
			return self._overlay.getSelectables()
		if self._currentCardTitle:
			return self._tabPanel.getSelectables()#+ self._tabDict[self._currentCardTitle].getSelectables()
		else:
			return []
	
	def _moveTo(self, title):
		"""Moves the tab holder to the given index."""
		with self.getRC():
			self._currentCardTitle = title
			for child in self._tabDict.values():
				child.setVisible(False)
			for child in self._tabButtonDict.values():
				child.setVisible(True)
	#			child.alpha(1.0)
	#			child.HIGHLIGHT_RESTORE_COLOR = vizmat.Vector(child.START_HIGHLIGHT_RESTORE_COLOR)*0.5
				child.forceHighlight = False
				child._connectorQuad.visible(False)
				child.setHighlightVisible(self._tabButtonDict[title], False)
	#			menu_highlight.dim(child, 0.5)
			index = self._tabDict.keys().index(title)
			self._tabDict[title].setVisible(True)
			# change local button
	#		self._tabButtonDict[title].HIGHLIGHT_RESTORE_COLOR = vizmat.Vector(self._tabButtonDict[title].START_HIGHLIGHT_RESTORE_COLOR)
			self._tabButtonDict[title].forceHighlight = True
			self._tabButtonDict[title]._connectorQuad.visible(True)
	#		menu_highlight.dim(self._tabButtonDict[title], 1.0)
			self._tabButtonDict[title].setHighlightVisible(self._tabButtonDict[title], True)
			
			tabWidth = self.getInteriorSize()[0] + self._tabHolder.getPadding()[0]
			newPos = self._startPosition-[index*tabWidth-self._tabHolder.getBoundedBoundingBox().width/2.0+self.getInteriorSize()[0]/2.0, 0, 0]
			self._tabHolder.setPosition(newPos)
			self._refreshSelectables()


class TabButton(Panel, DimHighlightable):
	"""Class for text buttons. Text surrounded by a panel item."""
	def __init__(self, size, text, padding=None, **kwargs):
		self._text = text
		
		padding = [theme.borderSize]*4
		padding[_B] = 0
		
		interiorSize = [size[0]-(padding[_L]+padding[_R]),
						(padding[_T]+padding[_B])]
		self._connectorQuad = None
		with self.getRC():
			self._connectorQuad = vizshape.addQuad(size=interiorSize, cornerRadius=theme.cornerRadius)
			self._connectorQuad.setPosition([0, -(size[1]+interiorSize[1])/2.0, 0])
			self._connectorQuad.disable(viz.INTERSECTION)
			self._connectorQuad.disable(viz.LIGHTING)
			self._connectorQuad.disable(viz.DEPTH_TEST)
		
		super(TabButton, self).__init__(size=size, padding=padding, **kwargs)
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
		interiorSize = self.getInteriorSize()
		self._textNode.setSize([interiorSize[0], interiorSize[1]])
		self.addChild(self._textNode)
		
		with self.getRC():
			self._connectorQuad.setParent(self._quadBorder)
		
		sgDepth = self._getSGDepth()
		if self._usingBorder:
			with self.getRC():
				s = viz.StencilFunc()
				s.func = viz.GL_EQUAL
				s.funcRef = self._stencilDepth
				s.zpass = viz.GL_KEEP
				self._connectorQuad.stencilFunc(s)
				self._connectorQuad.drawOrder(self._baseDepthOffset+(sgDepth+1)*100)
				self._connectorQuad.disable(viz.DEPTH_TEST)
		
		self.refreshLayout()
		
		DimHighlightable.__init__(self, self._theme)
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the object."""
		size = self._getConstrainedSize(size)
		oldSize = self._size[:]
		if padding is None:
			padding = self._padding
		oldInteriorSize = [oldSize[0]-(self._padding[_L]+self._padding[_R]),
							(self._padding[_T]+self._padding[_B])]
		interiorSize = [size[0]-(padding[_L]+padding[_R]),
						(padding[_T]+padding[_B])]
		with self.getRC():
			for i in range(0, self._connectorQuad.getVertexCount()):
				vert = self._connectorQuad.getVertex(i)
				vert[0] *= interiorSize[0]/oldInteriorSize[0]
				vert[1] *= interiorSize[1]/oldInteriorSize[1]
				self._connectorQuad.setVertex(i, vert)
		
		super(TabButton, self)._applySize(size, padding=padding)
		
		self._size = size
		return size
	
	def _applyTheme(self, theme): 
		"""Applies the given theme, if applicable"""
		with self.getRC():
			self._connectorQuad.alpha(theme.backColor[3])
			self._connectorQuad.color(theme.backColor)
		return super(TabButton, self)._applyTheme(theme)
	
	def getBoundedBoundingBox(self):
		"""Wrapper around the bounding box function.
		
		@return viz.BoundingBox()
		"""
		with self.getRC():
			for child in self._children:
				viz.VizNode.setParent(child, viz.WORLD)
			self._connectorQuad.setParent(viz.WORLD)
		bb = self.getBoundingBox()
		bb.width = min(bb.width, self._size[0])
		bb.height = min(bb.height, self._size[1])
		bb.size = [bb.width, bb.height, bb.depth]
		with self.getRC():
			for child in self._children:
				viz.VizNode.setParent(child, self)
			self._connectorQuad.setParent(self)
		return bb
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self.getVisible():
			return [self]
		else:
			return []



class NextButton(PanelButton):
	"""Convenience class holding a next button"""
	def __init__(self, text, size, **kwargs):
		nextPanel = Group(size=size)
		nextPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
											horizontalAlignment=layout.ALIGN_CENTER))
		texture = viz.add('resources/icons/back.png')
		self._imageNode = TextureQuad(maxSize=[size[0]*0.4, size[1]*0.8],
													texture=texture)
		self._imageNode.setEuler([0, 0, 180])
		nextPanelTextWrapper = Group(size=[size[0]*0.6, size[1]],
														margin=[0, 0, 0, 0.01])
		nextPanelTextWrapper.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
														horizontalAlignment=layout.ALIGN_CENTER))
		nextPanelTextWrapper.addChild(Text(text=text))
		nextPanel.addChild(nextPanelTextWrapper)
		nextPanel.addChild(self._imageNode)
		
		super(NextButton, self).__init__(size=size,
											panel=nextPanel,
											monitorRelease=False,
											**kwargs)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		self._imageNode.color(localTheme.textColor)
		return super(NextButton, self)._applyTheme(localTheme)


class BarredPanel(Group):
	"""Class for a message box. Message boxes are inherently overlays"""
	def __init__(self, size, title=None, buttonMask=0, **kwargs):
		self._titleWrapper = None
		self._bpSize = 0.1
		self._buttonMask = buttonMask
		self._buttons = []
		
		super(BarredPanel, self).__init__(size=size)
		self.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_TOP,
									horizontalAlignment=layout.ALIGN_CENTER))
		
		mainSize = size[:]
		if title:
			titleBarHeight = self._theme.H4*2
			titleBarWidth = mainSize[0]
			
			titleSize = [titleBarWidth, titleBarHeight]
			
			self._titleWrapper = TitleGroup(theme=self._theme, size=titleSize, title=title)
			mainSize[1] -= self._titleWrapper.getSize()[1]
			self.addChild(self._titleWrapper)
		
		self._bottomGroup = None
		
		if buttonMask != 0:
			self._bottomGroup = Group(size=[size[0], self._bpSize],
										padding=0.02,
										sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_METERS],
										sizeReference=[1.0, 1.0])
			mainSize[1] -= self._bottomGroup.getSize()[1]
		
		self._mainGroup = Group(size=mainSize,
								sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_REMAINING],
								sizeReference=[1.0, 1.0])
		
		self.addChild(self._mainGroup)
		if self._bottomGroup:
			self.addChild(self._bottomGroup)
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		return []
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		titleBarHeight = theme.H4*2
		titleBarWidth = self.getSize()[0]
		titleSize = [titleBarWidth, titleBarHeight]
		if self._titleWrapper:
			self._titleWrapper.setSize(titleSize)
		
		self.setSize(self.getSize())
		
		return super(BarredPanel, self)._applyTheme(theme)
	
	def _backCallbackFunction(self):
		"""Callback triggered when moving back a page or hiding an overlay"""
		self._hideMessageBox()


class MessageBox(BarredPanel):
	"""Class for a message box. Message boxes are inherently overlays"""
	def __init__(self, size, text, title=None, buttonMask=BUTTON_OK, padding=0.0, hideOnClose=True, **kwargs):
		self._text = text
		self._hideOnClose = hideOnClose
		buttonMask = buttonMask&(~BUTTON_BACK)
		
		super(MessageBox, self).__init__(size=size,
											title=title,
											padding=padding,
											buttonMask=buttonMask,
											**kwargs)
		self._mainGroup.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_TOP,
												horizontalAlignment=layout.ALIGN_CENTER))
		
		self._mainPanel = Group(size=self._mainGroup.getSize(),
								sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_REMAINING],
								sizeReference=[0.9, 1.0])
		self._mainPanel.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_TOP,
												horizontalAlignment=layout.ALIGN_CENTER))
		self._mainGroup.addChild(self._mainPanel)
		self._mainGroup.refreshLayout()
		interiorSize = self._mainPanel.getInteriorSize()
		
		self._textNode = Text(text, lineHeight=self._theme.lineHeight)
		self._textNode.setSize([interiorSize[0]*0.9, interiorSize[1]*0.85-0.1])
		self._mainPanel.addChild(self._textNode)
		
#		self._buttonPanel = Group(size=[interiorSize[0], interiorSize[1]*0.10])
		self._buttonPanel = self._bottomGroup
		
		if self._buttonPanel:
			if buttonMask == BUTTON_BACK:
				self._buttonPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
													horizontalAlignment=layout.ALIGN_LEFT))
			elif buttonMask == BUTTON_NEXT:
				self._buttonPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
													horizontalAlignment=layout.ALIGN_RIGHT))
			else:
				self._buttonPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
														horizontalAlignment=layout.ALIGN_CENTER))
			
			interiorSize = self._buttonPanel.getInteriorSize()
			btnHeight = interiorSize[1]
			# ok
			self._okButton = None
			if buttonMask & BUTTON_OK:
				self._okButton = OutlineButton(size=[interiorSize[0]*0.2, btnHeight],
											text='OK')#theme=getBlueTheme())
				self._okButton.addOnReleaseCallback(self._hideMessageBox)
				self._buttonPanel.addChild(self._okButton)
				self._buttons.append(self._okButton)
			# cancel
			self._cancelButton = None
			if buttonMask & BUTTON_CANCEL:
				self._cancelButton = OutlineButton(size=[interiorSize[0]*0.2, btnHeight],
											text='Cancel')#theme=getBlueTheme())
				self._cancelButton.addOnReleaseCallback(self._hideMessageBox)
				self._buttonPanel.addChild(self._cancelButton)
				self._buttons.append(self._cancelButton)
			# next
			self._nextButton = None
			if buttonMask & BUTTON_NEXT:
				self._nextButton = NextButton(size=[interiorSize[0]*0.2, btnHeight],
													text="Continue")
				self._nextButton.addOnReleaseCallback(self._hideMessageBox)
				self._buttonPanel.addChild(self._nextButton)
				self._buttons.append(self._nextButton)
			
			self._buttonPanel.refreshLayout()
		self.refreshLayout()
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		return self._buttons + super(MessageBox, self).getSelectables()
	
	def _hideMessageBox(self):
		"""hides the message box and removes it as an overlay."""
		if self._overlayParent:
			if self._hideOnClose:
				self.setParent(viz.WORLD)
				self.setVisible(False)
			self._overlayParent.removeOverlay(self.overlayId, delete=not self._hideOnClose)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.borderColor = theme.textColor
		localTheme.cornerRadius = theme.overlayCornerRadius
		return super(MessageBox, self)._applyTheme(localTheme)


class MessagePanelBox(BarredPanel):
	"""Class for a message box. Message boxes are inherently overlays"""
	def __init__(self, size, title=None, panel=None, buttonMask=BUTTON_OK, padding=0.0, hideOnClose=True, **kwargs):
		self._mainPanel = panel
		self._hideOnClose = hideOnClose
		buttonMask = buttonMask&(~BUTTON_BACK)
		
		super(MessagePanelBox, self).__init__(size=size,
												title=title,
												padding=padding,
												buttonMask=buttonMask,
												**kwargs)
		self._mainGroup.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_TOP,
												horizontalAlignment=layout.ALIGN_CENTER))
		
		if self._mainPanel:
			intSize = self._mainGroup.getInteriorSize()
			self._mainPanel.setSize(intSize)
			self._mainGroup.addChild(self._mainPanel)
			self._mainGroup.refreshLayout()
		
		self._buttonPanel = self._bottomGroup
		
		if self._buttonPanel:
			if buttonMask == BUTTON_BACK:
				self._buttonPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
														horizontalAlignment=layout.ALIGN_LEFT))
			elif buttonMask == BUTTON_NEXT:
				self._buttonPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
														horizontalAlignment=layout.ALIGN_RIGHT))
			else:
				self._buttonPanel.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_CENTER,
														horizontalAlignment=layout.ALIGN_CENTER))
			
			interiorSize = self._buttonPanel.getInteriorSize()
			btnHeight = interiorSize[1]
			# ok
			self._okButton = None
			if buttonMask & BUTTON_OK:
				self._okButton = OutlineButton(size=[interiorSize[0]*0.2, btnHeight],
												text='OK')#theme=getBlueTheme())
				self._okButton.addOnReleaseCallback(self._hideMessageBox)
				self._buttonPanel.addChild(self._okButton)
				self._buttons.append(self._okButton)
			# cancel
			self._cancelButton = None
			if buttonMask & BUTTON_CANCEL:
				self._cancelButton = OutlineButton(size=[interiorSize[0]*0.2, btnHeight],
													text='Cancel')#theme=getBlueTheme())
				self._cancelButton.addOnReleaseCallback(self._hideMessageBox)
				self._buttonPanel.addChild(self._cancelButton)
				self._buttons.append(self._cancelButton)
			# next
			self._nextButton = None
			if buttonMask & BUTTON_NEXT:
				self._nextButton = NextButton(size=[interiorSize[0]*0.2, btnHeight],
												text="Continue")
				self._nextButton.addOnReleaseCallback(self._hideMessageBox)
				self._buttonPanel.addChild(self._nextButton)
				self._buttons.append(self._nextButton)
			
			self._buttonPanel.refreshLayout()
		self.refreshLayout()
	
	def setMainPanel(self, panel):
		"""Allows the main panel to be set for this message box type"""
		if not self._mainPanel:
			self._mainPanel = panel
			intSize = self._mainGroup.getInteriorSize()
			self._mainPanel.setSize(intSize)
			self._mainGroup.addChild(self._mainPanel)
			self.refreshLayout()
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		list = self._buttons
		if self._mainPanel:
			list += self._mainPanel.getSelectables()
		list += super(MessagePanelBox, self).getSelectables()
		return list
	
	def _hideMessageBox(self):
		"""hides the message box and removes it as an overlay."""
		if self._overlayParent:
			if self._hideOnClose:
				self.setParent(viz.WORLD)
				self.setVisible(False)
			self._overlayParent.removeOverlay(self.overlayId, delete=not self._hideOnClose)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.borderColor = theme.textColor
		localTheme.cornerRadius = theme.overlayCornerRadius
		
		return super(MessagePanelBox, self)._applyTheme(localTheme)


class CursorIcon(TextureQuad):
	"""A specialized TextureQuad with a rep for the cursor"""
	def __init__(self, theme, **kwargs):
		super(CursorIcon, self).__init__(texture=viz.add(theme.cursorIcon), **kwargs)
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		self._setTexture(texture=viz.add(theme.cursorIcon))
		self.setSize(theme.cursorSize)
		self.setPosition(theme.cursorHotSpot[0]*theme.cursorSize[0]*0.5,
							theme.cursorHotSpot[1]*theme.cursorSize[1]*0.5,
							0)
		return super(CursorIcon, self)._applyTheme(theme)


class Cursor(Panel):
	"""Class for a cursor panel. This class holds a CursorIcon.
	"""
	def __init__(self, **kwargs):
		super(Cursor, self).__init__(size=[0.1, 0.1], **kwargs)
		self._quadBorder.disable(viz.COLOR_WRITE)
		self._quadInterior.disable(viz.COLOR_WRITE)
		
#		self.setLayout(layout.HBox(verticalAlignment=layout.ALIGN_BOTTOM, horizontalAlignment=layout.ALIGN_RIGHT))
		self._endQuad = CursorIcon(theme=self._theme,
									maxSize=[None, None],
									sizeMode=[SIZE_MODE_PERCENT_PARENT]*2,
									sizeReference=[1]*2)
		self._endQuad.disable(viz.INTERSECTION)
		self._endQuad.disable(viz.LIGHTING)
		
		self.addChild(self._endQuad)
		self.disable(viz.INTERSECTION)
		self.disable(viz.LIGHTING)
		self.refreshLayout()
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		self._localTheme = copy.deepcopy(theme)
		super(Cursor, self)._applyTheme(theme)
		self.setSize([theme.cursorSize[0]*2, theme.cursorSize[1]*2])
		self.setPosition(theme.cursorHotSpot+[0])
		return theme


class NavigationBar(Group):
	"""Base class for a bar with navigation controls"""
	def __init__(self,
					size,
					matchButtonHeight=True,
					buttonMask=BUTTON_CANCEL|BUTTON_BACK):#|BUTTON_MIN_MAX
		self._matchButtonHeight = matchButtonHeight
		
		self._mainWindow = None
		self._navigatedPanel = None
		self._spacerList = []
		self._buttonList = []
		
		self._backPanelButton = None
		self._homePanelButton = None
		self._hidePanelButton = None
		self._minimizePanelButton = None
		self._maximizePanelButton = None
		
		if self._matchButtonHeight:
			size[1] = 0.1
		
		super(NavigationBar, self).__init__(size=size, padding=0)
		self.setLayout(layout.HBox(horizontalAlignment=layout.ALIGN_CENTER,
									verticalAlignment=layout.ALIGN_CENTER))
		
		buttonSize = self._findButtonSize()
		if self._matchButtonHeight:
			self.setSize([self.getSize()[0], buttonSize[1]])
		
		buttonCount = 0
		for i in range(0, 10):
			if buttonMask&(2**i):
				buttonCount += 1
		spacerCount = buttonCount+1
		spacerSize = [(size[0]-buttonSize[0]*buttonCount)/spacerCount, size[1]]
		
		# add a spacer
		if buttonCount > 0:
			self._addSpacer(spacerSize)
		
		# add a back button
		if buttonMask&BUTTON_BACK:
			if self._theme.helpIndex == 0:
				self._backPanelButton = TextureQuadButton(maxSize=buttonSize,
															texture=viz.add(self._theme.backIcon),
															themeSyncAttribute='backIcon')
			elif self._theme.helpIndex == 1:
				self._backPanelButton = ImageAndTextPanelButton(size=buttonSize,
																textNode=Header(index=4, text='Back'),
																texture=viz.add(self._theme.backIcon),
																themeSyncAttribute='backIcon')
			else:
				self._backPanelButton = TextButton(size=buttonSize,
													text='BACK')
			self.addChild(self._backPanelButton)
			self._buttonList.append(self._backPanelButton)
			
			# add a spacer
			self._addSpacer(spacerSize)
		
		# add a home button
		if buttonMask&BUTTON_HOME:
			# add a home button
			if self._theme.helpIndex == 0:
				self._homePanelButton = TextureQuadButton(maxSize=buttonSize,
															texture=viz.add(self._theme.homeIcon),
															themeSyncAttribute='homeIcon')
			elif self._theme.helpIndex == 1:
				self._homePanelButton = ImageAndTextPanelButton(size=buttonSize,
																textNode=Header(index=4, text='Home'),
																texture=viz.add(self._theme.backIcon),
																themeSyncAttribute='homeIcon')
			else:
				self._homePanelButton = TextButton(size=buttonSize,
													text='HOME')
			self.addChild(self._homePanelButton)
			self._buttonList.append(self._homePanelButton)
			
			# add a spacer
			self._addSpacer(spacerSize)
		
		# add a max/minimize button
		if buttonMask&BUTTON_MIN_MAX:
			# add a minimize button
			if self._theme.helpIndex == 0:
				self._minimizePanelButton = TextureQuadButton(maxSize=buttonSize,
																texture=viz.add(self._theme.minimizeIcon),
																themeSyncAttribute='minimizeIcon')
			else:
				self._minimizePanelButton = ImageAndTextPanelButton(size=buttonSize,
																	textNode=Header(index=4, text='Minimize'),
																	texture=viz.add(self._theme.minimizeIcon),
																	themeSyncAttribute='minimizeIcon')
			self.addChild(self._minimizePanelButton)
			self._buttonList.append(self._minimizePanelButton)
			
			# add a maximize button
			self._maximizePanelButton = TextureQuadButton(maxSize=buttonSize,
															texture=viz.add(self._theme.maximizeIcon),
															themeSyncAttribute='maximizeIcon')
			self.addChild(self._maximizePanelButton)
			self._buttonList.append(self._maximizePanelButton)
			self._maximizePanelButton.setVisible(False)
			
			# add a spacer
			self._addSpacer(spacerSize)
			
			self._minTT = WorldOverlay(size=[0.3, 0.1],
									text='Click here to minimize your window',
									theme=self._theme,
									baseOffset=50,
									baseDepthOffset=MAX_DRAW_DEPTH_OFFSET)
			
			self._minimizePanelButton.setTT(self._minTT)
			self._minTT.setStateFunction(self._minimizePanelButton.setHighlightVisible, self._minimizePanelButton.getHighlightVisible)
			
			self._maxTT = WorldOverlay(size=[0.3, 0.1],
									text='Your window has been minimized, grab here to maximize again',
									theme=self._theme,
									baseOffset=50,
									baseDepthOffset=MAX_DRAW_DEPTH_OFFSET)
			
			self._maximizePanelButton.setTT(self._maxTT)
		
		# add a close/hide button
		if buttonMask&BUTTON_CANCEL:
			if self._theme.helpIndex == 0:
				self._hidePanelButton = TextureQuadButton(maxSize=buttonSize,
															texture=viz.add(self._theme.cancelIcon),
															themeSyncAttribute='cancelIcon')
			elif self._theme.helpIndex == 1:
				self._hidePanelButton = ImageAndTextPanelButton(size=buttonSize,
																textNode=Header(index=4, text='Close'),
																texture=viz.add(self._theme.cancelIcon),
																themeSyncAttribute='cancelIcon')
			else:
				self._hidePanelButton = TextButton(size=buttonSize,
													text='CLOSE')
			
			self._buttonList.append(self._hidePanelButton)
			self.addChild(self._hidePanelButton)
			# add a spacer
			self._addSpacer(spacerSize)
			
			self._hideTT = WorldOverlay(size=[0.3, 0.125],
										text='Your window has been closed, press the left control key to show again',
										theme=self._theme,
										baseOffset=50,
										baseDepthOffset=MAX_DRAW_DEPTH_OFFSET)
			
			self._hidePanelButton.setTT(self._hideTT)
	
	def setNavigatedPanel(self, navigatedPanel, mainWindow):
		"""Sets the navigated panel for the navigation bar"""
		self._mainWindow = mainWindow
		self._navigatedPanel = navigatedPanel
		if self._backPanelButton:
			self._backPanelButton.addOnReleaseCallback(self._navigatedPanel.back)
		if self._homePanelButton:
			self._homePanelButton.addOnReleaseCallback(self._navigatedPanel.home)
		if self._hidePanelButton:
			self._hidePanelButton.addOnReleaseCallback(self.hide)
			self._hideTT.setSetFunction(self._mainWindow.setAllVisible)
			self._hideTT.setGetFunction(lambda: (not self._mainWindow.getVisible()))
#			self._hideTT.setHideFunction(self._mainWindow, 'setVisible')
#			self._hidePanelButton.setTT(self._hideTT)
		if self._minimizePanelButton:
			self._minimizePanelButton.addOnReleaseCallback(self.minimize)
		if self._maximizePanelButton:
			self._maximizePanelButton.addOnReleaseCallback(self.maximize)
			self._maxTT.setShowFunction(self._mainWindow.minimize)
			self._maxTT.setHideFunction(self._mainWindow.maximize)
			self._maximizePanelButton.setTT(self._maxTT)
	
	def setButtonEnabled(self, buttonMask, state):
		"""Sets a buttion as enabled/disabled given the mask and state"""
		if buttonMask&BUTTON_BACK:
			if self._backPanelButton:
				self._backPanelButton.setSelectable(state)
				if self._backPanelButton._selectable:
					self._backPanelButton.alpha(1)
					for child in viz.VizNode.getChildren(self._backPanelButton):
						child.alpha(1)
						for s in viz.VizNode.getChildren(child):
							s.alpha(1)
				else:
					self._backPanelButton.alpha(0)
					for child in viz.VizNode.getChildren(self._backPanelButton):
						child.alpha(0)
						for s in viz.VizNode.getChildren(child):
							s.alpha(0)
		self._mainWindow._refreshSelectables()
	
	def hide(self):
		"""Hides the main window."""
		self._mainWindow.setVisible(False)
	
	def maximize(self):
		"""Maximizes the main window"""
		if self._maximizePanelButton and self._mainWindow:
			self._maximizePanelButton.setVisible(False)
			self._minimizePanelButton.setVisible(True)
			self.refreshLayout()
			self._mainWindow.maximize()
			self._mainWindow._refreshSelectables()
	
	def minimize(self):
		"""Minimizes the main window"""
		if self._minimizePanelButton and self._mainWindow and not self._mainWindow._minimized:
			self._maximizePanelButton.setVisible(True)
			self._minimizePanelButton.setVisible(False)
			self.refreshLayout()
			self._mainWindow.minimize(self._maximizePanelButton)
			self._mainWindow._refreshSelectables()
	
	def _addSpacer(self, size):
		"""Internal function to add spacers"""
		spacer = Group(size=size)
		self.addChild(spacer)
		self._spacerList.append(spacer)
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the quad"""
		buttonSize = self._findButtonSize()
		if self._matchButtonHeight:
			size[1] = buttonSize[1]
		
		super(NavigationBar, self)._applySize(size=size,
												padding=padding)
		buttonCount = 4
		spacerCount = 5
		spacerSize = [(size[0]-buttonSize[0]*buttonCount)/spacerCount, size[1]]
		for spacer in self._spacerList:
			spacer.setSize(spacerSize)
		self.getRoot().refreshLayout()
		return size
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
#		theme.backColor[3] = 0.1
		theme.cornerRaidus = 0
		theme.buttonCornerRadius = 0
		theme = super(NavigationBar, self)._applyTheme(theme)
#		theme.backColor[3] = 0.1
		theme.cornerRaidus = 0
		theme.buttonCornerRadius = 0
		
		buttonSize = self._findButtonSize(theme)
		if self._matchButtonHeight:
			size = self.getSize()
			self.setSize([size[0], buttonSize[1]])
		
		for button in self._buttonList:
			button.setSize(buttonSize)
		
		self.getRoot().refreshLayout()
		
		return theme
	
	def _findButtonSize(self, theme=None):
		"""Internal function to find the button size
		@return []
		"""
		if theme is None:
			theme = self._theme
		size = [theme.H3]*2
		if self._theme.helpIndex > 0:
			size[0] = theme.H3*4
		return size


class WorldPanel(Group):
	"""A panel which is meant to be the base item of a set of GUINodes in world coordinates."""
	def __init__(self,
					size,
					padding=0,
					**kwargs):
		for window in viz.getWindowList():
			window.setClearMask(viz.GL_COLOR_BUFFER_BIT|viz.GL_DEPTH_BUFFER_BIT|viz.GL_STENCIL_BUFFER_BIT, viz.MASK_SET)
		
		self._selectionEnabled = True
		
		self._node = viz.addGroup()
		with self.getRC():
			self._backPanel = vizshape.addQuad(size=size, cornerRadius=0)
			self._backPanel.enable(viz.INTERSECTION)
			self._backPanel.enable(viz.DEPTH_TEST)
			self._backPanel.setParent(self._node)
		
		self._proxyList = []
		self._selectionTools = []
		super(WorldPanel, self).__init__(size, padding=0, node=self._node, **kwargs)
		
		self._parent3d = viz.WORLD
		self._inTransition = False
		
		self.setParent(viz.WORLD)
		
		self.setTheme(self._theme)
	
	def getContainerNode3d(self):
		"""Returns the vizard node used as a rendering container
		
		@return viz.VizNode()
		"""
		return self._backPanel
	
	def getParent3d(self):
		"""Return the parent vizard node.
		
		@return viz.VizNode()
		"""
		return self._parent3d
	
	def getSelectables(self):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if not self.getVisible():
			selectables = []
		else:
			selectables = super(WorldPanel, self).getSelectables()
		return selectables
	
	def setParent(self, parent):
		"""Function to set the avatar that the embedded control menu follows"""
		with self.getRC():
			viz.VizNode.setParent(self, parent)
		self._parent3d = parent
	
	def setSelectionEnabled(self, state):
		"""Sets the enabled state of selection"""
		if state == viz.TOGGLE:
			state = not self._selectionEnabled
		
		for selectionTool in self._selectionTools:
			selectionTool.getRaw().visible(state)
			selectionTool.getRaw().silentRelease()
		for proxyTool in self._proxyList:
			proxyTool.updateEvent.setEnabled(state)
		
		if state:
			self._refreshSelectables()
		
		self._selectionEnabled = state
	
	def setVisible(self, visibility):
		"""Sets the visible state of this GUI"""
		super(WorldPanel, self).setVisible(visibility)
		self._refreshSelectables()
	
	def _applySize(self, size, padding=None):
		"""Applies the given size to the quad"""
		size = self._getConstrainedSize(size)
		with self.getRC():
			for i in range(0, self._backPanel.getVertexCount()):
				vert = self._backPanel.getVertex(i)
				vert[0] *= size[0]/self._size[0]
				vert[1] *= size[1]/self._size[1]
				self._backPanel.setVertex(i, vert)
		self._size = size
		return size
	
	def _applyTheme(self, theme): 
		"""Applies the given theme, if applicable"""
		with self.getRC():
			self._backPanel.alpha(theme.topBackColor[3])
			self._backPanel.color(theme.topBackColor)
			
			for selectionTool in self._selectionTools:
				selectionTool.getRaw().applyTheme(theme)
		return super(WorldPanel, self)._applyTheme(theme)
	
	def _refreshRenderDepth(self):
		"""Sets the render depth (draw order) of the GUI item."""
		with self.getRC():
			# stencil
			s = viz.StencilFunc()
			s.func = viz.GL_ALWAYS
			s.funcRef = self._stencilDepth
			s.zpass = viz.GL_REPLACE
			self._backPanel.stencilFunc(s)
			# draw order
			viz.VizNode.drawOrder(self._backPanel, self._baseDepthOffset+self._drawOrderIndex)
	
	def _refreshSelectables(self):
		"""Refreshes the list of selectable items and applies it to each of the
		selection tools.
		"""
		with self.getRC():
			for selectionTool in self._selectionTools:
				if selectionTool.getRaw().id == -1:
					viz.logError('**Error: Invalid selection tool')
				elif not hasattr(selectionTool.getRaw(), '_items'):
					viz.logError('**Error: Selection tool removed')
				else:
					selectionTool.getRaw().removeItems(self._prevSelectables[:])
					selectables = self.getSelectables()
					selectionTool.getRaw().addItems(selectables)
					self._prevSelectables = selectables[:]


class NavigatableWorldPanel(WorldPanel):
	"""Class for a world panel which has an attached navigation bar.
	
	Note:
		The NavigatableWorldPanel class has two main children a mainGroup
		which is used for adding pages, and the navigation bar. Children
		should not be added to the NavigatableWorldPanel directly, but should
		be added via the nodes returned by getMainGroup.
	"""
	def __init__(self, navigationBar=None, **kwargs):
		self._navigationBar = navigationBar
		self._mainGroup = None
		self._minimized = False
		self._minMaxTime =  0.3
		
		super(NavigatableWorldPanel, self).__init__(**kwargs)
		
		self._mainGroup = Group(size=self.getInteriorSize())
		self._mainGroup.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_BOTTOM,
												horizontalAlignment=layout.ALIGN_CENTER))
		
		self._navigationBar.setNavigatedPanel(self._mainGroup, self)
		
		self.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_LEFT,
									verticalAlignment=layout.ALIGN_BOTTOM))
		
		self.addChild(self._mainGroup)
		if self._navigationBar:
			self.addChild(self._navigationBar)
		
		self.setSize(self.getSize())
	
	def getMainGroup(self):
		"""Returns the container for adding/accessing pages. Note that
		the NavigatableWorldPanel class has two main children a mainGroup
		which is used for adding pages, and the navigation bar. Children
		should not be added to the NavigatableWorldPanel directly, but should
		be added via the nodes returned by getMainGroup.
		DO NOT ADD CHIDREN DIRECTLY!
		
		@return Group()
		"""
		return self._mainGroup
	
	def getPageContainerGroup(self):
		"""See getMainGroup"""
		return self.getMainGroup()
	
	def getMinimized(self):
		"""Returns True iff minimized
		
		@return bool
		"""
		return self._minimized
	
	def getNavigationBar(self):
		"""Returns the title bar for the window.
		
		@return NavigationBar()
		"""
		return self._navigationBar
	
	def getSelectables(self, *args, **kwargs):
		"""Returns a list of selectable objects.
		
		@return []
		"""
		if self._minimized:
			selectables = []
			if self._navigationBar:
				selectables = [self._navigationBar._maximizePanelButton]
			return selectables
		else:
			return super(NavigatableWorldPanel, self).getSelectables(*args, **kwargs)
	
	def minimize(self, target):
		"""Minimizes the page, a target needs to be set, the minimization will
		shrink down to the target.
		"""
		bpbb = self._backPanel.getBoundingBox()
		ts = target.getSize()
		rs = [1, 1, 1]
		rs[0] = ts[0]/bpbb.width
		rs[1] = ts[1]/bpbb.height
		relPos = self._backPanel.getMatrix(viz.ABS_GLOBAL).inverse().preMultVec(target.getPosition(viz.ABS_GLOBAL))
		self._backPanel.runAction(vizact.parallel(vizact.sizeTo(rs, time=self._minMaxTime),
													vizact.moveTo(relPos, time=self._minMaxTime)))
		self._minimized = True
	
	def maximize(self, animate=True):
		"""Maximizes the page"""
		if animate:
			self._backPanel.runAction(vizact.parallel(vizact.sizeTo([1]*3, time=self._minMaxTime),
														vizact.moveTo([0]*3, time=self._minMaxTime)))
		else:
			self._backPanel.setScale([1]*3)
			self._backPanel.setPosition([0]*3)
		self._minimized = False
	
	def setSize(self, *args, **kwargs):
		"""Set the size as opposed to setting the scale. Setting the scale will
		force the scale for all sub components. Setting the size will change the
		size used for the layout of the components.
		"""
		super(NavigatableWorldPanel, self).setSize(*args, **kwargs)
		interiorSize = self.getInteriorSize()
		if self._navigationBar:
			navigationBarHeight = self._navigationBar.getSize()[1]
			self._navigationBar.setSize([interiorSize[0], navigationBarHeight])
			interiorSize[1] -= navigationBarHeight
		if self._mainGroup:
			self._mainGroup.setSize(interiorSize)
		self.refreshLayout()
	
	def _setTheme(self, theme, recurse=True):
		"""Internal set theme"""
		super(NavigatableWorldPanel, self)._setTheme(theme, recurse=recurse)
		self.setSize(self.getSize())
	
	def setVisible(self, *args, **kwargs):
		"""Toggles visibility, but also ensures that the window is maximized."""
		super(NavigatableWorldPanel, self).setVisible(*args, **kwargs)
		self._navigationBar.maximize()


class WorldOverlay(WorldPanel):
	"""A class for notifications and tool tips"""
	REMOVE = 1
	HIDE = 2
	DISABLE = 4
	
	"""Main class for the event selector menu, should ideally be one per avatar."""
	def __init__(self, size, text, onHide=HIDE, **kwargs):
		self._onHideAction = onHide
		self._text = text
		
		self._anchor = None
		self._showCount = 0
		self._prevFunc = {
			'show':None,
			'hide':None,
			'set':None,
		}
		self._data = {}
		
		super(WorldOverlay, self).__init__(size=size,
											**kwargs)
		self.setLayout(layout.VBox(horizontalAlignment=layout.ALIGN_CENTER,
									verticalAlignment=layout.ALIGN_TOP))
		
		# add a visible panel
		self._panel = Panel(size=size,
						sizeMode=[SIZE_MODE_PERCENT_PARENT, SIZE_MODE_PERCENT_REMAINING],
						sizeReference=[1]*2)
		self._panel.setLayout(layout.VBox(verticalAlignment=layout.ALIGN_CENTER,
									horizontalAlignment=layout.ALIGN_CENTER))
		self.addChild(self._panel)
		
		# add a text node
		interiorSize = self._panel.getInteriorSize()
		self._textNode = Text(text,
								lineHeight=self._theme.lineHeight,
								size=[interiorSize[0]*0.9, interiorSize[1]*0.75],
								sizeMode=[SIZE_MODE_PERCENT_PARENT]*2,
								sizeReference=[1]*2)
		self._panel.addChild(self._textNode)
		
		# add a down icon
		self._anchor = TextureQuad(maxSize=[0.03, 0.03],
									texture=viz.add(self._theme.anchorIcon))
		self.addChild(self._anchor)
		
		self.setSize(size)
		self.setSize([size[0], self._textNode.getBoundingBox().height+0.1])
		self._updateEvent = vizact.onupdate(10000, self._update)
		self.setVisible(False)
	
	def remove(self):
		"""Removes the node and restores any intercepted functions"""
		self._setEnabled(False)
		super(WorldOverlay, self).remove()
		self._updateEvent.remove()
	
	def setEnabled(self, state):
		"""Set the enabled state of the overlay"""
		self._setEnabled(state)
		if self._updateEvent.getEnabled():
			self._showCount = 0
		else:
			self._showCount += 1
	
	def _replaceFunction(self, oldFunc, newFunc, functionName):
		"""Replace an existing function with a wrapper"""
		name = oldFunc.im_func.__name__
		if not functionName in self._prevFunc:
			self._prevFunc[functionName] = oldFunc
		if self._prevFunc[functionName] != newFunc:
			self._data[functionName] = viz.Data(old=oldFunc, new=newFunc)
			setattr(oldFunc.im_self, name, newFunc)
			self._prevFunc[functionName] = oldFunc
		else:
			viz.logWarn('**Warning: reapplying function', self._prevFunc[functionName], newFunc)
	
	def _restoreFunction(self, oldFunc, newFunc, functionName):
		"""Restore the old functions"""
		name = newFunc.im_func.__name__
		setattr(newFunc.im_self, name, newFunc)
		self._prevFunc[functionName] = None
	
	def setHideFunction(self, func):
		"""Set the object and function which trigger the hide function"""
		self._replaceFunction(oldFunc=func,
								newFunc=self._hideWrapper,
								functionName='hide')
	
	def setShowFunction(self, func):
		"""Set the object and function which trigger the show function"""
		self._replaceFunction(oldFunc=func,
								newFunc=self._showWrapper,
								functionName='show')
	
	def setGetFunction(self, getFunc):
		"""Set the getter function for sampling"""
		self._getFunc = getFunc
	
	def setSetFunction(self, func):
		"""sets the setter function for state checks"""
		self._replaceFunction(oldFunc=func,
								newFunc=self._setWrapper,
								functionName='state')
	
	def setStateFunction(self, setFunc, getFunc):
		"""Set the object and functions which will trigger show and hide.
		The set function will be called first then the get function will be
		sampled. The result of the get function will then be paseed to the
		show/hide.
		
		The set function is of the form 'setEnabled' and the get function
		is of the form 'getEnabled'.
		"""
		self._replaceFunction(oldFunc=setFunc,
								newFunc=self._setWrapper,
								functionName='state')
		self._getFunc = getFunc
	
	def setTarget(self, target):
		"""Sets the target GUI node that will be updated in short term"""
		self._target = target
	
	def _applyTheme(self, theme):
		"""Applies the given theme, if applicable"""
		localTheme = copy.deepcopy(theme)
		localTheme.cornerRadius = 0.02
		if self._anchor:
			self._anchor.color(localTheme.backColor)
		self._backPanel.disable(viz.COLOR_WRITE)
		return super(WorldOverlay, self)._applyTheme(localTheme)
	
	def _hideWrapper(self, *args, **kwargs):
		"""Wrapper function for hiding"""
		self._prevFunc['hide'](*args, **kwargs)
		self._onHide()
	
	def _onHide(self):
		"""Function triggered when the 'hide' related function is called"""
		self.setVisible(False)
		if self._showCount > 0:
			if self._onHideAction == self.REMOVE:
				self.remove()
			elif self._onHideAction == self.DISABLE:
				self._setEnabled(False)
			elif self._onHideAction == self.HIDE:
				pass
	
	def _onShow(self):
		"""Function triggered when the 'hide' related function is called"""
		self._showCount += 1
		self.setVisible(True)
		self._setEnabled(True)
	
	def _setEnabled(self, state):
		"""Function which sets the enabled/disabled state of the overlay"""
		currentState = self._updateEvent.getEnabled()
		
		if state == viz.TOGGLE:
			state = not currentState
		self._updateEvent.setEnabled(state)
		
		if state != currentState:
			if state:
				if 'hide' in self._data:
					self.setHideFunction(self._data['hide'].old)
				if 'show' in self._data:
					self.setShowFunction(self._data['show'].old)
				if 'state' in self._data:
					self.setSetFunction(self._data['state'].old)
			else:
				# hide
				if self._prevFunc['hide']:
					self._restoreFunction(self._data['hide'].new, self._data['hide'].old, 'hide')
				# show
				if self._prevFunc['show']:
					self._restoreFunction(self._data['show'].new, self._data['show'].old, 'show')
				# state (set/get)
				if self._prevFunc['state']:
					self._restoreFunction(self._data['state'].new, self._data['state'].old, 'state')
	
	def _setWrapper(self, *args, **kwargs):
		"""Wrapper function for set/get e.g. setEnabled, setVisible, etc"""
		self._prevFunc['state'](*args, **kwargs)
		state = self._getFunc()
		if not state:
			self._onHide()
		else:
			self._onShow()
	
	def _showWrapper(self, *args, **kwargs):
		"""Wrapper function for hiding"""
		self._prevFunc['show'](*args, **kwargs)
		self._onShow()
	
	def _update(self):
		"""Internal update function"""
		# Update the transformation of the node
		mat = self._target.getMatrix(viz.ABS_GLOBAL)
		posOff = [0, self.getSize()[1]/2.0+self._target.getSize()[1]/2.0, -0.01]
		pos = mat.preMultVec(posOff)
		mat.setPosition(pos)
		self.setMatrix(mat, viz.ABS_GLOBAL)

