"""
[Objective]
Specify truss member dimensions and order materials required to build a 20m-long bridge.

[Controls]
1. Look around and orient the highlighter with the VR HEADSET
2. Navigate using WASD-keys
3. Manually turn view using Q and E
4. Control elevation with Z and X
3. Interact with floating menus using the VIRTUAL MOUSE
4. Extend or retract virtual hand with MOUSE SCROLL WHEEL
5. Grab and hold onto truss members by LEFT MOUSE CLICK when highlighted green
6. Adjust truss ang le by RIGHT MOUSE CLICK while highlighting truss member
7. Toggle utilities with MIDDLE MOUSE CLICK
8. Toggle main menu with SPACE BAR
9. Grab and release main menu with LEFT CONTROL KEY
"""
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
import sys
import themes
import tools
import xml.etree.ElementTree as ET

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
BUILD_ROAM_LIMIT = ([12,-12,-10,10])	# Front,back,left,right limits in meters(m)
START_POS = ([0,5.82,-17])				# Set at 5m + avatar height above ground and 17m back fron center
BUILD_ROTATION = ([0,0,0])				# Zero-rotation to face dead center

MENU_RES = ([800,750])
MENU_POS = ([0,18,-8])
INSPECTOR_POS_OFFSET = ( [0,0,2] )
INSPECTOR_ROT_OFFSET = ( [] )
INVENTORY_MESSAGE = 'Order truss members from the catalogue and manage'

LEN_MIN = 0.1
LEN_MAX = 20.0
QTY_MIN = 1
QTY_MAX = 20

GRIDS = []
ENVIRONMENTS = []

# Setup order lists
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
BUILD_MEMBERS = []
SIDE_CLONES = []
BRIDGE_ROOT = vizshape.addAxes()
X = viz.addText3D('X',pos=[1.1,0,0],color=viz.RED,scale=[0.3,0.3,0.3],parent=BRIDGE_ROOT)
Y = viz.addText3D('Y',pos=[0,1.1,0],color=viz.GREEN,scale=[0.3,0.3,0.3],align=viz.ALIGN_CENTER_BASE,parent=BRIDGE_ROOT)
Z = viz.addText3D('Z',pos=[0,0,1.1],color=viz.BLUE,scale=[0.3,0.3,0.3],align=viz.ALIGN_CENTER_BASE,parent=BRIDGE_ROOT)
BRIDGE_ROOT_POS = [0,4,0]

PROXY_NODES = []
TARGET_NODES = []
SENSOR_NODES = []

PRE_SNAP_POS = []
PRE_SNAP_ROT = []
SNAP_TO_POS = []
VALID_SNAP = False

HAND_DISTANCE = 0.5
SCROLL_MIN = 0.2
SCROLL_MAX = 20

DEBUG_PROXIMITY = True
DEBUG_CAMBOUNDS = False

SAVE_FILES = [	 './data/bridge1.csv'
				,'./data/bridge2.csv'
				,'./data/bridge3.csv' ]

# Setup key commands
KEYS = { 'forward'	: 'w'
		,'back'		: 's'
		,'left'		: 'a'
		,'right'	: 'd'
		,'reset'	: 'r'
		,'home'		: viz.KEY_HOME
		,'builder'	: 'b'
		,'viewer'	: 'v'
		,'env'		: 't'
		,'grid'		: 'g'
		,'hand'		: 'h'
		,'showMenu' : ' '
		,'snapMenu'	: viz.KEY_CONTROL_L
		,'utility'	: viz.MOUSEBUTTON_MIDDLE
		,'proxi'	: 'p'
		,'rotate'	: viz.MOUSEBUTTON_RIGHT
		,'collide'	: 'c'
}

# Initialize scene
def initScene(res=([1280,720]),quality=4,stencil=8,stereoMode=viz.STEREO_HORZ,fullscreen=viz.FULLSCREEN,clearColor=viz.BLACK):
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
	return vp
	
	
def initLighting():
	# Disable the head lamps since we're doing lighting ourselves
	for window in viz.getWindowList():
		window.getView().getHeadLight().disable()
	sky_light = viz.addDirectionalLight(euler=(0,90,0))
	sky_light.color(viz.WHITE)
	sky_light.ambient([0.8]*3)
	viz.setOption('viz.lightModel.ambient',[0]*3)


