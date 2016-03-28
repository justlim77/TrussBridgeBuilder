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
		return self._norm*(vizmat.Vector(point)-self.tl)
	
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


class Holodeck(object):
	"""Full room warning. Warning along the full room, not along indivdual walls."""
	def __init__(self,
					node=None,
					threshold=0.8,
					wallList=None,
					scene=viz.MainScene,
					*args, **kwargs):# origin reference needed for placement of the warning in the scene
		
		self._wallList = wallList
		
		self._renderScene = scene
		
		if node is None:
			node = viz.addGroup()
		self._node = node
		self._isRoom = False
		self._minAlpha = 0.0
		
		self._threshold = threshold
		
		super(Holodeck, self).__init__(*args, **kwargs)
		
		# make the walls
		self._wallQuadDict = {}
		for wall in self._wallList:
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
			quad = _createTexturedWall([w, h], centerHeight, scene=self._renderScene)
			quad.setVertex(0, wall.bl)
			quad.setVertex(1, wall.br)
			quad.setVertex(2, wall.tr)
			quad.setVertex(3, wall.tl)
			quad.setParent(self._node)
			quad.drawOrder(0)
			s = viz.StencilFunc()
			s.func = viz.GL_ALWAYS
			s.funcRef = 1
			s.zpass = viz.GL_REPLACE
			quad.stencilFunc(s)
			if y == 0:
				quad.zoffset(-1)
			self._wallQuadDict[wall] = quad
		
		quad = vizshape.addQuad(axis=vizshape.AXIS_Y, size=[2.0, 2.0])
		texture = viz.addTexture('origin.png')
#		texture.wrap(viz.WRAP_S, viz.REPEAT)
#		texture.wrap(viz.WRAP_T, viz.REPEAT)
		quad.texture(texture)
#		quad.appearance(viz.TEXDECAL)
		quad.disable(viz.LIGHTING)
		quad.setParent(self._node)
		quad.zoffset(-2) 
		quad.setPosition(0, 0.01, 0)
		quad.drawOrder(2)
		quad.disable(viz.CULL_FACE)
#		quad.disable(viz.DEPTH_TEST)
#		quad.depthFunc(viz.GL_ALWAYS)
		self._originNode = quad
		
		self._node.disable(viz.INTERSECTION)
		self._node.enable(viz.CULL_FACE)
		self._node.cullFace(viz.GL_BACK)
		self._node.disable(viz.SHADOWS)
		self._node.disable(viz.SHADOW_CASTING)
	
	def remove(self):
		"""Removes the warning."""
		self._updateEvent.remove()
		self._node.remove()


def _createTexturedWall(size, centerHeight=False, textureFilename=None, scene=viz.MainScene):
	"""Creates a wall from the given size and center height.
	
	@return viz.VizNode()
	"""
	if textureFilename is None:
		textureFilename = 'holodeck/holodeck_main.png'
	quad = vizshape.addQuad(size=size, scene=scene)
	if centerHeight:
		ho = size[1]/4.0
	else:
		ho = 0
	quad.setTexCoord(0, quad.getTexCoord(0)[0]*size[0]/2.0-size[0]/4.0, quad.getTexCoord(0)[1]*size[1]/2.0-ho)
	quad.setTexCoord(1, quad.getTexCoord(1)[0]*size[0]/2.0-size[0]/4.0, quad.getTexCoord(1)[1]*size[1]/2.0-ho)
	quad.setTexCoord(2, quad.getTexCoord(2)[0]*size[0]/2.0-size[0]/4.0, quad.getTexCoord(2)[1]*size[1]/2.0-ho)
	quad.setTexCoord(3, quad.getTexCoord(3)[0]*size[0]/2.0-size[0]/4.0, quad.getTexCoord(3)[1]*size[1]/2.0-ho)
	texture = viz.addTexture(textureFilename)
	texture.wrap(viz.WRAP_S, viz.REPEAT)
	texture.wrap(viz.WRAP_T, viz.REPEAT)
	quad.appearance(viz.TEXDECAL)
	quad.texture(texture)
	quad.disable(viz.LIGHTING)
	quad.alpha(1)
	return quad


if __name__ == '__main__':
	myWallList = getWallsFromWHD(30, 10, 30, [0, 0, 0])
	myRoom = Holodeck(node=viz.addGroup(),
							wallList=myWallList)
	viz.go()
