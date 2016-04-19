﻿"""
This script demonstrates how to connect to 
a joystick device and handle state changes. 
The axes control the view position/rotation 
and the trigger button resets the view. 
""" 
import sys
import viz
import vizact
import vizconfig
import oculus

import vizinfo
#vizinfo.InfoPanel()

# Navigator Base Class
class Navigator(object):
	def __init__(self):
		object.__init__(self)
		
		#Save parameters
		# --Key commands
		self.KEYS = { 'forward'	: 'w'
					,'back' 	: 's'
					,'left' 	: 'a'
					,'right'	: 'd'
					,'down'		: 'z'
					,'up'		: 'x'
					,'reset'	: 'r'
					,'camera'	: 'c'
					,'restart'	: viz.KEY_END
					,'home'		: viz.KEY_HOME
					,'builder'	: 'b'
					,'viewer'	: 'v'
					,'env'		: 't'
					,'grid'		: 'g'
					,'hand'		: 'h'
					,'showMenu' : ' '
					,'snapMenu'	: viz.KEY_CONTROL_L
					,'interact' : viz.MOUSEBUTTON_LEFT
					,'utility'	: viz.MOUSEBUTTON_MIDDLE
					,'rotate'	: viz.MOUSEBUTTON_RIGHT
					,'cycle'	: viz.KEY_TAB
					,'mode'		: viz.KEY_SHIFT_L
					,'proxi'	: 'p'
					,'collide'	: 'c'
					,'walk'		: '/'
					,'esc'		: viz.KEY_ESCAPE
					,'viewMode' : 'm'
					,'capslock'	: viz.KEY_CAPS_LOCK
		}
		self.MOVE_SPEED = 1.4
		self.TURN_SPEED = 90
		self.ORIGIN_POS = [0,0,0]
		self.ORIGIN_ROT = [0,0,0]
		self.EYE_HEIGHT = 1.8
		self.FOV = 100
		
		self.NODE = viz.addGroup()
		self.VIEW = viz.MainView

		#Override view link on inheriting classes
		self.VIEW_LINK = viz.link(self.VIEW, self.NODE)	
		
	# Setup functions		
	def getPosition(self):
#		return self.navigationNode.getPosition(viz.REL_PARENT)
		return self.NODE.getPosition()
		
	def setPosition(self,position):
#		self.navigationNode.setPosition(position, viz.REL_PARENT)
		self.NODE.setPosition(position)
					
	def getEuler(self):
		return self.NODE.getEuler()
		
	def setEuler(self,euler):
#		self.navigationNode.setEuler(euler, viz.REL_PARENT)
		self.NODE.setEuler(euler)	
	
	def getView(self):
		return self.VIEW
		
	def getNode(self):
		return self.NODE
	
	def getLink(self):		
		return self.VIEW_LINK
		
	def getKeys(self):
		return self.KEYS
	
	def getEyeHeight(self):
		return self.EYE_HEIGHT
	
	def setEyeHeight(self,height):
		self.EYE_HEIGHT = height

	def getMoveSpeed(self):
		return self.MOVE_SPEED
	
	def setMoveSpeed(self,speed):
		self.MOVE_SPEED = speed
		
	def getTurnSpeed(self):
		return self.TURN_SPEED
	
	def setTurnSpeed(self,speed):
		self.TURN_SPEED = speed
		
	def setOrigin(self,pos,euler):
		self.ORIGIN_POS = pos
		self.ORIGIN_ROT = euler	
	
	def updateView(self):
		yaw,pitch,roll = self.VIEW.getEuler()
		m = viz.Matrix.euler(yaw,0,0)
		dm = viz.getFrameElapsed() * self.MOVE_SPEED
		if viz.key.isDown(self.KEYS['forward']):
			m.preTrans([0,0,dm])
		if viz.key.isDown(self.KEYS['back']):
			m.preTrans([0,0,-dm])
		if viz.key.isDown(self.KEYS['left']):
			m.preTrans([-dm,0,0])
		if viz.key.isDown(self.KEYS['right']):
			m.preTrans([dm,0,0])
		if viz.key.isDown(self.KEYS['up']):
			m.preTrans([0,dm,0])
		if viz.key.isDown(self.KEYS['down']):
			m.preTrans([0,-dm,0])
		self.VIEW.setPosition(m.getPosition(), viz.REL_PARENT)
