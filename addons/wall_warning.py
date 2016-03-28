"""
Need to provide dimensions or a physical model of the room.

Monitor:
check walls against trackers
when tracker is close to wall sends an alert to warning object

"""

import os
import math

import viz
import vizact
import vizmat
import vizshape

import vizconnect


viz.res.addPath(os.path.join(os.path.dirname(__file__), "."))


PRIORITY_WARNING = 1000
POST_SCENE_DRAW_ORDER = 100000



def getWallsFromCave(cave, offset=None):
	"""Returns a list of walls from a cave configuration.
	
	@return []
	"""
	if not offset:
		offset = [0, 0, 0]
	o = vizmat.Vector(offset)
	wallList = cave.getWalls()
	dataList = []
	for wall in wallList:
		dataList.append(Wall(o+wall.getUpperLeft(), o+wall.getUpperRight(), o+wall.getLowerLeft(), o+wall.getLowerRight()))
	return dataList


def getWallsFromWHD(w, h, d, offset):
	"""Returns a list of walls from a given of width, height and depth.
	
	@return []
	"""
	o = vizmat.Vector(offset)
	w /= 2.0
	d /= 2.0
	dataList = [Wall(o+[-w, h, d], o+[w, h, d], o+[-w, 0, d], o+[w, 0, d]), # front
				Wall(o+[w, h, d], o+[w, h, -d], o+[w, 0, d], o+[w, 0, -d]), # right
				Wall(o+[w, h, -d], o+[-w, h, -d], o+[w, 0, -d], o+[-w, 0, -d]), # back
				Wall(o+[-w, h, -d], o+[-w, h, d], o+[-w, 0, -d], o+[-w, 0, d]), # left
				Wall(o+[-w, h, -d], o+[w, h, -d], o+[-w, h, d], o+[w, h, d]), # ceiling
				Wall(o+[-w, 0, d], o+[w, 0, d], o+[-w, 0, -d], o+[w, 0, -d], collidable=False), # floor
				]
	return dataList


def getNormal(lowerLeft, lowerRight, upperLeft):
	"""Returns the (unit) normal of the wall with the given coordinates.
	
	@return []
	"""
	v0 = vizmat.Vector(lowerLeft) - vizmat.Vector(upperLeft)
	v1 = vizmat.Vector(lowerLeft) - vizmat.Vector(lowerRight)
	norm = vizmat.Vector(v0.cross(v1))
	norm.normalize()
	return norm


def getQuat(lowerLeft, lowerRight, upperLeft):
	"""Returns the orientation of the wall with the given coordinates.
	
	@return []
	"""
	mat = vizmat.Transform()
	mat.makeLookAt(vizmat.Vector(lowerLeft)-lowerRight,
					vizmat.Vector(lowerRight)-lowerRight,
					vizmat.Vector(upperLeft)-lowerRight)
	mat.preEuler([-90, 0, 0])
	return mat.getQuat()


class Wall(object):
	"""Represents a wall for computational purposes"""
	def __init__(self,
					tl, tr, bl, br,
					collidable=True,
					*args, **kwargs):
		super(Wall, self).__init__(*args, **kwargs)
		
		self.tl = tl
		self.tr = tr
		self.bl = bl
		self.br = br
		self.collidable = collidable
		
		# assume planar wall, and get vector for plane so we 
		self._quat = getQuat(self.bl, self.br, self.tl)
		self._norm = getNormal(self.bl, self.br, self.tl)
		
		mat = vizmat.Transform()
		mat.setQuat(self._quat)
		inv = mat.inverse()
		w = inv.preMultVec(self.tr)[0] - inv.preMultVec(self.tl)[0]
		h = inv.preMultVec(self.tr)[1] - inv.preMultVec(self.br)[1]
		self._size = [w, h]
		self._center = (vizmat.Vector(self.tr)+self.tl+self.bl+self.br)/4.0
	
	def getSize(self):
		"""Returns the size of the wall
		@return []
		"""
		return self._size
	
	def getQuat(self):
		"""Returns the orientation of the wall
		@return []
		"""
		return self._quat
	
	def getNormal(self):
		"""Returns the normal of the wall
		@return vizmat.Vector()
		"""
		return vizmat.Vector(self._norm)
	
	def getCenter(self):
		"""Returns the center of the wall
		@return vizmat.Vector()
		"""
		return vizmat.Vector(self._center)
	
	def getDistanceToPoint(self, point):
		"""Returns the distance from the given point to the wall.
		@return float
		"""
		return (self._norm[0]*(point[0]-self.tl[0])
				+self._norm[1]*(point[1]-self.tl[1])
				+self._norm[2]*(point[2]-self.tl[2]))
	
	def isClose(self, pos, threshold=0.2):
		"""Returns true if the tracker is within a certain threshold of the wall
		
		@return bool
		"""
		dist = self.getDistanceToPoint(pos)
		if dist < 0:
			return True
		elif dist > 0 and dist < threshold:
			return True
		else:
			return False


