"""Module that allows a step climber to be added which adjusts a user's height
to allow for stepping. Requires that a model/mesh is provided for an intersection
test.
"""

import viz
import vizact
import vizconnect


class StepClimber(viz.EventClass):
	"""Class that adjusts the movable node associated with a given vizconnect
	avatar wrapper, so that the user climbs up and down steps.
	"""
	
	def __init__(self, mesh, avatarWrapper=None, dropLimit=2.0, climbLimit=0.9, suppressTransportVertical=True, scene=None):
		"""
		@arg mesh viz.VizChild()
		"""
		if avatarWrapper is None:
			avatarWrapper = vizconnect.getAvatar().getNode3d()
			if not avatarWrapper:
				raise ValueError('**Error: No default avatar wrapper found.')
		self._avatarWrapper = avatarWrapper
		self._scene = scene
		
		self._dropLimit = dropLimit
		self._climbLimit = climbLimit
		self._suppressTransportVertical = suppressTransportVertical
		
		self._node3d = viz.addGroup()
		self._node3d.disable(viz.INTERSECTION)
		self._movableNode = vizconnect.addGroup(raw=viz.addGroup(), name='movable_group'+avatarWrapper.getName())
		movable = self._movableNode.getNode3d()
		self._movableLink = viz.link(self._node3d, movable)
		
		self._transportDict = {}
		
		self._mesh = mesh
		self._mesh.hint(viz.OPTIMIZE_INTERSECT_HINT)
		self._mesh.disable(viz.DYNAMICS)
		
		self._updateEvent = vizact.onupdate(vizconnect.PRIORITY_ANIMATOR+1, self._update)
		viz.EventClass.__init__(self)
		
		# cycle through the parents all the way down the scene graph
		base = vizconnect.getBase(avatarWrapper)
		node = avatarWrapper
		while node is not base.getParent():
			# check if the node is an avatar, if so try to disable intersections on the avatar
			if node.getClassification() == vizconnect.CLASS_AVATAR:
				# Get the related tracker node from vizconnect 
				node.getNode3d().disable(viz.INTERSECTION)
				# Disable the intersect test of Head node
				node.getAttachmentPoint(vizconnect.AVATAR_HEAD).getNode3d().disable(viz.INTERSECTION)
				# Disable the intersect test of Hand node, check one or two hands
				hand_dict = node.getHands()
				for handNode in hand_dict.values():
					handNode.disable(viz.INTERSECTION)
			
			if node.getClassification() == vizconnect.CLASS_TRANSPORT:
				self._transportDict[node.getName()] = node
			
			node = node.getParent()
		
		# add node for adjusting height right above the avatar, or transport
		child = self._avatarWrapper
		parent = self._avatarWrapper.getParent()
		
		if parent.getClassification() == vizconnect.CLASS_TRANSPORT:
			child = parent
			parent = parent.getParent()
		
		self._movableNode.setParent(parent)
		child.setParent(self._movableNode)
		
		# Suppress the vertical height of transporter
		if self._suppressTransportVertical:
			self._suppressTransportVerticalEvent = vizact.onupdate(vizconnect.PRIORITY_TRANSPORT+1, self._updateTransportVertical)
	
	def getAvatarWrapper(self):
		"""Returns the avatar wrapper used by the step climber
		
		@return vizconnect.Avatar()
		"""
		return self._avatarWrapper
	
	def _updateTransportVertical(self):
		"""Updates the vertical transport movement to restrict it. We don't want
		users flying in this case.
		"""
		for node in self._transportDict.values():
			raw = node.getRaw()
			pos = raw.getPosition()
			pos[1] = 0
			raw.setPosition(pos)
	
	def _update(self):
		"""An update function that keeps the view stay on the ground."""
		headPos = viz.MainView.getPosition()
		movablePos = self._node3d.getPosition(viz.ABS_GLOBAL)
		straightDown = [headPos[0], headPos[1]-100, headPos[2]]
		if self._scene is None:
			scene = viz.MainWindow.getScene()
		else:
			scene = self._scene
		intersection = scene.intersect(headPos, straightDown, ignoreBackFace=True)
		
		if intersection.valid:
			action = None
			
			if movablePos[1] - intersection.point[1] >= self._dropLimit:# Too low
				return
			elif intersection.point[1] - movablePos[1] >= self._climbLimit:# Too high
				return
			elif movablePos[1]-0.0001 > intersection.point[1]:# Step down
				action = vizact.moveTo([movablePos[0], intersection.point[1], movablePos[2]],
										speed=10,
										interpolate=vizact.easeInSine,
										mode=viz.ABS_GLOBAL)
			elif movablePos[1]+0.0001 < intersection.point[1]:# Step up
				action = vizact.moveTo([movablePos[0], intersection.point[1], movablePos[2]],
										speed=2.5,
										mode=viz.ABS_GLOBAL)
			
			if action is not None:
				self._node3d.runAction(action)
	
	def remove(self):
		"""Removes the step climber and associated events"""
		self._updateEvent.setEnabled(0)
		self._updateEvent.remove()
		# remove link to movable node
		self._movableLink.remove()
		self._node3d.setPosition(0, 0, 0)
		self._node3d.setEuler(0, 0, 0)
		self._mesh.remove()
		self._suppressTransportVerticalEvent.setEnabled(0)
		self._suppressTransportVerticalEvent.remove()
		self.unregister()


_CLIMBER_DICT = {}


def add(mesh, avatarWrapper=None, **kwargs):
	"""Wrapper to add a StepClimber object."""
	# get default avatar if not specified
	if avatarWrapper is None:
		avatarWrapper = vizconnect.getAvatar()
		if not avatarWrapper:
			raise ValueError('**Error: No default avatar wrapper found.')
	
	# check to ensure we haven't added the avatar already
	if avatarWrapper.getName() in _CLIMBER_DICT:
		viz.logNotice('**Notice: avatar wrapper {} already registered with climber.'.format(avatarWrapper.getName()))
		return
	
	# get the climber
	climber = StepClimber(mesh, avatarWrapper=avatarWrapper, **kwargs)
	_CLIMBER_DICT[climber.getAvatarWrapper().getName()] = climber
	return climber


def get(avatarWrapper=None):
	"""Returns an existing climber for the given avatar, if registered. Otherwise."""
	if avatarWrapper is None:
		avatarWrapper = vizconnect.getAvatar()
		if not avatarWrapper:
			raise ValueError('**Error: No default avatar wrapper found.')
	
	# return the climber if registered otherwise None
	name = avatarWrapper.getName()
	if name in _CLIMBER_DICT:
		return _CLIMBER_DICT[name]
	else:
		return None


if __name__ == '__main__':
	vizconnect.go('vizconnect_config.py')
	
	import vizfx
	lobby = vizfx.addChild('art/modern_lobby.osgb')
	
	add(lobby)
