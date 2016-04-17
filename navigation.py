""" 
This script demonstrates how to connect to 
a joystick device and handle state changes. 
The axes control the view position/rotation 
and the trigger button resets the view. 
""" 
import sys
import viz
import vizact
import vizconfig

import vizinfo
vizinfo.InfoPanel()

class Joystick(object):
	def __init__(self):
		# Get list of joystick device information
		dinput = viz.add('DirectInput.dle')
		self.devices = dinput.getJoystickDevices()

		# Exit if no joystick detected
		if not self.devices:
#			sys.exit('No joystick devices connected')			
			print('No joystick devices connected')
			return None

		# If there is more than one device, then display selection dialog
		if len(self.devices) > 1:
			selected = viz.choose('Select joystick device', [ d.productName for d in self.devices ])
		else:
			selected = 0

		# Connect to selected device
		self.joy = dinput.addJoystick(self.devices[selected])
		if not self.joy:
#			sys.exit('Failed to connect to joystick')
			print('Failed to connect to joystick')
			return None

		# Set dead zone threshold so small movements of joystick are ignored
		self.joy.setDeadZone(0.2)

		# Display joystick information in config window
		vizconfig.register(self.joy)
		vizconfig.getConfigWindow().setWindowVisible(True)

		# Create node for applying joystick movement and link to main view
#		self.node = viz.addGroup(pos=(0,1.8,0))
		self.node = viz.addGroup()
		self.viewLink = viz.link(self.node, viz.MainView)
		
		# Use joystick axes to move joystick node
		# Horizontal (X) axis controls yaw
		# Vertical (Y) axis controls position
		self.MOVE_SPEED = 1.0
		self.TURN_SPEED = 45.0
		def UpdateJoystickMovement():
			e = viz.elapsed()
			x,y,z = self.joy.getPosition()
			self.node.setEuler([x * self.TURN_SPEED * e, 0, 0], viz.REL_LOCAL)
			self.node.setPosition([0, 0, y * self.MOVE_SPEED * viz.getFrameElapsed()], viz.REL_LOCAL)
		vizact.ontimer(0, UpdateJoystickMovement)

		# Reset joystick when joystick button 0 is pressed
		def ResetPosition():
			self.node.setPosition([0,1.8,0])
			self.node.setEuler([0,0,0])
		vizact.onsensordown(self.joy, 0, ResetPosition)
		
		def SetMoveSpeed(self,val):
			self.MOVE_SPEED = val
			
		def SetTurnSpeed(self,val):
			self.TURN_SPEED = val


class Oculus(object):

	def __init__(self):		
		import oculus
		
		# --Key commands
		self.KEYS = { 'forward'	: 'w'
					,'back' 	: 's'
					,'left' 	: 'a'
					,'right'	: 'd'
					,'down'		: 'z'
					,'up'		: 'x'
					,'reset'	: 'r'
					,'camera'	: 'c'
		}
	
		# --add oculus as HMD
		self.hmd = oculus.Rift()
		
		if not self.hmd.getSensor():
		#	sys.exit('Oculus Rift not detected')
			print('Oculus Rift not detected')
			return None
		else:
			# Reset HMD orientation
			self.hmd.getSensor().reset()
			
			# Setup heading reset key
			vizact.onkeyup(self.KEYS['reset'], self.hmd.getSensor().reset)

			# Check if HMD supports position tracking
			self.supportPositionTracking = self.hmd.getSensor().getSrcMask() & viz.LINK_POS
			if self.supportPositionTracking:

				# Add camera bounds model
				camera_bounds = self.hmd.addCameraBounds()
				camera_bounds.visible(False)

				# Change color of bounds to reflect whether position was tracked
				def CheckPositionTracked():
					if self.hmd.getSensor().getStatus() & oculus.STATUS_POSITION_TRACKED:
						camera_bounds.color(viz.GREEN)
					else:
						camera_bounds.color(viz.RED)
				vizact.onupdate(0, CheckPositionTracked)

				# Setup camera bounds toggle key
				def toggleBounds():
					camera_bounds.visible(viz.TOGGLE)
					camera_toggle.set(camera_bounds.getVisible())
				vizact.onkeydown(self.KEYS['camera'], toggleBounds)
				
			# Setup navigation node and link to main view
			self.navigationNode = viz.addGroup()
			self.viewLink = viz.link(self.navigationNode, viz.MainView)
			self.viewLink.preMultLinkable(self.hmd.getSensor())

			# --Apply user profile eye height to view
			profile = self.hmd.getProfile()
			if profile:
				self.viewLink.setOffset([0,profile.eyeHeight,0])
			else:
				self.viewLink.setOffset([0,1.8,0])

			
	# Setup functions		
	def setPosition(self,position):
#		self.navigationNode.setPosition(position, viz.REL_PARENT)
		self.navigationNode.setPosition(position)
		
	def getPosition(self):
#		return self.navigationNode.getPosition(viz.REL_PARENT)
		return self.navigationNode.getPosition()
		
	def setEuler(self,euler):
#		self.navigationNode.setEuler(euler, viz.REL_PARENT)
		self.navigationNode.setEuler(euler)	
		
	def reset(self):
		self.hmd.getSensor().reset()
		
	def UpdateView(self):
		yaw,pitch,roll = self.viewLink.getEuler()
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
		self.navigationNode.setPosition(m.getPosition(), viz.REL_PARENT)

	def initOculusNavigation(self):
		# --Setup arrow key navigation
		self.MOVE_SPEED = 2.0	
		vizact.ontimer(0,self.UpdateView)
			
	def setMoveSpeed(self,speed):
		self.MOVE_SPEED = speed
		
		
# Run scene
viz.setMultiSample(4)
viz.fov(60)
viz.go()

joystick = Joystick()
hmd = Oculus()

if not hmd.hmd.getSensor():
	print 'No hmd'
	pass
elif not joystick.devices:
	hmd.initOculusNavigation()
	viewLink = hmd.viewLink
else:
	viewLink = viz.link(joystick.viewLink, hmd.navigationNode )

#viz.link(hmd.viewLink,joystick.joystick_node)
#viz.link(hmd.viewLink,joystick.viewLink)
#viz.link(joystick.viewLink,hmd.viewLink)

#mouseTracker = initTracker(HAND_DISTANCE)
#initMouse()
#gloveLink = initLink('glove.cfg',mouseTracker)
#viz.link(gloveLink,highlightTool)

# Add environment
viz.addChild('maze.osgb')

viewLink.setPosition([0,3,0])