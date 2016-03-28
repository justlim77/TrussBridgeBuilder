import os
import re
TARGET = 'embedded_gui.py'


def autoFormat():
	with open(TARGET, 'r') as tempFile:
		text = tempFile.read()
	
	changeList = [
		(' )', ')'),
		('( ', '('),
		('(	', '('),
		('	) ', ')'),
#		('==', ' =='), 
#		('  ==', ' =='), 
#		('==', '== '), 
#		('==  ', '== '), 
	]
	
	for src, dst in changeList:
		while src in text:
			text = text.replace(src, dst)
	
	patternList = [
		('\,\S', ',', ', '),
		('\=\=\S', '==', '== '),
		('\S\=\=', '==', ' ==')
#		('\=[^\=\s]', '=', '= '),
#		('[^\=\s]\=', '=', ' =')
	]
	for pattern, startChars, endChars  in patternList:
		match = re.search(pattern, text)
		while match:
			startText = match.group(0)
			endText = startText.replace(startChars, endChars)
			text = text.replace(startText, endText)
			match = re.search(pattern, text)
	
	with open(TARGET, 'w') as tempFile:
		tempFile.write(text)
autoFormat()


os.environ["PATH"] += os.pathsep + os.path.normpath(sys.exec_prefix)
os.environ["PATH"] += os.pathsep + os.path.normpath(r'C:\Program Files (x86)\WorldViz\Vizard5\bin\Scripts')

from pylint import epylint as lint
WEAKNESS = 2

disabledList = []
disabledList.append(['W0312', 'C0330', 'R0902', 'R0913', 'R0904', 'R0201', 'E1103', 'W0212'])# 1 (ignore tabs vs spaces (tabs are vizard convention))
disabledList.append(['C0301', 'C0303', 'C0103'])# 2
disabledList.append(['W0622', 'W0212'])# 2
disabledList.append(['C0111'])# 3
disabledList.append(['E1103'])# 4
disabledList.append(['W0612'])# 5
disabledList.append(['W0703', 'W0702'])# 6


#sys.stderr.write(r'  File "D:\repos\coffin\demo_dvd_sencha\demos\converting\modern_lobby\script_checker.py", line 29, in <module>\n')

finalDisabled = []
for i in range(0, WEAKNESS):
	finalDisabled += disabledList[i]

#sys.stderr.write( 'File "D:\\repos\\coffin\\demo_dvd_sencha\\demos\\converting\\modern_lobby\\script_checker.py", line 28')

def check(enabledString, disabledString):
	with open('pylint_error.log', 'w') as tempFile:
		if enabledString:
			enabledString = '--enable={}'.format(enabledString)
		if disabledString:
			disabledString = '--disable={}'.format(disabledString)
		commandLineString = '{} {} {}'.format(TARGET, disabledString, enabledString)
		print commandLineString
		lint.py_run(commandLineString, stdout=tempFile)
	
	with open('pylint_error.log', 'r') as tempFile:
		log = tempFile.read()
		for line in log.split('\n'):
			dataList = line.split(':')
			if len(dataList) >= 3:
				filename = dataList[0].lstrip(' ')
				lineNumber = dataList[1]
				msg = dataList[2]
				path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
				newLine = '  File "{}", line {}, in {}\n \t{}\n'.format(path, lineNumber, TARGET.replace('.py', ''), msg)
				
				sys.stderr.write(newLine)

#check(enabledString='', disabledString=','.join(finalDisabled))

#import traceback
#def test():
#	print 'yo'
#	traceback.print_stack()
#test()

## import check
##lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['W0611'])))
#check(enabledString='W0611', disabledString='R,C,W,E')
#
## redefining builtin
##lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['W0622'])))
#check(enabledString='W0622', disabledString='R,C,W,E')


# missing method docstring
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['W0622'])))
check(enabledString='C0111', disabledString='R,C,W,E')


# unused variable
#check(enabledString='W0612', disabledString='R,C,W,E')

# unused argument
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['C0326'])))
#check(enabledString='W0613', disabledString='R,C,W,E')

# whitespace check
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['C0326'])))
#check(enabledString='C0326', disabledString='R,C,W,E')

# protected access
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['W0212'])))
#check(enabledString='W0212', disabledString='R,C,W,E')

# attribute-defined-outside-init
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['W0201'])))
#check(enabledString='W0201', disabledString='R,C,W,E')

# reimport
#check(enabledString='W0404', disabledString='R,C,W,E')

# redefining built in
#check(enabledString='W0622', disabledString='R,C,W,E')

# attribute-defined-outside-init
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['W0613'])))
#check(enabledString='W0613', disabledString='R,C,W,E')

# line too long
#lint.py_run('{} --disable=R,C,W,E --enable={}'.format(TARGET, ','.join(['C0301'])))
#check(enabledString='C0301', disabledString='R,C,W,E')

import tokenize

def processStrings(type, token, (srow, scol), (erow, ecol), line):
    if tokenize.tok_name[type] == 'STRING' :
        print tokenize.tok_name[type], token, \
              (srow, scol), (erow, ecol), line

text = ""
with open(TARGET, 'r') as tempFile:
	text = tempFile.read()

def isVariable(word, code):
	patternList = [
		'{}\s*\='.format(word),
		'import {}'.format(word),
	]
	for pattern  in patternList:
		match = re.search(pattern, code)
		if match:
			print "is variable", word
			return True
	return False


with open(TARGET, 'r') as tempFile:
	from enchant.checker import SpellChecker
	chkr = SpellChecker("en_US")
	
	g = tokenize.generate_tokens(tempFile.readline)   # tokenize the string
	for toknum, tokval, _, _, _  in g:
		if tokenize.tok_name[toknum] in ['STRING', 'COMMENT']:
			chkr.set_text(tokval)
			for err in chkr:
				# check if the error has an assignment or import statement
				if not isVariable(err, text):
					pass#print "ERROR:", err.word