class _Warning(object):
	"""Base warning class"""
	def __init__(self,
					wallList,
					origin=None,
					*args, **kwargs):# origin reference needed for placement of the warning in the scene
		
		super(_Warning, self).__init__(*args, **kwargs)
		
		self._origin = origin
		self._wallList = wallList
		self._trackerDict = {}
		
		self._updateEvent = vizact.onupdate(PRIORITY_WARNING, self._onUpdate)
	
	def addWall(self, wall):
		"""Adds a wall to the warning object"""
		if not wall in self._wallList:
			self._wallList.append(wall)
	
	def addTracker(self, tracker, mode=None):
		"""Adds a tracker to the warning object. If mode is specified 
		(e.g. viz.ABS_GLOBAL), then that mode is used when sampling the
		tracker transformation.
		"""
		if not tracker in self._trackerDict:
			self._trackerDict[tracker] = mode
	
	def setEnabled(self, state):
		"""Set the enabled state of the warning."""
		self._updateEvent.setEnabled(state)
	
	def setOrigin(self, origin):
		"""Set the origin of the warning."""
		self._origin = origin
	
	def _onUpdate(self):
		"""The function that updates the warning. MUST be implemented."""
		raise NotImplementedError()


class FullRoomWarning(_Warning):
	"""Full room warning. Warning along the full room, not along individual walls.
	Use wallTextureSize if your texture has some physical dimensions (default is 1x1m).
	"""
	def __init__(self,
					node=None,
					wallTextureFilename='vizinfo.tif',
					wallTextureSize=None,
					internalColor=None,
					internalTextureFilename=None,
					threshold=0.8,
					scene=viz.MainScene,
					*args, **kwargs):# origin reference needed for placement of the warning in the scene
		
		self._renderScene = scene
		
		if internalColor is None:
			internalColor = [0.1, 0.1, 0.1, 0.8]
		self._internalColor = internalColor
		
		if wallTextureSize is None:
			wallTextureSize = [1, 1]
		
		if node is None:
			node = viz.addGroup()
		self._node = node
		self._isRoom = False
		
		self._threshold = threshold
		
		super(FullRoomWarning, self).__init__(*args, **kwargs)
		
		# make the walls
		self._wallQuadDict = {}
		self._hiddenWallQuadDict = {}
		for wall in self._wallList:
			quad = _createTexturedWall(wall,
										textureFilename=wallTextureFilename,
										textureSize=wallTextureSize,
										scene=self._renderScene)
			quad.setParent(self._node)
			quad.drawOrder(POST_SCENE_DRAW_ORDER)
			# always replace the stencil buffer wherever drawn
			s = viz.StencilFunc()
			s.func = viz.GL_ALWAYS
			s.funcRef = 1
			s.zpass = viz.GL_REPLACE
			quad.stencilFunc(s)
			# add to the regular wall dict
			self._wallQuadDict[wall] = quad
			
			# add a hidden wall quad
			quad = _createTexturedWall(wall,
										textureFilename=internalTextureFilename,
										scene=self._renderScene)
			quad.color(internalColor)
			quad.setParent(self._node)
			# draw after and on top of everything else, so we can color the scene black or with some other mask
			quad.drawOrder(POST_SCENE_DRAW_ORDER+1)
			quad.disable(viz.DEPTH_TEST)
			# only draw when the grid wall is not shown
			s = viz.StencilFunc()
			s.func = viz.GL_NOTEQUAL
			s.funcRef = 1
			quad.stencilFunc(s)
			# add to hidden wall dict
			self._hiddenWallQuadDict[wall] = quad
		
		# Set rendering flags for the node, removing it as much as possible
		# from interactions with the environment.
		self._node.disable(viz.INTERSECTION)
		self._node.enable(viz.CULL_FACE)
		self._node.cullFace(viz.GL_BACK)
		self._node.disable(viz.SHADOWS)
		self._node.disable(viz.SHADOW_CASTING)
		
		
		self.setRoom(False)
	
	def getClosestSignedDistance(self):
		"""Returns the distance to the closest wall. Will return a negative number
		if the user is past the wall.
		"""
		closestDistance = 1000000.0
		nodeInvMat = self._node.getMatrix(viz.ABS_GLOBAL).inverse()
		for wall in self._wallList:
			if wall.collidable:
				for tracker, mode in self._trackerDict.iteritems():
					# check to make sure the warning doesn't exist before we add one
					if mode is None:
						pos = tracker.getPosition()
					elif mode == viz.ABS_GLOBAL:
						pos = nodeInvMat.preMultVec(tracker.getPosition(mode))
					else:
						pos = tracker.getPosition(mode)
					distance = wall.getDistanceToPoint(pos)
					if closestDistance > distance:
						closestDistance = distance
		return closestDistance
	
	def getScene(self):
		"""Returns the scene the wall warning is being rendered to.
		
		@return viz.VizScene()
		"""
		return self._renderScene
	
	@classmethod
	def postInit(self):
		"""Setup that needs to be done after the current setup is initialized
		e.g. after vizconnect.go is called.
		"""
		for window in viz.getWindowList():
			window.setClearMask(viz.GL_COLOR_BUFFER_BIT|viz.GL_DEPTH_BUFFER_BIT|viz.GL_STENCIL_BUFFER_BIT, viz.MASK_SET)
	
	@classmethod
	def preVizGo(self):
		"""Setup that needs to be done before viz.go is called"""
		# pre viz.go
		viz.setOption('viz.display.stencil', 8)
	
	def setAvatar(self, avatar):
		"""
		@arg avatar vizconnect.Avatar()
		"""
		for name in avatar.getAttachmentPointNames():
			self.addTracker(avatar.getAttachmentPoint(name).getNode3d(), mode=viz.ABS_GLOBAL)
		transport = getParentOfClass(avatar, vizconnect.Transport)
		if transport:
			self.setOrigin(transport.getNode3d())
	
	def setRoom(self, state):
		"""Set warning to the "room" state in which the warning acts as a room."""
		if state is viz.TOGGLE:
			state = not self._isRoom
		self._isRoom = state
		# set the state of the update event so alpha changes or not if it's a room
		self._updateEvent.setEnabled(not self._isRoom)
		if self._isRoom:
			self._node.alpha(1.0)
			for wall in self._wallList:
				self._wallQuadDict[wall].visible(True)
		else:
			self._node.alpha(0.0)
			for wall in self._wallList:
				self._wallQuadDict[wall].visible(wall.collidable)
		for wall in self._hiddenWallQuadDict:
			self._hiddenWallQuadDict[wall].visible(not self._isRoom)
	
	def setEnabled(self, state):
		"""Set the enabled state of the warning. If disabled, will hide the warning."""
		super(FullRoomWarning, self).setEnabled(state)
		self._node.visible(self._updateEvent.getEnabled())
	
	def remove(self):
		"""Removes the warning."""
		self._updateEvent.remove()
		self._node.remove()
	
	def _onUpdate(self):
		"""Updates the wall warning."""
		if self._origin:
			self._node.setPosition(self._origin.getPosition(viz.ABS_GLOBAL), viz.ABS_GLOBAL)
			self._node.setQuat(self._origin.getQuat(viz.ABS_GLOBAL), viz.ABS_GLOBAL)
		# for each tracker test if it's getting close to the physical wall
		if not self._isRoom:
			closestDistance = self.getClosestSignedDistance()
			
			# when the tracker is close to a wall show the warning
			finalAlpha = 1.0-max(0, min(1, closestDistance/self._threshold))
			
			self._node.alpha(finalAlpha)


