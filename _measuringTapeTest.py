"""  
Left mouse button calls the cycle  
command.'1','2','3' keys call the  
start, end, and clear commands.  
Mouse movements and arrow keys  
control the viewpoint.  
""" 

import viz
import vizact
import vizshape
import vizcam
import vizinfo
vizinfo.InfoPanel()

viz.setMultiSample(4)
viz.fov(60)
viz.go()

gallery = viz.add('gallery.osgb')
arrow = vizshape.addArrow(length=0.2, color = viz.ORANGE)

# initialization code for measuringtape which is a MeasuringTape
from tools import measuring_tape
tool = measuring_tape.MeasuringTape()

vizact.onmousedown(viz.MOUSEBUTTON_LEFT,tool.cycle)
vizact.onkeydown('1',tool.setStartWall)
vizact.onkeydown('2',tool.setEndWall)
vizact.onkeydown('3',tool.clear)

#visualize it's position
#Link the examiner tool to an arrow in order to
from vizconnect.util import virtual_trackers
mouseTracker = virtual_trackers.ScrollWheel(followMouse = True)
mouseTracker.distance = 1
arrowLink = viz.link(mouseTracker,arrow)
arrowLink.postMultLinkable(viz.MainView)
viz.link(arrowLink,tool)

import vizcam
cam = vizcam.FlyNavigate()

#Hide the mouse curser
viz.mouse.setVisible(viz.OFF)