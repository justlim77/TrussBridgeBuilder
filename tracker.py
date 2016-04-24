import viz
import vizact
import vizmat
import vizdlg
import navigation

# Highlighter	
def initHighlighter():
	"""Initiailze highlighter tool"""
	from tools import highlighter
	return highlighter.Highlighter()
	
def initTracker(distance=1):
	"""Initialize scroll wheel tracker"""
	from vizconnect.util import virtual_trackers
	tracker = virtual_trackers.ScrollWheel(followMouse=True)
	tracker.distance = distance
	return tracker

def updateHighlightTool(highlightTool):
	highlightTool.highlight()

def updateHand(view,hand):
	line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
	mat = vizmat.Transform()
#	mat.makeLookAt([0, 0, 0], line.dir, [0, 1, 0])
#	if hasattr(hand,'setMatrix'):
#		hand.setMatrix(mat)
	pos = view.getPosition()
	mat.makeLookAt(pos, line.dir, [0,1,0])
	hand.setMatrix(mat)
#	hand.lookAt(line.end)
	
def toggleMenu(node=viz.addGroup(),view=viz.MainView,menu=viz.addGUICanvas(),val=viz.TOGGLE):
	menu.visible(val)
	menuLink = None
	if menu.getVisible() is True:
		pos = view.getPosition()
		menu.setPosition(pos[0],pos[1]-1,pos[2]+5)
#		menuLink.remove()
	else:
		menuLink = viz.grab(node,menu)
		
	
if __name__ == '__main__':
	viz.setMultiSample(8)
	viz.go()
	
	navigator = navigation.getNavigator()
#	resolution = navigator.getHMD().getSensor().getResolution()
	resolution = [1600,900]
	viz.mouse.setTrap()
	
	highlighter = initHighlighter()
	tracker = initTracker()
	glove = viz.addChild('glove.cfg')
	trackerLink = viz.link(tracker,glove)
	trackerLink.preMultLinkable(navigator.VIEW)
	viz.link(trackerLink,highlighter)
	trackerLink.setPosition([0,5,1])
	highlighter.setUpdateFunction(updateHighlightTool)
#	vizact.ontimer(0,updateClampedPos)
	vizact.ontimer(0,updateHand,navigator.VIEW,trackerLink)

	
	canvas = viz.addGUICanvas()
	canvas.setRenderWorld(resolution,[10,viz.AUTO_COMPUTE])
	panel = vizdlg.TabPanel(parent=canvas,align=viz.ALIGN_CENTER)
	panel_A = vizdlg.Panel()
	panel_B = vizdlg.Panel()
	tab_A = panel.addPanel('Tab A',panel_A)
	tab_B = panel.addPanel('Tab B',panel_B)
	canvas.setPosition(0,2,3)
	
	vizact.onkeyup(' ',toggleMenu,node=navigator.NODE,menu=canvas)
	
	piazza = viz.addChild('piazza.osgb')