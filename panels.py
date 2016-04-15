import viz
import vizdlg
import vizinfo

def CreateLabelledPanel():
	panel = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	diameterLabel = viz.addButtonLabel('d (mm)')
	thicknessLabel = viz.addButtonLabel('t (mm)')
	lengthLabel = viz.addButtonLabel('l (m)')
	quantityLabel = viz.addButtonLabel('qty')
	deleteLabel = viz.addButtonLabel('')
	headerRow = panel.addRow([diameterLabel,thicknessLabel,lengthLabel,quantityLabel,deleteLabel])
	return panel
	
def CreateInventoryPanel():
	panel = vizdlg.GridPanel(cellAlign=vizdlg.ALIGN_CENTER_TOP,border=False,spacing=0,padding=1,background=False,margin=0)
	return panel
	
class InspectorPanel(vizinfo.InfoPanel):
	def __init__(self):
#		self.statsPanel = vizinfo.InfoPanel(title='Inspector',text=None,align=viz.ALIGN_CENTER_BASE,icon=False)
#		self.statsPanel.getTitleBar().fontSize(16)
#		self.diameter_stat = viz.addText('d (mm)')
#		self.statsPanel.addItem(self.diameter_stat)
#		self.thickness_stat = viz.addText('t (mm)')
#		self.statsPanel.addItem(self.thickness_stat)
#		self.length_stat = viz.addText('l (m)')
#		self.statsPanel.addItem(self.length_stat)
#		self.rotation_stat = viz.addText('angle')
#		self.statsPanel.addItem(self.rotation_stat)
		
		self.statsPanel = vizdlg.Panel(align=viz.ALIGN_CENTER_TOP,border=False)
		self.statsMsg = self.statsPanel.addItem(viz.addText('Highlight truss member to inspect'))
	def GetPanel(self):
		return self.statsPanel
	def DiameterStat(self):
		return self.diameter_stat
	def SetMessage(self,message=None):
		if message != None:
			self.statsMsg.message(message)
		else:
			self.statsMsg.message('Highlight truss member to inspect')