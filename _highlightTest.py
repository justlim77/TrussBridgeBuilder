"""  
Left mouse button highlights.  
Right mouse button examines.  
Middle mouse button releases.  
Mouse movements and arrow keys  
control the viewpoint.  
""" 

import viz
import vizact
import vizshape
import vizinfo
vizinfo.InfoPanel()

viz.setOption('viz.display.stencil',1)

viz.setMultiSample(4)
viz.fov(60)
viz.go()

environment = viz.addChild('sky_day.osgb')
soccerball = viz.addChild('soccerball.osgb',pos=[-1,1.8,2])
basketball = viz.addChild('basketball.osgb',pos=[0,1.8,2])
volleyball = viz.addChild('volleyball.osgb',pos=[1,1.8,2])

#Add a model to represent the tool
arrow = vizshape.addArrow(length=0.2, color = viz.ORANGE, alpha=0.5)

#Initialize the examiner and items that can be examined
from tools import examiner
tool = examiner.Examiner(sizeOfCopy=1)
tool.setItems([soccerball,basketball,volleyball])

# update code for highlighter
def updateExaminer(tool):
    state = viz.mouse.getState()
    if state & viz. MOUSEBUTTON_LEFT:
        tool.highlight()
    if state & viz. MOUSEBUTTON_RIGHT:
        tool.examine()
    if state & viz. MOUSEBUTTON_MIDDLE:
        tool.release()
tool.setUpdateFunction(updateExaminer)

#Link the examiner tool to an arrow in order to
#visualize it's position
from vizconnect.util import virtual_trackers
mouseTracker = virtual_trackers.ScrollWheel(followMouse = True)
mouseTracker.distance = 1
arrowLink = viz.link(mouseTracker,arrow)
arrowLink.postMultLinkable(viz.MainView)
viz.link(arrowLink,tool)

import vizcam
cam = vizcam.FlyNavigate()

#Hide the mouse cursor
viz.mouse.setVisible(viz.OFF)

viz.add('carousel.wrl') 
window = viz.addWindow() 
window.ortho(-1,1,-1,1,-1,1) 