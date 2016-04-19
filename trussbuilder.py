"""
[ Objective ]
Order truss members required to build a 20m-long bridge across the Singapore River, then proceed to build in VR

[ Controls ]
[ JOYBUTTON12 or ESC KEY ] Close Menu / Quit Application

[ Movement ]
[ VR HEADSET or Mouse] Look around
[ JOYSTICK or WASD ] Navigate
[ JOYBUTTON5 | JOYBUTTON3 or Z | X ] Lower/Raise elevation
[ JOYHATDOWN | JOYHATUP or 1 | 2 ] Slide bridge towards or away from you in TOP/BOTTOM ORIENTATION

[ Build ]
[ JOYBUTTON6 or TAB ] Cycle through Bridge Orientation
[ JOYBUTTON4 or SHIFT ] Cycle through Build Mode
[ JOYBUTTON2 or SPACE BAR ] Toggle Main Menu
[ JOYBUTTON11 or MIDDLE MOUSE ] Toggle Utilities Menu
[ VIRTUAL MOUSE ] Interact with menu elements
[ LEFT MOUSE ] Grab and hold onto highlighted truss members
[ RIGHT MOUSE ] Adjust highlighted truss' angle by holding and dragging
[ SCROLL WHEEL ] Extend and retract virtual hand
"""
INVENTORY_TEXT = """Order truss members from the catalogue & manage your inventory"""

FEEDBACK_MESSAGE = """<FEEDBACK>"""

VIEW_MESSAGE = """[ 1 | 2 ] Slide bridge towards or away from you"""

LOAD_MESSAGE = """Any unsaved progress will be lost! 
Are you sure you want to proceed?
(Please remove headset if proceeding)"""

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
import navigation
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
FOV = 45
START_FOV = 114
STENCIL = 8
STEREOMODE = viz.STEREO_HORZ
FULLSCREEN = 0
CLEAR_COLOR = viz.GRAY
GRID_COLOR = viz.BLACK
BUTTON_SCALE = 0.5
INITIALIZED = False
SOUNDS = []
SFX_VOLUME = 0.5
WARNING_VOLUME = 0.05
ISMUTED = False

BUILD_ROAM_LIMIT = ([12,-12,-10,10])	# Front,back,left,right limits in meters(m)
START_POS = ([0,5,-17])					# Set at 5m + avatar height above ground and 17m back fron center
BUILD_ROTATION = ([0,0,0])				# Zero-rotation to face dead center
WALK_POS = ([35,7,-13])
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
ORDERS_SIDE_FLAG = 'Side'
ORDERS_TOP_FLAG = 'Top'
ORDERS_BOT_FLAG = 'Bot'

INVENTORY = []					# Deprecated
BUILD_MEMBERS = []				# Array to store all truss members of bridge for saving/loading
SIDE_MEMBERS = []				# Array to store Side truss
SIDE_CLONES = []				# Array to store cloned Side truss
TOP_MEMBERS = []				# Array to store Top truss
BOT_MEMBERS = []				# Array to store Bottom truss
GRAB_LINKS = []					# Array to store grab links between bridge root and truss members

BRIDGE_LENGTH = 20				# Length of bridge in meters
BRIDGE_SPAN = 10				# Span of bridge in meters
GRID_Z = -5						# Grid z-position for Build members to snap to
BRIDGE_ROOT_POS = [0,5,0]		# Origin point of bridge group to position and rotate
TOP_VIEW_POS = [0,5,-4]			# Position of Top View Bridge Root
BOT_VIEW_POS = [0,5,-5]			# Position of bottom view bridge root
SIDE_VIEW_ROT = [0,0,0]			# Rotation of Side View
TOP_VIEW_ROT = [0,-90,0]		# Rotation of Top View
BOT_VIEW_ROT = [0,90,0]			# Rotation of Bottom View
TOP_CACHED_Z = -4				# Cache z-position of Top Bridge View
TOP_Z_MIN = -4					# Minimum z-position of Top Bridge Root
BOT_CACHED_Z = -5				# Cache z-position of Bot Bridge View
BOT_Z_MIN = -5					# Minimum z-position of Bottom Bridge Root
SLIDE_MAX = 100					# Max z-position of bridge root sliding
SLIDE_INTERVAL = 0.05			# Interval to slide bridge root in TOP/BOTTOM View
SUPPORT_ALPHA = 0.25			# Alpha value for bridge red supports	

class Orientation(Enum):
	Side=1
	Top=2
	Bottom=3
ORIENTATION = Orientation.Side


class Mode(Enum):
	Build=0
	Edit=1
	Add=2
	View=3
	Walk=4
MODE = Mode.View


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
		,'FORWARD'	: 'W'
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
		,'road'		: 'n'
		,'proxi'	: 'p'
		,'collide'	: 'c'
		,'walk'		: '/'
		,'esc'		: viz.KEY_ESCAPE
		,'viewMode' : 'm'
		,'capslock'	: viz.KEY_CAPS_LOCK
}

# Initialize scene
def initScene(res=RESOLUTION,quality=4,fov=FOV,stencil=8,stereoMode=viz.STEREO_HORZ,fullscreen=viz.FULLSCREEN,clearColor=viz.BLACK):
	viz.window.setSize(res)
	viz.setMultiSample(quality)
	viz.fov(fov)
	viz.setOption('viz.display.stencil', stencil)
	viz.setOption('viz.default_key.quit', 0)
	viz.setOption('viz.model.optimize', 1)
	viz.window.setName( 'Virtual Truss Bridge Builder & Visualizer' ) 
	viz.window.setBorder( viz.BORDER_FIXED )
	viz.clearcolor(clearColor)
	viz.go(stereoMode | fullscreen)
	darkTheme = themes.getDarkTheme()
	viz.setTheme(darkTheme)	
	
			
def initViewport(position):
	# Add a viewpoint so the user starts at the specified position
	vp = vizconnect.addViewpoint(pos=position,euler=(0,0,0))
	vp.add(vizconnect.getDisplay())
	print vp.getName()
	print vp.getNode3d().getPosition()
	#Start collision detection.
#	viz.MainView.collision( viz.ON )
#	viz.phys.enable()
	#Make gravity weaker.
#	viz.MainView.gravity(2)
	#Set the current position and orientation as point to reset to. 
	viz.cam.setReset() 
	viz.stepsize(0.5)
	

	return vp
	
	
# Disable mouse navigation and hide the mouse cursor
def initMouse():
	viz.mouse(viz.OFF)
	viz.mouse.setVisible(viz.OFF)
	viz.mouse.setTrap()
	viz.mouse.setOverride(viz.ON) 
	
	
def initLighting():
	# Disable the head lamps since we're doing lighting ourselves
	for window in viz.getWindowList():
		window.getView().getHeadLight().disable()
	# Create directional light
	sky_light = viz.addDirectionalLight(euler=(-66,37,0),color=[0.8,0.8,0.8])
#	light1 = vizfx.addDirectionalLight(euler=(40,20,0), color=[0.7,0.7,0.7])
#	light2 = vizfx.addDirectionalLight(euler=(-65,15,0), color=[0.5,0.25,0.0])
#	sky_light.color(viz.WHITE)
	# Adjust ambient color
	viz.setOption('viz.lightModel.ambient',[0]*3)
	sky_light.ambient([0.8]*3)
	vizfx.setAmbientColor([0.3,0.3,0.4])


# Highlighter	
def initHighlightTool():
	"""Initiailze highlighter tool"""
	from tools import highlighter
	return highlighter.Highlighter()
	
	
def initProxy():
	"""Initialize proximity manager and register callbacks"""
	# Create proximity manager
	proxyManager = vizproximity.Manager()
	proxyManager.setDebug(DEBUG_PROXIMITY)
	
	# Register callbacks for proximity SENSOR_NODES
	def enterProximity(e):
		global SNAP_TO_POS
		global VALID_SNAP
		global SENSOR_NODE
		SENSOR_NODE = e.sensor.getSource()
		SNAP_TO_POS = e.sensor.getSource().getPosition()
		VALID_SNAP = True
	
	def exitProximity(e):
		global VALID_SNAP
		global SENSOR_NODE
		VALID_SNAP = False
		SENSOR_NODE = None

	proxyManager.onEnter(None, enterProximity)
	proxyManager.onExit(None, exitProximity)
	
	return proxyManager
	
	
def initTracker(distance=0.5):
	"""Initialize scroll wheel tracker"""
	from vizconnect.util import virtual_trackers
	tracker = virtual_trackers.ScrollWheel(followMouse=True)
	tracker.distance = distance
	return tracker