def _getSizeOfWall(wall):
	"""Returns a three tuple of width, height, centerHeight
	
	@return (float, float, bool)
	"""
	x = (wall.tl[0]-wall.tr[0])
	y = (wall.bl[1]-wall.tl[1])
	z = (wall.tl[2]-wall.tr[2])
	if z == 0:
		z = (wall.tl[2]-wall.bl[2])
	centerHeight = y == 0
	if y == 0:
		w = x
		h = z
	else:
		w = math.sqrt(x**2 + z**2)
		h = y
	return w, h, centerHeight


def _createTexturedWall(wall,
						textureFilename=None,
						textureSize=None,
						scene=viz.MainScene):
	"""Creates a wall from the given size and center height.
	
	@return viz.VizNode()
	"""
	# extract the width, height, and depth
	w, h, centerHeight = _getSizeOfWall(wall)
	
	quad = vizshape.addQuad(size=[w, h], scene=scene)
	if centerHeight:
		ho = h/4.0
	else:
		ho = 0
	for i in range(0, 4):
		tx = quad.getTexCoord(i)[0]*w/2.0-w/4.0
		ty = ho-quad.getTexCoord(i)[1]*h/2.0
		if textureSize:
			tx /= textureSize[0]
			ty /= textureSize[1]
		quad.setTexCoord(i, tx, ty)
	
	# add a texture to the wall
	if textureFilename:
		texture = viz.addTexture(textureFilename)
		texture.wrap(viz.WRAP_S, viz.REPEAT)
		texture.wrap(viz.WRAP_T, viz.REPEAT)
		quad.appearance(viz.TEXDECAL)
		quad.texture(texture)
		quad.alpha(1)
	quad.disable(viz.LIGHTING)
	
	# update the corner positions
	if wall:
		quad.setVertex(0, wall.bl)
		quad.setVertex(1, wall.br)
		quad.setVertex(2, wall.tr)
		quad.setVertex(3, wall.tl)
	
	# if it's the floor add a z offset to alleviate depth test issues
	if wall.bl[1] == 0 and wall.tl[1] == 0:
		quad.zoffset(-1)
	
	return quad


