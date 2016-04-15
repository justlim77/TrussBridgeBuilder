import sys
import viz
import vizact
import oculus

class Oculus:
	def __init__(self):		
		# --Key commands
		KEYS = { 'forward'	: 'w'
				,'back' 	: 's'
				,'left' 	: 'a'
				,'right'	: 'd'
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
			vizact.onkeyup(KEYS['reset'], self.hmd.getSensor().reset)

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
				vizact.onkeydown(KEYS['camera'], toggleBounds)
				
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
			# --Setup arrow key navigation
			MOVE_SPEED = 2.0
			def UpdateView():
				yaw,pitch,roll = self.viewLink.getEuler()
				m = viz.Matrix.euler(yaw,0,0)
				dm = viz.getFrameElapsed() * MOVE_SPEED
				if viz.key.isDown(KEYS['forward']):
					m.preTrans([0,0,dm])
				if viz.key.isDown(KEYS['back']):
					m.preTrans([0,0,-dm])
				if viz.key.isDown(KEYS['left']):
					m.preTrans([-dm,0,0])
				if viz.key.isDown(KEYS['right']):
					m.preTrans([dm,0,0])
				self.navigationNode.setPosition(m.getPosition(), viz.REL_PARENT)
			vizact.ontimer(0,UpdateView)
			
	# Setup functions		
	def setPosition(self,position):
		self.navigationNode.setPosition(position, viz.REL_PARENT)