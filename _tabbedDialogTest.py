import viz
import vizdlg

viz.go()

court = viz.add('gallery.ive')
ball = viz.add('white_ball.wrl',pos=[0,1.8,2])

#create two dialog objects
p1 = vizdlg.ColorDialog(value=[0.3,0.5,1])
p2 = vizdlg.TickerDialog(label='Scale',range=(0,2,.25),value=1)

#create a TabPanel
tp = vizdlg.TabPanel(align=vizdlg.ALIGN_RIGHT_TOP)

#add the dialog objects to the TabPanel
tp.addPanel('Color',p1,align=vizdlg.ALIGN_CENTER)
tp.addPanel('Scale',p2,align=vizdlg.ALIGN_CENTER)

#position the TabPanel
viz.link(viz.RightTop,tp,offset=(-20,-20,0))

#handle accept button events
def changeColor():
    ball.color(p1.value)

vizact.onbuttondown(p1.accept,changeColor)

def changeScale():
    ball.setScale([p2.value]*3)

vizact.onbuttondown(p2.accept,changeScale)