def initLink(modelPath,tracker):
	"""Initialize hand link with tracker and link group with main view"""
	model = vizfx.addChild(modelPath)
	link = viz.link(tracker,model)
	link.postMultLinkable(viz.MainView)
	return link


def getCatalogue(path):
	"""Parse catalogue from data subdirectory"""
	return ET.parse(str(path)).getroot()

getCatalogue
# Initialize
initScene(RESOLUTION,MULTISAMPLING,FOV,STENCIL,viz.PROMPT,FULLSCREEN,(0.1, 0.1, 0.1, 1.0))
initMouse()
initLighting()
highlightTool = initHighlightTool()
proxyManager = initProxy()
catalogue_root = getCatalogue('data/catalogues/catalogue_CHS.xml')
environment_root = roots.EnvironmentRoot(visibility=False)
bridge_root = roots.BridgeRoot(BRIDGE_ROOT_POS,SIDE_VIEW_ROT)
grid_root = roots.GridRoot(gridColor=GRID_COLOR,origin=START_POS)
orientation_text = viz.addText3D('<< View >>',pos=[0,13.5,-5],scale=(2,2,.5),parent=grid_root,align=viz.ALIGN_CENTER)
info_text = viz.addText3D('<< Info >>',pos=[0,12,-5],scale=(.5,.5,.5),parent=grid_root,align=viz.ALIGN_CENTER)

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
	sound.volume(SFX_VOLUME)
warningSound.volume(WARNING_VOLUME)


def updateResolution(panel,canvas):
	bb = panel.getBoundingBox()
	canvas.setRenderWorldOverlay([bb.width + 5, bb.height + 5], fov=bb.height * 0.15, distance=3.0)	
	canvas.setCursorPosition([0,0])

def updateMouseStyle(canvas):
	canvas.setMouseStyle(viz.CANVAS_MOUSE_BUTTON)

# Add environment effects
env = viz.addEnvironmentMap('resources/textures/sky.jpg')
#effect = vizfx.addAmbientCubeEffect(env)
#vizfx.getComposer().addEffect(effect)
#lightEffect = vizfx.addLightingModel(diffuse=vizfx.DIFFUSE_LAMBERT,specular=None)
#vizfx.getComposer().addEffect(lightEffect)

def applyEnvironmentEffect(obj):
	obj.texture(env)
	obj.appearance(viz.ENVIRONMENT_MAP)
#	obj.apply(effect)
#	obj.apply(lightEffect)	


environment = viz.addChild('resources/environment.osgb',parent=environment_root)
walkway = viz.addChild('resources/walkway.osgb',parent=environment_root)
wave_M = viz.addChild('resources/wave2.osgb',cache=viz.CACHE_CLONE,pos=([0,0.75,0]),parent=environment_root)
wave_M.setAnimationSpeed(0.01)
wave_B = viz.addChild('resources/wave2.osgb',cache=viz.CACHE_CLONE,pos=([0,0.75,-50]),parent=environment_root)
wave_B.setAnimationSpeed(0.01)
road_M = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(0,5,0))
road_M.setParent(environment_root)
road_M.visible(False)
road_L1 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(-20,5,0))
road_L1.setParent(environment_root)
road_L2 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(-40,5,0))
road_L2.setParent(environment_root)
road_R1 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(20,5,0))
road_R1.setParent(environment_root)
road_R2 = viz.addChild('resources/road3.osgb',cache=viz.CACHE_CLONE,pos=(40,5,0))
road_R2.setParent(environment_root)
#clamp_L = viz.addChild('resources/clamp3.osgb',cache=viz.CACHE_CLONE,pos=(-21,-2.5,0),euler=(-90,0,0),scale=(0.25,0.5,0.5))
#clamp_L.setParent(environment_root)
#clamp_R = viz.addChild('resources/clamp3.osgb',cache=viz.CACHE_CLONE,pos=(21,-2.5,0),euler=(90,0,0),scale=(0.25,0.5,0.5))
#clamp_R.setParent(environment_root)
applyEnvironmentEffect(road_M)
applyEnvironmentEffect(road_L1)
applyEnvironmentEffect(road_L2)
applyEnvironmentEffect(road_R1)
applyEnvironmentEffect(road_R2)
applyEnvironmentEffect(wave_M)
applyEnvironmentEffect(wave_B)
day = viz.addChild('resources/sky_day.osgb', scale=([5,5,5]),parent=environment_root)
walkway.disable(viz.LIGHTING)

# Bridge pin and roller supports
pinSupport = viz.addChild('resources/pinSupport.osgb',pos=(-9.5,4,0),scale=[1,1,11])
rollerSupport = viz.addChild('resources/rollerSupport.osgb',pos=(9.5,4,0),scale=[1,1,11])
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
#	applyEnvironmentEffect(model)
	viz.grab(bridge_root,model)

# Create canvas for displaying GUI objects
instructionsPanel = vizinfo.InfoPanel(title=HEADER_TEXT,align=viz.ALIGN_CENTER_BASE,icon=False,key=None)
instructionsPanel.getTitleBar().fontSize(36)

# Initialize order panel containing mainRow and midRow
#inventoryPanel = vizdlg.Panel(layout=vizdlg.LAYOUT_VERT_CENTER,align=viz.ALIGN_CENTER,spacing=0,margin=(0,0))
inventoryPanel = vizinfo.InfoPanel(title=HEADER_TEXT,text=INVENTORY_TEXT,align=viz.ALIGN_CENTER_TOP,icon=False,key=None)
inventoryPanel.getTitleBar().fontSize(36)

# Initialize midRow
inventoryRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_TOP,border=False,background=False,margin=0)
#inventoryGrid = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_LEFT_TOP,border=False)

# Initialize orderPanel
orderPanel = vizinfo.InfoPanel('Fill in all required fields',icon=False,key=None)
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
# Initialize quantitySlider with default value of 1
quantitySlider = viz.addProgressBar('1')
qtyProgressPos = mathlite.getNewRange(1,QTY_MIN,QTY_MAX,0.0,1.0)
quantitySlider.set(qtyProgressPos)
quantity = orderPanel.addLabelItem('Quantity', quantitySlider)
# Initialize ordering buttons
orderSideButton = orderPanel.addItem(viz.addButtonLabel('Add to Side'),align=viz.ALIGN_RIGHT_BOTTOM)
orderTopButton = orderPanel.addItem(viz.addButtonLabel('Add to Top'),align=viz.ALIGN_RIGHT_BOTTOM)
orderBottomButton = orderPanel.addItem(viz.addButtonLabel('Add to Bottom'),align=viz.ALIGN_RIGHT_BOTTOM)

# Initialize Stock Main Panel
stockMainPanel = vizinfo.InfoPanel('Ordered truss members',icon=False,key=None)
stockMainPanel.setTitle( 'Stock' )
stockMainPanel.getTitleBar().fontSize(28)
stockMainPanel.addSeparator()
# Initialize Side order tab
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

inventoryRow.addItem(orderPanel)
inventoryRow.addItem(stockMainPanel)
#inventoryGrid.addRow([orderPanel,stockPanel])

bottomRow = vizdlg.Panel(border=False)
doneButton = bottomRow.addItem(viz.addButtonLabel('Confirm order and start building in VR'))
doneButton.length(2)

# Add rows to inventory main panel
inventoryPanel.addItem(inventoryRow)
inventoryPanel.addItem(bottomRow)

# TAB 3: Options panel
optionPanel = vizinfo.InfoPanel(title=HEADER_TEXT,text='Options',align=viz.ALIGN_CENTER_TOP,icon=False,key=None)
optionPanel.getTitleBar().fontSize(36)
optionPanel.addSection('File')
saveHeader = optionPanel.addItem(viz.addText('Append ".csv" when saving'))
saveButton = optionPanel.addItem(viz.addButtonLabel('Save Bridge'))
saveButton.length(2)
loadButton = optionPanel.addItem(viz.addButtonLabel('Load Bridge'))
loadButton.length(2)
optionPanel.addSection('Game')
soundButton = optionPanel.addItem(viz.addButtonLabel('Toggle Audio'))
soundButton.length(2)
resetButton = optionPanel.addItem(viz.addButtonLabel('Clear Bridge'))
resetButton.length(2)
quitButton = optionPanel.addItem(viz.addButtonLabel('Quit Application'))
quitButton.length(2)

# Create inspector panel
inspectorCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
inspector = panels.InspectorPanel()
statPanel = inspector.GetPanel()
statPanel.setParent(inspectorCanvas)
## Link inspector canvas with main View
#inspectorLink = viz.link(viz.MainView, inspectorCanvas)
##inspectorLink.preMultLinkable(viz.MainView)
#inspectorLink.preTrans( [-2, -3, 5] )
#inspectorLink.preEuler( [-45, 0, 0] )