def getParentOfClass(node, refClass):
	"""Returns the parent of a given class of a node. If no match is found returns None.
	
	Recursively searches the parents of the given node and returns the first parent object
	of refClass found. If the root is reached and no match is found, the function
	returns None.
	
	@param node: the node for which we're finding a parent object of refClass
	
	@return vizconnect.Node()
	"""
	if isinstance(node, refClass):
		return node
	elif node.getParent() is None:
		return None
	elif vizconnect._isRoot(node.getParent()):
		return None
	else:
		return getParentOfClass(node.getParent(), refClass)


if __name__ == '__main__':
	# offset = (6.5405/2.0)-3.2766 = -0.00635
	# w, h, d = 6.5405, 2.61938, 6.5405
	myWallList = getWallsFromWHD(6.5405, 2.61938, 6.5405, [-0.00635, 0, -0.00635])
	myRoom = FullRoomWarning(node=viz.addGroup(),
							wallTextureFilename='holodeck/holodeck_green.png',
							internalTextureFilename='holodeck/holodeck_black.png',
							wallList=myWallList)
	
	FullRoomWarning.preVizGo()
	vizact.onkeydown('r', myRoom.setRoom, viz.TOGGLE)
#	vizact.onkeydown('v', myRoom._node.visible, viz.TOGGLE)
	vizact.onkeydown('v', myRoom.setEnabled, viz.TOGGLE)
	
	viz.add('maze.osgb')
	
	USE_VIZCONNECT = True
	if USE_VIZCONNECT:
		# if using vizconnect, you just need to set the avatar here
		vizconnect.go('vizconnect_config_default_desktop.py')
		myRoom.setAvatar(vizconnect.getAvatar())
	else:
		# if you're not using vizconnect you need to add the trackers manually
		# you also need to set the origin. The origin should be whatever is 
		# node or transport is moving the user virtually.
		viz.go()
		# add a keyboard tracker
		from vizconnect.util import virtual_trackers
		myTracker = virtual_trackers.MouseAndKeyboardWalking(positionSensitivity=3.0)
		viz.link(myTracker, viz.MainView)
		
		myRoom.addTracker(viz.MainView, mode=viz.ABS_GLOBAL)
		myRoom.setOrigin(viz.addGroup())
	
	FullRoomWarning.postInit()