# Laser pointer
def initPointerTool():
	from tools import laser_pointer
	return laser_pointer.LaserPointer()
	
	
def initHighlightTool():
	from tools import highlighter
	return highlighter.Highlighter()
	
	
def initPencilTool():
	from tools import pencil
	return pencil.Pencil()
	
	
def initProxy():
	# Create proximity manager
	proxyManager = vizproximity.Manager()
	proxyManager.setDebug(DEBUG_PROXIMITY)
	
	# Register callbacks for proximity SENSOR_NODES
	def enterProximity(e):
	#	print 'Entered',e.sensor
		global SNAP_TO_POS
		global VALID_SNAP
		SNAP_TO_POS = e.sensor.getSource().getPosition()
		VALID_SNAP = True
	

	def exitProximity(e):
	#	print 'Exited',e.sensor
		global VALID_SNAP
		VALID_SNAP = False

	proxyManager.onEnter(None, enterProximity)
	proxyManager.onExit(None, exitProximity)
	
	return proxyManager


# Initialize
initScene(RESOLUTION,MULTISAMPLING,STENCIL,STEREOMODE,FULLSCREEN,CLEAR_COLOR)
cameraRift = initCamera('vizconnect_config_riftDefault')
#cameraFly = initCamera('vizconnect_config_riftFly')
hmd = initOculus()
viewport = initViewport(START_POS)
initLighting()

laserTool = initPointerTool()
laserTool.disable(viz.PICKING)

highlightTool = initHighlightTool()
highlightTool.disable(viz.PICKING)

pencilTool = initPencilTool()
pencilTool.disable(viz.PICKING)

proxyManager = initProxy()

# Sounds
startSound = viz.addAudio('./resources/sounds/return_to_holodeck.wav')
buttonHighlightSound = viz.addAudio('./resources/sounds/button_highlight.wav')
clickSound = viz.addAudio('./resources/sounds/click.wav')
showMenuSound = viz.addAudio('./resources/sounds/show_menu.wav')
hideMenuSound = viz.addAudio('./resources/sounds/hide_menu.wav')
viewChangeSound = viz.addAudio('./resources/sounds/page_advance.wav')
warningSound = viz.addAudio('./resources/sounds/out_of_bounds_warning.wav')

# Set volume
startSound.volume(.5)
buttonHighlightSound.volume(.5)
clickSound.volume(.5)
showMenuSound.volume(.5)
hideMenuSound.volume(.5)
viewChangeSound.volume(.5)
warningSound.volume(.05)

viewChangeSound.play()

# Set grids
def initGrid():	
	# Create front grid
	grid_front = vizshape.addGrid(size=(20,8))
	grid_front.color(GRID_COLOR)
	grid_front.setPosition(0,2+4,-5)
	grid_front.setEuler(0,90,0)
	
	# Create back grid
	grid_back = vizshape.addGrid(size=(20,8))
	grid_back.color(GRID_COLOR)
	grid_back.setPosition(0,2+4,-5-24)
	grid_back.setEuler(0,90,0)
	grid_back.setScale(1,z=-1)

	# Create bottom grid
	grid_bottom = vizshape.addGrid(size=(20,24))
	grid_bottom.color(GRID_COLOR)
	grid_bottom.setPosition(0,2,START_POS[2])
	
	# Create left grid
	grid_left = vizshape.addGrid(size=(8,24),)
	grid_left.color(GRID_COLOR)
	grid_left.setPosition(-10,4+2,START_POS[2])
	grid_left.setEuler(0,0,90)
	
	# Create right grid
	grid_right = vizshape.addGrid(size=(8,24))
	grid_right.color(GRID_COLOR)
	grid_right.setPosition(10,4+2,START_POS[2])
	grid_right.setEuler(0,0,-90)

	# Create floating measurements
	span_text = viz.addText3D('<< 20 meters >>',pos=[-3.25,10.25,-5])
	span_text.disable(viz.PICKING)
	height_text = viz.addText3D('<< 8 meters >>',pos=[-10.25,2.5,-5],euler=[0,0,90])
	height_text.disable(viz.PICKING)
	
	GRIDS.append(grid_back)
	GRIDS.append(grid_bottom)
	GRIDS.append(grid_front)
	GRIDS.append(grid_left)
	GRIDS.append(grid_right)
	GRIDS.append(span_text)
	GRIDS.append(height_text)
initGrid()


