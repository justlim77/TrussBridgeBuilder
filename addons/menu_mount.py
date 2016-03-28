""" Given a vizconnect display, return a standard mount for placement of an 
immersive menu quad which is defined as plumb, level, and north-oriented 
with certain default ergonomic dimensions in world-space. 

For vizconnect Caves and Powerwalls, the standard mount is defined
with respect to the "Front Wall" determined by north-orientation test.
Caves and Powerwalls which do not have a north-oriented wall are
considered non-standard and invalid for use with this module.
In this case, the user should define an appropriate non-standard mount """

import viz
import vizmat
import vizconnect


# For Caves or Powerwalls, for use in checking wall orientation
CAVE_WALL_ORI_TOLERANCE = 1.0 # In degrees

DEFAULT_USER_EYEHEIGHT = 1.82 # meters

# Fraction of user eyeheight to place the menu mount center.
# Determined from an ergonomics perspective
DEFAULT_HEIGHT_FACTOR = 0.9
DEFAULT_DEPTH_FACTOR = 0.4 # previously was: 0.5

# Default values for an ergonomic menu mount for an average user
DEFAULT_MOUNT_CENTER = [0.0, DEFAULT_USER_EYEHEIGHT*DEFAULT_HEIGHT_FACTOR, DEFAULT_USER_EYEHEIGHT*DEFAULT_DEPTH_FACTOR]
DEFAULT_MOUNT_WIDTH = 0.65 # previously was: 1.0 Note: this is possibly biased on the small side due to limited HMD fov in testing
DEFAULT_MOUNT_HEIGHT = DEFAULT_MOUNT_WIDTH * 0.618 # Golden ratio ;)

CAVE_WALL_FORWARD_SHIFT = 0.75


def getDefault():
	"""Return a default mount.
	
	@return viz.Data()
	"""
	mount = viz.Data()
	mount.center = DEFAULT_MOUNT_CENTER[:]
	mount.width = DEFAULT_MOUNT_WIDTH
	mount.height = DEFAULT_MOUNT_HEIGHT
	return mount


def getDeviceSpecific(display=None):
	"""Return a standard mount appropriate to a given display type.
	
	If display is None the default display value is used. When an invalid 
	display is provided then a ValueError is raised.
	
	@return viz.Data()
	"""
	# Get the display, if no display is passed in, use the default defined in the given vizconnect config
	if display is None:
		display = vizconnect.getDisplay()
	
	# Get the underlying type and raw display, necessary for determining the mount
	try:
		displayType = display.getType()
		rawDisplay = display.getRaw()
	except AttributeError:
		raise ValueError("No valid vizconnect display specified and no default display defined")
	
	# get the default menu mount as a starting point
	mount = getDefault()
	
	# In the case of a Cave-like display, modify the mount according to underlying properties
	if displayType == vizconnect.DISPLAY_CAVE or displayType == vizconnect.DISPLAY_POWERWALL:
		try:
			cave = rawDisplay.displayNode
			frontWall = findFrontWall(cave)
			if frontWall is None:
				raise ValueError("No front wall is found, cave configuration is invalid")
			
			# Get wall parameters
			wall = viz.Data()
			wall.center = frontWall.getCenter()
			wall.width = frontWall.getWidth()
			wall.height = frontWall.getHeight()
			
			# For finding the edges of walls or mounts
			findBottom = lambda obj: obj.center[1] - obj.height/2.0
			findTop = lambda obj: obj.center[1] + obj.height/2.0
			
			# Compute the mount edges via comparison with wall edges
			mountBottom = max(findBottom(mount), findBottom(wall))
			mountTop = min(findTop(mount), findTop(wall))
			
			# Compute the mount
			mount.width = min(mount.width, DEFAULT_MOUNT_WIDTH)
			mount.height = mountTop - mountBottom
			mount.center = [wall.center[0], 
							mountBottom + mount.height/2.0,
							wall.center[2]-CAVE_WALL_FORWARD_SHIFT]
			
			# If the cave wall is mounted too high or low then the height
			# for the suggested mounting point may be zero, in which case
			# we have an invalid cave configuration.
			if mount.height < 0:
				raise ValueError("Invalid vizcave.Cave object, using default menu mount instead")
		except AttributeError:
			raise ValueError("Invalid vizcave.Cave object, using default menu mount instead")
	
	# successful but uninteresting, return the default mount
	return mount


def findFrontWall(cave):
	""" Given a vizcave.Cave object, get the walls and return
	the front wall. If no front wall is found, will return None.
	
	@return vizcave.Wall()
	"""
	for wall in cave.getWalls():
		# Check if the wall deviates in excess of tolerance along any axis from [Yaw=0, Pitch=0, Roll=0]
		if vizmat.QuatToAxisAngle(wall.getQuat())[3] < CAVE_WALL_ORI_TOLERANCE:
			return wall
	return None
