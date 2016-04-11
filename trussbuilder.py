"""
[Objective]
Specify truss member dimensions and order materials required to build a 20m-long bridge across the Singapore River

[Controls]
1. Look around and orient the highlighter with the VR HEADSET
2. Navigate using WASD-keys
3. Manually turn view using Q and E
4. Control elevation with Z and X
3. Interact with floating menus using the VIRTUAL MOUSE
4. Extend or retract virtual hand with MOUSE SCROLL WHEEL
5. Cycle through build modes with TAB KEY
6. Grab and hold onto truss members by LEFT MOUSE CLICK when highlighted green
7. Adjust truss angle by RIGHT MOUSE CLICK while highlighting truss member
8. Toggle utilities with MIDDLE MOUSE CLICK
9. Toggle main menu with SPACE BAR
"""

LOAD_MESSAGE = """Any unsaved progress will be lost! 
Are you sure you want to proceed?"""

CLEAR_MESSAGE = """Your current bridge will be wiped! 
Are you sure you want to proceed?"""

QUIT_MESSAGE = """Any unsaved progress will be lost! 
Are you sure you want to proceed?"""

# Imports
import viz
import vizact
import vizcam
import vizconnect
import vizdlg
import vizfx
import vizinfo
import vizinput
import vizmenu
import vizproximity
import vizshape
import viztask
import inventory
import mathlite
import oculuslite
import panels
import roots
import sys
import themes
import tools
import xml.etree.ElementTree as ET
import vizfx.postprocess
from vizfx.postprocess.color import GrayscaleEffect
from vizfx.postprocess.composite import BlendEffect
from enum import Enum

# Globals
RESOLUTION = ([1280,720])
UTILITY_CANVAS_RES = ([80,80])
MULTISAMPLING = 8
FOV = 60
STENCIL = 8
STEREOMODE = viz.STEREO_HORZ
FULLSCREEN = 0
CLEAR_COLOR = viz.GRAY
GRID_COLOR = viz.BLACK
BUTTON_SCALE = 0.5
SOUNDS = []

BUILD_ROAM_LIMIT = ([12,-12,-10,10])	# Front,back,left,right limits in meters(m)
START_POS = ([0,5.82,-17])				# Set at 5m + avatar height above ground and 17m back fron center
BUILD_ROTATION = ([0,0,0])				# Zero-rotation to face dead center
WALK_POS = ([35,8.7,-13])
WALK_ROT = ([-30,0,0])

MENU_RES = ([1000,750])
MENU_POS = ([0,18,-8])
INSPECTOR_POS_OFFSET = ( [0,0,2] )
INSPECTOR_ROT_OFFSET = ( [] )
HEADER_TEXT = 'Truss Bridge Builder & Visualizer'
INVENTORY_MESSAGE = 'Order truss members from the catalogue and manage'

LEN_MIN = 0.1				# Min length allowed for truss
LEN_MAX = 20.0				# Max length allowed for truss
QTY_MIN = 1					# Min quantity allowed for truss
QTY_MAX = 20				# Max quantity allowed for truss

GRIDS = []

ORDERS = []
ORDERS_SIDE = inventory.OrderList()
ORDERS_TOP = inventory.OrderList()
ORDERS_BOT = inventory.OrderList()
ROWS = []
ORDERS_SIDE_ROWS = []
ORDERS_TOP_ROWS = []
ORDERS_BOT_ROWS = []
ORDERS_SIDE_FLAG = 'side'
ORDERS_TOP_FLAG = 'top'
ORDERS_BOT_FLAG = 'bot'

INVENTORY = []
BUILD_MEMBERS = []				# Array to store all truss members of bridge for saving/loading
SIDE_CLONES = []				# Array to store cloned side truss
GRAB_LINKS = []					# Array to store grab links between bridge root and truss members

BRIDGE_LENGTH = 20				# Length of bridge in meters
BRIDGE_SPAN = 10				# Span of bridge in meters
GRID_Z = -5						# Grid z-position for build members to snap to
BRIDGE_ROOT_POS = [0,5,0]		# Origin point of bridge group to position and rotate
TOP_VIEW_POS = [0,5,0]
BOT_VIEW_POS = [0,5,0]
SIDE_VIEW_ROT = [0,0,0]			# Rotation of side view
TOP_VIEW_ROT = [0,-90,0]		# Rotation of top view
BOT_VIEW_ROT = [0,90,0]			# Rotation of bottom view

class Orientation(Enum):
	side=1
	top=2
	bottom=3
ORIENTATION = Orientation.side

class Mode(Enum):
	build=0
	edit=1
	add=2
	view=3
	walk=4
MODE = Mode.build

PROXY_NODES = []
TARGET_NODES = []
SENSOR_NODES = []

PRE_SNAP_POS = []
PRE_SNAP_ROT = []
SNAP_TO_POS = []
VALID_SNAP = False

SHOW_HIGHLIGHTER = False
HAND_DISTANCE = 0.5
SCROLL_MIN = 0.2
SCROLL_MAX = 20

CACHED_GLOVE_Z = 0

DEBUG_PROXIMITY = True
DEBUG_CAMBOUNDS = False

# Setup key commands
KEYS = { 'forward'	: 'w'
		,'back'		: 's'
		,'left'		: 'a'
		,'right'	: 'd'
		,'reset'	: 'r'
		,'restart'	: viz.KEY_END
		,'home'		: viz.KEY_HOME
		,'builder'	: 'b'
		,'viewer'	: 'v'
		,'env'		: 't'
		,'grid'		: 'g'
		,'hand'		: 'h'
		,'showMenu' : ' '
		,'snapMenu'	: viz.KEY_CONTROL_L
		,'interact' : viz.MOUSEBUTTON_LEFT
		,'utility'	: viz.MOUSEBUTTON_MIDDLE
		,'rotate'	: viz.MOUSEBUTTON_RIGHT
		,'cycle'	: viz.KEY_TAB
		,'mode'		: viz.KEY_SHIFT_L
		,'proxi'	: 'p'
		,'collide'	: 'c'
		,'walk'		: '/'
}

# Initialize scene
def initScene(res=RESOLUTION,quality=4,stencil=8,stereoMode=viz.STEREO_HORZ,fullscreen=viz.FULLSCREEN,clearColor=viz.BLACK):
	viz.window.setSize(res)
	viz.setMultiSample(quality)
	#viz.fov(FOV)
	viz.setOption('viz.display.stencil', stencil)
	viz.clearcolor(clearColor)
	viz.go(stereoMode | fullscreen)
	darkTheme = themes.getDarkTheme()
	viz.setTheme(darkTheme)	


def initCamera(configPath):
	nav = vizconnect.go(configPath)
	return nav


def initOculus():
	# Reset view
	from oculuslite import oculus
	hmd = oculus.Rift()
	if hmd.getSensor():
		hmd.getSensor().reset(0)
		# Check if HMD supports position tracking
		supportPositionTracking = hmd.getSensor().getSrcMask() & viz.LINK_POS
		if supportPositionTracking:

			# Add camera bounds model
			camera_bounds = hmd.addCameraBounds()
			camera_bounds.visible(DEBUG_CAMBOUNDS)

			# Change color of bounds to reflect whether position was tracked
			def CheckPositionTracked():
				if hmd.getSensor().getStatus() & oculus.STATUS_POSITION_TRACKED:
					camera_bounds.color(viz.GREEN)
				else:
					camera_bounds.color(viz.RED)
			vizact.onupdate(0, CheckPositionTracked)
	return hmd
	
			
def initViewport(position):
	# Add a viewpoint so the user starts at the specified position
	vp = vizconnect.addViewpoint(pos=position,euler=(0,0,0))
	vp.add(vizconnect.getDisplay())
	#Start collision detection.
	viz.MainView.collision( viz.ON )
	viz.phys.enable()
	#Make gravity weaker.
#	viz.MainView.gravity(2)

	viz.stepsize(0.5)
	return vp
	
	
# Disable mouse navigation and hide the mouse cursor
def initMouse():
	viz.mouse(viz.OFF)
	viz.mouse.setVisible(viz.OFF)
	viz.mouse.setTrap(viz.ON)
	
	
def initLighting():
	# Disable the head lamps since we're doing lighting ourselves
	for window in viz.getWindowList():
		window.getView().getHeadLight().disable()
	# Create directional light
	sky_light = vizfx.addDirectionalLight(euler=(0,90,0),color=[0.7,0.7,0.7])
