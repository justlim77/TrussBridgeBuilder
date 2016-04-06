

""" 
This script demonstrates how to use animation paths 
The 4 transparent balls represent the control points 
The rest of the animation is done by Vizard 
Use the on screen controls to change certain options 
Press spacebar to restart the path 
""" 
import viz
import vizinfo
import vizact

viz.setMultiSample(4)
viz.fov(60)
viz.go()

vizinfo.InfoPanel(align=viz.ALIGN_RIGHT_TOP)

#Add the ground plane
ground = viz.addChild('ground.osgb')

#Add the ball to animate
ball = viz.addChild('beachball.osgb')

#Move the viewpoint back
viz.MainView.move([0,0,-7])

#Create the animation path
path = viz.addAnimationPath()

#Initialize an array of control points
positions = [ [0,0,2], [2,0,0], [0,0,-2], [-2,0,0] ]

for x,pos in enumerate(positions):
    #Add a ball at each control point and make it
    #semi-transparent, so the user can see where the
    #control points are
    b = viz.addChild('beachball.osgb',cache=viz.CACHE_CLONE)
    b.setPosition(pos)
    b.alpha(0.2)
    #Add the control point to the animation path
    #at the new time
    path.addControlPoint(x+1,pos=pos)

#Set the initial loop mode to circular
path.setLoopMode(viz.CIRCULAR)

#Automatically compute tangent vectors for cubic bezier translations
path.computeTangents()

#Automatically rotate the path
path.setAutoRotate(viz.ON)

#Link the ball to the path
viz.link(path, ball)

#Play the animation path
path.play()

#Setup path control panel
controlPanel = vizinfo.InfoPanel(text=None, title='Settings', icon=False)

slider_speed = controlPanel.addLabelItem('Speed', viz.addSlider())
slider_speed.set(0.1)

controlPanel.addSection('Loop Mode')
radio_loop_off = controlPanel.addLabelItem('Off', viz.addRadioButton('LoopMode'))
radio_loop_on = controlPanel.addLabelItem('Loop', viz.addRadioButton('LoopMode'))
radio_loop_swing = controlPanel.addLabelItem('Swing', viz.addRadioButton('LoopMode'))
radio_loop_circular = controlPanel.addLabelItem('Circular', viz.addRadioButton('LoopMode'))
radio_loop_circular.set(1)

controlPanel.addSection('Interpolation Mode')
radio_interp_linear = controlPanel.addLabelItem('Linear', viz.addRadioButton('InterpolationMode'))
radio_interp_cubic = controlPanel.addLabelItem('Bezier', viz.addRadioButton('InterpolationMode'))
radio_interp_linear.set(1)

def changeSpeed(pos):
    #Adjust the speed of the animation path
    path.setSpeed(pos*10)

#Setup callbacks for slider events
vizact.onslider(slider_speed, changeSpeed)

#Setup button click events
vizact.onbuttondown(radio_loop_off,path.setLoopMode,viz.OFF)
vizact.onbuttondown(radio_loop_on,path.setLoopMode,viz.LOOP)
vizact.onbuttondown(radio_loop_swing,path.setLoopMode,viz.SWING)
vizact.onbuttondown(radio_loop_circular,path.setLoopMode,viz.CIRCULAR)
vizact.onbuttondown(radio_interp_linear,path.setTranslateMode,viz.LINEAR_INTERP)
vizact.onbuttondown(radio_interp_cubic,path.setTranslateMode,viz.CUBIC_BEZIER)

# Reset path
vizact.onkeydown(' ', path.reset)