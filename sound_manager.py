import viz
import vizconfig

import json


class Sound(object):
	def __init__(self, sound, name):
		self._sound = sound
		self._name = name
		self._volume = 1.0
		
		self._hasGet = False
		if hasattr(self._sound, 'getVolume'):
			self._hasGet = True
		
		if not hasattr(self._sound, 'setVolume') and hasattr(self._sound, 'volume'):
			self._sound.setVolume = self._sound.volume
	
	def getName(self):
		return self._name
	
	def getVolume(self):
		if self._hasGet:
			self._volume = self._sound.getVolume()
		return self._volume
	
	def setVolume(self, volume):
		self._volume = volume
		return self._sound.setVolume(volume)


class SoundManager(vizconfig.Configurable):
	def __init__(self):
		# make this a configurable node, so we can edit some parameters
		vizconfig.Configurable.__init__(self, 'Sound Manager')
		
		self._soundDict = {}
		# remove the activation key
#		self._vizconfigWindow = vizconfig.getConfigWindow('sound manager')
#		self._vizconfigWindow.setActivationKey(None)
		
		# Automatically register configurable
		vizconfig.register(self)
	
	def add(self, rawSound, name):
		sound = Sound(rawSound, name)
		self._soundDict[name] = sound
	
	def createConfigUI(self):
		"""Creates the vizconfig configuration ui. You do not need to call this
		function directly.
		"""
		ui = vizconfig.DefaultUI()
		print "creating"
#		ui.addBoolItem('enabled', self._sound.setEnabled, self._sound.getEnabled)
		for name, sound in self._soundDict.iteritems():
			ui.addFloatRangeItem(name, [0.0, 1.0], sound.setVolume, sound.getVolume)
		ui.addCommandItem('', label='save', fup=self.save)
		return ui
	
	def load(self, filename=None):
		"""Loads the setting file"""
		if filename is None:
			filename = 'sound_settings.json'
		volumeDict = {}
		try:
			with open(filename, 'r') as file:
				volumeDict.update(json.loads(file.read()))
			for name, volume in volumeDict.iteritems():
				self._soundDict[name].setVolume(volume)
				print name, volume
		except ValueError:
			pass
	
	def save(self, filename=None):
		"""Saves the setting file"""
		if filename is None:
			filename = 'sound_settings.json'
		volumeDict = {}
		for name, sound in self._soundDict.iteritems():
			volumeDict[name] = sound.getVolume()
		with open(filename, 'w') as file:
			file.write(json.dumps(volumeDict))



if __name__ == "__main__":
	sound = viz.addAudio('conversation.wav')
	sound.loop(True)
	sound.play()
	
	soundFountain = viz.addAudio('fountain.wav')
	soundFountain.loop(True)
	soundFountain.play()
	
#	window = vizconfig.getConfigWindow('sound manager')
#	window.setWindowVisible(True)
	manager = SoundManager()
	manager.add(sound, 'conversation')
	manager.add(soundFountain, 'fountain')
	viz.go()
	viz.add('piazza.osgb')
	
	manager.load()
	
#	manager.vizconfigWindow.setWindowVisible(True)
#	mixer = viz.addSoundMixer()
#	mixer.setVolume()