#	light1 = vizfx.addDirectionalLight(euler=(40,20,0), color=[0.7,0.7,0.7])
#	light2 = vizfx.addDirectionalLight(euler=(-65,15,0), color=[0.5,0.25,0.0])
#	sky_light.color(viz.WHITE)
	# Adjust ambient color
	sky_light.ambient([0.8]*3)
	viz.setOption('viz.lightModel.ambient',[0]*3)
	vizfx.setAmbientColor([0.3,0.3,0.4])


# Highlighter	
def initHighlightTool():
	from tools import highlighter
	return highlighter.Highlighter()
	
	
def initProxy():
	# Create proximity manager
	proxyManager = vizproximity.Manager()
	proxyManager.setDebug(DEBUG_PROXIMITY)
	
	# Register callbacks for proximity SENSOR_NODES
	def enterProximity(e):
		global SNAP_TO_POS
		global VALID_SNAP
		SNAP_TO_POS = e.sensor.getSource().getPosition()
		VALID_SNAP = True
	
	def exitProximity(e):
		global VALID_SNAP
		VALID_SNAP = False

	proxyManager.onEnter(None, enterProximity)
	proxyManager.onExit(None, exitProximity)
	
	return proxyManager
	
	
def initTracker(distance=0.5):
	from vizconnect.util import virtual_trackers
	tracker = virtual_trackers.ScrollWheel(followMouse=True)
	tracker.distance = distance
	return tracker


def initLink(modelPath,tracker):
	model = vizfx.addChild(modelPath)
	link = viz.link(tracker,model)
	link.postMultLinkable(viz.MainView)
	return link


# Initialize
initScene(RESOLUTION,MULTISAMPLING,STENCIL,viz.PROMPT,FULLSCREEN,(0.1, 0.1, 0.1, 1.0))
initMouse()
initLighting()
highlightTool = initHighlightTool()
proxyManager = initProxy()
grid_root = roots.GridRoot(gridColor=GRID_COLOR,origin=START_POS)
environment_root = roots.EnvironmentRoot(visibility=False)
bridge_root = roots.BridgeRoot(BRIDGE_ROOT_POS,SIDE_VIEW_ROT)

# Setup audio
startSound = viz.addAudio('./resources/sounds/return_to_holodeck.wav')
buttonHighlightSound = viz.addAudio('./resources/sounds/button_highlight.wav')
clickSound = viz.addAudio('./resources/sounds/click.wav')
showMenuSound = viz.addAudio('./resources/sounds/show_menu.wav')
hideMenuSound = viz.addAudio('./resources/sounds/hide_menu.wav')
viewChangeSound = viz.addAudio('./resources/sounds/page_advance.wav')
warningSound = viz.addAudio('./resources/sounds/out_of_bounds_warning.wav')

SOUNDS = [ startSound,buttonHighlightSound,clickSound,showMenuSound,
			hideMenuSound,viewChangeSound,warningSound ]

# Set volume
for sound in SOUNDS:
	sound.volume(0.5)
warningSound.volume(0.05)


# Parse catalogue from data subdirectory
def getCatalogue(path):
	return ET.parse(str(path)).getroot()
catalogue_root = getCatalogue('data/catalogues/catalogue_CHS.xml')


def updateMouseStyle(canvas):
	"""Update mouse style based on current options"""
	if canvas.getRenderMode() in [viz.CANVAS_WORLD,viz.CANVAS_WORLD_OVERLAY]:
		canvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
#		canvas.setMouseStyle(viz.CANVAS_MOUSE_VISIBLE)


# Add environment effects
env = viz.addEnvironmentMap('resources/textures/sky.jpg')
effect = vizfx.addAmbientCubeEffect(env)
vizfx.getComposer().addEffect(effect)
lightEffect = vizfx.addLightingModel(diffuse=vizfx.DIFFUSE_LAMBERT,specular=None)
vizfx.getComposer().addEffect(lightEffect)


# Bridge pin and roller supports
pinSupport = vizfx.addChild('resources/pinSupport.osgb',pos=(-9.5,4,0),scale=[1,1,11])
rollerSupport = vizfx.addChild('resources/rollerSupport.osgb',pos=(9.5,4,0),scale=[1,1,11])
supports = [pinSupport,rollerSupport]


#Setup anchor points for truss members
pinAnchorSphere = vizshape.addSphere(0.2,pos=([-BRIDGE_SPAN,BRIDGE_ROOT_POS[1],-(BRIDGE_SPAN*0.5)]))
pinAnchorSphere.visible(False)
pinLink = viz.link(pinAnchorSphere,viz.NullLinkable)
pinAnchorSensor = vizproximity.Sensor(vizproximity.Sphere(0.3,center=[0,0.1,0]),pinLink)
proxyManager.addSensor(pinAnchorSensor)
viz.grab(pinSupport,pinAnchorSphere)

rollerAnchorSphere = vizshape.addSphere(0.2,pos=([BRIDGE_SPAN,BRIDGE_ROOT_POS[1],-(BRIDGE_SPAN*0.5)]))
rollerAnchorSphere.visible(False)
rollerLink = viz.link(rollerAnchorSphere,viz.NullLinkable)
rollerAnchorSensor = vizproximity.Sensor(vizproximity.Sphere(0.3,center=[0,0.1,0]), rollerLink)
proxyManager.addSensor(rollerAnchorSensor)
viz.grab(rollerSupport,rollerAnchorSphere)

for model in supports:
#	model.texture(env)
#	model.appearance(viz.ENVIRONMENT_MAP)
	model.apply(effect)
	model.apply(lightEffect)
	model.collideMesh()
	model.disable(viz.DYNAMICS)
	viz.grab(bridge_root,model)

# Create canvas for displaying GUI objects
instructionsPanel = vizinfo.InfoPanel(title=HEADER_TEXT,align=viz.ALIGN_CENTER_BASE,icon=False)
instructionsPanel.getTitleBar().fontSize(36)

# Options panel
optionPanel = vizinfo.InfoPanel(title=HEADER_TEXT, text='Options',align=viz.ALIGN_CENTER_TOP,icon=False)
optionPanel.getTitleBar().fontSize(36)
optionPanel.addSection('File')
saveButton = optionPanel.addItem(viz.addButtonLabel('Save'))
saveButton.length(2)
loadButton = optionPanel.addItem(viz.addButtonLabel('Load'))
loadButton.length(2)
optionPanel.addSection('Game')
resetButton = optionPanel.addItem(viz.addButtonLabel('Reset'))
resetButton.length(2)
quitButton = optionPanel.addItem(viz.addButtonLabel('Quit'))
quitButton.length(2)

# Initialize order panel containing mainRow and midRow
#inventoryPanel = vizdlg.Panel(layout=vizdlg.LAYOUT_VERT_CENTER,align=viz.ALIGN_CENTER,spacing=0,margin=(0,0))
inventoryPanel = vizinfo.InfoPanel(title=HEADER_TEXT,text='Order truss members from the catalogue & manage your inventory', align=viz.ALIGN_CENTER_BASE, icon=False)
inventoryPanel.getTitleBar().fontSize(36)

# Initialize mainRow
# Initialize midRow
midRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,align=viz.ALIGN_CENTER_TOP,border=False,background=False,spacing=20)
# Initialize orderPanel box
orderPanel = midRow.addItem(vizinfo.InfoPanel('Fill in all required fields',align=viz.ALIGN_LEFT_TOP,margin=(0,0),icon=False))
orderPanel.setTitle( 'Order' )	
orderPanel.getTitleBar().fontSize(28)
orderPanel.addSeparator()
# Initialize type
typeDropList = viz.addDropList()
typeDropList.addItem('CHS', 0)
trussType = orderPanel.addLabelItem('Type', typeDropList)
# Initialize diameterDropList
diameterDropList = viz.addDropList()
for member in catalogue_root.iter('member'):
	diameter = member.get('diameter')
	diameterDropList.addItem(diameter)
diameterDropList.select(19)
diameter = orderPanel.addLabelItem('Diameter (mm)', diameterDropList)
# Initialize thicknessDropList
thicknessDropList = viz.addDropList()
thicknesses = []
for thickness in catalogue_root[diameterDropList.getSelection()]:
	thicknesses.append(thickness.text)