# Parse catalogue from data subdirectory
def getCatalogue(path):
	return ET.parse(str(path)).getroot()
root = getCatalogue('data/catalogue_CHS.xml')


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

# Setup environment
day = viz.add('resources/sky_day.osgb', scale=([5,5,5]))
river = viz.addChild('resources/singaporeEnv.osgb', pos=(0,0,0),scale=([1,1,1]))
water = viz.addChild('resources/water.osgb', pos=(0,0,0),scale=([1,1,1]))
riverEnv = viz.addChild('resources/riverEnv.osgb')

ENVIRONMENTS.append(day)
ENVIRONMENTS.append(river)
ENVIRONMENTS.append(water)
ENVIRONMENTS.append(riverEnv)

water.setAnimationSpeed(0.005)

for environment in ENVIRONMENTS:
	environment.visible(viz.OFF)

# Bridge pin and roller supports
pinSupport = viz.addChild('resources/pinSupport.osgb',pos=(-9.5,4,0),scale=[1,1,11])
rollerSupport = viz.addChild('resources/rollerSupport.osgb',pos=(9.5,4,0),scale=[1,1,11])
supports = [pinSupport,rollerSupport]
for model in supports:
	model.texture(env)
	model.appearance(viz.ENVIRONMENT_MAP)
	model.apply(effect)
	model.apply(lightEffect)

#Setup anchor points for truss members
pinAnchorSphere = vizshape.addSphere(0.2,pos=([-10,5,-5]))
#pinAnchorSphere.visible(False)
pinLink = viz.link(pinAnchorSphere,viz.NullLinkable)
pinAnchorSensor = vizproximity.Sensor(vizproximity.Sphere(0.3,center=[0,0.1,0]),pinLink)
proxyManager.addSensor(pinAnchorSensor)
viz.grab(pinSupport,pinAnchorSphere)

rollerAnchorSphere = vizshape.addSphere(0.2,pos=([10,5,-5]))
#rollerAnchorSphere.visible(False)
rollerLink = viz.link(rollerAnchorSphere,viz.NullLinkable)
rollerAnchorSensor = vizproximity.Sensor(vizproximity.Sphere(0.3,center=[0,0.1,0]), rollerLink)
proxyManager.addSensor(rollerAnchorSensor)
viz.grab(rollerSupport,rollerAnchorSphere)

# Setup bridge root
BRIDGE_ROOT.setPosition( BRIDGE_ROOT_POS )

for model in supports:
	viz.grab(BRIDGE_ROOT,model)
	
# Rotate root test
BRIDGE_ROOT.setEuler( [0,-90,0] )

# Create canvas for displaying GUI objects
instructionsPanel = vizinfo.InfoPanel(title='Truss Bridge Builder & Visualizer',align=viz.ALIGN_CENTER_BASE,icon=False)
instructionsPanel.getTitleBar().fontSize(36)

# Options panel
optionPanel = vizinfo.InfoPanel(text='Settings', title='Options', align=viz.ALIGN_CENTER_BASE, icon=False)
optionPanel.getTitleBar().fontSize(36)
optionPanel.addSection('Save')
saveBridgeButton1 = optionPanel.addItem(viz.addButtonLabel('Bridge 01'))
saveBridgeButton2 = optionPanel.addItem(viz.addButtonLabel('Bridge 02'))
saveBridgeButton3 = optionPanel.addItem(viz.addButtonLabel('Bridge 03'))
optionPanel.addSeparator()
optionPanel.addSection('Load')
loadBridgeButton1 = optionPanel.addItem(viz.addButtonLabel('Bridge 01'))
loadBridgeButton2 = optionPanel.addItem(viz.addButtonLabel('Bridge 02'))
loadBridgeButton3 = optionPanel.addItem(viz.addButtonLabel('Bridge 03'))

# Initialize order panel containing mainRow and midRow
#inventoryPanel = vizdlg.Panel(layout=vizdlg.LAYOUT_VERT_CENTER,align=viz.ALIGN_CENTER,spacing=0,margin=(0,0))
inventoryPanel = vizinfo.InfoPanel(title='Truss Member Inventory Management',text='Order & Manage truss members from the catalogue', align=viz.ALIGN_CENTER_BASE, icon=False)
inventoryPanel.getTitleBar().fontSize(36)

