#Class allows typical FPS navigation controls
#W,A,S,D and mouselook

import viz
import vizcam

#Define user movement class
class AvatarMove:
	#initialization function
	def __init__(self):
		self.move = False
		self.view = viz.MainView
		self.viewIndex = 0
		self.window = viz.MainWindow
		self.camera = viz.cam.setHandler(vizcam.KeyboardCamera(forward=None,backward=None,left=None,right=None,turnRight=None,turnLeft=None,up=None,down=None,pitchDown=None,pitchUp=None,rollRight=None,rollLeft=None,moveScale=2))
		viz.callback(viz.MOUSE_MOVE_EVENT,self.mousemove)
	#enable navigation
	def enable(self):
		viz.mouse.setTrap(viz.ON)
		self.move = True
		self.camera = viz.cam.setHandler(vizcam.KeyboardCamera(forward='w',backward='s',left='a',right='d',turnLeft=None,turnRight=None,up=' ',down=viz.KEY_SHIFT_L,pitchDown=None,pitchUp=None,rollRight=None,rollLeft=None))
	#disable navigation
	def disable(self):
		viz.mouse.setTrap(viz.OFF)
		self.move = False
		self.camera = viz.cam.setHandler(vizcam.KeyboardCamera(forward=None,backward=None,left=None,right=None,turnRight=None,turnLeft=None,up=None,down=None,pitchDown=None,pitchUp=None,rollRight=None,rollLeft=None))
	#set free mode
	def setBuildMode(self,position,rotation,moveSpeed=1.0,turnSpeed=1.0):		
		self.viewIndex = 0
		self.setPosition(position[0],position[1],position[2])
		self.setRotation(rotation[0],rotation[1],rotation[2])
		self.disable()
		viz.mouse.setTrap(viz.ON)		
		self.camera = viz.cam.setHandler(vizcam.WalkNavigate(forward='w',backward='s',left='a',right='d',moveScale=moveSpeed,turnScale=turnSpeed))
	#set free mode
	def setFreeMode(self,position,rotation):		
		self.viewIndex = 1
		self.setPosition(position[0],position[1],position[2])
		self.setRotation(rotation[0],rotation[1],rotation[2])	
		self.enable()
	#set front ortho mode
	def setFrontOrtho(self,left,right,bottom,top,near,far):
		self.viewIndex = 2
		self.disable()
#		self.window.ortho(left,right,bottom,top,near,far)
		self.setPosition(0,5,-17)
		self.setRotation(0,0,0)
	#set top ortho mode
	def setTopOrtho(self,left,right,bottom,top,near,far):
		self.viewIndex = 3
		self.disable()
#		self.window.ortho(left,right,bottom,top,near,far)	
		self.setPosition(0,20,0)
		self.setRotation(0,90,0)
	#tracks mouse movements
	def mousemove(self,e):
		if self.move == True:			
			euler = self.view.get(viz.HEAD_EULER)
			euler[0] += e.dx*0.1
			euler[1] += -e.dy*0.1
			euler[1] = viz.clamp(euler[1],-60.0,60.0)
			euler[2] = 0
			self.view.setEuler(euler,viz.HEAD_ORI) 
	#allows you to set the position of the user
	def setPosition(self,x,y,z):
		self.view.setPosition(x,y,z)
	#allows you to get the position of the user
	def getPosition(self):
		return self.view.getPosition()
	#allows you to set the rotation of the user
	def setRotation(self,y,p,r):
		self.view.setEuler(y,p,r)
	#allows you to get the rotation of the user
	def getRotation(self):
		return self.view.getEuler()
	#allows you to get the view index of the user
	def getViewIndex(self):
		return self.viewIndex
	#allows you to set move bool
	def setMove(self,value):
		self.move = value;