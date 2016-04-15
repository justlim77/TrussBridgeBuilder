

import viz
viz.go()

import viz
viz.go()

#Load model
logo = viz.add('logo.wrl')
logo.setPosition(0,2,5)

#Load textures
tex1 = viz.add('gb_noise.jpg')
tex2 = viz.add('ball.jpg')

#Apply textures
logo.texture(tex1)
logo.texture(tex2,'',1)

#Blend texture layer 1 with layer 0 by 50%
logo.texblend(0.5,'',1)

#Add the slider and set to 50%
slider = viz.addSlider(pos=[0.5,0.1,0])
slider.set(0.5)

def blendTextures(pos):
    #Blend texture layer 1 with layer 0 by amount specified by slider position
    logo.texblend(pos,'',1)

vizact.onslider(slider, blendTextures)