# Initialize mainRow
# Initialize midRow
midRow = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_CENTER,align=viz.ALIGN_CENTER_TOP,border=False,background=False,spacing=20)
# Initialize orderPanel box
orderPanel = midRow.addItem(vizinfo.InfoPanel('Fill in all required fields',align=None,margin=(0,0),icon=False),align=viz.ALIGN_LEFT_TOP)
orderPanel.setTitle( 'Order' )	
orderPanel.getTitleBar().fontSize(28)
orderPanel.addSeparator()
# Initialize type
typeDropList = viz.addDropList()
typeDropList.addItem('CHS', 0)
trussType = orderPanel.addLabelItem('Type', typeDropList)
# Initialize diameterDropList
diameterDropList = viz.addDropList()
for member in root.iter('member'):
	diameter = member.get('diameter')
	diameterDropList.addItem(diameter)
diameterDropList.select(19)
diameter = orderPanel.addLabelItem('Diameter (mm)', diameterDropList)
# Initialize thicknessDropList
thicknessDropList = viz.addDropList()
thicknesses = []
for thickness in root[diameterDropList.getSelection()]:
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
orderSideButton = orderPanel.addItem(viz.addButtonLabel('ADD TO SIDE'),align=viz.ALIGN_CENTER_BOTTOM)
orderTopButton = orderPanel.addItem(viz.addButtonLabel('ADD TO TOP'),align=viz.ALIGN_CENTER_BOTTOM)
orderBottomButton = orderPanel.addItem(viz.addButtonLabel('ADD TO BOTTOM'),align=viz.ALIGN_CENTER_BOTTOM)

# Initialize stockPanel
stockMainPanel = vizinfo.InfoPanel('Ordered truss members',align=None,margin=(0,0),icon=False)
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
inspectorCanvas = viz.addGUICanvas(align=viz.ALIGN_LEFT_CENTER)
inspector = panels.InspectorPanel()
statPanel = inspector.GetPanel()
statPanel.setParent(inspectorCanvas)
# Link inspector canvas with main view
inspectorLink = viz.link(viz.MainView, inspectorCanvas)
#inspectorLink.preMultLinkable(viz.MainView)
inspectorLink.preTrans( [-2, -3, 5] )
inspectorLink.preEuler( [-45, 0, 0] )

utilityButtons = []
# Create docked utility panel
utilityCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
points = mathlite.getPointsInCircum(30,7)
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

utilityButtons = ( [menuButton,homeButton,buildModeButton,viewerModeButton,toggleEnvButton,toggleGridButton,resetOriButton] )
for i, button in enumerate(utilityButtons):
	button.setPosition(0.5 + points[i][0], 0.5 + points[i][1])
	
# Link utility canvas with main view
utilityLink = viz.link(viz.MainView,utilityCanvas)
utilityLink.preTrans( [0, 0, 1.5] )

# Rotation Panel
rotationCanvas = viz.addGUICanvas(align=viz.ALIGN_CENTER)
rotationPanel = vizdlg.GridPanel(parent=rotationCanvas,align=viz.ALIGN_CENTER)
rotationSlider = viz.addSlider()
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
	menuCanvas.setRenderWorld(MENU_RES,[20,viz.AUTO_COMPUTE])
	menuCanvas.setPosition(MENU_POS)
	menuCanvas.setEuler(0,0,0)
	updateMouseStyle(menuCanvas)
	
	inspectorCanvas.setRenderWorld(RESOLUTION,[20,viz.AUTO_COMPUTE])
	inspectorCanvas.setPosition(0,0,0)
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
		
		
def inspectMember(obj):
	inspector.diameter_stat.message('d (mm): ' + str(obj.diameter))
	inspector.thickness_stat.message('t (mm): ' + str(obj.thickness))
	inspector.length_stat.message('l (m): ' + str(obj.length))
	inspector.rotation_stat.message('angle: ' + str(obj.getEuler()[2]))


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
	orderList.sortByAttr()
	
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
	
	global tabbedPanel
	tabbedPanel = vizdlg.TabPanel(align=viz.ALIGN_CENTER_TOP,layout=vizdlg.LAYOUT_VERT_LEFT,parent=inventoryCanvas)

	# Side truss inventory
	global sideInventory
	sideInventory = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	sideInventory.layout = vizdlg.LAYOUT_VERT_LEFT
	tabbedPanel.addPanel('Side',sideInventory)

	global sideRows
	sideRows = []
	
	# Top truss inventory
	global topInventory
	topInventory = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	topInventory.layout = vizdlg.LAYOUT_VERT_LEFT
	tabbedPanel.addPanel('Top',topInventory)
	
	global topRows
	topRows = []
	
	# Bottom truss inventory
	global bottomInventory
	bottomInventory = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	bottomInventory.layout = vizdlg.LAYOUT_VERT_LEFT
	tabbedPanel.addPanel('Bottom',bottomInventory)

	global bottomRows
	bottomRows = []

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
	truss = viz.addChild(path,cache=viz.CACHE_COPY)
	truss.order = order
	truss.diameter = float(order.diameter)
	truss.thickness = float(order.thickness)
	truss.length = float(order.length)
	truss.quantity = int(order.quantity)
	
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
	highlightTool.setItems(mergedList)
	
	if not loading:
		global grabbedItem
		global highlightedItem
		global isgrabbing
		
		grabbedItem = truss		
		highlightedItem = truss
		isgrabbing = True
		truss.isNewMember = True
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
	highlightTool.setItems(mergedList)
	
	# Clear ORDERS
	ORDERS = []
	

