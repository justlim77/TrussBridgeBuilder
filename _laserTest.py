"""  
Left mouse button activates the laser.  
Mouse movements control viewpoint orientation.  
Arrow Keys control viewpoint position.  
""" 

import viz
import vizact
import vizshape
import vizinfo
vizinfo.InfoPanel(align=viz.ALIGN_LEFT_BOTTOM)

viz.setMultiSample(4)
viz.fov(60)
viz.go()

# add a background environment
maze = viz.add('maze.osgb')

# add an arrow to represent the tool
arrow = vizshape.addArrow(length=0.2, color = viz.ORANGE)

# initialization code for laserpointer which is a LaserPointer
from tools import laser_pointer
tool = laser_pointer.LaserPointer()

# update code for grabber
def update(tool):
 state = viz.mouse.getState()
 if state & viz. MOUSEBUTTON_LEFT:
  tool.shoot()
  
tool.setUpdateFunction(update)

#Link the laser tool to an arrow  
#Then move the arrow in the reference frame of the viewpoint
from vizconnect.util import virtual_trackers
mouseTracker = virtual_trackers.ScrollWheel(followMouse = True)
mouseTracker.distance = 1
arrowLink = viz.link(mouseTracker,arrow)
arrowLink.postMultLinkable(viz.MainView)
viz.link(arrowLink,tool)

import vizcam
vizcam.FlyNavigate()

#Hide the mouse cursor
viz.mouse.setVisible(viz.OFF)