utilityButtons = []
# Create docked utility panel
utilityCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
points = mathlite.getPointsInCircum(30,8)
# Menu button
menuButton = viz.addButton(parent=utilityCanvas)
menuButton.texture(viz.addTexture('resources/GUI/menu-128.png'))
#menuButton.setPosition(0,0)
menuButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Reset View button
homeButton = viz.addButton(parent=utilityCanvas)
homeButton.texture(viz.addTexture('resources/GUI/reset-128.png'))
#homeButton.setPosition(0,0)
homeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Build mode button
buildModeButton = viz.addButton(parent=utilityCanvas)
buildModeButton.texture(viz.addTexture('resources/GUI/wrench-128.png'))
#buildModeButton.setPosition(0,0)
buildModeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Viewer mode button
viewerModeButton = viz.addButton(parent=utilityCanvas)
viewerModeButton.texture(viz.addTexture('resources/GUI/viewer-128.png'))
#viewerModeButton.setPosition(0,0)
viewerModeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Walk mode button
walkModeButton = viz.addButton(parent=utilityCanvas)
walkModeButton.texture(viz.addTexture('resources/GUI/walking-128.png'))
#walkModeButton.setPosition(0,0)
walkModeButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Toggle environment button
toggleEnvButton = viz.addButton(parent=utilityCanvas)
toggleEnvButton.texture(viz.addTexture('resources/GUI/environment-128.png'))
#toggleEnvButton.setPosition(0,0)
toggleEnvButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Toggle grid button
toggleGridButton = viz.addButton(parent=utilityCanvas)
toggleGridButton.texture(viz.addTexture('resources/GUI/grid-64.png'))
#toggleGridButton.setPosition(0,0)
toggleGridButton.setScale(BUTTON_SCALE,BUTTON_SCALE)
# Reset orientation button
resetOriButton = viz.addButton(parent=utilityCanvas)
resetOriButton.texture(viz.addTexture('resources/GUI/compass-128.png'))
#resetOriButton.setPosition(0,0)
resetOriButton.setScale(BUTTON_SCALE,BUTTON_SCALE)

utilityButtons = ( [menuButton,homeButton,buildModeButton,viewerModeButton,walkModeButton,toggleEnvButton,toggleGridButton,resetOriButton] )
for i, button in enumerate(utilityButtons):
	button.setPosition(0.5 + points[i][0], 0.5 + points[i][1])
	
# Link utility canvas with main View
utilityLink = viz.link(viz.MainView,utilityCanvas)
#utilityLink.postMultLinkable(viz.MainView)
utilityLink.preTrans( [0, 0, 1.5] )

# Rotation Panel
rotationCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
rotationPanel = vizdlg.GridPanel(parent=rotationCanvas,align=viz.ALIGN_CENTER,border=False)
rotationSlider = viz.addProgressBar('Angle')
rotationLabel = viz.addText('0')
row = rotationPanel.addRow([rotationSlider,rotationLabel])
# Link rotation canvas with main View
#rotationLink = viz.link(viz.MainView,rotationCanvas)
#rotationLink.preEuler( [0,30,0] )
#rotationLink.preTrans( [0,0.1,1] )

# Add tabbed panels to main menu canvas
menuCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER_TOP)
menuTabPanel = vizdlg.TabPanel(align=viz.ALIGN_CENTER_TOP,parent=menuCanvas)
menuTabPanel.addPanel('Instructions',instructionsPanel)
menuTabPanel.addPanel('Inventory',inventoryPanel)
menuTabPanel.addPanel('Options',optionPanel)

# Add dialog canvas
dialogCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
dialog = vizdlg.MessageDialog(message='<Message>', title='Warning', accept='Yes (Enter)', cancel='No (Esc)',parent=dialogCanvas)
dialog.setScreenAlignment(viz.ALIGN_CENTER)
dialogCanvas.visible(viz.OFF)

# Add feedback canvas
feedbackCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
feedbackQuad = viz.addTexQuad(size=[500,100],parent=feedbackCanvas)
blackTex = viz.addTexture('resources/textures/blackTex.bmp',parent=feedbackQuad)
blackTex.wrap(viz.WRAP_S,viz.REPEAT) 
blackTex.wrap(viz.WRAP_T,viz.REPEAT)
feedbackText = viz.addText(FEEDBACK_MESSAGE,parent=feedbackQuad,align=viz.ALIGN_CENTER)
feedbackQuad.texture(blackTex)
feedbackQuad.alpha(0.5) 
feedbackText.color(viz.WHITE)
feedbackText.fontSize(50)
feedbackCanvas.visible(viz.OFF)

def initCanvas():	
	# Set canvas resolution to fit bounds of info panel
#	updateResolution(menuTabPanel,menuCanvas)
	bb = menuTabPanel.getBoundingBox()
	menuCanvas.setRenderWorldOverlay([bb.width + 5, bb.height + 100], fov=bb.height * 0.15, distance=3.0)	
	menuCanvas.setCursorPosition([0,0])
	menuCanvas.setPosition(0,0,8)
	menuCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
	
	updateResolution(dialog,dialogCanvas)
	dialogCanvas.setPosition(0,0,6)
	dialogCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
	
	updateResolution(feedbackQuad,feedbackCanvas)
	feedbackCanvas.setPosition(0,0,6)	
	
#	inspectorCanvas.setRenderWorld(RESOLUTION,[20,viz.AUTO_COMPUTE])
	inspectorCanvas.setRenderWorldOverlay(RESOLUTION,fov=90.0,distance=3.0)
	inspectorCanvas.setPosition(0,0,2)
	inspectorCanvas.setEuler(0,0,0)
	
	utilityCanvas.setRenderWorld(UTILITY_CANVAS_RES,[1,viz.AUTO_COMPUTE])
	utilityCanvas.setPosition(0,0,0)
	utilityCanvas.setEuler(0,0,0)
	utilityCanvas.setCursorPosition([0,0])
	utilityCanvas.visible(False)
	utilityCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
	
#	rotationCanvas.setRenderWorld(RESOLUTION,[1,viz.AUTO_COMPUTE])
#	rotationCanvas.setRenderWorldOverlay(MENU_RES,fov=90.0,distance=3.0)
	updateResolution(rotationPanel,rotationCanvas)
	rotationCanvas.setPosition(0,0,0)
	rotationCanvas.setEuler(0,0,0)
	rotationCanvas.visible(False)
initCanvas()

menuTabPanel.selectPanel(1)

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


def showFeedback():
	while True:
		feedbackCanvas.runAction(vizact.fadeTo(.5,begin=0,time=0.5))
		feedbackText.runAction(vizact.fadeTo(1,begin=0,time=0.5))
		yield viztask.waitTime(1)
		feedbackCanvas.runAction(vizact.fadeTo(0,begin=.5,time=0.25))
		feedbackText.runAction(vizact.fadeTo(0,begin=1,time=0.25))
		break


task = viztask.schedule( showFeedback() )
def runFeedbackTask(message='Welcome'):
	global task
	task.kill()
	
	feedbackCanvas.alpha(0)
	feedbackText.alpha(0)
	feedbackText.message(message)
	feedbackCanvas.visible(viz.ON)
	task = viztask.schedule( showFeedback() )
	

