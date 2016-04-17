""" 
Navigator: Basic Keyboard & Mouse
Joystick: Hybrid Navigator & Joystick
Oculus: Hybrid Navigator & Oculus
Joculus: Hybrid Joystick & Oculus
""" 
import sys
import viz
import vizact
import vizconfig

# Default
class Navigator(object):
	def __init__(self):
		#Save parameters
		# --Key commands
		self._keys = { 'forward'	: 'w'
					,'back' 	: 's'
					,'left' 	: 'a'
					,'right'	: 'd'
					,'down'		: 'z'
					,'up'		: 'x'
					,'reset'	: 'r'
					,'camera'	: 'c'
		}
		self._moveSpeed = 1.0
		self._turnSpeed = 45.0
		self._originPos = [0,0,0]
		self._originRot = [0,0,0]
		
		self._eyeHeight = 1.8
		self._node = viz.addGroup()
		
	# Setup functions		
	def setPosition(self,position):
#		self.navigationNode.setPosition(position, viz.REL_PARENT)
		self._node.setPosition(position)
		
	def getPosition(self):
#		return self.navigationNode.getPosition(viz.REL_PARENT)
		return self._node.getPosition()
		
	def setEuler(self,euler):
#		self.navigationNode.setEuler(euler, viz.REL_PARENT)
		self._node.setEuler(euler)	
			
	def getEuler(self):
		return self._node.getEuler()
	
	def getNode(self):
		return self._node

	def getKeys(self):
		return self._keys
	
	def setEyeHeight(self,height):
		self._eyeHeight = height
	
	def getEyeHeight(self):
		return self._eyeHeight
	
	def setMoveSpeed(self,speed):
		self._moveSpeed = speed

	def getMoveSpeed(self):
		return self._moveSpeed
		
	def setTurnSpeed(self,speed):
		self._turnSpeed = speed
		
	def getTurnSpeed(self):
		return self._turnSpeed
	
	def setOrigin(self,pos,euler):
		self._originPos = pos
		self._originRot = euler	
	
	def updateView(self):
		#TODO: Implement WASD movement and mouse look
		yaw,pitch,roll = self._viewLink.getEuler()
		m = viz.Matrix.euler(yaw,0,0)
		dm = viz.getFrameElapsed() * self._moveSpeed
		if viz.key.isDown(self._keys['forward']):
			m.preTrans([0,0,dm])
		if viz.key.isDown(self._keys['back']):
			m.preTrans([0,0,-dm])
		if viz.key.isDown(self._keys['left']):
			m.preTrans([-dm,0,0])
		if viz.key.isDown(self._keys['right']):
			m.preTrans([dm,0,0])
		if viz.key.isDown(self._keys['up']):
			m.preTrans([0,dm,0])
		if viz.key.isDown(self._keys['down']):
			m.preTrans([0,-dm,0])
		self._node.setPosition(m.getPosition(), viz.REL_PARENT)
		
	def reset(self):
		self._node.setPosition(self._originPos)
		self._node.setEuler(self._originRot)
	
	def valid(self):
		return True
	
	def setMain(self):
		self._viewLink = viz.link(self._node,viz.MainView)
		self._viewLink.setOffset([0,self._eyeHeight,0])
		vizact.ontimer(0,self.updateView)
		vizact.onkeyup(self._keys['reset'],self.reset)
		def mouseMove(e):
			euler = self._viewLink.getEuler(viz.HEAD_ORI)
			euler[0] += e.dx*0.05
			euler[1] += -e.dy*0.05
			euler[1] = viz.clamp(euler[1],-85.0,85.0)
			self._viewLink.setEuler(euler,viz.HEAD_ORI)
		viz.callback(viz.MOUSE_MOVE_EVENT,mouseMove)
		viz.mouse(viz.OFF)
		viz.mouse.setVisible(False)
		viz.mouse.setTrap()
		

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
	def __init__(self, device=None):
		super(self.__class__,self).__init__()

		# Get device from extension if not specified
		if device is None:
			allDevices = getDevices()
			if allDevices:
				device = allDevices[0]	
			else:
				viz.logError('** ERROR: Failed to detect Joystick')

		#Save parameters
		self._device = device
		self._joy = None
		
	# Use joystick axes to move joystick _node
	# Horizontal (X) axis controls yaw
	# Vertical (Y) axis controls position
	def updateView(self):
		e = viz.elapsed()
		f = viz.getFrameElapsed()
		x,y,z = self._joy.getPosition()
		forward = y * self._moveSpeed * e
		rotation = x * self._turnSpeed * f
		self._node.setEuler([rotation, 0, 0], viz.REL_LOCAL)
		self._node.setPosition([0, 0, forward], viz.REL_LOCAL)

	# Reset joystick when joystick button 0 is pressed
	def reset(self):
		self._node.setPosition(self._originPos)
		self._node.setEuler(self._originRot)
		
	def valid(self):
		if not self._device:
			return False
		if not self._joy.valid():
			return False
		return True

	def getDevice(self):
		"""Returns Joystick device"""
		return self._device
			
	def setMain(self):
		self._joy = getExtension().addJoystick(self._device)
		
		# Set dead zone threshold so small movements of joystick are ignored
		self._joy.setDeadZone(0.2)

		# Display joystick information in config window
		vizconfig.register(self._joy)
		vizconfig.getConfigWindow().setWindowVisible(True)
		
		vizact.ontimer(0, self.updateView)
		vizact.onsensordown(self._joy, 0, reset)
	
