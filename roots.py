import viz
import vizfx
import vizshape

def GridRoot(gridColor=viz.CYAN,origin=([0,0,0])):
	grid_root = viz.addGroup()
	
	# Create front grid
	grid_front = vizshape.addGrid(size=(20,10))
	grid_front.color(gridColor)
	grid_front.setPosition(0,5,-5)
	grid_front.setEuler(0,90,0)
	grid_front.setParent(grid_root)
	
	# Create back grid
	grid_back = vizshape.addGrid(size=(20,10))
	grid_back.color(gridColor)
	grid_back.setPosition(0,5,-5-24)
	grid_back.setEuler(0,90,0)
	grid_back.setScale(1,z=-1)
	grid_back.setParent(grid_root)

	# Create bottom grid
	grid_bottom = vizshape.addGrid(size=(20,24))
	grid_bottom.color(gridColor)
	grid_bottom.setPosition(0,0,origin[2])
	grid_bottom.setParent(grid_root)
	
	# Create left grid
	grid_left = vizshape.addGrid(size=(10,24))
	grid_left.color(gridColor)
	grid_left.setPosition(-10,5,origin[2])
	grid_left.setEuler(0,0,90)
	grid_left.setParent(grid_root)
	
	# Create right grid
	grid_right = vizshape.addGrid(size=(10,24))
	grid_right.color(gridColor)
	grid_right.setPosition(10,5,origin[2])
	grid_right.setEuler(0,0,-90)
	grid_right.setParent(grid_root)
	
	# Create floating measurements
	span_text = viz.addText3D('<< 20 meters >>',pos=[-3.25,10.25,-5],parent=grid_root)
	height_text = viz.addText3D('<< 10 meters >>',pos=[-10.25,1,-5],euler=[0,0,90],parent=grid_root)
	
	print 'Creating grid...'
	return grid_root
	
def EnvironmentRoot(visibility=True):
	environment_root = viz.addGroup()
	day = viz.add('resources/sky_day.osgb', scale=([5,5,5]),parent=environment_root)
	environment = vizfx.addChild('resources/environment.osgb',parent=environment_root)
	walkway = vizfx.addChild('resources/walkway.osgb',parent=environment_root)
	river = vizfx.addChild('resources/river.osgb', pos=(0,0.75,20),scale=([10,1,10]),parent=environment_root)
	river.setAnimationSpeed(0.005)
	environment_root.visible(visibility)
	
	print 'Creating environment...'
	return environment_root
	
def BridgeRoot(pos=([0,0,0]),euler=([0,0,0])):
	bridge_root = viz.addGroup()
	axes = vizshape.addAxes(parent=bridge_root)
	X = viz.addText3D('X',pos=[1.1,0,0],color=viz.RED,scale=[0.3,0.3,0.3],parent=axes)
	Y = viz.addText3D('Y',pos=[0,1.1,0],color=viz.GREEN,scale=[0.3,0.3,0.3],align=viz.ALIGN_CENTER_BASE,parent=axes)
	Z = viz.addText3D('Z',pos=[0,0,1.1],color=viz.BLUE,scale=[0.3,0.3,0.3],align=viz.ALIGN_CENTER_BASE,parent=axes)
	bridge_root.setPosition(pos)
	bridge_root.setEuler(euler)
	
	print 'Creating bridge root...'
	return bridge_root