def showdialog(message,func):
	menuCanvas.setMouseStyle(viz.CANVAS_MOUSE_VISIBLE)
	inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VISIBLE)
	
	# Re-adjust resolution	
	dialog = vizdlg.MessageDialog(message=message, title='Warning', accept='Yes (Enter)', cancel='No (Esc)',parent=dialogCanvas)
	dialog.setScreenAlignment(viz.ALIGN_CENTER)
	
	bb = dialog.getBoundingBox()
	dialogCanvas.setRenderWorldOverlay([bb.width + 5, bb.height + 5], fov=bb.height * 0.15, distance=3.0)	
	dialogCanvas.visible(viz.ON)
	
	warningSound.play()
	
	while True:
		yield dialog.show()
		if dialog.accepted:
			func()
		else:
			pass
		dialog.remove()
		dialogCanvas.visible(viz.OFF)
		
		menuCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
		if MODE is Mode.Build:
			inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
		
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
	try:
		_length = viz.clamp(float(lengthTextbox.get()),LEN_MIN,LEN_MAX)
		_length = round(_length,2)
	except:
		runFeedbackTask('Invalid length!')
		warningSound.play()
		lengthTextbox.message('')
		return
	_quantity = mathlite.getNewRange(quantitySlider.get(),0.0,1.0,QTY_MIN,QTY_MAX)
	
	setattr(newOrder, 'diameter', float(_diameter))
	setattr(newOrder, 'thickness', float(_thickness))
	setattr(newOrder, 'length', float(_length))
	setattr(newOrder, 'quantity', int(_quantity))

	global ORDERS_SIDE
	global ORDERS_TOP
	global ORDERS_BOT

	if flag == ORDERS_SIDE_FLAG:
		orderList = inventory.OrderList(ORDERS_SIDE)
	elif flag == ORDERS_TOP_FLAG:
		orderList = inventory.OrderList(ORDERS_TOP)
	elif flag == ORDERS_BOT_FLAG:
		orderList = inventory.OrderList(ORDERS_BOT)
		
	print 'addOrder: orderList:', orderList
	
	
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

	# Change global list based on order flag
	if flag == ORDERS_SIDE_FLAG:
		ORDERS_SIDE = orderList
	elif flag == ORDERS_TOP_FLAG:
		ORDERS_TOP = orderList
	elif flag == ORDERS_BOT_FLAG:
		ORDERS_BOT = orderList
	
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


#TODO Fix
def deleteOrder(order, orderList, index, row, orderRow, orderTab, flag ):	
	orderList.pop(index)		
	orderTab.removeRow(row)
	orderRow.remove(row)	
	
	
def createInventory():
#	Create inventory panel
	global inventoryCanvas
	inventoryCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER_TOP)
	inventoryGrid = vizdlg.GridPanel(align=viz.ALIGN_CENTER_TOP,cellAlign=vizdlg.LAYOUT_HORZ_TOP,parent=inventoryCanvas,border=False,background=False)
	
	global tabbedPanel
	tabbedPanel = vizdlg.TabPanel(align=viz.ALIGN_CENTER_TOP,layout=vizdlg.LAYOUT_VERT_LEFT,parent=inventoryCanvas,border=False)

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

	inventoryGrid.addRow([statPanel])
	inventoryGrid.addRow([tabbedPanel])

	inventoryCanvas.setRenderWorld(RESOLUTION,[1,viz.AUTO_COMPUTE])
	inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
	# Link rotation canvas with main View
#	inventoryLink = viz.link(viz.MainView,inventoryCanvas)

#	inventoryLink.preEuler( [0,30,0] )
#	inventoryLink.preTrans( [0,0,1] )
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
	

def populateInventory():
	clearInventory()
	
	# Generate truss buttons based on respective lists
	global ORDERS_SIDE
	for sideOrder in ORDERS_SIDE:
		msg = '{}mm(d) x {}mm(th) x {}m(l) [{}]'.format ( sideOrder.diameter, sideOrder.thickness, sideOrder.length, sideOrder.quantity )
		sideButton = viz.addButtonLabel ( msg )
		vizact.onbuttonup ( sideButton, createTrussNew, sideOrder, 'resources/chs.osgb' )
		row = sideInventory.addRow ( [sideButton] )
		sideRows.append ( row )
		vizact.onbuttonup ( sideButton, updateQuantity, sideOrder, sideButton, ORDERS_SIDE, sideInventory, row )
		vizact.onbuttonup ( sideButton, clickSound.play )
	global ORDERS_TOP
	for topOrder in ORDERS_TOP:
		msg = '{}mm(d) x {}mm(th) x {}m(l) [{}]'.format ( topOrder.diameter, topOrder.thickness, topOrder.length, topOrder.quantity )
		topButton = viz.addButtonLabel ( msg )
		vizact.onbuttonup ( topButton, createTrussNew, topOrder, 'resources/chs.osgb' )
		row = topInventory.addRow( [topButton] )
		topRows.append ( row )
		vizact.onbuttonup ( topButton, updateQuantity, topOrder, topButton, ORDERS_TOP, topInventory, row )
		vizact.onbuttonup ( topButton, clickSound.play )
	global ORDERS_BOT
	for botOrder in ORDERS_BOT:
		msg = '{}mm(d) x {}mm(th) x {}m(l) [{}]'.format ( botOrder.diameter, botOrder.thickness, botOrder.length, botOrder.quantity )
		botButton = viz.addButtonLabel ( msg )
		vizact.onbuttonup ( botButton, createTrussNew, botOrder, 'resources/chs.osgb' )
		row = bottomInventory.addRow ( [botButton] )
		bottomRows.append ( row )
		vizact.onbuttonup ( botButton, updateQuantity, botOrder, botButton, ORDERS_BOT, bottomInventory, row )
		vizact.onbuttonup ( botButton, clickSound.play )
		
	# Clear order panel rows
	for topRow in ORDERS_TOP_ROWS:
		ORDERS_TOP_GRID.removeRow(topRow)
	for sideRow in ORDERS_SIDE_ROWS:
		ORDERS_SIDE_GRID.removeRow(sideRow)
	for botRow in ORDERS_BOT_ROWS:
		ORDERS_BOT_GRID.removeRow(botRow)
	
	# Clear orders from order list
	for order in ORDERS_SIDE:
		ORDERS_SIDE.pop()
	ORDERS_SIDE = []
	for order in ORDERS_TOP:
		ORDERS_TOP.pop()
	ORDERS_TOP = []
	for order in ORDERS_BOT:
		ORDERS_BOT.pop()
	ORDERS_BOT = []
	
	# Show menu
	inventoryCanvas.visible(False)


def createTruss(order=Order(),path=''):
	truss = viz.addChild(path,cache=viz.CACHE_COPY)
	truss.order = order
	truss.diameter = float(order.diameter)
	truss.thickness = float(order.thickness)
	truss.length = float(order.length)
	truss.quantity = int(order.quantity)
	
	truss.setScale([truss.length,truss.diameter*0.001,truss.diameter*0.001])	

	posA = truss.getPosition()
	posA[0] -= truss.length * 0.5
	nodeA = vizshape.addSphere(0.2,pos=posA)
	nodeA.disable(viz.PICKING)
	nodeA.visible(False)
	viz.grab(truss,nodeA)
	
	posB = truss.getPosition()
	posB[0] += truss.length * 0.5
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
	
	truss.setScale([truss.length,truss.diameter*0.001,truss.diameter*0.001])	

	# Setup proximity-based snapping nodes
	posA = truss.getPosition()
	posA[0] -= truss.length * 0.5
	nodeA = vizshape.addSphere(0.2,pos=posA)
	nodeA.visible(False)
	viz.grab(truss,nodeA)
	
	posB = truss.getPosition()
	posB[0] += truss.length * 0.5
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
	applyEnvironmentEffect(truss)
	
	try:
		# Clear highlighter
		highlightTool.clear()
		currentTruss = [truss]
		highlightTool.setItems(currentTruss)
	except:
		print 'Failed: Highlighter not initialized!'
	
	if not loading:
		global grabbedItem
		global highlightedItem
		global isgrabbing
		
		grabbedItem = truss		
		highlightedItem = truss
		isgrabbing = True
		
		truss.isNewMember = True		
		cycleMode(Mode.Add)
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
		trussMember = createTruss(order,'resources/chs.osgb')
		trussMember.order = order
		
		PROXY_NODES.append(trussMember.proxyNodes[0])
		PROXY_NODES.append(trussMember.proxyNodes[1])
		TARGET_NODES.append(trussMember.targetNodes[0])
		TARGET_NODES.append(trussMember.targetNodes[1])
		SENSOR_NODES.append(trussMember.sensorNodes[0])
		SENSOR_NODES.append(trussMember.sensorNodes[1])
		
		proxyManager.addSensor(trussMember.sensorNodes[0])
		proxyManager.addSensor(trussMember.sensorNodes[1])

		BUILD_MEMBERS.append(trussMember)
		applyEnvironmentEffect(trussMember)

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
	global SIDE_MEMBERS
	global TOP_MEMBERS
	global BOT_MEMBERS
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
	for clone in SIDE_CLONES:
		clone.remove()
		clone = None
	SIDE_CLONES = []
	for member in SIDE_MEMBERS:
		member.remove()
		member = None
	SIDE_MEMBERS = []
	for member in TOP_MEMBERS:
		member.remove()
		member = None
	TOP_MEMBERS = []
	for member in BOT_MEMBERS:
		member.remove()
		member = None
	BOT_MEMBERS = []
	
	# Clear grab links
	for link in GRAB_LINKS:
		link.remove()
		link = None
	GRAB_LINKS = []
	
	# Show feedback
	runFeedbackTask('Bridge cleared!')
	hideMenuSound.play()