thicknessDropList.addItems(thicknesses)
thicknessDropList.select(2)
thickness = orderPanel.addLabelItem('Thickness (mm)', thicknessDropList)
# Initilize lengthTextbox with default value of 1m
lengthTextbox = viz.addTextbox()
lengthTextbox.message('1')
length = orderPanel.addLabelItem('Length (m)', lengthTextbox)
# Initialize quantityTextbox with default value of 1qty
quantityTextbox = viz.addTextbox()
quantitySlider = viz.addProgressBar('1')
qtyProgressPos = mathlite.getNewRange(1,QTY_MIN,QTY_MAX,0.0,1.0)
quantitySlider.set(qtyProgressPos)
#quantity = orderPanel.addLabelItem('Quantity', quantityTextbox)
quantity = orderPanel.addLabelItem('Quantity', quantitySlider)

# Initialize ordering buttons
orderSideButton = orderPanel.addItem(viz.addButtonLabel('Add to Side'),align=viz.ALIGN_RIGHT_BOTTOM)
orderTopButton = orderPanel.addItem(viz.addButtonLabel('Add to Top'),align=viz.ALIGN_RIGHT_BOTTOM)
orderBottomButton = orderPanel.addItem(viz.addButtonLabel('Add to Bottom'),align=viz.ALIGN_RIGHT_BOTTOM)

# Initialize stockPanel
stockMainPanel = vizinfo.InfoPanel('Ordered truss members',align=viz.ALIGN_CENTER_TOP,margin=(0,0),icon=False)
stockMainPanel.setTitle( 'Stock' )
stockMainPanel.getTitleBar().fontSize(28)
stockMainPanel.addSeparator()

# Initialize side order tab
stockPanel = vizdlg.TabPanel()

# Side orders inventory
ORDERS_SIDE_GRID = panels.CreateLabelledPanel()
stockPanel.addPanel('Side',ORDERS_SIDE_GRID)

# Top orders inventory
ORDERS_TOP_GRID = panels.CreateLabelledPanel()
stockPanel.addPanel('Top',ORDERS_TOP_GRID)

# Bottom orders inventory
ORDERS_BOT_GRID = panels.CreateLabelledPanel()
stockPanel.addPanel('Bottom',ORDERS_BOT_GRID)

stockMainPanel.addItem(stockPanel)
midRow.addItem(stockMainPanel,align=viz.ALIGN_LEFT_TOP)

# Add mid row to inventory main panel
inventoryPanel.addItem(midRow)

bottomRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,align=viz.ALIGN_CENTER_TOP,border=False,background=False,spacing=20)
doneButton = bottomRow.addItem(viz.addButtonLabel('DONE'),align=viz.ALIGN_CENTER_TOP)
doneButton.length(2)
inventoryPanel.addItem(bottomRow)

# Create floating inspector panel
inspectorCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
inspector = panels.InspectorPanel()
statPanel = inspector.GetPanel()
statPanel.setParent(inspectorCanvas)
## Link inspector canvas with main view
#inspectorLink = viz.link(viz.MainView, inspectorCanvas)
##inspectorLink.preMultLinkable(viz.MainView)
#inspectorLink.preTrans( [-2, -3, 5] )
#inspectorLink.preEuler( [-45, 0, 0] )

utilityButtons = []
# Create docked utility panel
utilityCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
points = mathlite.getPointsInCircum(30,8)
# Circle backdrop
circleBackdrop = viz.addButton(parent=utilityCanvas)
circleBackdrop.texture(viz.addTexture('resources/GUI/dropdownarrow-128.png'))
circleBackdrop.setScale(1.5,1.5)
# Menu button
menuButton = viz.addButton(parent=utilityCanvas)
menuButton.texture(viz.addTexture('resources/GUI/menu-128.png'))
menuButton.setPosition(0,0)
menuButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Reset view button
homeButton = viz.addButton(parent=utilityCanvas)
homeButton.texture(viz.addTexture('resources/GUI/reset-128.png'))
homeButton.setPosition(0,0)
homeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Build mode button
buildModeButton = viz.addButton(parent=utilityCanvas)
buildModeButton.texture(viz.addTexture('resources/GUI/wrench-128.png'))
buildModeButton.setPosition(0,0)
buildModeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Viewer mode button
viewerModeButton = viz.addButton(parent=utilityCanvas)
viewerModeButton.texture(viz.addTexture('resources/GUI/viewer-128.png'))
viewerModeButton.setPosition(0,0)
viewerModeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Walk mode button
walkModeButton = viz.addButton(parent=utilityCanvas)
walkModeButton.texture(viz.addTexture('resources/GUI/walking-128.png'))
walkModeButton.setPosition(0,0)
walkModeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Toggle environment button
toggleEnvButton = viz.addButton(parent=utilityCanvas)
toggleEnvButton.texture(viz.addTexture('resources/GUI/environment-128.png'))
toggleEnvButton.setPosition(0,0)
toggleEnvButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Toggle grid button
toggleGridButton = viz.addButton(parent=utilityCanvas)
toggleGridButton.texture(viz.addTexture('resources/GUI/grid-64.png'))
toggleGridButton.setPosition(0,0)
toggleGridButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Reset orientation button
resetOriButton = viz.addButton(parent=utilityCanvas)
resetOriButton.texture(viz.addTexture('resources/GUI/compass-128.png'))
resetOriButton.setPosition(0,0)
resetOriButton.setScale(BUTTON_SCALE,BUTTON_SCALE)

utilityButtons = ( [menuButton,homeButton,buildModeButton,viewerModeButton,walkModeButton,toggleEnvButton,toggleGridButton,resetOriButton] )
for i, button in enumerate(utilityButtons):
	button.setPosition(0.5 + points[i][0], 0.5 + points[i][1])
	
# Link utility canvas with main view
utilityLink = viz.link(viz.MainView,utilityCanvas)
utilityLink.preTrans( [0, 0, 1.5] )

# Rotation Panel
rotationCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
rotationPanel = vizdlg.GridPanel(parent=rotationCanvas,align=viz.ALIGN_CENTER)
rotationSlider = viz.addProgressBar('Angle')
rotationLabel = viz.addText('0')
row = rotationPanel.addRow([rotationSlider,rotationLabel])

# Link rotation canvas with main view
rotationLink = viz.link(viz.MainView,rotationCanvas)
rotationLink.preEuler( [0,30,0] )
rotationLink.preTrans( [0,0.1,1] )

# Add tabbed panels to main menu canvas
menuCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER_TOP)
tabbedMenu = vizdlg.TabPanel(align=viz.ALIGN_CENTER_TOP,parent=menuCanvas)
tabbedMenu.addPanel('Instructions',instructionsPanel)
tabbedMenu.addPanel('Inventory',inventoryPanel)
tabbedMenu.addPanel('Options',optionPanel)


def initCanvas():	
#	menuCanvas.setRenderWorld(MENU_RES,[20,viz.AUTO_COMPUTE])
	menuCanvas.setRenderWorldOverlay(MENU_RES,fov=90.0,distance=3.0)
	menuCanvas.setPosition(0,0,6)
	updateMouseStyle(menuCanvas)
	
#	inspectorCanvas.setRenderWorld(RESOLUTION,[20,viz.AUTO_COMPUTE])
	inspectorCanvas.setRenderWorldOverlay(RESOLUTION,fov=90.0,distance=3.0)
	inspectorCanvas.setPosition(0,0,2)
	inspectorCanvas.setEuler(0,0,0)
	
	utilityCanvas.setRenderWorld(UTILITY_CANVAS_RES,[1,viz.AUTO_COMPUTE])
	utilityCanvas.setPosition(0,0,0)
	utilityCanvas.setEuler(0,0,0)
	utilityCanvas.visible(viz.OFF)
	updateMouseStyle(utilityCanvas)
	
	rotationCanvas.setRenderWorld([300,100],[1,viz.AUTO_COMPUTE])
	rotationCanvas.setPosition(0,0,0)
	rotationCanvas.setEuler(0,0,0)
#	rotationCanvas.visible(viz.OFF)
initCanvas()
		
		
#def inspectMember(obj):
#	inspector.diameter_stat.message('d (mm): ' + str(obj.diameter))
#	inspector.thickness_stat.message('t (mm): ' + str(obj.thickness))
#	inspector.length_stat.message('l (m): ' + str(obj.length))
#	inspector.rotation_stat.message('angle: ' + str(obj.getEuler()[2]))

