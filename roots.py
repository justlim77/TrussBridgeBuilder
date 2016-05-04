import viz
import vizfx
import vizshape

class Root(object):
	def __init__(self, *args):	
		self._root = viz.addGroup()
	def visible(self, state = viz.ON, node='', op=viz.OP_DEFAULT):
		self._root.visible(state, node, op)
	def getVisible(self, node='', op=viz.OP_DEFAULT):
		return self._root.getVisible(node, op)
	def getGroup(self):
		return self._root
		
class GridRoot(Root):
	def __init__(self,color=viz.CYAN,textColor=viz.WHITE,shadowColor=viz.BLACK):
		super(self.__class__, self).__init__()
		
		# Create front grid
		self._grid_front = vizshape.addGrid(size=(20,10))
		self._grid_front.color(color)
		self._grid_front.setPosition(0,5,-5)
		self._grid_front.setEuler(0,90,0)
		self._grid_front.setParent(self._root)

		# Create back grid
		self._grid_back = vizshape.addGrid(size=(20,10))
		self._grid_back.color(color)
		self._grid_back.setPosition(0,5,-5-24)
		self._grid_back.setEuler(0,90,0)
		self._grid_back.setParent(self._root)

		# Create bottom grid
		self._grid_bottom = vizshape.addGrid(size=(20,24))
		self._grid_bottom.color(color)
		self._grid_bottom.setPosition(0,0,-17)
		self._grid_bottom.setParent(self._root)
		
		# Create left grid
		self._grid_left = vizshape.addGrid(size=(10,24))
		self._grid_left.color(color)
		self._grid_left.setPosition(-10,5,-17)
		self._grid_left.setEuler(0,0,90)
		self._grid_left.setParent(self._root)
		
		# Create right grid
		self._grid_right = vizshape.addGrid(size=(10,24))
		self._grid_right.color(color)
		self._grid_right.setPosition(10,5,-17)
		self._grid_right.setEuler(0,0,-90)
		self._grid_right.setParent(self._root)
		
		# Create floating measurements
		self._span_text = viz.addText3D('<< 20 meters >>',pos=[0,11,-5],scale=[1,1,1],parent=self._root,align=viz.ALIGN_CENTER)
		self._span_text_shadow = viz.addText3D('<< 20 meters >>',parent=self._span_text,align=viz.ALIGN_CENTER)
		self._span_text_shadow.setPosition([0,0,0.2])
		self._span_text_shadow.color(shadowColor)
		self._span_text_shadow.alpha(0.75)	
		
		self._height_text = viz.addText3D('<< 10 meters >>',pos=[-11,5,-5],scale=[1,1,1],euler=[0,0,90],parent=self._root,align=viz.ALIGN_CENTER)
		self._height_text_shadow = viz.addText3D('<< 10 meters >>',parent=self._height_text,align=viz.ALIGN_CENTER)
		self._height_text_shadow.setPosition([0,0,0.2])
		self._height_text_shadow.color(shadowColor)
		self._height_text_shadow.alpha(0.75)	
		
		#--Create orientation info text
		self._orientation_text = viz.addText3D('<< View >>',pos=[0,13.5,-5],scale=(2,2,.5),parent=self._root,align=viz.ALIGN_CENTER)
		self._orientation_text.color(textColor)
		self._orientation_text_shadow = viz.addText3D('<< View >>',parent=self._orientation_text,align=viz.ALIGN_CENTER)
		self._orientation_text_shadow.setPosition([0,0,0.2])
		self._orientation_text_shadow.color(shadowColor)
		self._orientation_text_shadow.alpha(0.75)
		
		self._info_text = viz.addText3D('<< Info >>',pos=[0,12,-5],scale=(.5,.5,.5),parent=self._root,align=viz.ALIGN_CENTER)
		self._info_text.color(textColor)
		self._info_text_shadow = viz.addText3D('<< Info >>',parent=self._info_text,align=viz.ALIGN_CENTER)
		self._info_text_shadow.setPosition([0,0,0.2])
		self._info_text_shadow.color(shadowColor)
		self._info_text_shadow.alpha(0.75)
		
	def setOrientationMessage(self, value):
		self._orientation_text.message(value)
		self._orientation_text_shadow.message(value)
		
	def setInfoMessage(self, value):
		self._info_text.message(value)
		self._info_text_shadow.message(value)
		
class EnvironmentRoot(Root):
	def __init__(self):
		super(self.__class__, self).__init__()
		
		self._day = viz.add('resources/sky_day.osgb', scale=([1,1,1]),parent=self._root)
		self._day.renderToBackground(order=8)
		self._environment = viz.add('resources/environment.osgb',parent=self._root)
		self._environment.renderToBackground()
		self._waveGroup = viz.addGroup(parent=self._root)
		self._wave_M = viz.addChild('resources/wave.osgb',cache=viz.CACHE_CLONE,pos=([0,2,0]),parent=self._waveGroup)
		self._wave_B = viz.addChild('resources/wave.osgb',cache=viz.CACHE_CLONE,pos=([0,2,-50]),parent=self._waveGroup)
		self._newWalkway = viz.add('resources/newWalkway.osgb',parent=self._root)	
		
	def getWaveGroup(self):
		return self._waveGroup
		
	def setWaveAnimationSpeed(self, speed, node=''):
		self._waveGroup.setAnimationSpeed(speed, node)
		
	
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
