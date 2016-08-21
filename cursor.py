# Copyright (c) 2001-2016 WorldViz LLC.
# All rights reserved.

# viztracker also includes a library of tracking functions that can be used by customers in their scripts, and
# so these are included here as well. You can use these without having to run any of the above code.
#

"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DO NOT MODIFY CODE BELOW - LEGACY VIZTRACKER CODE EXPECTED BY SOME VIZARD DEMO SCRIPTS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

import viz
import vizact
import vizcam
import vizinfo

_CameraTracker = vizcam.addCameraTracker

def MousePos(**kw):
	"""Legacy viztracker: Add a position mouse tracker"""
	return MouseTracker(**kw)

##_________TRACKER________
#canvas = viz.addGUICanvas()
## Reduce canvas FOV from default 50 to 40
#sc = viz.window.getSize()
#print sc,'SCREENSIZE'
##canvas.setRenderWorldOverlay([600,800],fov=30.0,distance=3.0)
#canvas.setRenderWorldOverlay([1200,900],fov=50.0,distance=3.0)
#canvas.setMouseStyle(viz.CANVAS_MOUSE_BUTTON | viz.CANVAS_MOUSE_MOVE)
#canvas.disable(viz.PICKING)

class MouseTracker(viz.VizNode,viz.EventClass):	
	"""Legacy viztracker: Class that provides the ability to turn a 2D mouse into a 3D tracker"""
	def __init__(self,**kw):
		viz.EventClass.__init__(self)
		node = viz.addGroup()
		viz.VizNode.__init__(self,node.id)
#		viz.EventClass.callback(self,viz.UPDATE_EVENT,self.onUpdate)
		self.sPos = [0,0]
		self.length = 100
		
	def setLength(self,length):
		self.length = length
		
	def setPos(self,canvas):
	#	self.sPos = viz.Mouse.getPosition()
		self.sPos = canvas.getCursorPosition(viz.CANVAS_CURSOR_NORMALIZED)
		line = viz.MainWindow.screenToWorld(self.sPos)
		
		line.length=self.length
		self.setPosition(line.end)
		
	def onUpdate(self,e):
#		self.sPos = viz.Mouse.getPosition()
		self.sPos = canvas.getCursorPosition(viz.CANVAS_CURSOR_NORMALIZED)
		line = viz.screentoworld(self.sPos)
		line.length=self._length
		self.setPosition(line.end)