def diameterListChanged(e,sound=True):
	thicknesses = []
	index = e.object.getSelection()
	for thickness in root[int(index)]:
		thicknesses.append(thickness.text)
	thicknessDropList.clearItems()
	thicknessDropList.addItems(thicknesses)
	
	if sound:
		clickSound.play()


def clearMembers():
	"""Delete truss members"""
	global INVENTORY
	global BUILD_MEMBERS
	global PROXY_NODES
	global TARGET_NODES
	global SENSOR_NODES
	
	highlightTool.removeItems(INVENTORY)
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
		del target
	TARGET_NODES = []
	for sensor in SENSOR_NODES:
		proxyManager.removeSensor(sensor)
		del sensor
	SENSOR_NODES = []
	
	# Add glove grabberTool back to proximity targets
#	proxyManager.addTarget(proxTarget)

	
def toggleEnvironment(value=viz.TOGGLE):
	for environment in ENVIRONMENTS:
		environment.visible(value)

			
def toggleUtility(sound=True):
	utilityCanvas.visible(viz.TOGGLE)
	menuCanvas.visible(viz.OFF)
	
	if sound:
		if utilityCanvas.getVisible == False:
			hideMenuSound.play()
		else:
			showMenuSound.play()

	
#Link the grabber to an arrow in order to
#visualize it's position
def initTracker(distance=0.5):
	from vizconnect.util import virtual_trackers
	tracker = virtual_trackers.ScrollWheel(followMouse=True)
	tracker.distance = distance
	return tracker
mouseTracker = initTracker(HAND_DISTANCE)


def initLink(modelPath):
	model = viz.addChild(modelPath)
	link = viz.link(mouseTracker,model)
	link.postMultLinkable(viz.MainView)
	return link
gloveLink = initLink('glove.cfg')
viz.link(gloveLink,highlightTool)
viz.link(gloveLink,laserTool)
viz.link(gloveLink,pencilTool)


def clampTrackerScroll(tracker,min=0.2,max=20):
	tracker.distance = viz.clamp(tracker.distance,min,max)
vizact.ontimer(0,clampTrackerScroll,mouseTracker,SCROLL_MIN,SCROLL_MAX)

## Hand
#import hand
#r_hand = hand.add(sensor=None)
#r_hand.disable(viz.PICKING)
#viz.link(glove,r_hand)

menuLink = None
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
		
		
def toggleCollision():
	viz.collision(viz.TOGGLE)


# Disable mouse navigation and hide the mouse curser
viz.mouse(viz.OFF)
viz.mouse.setVisible(viz.OFF)
viz.mouse.setTrap(viz.ON)

# update code for grabber
isgrabbing = False
grabbedItem = None
highlightedItem = None
grabbedRotation = []
def updateHandGrabber(grabberTool):
	global grabbedItem
	state = viz.mouse.getState()
	if state & viz.MOUSEBUTTON_LEFT:
		grabberTool.grabAndHold()
	if grabbedItem is not None:	
#		print 'Grabbing', grabbedItem
		xOffset = grabbedItem.getScale()[0] / 2
		clampedX =  viz.clamp(grabbedItem.getPosition()[0],-10 + xOffset,10 - xOffset)
		clampedY =  viz.clamp(grabbedItem.getPosition()[1],2,10)
		grabbedItem.setPosition( [clampedX,clampedY,-5] )
		grabbedItem.setEuler( [0,0,0] )