def inspectMember(obj):
#	inspector.diameter_stat.message('d (mm): ' + str(obj.diameter))
#	inspector.thickness_stat.message('t (mm): ' + str(obj.thickness))
#	inspector.length_stat.message('l (m): ' + str(obj.length))
#	inspector.rotation_stat.message('angle: ' + str(obj.getEuler()[2]))
	if obj != None:			
		inspector.SetMessage(str(obj.diameter) + 'mm x ' +
								str(obj.thickness) + 'mm x' +
								str(obj.length) + 'm at' +
								str(int(obj.getEuler()[2])) + 'deg')
	else:
		inspector.SetMessage(None)


def showdialog(message,func):
	dialog = vizdlg.MessageDialog(message=message, title='Warning', accept='Yes (Enter)', cancel='No (Esc)')
	dialog.setScreenAlignment(viz.ALIGN_CENTER)
	
	warningSound.play()
	
	while True:

		yield dialog.show()

		if dialog.accepted:
			func()
		else:
			pass
			
		dialog.remove()			
		yield viztask.waitTime(1)
		
def clearBridge():
	viztask.schedule(showdialog(CLEAR_MESSAGE,clearMembers))

def quitGame():
	viztask.schedule(showdialog(QUIT_MESSAGE,viz.quit))
	
def loadBridge():
	viztask.schedule(showdialog(LOAD_MESSAGE,LoadData))
	
class Order(object):
	'Base class for all ORDERS'
	orderCount = 0
	
	def __init__(self,type='CHS',diameter=508,thickness=16,length=4,quantity=1):
		self.type = type
		self.diameter = diameter
		self.thickness = thickness
		self.length = length
		self.quantity = quantity
		Order.orderCount += 1		
		
	def __repr__(self):
		return repr((self.diameter, self.thickness, self.length, self.quantity))

	def __del__(self):
		class_name = self.__class__.__name__
		
	def __add__(self,other):
		return Order(self.type,self.diameter,self.thickness,self.length,self.quantity+other.quantity)
		
	def displayCount(self):
		print "Total ORDERS %d" % Order.orderCount
		
	def displayOrder(self):
		print "Type: ", self.type, ", Diameter: ", self.diameter, ", Thickness: ", self.thickness, " Length: ", self.length, " Quantity: ", self.quantity
		
def addOrder(orderTab,orderList=inventory.OrderList(),orderRow=[],flag=''):
	"""
	adds new truss member order
	"""	
	newOrder = Order()
	
	_diameter = diameterDropList.getItem(diameterDropList.getSelection())
	_thickness = thicknessDropList.getItem(thicknessDropList.getSelection())
	_length = viz.clamp(float(lengthTextbox.get()),LEN_MIN,LEN_MAX)
	_quantity = mathlite.getNewRange(quantitySlider.get(),0.0,1.0,QTY_MIN,QTY_MAX)
	
	setattr(newOrder, 'diameter', float(_diameter))
	setattr(newOrder, 'thickness', float(_thickness))
	setattr(newOrder, 'length', float(_length))
	setattr(newOrder, 'quantity', int(_quantity))
	
	#Check for existing order
	append = True
	if len(orderList) < 1:
		orderList.append(newOrder)
		append = False
	else:	
		for order in orderList:
			_d = order.diameter
			_t = order.thickness
			_l = order.length
			_q = order.quantity
					
			if newOrder.diameter == _d and newOrder.thickness == _t and newOrder.length == _l:
				order.quantity += newOrder.quantity
				if(order.quantity > 99):
					setattr(order, 'quantity', 99)
				append = False
	
	if append == True:	
		orderList.append(newOrder)
	
	#Clear grid
	for row in orderRow:
		orderTab.removeRow(row)
	
	#Sort lowest to highest (d x Th x l)
	orderList = orderList.sortByAttr()
	
	#Populate grid with ORDERS in order list
	for _order in orderList:
		__d = viz.addText(str(_order.diameter))
		__t = viz.addText(str(_order.thickness))
		__l = viz.addText(str(_order.length))
		__q = viz.addText(str(_order.quantity))
		deleteButton = viz.addButtonLabel('X')
		_index = orderList.index(_order)
		_row = orderTab.addRow( [__d,__t,__l,__q,deleteButton] )
		vizact.onbuttonup ( deleteButton, deleteOrder, _order, orderList, _index, _row, orderRow, orderTab, flag )
		orderRow.append(_row)


def deleteOrder(order, orderList, index, row, orderRow, orderTab, flag ):	
	orderList.pop(index)		
	orderTab.removeRow(row)
	orderRow.remove(row)	
	
	
def createInventory():
#	Create inventory panel
	global inventoryCanvas
	inventoryCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER_TOP)
	inventoryGrid = vizdlg.GridPanel(align=viz.ALIGN_CENTER_TOP,cellAlign=vizdlg.LAYOUT_VERT_LEFT,parent=inventoryCanvas)
	
	global tabbedPanel
	tabbedPanel = vizdlg.TabPanel(align=viz.ALIGN_CENTER_TOP,layout=vizdlg.LAYOUT_VERT_LEFT,parent=inventoryCanvas)

	# Side truss inventory
	global sideInventory
	sideInventory = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	sideInventory.layout = vizdlg.LAYOUT_VERT_LEFT
	
	global sidePanel
	sidePanel = tabbedPanel.addPanel('Side',sideInventory)
	
	global sideRows
	sideRows = []
	
	# Top truss inventory
	global topInventory
	topInventory = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	topInventory.layout = vizdlg.LAYOUT_VERT_LEFT
	
	global topPanel
	topPanel = tabbedPanel.addPanel('Top',topInventory)
	
	global topRows
	topRows = []
	
	# Bottom truss inventory
	global bottomInventory
	bottomInventory = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	bottomInventory.layout = vizdlg.LAYOUT_VERT_LEFT
	
	global bottomPanel
	bottomPanel = tabbedPanel.addPanel('Bottom',bottomInventory)

	global bottomRows
	bottomRows = []

	inventoryGrid.addRow([statPanel,tabbedPanel])

	inventoryCanvas.setRenderWorld([400,200],[1,viz.AUTO_COMPUTE])
	updateMouseStyle(inventoryCanvas)
	# Link rotation canvas with main view
	inventoryLink = viz.link(viz.MainView,inventoryCanvas)
	inventoryLink.preEuler( [0,30,0] )
	inventoryLink.preTrans( [0,0,1] )
createInventory()


def clearInventory():
	global sideRows
	global topRows
	global bottomRows
	
	for row in sideRows:
		sideInventory.removeRow(row)
	for row in topRows:
		topInventory.removeRow(row)
	for row in bottomRows:
		bottomInventory.removeRow(row)
		
	sideRows = []
	topRows = []
	bottomRows = []
	

def populateInventory(sideList,topList,botList):
	clearInventory()
	
	print 'populateInventory: sideList:', sideList
	
	# Generate truss buttons based on respective lists
	for sideOrder in sideList:
		msg = '{}mm(d) x {}mm(th) x {}m(l) [{}]'.format ( sideOrder.diameter, sideOrder.thickness, sideOrder.length, sideOrder.quantity )
		sideButton = viz.addButtonLabel ( msg )
		vizact.onbuttonup ( sideButton, createTrussNew, sideOrder, 'resources/CHS.osgb' )
		row = sideInventory.addRow ( [sideButton] )
		sideRows.append ( row )
		vizact.onbuttonup ( sideButton, updateQuantity, sideOrder, sideButton, sideList, sideInventory, row )
		vizact.onbuttonup ( sideButton, clickSound.play )
	for topOrder in topList:
		msg = '{}mm(d) x {}mm(th) x {}m(l) [{}]'.format ( topOrder.diameter, topOrder.thickness, topOrder.length, topOrder.quantity )
		topButton = viz.addButtonLabel ( msg )
		vizact.onbuttonup ( topButton, createTrussNew, topOrder, 'resources/CHS.osgb' )
		row = topInventory.addRow( [topButton] )
		topRows.append ( row )
		vizact.onbuttonup ( topButton, updateQuantity, topOrder, topButton, topList, topInventory, row )
		vizact.onbuttonup ( topButton, clickSound.play )
	for botOrder in botList:
		msg = '{}mm(d) x {}mm(th) x {}m(l) [{}]'.format ( botOrder.diameter, botOrder.thickness, botOrder.length, botOrder.quantity )
		botButton = viz.addButtonLabel ( msg )
		vizact.onbuttonup ( botButton, createTrussNew, botOrder, 'resources/CHS.osgb' )
		row = bottomInventory.addRow ( [botButton] )
		bottomRows.append ( row )
		vizact.onbuttonup ( botButton, updateQuantity, botOrder, botButton, botList, bottomInventory, row )
		vizact.onbuttonup ( botButton, clickSound.play )
		
	# Clear order panel rows
	for topRow in ORDERS_TOP_ROWS:
		ORDERS_TOP_GRID.removeRow(topRow)
	for sideRow in ORDERS_SIDE_ROWS:
		ORDERS_SIDE_GRID.removeRow(sideRow)
	for botRow in ORDERS_BOT_ROWS:
		ORDERS_BOT_GRID.removeRow(botRow)
	
	# Clear orders from order list
	for order in sideList:
		sideList.pop()
	sideList = []
	for order in topList:
		topList.pop()
	topList = []
	for order in botList:
		botList.pop()
	botList = []
	
	# Show menu
	inventoryCanvas.visible(viz.ON)


