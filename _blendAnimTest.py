"""
This script demonstrates the various kinds of animations
that can be exported by our 3ds Max exporter plugin.
Use the drop list to link the view to an animation path.
The avatar and pigeon are attached to an animation path.
The fountain shows an example of animated UVs.
The banner uses a sequence helper to animate.
Use the WASD keys to move around.
"""
import viz
import vizact
import vizcam
import vizshape
import vizconfig

viz.setMultiSample(8)
viz.fov(60)
viz.go()

import vizinfo
vizinfo.InfoPanel(align=viz.ALIGN_LEFT_TOP)

# Add piazza model
model = viz.addChild('piazza.osgb')

# Add piazza animations
animations = viz.add('piazza_animations.osgb')

# Create pigeon parented to walk animation
pigeon_path = animations.getChild('walk').copy()
pigeon_path.setAnimationSpeed(0.5)
pigeon = viz.addAvatar('pigeon.cfg')
pigeon.setParent(pigeon_path,node='walk')
pigeon.state(2)

# Create avatar parented to walk animation
avatar_path = animations.getChild('walk').copy()
avatar_path.setAnimationTime(10.0)
avatar_path.setAnimationSpeed(1.5)
avatar = viz.addAvatar('vcc_male2.cfg')
avatar.setParent(avatar_path,node='walk')
avatar.state(2)

# Create axes parented to fly animation
axes = vizshape.addAxes()
axes.setParent(animations,node='fly')

# Create keyboard navigation for viewpoint
camera = vizcam.addKeyboard6DOF()
camera.setPosition([0,2,0])

# Create blend linkable for transitioning between view links
blend = viz.blendLinkable(camera,camera)
blend.setBlend(1.0)

# Create link for viewpoint
view_link = viz.link(blend,viz.MainView)

# Create view attachment options
fly_attach = viz.flagWrappedLinkable(axes,viz.ABS_GLOBAL)
avatar_attach = viz.link(avatar,viz.NullLinkable,srcFlag=viz.ABS_GLOBAL)
avatar_attach.preTrans([0,2,-2])
avatar_attach.preEuler([0,10,0])

view_options = [ ('Keyboard',camera)
				,('Fly Animation',fly_attach)
				,('Walking Avatar',avatar_attach)]

# Config helper functions

def setFlySpeed(speed):
	animations.setAnimationSpeed(speed,node='fly')

def getFlySpeed():
	return animations.getAnimationSpeed(node='fly')

def setViewLink(src):

	# Blend from current source to new source
	blend.setBeginLinkable(blend.getEndLinkable())
	blend.setEndLinkable(src)
	blend.setBlend(0.0)
	viz.MainView.runAction(vizact.call(blend.setBlend,vizact.mix(0.0,1.0,time=1.0,interpolate=vizact.easeOutStrong)))

	#Hide axes when attached to it
	axes.visible(src is not fly_attach)

def getViewLink():
	return blend.getEndLinkable()

# Create config window for displaying options
config = vizconfig.BasicConfigurable('Options')
config.addFloatRangeItem('Fly Speed',[0.0,2.0],fset=setFlySpeed,fget=getFlySpeed)
config.addChoiceListItem('View Link',view_options,fset=setViewLink,fget=getViewLink)
vizconfig.register(config)
vizconfig.getConfigWindow().setWindowVisible(True)
