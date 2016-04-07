""" 
This script demonstrates how to add multiple windows. 
The upper right window is a rear view of the scene 
The upper left window is a birds eye view 
""" 

import viz
import vizact

viz.setMultiSample(4)
viz.fov(60)
viz.go()

import vizinfo
vizinfo.InfoPanel(align=viz.ALIGN_RIGHT_BOTTOM)

#Add environment
viz.addChild('maze.osgb')

# Create a new window in the upper left corner
UpperLeftWindow = viz.addWindow(pos=(0,1.0),size=(0.2,0.2))
UpperLeftWindow.visible(0,viz.SCREEN)

#Create a new window in the upper right corner
UpperRightWindow = viz.addWindow(pos=(0.8,1.0),size=(0.2,0.2))
UpperRightWindow.visible(0,viz.SCREEN)

# Create a new viewpoint
BirdView = viz.addView()

#Attach the bird's eye view to the upper left window
UpperLeftWindow.setView(BirdView)

#Move the view above the center of the room
BirdView.setPosition([0,25,0])

#Rotate the view so that it looks down
BirdView.setEuler([0,90,0])

#Create another viewpoint
RearView = viz.addView()

#Attach the rear view to the upper right window
UpperRightWindow.setView(RearView)

#Increase the field-of-view for both windows
UpperLeftWindow.fov(60)
UpperRightWindow.fov(60)

#Add an arrow marker to bird's eye view window to represent our current position/orientation
arrow = viz.addTexQuad(parent=viz.ORTHO,scene=UpperLeftWindow,size=20)
arrow.texture(viz.add('arrow.tif'))

def UpdateViews():

    #Get the current head orientation and position
    yaw,pitch,roll = viz.MainView.getEuler()
    pos = viz.MainView.getPosition()

    #Move the rear view to the current position
    RearView.setPosition(pos)

    #Rotate the rear view so that it faces behind us
    RearView.setEuler([yaw+180,0,0])

    #Move arrow to our current location
    x,y,z = UpperLeftWindow.worldToScreen(pos,mode=viz.WINDOW_PIXELS)
    arrow.setPosition([x,y,0])
    arrow.setEuler([0,0,-yaw])

vizact.ontimer(0,UpdateViews)

# Turn on collision detection so we can't go through walls
viz.collision(viz.ON)