def toggleAudio(value=viz.TOGGLE):
	global ISMUTED
	if ISMUTED:
		for sound in SOUNDS:
			sound.volume(SFX_VOLUME)
		warningSound.volume(WARNING_VOLUME)
		runFeedbackTask('Sound ON')
	else:
		for sound in SOUNDS:
			sound.volume(0)
		runFeedbackTask('Sound OFF')

	ISMUTED = not ISMUTED
	clickSound.play()
	
	
def toggleEnvironment(value=viz.TOGGLE):
	environment_root.visible(value)
	
	# Show feedback
	if environment_root.getVisible() is True:
		runFeedbackTask('Environment ON')
		clickSound.play()
	else:
		runFeedbackTask('Environment OFF')
		hideMenuSound.play()

def toggleGrid(value=viz.TOGGLE):
	grid_root.visible(value)
	
	# Show feedback

	if grid_root.getVisible() is True:
		runFeedbackTask('Grid On')
		clickSound.play()
	else:
		runFeedbackTask('Grid Off')
		hideMenuSound.play()
			
def toggleUtility(val=viz.TOGGLE):
	utilityCanvas.visible(val)
	menuCanvas.visible(False)

	if utilityCanvas.getVisible() is True:
		inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VISIBLE)
		showMenuSound.play()
	else:
		updateMouseStyle(inventoryCanvas)
		hideMenuSound.play()


def clampTrackerScroll(tracker,min=0.2,max=20):
	tracker.distance = viz.clamp(tracker.distance,min,max)


def toggleMenu(val=viz.TOGGLE):
	menuCanvas.visible(val)
	utilityCanvas.visible(False)
	if menuCanvas.getVisible() is True or MODE is Mode.Edit or MODE is Mode.View:
		inventoryCanvas.visible(False)
		runFeedbackTask('Menu')
		showMenuSound.play()
	else:
		hideMenuSound.play()
		if MODE == Mode.Build:
			inventoryCanvas.visible(True)


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

def updateScreenText():
    object = viz.MainWindow.pick(info=True)
    if object.valid:
        name = object.name
        if name.startswith('painting_'):
            name = name.replace('painting_','')
            textScreen.message(name)
        else:
            textScreen.message('')
#vizact.ontimer(0.1,updateScreenText)

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
	else:
#		highlightTool.clear()
#		highlightTool.setItems([])
		return
		
	if highlightTool.getSelection() is None:
		return	
		
	state = viz.mouse.getState()
	if state & viz.MOUSEBUTTON_LEFT:
		if isgrabbing == False:
			# Prevent grabbing truss of other orientation groups
			if highlightTool.getSelection().orientation != ORIENTATION:
				return

			grabbedItem = highlightTool.getSelection()
				
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
#vizact.ontimer(0,onHighlightGrab)

def onHighlightGrab2():
	""" Clamp grabbed member to front glove position and grid z """
	global grabbedItem
	global isgrabbing
	if grabbedItem != None and isgrabbing == True:		
		startPos = highlightTool.getRayCaster().getPosition()
		dist = mathlite.math.fabs(startPos[2] - GRID_Z)
		raycaster = highlightTool.getRayCaster().getLineForward()
		newPos = raycaster.endFromDistance(dist)
		newPos[2] = GRID_Z
#		print newPos
#		print startPos
#		pos[0] += -dir[0]*GRID_Z
#		pos[1] += -dir[1]*GRID_Z
#		pos[2] = GRID_Z
#		newPos = pos + (dir * dist)
		grabbedItem.setPosition(newPos)
vizact.ontimer(0,onHighlightGrab2)


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
	global SHOW_HIGHLIGHTER
	global highlightTool
		
	if VALID_SNAP:
		# If new member, group appropriately
		if grabbedItem.isNewMember == True:
			grabbedItem.orientation = ORIENTATION
			if ORIENTATION == Orientation.Side:		
				SIDE_MEMBERS.append(grabbedItem)
				cloneSide(grabbedItem)
			elif ORIENTATION == Orientation.Top:
				TOP_MEMBERS.append(grabbedItem)
			elif ORIENTATION == Orientation.Bottom:
				BOT_MEMBERS.append(grabbedItem)
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
		xOffset *= xFacing
		yOffset = mathlite.math.fabs(grabbedItem.proxyNodes[1].getPosition()[1] - grabbedItem.proxyNodes[0].getPosition()[1]) / 2
		yOffset *= yFacing

		clampedX =  viz.clamp(grabbedItem.getPosition()[0],-10 + xOffset,10 - xOffset)
		clampedY =  viz.clamp(grabbedItem.getPosition()[1],2,10)
		grabbedItem.setPosition( [SNAP_TO_POS[0] + xOffset, SNAP_TO_POS[1] + yOffset, SENSOR_NODE.getPosition()[2]] )
		grabbedItem.setEuler( [0,0,grabbedItem.getEuler()[2]] )
		
		# Enable sensor nodes for other members to snap to
		proxyManager.addSensor(grabbedItem.sensorNodes[0])
		proxyManager.addSensor(grabbedItem.sensorNodes[1])
		
		# Play snap MUTE
		clickSound.play()
	else:
		# If invalid position and newly-generated truss, destroy it
		if grabbedItem.isNewMember == True:
			highlightTool.clear()
			BUILD_MEMBERS.remove(grabbedItem)
			proxyManager.removeTarget(grabbedItem.targetNodes[0])
			proxyManager.removeTarget(grabbedItem.targetNodes[1])
#			grabbedItem.setPosition(0,10,-5)
			grabbedItem.remove()
			highlightedItem = None
			grabbedItem = None
		else:	
			grabbedItem.setPosition(PRE_SNAP_POS)
			grabbedItem.setEuler(PRE_SNAP_ROT)
			# Enable sensor nodes for other members to snap to
			proxyManager.addSensor(grabbedItem.sensorNodes[0])
			proxyManager.addSensor(grabbedItem.sensorNodes[1])
		
		# Play warning MUTE
		warningSound.play()
			
	# Re-grab existing Build members
#	for members in BUILD_MEMBERS:
#		link = viz.grab(bridge_root,members)
#		GRAB_LINKS.append(link)
	if grabbedItem != None:
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
	
	# Change mode back to Build if not editing
	if MODE != Mode.Edit:
		cycleMode(Mode.Build)


def cloneSide(truss):
	pos = truss.getPosition()
	pos[2] *= -1
	clone = truss.clone()
	clone.setScale(truss.getScale())
	clone.setEuler(truss.getEuler())
	clone.setPosition(pos)
	viz.grab(truss,clone)
	SIDE_CLONES.append(clone)
	clone.visible(False)
	return clone

def toggleRoad(road):
	if len(BOT_MEMBERS) is not 0:
		message = ''
		if road_M.getVisible() is True:
			message = 'Road exists'
		else:
			message = 'Added road!'
			road.visible(True)
		runFeedbackTask(message)
	else:
		runFeedbackTask('No bottom support!')
		road.visible(False)
	
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
		rotationCanvas.visible(viz.ON)
		mouseTracker.visible(viz.OFF)
		mouseTracker.distance = 0.1
		pos = viz.Mouse.getPosition(viz.WINDOW_NORMALIZED)[0]
		slider.set(pos)
		rotateTo = mathlite.getNewRange(pos,0,1,90,-90)
		objToRotate.setEuler(0,0,int(rotateTo))
		rotation = int(objToRotate.getEuler()[2])
		string = str(rotation)
		rotationLabel.message(string)

def resetSensors():
	proxyManager.clearSensors()
	proxyManager.addSensor(pinAnchorSensor)
	proxyManager.addSensor(rollerAnchorSensor)
	
