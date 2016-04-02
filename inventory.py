
class OrderList(list):
	def __init__(self, *args):
		list.__init__(self, *args)
	def sortByAttr(self, firstAttr='diameter', secondAttr='thickness', thirdAttr='length'):
		from operator import attrgetter
		sortedList = sorted(self, key=attrgetter(firstAttr, secondAttr, thirdAttr))
		self = sortedList
		return self