#		viz.logNotice('Node position:', self.getPosition())
		
	def reset(self):
		print 'Navigator: Reset'
		self.NODE.setPosition(self.ORIGIN_POS)
		self.NODE.setEuler(self.ORIGIN_ROT)
		print self.getPosition()
	
	def valid(self):
		return True
	
	def setAsMain(self):
		viz.logStatus("""Setting Navigator as main""")
		
		self.VIEW_LINK.setOffset([0,-self.EYE_HEIGHT,0])
		self.MOVE_SPEED = 3
		
		vizact.ontimer(0,self.updateView)
		vizact.onkeyup(self.KEYS['reset'],self.reset)
		
		def onMouseMove(e):
			euler = self.VIEW.getEuler(viz.HEAD_ORI)
			euler[0] += e.dx*0.05
			euler[1] += -e.dy*0.05
			euler[1] = viz.clamp(euler[1],-85.0,85.0)
			self.VIEW.setEuler(euler,viz.HEAD_ORI)
			print self.getPosition()
		viz.callback(viz.MOUSE_MOVE_EVENT, onMouseMove)
		
# Joystick
_extension = None
def getExtension():
	"""Get Joystick extension object"""
	global _extension
	if _extension is None:
		_extension = viz.addExtension('DirectInput.dle')
	return _extension
	
def getDevices():
	"""Returns a list of all Joystick device objects"""
	return getExtension().getJoystickDevices()
	
class Joystick(Navigator):
	def __init__(self):
		super(self.__class__,self).__init__()
		# --Override Key commands
		self.KEYS = { 'forward'	: 'w'
					,'back' 	: 's'
					,'left' 	: 'a'
					,'right'	: 'd'
					,'up'		: 4
					,'down'		: 2
					,'camera'	: 'c'
					,'restart'	: viz.KEY_END
					,'home'		: viz.KEY_HOME
					,'reset'	: 0
					,'showMenu' : 1
					,'mode'		: 5
					,'cycle'	: 3
					,'builder'	: 6
					,'walk'		: 7
					,'env'		: 8
					,'grid'		: 9
					,'utility'	: 10
					,'esc'		: 11
					,'snapMenu'	: viz.KEY_CONTROL_L
					,'interact' : viz.MOUSEBUTTON_LEFT
					,'rotate'	: viz.MOUSEBUTTON_RIGHT
					,'proxi'	: 'p'
					,'viewer'	: 'o'
					,'collide'	: 'c'
					,'viewMode' : 'm'
					,'hand'		: 'h'
					,'capslock'	: viz.KEY_CAPS_LOCK
		}
		
		# Get device from extension if not specified
		self.device = None
		if self.device is None:
			allDevices = getDevices()
			if allDevices:
				self.device = allDevices[0]	
			else:
				viz.logError('** ERROR: Failed to detect Joystick')

		# Connect to selected device
		self.joy = getExtension().addJoystick(self.device)
		if not self.joy:
			viz.logError('** ERROR: Failed to connect to Joystick')
			return None

		# Set dead zone threshold so small movements of joystick are ignored
		self.joy.setDeadZone(0.2)

		# Display joystick information in config window
		vizconfig.register(self.joy)
		vizconfig.getConfigWindow().setWindowVisible(True)

		# Create node for applying joystick movement and link to main view
		self.NODE = viz.addGroup()
		self.VIEW_LINK = viz.link(self.NODE, self.VIEW)
			
		# Use joystick axes to move joystick node
		# Horizontal (X) axis controls yaw
		# Vertical (Y) axis controls position
		
	def updateView(self):
		elapsed = viz.elapsed()
		x,y,z = self.joy.getPosition()
		twist = self.joy.getTwist()
		elevation_amount = 0
		if self.joy.isButtonDown(self.KEYS['up']):
			elevation_amount = self.MOVE_SPEED * elapsed
		if self.joy.isButtonDown(self.KEYS['down']):
			elevation_amount = -self.MOVE_SPEED * elapsed
		move_amount = self.MOVE_SPEED * elapsed
