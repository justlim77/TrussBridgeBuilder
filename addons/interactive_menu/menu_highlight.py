"""Contains highlight tools for embedded gui items"""

import viz
import vizmat
import vizact

import tools


class QuadHighlight(tools.highlighter.Highlight):
	"""Places a box around the highlighted object"""
	
	def __init__(self, theme):
		super(QuadHighlight, self).__init__()
		
		self._theme = theme
		
		self._color = theme.highlightColor
	
	def add(self, node):
		"""Adds a node to the highlight object
		@arg node viz.VizNode()
		"""
		with viz.MainResourceContext:
			if not self.highlightingNode(node):
				if hasattr(node, 'addHighlight'):
					node.addHighlight(node)
					# append the node to the resource list
					self._resourceList.append(viz.Data(node=node, box=None, maskBox=None, link=None))
	
	def getMode(self):
		"""Returns the mode of the highlight"""
		return -1
	
	def getVisible(self, selectedNode):
		"""Returns the visibility of the highlight"""
		with viz.MainResourceContext:
			for data in self._resourceList:
				if data.node == selectedNode:
					if hasattr(data.node, 'getHighlightVisible'):
						return data.node.getHighlightVisible()
					else:
						return data.maskBox.getVisible()
			return False
	
	def remove(self, node=None):
		"""Removes the GUI node."""
		with viz.MainResourceContext:
			if node is None:
				for data in self._resourceList:
					if hasattr(data.node, 'removeHighlight'):
						data.node.removeHighlight(data.node)
					else:
						data.maskBox.remove()
						data.link.remove()
			else:
				for data in self._resourceList:
					if data.node == node:
						if hasattr(data.node, 'removeHighlight'):
							data.node.removeHighlight(data.node)
						else:
							data.maskBox.remove()
							data.link.remove()
		
		super(QuadHighlight, self).remove(node)
	
	def restoreColorForActive(self):
		"""Sets the color of the highlight, if appropriate."""
		with viz.MainResourceContext:
			for data in self._resourceList:
				if data.maskBox:
					data.maskBox.color(self._color)
	
	def setColorForActive(self, color):
		"""Sets the color of the highlight, if appropriate."""
		with viz.MainResourceContext:
			for data in self._resourceList:
				if data.maskBox:
					data.maskBox.color(color)
	
	def setVisible(self, node, *args, **kwargs):
		"""Sets the visibility of the highlight for the node, use in place of
		remove in order to avoid adding and removing extra resources.
		"""
		with viz.MainResourceContext:
			for data in self._resourceList:
				if data.node == node and hasattr(node, 'setHighlightVisible'):
					node.setHighlightVisible(*args, **kwargs)
				elif data.node == node or node == None:
					data.maskBox.visible(*args, **kwargs)
	
	def updateHighlightLinks(self):
		"""update the links for the highlights so that the highlights are in
		the correct locations.
		"""
		with viz.MainResourceContext:
			for data in self._resourceList:
				if data.link:
					data.link.update()


def reset(node):
	"""Dim a node by reducing the brightness of the diffuse color. The previous
	color of the node is stored in the nodes (possibly new) HIGHLIGHT_RESTORE_COLOR
	attribute. All child objects will also be dimmed.
	"""
	with viz.MainResourceContext:
		if hasattr(node, 'HIGHLIGHT_RESTORE_COLOR'):
			node.HIGHLIGHT_RESTORE_COLOR = vizmat.Vector(node.getColor())
		for child in viz.VizNode.getChildren(node):
			reset(child)


def restore(node):
	"""Dim a node by reducing the brightness of the diffuse color. The previous
	color of the node is stored in the nodes (possibly new) HIGHLIGHT_RESTORE_COLOR
	attribute. All child objects will also be dimmed.
	"""
	with viz.MainResourceContext:
		if hasattr(node, 'HIGHLIGHT_RESTORE_COLOR'):
			node.clearActions()
			node.color(node.HIGHLIGHT_RESTORE_COLOR)
		for child in viz.VizNode.getChildren(node):
			restore(child)


def restoreVal(node):
	"""Dim a node by reducing the brightness of the diffuse color. The previous
	color of the node is stored in the nodes (possibly new) HIGHLIGHT_RESTORE_COLOR
	attribute. All child objects will also be dimmed.
	"""
	with viz.MainResourceContext:
		if hasattr(node, 'HIGHLIGHT_RESTORE_COLOR'):
			node.color((node.HIGHLIGHT_RESTORE_COLOR*node.HIGHLIGHT_CURRENT_VAL) + node.HIGHLIGHT_CURRENT_OFF)
		for child in viz.VizNode.getChildren(node):
			restoreVal(child)


def dim(node, val, off=None, fadeTime=0.2):
	"""Dim a node by reducing the brightness of the diffuse color. The previous
	color of the node is stored in the nodes (possibly new) HIGHLIGHT_RESTORE_COLOR
	attribute. All child objects will also be dimmed.
	"""
	with viz.MainResourceContext:
		try:
			if node.forceHighlight:
				keep = False
			else:
				keep = True
		except AttributeError:
			keep = True
		if off is None:
			off = [0]*3
		
		if not keep:
			val = 1.0
		try:
			if fadeTime == 0:
				node.color(node.HIGHLIGHT_RESTORE_COLOR*val+off)
			else:
				node.runAction(vizact.fadeTo(node.HIGHLIGHT_RESTORE_COLOR*val+off, time=fadeTime))
		except AttributeError:
			node.HIGHLIGHT_RESTORE_COLOR = vizmat.Vector(node.getColor())
			if fadeTime == 0:
				node.color(node.HIGHLIGHT_RESTORE_COLOR*val+off)
			else:
				node.runAction(vizact.fadeTo(node.HIGHLIGHT_RESTORE_COLOR*val+off, time=fadeTime))
		node.HIGHLIGHT_CURRENT_VAL = val
		node.HIGHLIGHT_CURRENT_OFF = off[:]
		for child in viz.VizNode.getChildren(node):
			dim(child, val, off)
	#	for child in node.getChildren():
	#		dim(child, val)

