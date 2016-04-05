import viz 
import vizact 
import vizdlg

PANEL_EVENT = viz.getEventID('PANEL_EVENT')

global _panel
def CheckPanel():
	_panel = vizdlg.TabPanel()
	viz.sendEvent(PANEL_EVENT,_panel)
vizact.onupdate(0,CheckPanel)


	