#grabberTool.setUpdateFunction(updateHandGrabber)

objToRotate = None
# update code for highlight tool
def updateHighlightTool(highlightTool):
	global grabbedItem
	global grabbedRotation
	global isgrabbing
	
	global proxyManager
	global PRE_SNAP_POS
	global PRE_SNAP_ROT
	global SNAP_TO_POS
	
	highlightTool.highlight()
	if highlightTool.getSelection() is None:
		return	
		
	state = viz.mouse.getState()
	if state & viz.MOUSEBUTTON_LEFT:
		if isgrabbing == False:
			grabbedItem = highlightTool.getSelection()
			print 'Grabbing onto:', grabbedItem

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
highlightTool.setUpdateFunction(updateHighlightTool)


#Register a callback function for the highlight event
def onHighlight(e):
	global isgrabbing
	global highlightedItem
	if e.new != None and e.new.length != None:
		inspectMember(e.new)
		highlightedItem = e.new
from tools import highlighter
viz.callback(highlighter.HIGHLIGHT_EVENT,onHighlight)


def onHighlightGrab():
	""" Clamp grabbed member to front glove position and grid z """
	global grabbedItem
	global isgrabbing
	global gloveLink	
	if grabbedItem != None and isgrabbing == True:
		xOffset = grabbedItem.getScale()[0] / 2
		clampedX =  viz.clamp( gloveLink.getPosition()[0],-10 + xOffset,10 - xOffset )
		clampedY =  viz.clamp( gloveLink.getPosition()[1],2,10 )
		grabbedItem.setPosition( [gloveLink.getPosition()[0],gloveLink.getPosition()[1],-5] )
vizact.ontimer(0,onHighlightGrab)


# update code for laser pointer
def updateLaserPointer(pointerTool):
	state = viz.mouse.getState()
	if state & viz. MOUSEBUTTON_LEFT:
		pointerTool.shoot()
#laserTool.setUpdateFunction(updateLaserPointer)


from tools import grabber
def onGrab(e):
	global grabbedItem
	global proxyManager
	global PRE_SNAP_POS
	global PRE_SNAP_ROT
	global SNAP_TO_POS
	
	grabbedItem = e.grabbed
	
	# Enable truss member target nodes
	proxyManager.addTarget(grabbedItem.targetNodes[0])
	proxyManager.addTarget(grabbedItem.targetNodes[1])
	
	# Disable truss member sensor nodes
	proxyManager.removeSensor(grabbedItem.sensorNodes[0])
	proxyManager.removeSensor(grabbedItem.sensorNodes[1])
	
	PRE_SNAP_POS = e.grabbed.getPosition()
	PRE_SNAP_ROT = e.grabbed.getEuler()
	
	SNAP_TO_POS = grabbedItem.getPosition()
#viz.callback(grabber.GRAB_EVENT,onGrab)


def onRelease(e=None,sound=True):
	global INVENTORY
	global BUILD_MEMBERS
	global grabbedItem
	global proxyManager
	global PRE_SNAP_POS
	global PRE_SNAP_ROT
	global SNAP_TO_POS
	global VALID_SNAP
		
	if VALID_SNAP:
		try:			
			if grabbedItem.isNewMember == True:
				cloneSide(grabbedItem)			
				grabbedItem.isNewMember = False
		except:
			print 'Not new member'
			pass
			
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
		if sound:
			clickSound.play()
	else:
		try:			
			# If invalid position and newly-generated truss, destroy it
			if grabbedItem.isNewMember == True:
				BUILD_MEMBERS.remove(grabbedItem)
				proxyManager.removeTarget(grabbedItem.targetNodes[0])
				proxyManager.removeTarget(grabbedItem.targetNodes[1])
				grabbedItem.remove()
				highlightedItem = None
			else:	
				grabbedItem.setPosition(PRE_SNAP_POS)
				grabbedItem.setEuler(PRE_SNAP_ROT)
				# Enable sensor nodes for other members to snap to
				proxyManager.addSensor(grabbedItem.sensorNodes[0])
				proxyManager.addSensor(grabbedItem.sensorNodes[1])
		except:
			highlightedItem = None
			grabbedItem.setPosition(PRE_SNAP_POS)
			grabbedItem.setEuler(PRE_SNAP_ROT)
			# Enable sensor nodes for other members to snap to
			proxyManager.addSensor(grabbedItem.sensorNodes[0])
			proxyManager.addSensor(grabbedItem.sensorNodes[1])
			
		# Play warning sound
		if sound:
			warningSound.play()
		
	# Disable truss member target nodes on release
	proxyManager.removeTarget(grabbedItem.targetNodes[0])
	proxyManager.removeTarget(grabbedItem.targetNodes[1])
	grabbedItem = None
	SNAP_TO_POS = []


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
	rot = obj.getEuler()
	pos = mathlite.getNewRange(rot[2],90,-90,0,1)
	slider.set(pos)
	string = str(int(rot[2]))
	label.message(string)