def createTruss(order=Order(),path=''):
	truss = viz.addChild(path,cache=viz.CACHE_COPY)
	truss.order = order
	truss.diameter = float(order.diameter)
	truss.thickness = float(order.thickness)
	truss.length = float(order.length)
	truss.quantity = int(order.quantity)
	
	truss.setScale([truss.length,truss.diameter/1000,truss.diameter/1000])	

	posA = truss.getPosition()
	posA[0] -= truss.length / 2
	nodeA = vizshape.addSphere(0.2,pos=posA)
	nodeA.disable(viz.PICKING)
	nodeA.visible(False)
	viz.grab(truss,nodeA)
	
	posB = truss.getPosition()
	posB[0] += truss.length / 2
	nodeB = vizshape.addSphere(0.2,pos=posB)
	nodeB.disable(viz.PICKING)
	nodeB.visible(False)
	viz.grab(truss,nodeB)
	
	truss.proxyNodes = [nodeA,nodeB]
	
	targetA = vizproximity.Target(truss.proxyNodes[0])
	targetB = vizproximity.Target(truss.proxyNodes[1])
	
	truss.targetNodes = [targetA,targetB]
	
	sensorA =  vizproximity.addBoundingSphereSensor(truss.proxyNodes[0])
	sensorB =  vizproximity.addBoundingSphereSensor(truss.proxyNodes[1])
	
	truss.sensorNodes = [sensorA,sensorB]
	
	return truss


def createTrussNew(order=Order(),path='',loading=False):
	truss = vizfx.addChild(path,cache=viz.CACHE_COPY)
	truss.order = order
	truss.diameter = float(order.diameter)
	truss.thickness = float(order.thickness)
	truss.length = float(order.length)
	truss.quantity = int(order.quantity)
	truss.orientation = ORIENTATION
	
	truss.setScale([truss.length,truss.diameter/1000,truss.diameter/1000])	

	# Setup proximity-based snapping nodes
	posA = truss.getPosition()
	posA[0] -= truss.length / 2
	nodeA = vizshape.addSphere(0.2,pos=posA)
	nodeA.visible(False)
	viz.grab(truss,nodeA)
	
	posB = truss.getPosition()
	posB[0] += truss.length / 2
	nodeB = vizshape.addSphere(0.2,pos=posB)
	nodeB.visible(False)
	viz.grab(truss,nodeB)
	
	truss.proxyNodes = [nodeA,nodeB]
	
	# Setup target nodes at both ends
	targetA = vizproximity.Target(truss.proxyNodes[0])
	targetB = vizproximity.Target(truss.proxyNodes[1])	
	truss.targetNodes = [targetA,targetB]
	
	# Setup sensor nodes at both ends
	sensorA =  vizproximity.addBoundingSphereSensor(truss.proxyNodes[0])
	sensorB =  vizproximity.addBoundingSphereSensor(truss.proxyNodes[1])	
	truss.sensorNodes = [sensorA,sensorB]
	
	global INVENTORY
	global BUILD_MEMBERS
	global highlightTool
	global proxyManager
	global PROXY_NODES
	global TARGET_NODES
	global SENSOR_NODES
	
	global PRE_SNAP_POS	
	global PRE_SNAP_ROT
	global SNAP_TO_POS
	PRE_SNAP_POS = truss.getPosition()
	PRE_SNAP_ROT = truss.getEuler()
	
	PROXY_NODES.append(truss.proxyNodes[0])
	PROXY_NODES.append(truss.proxyNodes[1])
	TARGET_NODES.append(truss.targetNodes[0])
	TARGET_NODES.append(truss.targetNodes[1])
	SENSOR_NODES.append(truss.sensorNodes[0])
	SENSOR_NODES.append(truss.sensorNodes[1])
	
	# Enable truss nodes to interact with other sensors
	proxyManager.addTarget(truss.targetNodes[0])
	proxyManager.addTarget(truss.targetNodes[1])

	BUILD_MEMBERS.append(truss)
		
	# Merge lists
	mergedList = BUILD_MEMBERS + INVENTORY
	for listItem in mergedList:
		listItem.texture(env)
		listItem.appearance(viz.ENVIRONMENT_MAP)
		listItem.apply(effect)
		listItem.apply(lightEffect)		
	try:
		highlightTool.setItems(mergedList)
	except:
		print 'Highlighter not initialized!'
	
	if not loading:
		global grabbedItem
		global highlightedItem
		global isgrabbing
		
		grabbedItem = truss		
		highlightedItem = truss
		isgrabbing = True
		
		truss.isNewMember = True		
		cycleMode(Mode.add)
		print 'New truss: Not loading'
	else:
		truss.isNewMember = False
	
	return truss


def generateMembers(loading=False):
	"""Create truss members based on order list"""
	global INVENTORY
	global BUILD_MEMBERS
	global highlightTool
	global ORDERS
	global ROWS
	global proxyManager
	global highlightTool
	
	#Clear order ROWS
	for row in ROWS:
		ORDERS_SIDE_GRID.removeRow(row)
	ROWS = []
	
	# Clear current inventory
	for item in INVENTORY:
		PROXY_NODES.remove(item.proxyNodes[0])
		PROXY_NODES.remove(item.proxyNodes[1])
		TARGET_NODES.remove(item.targetNodes[0])
		TARGET_NODES.remove(item.targetNodes[1])
		SENSOR_NODES.remove(item.sensorNodes[0])
		SENSOR_NODES.remove(item.sensorNodes[1])
		proxyManager.removeSensor(item.sensorNodes[0])
		proxyManager.removeSensor(item.sensorNodes[1])
		item.remove()
		del item
	INVENTORY = []
	
#	clearMembers()
	
	for i, order in enumerate(ORDERS):
		trussMember = createTruss(order,'resources/CHS.osgb')
		trussMember.order = order
		trussMember.setEuler([0,0,0])
		qty = int(trussMember.order.quantity)
		trussMember.setPosition([0,4,-6-i])
		
		PROXY_NODES.append(trussMember.proxyNodes[0])
		PROXY_NODES.append(trussMember.proxyNodes[1])
		TARGET_NODES.append(trussMember.targetNodes[0])
		TARGET_NODES.append(trussMember.targetNodes[1])
		SENSOR_NODES.append(trussMember.sensorNodes[0])
		SENSOR_NODES.append(trussMember.sensorNodes[1])
		
		proxyManager.addSensor(trussMember.sensorNodes[0])
		proxyManager.addSensor(trussMember.sensorNodes[1])

		if loading == True:
			BUILD_MEMBERS.append(trussMember)
		else:
			INVENTORY.append(trussMember)

	# Merge lists
	mergedList = BUILD_MEMBERS + INVENTORY
	for listItem in mergedList:
		listItem.texture(env)
		listItem.appearance(viz.ENVIRONMENT_MAP)
		listItem.apply(effect)
		listItem.apply(lightEffect)		
	
	try:
		highlightTool.setItems(mergedList)
	except:
		print 'Highlighter not initialized!'
	
	# Clear ORDERS
	ORDERS = []