#		self.NODE.setPosition([0, 0, y * self.MOVE_SPEED * viz.getFrameElapsed()], viz.REL_LOCAL)
		self.NODE.setPosition([x*move_amount,elevation_amount,y*move_amount], viz.REL_LOCAL)
		turn_amount = self.TURN_SPEED * elapsed
		self.NODE.setEuler([twist*turn_amount,0,0], viz.REL_LOCAL)
#		self.NODE.setEuler([x * self.TURN_SPEED * , 0, 0], viz.REL_LOCAL)

	def getSensor(self):
		return self.joy
		
	def setAsMain(self):
		self.VIEW_LINK.setOffset([0,self.EYE_HEIGHT,0])
		
		viz.fov(self.FOV)
		
		self.MOVE_SPEED = 3
		
		vizact.ontimer(0, self.updateView)
		vizact.onsensorup(self.joy, 0, self.reset)

class Oculus(Navigator):
	def __init__(self):		
		super(self.__class__,self).__init__()
		
		# Link navigation node to main view
		self.NODE = viz.addGroup()
		self.VIEW_LINK = viz.link(self.NODE, self.VIEW)
		
		# --add oculus as HMD
		self.hmd = oculus.Rift()
		
		if not self.hmd.getSensor():
			viz.logError('** ERROR: Failed to detect Oculus Rift')
			return None
		else:
			# Reset HMD orientation
			self.hmd.getSensor().reset()

			# Setup navigation node and link to main view
#			self.NODE = viz.addGroup()
#			self.VIEW_LINK = viz.link(self.NODE, viz.VIEW)
			self.VIEW_LINK.preMultLinkable(self.hmd.getSensor())

			# --Apply user profile eye height to view
			profile = self.hmd.getProfile()
			if profile:
				self.VIEW_LINK.setOffset([0,profile.eyeHeight,0])
				viz.logNotice('Oculus profile name:', profile.name)
				viz.logNotice('Oculus IPD:', profile.ipd)
				viz.logNotice('Oculus player height:', profile.playerHeight)
				viz.logNotice('Oculus eye height:', profile.eyeHeight)
			else: 
				self.VIEW_LINK.setOffset([0,self.EYE_HEIGHT,0])
				
			# Check if HMD supports position tracking
			supportPositionTracking = self.hmd.getSensor().getSrcMask() & viz.LINK_POS
			if supportPositionTracking:
				
				# Add camera bounds model
				self.camera_bounds = self.hmd.addCameraBounds()
				self.camera_bounds.visible(False)

				# Change color of bounds to reflect whether position was tracked
				def checkPositionTracked():
					if self.hmd.getSensor().getStatus() & oculus.STATUS_POSITION_TRACKED:
						self.camera_bounds.color(viz.GREEN)
					else:
						self.camera_bounds.color(viz.RED)
				vizact.onupdate(0, checkPositionTracked)

				# Setup camera bounds toggle key
				def toggleBounds():
					self.camera_bounds.visible(viz.TOGGLE)
				vizact.onkeydown(self.KEYS['camera'], toggleBounds)

	# Setup functions				
	def reset(self):
		print 'Oculus: Reset'
		super(self.__class__,self).reset()
		self.hmd.getSensor().reset()
		
	def updateView(self):
		yaw,pitch,roll = self.VIEW_LINK.getEuler()
		m = viz.Matrix.euler(yaw,0,0)
		dm = viz.getFrameElapsed() * self.MOVE_SPEED
		if viz.key.isDown(self.KEYS['forward']):
			m.preTrans([0,0,dm])
		if viz.key.isDown(self.KEYS['back']):
			m.preTrans([0,0,-dm])
		if viz.key.isDown(self.KEYS['left']):
			m.preTrans([-dm,0,0])
		if viz.key.isDown(self.KEYS['right']):
			m.preTrans([dm,0,0])
		if viz.key.isDown(self.KEYS['up']):
			m.preTrans([0,dm,0])
		if viz.key.isDown(self.KEYS['down']):
			m.preTrans([0,-dm,0])
		self.NODE.setPosition(m.getPosition(), viz.REL_PARENT)

	def setAsMain(self):
		# Setup heading reset key
		vizact.onkeyup(self.KEYS['reset'], self.reset)
		
		# --Setup arrow key navigation
		self.MOVE_SPEED = 2.0	
		vizact.ontimer(0,self.updateView)
			
