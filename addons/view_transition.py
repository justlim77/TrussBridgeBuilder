"""Module containing code for view transitions"""

import viz
import vizact
import viztask


POST_SCENE_DRAW_ORDER = 100000


class Fader(object):
	"""A fader transition moving into and out of a fullscreen color mask."""
	def __init__(self, windows=None):
		if windows is None:
			windows = viz.getWindowList()
		# Fade-in/fade-out quad which is used when changing between in-door and out-door scenes.
		self._fadeQuadList = []
		for window in windows:
			if hasattr(window, 'displayNode')\
					and hasattr(window.displayNode, 'getHUD'):
				fadeQuad = viz.addTexQuad(parent=window.displayNode.getHUD(), color=viz.GRAY, pos=(.5, .5, 1.1), scale=(20, 20, 1), euler=[0, 0, 0])
				window.displayNode.getHUD().draworder(POST_SCENE_DRAW_ORDER+100)
			else:
				fadeQuad = viz.addTexQuad(parent=viz.SCREEN, color=viz.GRAY, pos=(.5, .5, 0.1), scale=(20, 20, 1), euler=[0, 0, 0])
			fadeQuad.disable(viz.LIGHTING)
			fadeQuad.disable(viz.DEPTH_TEST)
#			fadeQuad.draworder(POST_SCENE_DRAW_ORDER+100)
			fadeQuad.alpha(0)
			fadeQuad.visible(1)
			fadeQuad.renderOnlyToWindows([window])
			self._fadeQuadList.append(fadeQuad)
		
		# render nodes don't work on some systems
#		rn = viz.addRenderNode()
#		rn.setOrder(viz.POST_RENDER)
#		rn.setHUD(0, 1, 0, 1, renderQuad=True)
#		rn.texture(viz.addTexture('worldviz-logo-white.jpg'))
#		self._fadeQuad = rn
#		self._fadeQuad.alpha(0)
		
		# Add actions for fading in and fading out
		self._fadeIn = vizact.fadeTo(0, time=0.2, interpolate=vizact.easeIn)
		self._fadeOut = vizact.fadeTo(1, time=0.2, interpolate=vizact.easeIn)
		self._inTransition = False
	
	def inTransition(self):
		"""Returns True if the Fader is currently in a transition"""
		return self._inTransition
	
	def runInTransition(self, task=None, *args, **kwargs):
		"""Runs a task inside of the transition. The purpose is for setting a
		task that will happen after the scene fades out, then when the task is
		complete the scene fades back in.
		"""
		self._inTransition = True
		viztask.schedule(self._runInTransitionTask(task, *args, **kwargs))
	
	def _runInTransitionTask(self, task=None, *args, **kwargs):
		"""Actual task method for running in a transition"""
		yield self._fadeOutTask(None)
		if task:
			task(*args, **kwargs)
		yield self._fadeInTask(None)
		self._inTransition = False
	
	def start(self, onComplete=None, *args, **kwargs):
		"""Starts a fade out"""
		self._inTransition = True
		viztask.schedule(self._fadeOutTask(onComplete, *args, **kwargs))
	
	def stop(self, onComplete=None, *args, **kwargs):
		"""Stops the fade, starts a fade in."""
		viztask.schedule(self._fadeInTask(onComplete, *args, **kwargs))
	
	def _fadeOutTask(self, onComplete, *args, **kwargs):
		"""Implementation of fade out task."""
		conditions = []
		for fadeQuad in self._fadeQuadList:
			fadeQuad.runAction(self._fadeOut)
			conditions.append(viztask.runAction(fadeQuad, self._fadeOut))
		yield viztask.waitAll(conditions)
		yield viztask.waitTime(.1)
		if onComplete:
			onComplete(*args, **kwargs)
	
	def _fadeInTask(self, onComplete, *args, **kwargs):
		"""Implementation of fade in task."""
		conditions = []
		for fadeQuad in self._fadeQuadList:
			fadeQuad.runAction(self._fadeIn)
			conditions.append(viztask.runAction(fadeQuad, self._fadeIn))
		yield viztask.waitAll(conditions)
		yield viztask.waitTime(.1)
		if onComplete:
			onComplete(*args, **kwargs)
		self._inTransition = False
	
	def remove(self):
		"""Removes the view transition object"""
		for fadeQuad in self._fadeQuadList:
			fadeQuad.remove()
		self._fadeIn = None
		self._fadeOut = None


if __name__ == '__main__':
	viz.go()
	viz.add('piazza.osgb')
	
	#VC: set the window for the display
	_window = viz.MainWindow
	
	#VC: set some parameters
	autoDetectMonitor = True
	timeWarpEnabled = True
	
#	#VC: create the raw object
#	import oculus
#	try:
#		display = oculus.Rift(window=_window, autoDetectMonitor=autoDetectMonitor)
#		display.setTimeWarp(timeWarpEnabled)
#		_window.displayNode = display
#		viz.window.setFullscreen(True)
#	except AttributeError:
#		_window.displayNode = None
	
	vt = Fader()
	
	def startComplete(text):
		"""Triggered when fade out is complete"""
		print 'start complete', text
	vizact.onkeydown('1', vt.start, startComplete, 'one')
	
	def stopComplete(text):
		"""Triggered when fade in is complete"""
		print 'stop complete', text
	vizact.onkeydown('2', vt.stop, stopComplete, 'two')
	
	vizact.onkeydown('3', vt.start)
	vizact.onkeydown('4', vt.stop)
	
	def inTransition():
		"""Triggered when inside transition"""
		print 'inside'
	vizact.onkeydown('5', vt.runInTransition, inTransition)