def clearMembers():
	"""Delete truss members"""
	global highlightTool
	global PROXY_NODES
	global TARGET_NODES
	global SENSOR_NODES
	global INVENTORY
	global BUILD_MEMBERS
	global SIDE_CLONES
	global GRAB_LINKS
	
	try:
		highlightTool.removeItems(INVENTORY)
	except:
		pass
		
	proxyManager.clearTargets()
			
	for item in INVENTORY:
		item.remove()
		del item
	INVENTORY = []
	for node in PROXY_NODES:
		node.remove()
		del node
	PROXY_NODES = []
	for target in TARGET_NODES:
		target = None
		del target
	TARGET_NODES = []
	for sensor in SENSOR_NODES:
		proxyManager.removeSensor(sensor)
		del sensor
	SENSOR_NODES = []
	
	# Clear previous bridge
	for member in BUILD_MEMBERS:
		member.remove()
		member = None
	BUILD_MEMBERS = []
	
	# Clear side clones
	for clone in SIDE_CLONES:
		clone.remove()
		clone = None
	SIDE_CLONES = []
	
	# Clear grab links
	for link in GRAB_LINKS:
		link.remove()
		link = None
	GRAB_LINKS = []

	
def toggleEnvironment(value=viz.TOGGLE):
	environment_root.visible(value)

def toggleGrid(value=viz.TOGGLE):
	grid_root.visible(value)
			
def toggleUtility(sound=True):
	utilityCanvas.visible(viz.TOGGLE)
	menuCanvas.visible(viz.OFF)
	
	if sound:
		if utilityCanvas.getVisible == False:
			hideMenuSound.play()
		else:
			showMenuSound.play()


def clampTrackerScroll(tracker,min=0.2,max=20):
	tracker.distance = viz.clamp(tracker.distance,min,max)


def toggleMenuLink():
	global menuLink
	if menuLink:
		# If link exists, stop grabbing
		menuLink.remove()
		menuLink = None
	else:
		euler = gloveLink.getEuler()
		menuCanvas.setPosition(gloveLink.getPosition())
		menuCanvas.setEuler(0,0,0)
		menuLink = viz.grab( gloveLink, menuCanvas )
		menuCanvas.visible(True)
		
		
def toggleCollision(val=viz.TOGGLE):
	viz.collision(val)
	if val == 1:
		viz.phys.enable()
		print 'Physics: ON | Collision: ', val
		
	else:
		viz.phys.disable()
		print 'Physics: OFF | Collision: ', val


# Update code for highlight tool
isgrabbing = False
grabbedItem = None
highlightedItem = None
grabbedRotation = []
objToRotate = None
def updateHighlightTool(highlightTool):
	global grabbedItem
	global grabbedRotation
	global isgrabbing
	global GRAB_LINKS
	
	global proxyManager
	global PRE_SNAP_POS
	global PRE_SNAP_ROT
	global SNAP_TO_POS
	
	if SHOW_HIGHLIGHTER == True:
		highlightTool.highlight()
		
	if highlightTool.getSelection() is None:
		return	
		
	state = viz.mouse.getState()
	if state & viz.MOUSEBUTTON_LEFT:
		if isgrabbing == False:
			grabbedItem = highlightTool.getSelection()
			
			# Break grab links to free truss
#			for link in GRAB_LINKS:
#				link.remove()
#				link = None
			try:
				GRAB_LINKS.remove(grabbedItem.link)
				grabbedItem.link.remove()
				grabbedItem.link = None
			except:
				print 'No link'
				

			# Enable truss member target nodes
			proxyManager.addTarget(grabbedItem.targetNodes[0])
			proxyManager.addTarget(grabbedItem.targetNodes[1])
			
			# Disable truss member sensor nodes
			proxyManager.removeSensor(grabbedItem.sensorNodes[0])
			proxyManager.removeSensor(grabbedItem.sensorNodes[1])
			
			PRE_SNAP_POS = grabbedItem.getPosition()
			PRE_SNAP_ROT = grabbedItem.getEuler()
			grabbedRotation = PRE_SNAP_ROT
			SNAP_TO_POS = PRE_SNAP_POS
			
			isgrabbing = True
			
	global objToRotate
	if state & KEYS['rotate']:
		if objToRotate == None:
			objToRotate = highlightTool.getSelection()
		updateAngle(objToRotate,rotationSlider,rotationLabel)


# Register a callback function for the highlight event
def onHighlight(e):
	global isgrabbing
	global highlightedItem
	if e.new != None and e.new.length != None:
		inspectMember(e.new)
		highlightedItem = e.new
	else:
		inspectMember(None)
from tools import highlighter
viz.callback(highlighter.HIGHLIGHT_EVENT,onHighlight)


def onHighlightGrab():
	""" Clamp grabbed member to front glove position and grid z """
	global grabbedItem
	global isgrabbing
	global gloveLink	
	if grabbedItem != None and isgrabbing == True:
#		dir = gloveLink.getLineForward().getDir()
		
		xOffset = grabbedItem.getScale()[0] / 2
		clampedX =  viz.clamp( gloveLink.getPosition()[0], (BRIDGE_LENGTH * (-0.5)) + xOffset,(BRIDGE_LENGTH * 0.5) - xOffset )
		clampedY =  viz.clamp( gloveLink.getPosition()[1],2,10 )
#		pos = [ (BRIDGE_LENGTH)*(dir[0]*dir[2]), gloveLink.getPosition()[1], GRID_Z ]
		pos = [ gloveLink.getPosition()[0] , gloveLink.getPosition()[1] , GRID_Z ]

		grabbedItem.setPosition(pos)
vizact.ontimer(0,onHighlightGrab)


def onRelease(e=None):
	global INVENTORY
	global BUILD_MEMBERS
	global grabbedItem
	global highlightedItem
	global proxyManager
	global PRE_SNAP_POS
	global PRE_SNAP_ROT
	global SNAP_TO_POS
	global VALID_SNAP
	global bridge_root
	global GRAB_LINKS
	
	if VALID_SNAP:
		if grabbedItem.isNewMember == True:
			grabbedItem.orientation = ORIENTATION
			if ORIENTATION == Orientation.side:				
				cloneSide(grabbedItem)	
			grabbedItem.isNewMember = False
			
		# Check facing of truss
		xFacing = 1
		if grabbedItem.getPosition()[0] < SNAP_TO_POS[0]:
			xFacing = -1
		yFacing = 1
		if grabbedItem.getPosition()[1] < SNAP_TO_POS[1]:
			yFacing = -1
		
		# Check if vertical truss
		xOffset = mathlite.math.fabs(grabbedItem.proxyNodes[1].getPosition()[0] - grabbedItem.proxyNodes[0].getPosition()[0]) / 2
		yOffset = mathlite.math.fabs(grabbedItem.proxyNodes[1].getPosition()[1] - grabbedItem.proxyNodes[0].getPosition()[1]) / 2
		xOffset *= xFacing
		yOffset *= yFacing
		
		clampedX =  viz.clamp(grabbedItem.getPosition()[0],-10 + xOffset,10 - xOffset)
		clampedY =  viz.clamp(grabbedItem.getPosition()[1],2,10)
		grabbedItem.setPosition( [SNAP_TO_POS[0] + xOffset, SNAP_TO_POS[1] + yOffset, SNAP_TO_POS[2]] )
		grabbedItem.setEuler( [0,0,grabbedItem.getEuler()[2]] )
		
		# Enable sensor nodes for other members to snap to
		proxyManager.addSensor(grabbedItem.sensorNodes[0])
		proxyManager.addSensor(grabbedItem.sensorNodes[1])
		
		# Play snap sound
		clickSound.play()
	else:
		# If invalid position and newly-generated truss, destroy it
		if grabbedItem.isNewMember == True:
			BUILD_MEMBERS.remove(grabbedItem)
			proxyManager.removeTarget(grabbedItem.targetNodes[0])
			proxyManager.removeTarget(grabbedItem.targetNodes[1])
			grabbedItem.remove()
		else:	
			grabbedItem.setPosition(PRE_SNAP_POS)
			grabbedItem.setEuler(PRE_SNAP_ROT)
			# Enable sensor nodes for other members to snap to
			proxyManager.addSensor(grabbedItem.sensorNodes[0])
			proxyManager.addSensor(grabbedItem.sensorNodes[1])
		
		# Play warning sound
		warningSound.play()
			
	# Re-grab existing build members
#	for members in BUILD_MEMBERS:
#		link = viz.grab(bridge_root,members)
#		GRAB_LINKS.append(link)
	link = viz.grab(bridge_root,grabbedItem)
	GRAB_LINKS.append(link)
	grabbedItem.link = link
	
	# Disable truss member target nodes on release
	proxyManager.removeTarget(grabbedItem.targetNodes[0])
	proxyManager.removeTarget(grabbedItem.targetNodes[1])
	SNAP_TO_POS = []
	
	# Clear item references
	highlightedItem = None
	grabbedItem = None
	
	# Change mode back to build if not editing
	if MODE != Mode.edit:
		cycleMode(Mode.build)