def cycleOrientation(val):
	global ORIENTATION
	global grabbedItem
	
	if MODE == Mode.View or MODE == Mode.Walk:
		return
	
	if grabbedItem != None:
		return
		
	pos = []
	rot = []

	resetSensors()
	
	for member in SIDE_CLONES:
		member.visible(viz.OFF)
	for model in supports:
		model.alpha(SUPPORT_ALPHA)	
		
	ORIENTATION = val
	if val == Orientation.Top:
		rot = TOP_VIEW_ROT
		pos = TOP_VIEW_POS
		pos[2] = TOP_CACHED_Z
		
		for member in SIDE_MEMBERS:
			member.visible(viz.OFF)
			proxyManager.addSensor(member.sensorNodes[0])
			proxyManager.addSensor(member.sensorNodes[1])
		for member in BOT_MEMBERS:
			member.visible(viz.OFF)
			proxyManager.removeSensor(member.sensorNodes[0])
			proxyManager.removeSensor(member.sensorNodes[1])
		for member in TOP_MEMBERS:
			member.visible(viz.ON)	
			proxyManager.addSensor(member.sensorNodes[0])
			proxyManager.addSensor(member.sensorNodes[1])
			
		info_text.message(VIEW_MESSAGE)
	elif val == Orientation.Bottom:
		rot = BOT_VIEW_ROT
		pos = BOT_VIEW_POS
		pos[2] = BOT_CACHED_Z
		
		for member in SIDE_MEMBERS:
			member.visible(viz.OFF)
			proxyManager.addSensor(member.sensorNodes[0])
			proxyManager.addSensor(member.sensorNodes[1])
		for member in TOP_MEMBERS:
			member.visible(viz.OFF)
			proxyManager.removeSensor(member.sensorNodes[0])
			proxyManager.removeSensor(member.sensorNodes[1])
		for member in BOT_MEMBERS:
			member.visible(viz.ON)
			proxyManager.addSensor(member.sensorNodes[0])
			proxyManager.addSensor(member.sensorNodes[1])
			
		info_text.message(VIEW_MESSAGE)
	else:
		rot = SIDE_VIEW_ROT
		pos = BRIDGE_ROOT_POS
		
		for member in SIDE_MEMBERS:
			member.visible(viz.ON)
			proxyManager.addSensor(member.sensorNodes[0])
			proxyManager.addSensor(member.sensorNodes[1])
		for member in TOP_MEMBERS:
			member.visible(viz.OFF)
			proxyManager.removeSensor(member.sensorNodes[0])
			proxyManager.removeSensor(member.sensorNodes[1])
		for member in BOT_MEMBERS:
			member.visible(viz.OFF)
			proxyManager.removeSensor(member.sensorNodes[0])
			proxyManager.removeSensor(member.sensorNodes[1])
		info_text.message('')		
	bridge_root.setEuler(rot)
	bridge_root.setPosition(pos)
	
	# Show feedback
	runFeedbackTask(str(ORIENTATION.name))
	orientation_text.message(str(ORIENTATION.name))
	hideMenuSound.play()

def cycleMode(mode=Mode.Add):
	global SHOW_HIGHLIGHTER
	global MODE
	global highlightTool
	global highlightedItem
	
	if MODE is Mode.Add and grabbedItem is not None:
		return		
	
	if MODE is Mode.Edit and grabbedItem is not None:
		return
		
	MODE = mode
	
	toggleEnvironment(False)
	toggleGrid(True)
	proxyManager.setDebug(True)
	inventoryCanvas.visible(viz.ON)
	
	if MODE == Mode.Build:
		inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VIRTUAL)
#		viewport.getNode3d().setPosition(START_POS)
#		hmd.setPosition(START_POS)
		navigator.setPosition(START_POS)
		
		# Clear highlighter
		SHOW_HIGHLIGHTER = False
		highlightedItem = None
		highlightTool.clear()
		highlightTool.removeItems(BUILD_MEMBERS)
		highlightTool.setItems([])
		
		cycleOrientation(ORIENTATION)
	if MODE == Mode.Edit:
		inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VISIBLE)
#		viewport.getNode3d().setPosition(START_POS)
#		hmd.setPosition(START_POS)
		navigator.setPosition(START_POS)
		
		# Clear highlighter
		SHOW_HIGHLIGHTER = True

		highlightTool.clear()
		highlightTool.removeItems(BUILD_MEMBERS)
		highlightTool.setItems([])
		
		highlightTool.setItems(BUILD_MEMBERS)
		
		cycleOrientation(ORIENTATION)
	if MODE == Mode.Add:
		inventoryCanvas.setMouseStyle(viz.CANVAS_MOUSE_VISIBLE)
#		viewport.getNode3d().setPosition(START_POS)
		hmd.setPosition(START_POS)	
		
		# Show highlighter
		SHOW_HIGHLIGHTER = True
	if MODE == Mode.View:
		inventoryCanvas.visible(viz.OFF)
		toggleGrid(False)
		toggleEnvironment(True)
		proxyManager.setDebug(False)
		bridge_root.setPosition(BRIDGE_ROOT_POS)
		bridge_root.setEuler(SIDE_VIEW_ROT)
		
		# Show all truss members
		for member in SIDE_CLONES:
			member.visible(viz.ON)
		for member in SIDE_MEMBERS:
			member.visible(viz.ON)
		for member in TOP_MEMBERS:
			member.visible(viz.ON)
		for member in BOT_MEMBERS:
			member.visible(viz.ON)
		
		# Clear highlighter
		SHOW_HIGHLIGHTER = False
		highlightedItem = None
		highlightTool.clear()
		highlightTool.removeItems(BUILD_MEMBERS)
		highlightTool.setItems([])
		
		# Hide supports
		for model in supports:
			model.alpha(0)
	if MODE == Mode.Walk:
		inventoryCanvas.visible(viz.OFF)
		toggleEnvironment(True)
		toggleGrid(False)
		proxyManager.setDebug(False)
		mouseTracker.distance = HAND_DISTANCE
		bridge_root.setPosition(BRIDGE_ROOT_POS)
		bridge_root.setEuler(SIDE_VIEW_ROT)
#		viewport.getNode3d().setPosition(WALK_POS)
#		viewport.getNode3d().setEuler(WALK_ROT)
#		hmd.setPosition(WALK_POS)
#		hmd.setEuler(WALK_ROT)
		navigator.setPosition(WALK_POS)
		navigator.setPosition(WALK_ROT)
		
		# Show all truss members
		for member in SIDE_CLONES:
			member.visible(viz.ON)
		for member in SIDE_MEMBERS:
			member.visible(viz.ON)
		for member in TOP_MEMBERS:
			member.visible(viz.ON)
		for member in BOT_MEMBERS:
			member.visible(viz.ON)
	
		# Clear highlighter
		SHOW_HIGHLIGHTER = False
		highlightedItem = None
		highlightTool.clear()
		highlightTool.removeItems(BUILD_MEMBERS)
		highlightTool.setItems([])
		
		# Hide supports
		for model in supports:
			model.alpha(0)
	
	# UI/Sound feedback
	runFeedbackTask(str(MODE.name))
	hideMenuSound.play()
	

# Setup Callbacks and Events
def onKeyUp(key):
	if key == KEYS['esc']:
		if utilityCanvas.getVisible() is True:
			toggleUtility(False)
		elif menuCanvas.getVisible() is True:
			toggleMenu(False)
		else:
			quitGame()
	elif key == KEYS['home']:
#		viewport.reset()
#		hmd.reset()
		navigator.reset()
		mouseTracker.distance = HAND_DISTANCE
		runFeedbackTask('View reset!')
		viewChangeSound.play()
	elif key == ',':
#		print viz.MainView.getPosition()
		print navigator.getPosition()
	elif key == KEYS['env'] or key == KEYS['env'].upper():
		toggleEnvironment()	
	elif key == KEYS['reset'] or key == KEYS['reset'].upper():
		try:
#			hmd.getSensor().reset(0)
			runFeedbackTask('Orientation reset!')
			clickSound.play()
		except:
			runFeedbackTask('No headset!')
			warningSound.play()
			print 'Reset orientation failed: Unable to get Oculus Rift sensor!'
	elif key == KEYS['hand'] or key == KEYS['hand'].upper():
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif key == KEYS['builder'] or key == KEYS['builder'].upper():
		cycleMode(Mode.Edit)
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif key == KEYS['viewer'] or key == KEYS['viewer'].upper():
		cycleMode(Mode.View)
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif key == KEYS['walk'] or key == KEYS['walk'].upper():
		cycleMode(Mode.Walk)
		clickSound.play()
	elif key == KEYS['grid'] or key == KEYS['grid'].upper():
		toggleGrid(viz.TOGGLE)
	elif key == KEYS['showMenu']:
		toggleMenu()
	elif key == KEYS['road']:
		toggleRoad(road_M)
		clickSound.play()
	elif key == KEYS['proxi'] or key == KEYS['proxi'].upper():
		proxyManager.setDebug(viz.TOGGLE)
		clickSound.play()
	elif key == KEYS['capslock']:
		runFeedbackTask('Caps Lock')
		warningSound.play()


def onKeyDown(key):
	if key == KEYS['snapMenu']:
#		toggleMenuLink()
		pass

