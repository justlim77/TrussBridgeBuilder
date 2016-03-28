"""Module to provide convenience function for accessing validity of 
vizconnect-based hardware
"""

import viz
import vizconnect

import external_opening_tools


def everythingValid():
	"""Returns True if all trackers and inputs are valid.
	
	@return bool
	"""
	for tracker in vizconnect.getTrackerDict().values():
		if not tracker.getTemplateObject().isValid(tracker.getRaw()):
			return False
	for inputWrapper in vizconnect.getInputDict().values():
		if not inputWrapper.getTemplateObject().isValid(inputWrapper.getRaw()):
			return False
	return True


def getInvalidObjects():
	"""Returns a list of objects which are invalid
	
	@return []
	"""
	invalidList = []
	for tracker in vizconnect.getTrackerDict().values():
		if not tracker.getTemplateObject().isValid(tracker.getRaw()):
			invalidList.append(tracker)
	for inputWrapper in vizconnect.getInputDict().values():
		if not inputWrapper.getTemplateObject().isValid(inputWrapper.getRaw()):
			invalidList.append(inputWrapper)
	return invalidList


def getInvalidString():
	"""Returns a list of strings with makes and models of objects which are invalid.
	
	@return []
	"""
	stringList = []
	invalidList = getInvalidObjects()
	for obj in invalidList:
		stringList.append("Make: {} Model: {} Name: {}".format(obj.getMake(), obj.getModel(), obj.getName()))
	return stringList


def openPagesForInvalidObjects():
	"""Returns a list of strings with makes and models of objects which are invalid.
	
	@return []
	"""
	stringList = []
	invalidList = getInvalidObjects()
	pageSet = set()
	for obj in invalidList:
		pageSet.add(obj.getTemplateObject().getDocPage())
	for page in pageSet:
		external_opening_tools.openCHM(page)
	return stringList


if __name__ == '__main__':
	vizconnect.go('vizconnect_config_hardware_status_test.py')
	viz.add('piazza.osgb')
	print everythingValid()
	print '\n'.join(getInvalidString())
