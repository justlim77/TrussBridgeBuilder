import os
import re
TARGET = 'placer.py'
ONLY_FIND_ONCE = True# only find each error once

import tokenize

def processStrings(type, token, (srow, scol), (erow, ecol), line):
    if tokenize.tok_name[type] == 'STRING' :
        print tokenize.tok_name[type], token, \
              (srow, scol), (erow, ecol), line

text = ""
with open(TARGET, 'r') as tempFile:
	text = tempFile.read()

def isVariable(word, code):
	if word.isupper():
		return True
	patternList = [
		'{}\s*='.format(word),
		'import[\_\s]*{}'.format(word),
		'class[\_\s]*{}'.format(word),
		'def[\_\s]*{}'.format(word),
		'self.[\_]*{}'.format(word),
		'viz.[\_]*{}'.format(word),
		'vizshape.[\_]*{}'.format(word),
		'\.[\_]*{}\('.format(word),
		'{}\.dle'.format(word),
	]
	for pattern  in patternList:
		match = re.search(pattern, code)
		if match:
			return True
	return False


with open(TARGET, 'r') as tempFile:
	from enchant.checker import SpellChecker
	chkr = SpellChecker("en_US")
	chkr.add("param")
	chkr.add("quat")
	chkr.add("euler")
	chkr.add("pos")
	chkr.add("win32gui")
	chkr.add("dle")
	chkr.add("vizard")
	chkr.add("wasd")
	chkr.add("indices")
	chkr.add("vizard")
	chkr.add("KINECT")
	chkr.add("localhost")
	chkr.add("vcc")
	chkr.add("osgb")
	chkr.add("cfg")
	chkr.add("diff")
	chkr.add("mult")
	chkr.add("TODO")
	chkr.add("args")
	chkr.add("vec")
	chkr.add("programmatically")
	
	wordList = []
	
	g = tokenize.generate_tokens(tempFile.readline)   # tokenize the string
	for toknum, tokval, _, _, _  in g:
		if tokenize.tok_name[toknum] in ['STRING', 'COMMENT']:
			chkr.set_text(tokval)
			for err in chkr:
				# check if the error has an assignment or import statement
				if not isVariable(err.word, text):
					#print "ERROR:", err.word
					i = 1
					for line in text.splitlines():
						if err.word in line:
							inList = err.word in wordList
							if not (ONLY_FIND_ONCE and inList):
								msg = "Error: {}".format(err.word)
								path = os.path.abspath(os.path.join(os.path.dirname(__file__), TARGET))
								newLine = '  File "{}", line {}, in {}\n \t{}\n'.format(path, i, TARGET.replace('.py', ''), msg)
								sys.stderr.write(newLine)
								if not inList:
									wordList.append(err.word)
						i+=1

