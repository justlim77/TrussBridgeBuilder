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

class Navigator(object):
	def __init__(self):
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
		self.MOVE_SPEED = 1.0
		self.TURN_SPEED = 45.0
		self.ORIGIN_POS = [0,0,0]
		self.ORIGIN_EULER = [0,0,0]
		
		self.node = viz.addGroup()
		self.viewLink = viz.link(self.node,viz.MainView)
		
	# Setup functions		
	def setPosition(self,position):
#		self.navigationNode.setPosition(position, viz.REL_PARENT)
		self.node.setPosition(position)
		
	def getPosition(self):
#		return self.navigationNode.getPosition(viz.REL_PARENT)
		return self.node.getPosition()
		
	def setEuler(self,euler):
#		self.navigationNode.setEuler(euler, viz.REL_PARENT)
		self.node.setEuler(euler)	
			
	def setMoveSpeed(self,speed):
		self.MOVE_SPEED = speed

	def setTurnSpeed(self,speed):
		self.TURN_SPEED = speed
	
	def setOrigin(self,pos,euler):
		self.ORIGIN_POS = pos
		self.ORIGIN_EULER = euler	
	
	def updateView(self):
		#TODO: Implement WASD movement and mouse look
		pass
		
	def reset(self):
		self.node.setPosition(self.ORIGIN_POS)
		self.node.setEuler(self.ORIGIN_EULER)
	
	def valid(self):
		return True
	
	def setMain(self):
		vizact.ontimer(0,self.updateView)
		vizact.onkeyup(KEYS['reset'],self.reset)

class Joystick(Navigator):
	def __init__(self):
		super(self.__class__,self).__init__()
		
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
		if not self.joy.valid():
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
#		self.node = viz.addGroup()
#		self.viewLink = viz.link(self.node, viz.MainView)
		
	# Use joystick axes to move joystick node
	# Horizontal (X) axis controls yaw
	# Vertical (Y) axis controls position
	def updateView(self):
		e = viz.elapsed()
		f = viz.getFrameElapsed()
		x,y,z = self.joy.getPosition()
		forward = y * self.MOVE_SPEED * e
		rotation = x * self.TURN_SPEED * f
		self.node.setEuler([rotation, 0, 0], viz.REL_LOCAL)
		self.node.setPosition([0, 0, forward], viz.REL_LOCAL)

	# Reset joystick when joystick button 0 is pressed
	def reset(self):
		self.node.setPosition(self.ORIGIN_POS)
		self.node.setEuler(self.ORIGIN_EULER)

	def valid(self):
		if not self.joy.valid():
			return False
		return True

	def setMain(self):
		vizact.ontimer(0, self.updateView)
		vizact.onsensordown(self.joy, 0, reset)
	

class Oculus(Navigator):
	def __init__(self):
		super(self.__class__,self).__init__()	
		
		import oculus

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
#			vizact.onkeyup(self.KEYS['reset'], self.hmd.getSensor().reset)

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
	def reset(self):
		self.hmd.getSensor().reset()
		
	def updateView(self):
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

	def valid(self):
		if not self.hmd.getSensor():
			return False
		return True

	def setMain(self):
		# --Setup arrow key navigation
		self.MOVE_SPEED = 2.0
		vizact.ontimer(0,self.updateView)
		vizact.onkeyup(KEYS['reset'],self.reset)

class Joculus(Navigator):
	def __init__(self):
		super(self.__class__,self).__init__()
		
		self.joystick = Joystick()
		self.hmd = Oculus()

		if not self.valid():
			print 'Failed to initialize Joculus'
			return None
			
		self.viewLink = viz.link(self.joystick.viewLink, self.hmd.navigationNode)
		
	def reset(self):
		self.joystick.reset()
		self.hmd.reset()
		
	def valid(self):
		if not self.joystick.valid() or not self.hmd.valid():
			return False
		return True
			
	def setMain(self):
		vizact.ontimer(0,self.joystick.updateView)
		vizact.onsensorup(self.joystick.joy,0,self.reset)
		

if __name__ == "__main__":
	
	vizinfo.InfoPanel()

	# Run scene
	viz.setMultiSample(4)
	viz.fov(60)
	viz.go()

#	joystick = Joystick()
#	hmd = Oculus()
	joculus = Joculus()
	if not joculus.valid():
		pass
	else:
		joculus.setMain()
#	if not hmd.hmd.getSensor():
#		print 'No hmd'
#		pass
#	elif not joystick.devices:
#		hmd.setMain()
#		viewLink = hmd.viewLink
#	else:
#		viewLink = viz.link(joystick.viewLink, hmd.navigationNode )

	#viz.link(hmd.viewLink,joystick.joystick_node)
	#viz.link(hmd.viewLink,joystick.viewLink)
	#viz.link(joystick.viewLink,hmd.viewLink)

	#mouseTracker = initTracker(HAND_DISTANCE)
	#initMouse()
	#gloveLink = initLink('glove.cfg',mouseTracker)
	#viz.link(gloveLink,highlightTool)

	# Add environment
	viz.addChild('maze.osgb')
