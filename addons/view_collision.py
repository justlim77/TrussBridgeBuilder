"""Implementation of view collision module."""

import math

import viz
import vizact
import vizshape
import vizconnect
import vizmat


def getPointToPlaneDistance(normal, point, pos):
	"""Returns the signed distance from the point to the plane."""
	return (normal * point) + normal * pos


def getPointToLineDistance(linePt, normVec, pX):
	"""Returns the signed distance from the point to the line."""
	p2 = linePt + normVec
	return vizmat.Vector(pX-linePt).cross(pX-p2)


class AvatarCollision(object):
	"""An avatar collision class. This code will check for any collision of
	an avatar with the environment and modify the given avatar/transport so
	that the collisions are avoided. This is true even if physical trackers
	are being used.
	"""
	
	def __init__(self, name=None, debug=False, height=0.5, offsetDistance=0.2, collideTrackers=True, scene=None):
		self._avatar = vizconnect.getAvatar(name)
		self._avatar.getNode3d().disable(viz.INTERSECTION)
		self._updateEvent = vizact.onupdate(vizconnect.PRIORITY_ANIMATOR+2, self._update)
		
		self._trackerDict = {}
		self._transport = None
		self._intersectionList = []
		self._lastBoneMat = {}
		self._lastTransportMat = None
		self._lastNorm = None
		self._lineRot = 0
		self._collideTrackers = collideTrackers
		self._scene = scene
		
		self._offDist = offsetDistance
		
		self._height = height
		self._debug = debug
		
		self._offsetList = []
		self._debugLines = []
		self._debugPostLines = []
		self._collisionPoints = []
		self._collisionPostPoints = []
		self._generateOffsetList()
	
	def _generateOffsetList(self):
		"""Build a static offset list ahead of time to save time later"""
		# remove old
		while self._debugLines:
			self._debugLines.pop(0).remove()
		self._offsetList = []
		# add new
		angle = 0
		mat = vizmat.Transform()
		for sign in [-1, 1]:
			for angle in [0, 90, 180, 270]:
				mat.setEuler([angle, 0, 0])
				p1 = vizmat.Vector(mat.preMultVec([-sign*self._offDist, 0, self._offDist*0.75]))
				p2 = vizmat.Vector(mat.preMultVec([sign*self._offDist, 0, self._offDist*0.75]))
				self._offsetList.append((p1, p2))
				
				if self._debug:
					# add debug lines
					viz.lineWidth(5)
					viz.startLayer(viz.LINES)  
					viz.vertex(p1)
					viz.vertex(p2) 
					line = viz.endLayer()
					line.disable(viz.INTERSECTION)
					if sign == -1:
						line.color(viz.GREEN)
					else:
						line.color(viz.YELLOW)
					self._debugLines.append(line)
					sphere = vizshape.addSphere(0.1)
					sphere.disable(viz.INTERSECTION)
					sphere.disable(viz.DEPTH_TEST)
					sphere.alpha(0.5)
					sphere.drawOrder(100000)
					sphere.color(viz.YELLOW)
					self._collisionPoints.append(sphere)
		
		for angle in [0, 90, 180, 270]:
			mat.setEuler([angle, 0, 0])
			p1 = vizmat.Vector(mat.preMultVec([0, 0, 0]))
			p2 = vizmat.Vector(mat.preMultVec([0, 0, self._offDist]))
			self._offsetList.append((p1, p2))
			if self._debug:
				# add debug lines
				viz.lineWidth(5)
				viz.startLayer(viz.LINES)  
				viz.vertex(p1)
				viz.vertex(p2) 
				line = viz.endLayer()
				line.disable(viz.INTERSECTION)
				self._debugLines.append(line)
				sphere = vizshape.addSphere(0.1)
				sphere.disable(viz.INTERSECTION)
				sphere.disable(viz.DEPTH_TEST)
				sphere.alpha(0.5)
				sphere.drawOrder(100000)
				sphere.color(viz.YELLOW)
				self._collisionPoints.append(sphere)
	
	def _findCollisions(self, boneMat, startVelocity):
		"""Finds any collisions. Returns a tuple of intersection list and, updated
		velocity
		
		@return [], vizmat.Vector()
		"""
		self._intersectionList = []
		headingMat = vizmat.Transform()
		pos = boneMat.getPosition()
		headingMat.setPosition([pos[0], self._height+self._avatar.getNode3d().getPosition(viz.ABS_GLOBAL)[1], pos[2]])
		i = 0
		offsetVelocity = vizmat.Vector([0, 0, 0])
		for start, end in self._offsetList:
			start = vizmat.Vector(headingMat.preMultVec(start))
			end = vizmat.Vector(headingMat.preMultVec(end))
			# collide with the scene using intersect test
			if self._scene is None:
				scene = viz.MainWindow.getScene()
			else:
				scene = self._scene
			intersection = scene.intersect(lineBegin=start,
												lineEnd=end,
												ignoreBackFace=True)
			normal = vizmat.Vector([intersection.normal[0], 0, intersection.normal[2]]).normalize()
			
			# draw a line for the start and end
			if self._debug:
				self._debugLines[i].setVertex(0, start)
				self._debugLines[i].setVertex(1, end)
			if intersection:
				self._intersectionList.append(intersection)
				if self._debug:
					self._collisionPoints[i].setPosition(intersection.point)
					self._collisionPoints[i].visible(True)
				
				# end velocity is using intersection test to push off in vector opposite normal
				normalSign = math.copysign(1, (end-start) * normal)
				offset = (end - intersection.point)*normalSign
				if offset.length() < self._offDist:
					# get the max offset along the current offset vector
					unitOffset = vizmat.Vector(offset).normalize()
					currentMag = offsetVelocity*unitOffset
					newOffsetMag = offset.length()
					# update the current magnitude by the offset mag
					if currentMag < newOffsetMag:
						delta = unitOffset*(newOffsetMag - currentMag)
						delta[1] = 0
						offsetVelocity += delta
						offsetVelocity[1] = 0
				
				if self._debug:
					self._debugLines[i].visible(True)
			else:
				if self._debug:
					self._debugLines[i].visible(False)
					self._collisionPoints[i].visible(False)
			i += 1
		return self._intersectionList, startVelocity+offsetVelocity
	
	def adjust(self, boneDict):
		"""Adjusts the trackers/avatar based collisions using boneDict.
		Returns True if there's been a collision.
		"""
		collided = False
		boneDict = self._avatar.getSkeleton().getBoneDict()
		for bodyPart in self._trackerDict:
			if bodyPart in self._lastBoneMat:
				startPos = vizmat.Vector(self._lastBoneMat[bodyPart].getPosition())
				
				boneMat = boneDict[bodyPart].getMatrix(viz.ABS_GLOBAL)
				pos = vizmat.Vector(boneDict[bodyPart].getPosition(viz.ABS_GLOBAL))
				startingVelocity = pos-startPos
				
				intersectionList, endVelocity = self._findCollisions(boneMat, startingVelocity)
				for intersection in intersectionList:
					collided = True
					normal = vizmat.Vector(intersection.normal).normalize()
					vel = vizmat.Vector(self._transport.getVelocity())
					velMag = vel*normal
					vel = vel - (vizmat.Vector(normal)*velMag)
					vel[1] = 0
					self._transport.setVelocity(vel)
				
				# move the transport back by the difference between the starting velocity
				# and the end velocity
				transportPos = vizmat.Vector(self._transport.getPosition(viz.ABS_GLOBAL))
				diff = (endVelocity-startingVelocity)
				diff[1] = 0
				if self._collideTrackers:
					pass
				else:
					# prevent the transport from moving
					diffNorm = vizmat.Vector(diff).normalize()
					transportVec = transportPos - self._lastTransportMat.getPosition()
					# how much the transport has moved along the vector we want to move the transport back
					mag = -(diffNorm * transportVec)
					
					diff = diffNorm*min(mag, diff.length())
					diff[1] = 0
				
				self._transport.setPosition(diff+transportPos, viz.ABS_GLOBAL)
		
		for bodyPart in self._trackerDict:
			self._lastBoneMat[bodyPart] = boneDict[bodyPart].getMatrix(viz.ABS_GLOBAL)
		
		# get the matrix from the transport
		self._lastTransportMat = self._transport.getMatrix(viz.ABS_GLOBAL)
		
		return collided
	
	def _update(self):
		"""adjusts for any collision based on updates"""
		self.adjust(self._avatar.getSkeleton().getBoneDict())
	
	def setTransport(self, transport):
		"""Sets the transport. The transport node is modified as needed when
		collisions occur.
		"""
		self._transport = transport
	
	def setEnabled(self, state):
		"""Sets the enabled state of the collision tester."""
		self._updateEvent.setEnabled(state)
	
	def _removeTracker(self, bodyPart):
		"""Removes the collision tester."""
		if bodyPart in self._lastBoneMat:
			self._lastBoneMat.pop(bodyPart)
		if bodyPart in self._trackerDict:
			self._trackerDict.pop(bodyPart)
	
	def setCollideList(self, bodyPartList):
		"""Sets the body part list that's used for collision testing
		each frame.
		"""
		self._trackerDict = {}
		self._lastBoneMat = {}
		for bodyPart in bodyPartList:
			raw = None
			wrapper = self._avatar.getTrackerForBone(bodyPart)
			if wrapper:
				raw = wrapper.getRaw()
			if raw and hasattr(raw, 'setPosition'):
				self._trackerDict[bodyPart] = raw

