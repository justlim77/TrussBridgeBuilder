import viz
import vizdlg

viz.go()

myPanel = vizdlg.Panel()

#Add row of checkboxes
row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,border=False,background=False,margin=0)
row.addItem(viz.addText('Checkboxes'))
check1 = row.addItem(viz.addCheckbox())
check2 = row.addItem(viz.addCheckbox())
check3 = row.addItem(viz.addCheckbox())

#Add row to myPanel
myPanel.addItem(row)

#Add a subgroup containing slider/textbox
group = vizdlg.Panel()

#Add row for slider to subgroup
row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,border=False,background=False,margin=0)
row.addItem(viz.addText('Slider'))
slider = row.addItem(viz.addSlider())
group.addItem(row)

#Add row for textbox to subgroup
row = vizdlg.Panel(layout=vizdlg.LAYOUT_HORZ_BOTTOM,border=False,background=False,margin=0)
row.addItem(viz.addText('Textbox'))
textbox = row.addItem(viz.addTextbox())
group.addItem(row)

myPanel.addItem(group)
viz.link(viz.CenterCenter,myPanel,offset=(-100,50,0))