from enum import Enum

class Orientation(Enum):
	Side=1
	Top=2
	Bottom=3
	
class Mode(Enum):
	Build=0
	Edit=1
	Add=2
	View=3
	Walk=4
	
class Level(Enum):
	Horizontal = 0
	Vertical = 1