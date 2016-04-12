import viz
import vizact

viz.go()

#Create some objects. 
for i in range(10): 
    viz.add('wheelbarrow.ive',cache=viz.CACHE_CLONE).setPosition(i,0,0) 
#Create an action to cue. 
MouseOverAction = vizact.fadeTo(1,begin=0,time=1) 

def picker(): 
    #Check if the mouse is over one of the boxes 
    item = viz.MainWindow.pick( info = True ) 
    #If there is an intersection 
    if item.valid: 
        #Add mouse over action 
        item.object.runAction(MouseOverAction) 
        #Print the point where the line intersects the object. 
        print item.point 

#Start a timer to execute picker repeatedly. 
vizact.ontimer(.1, picker ) 