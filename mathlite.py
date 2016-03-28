import math
from math import pi

def getPointsInCircum(r,n=10):
	return [(math.cos(2*pi/n*x)*r,math.sin(2*pi/n*x)*r) for x in xrange(0,n+1)]
	
def getNewRange(value, fromMin, fromMax, toMin, toMax):
	return (((value - fromMin) * (toMax - toMin)) / (fromMax - fromMin) + toMin)