def cloneSide(truss):
	pos = truss.getPosition()
	pos[2] *= -1
	clone = truss.clone()
	clone.setScale(truss.getScale())
	clone.setEuler(truss.getEuler())
	clone.setPosition(pos)
	viz.grab(truss,clone)
	SIDE_CLONES.append(clone)
	return clone

	
def updateQuantity(order,button,orderList,inventory,row):
	if order.quantity > 0:
		order.quantity -= 1
		button.message('{}mm(d) x {}mm(th) x {}m(l) [{}]'.format(order.diameter, order.thickness, order.length, order.quantity))
	if order.quantity <= 0:
		inventory.removeRow(row)
#		orderList.remove(order)
		

def updateAngle(obj,slider,label):
	if obj != None:
		rot = obj.getEuler()
		pos = mathlite.getNewRange(rot[2],90,-90,0,1)
		slider.set(pos)
		string = str(int(rot[2]))
		label.message(string)


def rotateTruss(obj,slider,label):	
	if objToRotate != None:
		# Clamp glove link z-orientation
		mouseTracker.visible(viz.OFF)
		mouseTracker.distance = 0.1
		slider.visible(True)
		pos = viz.Mouse.getPosition(viz.WINDOW_NORMALIZED)[0]
		slider.set(pos)
		rotateTo = mathlite.getNewRange(pos,0,1,90,-90)
		objToRotate.setEuler(0,0,int(rotateTo))
		rotation = int(objToRotate.getEuler()[2])
		string = str(rotation)
		rotationLabel.message(string)
	
	
def cycleOrientation(val):
	global ORIENTATION
	global grabbedItem
	
	if MODE == Mode.view or MODE == Mode.walk:
		return
	
	if grabbedItem != None:
		return
		
	pos = []
	rot = []
	
	ORIENTATION = val

	if val == Orientation.top:
		rot = TOP_VIEW_ROT
		pos = TOP_VIEW_POS
	elif val == Orientation.bottom:
		rot = BOT_VIEW_ROT
		pos = BOT_VIEW_POS
	else:
		rot = SIDE_VIEW_ROT
		pos = BRIDGE_ROOT_POS
		
	bridge_root.setEuler(rot)
	bridge_root.setPosition(pos)
vizact.onkeyup(KEYS['cycle'],cycleOrientation,vizact.choice([Orientation.top,Orientation.bottom,Orientation.side]))


def cycleMode(mode=Mode.add):
	global SHOW_HIGHLIGHTER
	global MODE
	
	MODE = mode
	
	toggleEnvironment(False)
	toggleGrid(True)
	proxyManager.setDebug(True)
	
	if MODE == Mode.build:
		SHOW_HIGHLIGHTER = True
		inventoryCanvas.visible(viz.ON)
		inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
		viewport.getNode3d().setPosition(START_POS)
	if MODE == Mode.edit:
		SHOW_HIGHLIGHTER = True
		inventoryCanvas.visible(viz.OFF)
		toggleGrid(True)
		toggleEnvironment(False)
		proxyManager.setDebug(True)
		viewport.getNode3d().setPosition(START_POS)
	if MODE == Mode.add:
		SHOW_HIGHLIGHTER = True
		inventoryCanvas.visible(viz.OFF)
		viewport.getNode3d().setPosition(START_POS)
	if MODE == Mode.view:
		SHOW_HIGHLIGHTER = False
		inventoryCanvas.visible(viz.OFF)
		toggleGrid(False)
		toggleEnvironment(True)
		proxyManager.setDebug(False)
		bridge_root.setPosition(BRIDGE_ROOT_POS)
		bridge_root.setEuler(SIDE_VIEW_ROT)
	if MODE == Mode.walk:
		SHOW_HIGHLIGHTER = False
		inventoryCanvas.visible(viz.OFF)
		toggleEnvironment(True)
		toggleGrid(False)
		proxyManager.setDebug(False)
		mouseTracker.distance = HAND_DISTANCE
		bridge_root.setPosition(BRIDGE_ROOT_POS)
		bridge_root.setEuler(SIDE_VIEW_ROT)
		viewport.getNode3d().setPosition(WALK_POS)
		viewport.getNode3d().setEuler(WALK_ROT)
	
	clickSound.play()
	print 'Mode cycle: ', MODE
vizact.onkeyup(KEYS['mode'],cycleMode,vizact.choice([Mode.edit,Mode.build]))		
	

# Setup Callbacks and Events
def onKeyUp(key):
	if key == '=':
		pass
	elif key == KEYS['home']:
		viewport.reset()
		viewport.getNode3d().setPosition(START_POS)
		viewport.getNode3d().setEuler(0,0,0)
		mouseTracker.distance = HAND_DISTANCE
		viewChangeSound.play()
	elif key == ',':
		print viz.MainView.getPosition()
	elif key == KEYS['env']:
		toggleEnvironment()
		clickSound.play()		
	elif key == KEYS['reset']:
		try:
			hmd.getSensor().reset(0)
		except:
			warningSound.play()
			print 'Reset orientation failed: Unable to get Oculus Rift sensor!'
		clickSound.play()
	elif key == KEYS['hand']:
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif key == KEYS['builder']:
		cycleMode(Mode.edit)
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif key == KEYS['viewer']:
		cycleMode(Mode.view)
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif key == KEYS['walk']:
		cycleMode(Mode.walk)
		clickSound.play()
	elif key == KEYS['grid']:
		toggleGrid(viz.TOGGLE)
		clickSound.play()
	elif key == KEYS['showMenu']:
		menuCanvas.visible(viz.TOGGLE)
		utilityCanvas.visible(viz.OFF)
		if menuCanvas.getVisible() == viz.ON or MODE == Mode.edit or MODE == Mode.view:
			inventoryCanvas.visible(viz.OFF)
		else:
			if MODE == Mode.build:
				inventoryCanvas.visible(viz.ON)
		showMenuSound.play()
	elif key == KEYS['proxi']:
		proxyManager.setDebug(viz.TOGGLE)
		clickSound.play()


def onKeyDown(key):
	if key == KEYS['snapMenu']:
#		toggleMenuLink()
		pass
		
		
def onMouseWheel(dir):
#	global ORIENTATION
#	global bridge_root
#	
#	if ORIENTATION == Orientation.top or ORIENTATION == Orientation.bottom:
#		pos = bridge_root.getPosition()
#		if dir > 0:
#			pos[2] += 0.5	
#		else:
#			pos[2] -= 0.5
#		bridge_root.setPosition(pos)
	pass
		

def slideRoot(val):
	global ORIENTATION
	global bridge_root
	
	if ORIENTATION == Orientation.top or ORIENTATION == Orientation.bottom:
		pos = bridge_root.getPosition()
		pos[2] += val
		bridge_root.setPosition(pos)
vizact.whilekeydown('1',slideRoot,-0.1)		
vizact.whilekeydown('2',slideRoot,0.1)		


def onMouseDown(button):
	global objToRotate
	global CACHED_GLOVE_Z
	if button == KEYS['rotate']:
		CACHED_GLOVE_Z = mouseTracker.distance
		if objToRotate != None:
			print 'Rotating', objToRotate.name, CACHED_GLOVE_Z
			rotationSlider.visible(True)


def onMouseUp(button):	
	global isgrabbing
	if button == KEYS['interact']:
		if isgrabbing == True:
			onRelease()
			isgrabbing = False
	
	global CACHED_GLOVE_Z
	global objToRotate
	if button == KEYS['rotate']:
		if objToRotate != None:
			objToRotate = None
			mouseTracker.visible(viz.ON)
			mouseTracker.distance = CACHED_GLOVE_Z
		rotationSlider.visible(False)
	
	if button == KEYS['utility']:
		toggleUtility()


def onSlider(obj,pos):
	global objToRotate
	if obj == rotationSlider:
		if objToRotate != None:
			rotateTo = mathlite.getNewRange(pos,0,1,90,-90)
			highlightedItem.setEuler(0,0,int(rotateTo))
			rotation = highlightedItem.getEuler()
			string = str(int(rotation[2]))
			rotationLabel.message(string)
	if obj == quantitySlider:
		quantitySlider.set(pos)
		displayedQty = int(mathlite.getNewRange(pos,0.0,1.0,QTY_MIN,QTY_MAX))
		quantitySlider.message(str(displayedQty))
		

