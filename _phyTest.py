import viz

viz.go()
viz.phys.enable()

viz.phys.setGravity(0,-9.8/6,0) #Half Gravity 
ground1 = viz.add('tut_ground.wrl',euler=[0,0,-30]) 
r = viz.Matrix.euler(0,0,-30).getUp() # Calculate Normal 
r.append(0) # Add length 
ground1.collidePlane(*r) # Collide Plane 

ground2 = viz.add('tut_ground.wrl',euler=[0,0,30]) 
r = viz.Matrix.euler(0,0,30).getUp() # Calculate normal from euler. 
r.append(0) # Add length 
ground2.collidePlane(*r) # Collide Plane 

for x in range(10): 
    for z in range(10): 
        ball = viz.add('white_ball.wrl',pos=[-.5+.1*x,2.5+.1*z,6+.01*z],scale=[.5,.5,.5]) 
        ball.collideSphere() 