"""Provides features for controlling layouts of immersive menus"""

import vizmat


ALIGN_CENTER = 1
ALIGN_TOP = 2
ALIGN_BOTTOM = 3
ALIGN_LEFT = 4
ALIGN_RIGHT = 5
ALIGN_JUSTIFY = 6

_T = 0
_R = 1
_B = 2
_L = 3


def getMaxHeight(children):
	"""Returns the max height from a set of children.
	
	@return float
	"""
	# filter visible children
	children = [c for c in children if c.getVisible()]
	
	maxHeight = 0
	for child in children:
		margin = child.getMargin()
		bb = child.getBoundedBoundingBox()
		tempSum = bb.height+margin[_T]+margin[_B]
		if tempSum > maxHeight:
			maxHeight = tempSum
	return maxHeight


def getMaxWidth(children):
	"""Returns the max width from a set of children.
	
	@return float
	"""
	# filter visible children
	children = [c for c in children if c.getVisible()]
	
	maxWidth = 0
	for child in children:
		margin = child.getMargin()
		bb = child.getBoundedBoundingBox()
		tempSum = bb.width+margin[_L]+margin[_R]
		if tempSum > maxWidth:
			maxWidth = tempSum
	return maxWidth


def getTotalWidth(children):
	"""Returns the total width for the given set of child objects.
	
	@return float
	"""
	# filter visible children
	children = [c for c in children if c.getVisible()]
	
	# build a padding list
	paddingList = [0]
	for child in children:
		margin = child.getMargin()
		paddingList[-1] = max(paddingList[-1], margin[_L])
		paddingList.append(margin[_R])
	# add padding list together
	totalWidth = sum(paddingList)
	# add child sizes
	for child in children:
		totalWidth += child.getBoundedBoundingBox().width
	return totalWidth


def getTotalHeight(children):
	"""Returns the total height for the given set of child objects.
	
	@return float
	"""
	# filter visible children
	children = [c for c in children if c.getVisible()]
	
	# build a padding list
	paddingList = [0]
	for child in children:
		margin = child.getMargin()
		paddingList[-1] = max(paddingList[-1], margin[_T])
		paddingList.append(margin[_B])
	# add padding list together
	totalHeight = sum(paddingList)
	# add child sizes
	for child in children:
		totalHeight += child.getBoundedBoundingBox().height
	return totalHeight