def rotateTruss(obj,slider,label):	
	if objToRotate != None:
		slider.visible(True)
		pos = viz.Mouse.getPosition(viz.WINDOW_NORMALIZED)[0]
		slider.set(pos)
		rotateTo = mathlite.getNewRange(pos,0,1,90,-90)
		objToRotate.setEuler(0,0,int(rotateTo))
		rotation = int(objToRotate.getEuler()[2])
		string = str(rotation)
		rotationLabel.message(string)
		

# Setup Callbacks and Events
def onKeyUp(key,sound=True):	
	if key == viz.KEY_TAB:
		pass
	elif key == KEYS['home']:
		viewport.reset()
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
			print 'Reset orientation failed: Unable to get Oculus Rift sensor!'
			warningSound.play()
		clickSound.play()
	elif key == KEYS['hand']:
		mouseTracker.distance = HAND_DISTANCE
	elif key == KEYS['builder']:
		toggleEnvironment(False)
		proxyManager.setDebug(True)
		mouseTracker.distance = HAND_DISTANCE
		for grid in GRIDS:
			grid.visible(True)
		clickSound.play()
	elif key == KEYS['viewer']:
		toggleEnvironment(True)
		proxyManager.setDebug(False)
		mouseTracker.distance = HAND_DISTANCE
		for grid in GRIDS:
			grid.visible(False)
		clickSound.play()
	elif key == KEYS['grid']:
		for grid in GRIDS:
			grid.visible(viz.TOGGLE)
		clickSound.play()
	elif key == KEYS['showMenu']:
		menuCanvas.visible(viz.TOGGLE)
		utilityCanvas.visible(viz.OFF)
		showMenuSound.play()
	elif key == KEYS['proxi']:
		proxyManager.setDebug(viz.TOGGLE)
		clickSound.play()
	elif key == 'l':
		viz.link(cameraFly,viz.MainView)

		
def onMouseUp(button):	
	global isgrabbing
	if button == viz.MOUSEBUTTON_LEFT:
		if isgrabbing == True:
			onRelease()
			isgrabbing = False
			
#	global highlightedItem
#	if button == KEYS['rotate']:
#		if highlightedItem != None:
#			rot = highlightedItem.getEuler()
#			pos = mathlite.getNewRange(rot[2],90,-90,0,1)
#			rotationSlider.set(pos)
#			rotationLabel.message(str(int(rot[2])))
#			rotationCanvas.visible(viz.TOGGLE)

	global objToRotate
	if button == KEYS['rotate']:
		if objToRotate != None:
			objToRotate = None
		rotationSlider.visible(False)
	
	if button == KEYS['utility']:
		toggleUtility()


def onMouseDown(button):
	global objToRotate
	if button == KEYS['rotate']:
		if objToRotate != None:
			rotationSlider.visible(True)


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


import csv
# Saves current build members' truss dimensions, position, rotation to './data/bridge#.csv'
def SaveData(filePath,sound=True):
	global BUILD_MEMBERS
		
	if sound:
		clickSound.play()
	
	with open(filePath,'wb') as f:
		writer = csv.writer(f)
		for truss in BUILD_MEMBERS:
			writer.writerow([str(truss.order.diameter),str(truss.order.thickness),str(truss.order.length),str(truss.order.quantity),
							str(truss.getPosition()[0]), str(truss.getPosition()[1]),str(truss.getPosition()[2]),
							str(truss.getEuler()[0]),str(truss.getEuler()[1]),str(truss.getEuler()[2])])
	
		
