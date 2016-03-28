import viz
import vizconnect
import math
import vizshape
import vizmat

import vizact
import viztask


ZONE_RADIUS = 1.5
MAX_STOP_FRAMES = 30 # Number of frames to count for stopCheck()
STOP_THRESHOLD_SQ = .03 # Starts counting for the stopCheck() when reaching below this threshold.
INTERPOLATION_TIME = 2.0
START_FOLLOWING_EVENT = viz.getEventID('FOLLOWER_START_FOLLOWING_EVENT')


class VecSum(object):
	def __init__(self, maxSize):
		self._maxSize = maxSize
		self._vecList = []
		self._sum = vizmat.Vector()
		self._index = 0
		self._maxed = False
	
	def add(self, vec):
		if not self._maxed:
			self._vecList.append(vec)
			if len(self._vecList) >= self._maxSize:
				self._maxed = True
				self._index = 0
		else:
			self._index = (self._index+1) % self._maxSize
			self._sum -= self._vecList[self._index]
			self._vecList[self._index] = vec
		self._sum += vec
	
	def getSum(self):
		return self._sum


class Follower(object):
	STATE_FOLLOWING = 1
	STATE_STATIC = 2
	
	def __init__(self, avatar, debug=False):
		# create a zone object that we can use as a base for attachment
		self._avatar = avatar
		self._debug = debug
		
		self._offset = vizmat.Vector([0,0,0])
		self._lastPos = None
		self._state = self.STATE_STATIC
		self._motionVectorSum = VecSum(MAX_STOP_FRAMES)
		self._stopCount = 0
		self._currentInterpolationTime = 0
		parent = avatar.getParents()[0]
		
		if self._debug:
			self._zone = vizshape.addCircle(radius=ZONE_RADIUS,axis=vizshape.AXIS_Y,slices=40)
			self._zone.color(viz.GREEN)
			self._zone.alpha(0.2)
		else:
			self._zone = viz.addGroup()
		self._zone.disable(viz.INTERSECTION)
		self._zone.setParent(parent)
		
		if self._debug:
			self._menu = vizshape.addBox(size=(1.0, 0.5, .5))
			self._menu.alpha(0.5)
		else:
			self._menu = viz.addGroup()
		self._menu.disable(viz.INTERSECTION)
		self._menu.setParent(parent)
		
		self._updateEvent = vizact.onupdate(100, self._onUpdate)
	
	def getMenu(self):
		return self._menu
	
	def setAvatar(self, avatar):
		"""Sets the avatar to be followed"""
		self._avatar = avatar
		parent = avatar.getParents()[0]
		self._zone.setParent(parent)
		self._menu.setParent(parent)
	
	def startStatic(self):
		""" """
		self._startStatic()
	
	def _checkOutOfZone(self):
		"""Check the zone to see if the user is outside, if so, then switch to following."""
		distance = vizmat.Distance(self._zone.getPosition(viz.ABS_GLOBAL), self._currentPos)
		if distance > ZONE_RADIUS:
			self._startFollowing()
	
	def _checkStatic(self):
		""" Checks velocity of head tracker, waits for it to 
		remain under a threshold for a duration
		"""
		self._motionVectorSum.add(self._vel)
		speed = self._motionVectorSum.getSum().length2()
		if speed < STOP_THRESHOLD_SQ:
			# counts frames spent under the speed threshold
			self._stopCount += 1
		else:
			# while moving
			self._stopCount = 0
		
		if self._stopCount > MAX_STOP_FRAMES:
			# End menu following.
			self._startStatic()
	
	def _follow(self):
		"""Function to follow the user"""
		beginPos = self._menu.getPosition(viz.ABS_GLOBAL)
		endPos = self._currentPos + self._offset
		
		velocityCorrection = vizmat.Vector([x*viz.getFrameElapsed() for x in self._vel])
		beginPos += velocityCorrection
		
		# Have interpolation speed up towards the end of the waiting period.
		self._currentInterpolationTime += viz.getFrameElapsed()
		
		interpolation = min(1, self._currentInterpolationTime/INTERPOLATION_TIME)
		if interpolation == 1:
			pos = endPos
		else:
			pos = vizmat.Interpolate(beginPos, endPos, interpolation)
		self._menu.setPosition(pos, viz.ABS_GLOBAL)
	
	def _onUpdate(self):
		"""Update function"""
		self._currentPos = vizmat.Vector(self._avatar.getPosition(viz.ABS_GLOBAL))
		if self._lastPos is None:
			self._lastPos = self._currentPos
		self._vel = self._lastPos - self._currentPos
		if self._state == self.STATE_FOLLOWING:
			self._follow()
			self._checkStatic()
		elif self._state == self.STATE_STATIC:
			self._checkOutOfZone()
		self._lastPos = self._currentPos
	
	def _startFollowing(self):
		""" """
		self._currentInterpolationTime = 0
		self._zone.color(viz.RED)
#		self._menu.alpha(0.5)
		self._state = self.STATE_FOLLOWING
		viz.sendEvent(START_FOLLOWING_EVENT, viz.Event(follower=self))
	
	def _startStatic(self):
		""" """
		# reset the zone
		avatarPos = self._avatar.getPosition(viz.ABS_GLOBAL)
		self._zone.color(viz.GREEN)
		self._zone.setPosition(avatarPos, viz.ABS_GLOBAL)
		# update the menu
		self._menu.setPosition(self._offset+avatarPos, viz.ABS_GLOBAL)
		self._stopCount = 0
#		self._menu.alpha(1.0)
		self._state = self.STATE_STATIC


if __name__ == "__main__":
	vizconnect.go('vizconnect_config.py')
	
	DEBUGGING = False
	
	# initialize
	viz.mouse.setOverride(viz.ON) 
	viz.MainWindow.ortho(-4, 4, -4, 4, 1, -1)
	viz.window.setSize(1000	,1000) 
	viz.MainView.setPosition([0, 5, 0])
	viz.MainView.setEuler(0,90,0)
	viz.clearcolor(viz.GRAY)
	
	# add visual aids
	grid = vizshape.addGrid()
	grid.disable(viz.INTERSECTION)
	global_axes = vizshape.addAxes()
	global_axes.disable(viz.INTERSECTION)
	
	headTrackerNode = viz.add('soccerball.osgb')
	headTrackerNode.scale(2,2,2)
	headAxes = vizshape.addAxes(parent=headTrackerNode,scale=(.25,.25,.25))
	
	avatar = vizconnect.getAvatar().getNode3d()
	follower = Follower(avatar)
	viz.link(avatar, headTrackerNode)
	vizact.onkeydown(' ', follower.startStatic)
	
	cross1 = vizshape.addBox(size=(.4, 0.5, .04))
	cross1.setEuler(45,0,0)
	cross1.color(viz.RED)
	cross1.alpha(.5)
	cross1.setParent(avatar)
	cross1.setPosition([0,0,1])
	
	cross2 = vizshape.addBox(size=(.4, 0.5, .04))
	cross2.setEuler(-45,0,0)
	cross2.color(viz.RED)
	cross2.alpha(.5)
	cross2.setParent(avatar)
	cross2.setPosition([0,0,1])

#	
#	
#	menuFollowTimer = vizact.onupdate(1,menuFollow)
#	menuFollowTimer.setEnabled(False)
#	
#	zoneCheckTimer = vizact.onupdate(1,zoneCheck)
#	zoneCheckTimer.setEnabled(False)
#	
#	stopCheckTimer = vizact.onupdate(1,stopCheck)
#	stopCheckTimer.setEnabled(False)


