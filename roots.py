import viz
import vizfx
import vizshape

def GridRoot(gridColor=viz.CYAN):
	grid_root = viz.addGroup()
	
	# Create front grid
	grid_front = vizshape.addGrid(size=(20,10))
	grid_front.color(gridColor)
	grid_front.setPosition(0,5,-5)
	grid_front.setEuler(0,90,0)
	grid_front.setParent(grid_root)

#	grid_front_intersect = vizshape.addPlane(size=(20,10),cullFace=False)
#	grid_front_intersect.setPosition(grid_front.getPosition())
#	grid_front_intersect.setEuler(grid_front.getEuler())
#	grid_front_intersect.setParent(grid_root)
#	grid_front_intersect.snap = True

	# Create back grid
	grid_back = vizshape.addGrid(size=(20,10))
	grid_back.color(gridColor)
	grid_back.setPosition(0,5,-5-24)
	grid_back.setEuler(0,90,0)
	grid_back.setParent(grid_root)

	# Create bottom grid
	grid_bottom = vizshape.addGrid(size=(20,24))
	grid_bottom.color(gridColor)
	grid_bottom.setPosition(0,0,-17)
	grid_bottom.setParent(grid_root)
	
	# Create left grid
	grid_left = vizshape.addGrid(size=(10,24))
	grid_left.color(gridColor)
	grid_left.setPosition(-10,5,-17)
	grid_left.setEuler(0,0,90)
	grid_left.setParent(grid_root)
	
	# Create right grid
	grid_right = vizshape.addGrid(size=(10,24))
	grid_right.color(gridColor)
	grid_right.setPosition(10,5,-17)
	grid_right.setEuler(0,0,-90)
	grid_right.setParent(grid_root)
	
	# Create floating measurements
	span_text = viz.addText3D('<< 20 meters >>',pos=[0,11,-5],scale=[1,1,1],parent=grid_root,align=viz.ALIGN_CENTER)
	span_text_shadow = viz.addText3D('<< 20 meters >>',parent=span_text,align=viz.ALIGN_CENTER)
	span_text_shadow.setPosition([0,0,0.2])
	span_text_shadow.color(viz.BLACK)
	span_text_shadow.alpha(0.75)	
	
	height_text = viz.addText3D('<< 10 meters >>',pos=[-11,5,-5],scale=[1,1,1],euler=[0,0,90],parent=grid_root,align=viz.ALIGN_CENTER)
	height_text_shadow = viz.addText3D('<< 10 meters >>',parent=height_text,align=viz.ALIGN_CENTER)
	height_text_shadow.setPosition([0,0,0.2])
	height_text_shadow.color(viz.BLACK)
	height_text_shadow.alpha(0.75)
	
	return grid_root
	
	
def EnvironmentRoot(visibility=True):
	environment_root = viz.addGroup()
	day = viz.add('resources/sky_day.osgb', scale=([5,5,5]),parent=environment_root)
	day.renderToBackground(order=8)
	environment = viz.add('resources/environment.osgb',parent=environment_root)
	environment.renderToBackground()
	try:
		newWalkway = viz.add('resources/newWalkway.osgb',parent=environment_root)
	except:
		viz.logError('**Error: New walkway not found - loading old walkway!')
		L_offset = 26
		R_offset = -13
	#	walkway = viz.addChild('resources/walkwayTest.osgb',parent=environment_root)
		walkway_L = viz.add('resources/walkway_L.osgb',pos=([-60.72457+L_offset,-1.75,31.85828+3.25]),parent=environment_root)
		walkway_R = viz.add('resources/walkway_R.osgb',pos=([64.14527+R_offset,-1,0-11]),parent=environment_root)	
	environment_root.visible(visibility)
	return environment_root
	
	
def BridgeRoot(pos=([0,0,0]),euler=([0,0,0])):
	bridge_root = viz.addGroup()
#	axes = vizshape.addAxes(parent=bridge_root)
#	X = viz.addText3D('X',pos=[1.1,0,0],color=viz.RED,scale=[0.3,0.3,0.3],parent=axes)
#	Y = viz.addText3D('Y',pos=[0,1.1,0],color=viz.GREEN,scale=[0.3,0.3,0.3],align=viz.ALIGN_CENTER_BASE,parent=axes)
#	Z = viz.addText3D('Z',pos=[0,0,1.1],color=viz.BLUE,scale=[0.3,0.3,0.3],align=viz.ALIGN_CENTER_BASE,parent=axes)
	bridge_root.setPosition(pos)
	bridge_root.setEuler(euler)
	return bridge_root
	
if __name__ == '__main__':
	viz.setMultiSample(8)
	
	viz.go()
	
	for window in viz.getWindowList():
		window.getView().getHeadLight().disable()
#		
#	# Create directional light
	sky_light = viz.addDirectionalLight(euler=(-66,37,0),color=[1,1,1])
##	light1 = vizfx.addDirectionalLight(euler=(40,20,0), color=[0.7,0.7,0.7])
##	light2 = vizfx.addDirectionalLight(euler=(-65,15,0), color=[0.5,0.25,0.0])
##	sky_light.color(viz.WHITE)
#	# Adjust ambient color
#	viz.setOption('viz.lightModel.ambient',[0]*3)
#	sky_light.ambient([0.8]*3)
#	vizfx.setAmbientColor([0.3,0.3,0.4])	
	import oculus
	hmd = oculus.Rift()
	if not hmd.getSensor(): 
		viz.logError('**ERROR: Failed to detect Oculus!')
	
	ORIGIN = [0,5,-17]
	
	gridRoot = GridRoot()
	viz.MainView.setPosition(ORIGIN)
	
#	bridgeRoot = BridgeRoot()
#	environment_root = EnvironmentRoot()
#	wave_M = viz.addChild('resources/wave.osgb',cache=viz.CACHE_CLONE,pos=([0,0.75,0]),parent=environment_root)
#	wave_M.setAnimationSpeed(0.02)
#	wave_B = viz.addChild('resources/wave.osgb',cache=viz.CACHE_CLONE,pos=([0,0.75,-50]),parent=environment_root)
#	wave_B.setAnimationSpeed(0.02)
#	road_L1 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(-20,5,0),parent=environment_root)
#	road_L2 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(-40,5,0),parent=environment_root)
#	road_R1 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(20,5,0),parent=environment_root)
#	road_R2 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(40,5,0),parent=environment_root)
#	road_M = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(0,5,0),parent=environment_root)