def onJoyButton(e):
	KEYS = navigator.KEYS
	
	if e.button == KEYS['esc']:
		if utilityCanvas.getVisible() is True:
			toggleUtility(False)
		elif menuCanvas.getVisible() is True:
			toggleMenu(False)
		else:
			quitGame()
	elif e.button == ',':
		print navigator.getPosition()
	elif e.button == KEYS['env']:
		toggleEnvironment()	
	elif e.button == KEYS['reset']:
		navigator.reset()
		mouseTracker.distance = HAND_DISTANCE
		runFeedbackTask('View reset!')
		viewChangeSound.play()
	elif e.button == KEYS['hand']:
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif e.button == KEYS['builder']:
		cycleMode(Mode.Edit)
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif e.button == KEYS['viewer']:
		cycleMode(Mode.View)
		mouseTracker.distance = HAND_DISTANCE
		clickSound.play()
	elif e.button == KEYS['walk']:
		cycleMode(Mode.Walk)
		clickSound.play()
	elif e.button == KEYS['grid']:
		toggleGrid(viz.TOGGLE)
	elif e.button == KEYS['showMenu']:
		toggleMenu()
	elif e.button == KEYS['utility']:
		toggleUtility()
	elif e.button == KEYS['proxi']:
		proxyManager.setDebug(viz.TOGGLE)
		clickSound.play()

		
def onMouseWheel(dir):
#	global ORIENTATION
#	global bridge_root
#	
#	if ORIENTATION == Orientation.Top or ORIENTATION == Orientation.Bottom:
#		pos = bridge_root.getPosition()
#		if dir > 0:
#			pos[2] += 0.5	
#		else:
#			pos[2] -= 0.5
#		bridge_root.setPosition(pos)
	pass
		
def slideRoot(val):
	global TOP_CACHED_Z
	global BOT_CACHED_Z
	global bridge_root
	
	if ORIENTATION == Orientation.Top or ORIENTATION == Orientation.Bottom:
		pos = bridge_root.getPosition()
		pos[2] += val
		if ORIENTATION == Orientation.Top:
			clampedZ = viz.clamp(pos[2],TOP_Z_MIN,SLIDE_MAX)
			pos[2] = clampedZ
			TOP_CACHED_Z = pos[2]
		elif ORIENTATION == Orientation.Bottom:
			clampedZ = viz.clamp(pos[2],BOT_Z_MIN,SLIDE_MAX)
			pos[2] = clampedZ
			BOT_CACHED_Z = pos[2]
		bridge_root.setPosition(pos)
vizact.whilekeydown('1',slideRoot,-SLIDE_INTERVAL)		
vizact.whilekeydown('2',slideRoot,SLIDE_INTERVAL)	
	
global SLIDE_VAL
SLIDE_VAL = 0
def slideRootHat():
	global SLIDE_VAL
	global TOP_CACHED_Z
	global BOT_CACHED_Z
	global bridge_root
	
	if ORIENTATION == Orientation.Top or ORIENTATION == Orientation.Bottom:
		pos = bridge_root.getPosition()
		if SLIDE_VAL == 0:
			pos[2] += SLIDE_INTERVAL
		elif SLIDE_VAL == 180:
			pos[2] -= SLIDE_INTERVAL
			
		if ORIENTATION == Orientation.Top:
			clampedZ = viz.clamp(pos[2],TOP_Z_MIN,SLIDE_MAX)
			pos[2] = clampedZ
			TOP_CACHED_Z = pos[2]
		elif ORIENTATION == Orientation.Bottom:
			clampedZ = viz.clamp(pos[2],BOT_Z_MIN,SLIDE_MAX)
			pos[2] = clampedZ
			BOT_CACHED_Z = pos[2]
		bridge_root.setPosition(pos)
	
def onHatChange(e):
	global SLIDE_VAL
	SLIDE_VAL = e.value

def onMouseDown(button):
	global objToRotate
	global CACHED_GLOVE_Z
	if button == KEYS['rotate']:
		CACHED_GLOVE_Z = mouseTracker.distance
		if objToRotate != None:
			print 'Rotating', objToRotate.name, CACHED_GLOVE_Z
			rotationCanvas.visible(True)


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
		rotationCanvas.visible(False)
	
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
			ORIENTATION = Orientation.Side
		if e.newSel == 1:
			ORIENTATION = Orientation.Top
		if e.newSel == 2:
			ORIENTATION = Orientation.Bottom
		
	clickSound.play()
	
		
import csv
# Saves current Build members' truss dimensions, position, rotation to './data/bridge#.csv'
def SaveData():
	global BUILD_MEMBERS
		
	# Play MUTE
	clickSound.play()
	
	filePath = vizinput.fileSave(file='bridge01.csv',filter=[('CSV Files','*.csv')],directory='/data/saves')		
	if filePath == '':
		return
	
	currentOrientation = ORIENTATION
	cycleOrientation(Orientation.Side)
	
	with open(filePath,'wb') as f:
		writer = csv.writer(f)
		for truss in BUILD_MEMBERS:
			writer.writerow([str(truss.order.diameter),str(truss.order.thickness),str(truss.order.length),str(truss.order.quantity),
							str(truss.getPosition()[0]), str(truss.getPosition()[1]),str(truss.getPosition()[2]),
							str(truss.getEuler()[0]),str(truss.getEuler()[1]),str(truss.getEuler()[2]),
							int(truss.orientation.value)])
	
	cycleOrientation(currentOrientation)
	
	# Save successful feedback
	runFeedbackTask('Save success!')
		
# Loads Build members' truss dimensions, position, rotation from './data/bridge#.csv'					
def LoadData():
	global BUILD_MEMBERS
	global SIDE_MEMBERS
	global TOP_MEMBERS
	global BOT_MEMBERS
	global SIDE_CLONES
	global ORDERS
	global GRAB_LINKS
	
	# Play MUTE
	clickSound.play()
	
	filePath = vizinput.fileOpen(filter=[('CSV Files','*.csv')],directory='./data/saves')		
	if filePath == '':
		return	

	clearMembers()
	
	currentOrientation = ORIENTATION
	cycleOrientation(Orientation.Side)
	
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
		if truss.orientation == Orientation.Side:
			SIDE_MEMBERS.append(truss)
			SIDE_CLONES.append(cloneSide(truss))
		elif truss.orientation == Orientation.Top:
			TOP_MEMBERS.append(truss)
		elif truss.orientation == Orientation.Bottom:
			BOT_MEMBERS.append(truss)
		link = viz.grab(bridge_root,truss)
		truss.link = link
		GRAB_LINKS.append(link)
	
	toggleRoad(road_M)
		
	cycleOrientation(currentOrientation)
	
	# Show load feedback
	runFeedbackTask('Load success!')

# Events
viz.callback ( viz.SLIDER_EVENT, onSlider )
viz.callback ( viz.LIST_EVENT, onList )

# Button callbacks
vizact.onbuttonup ( orderSideButton, addOrder, ORDERS_SIDE_GRID, ORDERS_SIDE, ORDERS_SIDE_ROWS, ORDERS_SIDE_FLAG )
vizact.onbuttonup ( orderSideButton, clickSound.play )
vizact.onbuttonup ( orderTopButton, addOrder, ORDERS_TOP_GRID, ORDERS_TOP, ORDERS_TOP_ROWS, ORDERS_TOP_FLAG )
vizact.onbuttonup ( orderTopButton, clickSound.play )
vizact.onbuttonup ( orderBottomButton, addOrder, ORDERS_BOT_GRID, ORDERS_BOT, ORDERS_BOT_ROWS, ORDERS_BOT_FLAG )
vizact.onbuttonup ( orderBottomButton, clickSound.play )
vizact.onbuttonup ( doneButton, populateInventory )
vizact.onbuttonup ( doneButton, clickSound.play )
vizact.onbuttonup ( resetButton, clearBridge )
vizact.onbuttonup ( resetButton, clickSound.play )
vizact.onbuttonup ( quitButton, quitGame )
vizact.onbuttonup ( quitButton, clickSound.play )
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
vizact.onbuttonup ( soundButton, toggleAudio )


FLASH_TIME = 3.0			# Time to flash screen

def CreateFlashQuad():
	""" Create flash screen quad """
	flash_quad = viz.addTexQuad(parent=viz.ORTHO)
	flash_quad.color(viz.WHITE)
	flash_quad.drawOrder(-10)
	flash_quad.blendFunc(viz.GL_ONE,viz.GL_ONE)
	flash_quad.visible(False)
	flash_quad.setBoxTransform(viz.BOX_ENABLED)
	return flash_quad
flash_quad = CreateFlashQuad()


