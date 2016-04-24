import viz
import vizact
import vizmat
import vizdlg
import vizshape
import navigation
import vizconnect.util
import tools

# Highlighter	
def initHighlighter():
	"""Initiailze highlighter tool"""
	from tools import highlighter
	return highlighter.Highlighter()
	
	
from vizconnect.util import virtual_trackers
class ScrollWheel2(virtual_trackers.ScrollWheel):
	def __init__(self,**kwargs):
		super(ScrollWheel2, self).__init__(**kwargs)
		
	def onUpdate(self):
		
		"""Callback that updates the tracker"""
#		if self._enabled:
#			# get the line along the mouse position
#			dt = 0.03#viz.getFrameElapsed()
#			self._vel += self._accel*dt
#			if self.scaleVelocityWithDistance:
#				self._vel *= max(1.0, self.distance)
#			self.distance += self._vel*dt
#			if self.followMouse:
#				line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
#				mat = vizmat.Transform()
#				mat.makeEuler(viz.MainView.getEuler(viz.ABS_GLOBAL))
#				mat = mat.inverse()
#				dir = mat.preMultVec(line.dir)
#				dir = vizmat.Vector(dir)
#				dir.normalize()
#				vector = dir*self.distance
#			else:
#				vector = [0, 0, self.distance]
#			self._vel = 0
#			self._accel = 0
#			self.setPosition(vector)
		if self._enabled:
			# get the line along the mouse position
			dt = 0.03#viz.getFrameElapsed()
			self._vel += self._accel*dt
			if self.scaleVelocityWithDistance:
				self._vel *= max(1.0, self.distance)
			self.distance += self._vel*dt
			if self.followMouse:
				line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
				mat = vizmat.Transform()
#				mat.makeLookAt(line.begin, line.dir, [0, 1, 0])
				mat.makeEuler(viz.MainView.getEuler(viz.ABS_GLOBAL))
				mat = mat.inverse()
				dir = mat.preMultVec(line.dir)
				dir = vizmat.Vector(dir)
				dir.normalize()
				vector = dir*self.distance
			else:
				vector = [0, 0, self.distance]
			self._vel = 0
			self._accel = 0
			self.setPosition(vector)
#			self.lookAt(vector)
			
def initTracker(distance=1):
	"""Initialize scroll wheel tracker"""
#	from vizconnect.util import virtual_trackers
#	tracker = virtual_trackers.ScrollWheel(followMouse=True)
	tracker = ScrollWheel2(followMouse=True)
	tracker.distance = distance
	return tracker

def updateHighlightTool(highlightTool):
	highlightTool.highlight()


def updateHand(hand):
#	line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
#	mat = vizmat.Transform()
#	pos = link.getPosition()
##	mat.makeLookAt([0, 0, 0], line.dir, [0, 1, 0])
#	mat.makeLookAt(pos, line.dir, [0, 1, 0])
#	if hasattr(hand,'setMatrix'):
#		hand.setMatrix(mat)
	distance = 5
	line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
	mat = vizmat.Transform()
	mat.makeEuler(viz.MainView.getEuler(viz.ABS_GLOBAL))
	mat = mat.inverse()
	dir = mat.preMultVec(line.dir)
	dir = vizmat.Vector(dir)
	dir.normalize()
	vector = dir*distance
	hand.lookAt(vector)
	
def updateArrow(link,arrow):
	line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
	mat = vizmat.Transform()
	pos = link.getPosition()
#	mat.makeLookAt([0, 0, 0], line.dir, [0, 1, 0])
	pos[2] += 1
	mat.makeLookAt(pos, line.dir, [0, 1, 0])
	if hasattr(arrow,'setMatrix'):
		arrow.setMatrix(mat)	
#	arrow.lookAt(line.end)
	
def toggleMenu(node=viz.addGroup(),view=viz.MainView,menu=viz.addGUICanvas(),val=viz.TOGGLE):
	menu.visible(val)
	menuLink = None
	if menu.getVisible() is True:
		pos = view.getPosition()
		menu.setPosition(pos[0],pos[1]-1,pos[2]+5)
#		menuLink.remove()
	else:
		menuLink = viz.grab(node,menu)
			
from tools import ray_caster
def updateMousePosition(canvas=viz.addGUICanvas(),raycaster=ray_caster.RayCaster(autoHide=False)):
	line = raycaster.getLineForward()
	newPos = line.endFromDistance(2)
	screenPos = viz.MainWindow.worldToScreen(newPos)
	canvas.setCursorPosition(screenPos)
#	print canvas.getCursorPosition()
#	print screenPos
	
if __name__ == '__main__':
	viz.setMultiSample(8)
	viz.go()
	
	viz.mouse.setTrap()
	viz.mouse.setOverride()
	
	navigator = navigation.getNavigator()
	try:
		resolution = navigator.getHMD().getSensor().getResolution()
	except:
		resolution = [1600,900]

	highlighter = initHighlighter()
	highlighter.setUpdateFunction(updateHighlightTool)
	tracker = initTracker()
	glove = viz.addChild('glove.cfg')
	glove.alpha(0.2)
	arrow=vizshape.addArrow()
	trackerLink = viz.link(tracker,glove)
	viz.link(trackerLink,highlighter)
#	trackerLink.postMultLinkable(navigator.VIEW)
	trackerLink.postMultLinkable(navigator.VIEW)
#	trackerLink.preTrans([.1,-.1,.5])
#	trackerLink.preEuler([0,0,0])
#	trackerLink.postTrans([.5,-.2,0])
	
#	trackerLink.setPosition([0,5,1])
#	vizact.ontimer(0,updateClampedPos)
#	vizact.ontimer(0,updateHand,tracker)
#	arrowLink = viz.link(tracker,highlighter)
#	arrowLink.postMultLinkable(navigator.VIEW)
#	arrowLink = viz.link(tracker,arrow)
#	arrowLink = viz.link(arrow,highlighter)
#	arrowLink.preMultLinkable(viz.MainView)
#	arrowLink.preMultLinkable(navigator.VIEW)
#	arrowLink.postMultLinkable(navigator.VIEW)
#	vizact.ontimer(0,updateHand,arrow)
#	vizact.ontimer(0,updateArrow,trackerLink,arrow)
	
	canvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
	viz.MainWindow.setDefaultGUICanvas(canvas)
	canvas.setRenderWorld([600,400],[2,viz.AUTO_COMPUTE])
	canvas.setMouseStyle(viz.CANVAS_MOUSE_BUTTON | viz.CANVAS_MOUSE_VISIBLE)
	panel = vizdlg.TabPanel(parent=canvas,align=viz.ALIGN_CENTER)
	panel_A = vizdlg.Panel()
	panel_B = vizdlg.Panel()
	tab_A = panel.addPanel('Tab A',panel_A)
	tab_B = panel.addPanel('Tab B',panel_B)
	canvas.setPosition(0,2,3)
	
	vizact.ontimer(0,updateMousePosition,canvas,highlighter.getRayCaster())
	vizact.onkeyup(' ',toggleMenu,node=navigator.NODE,menu=canvas)
	
	viz.addChild('maze.osgb')