class Joyoculus(Navigator):
	def __init__(self):		
		super(self.__class__,self).__init__()
	
		# --Override Key commands
		self.KEYS = { 'forward'	: 'w'
					,'back' 	: 's'
					,'left' 	: 'a'
					,'right'	: 'd'
					,'up'		: 4
					,'down'		: 2
					,'camera'	: 'c'
					,'restart'	: viz.KEY_END
					,'home'		: viz.KEY_HOME
					,'reset'	: 0
					,'showMenu' : 1
					,'mode'		: 5
					,'cycle'	: 3
					,'builder'	: 6
					,'walk'		: 7
					,'env'		: 8
					,'grid'		: 9
					,'utility'	: 10
					,'esc'		: 11
					,'snapMenu'	: viz.KEY_CONTROL_L
					,'interact' : viz.MOUSEBUTTON_LEFT
					,'rotate'	: viz.MOUSEBUTTON_RIGHT
					,'proxi'	: 'p'
					,'viewer'	: 'o'
					,'collide'	: 'c'
					,'viewMode' : 'm'
					,'hand'		: 'h'
					,'capslock'	: viz.KEY_CAPS_LOCK
		}
		
		self.joystick = Joystick()
		self.oculus = Oculus()
	# Setup functions
	def getJoy(self):
		return self.joystick.joy
		
	def getHMD(self):
		return self.oculus
		
	def setOrigin(self,pos,euler):
		super(self.__class__,self).setOrigin(pos,euler)
		self.joystick.setOrigin(pos,euler)
	
	def reset(self):
		print 'Joyoculus: Reset'
		super(self.__class__,self).reset()
		self.joystick.reset()
		self.oculus.reset()
		
	def updateView(self):
		self.joystick.updateView()

	def setAsMain(self):
		viz.logStatus('Setting Joyoculus as main')
		self.VIEW_LINK = viz.link(self.joystick.VIEW_LINK,self.oculus.NODE)
		
		vizact.onsensordown(self.joystick.getSensor(),self.KEYS['reset'], self.reset)
		vizact.ontimer(0,self.joystick.updateView)
		self.joystick.setMoveSpeed(2)
		
# Check for devices
def checkOculus():
	hmd = oculus.Rift()
	if not hmd.getSensor():
		return False
	return True

def checkJoystick():
	allDevices = getDevices()
	if allDevices:
		device = allDevices[0]	
		return True
	else:
		return False

def getNavigator():
	joystickConnected = checkJoystick()
	oculusConnected = checkOculus()
	
	if oculusConnected and joystickConnected:
		nav = Joyoculus()
	elif joystickConnected:
		nav = Joystick()
	elif oculusConnected:
		nav = Oculus()
	else:
		nav = Navigator()
	nav.setAsMain()
	return nav

if __name__ == '__main__':		
	# Run scene
	viz.setMultiSample(8)
#	viz.fov(60)
	viz.go()
	
	nav = getNavigator()

	def printPos():
		print nav.getPosition()
	vizact.onkeyup(' ',printPos)
	
#	viz.mouse(viz.OFF)
	viz.mouse.setVisible(False)
	viz.mouse.setTrap()

	# Add environment
	viz.addChild('maze.osgb')