def FlashScreen():
	"""Flash screen and fade out"""
	flash_quad.visible(True)
	flash_quad.color(viz.WHITE)
	fade_out = vizact.fadeTo(viz.BLACK,time=FLASH_TIME,interpolate=vizact.easeOutStrong)
	flash_quad.runAction(vizact.sequence(fade_out,vizact.method.visible(False)))


def GrayEffect():
	# Create post process effect for blending to gray scale
	gray_effect = BlendEffect(None,GrayscaleEffect(),blend=0.0)
	gray_effect.setEnabled(False)
	vizfx.postprocess.addEffect(gray_effect)
	return gray_effect
gray_effect = GrayEffect()


# Schedule tasks
def MainTask():
	global INITIALIZED
	viewChangeSound.play()	
	
	while True:		
		FlashScreen()
		
		yield viztask.waitButtonUp(doneButton)
		
		bottomRow.removeItem(doneButton)
		confirmButton = bottomRow.addItem(viz.addButtonLabel('Confirm order'),align=viz.ALIGN_CENTER_TOP)
		confirmButton.length(2)
		vizact.onbuttonup ( confirmButton, populateInventory )
		vizact.onbuttonup ( confirmButton, clickSound.play )
		vizact.onbuttonup ( confirmButton, cycleMode, Mode.Build )
		vizact.onbuttonup ( confirmButton, menuCanvas.visible, viz.OFF )

		menuCanvas.visible(viz.OFF)
		menuCanvas.setPosition(0,-2,2)
		dialogCanvas.setPosition(0,-2,2)
		feedbackCanvas.setPosition(0,-2,2)
		
		viz.clearcolor(CLEAR_COLOR)
		
		# Define globals
		global mouseTracker
		global gloveLink
		global highlightTool
		global playerNode
		global navigator
		
		# Setup callbacks
		viz.callback ( viz.KEYUP_EVENT, onKeyUp )
		viz.callback ( viz.KEYDOWN_EVENT, onKeyDown )
		viz.callback ( viz.MOUSEUP_EVENT, onMouseUp )
		viz.callback ( viz.MOUSEDOWN_EVENT, onMouseDown )
		viz.callback ( viz.MOUSEWHEEL_EVENT, onMouseWheel )
		viz.callback ( viz.SENSOR_UP_EVENT, onJoyButton )
		
		import navigation
		joystickConnected = navigation.checkJoystick()
		oculusConnected = navigation.checkOculus()
		navigator = None
		
		if oculusConnected and joystickConnected:
			navigator = navigation.Joyoculus()
			navigator.setAsMain()
			vizact.onsensorup( navigator.getJoy(), navigator.KEYS['mode'],cycleMode,vizact.choice([Mode.Edit,Mode.Build]))
			vizact.onsensorup( navigator.getJoy(), navigator.KEYS['cycle'],cycleOrientation,vizact.choice([Orientation.Top,Orientation.Bottom,Orientation.Side]))
			vizact.onsensorup( navigator.getJoy(), navigator.KEYS['viewMode'],toggleStereo,vizact.choice([False,True]))		
			viz.callback( navigation.getExtension().HAT_EVENT, onHatChange )
			vizact.ontimer(0,slideRootHat)	
		elif joystickConnected:
			navigator = navigation.Joystick()
			navigator.setAsMain()
		elif oculusConnected:
			navigator = navigation.Oculus()
			vizact.onkeyup( navigator.KEYS['mode'],cycleMode,vizact.choice([Mode.Edit,Mode.Build]))
			vizact.onkeyup( navigator.KEYS['cycle'],cycleOrientation,vizact.choice([Orientation.Top,Orientation.Bottom,Orientation.Side]))
			vizact.onkeyup( navigator.KEYS['viewMode'],toggleStereo,vizact.choice([False,True]))
			navigator.setAsMain()
		else:
			navigator = navigation.Navigator()
			vizact.onkeyup( navigator.KEYS['mode'],cycleMode,vizact.choice([Mode.Edit,Mode.Build]))
			vizact.onkeyup( navigator.KEYS['cycle'],cycleOrientation,vizact.choice([Orientation.Top,Orientation.Bottom,Orientation.Side]))
			vizact.onkeyup( navigator.KEYS['viewMode'],toggleStereo,vizact.choice([False,True]))
			viz.fov(START_FOV)
			navigator.setAsMain()
		

		navigator.setOrigin(START_POS,[0,0,0])
		navigator.reset()
		print navigator.getPosition()
		highlightTool.setUpdateFunction(updateHighlightTool)
		mouseTracker = initTracker(HAND_DISTANCE)
		initMouse()
		gloveLink = initLink('glove.cfg',mouseTracker)
		viz.link(gloveLink,highlightTool)	
		vizact.ontimer(0,clampTrackerScroll,mouseTracker,SCROLL_MIN,SCROLL_MAX)
		vizact.whilemousedown ( navigator.KEYS['rotate'], rotateTruss, objToRotate, rotationSlider, rotationLabel )
		
		global axes
		axes = vizshape.addAxes()
		axes.visible(False)
#		playerLink = viz.link(viz.MainView,playerNode)
#		playerLink.setMask(viz.LINK_POS)
#		vizact.onupdate(0,updatePosition(inventoryCanvas,playerNode))
#		viewPos = hmd.getPosition()
		viewPos = navigator.getPosition()
#		keyTracker = vizconnect.getTracker('rift_with_mouse_and_keyboard').getNode3d()
#		keyTransport = vizconnect.getTransport('main_transport').getNode3d()
#		viz.link(viz.MainView,keyTracker)
#		viz.MainView.setPosition(START_POS)
#		playerLink = viz.link(viz.MainView,keyTracker)
#		trackerLink = viz.link(keyTracker,axes)
		inventoryCanvas.setEuler( [0,30,0] )
		inventoryCanvas.setPosition ( [0,viewPos[1]-.2,viewPos[2]+.2] )
		rotationCanvas.setEuler( [0,30,0] )
#		rotationCanvas.setPosition ( [0,viewPos[1]-.1,viewPos[2]+.2] )
#		link = viz.link(viz.MainView,rotationCanvas)
#		link.postMultLinkable(viz.MainView)
#		rotationCanvas.visible(viz.OFF)
#		vizact.onupdate(0,getAvatarPos,keyTransport)
#		vizact.onupdate(0,getAvatarPos,viz.MainView)
#		vizact.onupdate(0,getAvatarPos,viewport.getNode3d())
#		vizact.onupdate(0,updatePosition,axes,keyTransport)
#		link = viz.link(keyTransport,axes,viz.LINK_POS)

#		axesLink = viz.link(hmd.viewLink,axes)
		axesLink = viz.link(navigator.VIEW_LINK,axes)
		axesLink.setMask(viz.LINK_POS)
		axesLink.postTrans([0,-1,2])

		viz.grab(axes,inventoryCanvas)
		
#		pos = START_POS
#		pos[1] += -1
#		pos[2] += 1
#		axes.setPosition(pos)
#		viz.grab(keyTransport,axes)
		cycleMode(Mode.View)
		
		
		INITIALIZED = True
viztask.schedule( MainTask() )

def toggleStereo(val=viz.TOGGLE):
	if val is True:
		viz.MainWindow.stereo(STEREOMODE)
	else:
		viz.MainWindow.stereo(viz.STEREO_RIGHT)
# Pre-load sounds
viz.playSound('./resources/sounds/return_to_holodeck.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/button_highlight.wav',viz.SOUND_PRELOAD) 
viz.playSound('./resources/sounds/click.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/show_menu.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/hide_menu.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/page_advance.wav',viz.SOUND_PRELOAD)
viz.playSound('./resources/sounds/out_of_bounds_warning.wav',viz.SOUND_PRELOAD)

	
def updatePosition(self):
	"""Internal update function"""
	# Update the transformation of the node
	mat = self._target.getMatrix(viz.ABS_GLOBAL)
	posOff = [0, self.getSize()[1]/2.0+self._target.getSize()[1]/2.0, -0.01]
	pos = mat.preMultVec(posOff)
	mat.setPosition(pos)
	self.setMatrix(mat, viz.ABS_GLOBAL)
	
def updatePosition(obj,target):
	"""Internal update function"""
	# Update the transformation of the node
	mat = target.getMatrix(viz.ABS_GLOBAL)
#	posOff = [0, obj.getSize()[1]/2.0+target.getSize()[1]/2.0, -0.01]
	posOff = [0, -1, 1]
	pos = mat.preMultVec(posOff)
	mat.setPosition(pos)
	obj.setEuler([0,0,0])
	obj.setMatrix(mat, viz.ABS_GLOBAL)


def getAvatarPos(obj):
	print obj.getPosition()