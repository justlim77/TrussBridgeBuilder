from datetime import datetime
from pyInstall import installIfNeeded

def log(message):
    print(datetime.now().strftime("%a %b %d %H:%M:%S") + " - " + str(message))

# Enum34 is actually named enum on pip.
installIfNeeded("enum", "enum34", log = log)

import enum
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