# Loads build members' truss dimensions, position, rotation from './data/bridge#.csv'					
def LoadData(filePath,sound=True):
	global BUILD_MEMBERS
	global SIDE_CLONES
	global ORDERS
	global highlightTool
	
	if sound:
		clickSound.play()	
	
	# Clear previous bridge
	for member in BUILD_MEMBERS:
		member.remove()
		del member
	BUILD_MEMBERS = []
	
	# Clear side clones
	for clone in SIDE_CLONES:
		clone.remove()
		del clone
	SIDE_CLONES = []
	
	ORDERS = []
	with open(filePath,'rb') as f:
		reader = csv.reader(f)
		for row in reader:
			 order = Order(diameter=float(row[0]),thickness=float(row[1]),length=float(row[2]),quantity=int(row[3]))
			 order.pos = ( [float(row[4]), float(row[5]), float(row[6])] )
			 order.euler = ( [float(row[7]), float(row[8]), float(row[9])] )
			 ORDERS.append(order)
	
	clearMembers()
	generateMembers(loading=True)

	for truss in BUILD_MEMBERS:
		truss.setPosition(truss.order.pos)
		truss.setEuler(truss.order.euler)
		SIDE_CLONES.append(cloneSide(truss))
		
		

# Events
viz.callback ( viz.KEYUP_EVENT, onKeyUp )
viz.callback ( viz.MOUSEUP_EVENT, onMouseUp )
viz.callback ( viz.MOUSEDOWN_EVENT, onMouseDown )
viz.callback ( viz.SLIDER_EVENT, onSlider )

# Button callbacks
vizact.onbuttonup ( orderSideButton, addOrder, ORDERS_SIDE_GRID, ORDERS_SIDE, ORDERS_SIDE_ROWS, ORDERS_SIDE_FLAG )
vizact.onbuttonup ( orderSideButton, clickSound.play )
vizact.onbuttonup ( orderTopButton, addOrder, ORDERS_TOP_GRID, ORDERS_TOP, ORDERS_TOP_ROWS, ORDERS_TOP_FLAG )
vizact.onbuttonup ( orderTopButton, clickSound.play )
vizact.onbuttonup ( orderBottomButton, addOrder, ORDERS_BOT_GRID, ORDERS_BOT, ORDERS_BOT_ROWS, ORDERS_BOT_FLAG )
vizact.onbuttonup ( orderBottomButton, clickSound.play )
#vizact.onbuttonup ( doneButton, generateMembers )
vizact.onbuttonup ( doneButton, populateInventory, ORDERS_SIDE, ORDERS_TOP, ORDERS_BOT )
vizact.onbuttonup ( doneButton, clickSound.play )
vizact.onkeydown ( KEYS['snapMenu'], toggleMenuLink )
vizact.onlist( diameterDropList, diameterListChanged )
vizact.whilemousedown ( KEYS['rotate'], rotateTruss, objToRotate, rotationSlider, rotationLabel )

# Utility
vizact.onbuttonup ( menuButton, toggleMenuLink )
vizact.onbuttonup ( menuButton, onKeyUp, KEYS['showMenu'], )
vizact.onbuttonup ( homeButton, onKeyUp, KEYS['home'] )
vizact.onbuttonup ( resetOriButton, onKeyUp, KEYS['reset'] )
vizact.onbuttonup ( buildModeButton, onKeyUp, KEYS['builder'] )
vizact.onbuttonup ( viewerModeButton, onKeyUp, KEYS['viewer'] )
vizact.onbuttonup ( resetOriButton, onKeyUp, KEYS['reset'] )
vizact.onbuttonup ( toggleEnvButton, onKeyUp, KEYS['env'] )
vizact.onbuttonup ( toggleGridButton, onKeyUp, KEYS['grid'] )
vizact.onbuttonup ( saveBridgeButton1, SaveData, SAVE_FILES[0] )
vizact.onbuttonup ( saveBridgeButton2, SaveData, SAVE_FILES[1] )
vizact.onbuttonup ( saveBridgeButton3, SaveData, SAVE_FILES[2] )
vizact.onbuttonup ( loadBridgeButton1, LoadData, SAVE_FILES[0] )
vizact.onbuttonup ( loadBridgeButton2, LoadData, SAVE_FILES[1] )
vizact.onbuttonup ( loadBridgeButton3, LoadData, SAVE_FILES[2] )
