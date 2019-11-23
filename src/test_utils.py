from unittest import TestCase

from SINUtil import *

def is_sorted_rev(a):
	for i in range(len(a)-1):
		if a[i] <= a[i+1]:
			return False
	return True

class TestUtils(TestCase):

	def test_stoch_sort(self):
		np.random.seed(0)#determinism
		a = list(range(10))
		np.random.shuffle(a)

		aa = stoch_sort(a,levels=100)#should sort the array in descending order
		assert(is_sorted_rev(aa))

		#just regression for this
		a = list(range(10))
		np.random.shuffle(a)
		aa = stoch_sort(a,levels=1)
		assert(aa == [9,8,7,6,5,0,2,3,1,4])