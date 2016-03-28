"""Tools for opening external files, etc"""

import os
import win32api

from launcher_tools import path_tools

def openPDF(url):
	"""Command to launch an instance of chromium portable"""
	cmdline = 'start "" "{}"'.format(url)
	print cmdline
	try:
		os.system(cmdline)
	except OSError:
		return False


def openCHM(url):
	"""Command to launch an instance of chromium portable"""
	cmdline = 'hh.exe {}'.format(url)
	try:
		#or... subprocess.call(cmdline), os.system(cmdline)
		win32api.WinExec(cmdline)
	except OSError:
		return False


def openVizardRelativeCHM(url):
	"""Command to launch an instance of chromium portable"""
	vizardHelpDir = os.path.join(path_tools.getVizardPath(), 'help/Vizard.chm')
	cmdline = 'hh.exe "{}::/{}"'.format(vizardHelpDir, url)
	print cmdline
	try:
		win32api.WinExec(cmdline)
	except OSError:
		return False


def openVizardToFile(fullPath):
	"""Command to launch an instance of chromium portable"""
	cmdline = '"{}" "{}"'.format(os.path.join(path_tools.getVizardPath(), 'bin/Vizard.exe'), fullPath)
	print cmdline
	try:
		win32api.WinExec(cmdline)
	except OSError:
		return False