def onList(e):
	if e.object == diameterDropList:
		thicknesses = []
		index = e.object.getSelection()
		for thickness in catalogue_root[int(index)]:
			thicknesses.append(thickness.text)
		thicknessDropList.clearItems()
		thicknessDropList.addItems(thicknesses)
		
	if e.object == tabbedPanel.tabGroup:
		if e.newSel == 0:
			ORIENTATION = Orientation.side
		if e.newSel == 1:
			ORIENTATION = Orientation.top
		if e.newSel == 2:
			ORIENTATION = Orientation.bottom
		
	clickSound.play()
	
		
import csv
# Saves current build members' truss dimensions, position, rotation to './data/bridge#.csv'
def SaveData():
	global BUILD_MEMBERS
		
	# Play sound
	clickSound.play()
	
	filePath = vizinput.fileSave(file='bridge01')		
	if filePath == '':
		return
		
	currentOrientation = ORIENTATION
	cycleOrientation(Orientation.side)
	
	with open(filePath,'wb') as f:
		writer = csv.writer(f)
		for truss in BUILD_MEMBERS:
			writer.writerow([str(truss.order.diameter),str(truss.order.thickness),str(truss.order.length),str(truss.order.quantity),
							str(truss.getPosition()[0]), str(truss.getPosition()[1]),str(truss.getPosition()[2]),
							str(truss.getEuler()[0]),str(truss.getEuler()[1]),str(truss.getEuler()[2]),
							int(truss.orientation.value)])
	
	# Save successful feedback
	FlashScreen()
	cycleOrientation(currentOrientation)
		
# Loads build members' truss dimensions, position, rotation from './data/bridge#.csv'					
def LoadData():
	global BUILD_MEMBERS
	global SIDE_CLONES
	global ORDERS
	global GRAB_LINKS
	
	# Play sound
	clickSound.play()
	
	filePath = vizinput.fileOpen(filter=[('CSV Files','*.csv')],directory='/data')		
	if filePath == '':
		return	

	clearMembers()
	
	currentOrientation = ORIENTATION
	cycleOrientation(Orientation.side)
	
	ORDERS = []
	with open(filePath,'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			 order = Order(diameter=float(row[0]),thickness=float(row[1]),length=float(row[2]),quantity=int(row[3]))
			 order.pos = ( [float(row[4]), float(row[5]), float(row[6])] )
			 order.euler = ( [float(row[7]), float(row[8]), float(row[9])] )
			 order.orientation = Orientation(int(row[10]))
			 ORDERS.append(order)
	
	generateMembers(loading=True)

	for truss in BUILD_MEMBERS:
		truss.isNewMember = False
		truss.setPosition(truss.order.pos)
		truss.setEuler(truss.order.euler)
		truss.orientation = truss.order.orientation
		if truss.orientation == Orientation.side:
			SIDE_CLONES.append(cloneSide(truss))
		link = viz.grab(bridge_root,truss)
		truss.link = link
		GRAB_LINKS.append(link)
	
	cycleOrientation(currentOrientation)

# Events
viz.callback ( viz.MOUSEUP_EVENT, onMouseUp )
viz.callback ( viz.MOUSEDOWN_EVENT, onMouseDown )
viz.callback ( viz.MOUSEWHEEL_EVENT, onMouseWheel )
viz.callback ( viz.SLIDER_EVENT, onSlider )
viz.callback ( viz.LIST_EVENT, onList )

# Button callbacks
vizact.onbuttonup ( orderSideButton, addOrder, ORDERS_SIDE_GRID, ORDERS_SIDE, ORDERS_SIDE_ROWS, ORDERS_SIDE_FLAG )
vizact.onbuttonup ( orderSideButton, clickSound.play )
vizact.onbuttonup ( orderTopButton, addOrder, ORDERS_TOP_GRID, ORDERS_TOP, ORDERS_TOP_ROWS, ORDERS_TOP_FLAG )
vizact.onbuttonup ( orderTopButton, clickSound.play )
vizact.onbuttonup ( orderBottomButton, addOrder, ORDERS_BOT_GRID, ORDERS_BOT, ORDERS_BOT_ROWS, ORDERS_BOT_FLAG )
vizact.onbuttonup ( orderBottomButton, clickSound.play )
vizact.onbuttonup ( doneButton, populateInventory, ORDERS_SIDE, ORDERS_TOP, ORDERS_BOT )
vizact.onbuttonup ( doneButton, clickSound.play )
vizact.onbuttonup ( resetButton, clearBridge )
vizact.onbuttonup ( resetButton, clickSound.play )
vizact.onbuttonup ( quitButton, quitGame )
vizact.onbuttonup ( quitButton, clickSound.play )
vizact.whilemousedown ( KEYS['rotate'], rotateTruss, objToRotate, rotationSlider, rotationLabel )

# Utility
vizact.onbuttonup ( menuButton, onKeyUp, KEYS['showMenu'], )
vizact.onbuttonup ( homeButton, onKeyUp, KEYS['home'] )
vizact.onbuttonup ( buildModeButton, onKeyUp, KEYS['builder'] )
vizact.onbuttonup ( viewerModeButton, onKeyUp, KEYS['viewer'] )
vizact.onbuttonup ( walkModeButton, onKeyUp, KEYS['walk'] )
vizact.onbuttonup ( resetOriButton, onKeyUp, KEYS['reset'] )
vizact.onbuttonup ( toggleEnvButton, onKeyUp, KEYS['env'] )
vizact.onbuttonup ( toggleGridButton, onKeyUp, KEYS['grid'] )
vizact.onbuttonup ( saveButton, SaveData )
vizact.onbuttonup ( loadButton, loadBridge )


FLASH_TIME = 3.0			# Time to flash screen

# Create flash screen quad
flash_quad = viz.addTexQuad(parent=viz.ORTHO)
flash_quad.color(viz.WHITE)
flash_quad.drawOrder(-10)
flash_quad.blendFunc(viz.GL_ONE,viz.GL_ONE)
flash_quad.visible(False)
flash_quad.setBoxTransform(viz.BOX_ENABLED)

def FlashScreen():
	"""Flash screen and fade out"""
	flash_quad.visible(True)
	flash_quad.color(viz.WHITE)
	fade_out = vizact.fadeTo(viz.BLACK,time=FLASH_TIME,interpolate=vizact.easeOutStrong)
	flash_quad.runAction(vizact.sequence(fade_out,vizact.method.visible(False)))

# Create post process effect for blending to gray scale
gray_effect = BlendEffect(None,GrayscaleEffect(),blend=0.0)
gray_effect.setEnabled(False)
vizfx.postprocess.addEffect(gray_effect)

# Schedule tasks
def MainTask():
	viewChangeSound.play()	
	
	while True:
		
		FlashScreen()
		
		yield viztask.waitButtonUp(doneButton)
		cameraRift = initCamera('vizconnect_config_riftDefault')
		#cameraFly = initCamera('vizconnect_config_riftFly')

		menuCanvas.visible(viz.OFF)
		menuCanvas.setPosition(0,-2,2)
		
		viz.clearcolor(CLEAR_COLOR)
		
		# Define globals
		global hmd
		global viewport
		global mouseTracker
		global gloveLink
		global highlightTool
		
		# Initialize remaining
		hmd = initOculus()
		viewport = initViewport(START_POS)
		highlightTool.setUpdateFunction(updateHighlightTool)
		mouseTracker = initTracker(HAND_DISTANCE)
		initMouse()
		gloveLink = initLink('glove.cfg',mouseTracker)
		viz.link(gloveLink,highlightTool)	
		
		vizact.ontimer(0,clampTrackerScroll,mouseTracker,SCROLL_MIN,SCROLL_MAX)
		
		# Setup callbacks
		viz.callback ( viz.KEYUP_EVENT, onKeyUp )
		viz.callback ( viz.KEYDOWN_EVENT, onKeyDown )
viztask.schedule( MainTask() )

# Pre-load sounds
viz.playSound('./resources/sounds/return_to_holodeck.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/button_highlight.wav',viz.SOUND_PRELOAD) 
viz.playSound('./resources/sounds/click.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/show_menu.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/hide_menu.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/page_advance.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/out_of_bounds_warning.wav',viz.SOUND_PRELOAD)