class BaseLayout(object):
	"""An abstract base layout"""
	
	def getSize(self, parent, children):
		"""Returns the size of the item.
		
		@arg children viz.VizNode()
		"""
		return vizmat.Vector(0, 0, 0)
	
	def refresh(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg parent viz.VizNode()
		@arg children viz.VizNode()
		"""
		pass

#class Absolute(BaseLayout):
#	"""A layout where items are placed using x, y coordinates and
#	not rearranged.
#	"""
#	def refresh(self, parent, children):
#		"""Refreshes the layout using the given parent and children.
#		
#		@arg parent viz.VizNode()
#		@arg children viz.VizNode()
#		"""
#		pass


#class Grid(BaseLayout):
#	"""Places items into a grid"""
#	def refresh(self, parent, children):
#		pass


class Overlapping(BaseLayout):
	"""Places items into a single horizontal line"""
	def __init__(self, verticalAlignment=ALIGN_TOP, horizontalAlignment=ALIGN_CENTER, **kwargs):
		super(Overlapping, self).__init__(**kwargs)
		self._verticalAlignment = verticalAlignment
		self._horizontalAlignment = horizontalAlignment
	
	def getSize(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg children viz.VizNode()
		"""
		return vizmat.Vector(getMaxWidth(children), getMaxHeight(children), 0)
	
	def refresh(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg parent viz.VizNode()
		@arg children viz.VizNode()
		"""
		# filter visible children
		children = [c for c in children if c.getVisible()]
		
		size = parent.getInteriorSize()
		center = parent.getInteriorCenter()
		startPos = vizmat.Vector([(-size[0]/2.0)+center[0], size[1]/2.0+center[1], 0])
		
		for i, child in enumerate(children):
			bb = child.getBoundedBoundingBox()
			
			# top
			top = (bb.height/2.0 + bb.center[1]) - child.getPosition()[1]
			totalHeight = bb.height
			if self._verticalAlignment == ALIGN_TOP:
				y = top
			elif self._verticalAlignment == ALIGN_BOTTOM:
				y = (size[1]-totalHeight)+top
			else:#self._verticalAlignment == ALIGN_CENTER:
				y = (size[1]-totalHeight)/2.0+top
			
			# left
			left = child.getPosition()[0] - bb.center[0]+bb.width/2.0
			totalWidth = bb.width
			if (self._horizontalAlignment == ALIGN_LEFT):
				x = left
			elif self._horizontalAlignment == ALIGN_RIGHT:
				x = (size[0]-totalWidth)+left
			else:#self._horizontalAlignment == ALIGN_CENTER:
				x = (size[0]-totalWidth)/2.0+left
			
			justifyShift = vizmat.Vector(0, 0, 0)
			if (self._horizontalAlignment == ALIGN_JUSTIFY
					and len(children) > 1):
				justifyShift[0] = (size[0]-getTotalWidth(children))/(len(children)-1)
			
			# get the margin
			marginShift = vizmat.Vector(0, 0, 0)
			# y
			if self._verticalAlignment == ALIGN_TOP:
				marginShift[1] = -child.getMargin()[_T]
			elif self._verticalAlignment == ALIGN_BOTTOM:
				marginShift[1] = child.getMargin()[_B]
			# x
			marginShift[0] = child.getMargin()[_L]
			
			centerShift = vizmat.Vector([x, -y, 0])
			child.setPosition(startPos + centerShift + marginShift)
			
			# prep for next cycle
			i += 1


class HBox(BaseLayout):
	"""Places items into a single horizontal line"""
	def __init__(self, verticalAlignment=ALIGN_TOP, horizontalAlignment=ALIGN_CENTER, **kwargs):
		super(HBox, self).__init__(**kwargs)
		self._verticalAlignment = verticalAlignment
		self._horizontalAlignment = horizontalAlignment
		self._fixedWidthList = []
		self._horizontalAlignmentList = []
	
	def setFixedWidthList(self, fixedWidthList):
		"""Set the fixed width list, list of percent of width that col occupies"""
		self._fixedWidthList = fixedWidthList[:]
	
	def setHorizonalAlignList(self, horizontalAlignmentList):
		"""Set a list of alignments on a per item basis, cycles/repeats if list
		is shorter than number of items.
		
		NOTE! only valid if using fixed width lists.
		"""
		self._horizontalAlignmentList = horizontalAlignmentList[:]
	
	def getSize(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg children viz.VizNode()
		"""
		return vizmat.Vector(getTotalWidth(children), getMaxHeight(children), 0)
	
	def refresh(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg parent viz.VizNode()
		@arg children viz.VizNode()
		"""
		# filter visible children
		children = [c for c in children if c.getVisible()]
		
		size = parent.getInteriorSize()
		center = parent.getInteriorCenter()
		startPos = [(-size[0]/2.0)+center[0], size[1]/2.0+center[1], 0]
		# find the corner
		childPos = vizmat.Vector(startPos)
		
		prevChild = None
		for i, child in enumerate(children):
			bb = child.getBoundedBoundingBox()
			top = (bb.height/2.0 + bb.center[1]) - child.getPosition()[1]
			totalHeight = bb.height
			if self._verticalAlignment == ALIGN_TOP:
				y = top
			elif self._verticalAlignment == ALIGN_BOTTOM:
				y = (size[1]-totalHeight)+top
			else:#self._verticalAlignment == ALIGN_CENTER:
				y = (size[1]-totalHeight)/2.0+top
			
			left = child.getPosition()[0] - bb.center[0]+bb.width/2.0
#			left = (bb.width/2.0 + bb.center[0]) - child.getPosition()[0]
			if (self._horizontalAlignment == ALIGN_LEFT
					or self._horizontalAlignment == ALIGN_JUSTIFY):
				x = left
			elif self._horizontalAlignment == ALIGN_RIGHT:
				x = (size[0]-getTotalWidth(children))+left
			else:#self._horizontalAlignment == ALIGN_CENTER:
				x = (size[0]-getTotalWidth(children))/2.0+left
			
			justifyShift = vizmat.Vector(0, 0, 0)
			if (self._horizontalAlignment == ALIGN_JUSTIFY
					and len(children) > 1):
				justifyShift[0] = (size[0]-getTotalWidth(children))/(len(children)-1)
			
			# get the margin
			marginShift = vizmat.Vector(0, 0, 0)
			# y
			if self._verticalAlignment == ALIGN_TOP:
				marginShift[1] = -child.getMargin()[_T]
			elif self._verticalAlignment == ALIGN_BOTTOM:
				marginShift[1] = child.getMargin()[_B]
			# x
			marginShift[0] = child.getMargin()[_L]
			if prevChild:
				marginShift[0] = max(marginShift[0], prevChild.getMargin()[_R])
			
			centerShift = vizmat.Vector([x, -y, 0])
			child.setPosition(childPos + centerShift + marginShift)
			
			if self._fixedWidthList and i < len(self._fixedWidthList):
				fixWidth = vizmat.Vector([self._fixedWidthList[i]*size[0], 0, 0])
				if self._horizontalAlignmentList:
					haIndex = i % len(self._horizontalAlignmentList)
					ha = self._horizontalAlignmentList[haIndex]
					if ha == ALIGN_LEFT:
						centerShift[0] = left
						child.setPosition(childPos + centerShift + marginShift)
					elif ha == ALIGN_RIGHT:
						child.setPosition(childPos
											+vizmat.Vector([fixWidth[0] - (bb.width + child.getMargin()[_R]-left), centerShift[1]+marginShift[1], 0]))
					else:# ha == ALIGN_CENTER
						child.setPosition(fixWidth+child.getPosition())
				childPos += fixWidth
			else:
				# add in justify shift for next child
				childPos += justifyShift
				childPos += vizmat.Vector([bb.width+marginShift[0], 0, 0])
			
			# prep for next cycle
			prevChild = child
			i += 1


class VBox(BaseLayout):
	"""Places items into a single vertical line"""
	def __init__(self, verticalAlignment=ALIGN_TOP, horizontalAlignment=ALIGN_CENTER, useMarginsAlongBorders=True, **kwargs):
		super(VBox, self).__init__(**kwargs)
		self._verticalAlignment = verticalAlignment
		self._horizontalAlignment = horizontalAlignment
		self._fixedHeightList = []
		self._useMarginsAlongBorders = useMarginsAlongBorders
	
	def setFixedHeightList(self, fixedHeightList):
		"""Set the fixed width list, list of percent of width that col occupies"""
		self._fixedHeightList = fixedHeightList[:]
	
	def refresh(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg parent viz.VizNode()
		@arg children viz.VizNode()
		"""
		# filter visible children
		children = [c for c in children if c.getVisible()]
		
		size = parent.getInteriorSize()
		center = parent.getInteriorCenter()
		startPos = [(-size[0]/2.0)+center[0], size[1]/2.0+center[1], 0]
		
		# margins added to border test, not just inbetween items
		if children and self._useMarginsAlongBorders:
			if (self._verticalAlignment == ALIGN_TOP
					or self._verticalAlignment == ALIGN_JUSTIFY):
				startPos[1] -= children[0].getMargin()[_T]
			
			if (self._verticalAlignment == ALIGN_BOTTOM):
				startPos[1] += children[-1].getMargin()[_B]
		
		# find the corner
		childPos = vizmat.Vector(startPos)
		
		totalHeight = 0
		if self._verticalAlignment != ALIGN_TOP:
			totalHeight = getTotalHeight(children)
		
		prevChild = None
		for i, child in enumerate(children):
			bb = child.getBoundedBoundingBox()
			top = (bb.height/2.0 + bb.center[1]) - child.getPosition()[1]
			if (self._verticalAlignment == ALIGN_TOP
					or self._verticalAlignment == ALIGN_JUSTIFY):
				y = top
			elif self._verticalAlignment == ALIGN_BOTTOM:
				y = (size[1]-totalHeight)+top
			else:#self._verticalAlignment == ALIGN_CENTER:
				y = (size[1]-totalHeight)/2.0+top
			
			left = child.getPosition()[0] - bb.center[0]+bb.width/2.0
#			left = (bb.width/2.0 + bb.center[0]) - child.getPosition()[0]
			if self._horizontalAlignment == ALIGN_LEFT:
				x = left
			elif self._horizontalAlignment == ALIGN_RIGHT:
				x = (size[0]-bb.width)+left
			else:#self._horizontalAlignment == ALIGN_CENTER:
				x = (size[0]-bb.width)/2.0+left
			
			justifyShift = vizmat.Vector(0, 0, 0)
			if (self._verticalAlignment == ALIGN_JUSTIFY
					and len(children) > 1):
				justifyShift[1] = -(size[1]-getTotalHeight(children))/(len(children)-1)
			
			marginShift = vizmat.Vector(0, 0, 0)
			if self._horizontalAlignment == ALIGN_LEFT:
				marginShift[0] = child.getMargin()[_L]
			elif self._horizontalAlignment == ALIGN_RIGHT:
				marginShift[0] = -child.getMargin()[_R]
			
			# get the vertical margin
			marginShift[1] = child.getMargin()[_T]
			if prevChild:
				marginShift[1] = max(marginShift[1], prevChild.getMargin()[_B])
			marginShift[1] = -marginShift[1]
			
			prevChild = child
			
			centerShift = vizmat.Vector([x, -y, 0])
			child.setPosition(childPos + centerShift + marginShift)
			
			# add in justify shift for next child
			childPos += justifyShift
			
			if self._fixedHeightList and i < len(self._fixedHeightList):
				childPos += vizmat.Vector([0, -self._fixedHeightList[i]*size[1], 0])
			else:
				childPos += vizmat.Vector([0, -bb.height+marginShift[1], 0])
	
	def getSize(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg children viz.VizNode()
		"""
		# filter visible children
		children = [c for c in children if c.getVisible()]
		return vizmat.Vector(getMaxWidth(children), getTotalHeight(children), 0)


class ListWrap(BaseLayout):
	"""Places items into a grid by placing items into rows. New rows are added
	when the items pass the interior width provided by the parent object.
	"""
	def __init__(self,
					horizontalAlignment=ALIGN_CENTER,
					lastLineAlignment=None,
					singleLineAlignment=None,
					unifySpacing=False,
					**kwargs):
		super(ListWrap, self).__init__(**kwargs)
		self._horizontalAlignment = horizontalAlignment
		self._unifySpacing = unifySpacing
		self._verticalAlignment = ALIGN_TOP
		if lastLineAlignment is None:
			lastLineAlignment = self._horizontalAlignment
		self._lastLineAlignment = lastLineAlignment
		if singleLineAlignment is None:
			singleLineAlignment = self._horizontalAlignment
		self._singleLineAlignment = singleLineAlignment
		self._full = False
		self._rowCount = 0
	
	def refresh(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg parent viz.VizNode()
		@arg children viz.VizNode()
		"""
		# filter visible children
		children = [c for c in children if c.getVisible()]
		
		size = parent.getInteriorSize()
		center = parent.getInteriorCenter()
		startPos = [(-size[0]/2.0)+center[0], size[1]/2.0+center[1], 0]
		# find the corner
		childPos = vizmat.Vector(startPos)
		
		colPadding = vizmat.Vector(0, 0, 0)
		rowPadding = vizmat.Vector(0, 0, 0)
		
		prevChild = None
		rowPos = vizmat.Vector(0, 0, 0)
		maxHeight = 0
		currentRow = []
		currentWidth = 0
		jusifySpacing = None
		self._rowCount = 0
		
		for child in children:
			child.setPosition([0]*3)
			bb = child.getBoundedBoundingBox()
			childHeight = bb.height
#			if self._verticalAlignment == ALIGN_TOP:
#				childHeight += child.getMargin()[_T]
#			elif self._verticalAlignment == ALIGN_BOTTOM:
#				childHeight += child.getMargin()[_B]
			childHeight += child.getMargin()[_B] + child.getMargin()[_T]
			
			margin = child.getMargin()[_L]
			if prevChild:
				margin = max(margin, prevChild.getMargin()[_R])
			prevChild = child
			childPos[0] += margin
			
			if childHeight > maxHeight:
				maxHeight = childHeight
			# check if we need to go down a row, find proposed right hand border
			centerShift = vizmat.Vector([bb.width/2.0, -bb.ymax, 0])
			rightHandBorder = childPos[0] + bb.width
			
			# get the margin
			marginShift = vizmat.Vector(0, 0, 0)
			if self._verticalAlignment == ALIGN_TOP:
				marginShift[1] = -child.getMargin()[_T]
			elif self._verticalAlignment == ALIGN_BOTTOM:
				marginShift[1] = child.getMargin()[_B]
			
			# handle a new line
			if rightHandBorder-0.0001 > size[0]/2.0 + center[0]:# add some margin of error
				rowPos -= vizmat.Vector(0, maxHeight, 0) + rowPadding
				if (self._horizontalAlignment == ALIGN_JUSTIFY
						and len(currentRow) > 1):
					jusifySpacing = (size[0]-currentWidth-currentRow[-1].getMargin()[_R])/(len(currentRow)-1)
					justifyShift = 0
					for prevRowChild in currentRow:
						cp = prevRowChild.getPosition()
						cp[0] += justifyShift
						prevRowChild.setPosition(cp)
						justifyShift += jusifySpacing
				currentWidth = 0
				self._rowCount += 1
				currentRow = []
				childPos = vizmat.Vector(startPos) + rowPos
				childPos[0] += child.getMargin()[_L]
				maxHeight = childHeight
			currentRow.append(child)
			
			child.setPosition(childPos + centerShift + marginShift)
			childPos += colPadding + [bb.width, 0, 0]
			# compute the total width to this point
			currentWidth = childPos[0]-startPos[0]
		
		# handle last line
		lastLineAlignment = self._lastLineAlignment
		if self._rowCount == 0:# if it's the only line 
			lastLineAlignment = self._singleLineAlignment
		
		xoff = 0
		if lastLineAlignment == ALIGN_RIGHT:
			xoff = (size[0]-getTotalWidth(currentRow))
		elif lastLineAlignment == ALIGN_CENTER:
			xoff = (size[0]-getTotalWidth(currentRow))/2.0
		
		if (lastLineAlignment == ALIGN_JUSTIFY
				and len(currentRow) > 1):
			jusifySpacing = (size[0]-currentWidth-currentRow[-1].getMargin()[_R])/(len(currentRow)-1)
			justifyShift = 0
			for prevRowChild in currentRow:
				cp = prevRowChild.getPosition()
				cp[0] += justifyShift
				prevRowChild.setPosition(cp)
				justifyShift += jusifySpacing
		elif self._unifySpacing and jusifySpacing is not None:
			justifyShift = 0
			for prevRowChild in currentRow:
				cp = prevRowChild.getPosition()
				cp[0] += justifyShift + xoff
				prevRowChild.setPosition(cp)
				justifyShift += jusifySpacing
		else:
			jusifySpacing = 0.0
			justifyShift = 0
			for prevRowChild in currentRow:
				cp = prevRowChild.getPosition()
				cp[0] += justifyShift + xoff
				prevRowChild.setPosition(cp)
				justifyShift += jusifySpacing
		
		bottomY = -rowPos[1] + maxHeight
		if bottomY < size[1]:
			self._full = False
		else:
			self._full = True
	
	def isFull(self):
		"""Returns true if the layout can't contain all of the items it has."""
		return self._full
	
	def getFullRowCount(self):
		"""Returns the number of full rows"""
		return self._rowCount


class ColGrid(BaseLayout):
	"""Lays items out in a column based grid"""
	def __init__(self, *args, **kwargs):
		super(ColGrid, self).__init__(*args, **kwargs)
		self._numCols = 2
	
	def refresh(self, parent, children):
		"""Refreshes the layout using the given parent and children.
		
		@arg parent viz.VizNode()
		@arg children viz.VizNode()
		"""
		# filter visible children
		children = [c for c in children if c.getVisible()]
		
		# determine the width of each colum (width of widest item)
#		i = 0
#		self._colWidths = [0]*self._numCols
#		for child in children:
#			col = i % self._numCols
#			bb = child.getBoundedBoundingBox()
#			if bb.width < self._colWidths[col]:
#				self._colWidths[col] = bb.width
#			i += 1
		
		# determine height of each row
		i = 0
		rowHeights = [0]*(int(len(children)/self._numCols)+1)
		for child in children:
			row = int(i / self._numCols)
			bb = child.getBoundedBoundingBox()
			if bb.height > rowHeights[row]:
				rowHeights[row] = bb.height
			i += 1
		
		# determine
		size = parent.getInteriorSize()
		center = parent.getInteriorCenter()
		startPos = vizmat.Vector([(-size[0]/2.0)+center[0], size[1]/2.0+center[1], 0])
		# find the corner
		colPadding = vizmat.Vector(0, 0, 0)
		rowPadding = vizmat.Vector(0, 0, 0)
		i = 0
		for child in children:
			row = int(i / self._numCols)
			col = i % self._numCols
			bb = child.getBoundedBoundingBox()
			
			pos = vizmat.Vector(sum(self._colWidths[0:col]), -sum(rowHeights[0:row]), 0)
			pos += colPadding*float(col)# + vizmat.Vector([bb.width/2.0, 0, 0])
			pos += rowPadding*float(row)# + vizmat.Vector([0, bb.height/2.0, 0])
			final = startPos+pos
			child.setPosition(final)
			i += 1