# Oculus
class Oculus(Navigator):
	def __init__(self):
		super(self.__class__,self).__init__()	
		import oculus
		self._hmd = oculus.Rift()
		#Save parameters
#		self._hmd = None

	def getHMD(self):
		"""Returns HMD"""
		return self._hmd
		
	def reset(self):
		"""Resets HMD"""
		self._hmd.getSensor().reset()
		
	def updateView(self):
		"""Handles updating of view"""
		yaw,pitch,roll = self._viewLink.getEuler()
		m = viz.Matrix.euler(yaw,0,0)
		dm = viz.getFrameElapsed() * self._moveSpeed
		if viz.key.isDown(self._keys['forward']):
			m.preTrans([0,0,dm])
		if viz.key.isDown(self._keys['back']):
			m.preTrans([0,0,-dm])
		if viz.key.isDown(self._keys['left']):
			m.preTrans([-dm,0,0])
		if viz.key.isDown(self._keys['right']):
			m.preTrans([dm,0,0])
		if viz.key.isDown(self._keys['up']):
			m.preTrans([0,dm,0])
		if viz.key.isDown(self._keys['down']):
			m.preTrans([0,-dm,0])
		self._node.setPosition(m.getPosition(), viz.REL_PARENT)

	def valid(self):
		if not self._hmd.getSensor():
			return False
		return True

	def setMain(self):
		# --add oculus as HMD
#		import oculus
#		self._hmd = oculus.Rift()
		if self._hmd.getSensor():
			# Reset HMD orientation
			self._hmd.getSensor().reset()
			
			# Check if HMD supports position tracking
			supportPositionTracking = self._hmd.getSensor().getSrcMask() & viz.LINK_POS
			if supportPositionTracking:
				
				# Add camera bounds model
				camera_bounds = self._hmd.addCameraBounds()
				camera_bounds.visible(False)

				# Change color of bounds to reflect whether position was tracked
				def CheckPositionTracked():
					if self._hmd.getSensor().getStatus() & oculus.STATUS_POSITION_TRACKED:
						camera_bounds.color(viz.GREEN)
					else:
						camera_bounds.color(viz.RED)
				vizact.onupdate(0, CheckPositionTracked)

				# Setup camera bounds toggle key
				def toggleBounds():
					camera_bounds.visible(viz.TOGGLE)
					camera_toggle.set(camera_bounds.getVisible())
				vizact.onkeydown(self._keys['camera'], toggleBounds)
				
			# Setup navigation _node and link to main view
			self._viewLink = viz.link(self._node, viz.MainView)
			self._viewLink.preMultLinkable(self._hmd.getSensor())

			# --Apply user profile eye height to view
			profile = self._hmd.getProfile()
			if profile:
				self._viewLink.setOffset([0,profile.eyeHeight,0])
			else:
				self._viewLink.setOffset([0,self._eyeHeight,0])
				
			vizact.ontimer(0,self.updateView)
			vizact.onkeyup(self._keys['reset'],self.reset)

# Hybrid Joystick & Oculus
class Joculus(Navigator):
	def __init__(self):
		super(self.__class__,self).__init__()
		
		self._nav = Navigator()
		self._hmd = Oculus()
		self._joy = Joystick()
			
	def reset(self):
		self._joy.reset()
		self._hmd.reset()
		
	def valid(self):
		if not self._joy.valid() or not self._hmd.valid():
			return False
		return True
			
	def setMain(self):
		if self._hmd.valid() and self._joy.valid():
			self._viewLink = viz.link(self.joystick._viewLink, self.hmd.navigationNode)
			vizact.ontimer(0,self._joy.updateView)
			vizact.onsensorup(self._joy.getDevice(),0,self.reset)
		elif self._hmd.valid():
			self._hmd.setMain()
		elif self._joy.valid():
			self._joy.setMain()
		else:
			self._nav.setMain()		

if __name__ == '__main__':
	
	viz.setMultiSample(8)
	viz.go()
	
	import vizinfo
	vizinfo.InfoPanel()

	joculus = Joculus()
	joculus.setMain()
	
	joculus.setPosition([5,10,0])
	joculus.setMoveSpeed(5)
	print joculus.getPosition()
	joculus.setEuler([30,0,0])
	print joculus.getEuler()
		
	# Add environment
	viz.addChild('maze.osgb')
